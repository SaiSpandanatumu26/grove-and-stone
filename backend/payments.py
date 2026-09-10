"""Razorpay hosted checkout and signed callbacks; isolated local payment simulator."""
import base64
import hashlib
import hmac
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import current_app, render_template_string, request
from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlalchemy import select

from .api import api, body, fail, respond
from .auth import require
from .checkout import detail, now, owned_order, release
from .extensions import db, limiter
from .models import CheckoutSession, Order, RefundRequest
from .notifications import order_changed


def gateway(path, data=None):
    config = current_app.config
    credentials = base64.b64encode(f"{config['RAZORPAY_KEY_ID']}:{config['RAZORPAY_KEY_SECRET']}".encode()).decode()
    req = Request('https://api.razorpay.com/v1/' + path, data=json.dumps(data).encode() if data is not None else None,
                  headers={'Authorization': 'Basic ' + credentials, 'Content-Type': 'application/json'})
    try:
        with urlopen(req, timeout=10) as response: return json.load(response)
    except (HTTPError, URLError, TimeoutError, ValueError): fail(503, 'PAYMENT_PROVIDER_UNAVAILABLE', 'The payment provider could not respond. Try again; your order is saved.')


def signer(): return URLSafeTimedSerializer(current_app.secret_key, salt='payment-checkout')
def signed(value, signature, secret):
    return bool(secret and signature) and hmac.compare_digest(hmac.new(secret.encode(), value, hashlib.sha256).hexdigest(), signature)


def apply_capture(row, payment):
    session = db.session.get(CheckoutSession, row.id)
    if (payment.get('order_id') != session.gateway_order_id or payment.get('amount') != int(row.grand_total * 100)
            or payment.get('currency') != 'INR' or payment.get('status') != 'captured' or payment.get('method') != row.payment_method):
        fail(400, 'PAYMENT_MISMATCH', 'Payment details do not match the order.')
    if session.gateway_payment_id:
        if session.gateway_payment_id != payment['id']: fail(409, 'PAYMENT_CONFLICT', 'This order already has a different payment. Contact support.')
        return
    session.gateway_payment_id = payment['id']
    row.payment_status, row.payments[0].status, row.payments[0].gateway_ref = 'paid', 'paid', payment['id']
    if row.status == 'cancelled' or session.expires_at <= now():
        row.status = 'cancelled'
        release(row)
        if not db.session.get(RefundRequest, row.id): db.session.add(RefundRequest(order_id=row.id, amount=row.grand_total))
    else: row.status = 'confirmed'
    order_changed(row)


@api.post('/orders/<number>/payment-session')
@require()
def payment_session(number):
    row = owned_order(number)
    session = db.session.get(CheckoutSession, row.id)
    if not session or row.status != 'pending_payment': fail(422, 'PAYMENT_UNAVAILABLE', 'This order is not awaiting payment.')
    if session.expires_at <= now(): fail(422, 'PAYMENT_EXPIRED', 'This payment window has expired. Please start a new cart.')
    if session.backend == 'demo': return respond({'backend': 'demo'})
    if session.backend != 'razorpay': fail(422, 'PAYMENT_UNAVAILABLE', 'This order does not use online payment.')
    if not session.gateway_order_id:
        # The unique receipt lets a retry recover a provider order after an uncertain timeout.
        matches = gateway('orders?receipt=' + row.id.hex)['items']
        provider = matches[0] if matches else gateway('orders', dict(amount=int(row.grand_total * 100), currency='INR', receipt=row.id.hex))
        if provider['amount'] != int(row.grand_total * 100) or provider['currency'] != 'INR': fail(409, 'PAYMENT_MISMATCH', 'Payment order mismatch.')
        session.gateway_order_id = provider['id']
    token = signer().dumps(str(row.id))
    return respond({'backend': 'razorpay', 'url': current_app.config['PUBLIC_API_URL'].rstrip('/') + '/api/v1/pay/' + token})


@api.get('/pay/<token>')
@limiter.limit('30/minute')
def hosted_payment(token):
    try: key = signer().loads(token, max_age=1800)
    except BadSignature: fail(403, 'LINK_EXPIRED', 'Open payment again from your order.')
    from .api import uid
    row = db.session.get(Order, uid(key))
    session = db.session.get(CheckoutSession, row.id) if row else None
    if not session or session.backend != 'razorpay' or row.status != 'pending_payment' or session.expires_at <= now(): fail(422, 'PAYMENT_UNAVAILABLE', 'This payment window is closed. Return to your order.')
    options = dict(key=current_app.config['RAZORPAY_KEY_ID'], amount=int(row.grand_total * 100), currency='INR', name='Grove & Stone', order_id=session.gateway_order_id,
                   callback_url=current_app.config['PUBLIC_API_URL'].rstrip('/') + '/api/v1/payments/callback', redirect=True,
                   config={'display': {'blocks': {'chosen': {'name': 'Pay via ' + row.payment_method.upper(), 'instruments': [{'method': row.payment_method}]}},
                                       'sequence': ['block.chosen'], 'preferences': {'show_default_blocks': False}}})
    return render_template_string('''<!doctype html><html lang="en"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Grove & Stone payment</title>
    <body style="font:18px system-ui;max-width:560px;margin:60px auto;padding:24px;background:#fffaf2"><h1>Complete your payment</h1>
    <p>Your card or UPI details are handled by Razorpay. Return to Grove & Stone after payment and refresh your order.</p>
    <button id="pay" style="padding:16px;background:#ec650e;color:white;border:0;border-radius:8px">Open secure payment</button>
    <script src="https://checkout.razorpay.com/v1/checkout.js"></script><script>const checkout = new Razorpay({{ options|tojson }});document.getElementById('pay').onclick=()=>checkout.open();</script></body></html>''', options=options)


@api.post('/payments/callback')
@limiter.limit('60/minute')
def callback():
    order_id, payment_id = request.form.get('razorpay_order_id', ''), request.form.get('razorpay_payment_id', '')
    session = db.session.scalar(select(CheckoutSession).where(CheckoutSession.gateway_order_id == order_id, CheckoutSession.backend == 'razorpay'))
    if not session or not signed((order_id + '|' + payment_id).encode(), request.form.get('razorpay_signature', ''), current_app.config['RAZORPAY_KEY_SECRET']):
        fail(403, 'INVALID_SIGNATURE', 'Payment signature could not be verified.')
    row = db.session.scalar(select(Order).where(Order.id == session.order_id).with_for_update())
    payment = gateway('payments/' + payment_id)
    if payment.get('status') == 'captured': apply_capture(row, payment)
    return '<!doctype html><title>Grove & Stone</title><p>Payment received for verification. Return to Grove &amp; Stone and refresh your order to see its status.</p>'


@api.post('/payments/gateway-webhook')
def webhook():
    if not signed(request.get_data(), request.headers.get('X-Razorpay-Signature', ''), current_app.config['RAZORPAY_WEBHOOK_SECRET']):
        fail(403, 'INVALID_SIGNATURE', 'Invalid webhook signature.')
    event = request.get_json()
    payload = event.get('payload', {})
    payment = payload.get('payment', {}).get('entity', {})
    if payment.get('order_id'):
        session = db.session.scalar(select(CheckoutSession).where(CheckoutSession.gateway_order_id == payment['order_id'], CheckoutSession.backend == 'razorpay'))
        if session:
            row = db.session.scalar(select(Order).where(Order.id == session.order_id).with_for_update())
            if event.get('event') in {'payment.captured', 'order.paid'}: apply_capture(row, payment)
            elif event.get('event') == 'payment.failed' and row.status == 'pending_payment' and row.payment_status != 'paid':
                row.payment_status, row.payments[0].status = 'failed', 'failed'
    refund = payload.get('refund', {}).get('entity', {})
    if event.get('event') == 'refund.processed' and refund.get('id'):
        job = db.session.scalar(select(RefundRequest).where(RefundRequest.gateway_ref == refund['id']).with_for_update())
        if job and refund.get('amount') == int(job.amount * 100): job.status = 'processed'
    return respond({'received': True})


@api.post('/orders/<number>/demo-payment')
@require()
def demo_payment(number):
    row = owned_order(number)
    session = db.session.get(CheckoutSession, row.id)
    if current_app.config['PAYMENT_BACKEND'] != 'demo' or not session or session.backend != 'demo': fail(404, 'NOT_FOUND', 'Not found.')
    outcome = body({'outcome'}, {'outcome'})['outcome']
    if outcome not in {'success', 'failure'}: fail(400, 'VALIDATION_ERROR', 'Choose success or failure.')
    if row.payment_status == 'paid': return respond(detail(row))
    if row.status != 'pending_payment' or session.expires_at <= now(): fail(422, 'PAYMENT_EXPIRED', 'The payment window is closed.')
    if outcome == 'success':
        session.gateway_order_id = 'demo_order_' + row.id.hex
        apply_capture(row, dict(id='demo_pay_' + row.id.hex, order_id=session.gateway_order_id, amount=int(row.grand_total * 100), currency='INR', status='captured', method=row.payment_method))
    else: row.payment_status, row.payments[0].status = 'failed', 'failed'
    return respond(detail(row))


def dispatch_refunds():
    count = 0
    jobs = db.session.scalars(select(RefundRequest).where(RefundRequest.status != 'processed').order_by(RefundRequest.order_id).with_for_update(skip_locked=True)).all()
    for job in jobs:
        session = db.session.get(CheckoutSession, job.order_id)
        if session and session.backend == 'demo' and current_app.config['PAYMENT_BACKEND'] == 'demo': job.status, job.gateway_ref = 'processed', 'demo_refund_' + job.order_id.hex
        elif session and session.backend == 'razorpay' and session.gateway_payment_id:
            matches = gateway('payments/' + session.gateway_payment_id + '/refunds')['items']
            refund = next((item for item in matches if item.get('receipt') == job.order_id.hex), None)
            refund = refund or gateway('payments/' + session.gateway_payment_id + '/refund', dict(amount=int(job.amount * 100), receipt=job.order_id.hex))
            job.gateway_ref, job.status = refund['id'], 'processed' if refund['status'] == 'processed' else 'submitted'
        else:
            job.last_error = 'Payment metadata missing; manual reconciliation required'
            continue
        job.last_error = None
        count += 1
    db.session.commit()
    return {'handled': count}
