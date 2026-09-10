"""Atomic checkout, inventory reservations and customer cancellation."""
import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from uuid import uuid4

import click
from flask import current_app, g
from sqlalchemy import select

from .api import api, assign, body, fail, get_row, invalid, json_value, respond, text_value, uid
from .auth import require
from .carts import cart_json, coverage, current_cart, locked_variant
from .extensions import db
from .models import Address, CheckoutSession, Order, OrderLine, Payment, Product, RefundRequest, StockReservation
from .notifications import order_changed

STATES = 'Andhra Pradesh|Arunachal Pradesh|Assam|Bihar|Chhattisgarh|Goa|Gujarat|Haryana|Himachal Pradesh|Jharkhand|Karnataka|Kerala|Madhya Pradesh|Maharashtra|Manipur|Meghalaya|Mizoram|Nagaland|Odisha|Punjab|Rajasthan|Sikkim|Tamil Nadu|Telangana|Tripura|Uttar Pradesh|Uttarakhand|West Bengal|Andaman and Nicobar Islands|Chandigarh|Dadra and Nagar Haveli and Daman and Diu|Delhi|Jammu and Kashmir|Ladakh|Lakshadweep|Puducherry'.split('|')
ADDRESS = set('full_name phone line1 line2 city state pincode landmark address_type'.split())


def now(): return datetime.now(timezone.utc)
def digest(value): return hashlib.sha256(json.dumps(json_value(value), sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def shipping(subtotal):
    try:
        fee, threshold = (Decimal(str(current_app.config[key])) for key in ('SHIPPING_FEE', 'FREE_SHIPPING_THRESHOLD'))
        if any(not x.is_finite() or x < 0 or x > 999999 or x != x.quantize(Decimal('.01')) for x in (fee, threshold)): raise ValueError()
    except (InvalidOperation, ValueError): fail(503, 'SHIPPING_UNAVAILABLE', 'Delivery pricing is not configured yet.')
    return Decimal(0) if subtotal >= threshold else fee


def quote(cart, pincode):
    area = coverage(pincode)
    cart.pincode = pincode
    for key in sorted({line.product_id for line in cart.lines}): get_row(Product, key, lock=True)
    for line in sorted(cart.lines, key=lambda line: line.variant_id): line.unit_price = locked_variant(line.variant_id).price
    value = cart_json(cart)
    if value['block_reason']: fail(422, value['block_reason'], 'Check your cart and delivery pincode before continuing.')
    today = (now() + timedelta(hours=5, minutes=30)).date()
    dates = [today + timedelta(days=offset) for offset in range(area['delivery_days_min'], 15)]
    if not dates: fail(422, 'DELIVERY_UNAVAILABLE', 'No delivery dates are available within the next 14 days.')
    fee = shipping(value['subtotal'])
    result = dict(cart=value, shipping=fee, grand_total=value['subtotal'] + fee, delivery_dates=dates, area=area,
                  payment_backend=current_app.config['PAYMENT_BACKEND'], states=STATES)
    result['quote_id'] = digest(dict(lines=[(line.variant_id, line.qty, line.unit_price, line.variant.gst_percent) for line in sorted(cart.lines, key=lambda line: line.variant_id)],
                                    pincode=pincode, shipping=fee, dates=dates, cod=value['cod_allowed']))
    return result


def owned_order(number):
    row = db.session.scalar(select(Order).where(Order.order_number == number, Order.customer_id == g.customer.id).with_for_update())
    if row is None: fail(404, 'NOT_FOUND', 'Not found.')
    return row


def detail(row):
    session = db.session.get(CheckoutSession, row.id)
    return {**json_value(row), 'lines': json_value(row.lines), 'payments': json_value(row.payments),
            'payment_backend': session.backend if session else None, 'payment_expires_at': json_value(session.expires_at) if session else None,
            'refund': json_value(db.session.get(RefundRequest, row.id))}


def release(row):
    session = db.session.get(CheckoutSession, row.id)
    if not session or session.released_at: return
    reservations = db.session.scalars(select(StockReservation).where(StockReservation.order_id == row.id).order_by(StockReservation.variant_id)).all()
    from .models import Variant
    products = db.session.scalars(select(Variant.product_id).where(Variant.id.in_([item.variant_id for item in reservations]))).all()
    for key in sorted(set(products)): get_row(Product, key, lock=True)
    for item in reservations: locked_variant(item.variant_id).stock_qty += item.qty
    session.released_at = now()


def cancel_order(row):
    if row.status != 'confirmed': fail(422, 'INVALID_TRANSITION', 'Only confirmed orders can be cancelled.')
    row.status = 'cancelled'
    release(row)
    if row.payment_status == 'paid' and row.payment_method != 'cod':
        db.session.add(RefundRequest(order_id=row.id, amount=row.grand_total))
    order_changed(row)


@api.post('/checkout/quote')
@require()
def checkout_quote(): return respond(quote(current_cart(), body({'pincode'}, {'pincode'})['pincode']))


@api.get('/checkout/attempts/<uuid:key>')
@require()
def checkout_attempt(key):
    session = db.session.scalar(select(CheckoutSession).where(CheckoutSession.customer_id == g.customer.id, CheckoutSession.request_id == key))
    return respond({'order': detail(session.order) if session else None})


@api.post('/checkout')
@require()
def checkout():
    data = body({'request_id', 'quote_id', 'address_id', 'address', 'delivery_date', 'payment_method', 'customer_notes'}, {'request_id', 'quote_id', 'delivery_date', 'payment_method'})
    cart, key = current_cart(), uid(data['request_id'], 'request_id')
    previous = db.session.scalar(select(CheckoutSession).where(CheckoutSession.customer_id == g.customer.id, CheckoutSession.request_id == key))
    if previous:
        if previous.request_hash != digest(data): fail(409, 'CHECKOUT_CHANGED', 'This checkout attempt already exists. Open your order history.')
        return respond({'order': detail(previous.order), 'payment': json_value(previous.order.payments[0])})
    if bool(data.get('address_id')) == bool(data.get('address')): invalid('address', 'Choose a saved address or enter a new one.')
    if data.get('address_id'):
        address = get_row(Address, data['address_id'])
        if address.customer_id != g.customer.id: fail(404, 'NOT_FOUND', 'Not found.')
        address = {key: getattr(address, key) for key in ADDRESS}
    else:
        address = data['address']
        if not isinstance(address, dict): invalid('address', 'Enter a delivery address.')
        assign(Address(), address, ADDRESS, ADDRESS - {'line2', 'landmark'})
    text_value(address['full_name'], 'full_name', 2, 80)
    text_value(address['line1'], 'line1', 5, 120)
    if address['state'] not in STATES: invalid('state', 'Choose an Indian state or union territory.')
    if len(address['phone']) != 10 or not address['phone'].isascii() or not address['phone'].isdigit(): invalid('phone', 'Enter a 10-digit mobile number.')
    value = quote(cart, address['pincode'])
    if data['quote_id'] != value['quote_id']: fail(409, 'QUOTE_CHANGED', 'Prices or availability changed. Review the refreshed total.')
    try: delivery = date.fromisoformat(data['delivery_date'])
    except (ValueError, TypeError): invalid('delivery_date', 'Pick a delivery date.')
    if delivery not in value['delivery_dates']: invalid('delivery_date', 'Choose an available delivery date.')
    method = data['payment_method']
    if method not in {'cod', 'upi', 'card'}: invalid('payment_method', 'Choose UPI, card or COD.')
    if method == 'cod' and not value['cart']['cod_allowed']: invalid('payment_method', 'COD is unavailable for this delivery.')
    backend = 'cod' if method == 'cod' else current_app.config['PAYMENT_BACKEND']
    if backend not in {'cod', 'demo', 'razorpay'}: fail(503, 'PAYMENT_UNAVAILABLE', 'Online payments are not configured yet. Choose COD if available.')
    if backend == 'razorpay' and not all(current_app.config.get(key) for key in ('RAZORPAY_KEY_ID', 'RAZORPAY_KEY_SECRET', 'RAZORPAY_WEBHOOK_SECRET', 'PUBLIC_API_URL')):
        fail(503, 'PAYMENT_UNAVAILABLE', 'Online payments are not configured yet.')
    notes = text_value(data.get('customer_notes', ''), 'customer_notes', 0, 200)
    row = Order(order_number='GS-' + str(uuid4().int)[:18], customer_id=g.customer.id, address=address, pincode=address['pincode'], delivery_date=delivery,
                payment_method=method, status='confirmed' if method == 'cod' else 'pending_payment', payment_status='cod' if method == 'cod' else 'pending',
                subtotal=value['cart']['subtotal'], shipping=value['shipping'], gst=value['cart']['included_gst'], grand_total=value['grand_total'], customer_notes=notes)
    db.session.add(row)
    db.session.flush()
    for line in list(cart.lines):
        line.variant.stock_qty -= line.qty
        db.session.add_all([StockReservation(order_id=row.id, variant_id=line.variant_id, qty=line.qty),
                            OrderLine(order=row, product_name=line.product.name, variant_label=line.variant.pack_label, sku=line.variant.sku, qty=line.qty, unit_price=line.unit_price)])
        db.session.delete(line)
    payment = Payment(order=row, method=method, status='cod_pending' if method == 'cod' else 'pending', amount=row.grand_total)
    db.session.add_all([payment, CheckoutSession(order=row, customer_id=g.customer.id, request_id=key, request_hash=digest(data), backend=backend, expires_at=now() + timedelta(minutes=30))])
    db.session.flush()
    if method == 'cod': order_changed(row)
    return respond({'order': detail(row), 'payment': json_value(payment)}, 201)


@api.post('/orders/<number>/cancel')
@require()
def cancel(number):
    row = owned_order(number)
    cancel_order(row)
    return respond(detail(row))


def expire_payments():
    rows = db.session.scalars(select(Order).join(CheckoutSession).where(Order.status == 'pending_payment', CheckoutSession.expires_at <= now())
                              .order_by(Order.id).with_for_update(of=Order, skip_locked=True)).all()
    for row in rows:
        row.status = 'cancelled'
        release(row)
        order_changed(row)
    db.session.commit()
    return len(rows)


def install_checkout_commands(app):
    # Free web hosts can sleep. Release expired reservations when traffic resumes.
    from threading import Lock
    from time import monotonic
    sweep_lock, last_sweep = Lock(), [0.0]

    @app.before_request
    def sweep_expired():
        if app.testing or monotonic() - last_sweep[0] < 60 or not sweep_lock.acquire(blocking=False): return
        try:
            expire_payments()
            last_sweep[0] = monotonic()
        finally: sweep_lock.release()

    @app.cli.command('expire-payments')
    def expire():
        """Release inventory for unpaid checkouts older than 30 minutes."""
        click.echo(f'Expired {expire_payments()} unpaid orders.')

    @app.cli.command('dispatch-refunds')
    def refunds():
        """Submit queued refunds to the configured payment provider."""
        from .payments import dispatch_refunds
        click.echo(dispatch_refunds())


from . import payments  # noqa: E402,F401
