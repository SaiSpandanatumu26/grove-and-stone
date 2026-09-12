"""Owner operations, delivery imports and a transactional alert dispatcher."""
import csv
import gzip
import hashlib
import io
import json
import secrets
from pathlib import Path
from threading import Lock, Thread
from time import sleep
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import click
from email_validator import validate_email, EmailNotValidError
from flask import current_app, g, request, send_from_directory
from sqlalchemy import select, func, or_
from sqlalchemy.dialects.postgresql import insert

from .api import api, assign, body, fail, get_row, invalid, paginated, respond, text_value
from .auth import require
from .extensions import db, limiter
from .models import AdminUser, AdminInvite, AuthSession, CMSBanner, Order, OwnerAlert, Shipment, ShopSetting, AdminAudit, PostalArea, PincodeService, RefundRequest

_dispatch_lock = Lock()


def kick_owner_dispatch(app):
    """Start a process-local mail loop after commit; durable jobs survive restarts."""
    if app.testing or not app.config.get('RESEND_API_KEY') or not _dispatch_lock.acquire(False): return
    def run():
        try:
            while True:
                with app.app_context():
                    try: dispatch_owner_alerts()
                    except Exception as error:
                        db.session.rollback()
                        app.logger.error('Owner email dispatch: %s', type(error).__name__)
                    finally: db.session.remove()
                sleep(30)
        finally: _dispatch_lock.release()
    Thread(target=run, daemon=True, name='owner-alert-dispatch').start()


def now(): return datetime.now(timezone.utc)


def setting(key, default=None):
    row = db.session.get(ShopSetting, key)
    return row.value if row else current_app.config.get(key.upper(), default)


def accepting_orders():
    return setting('orders_enabled', current_app.testing or current_app.config['PAYMENT_BACKEND'] == 'demo') is True


SETTINGS = {'business_name', 'support_email', 'support_phone', 'business_address', 'gstin', 'owner_email',
            'email_alerts_enabled', 'orders_enabled', 'coverage_reviewed', 'catalog_reviewed', 'policies_reviewed'}


def email_ready():
    return bool(setting('owner_email') and current_app.config.get('RESEND_API_KEY') and current_app.config.get('CONTACT_FROM'))


def readiness():
    config = current_app.config
    return dict(business=all(setting(k) for k in ('business_name', 'business_address', 'support_email')),
                delivery=bool(setting('coverage_reviewed', False)) and bool(db.session.scalar(select(func.count()).select_from(PincodeService).where(PincodeService.serviceable.is_(True)))),
                catalog=bool(setting('catalog_reviewed', False)), policies=bool(setting('policies_reviewed', False)),
                owner_email=email_ready() and bool(setting('email_alerts_enabled', False)),
                online_payments=config['PAYMENT_BACKEND'] == 'razorpay' and all(config.get(k) for k in ('RAZORPAY_KEY_ID', 'RAZORPAY_KEY_SECRET', 'RAZORPAY_WEBHOOK_SECRET', 'PUBLIC_API_URL')),
                payment_mode='live' if (config.get('RAZORPAY_KEY_ID') or '').startswith('rzp_live_') else 'test' if (config.get('RAZORPAY_KEY_ID') or '').startswith('rzp_test_') else 'disabled',
                orders_enabled=accepting_orders())


@api.get('/admin/auth/me')
@require('admin', {'admin', 'packer'})
def me(): return respond(g.actor)


@api.post('/admin/auth/logout')
@require('admin', {'admin', 'packer'})
def admin_logout():
    db.session.delete(g.auth_session)
    return '', 204


@api.post('/admin/auth/activate')
@limiter.limit('5/minute;20/hour')
def activate_owner():
    data = body({'token', 'password'}, {'token', 'password'})
    token = text_value(data['token'], 'token', 32, 150)
    invite = db.session.scalar(select(AdminInvite).where(AdminInvite.token_digest == hashlib.sha256(token.encode()).hexdigest()).with_for_update())
    if not invite or invite.used_at or invite.expires_at <= now(): fail(403, 'INVITE_EXPIRED', 'This invitation is invalid or expired. Ask for a new invitation.')
    if not isinstance(data['password'], str) or not 12 <= len(data['password']) <= 1024: invalid('password', 'Use at least 12 characters.')
    if db.session.scalar(select(AdminUser.id).where(func.lower(AdminUser.email) == invite.email.lower())): fail(409, 'ACCOUNT_EXISTS', 'This staff account already exists. Sign in instead.')
    actor = AdminUser(name=invite.name, email=invite.email, password=data['password'], role='admin', is_active=True)
    invite.used_at = now()
    db.session.add(actor)
    db.session.flush()
    from .auth import issue
    return respond(issue(actor), 201)


@api.route('/admin/settings', methods=['GET', 'PATCH'])
@require('admin', {'admin'})
def settings():
    if request.method == 'PATCH':
        data = body(SETTINGS)
        for key, value in data.items():
            if key.endswith(('_enabled', '_reviewed')):
                if type(value) is not bool: invalid(key, 'Choose yes or no.')
            else:
                value = text_value(value, key, 0, 500)
                if key.endswith('_email') and value:
                    try: value = validate_email(value, check_deliverability=False).normalized.lower()
                    except EmailNotValidError: invalid(key, 'Enter a valid email address.')
                if key == 'support_phone' and value and (not value.isascii() or not value.isdigit() or len(value) != 10): invalid(key, 'Enter a 10-digit phone number.')
            row = db.session.get(ShopSetting, key) or ShopSetting(key=key)
            row.value = value
            db.session.add(row)
        db.session.flush()
        if data.get('orders_enabled'):
            ready = readiness()
            if not all(ready[k] for k in ('business', 'delivery', 'catalog', 'policies')):
                fail(422, 'SETUP_INCOMPLETE', 'Complete business details and review your catalog, delivery coverage and policies before opening orders.')
        if data.get('email_alerts_enabled') and not email_ready(): fail(422, 'EMAIL_NOT_CONFIGURED', 'Configure the verified sender and email provider in hosting settings first.')
    return respond(dict(values={key: setting(key, False if key.endswith(('_enabled', '_reviewed')) else '') for key in SETTINGS}, readiness=readiness()))


@api.get('/admin/alerts')
@require('admin', {'admin', 'packer'})
def alerts():
    from .api import json_value
    return respond({**paginated(select(OwnerAlert).order_by(OwnerAlert.created_at.desc(), OwnerAlert.id), lambda row: {**json_value(row), 'order_number': row.order.order_number, 'total': json_value(row.order.grand_total)}),
                    'unread': db.session.scalar(select(func.count()).select_from(OwnerAlert).where(OwnerAlert.seen_at.is_(None)))})


@api.post('/admin/alerts/<uuid:key>/read')
@require('admin', {'admin', 'packer'})
def read_alert(key):
    row = get_row(OwnerAlert, key, lock=True)
    row.seen_at = now()
    return respond(row)


@api.post('/admin/alerts/<uuid:key>/retry')
@require('admin', {'admin'})
def retry_alert(key):
    row = get_row(OwnerAlert, key, lock=True)
    if row.sent_at: fail(422, 'ALREADY_SENT', 'This email was already accepted by the provider.')
    if not email_ready() or not setting('email_alerts_enabled', False): fail(422, 'EMAIL_NOT_CONFIGURED', 'Configure and enable owner email alerts first.')
    row.attempts, row.next_attempt_at, row.last_error = 0, now(), None
    return respond(row)


def enqueue_owner(order):
    if order.status not in {'confirmed', 'cancelled'}: return
    kind = 'new_order' if order.status == 'confirmed' else 'order_cancelled'
    db.session.execute(insert(OwnerAlert).values(order_id=order.id, kind=kind).on_conflict_do_nothing(index_elements=['order_id', 'kind']))


def dispatch_owner_alerts(limit=25):
    if not email_ready() or not setting('email_alerts_enabled', False): return {'sent': 0, 'failed': 0, 'configured': False}
    jobs = db.session.scalars(select(OwnerAlert).where(OwnerAlert.sent_at.is_(None), OwnerAlert.attempts < 8, OwnerAlert.next_attempt_at <= now())
                              .order_by(OwnerAlert.created_at).limit(limit).with_for_update(skip_locked=True)).all()
    counts = dict(sent=0, failed=0, configured=True)
    for job in jobs:
        order = job.order
        # Never retry an uncertain delivery beyond the provider's 24h idempotency window.
        if job.attempts and job.created_at < now() - timedelta(hours=23):
            job.attempts, job.last_error = 8, 'Delivery uncertain; check provider before retrying'
            counts['failed'] += 1
            continue
        payload = {'from': current_app.config['CONTACT_FROM'], 'to': [setting('owner_email')],
                   'subject': f"{setting('business_name', 'Grove & Stone')}: {job.kind.replace('_', ' ')} {order.order_number}",
                   'text': f"Order: {order.order_number}\nStatus: {order.status}\nPayment: {order.payment_method} / {order.payment_status}\nTotal: INR {order.grand_total}\nDelivery: {order.delivery_date}\nPincode: {order.pincode}\n\nOpen your private owner dashboard to see the address and fulfil this order."}
        req = Request('https://api.resend.com/emails', data=json.dumps(payload).encode(), headers={
            'Authorization': 'Bearer ' + current_app.config['RESEND_API_KEY'], 'Content-Type': 'application/json', 'Idempotency-Key': 'owner-alert-' + str(job.id)})
        job.attempts += 1
        try:
            with urlopen(req, timeout=10) as response:
                if not json.load(response).get('id'): raise ValueError('Missing receipt')
            job.sent_at, job.last_error = now(), None
            counts['sent'] += 1
        except Exception as error:
            job.last_error = type(error).__name__
            job.next_attempt_at = now() + timedelta(minutes=min(60, 2 ** job.attempts))
            counts['failed'] += 1
    db.session.commit()
    return counts


@api.route('/admin/orders/<uuid:key>/shipment', methods=['PUT'])
@require('admin', {'admin', 'packer'})
def shipment(key):
    order = get_row(Order, key, lock=True)
    if order.status not in {'confirmed', 'packed', 'shipped'}: fail(422, 'INVALID_TRANSITION', 'Only an active confirmed order can have shipment details edited.')
    data = body({'carrier', 'tracking_number', 'tracking_url'}, {'carrier', 'tracking_number'})
    if data.get('tracking_url'):
        url = urlparse(data['tracking_url'])
        if url.scheme != 'https' or not url.netloc or url.username or url.password: invalid('tracking_url', 'Enter an HTTPS tracking URL.')
    row = db.session.scalar(select(Shipment).where(Shipment.order_id == order.id)) or Shipment(order_id=order.id)
    assign(row, data, {'carrier', 'tracking_number', 'tracking_url'})
    row.updated_at = now()
    db.session.add(row)
    return respond(row)


@api.post('/admin/orders/<uuid:key>/collect-cod')
@require('admin', {'admin', 'packer'})
def collect_cod(key):
    order = get_row(Order, key, lock=True)
    if order.payment_method != 'cod' or order.status != 'delivered': fail(422, 'COD_UNAVAILABLE', 'Record cash collection only for a delivered COD order.')
    if body({'amount'}, {'amount'})['amount'] != format(order.grand_total, '.2f'): invalid('amount', 'Collected amount must match the full order total.')
    order.payment_status = 'paid'
    for payment in order.payments: payment.status = 'paid'
    return respond(order)


@api.get('/admin/refunds')
@require('admin', {'admin'})
def refunds(): return respond(paginated(select(RefundRequest).order_by(RefundRequest.created_at.desc())))


@api.post('/admin/refunds/process')
@require('admin', {'admin'})
@limiter.limit('2/minute')
def process_refunds():
    from .payments import dispatch_refunds
    return respond(dispatch_refunds())


@api.get('/admin/audit')
@require('admin', {'admin'})
def audit(): return respond(paginated(select(AdminAudit).order_by(AdminAudit.created_at.desc())))


@api.route('/admin/staff', methods=['GET', 'POST'])
@require('admin', {'admin'})
def staff():
    if request.method == 'GET': return respond({'items': db.session.scalars(select(AdminUser).order_by(AdminUser.name)).all()})
    fields = {'name', 'email', 'password', 'role', 'is_active'}
    data = body(fields, fields)
    if not isinstance(data['password'], str) or len(data['password']) < 12: invalid('password', 'Use at least 12 characters.')
    row = assign(AdminUser(), data, fields, fields)
    db.session.add(row)
    return respond(row, 201)


@api.patch('/admin/staff/<uuid:key>')
@require('admin', {'admin'})
def edit_staff(key):
    # Serialize staff changes so two admins cannot deactivate the last admins concurrently.
    from .carts import lock_owners
    lock_owners('admin:staff')
    row = get_row(AdminUser, key, lock=True)
    data = body({'name', 'is_active', 'role', 'password'})
    if key == g.actor.id and (data.get('is_active') is False or data.get('role', 'admin') != 'admin'): invalid('role', 'You cannot deactivate or demote your own account.')
    if 'password' in data and (not isinstance(data['password'], str) or len(data['password']) < 12): invalid('password', 'Use at least 12 characters.')
    assign(row, data, {'name', 'is_active', 'role', 'password'})
    if 'password' in data or data.get('is_active') is False or 'role' in data:
        for session in db.session.scalars(select(AuthSession).where(AuthSession.admin_id == row.id)): db.session.delete(session)
    return respond(row)


@api.route('/admin/banners', methods=['GET', 'POST'])
@require('admin', {'admin'})
def admin_banners():
    if request.method == 'GET': return respond({'items': db.session.scalars(select(CMSBanner).order_by(CMSBanner.start_date.desc(), CMSBanner.id)).all()})
    fields = set('title subtitle season_state cta_label cta_url image start_date end_date is_published'.split())
    row = assign(CMSBanner(), body(fields, fields - {'subtitle'}), fields)
    db.session.add(row)
    return respond(row, 201)


@api.patch('/admin/banners/<uuid:key>')
@require('admin', {'admin'})
def edit_banner(key):
    fields = set('title subtitle season_state cta_label cta_url image start_date end_date is_published'.split())
    return respond(assign(get_row(CMSBanner, key, lock=True), body(fields), fields))


@api.get('/admin/postal-directory')
@require('admin', {'admin'})
def postal_directory():
    query = select(PostalArea)
    if term := request.args.get('search'):
        term = text_value(term, 'search', 1, 100)
        query = query.where(or_(PostalArea.pincode.startswith(term, autoescape=True), PostalArea.district.icontains(term, autoescape=True), PostalArea.state.icontains(term, autoescape=True), func.array_to_string(PostalArea.offices, ' ').icontains(term, autoescape=True)))
    return respond(paginated(query.order_by(PostalArea.pincode)))


@api.get('/delivery/places')
@limiter.limit('60/minute')
def delivery_places():
    term = text_value(request.args.get('q', ''), 'q', 2, 80)
    query = select(PostalArea).where(or_(PostalArea.pincode.startswith(term, autoescape=True), PostalArea.district.icontains(term, autoescape=True),
        func.array_to_string(PostalArea.offices, ' ').icontains(term, autoescape=True))).order_by(PostalArea.pincode).limit(20)
    rows = db.session.scalars(query).all()
    areas = {r.pincode: r for r in db.session.scalars(select(PincodeService).where(PincodeService.pincode.in_([r.pincode for r in rows])))}
    return respond({'items': [dict(pincode=r.pincode, district=r.district, state=r.state,
        localities=[name for name in r.offices if term.lower() in name.lower()][:4] or r.offices[:3],
        serviceable=bool(areas.get(r.pincode) and areas[r.pincode].serviceable)) for r in rows], 'attribution': 'GeoNames'})


def load_postal_file(path, source):
    grouped = {}
    with (gzip.open if str(path).endswith('.gz') else open)(path, 'rt', encoding='utf-8-sig', newline='') as stream:
        for record in csv.DictReader(stream):
            row = {k.lower().replace(' ', '').replace('_', ''): (v or '').strip() for k, v in record.items() if k}
            pin = row.get('pincode', '')
            if not (len(pin) == 6 and pin.isascii() and pin.isdigit()): raise click.ClickException('Invalid pincode: ' + pin)
            district, state = row.get('district') or row.get('districtname'), row.get('state') or row.get('statename')
            if not district or not state: raise click.ClickException('CSV requires district and state.')
            target = grouped.setdefault(pin, dict(pincode=pin, district=district, state=state, offices=set(), source=source))
            target['offices'].add(row.get('office') or row.get('officename') or district)
    records = [{**row, 'offices': sorted(row['offices'])} for row in grouped.values()]
    for offset in range(0, len(records), 250):
        stmt = insert(PostalArea).values(records[offset:offset + 250])
        db.session.execute(stmt.on_conflict_do_update(index_elements=['pincode'], set_={**{k: getattr(stmt.excluded, k) for k in ('district', 'state', 'offices', 'source')}, 'updated_at': now()}))
    return len(records)


def load_bundled_postal():
    path = Path(__file__).parent / 'data/india-postal.csv.gz'
    if path.is_file() and not db.session.scalar(select(PostalArea.pincode).limit(1)):
        load_postal_file(path, 'https://download.geonames.org/export/zip/IN.zip')


@api.post('/admin/pincodes/import')
@require('admin', {'admin'})
def import_coverage():
    from .admin import PIN_FIELDS
    data = body({'csv'}, {'csv'})
    value = text_value(data['csv'], 'csv', 1, 800000)
    reader = csv.DictReader(io.StringIO(value.lstrip('\ufeff')))
    if set(reader.fieldnames or []) != PIN_FIELDS: invalid('csv', 'Use exactly these headers: ' + ','.join(sorted(PIN_FIELDS)))
    rows, seen = [], set()
    for line, record in enumerate(reader, 2):
        if len(rows) >= 3000: invalid('csv', 'Import at most 3,000 rows per file.')
        if None in record or any(value is None for value in record.values()): invalid('csv', f'Row {line}: use exactly one value per header.')
        record = {key: value.strip() for key, value in record.items()}
        if record.get('pincode') in seen: invalid('csv', f'Duplicate pincode on row {line}.')
        seen.add(record.get('pincode'))
        for key in ('serviceable', 'mango_eligible', 'cod_allowed'):
            raw = str(record[key]).strip().lower()
            if raw not in {'true', 'false'}: invalid('csv', f'Row {line}: {key} must be true or false.')
            record[key] = raw == 'true'
        for key in ('delivery_days_min', 'delivery_days_max'):
            try: record[key] = int(record[key])
            except (ValueError, TypeError): invalid('csv', f'Row {line}: {key} must be a whole number.')
        if not record.get('pincode', '').isascii() or not record['pincode'].isdigit() or len(record['pincode']) != 6: invalid('csv', f'Row {line}: invalid pincode.')
        row = db.session.get(PincodeService, record['pincode']) or PincodeService()
        assign(row, record, PIN_FIELDS, PIN_FIELDS)
        db.session.add(row)
        rows.append(row)
    if not rows: invalid('csv', 'Add at least one data row.')
    return respond({'imported': len(rows)})


def install_operations(app):
    @app.get('/admin')
    @app.get('/admin/<path:page>')
    def admin_page(page=''):
        response = send_from_directory('admin_web', page if page in {'app.js', 'style.css'} else 'index.html')
        response.headers.update({'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' https: data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'", 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer', 'X-Frame-Options': 'DENY'})
        return response

    @app.cli.command('dispatch-owner-alerts')
    def send_alerts(): click.echo(dispatch_owner_alerts())

    @app.cli.command('invite-owner')
    @click.option('--email', required=True)
    @click.option('--name', required=True)
    @click.option('--url', required=True, help='Public API origin, e.g. https://grove-and-stone.onrender.com')
    def invite_owner(email, name, url):
        """Privately issue a 24-hour, one-use owner activation link."""
        email = validate_email(email, check_deliverability=False).normalized.lower()
        if db.session.scalar(select(AdminUser.id).where(func.lower(AdminUser.email) == email)): raise click.ClickException('Account exists; use staff password recovery from a trusted administrator.')
        for previous in db.session.scalars(select(AdminInvite).where(AdminInvite.email == email, AdminInvite.used_at.is_(None))): previous.expires_at = now()
        token = secrets.token_urlsafe(40)
        db.session.add(AdminInvite(email=email, name=name, token_digest=hashlib.sha256(token.encode()).hexdigest(), expires_at=now() + timedelta(hours=24)))
        db.session.commit()
        click.echo(url.rstrip('/') + '/admin/activate#invite=' + token)

    @app.cli.command('operations-worker')
    def worker():
        """Run in an always-on worker or schedule dispatch-owner-alerts every minute."""
        import time
        from .checkout import expire_payments
        while True:
            try:
                expire_payments()
                dispatch_owner_alerts()
            except Exception as error:
                db.session.rollback()
                app.logger.error('Operations worker: %s', type(error).__name__)
            finally: db.session.remove()
            time.sleep(30)

    @app.cli.command('import-postal-directory')
    @click.argument('path', type=click.Path(exists=True, dir_okay=False))
    @click.option('--source', required=True, help='Publisher URL for this CSV snapshot.')
    def import_postal(path, source):
        """Import pincode,district,state,office CSV without enabling delivery."""
        count = load_postal_file(path, source)
        db.session.commit()
        click.echo(f'Imported {count} postal areas. Delivery coverage unchanged.')
