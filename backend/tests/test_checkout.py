import hashlib
import hmac
import json
from datetime import timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select

from backend.checkout import expire_payments, now
from backend.extensions import db
from backend.models import CheckoutSession, Order, PushMessage, Variant
from backend.payments import dispatch_refunds
from backend.tests.test_api import app, setup, call, login, address_payload


@pytest.fixture(autouse=True)
def config(app):
    original = app.config.copy()
    app.config.update(PAYMENT_BACKEND='demo', SHIPPING_FEE='49', FREE_SHIPPING_THRESHOLD='999', CONTACT_BACKEND='demo')
    yield
    app.config.update(original)


def prepare(setup, method='upi'):
    client, ids = setup
    auth, _ = login(client)
    call(client, 'POST', '/cart/lines', dict(variant_id=ids['variant'], qty=2), auth, 201)
    quote = call(client, 'POST', '/checkout/quote', {'pincode': '400001'}, auth)
    data = dict(request_id=str(uuid4()), quote_id=quote['quote_id'], address={key: value for key, value in address_payload().items() if key != 'is_default'},
                delivery_date=quote['delivery_dates'][0], payment_method=method)
    return client, ids, auth, quote, data


def test_checkout_retry_totals_snapshot_stock_and_cancellation(setup, app):
    client, ids, auth, quote, data = prepare(setup)
    assert quote['grand_total'] == '249.50' and quote['cart']['included_gst'] == '9.55'
    order = call(client, 'POST', '/checkout', data, auth, 201)['order']
    assert order['status'] == 'pending_payment' and order['address']['line1'] == data['address']['line1']
    assert call(client, 'POST', '/checkout', data, auth)['order']['id'] == order['id']
    call(client, 'POST', '/checkout', {**data, 'customer_notes': 'changed'}, auth, 409)
    assert call(client, 'GET', '/checkout/attempts/' + data['request_id'], headers=auth)['order']['id'] == order['id']
    assert call(client, 'GET', '/cart', headers=auth)['lines'] == []
    path = '/orders/' + order['order_number']
    call(client, 'POST', path + '/cancel', {}, auth, 422)
    assert call(client, 'POST', path + '/demo-payment', {'outcome': 'failure'}, auth)['payment_status'] == 'failed'
    assert call(client, 'POST', path + '/demo-payment', {'outcome': 'success'}, auth)['status'] == 'confirmed'
    call(client, 'POST', path + '/demo-payment', {'outcome': 'success'}, auth)
    with app.app_context():
        assert db.session.get(Variant, ids['variant']).stock_qty == 13
        assert len(db.session.scalars(select(PushMessage)).all()) == 1
    cancelled = call(client, 'POST', path + '/cancel', {}, auth)
    assert cancelled['status'] == 'cancelled' and cancelled['refund']['status'] == 'pending'
    call(client, 'POST', path + '/cancel', {}, auth, 422)
    with app.app_context():
        assert db.session.get(Variant, ids['variant']).stock_qty == 15
        assert dispatch_refunds()['handled'] == 1
    assert call(client, 'GET', path, headers=auth)['refund']['status'] == 'processed'


def test_checkout_changed_price_date_coverage_and_cod(setup, app):
    with app.app_context():
        db.session.get(Variant, setup[1]['variant']).cod_allowed = False
        db.session.commit()
    client, ids, auth, quote, data = prepare(setup, 'cod')
    call(client, 'POST', '/checkout', {**data, 'delivery_date': '2000-01-01'}, auth, 400)
    call(client, 'POST', '/checkout', {**data, 'address': {**data['address'], 'pincode': '999999'}}, auth, 422)
    call(client, 'POST', '/checkout', data, auth, 400)
    with app.app_context():
        variant = db.session.get(Variant, ids['variant'])
        variant.cod_allowed, variant.price = True, 110
        db.session.commit()
    call(client, 'POST', '/checkout', data, auth, 409)
    updated = call(client, 'POST', '/checkout/quote', {'pincode': '400001'}, auth)
    order = call(client, 'POST', '/checkout', {**data, 'quote_id': updated['quote_id']}, auth, 201)['order']
    assert order['status'] == 'confirmed' and order['payment_status'] == 'cod' and order['grand_total'] == '269.00'
    admin, _ = login(client, 'admin')
    call(client, 'POST', '/admin/orders/' + order['id'] + '/status', {'status': 'cancelled'}, admin)
    with app.app_context(): assert db.session.get(Variant, ids['variant']).stock_qty == 15


def test_expiry_releases_stock_once_and_blocks_payment(setup, app):
    client, ids, auth, _, data = prepare(setup)
    order = call(client, 'POST', '/checkout', data, auth, 201)['order']
    with app.app_context():
        db.session.get(CheckoutSession, order['id']).expires_at = now() - timedelta(seconds=1)
        db.session.commit()
        assert expire_payments() == 1
        assert expire_payments() == 0
        assert db.session.get(Variant, ids['variant']).stock_qty == 15
    call(client, 'POST', '/orders/' + order['order_number'] + '/demo-payment', {'outcome': 'success'}, auth, 422)


def test_signed_gateway_webhook_amount_checks_replay_and_late_capture(setup, app):
    client, ids, auth, _, data = prepare(setup)
    order = call(client, 'POST', '/checkout', data, auth, 201)['order']
    with app.app_context():
        session = db.session.get(CheckoutSession, order['id'])
        session.backend, session.gateway_order_id = 'razorpay', 'order_test'
        session.expires_at = now() - timedelta(seconds=1)
        db.session.commit()
    app.config['RAZORPAY_WEBHOOK_SECRET'] = 'test-webhook-secret'
    event = {'event': 'payment.captured', 'payload': {'payment': {'entity': dict(id='pay_test', order_id='order_test', amount=24950, currency='INR', method='upi', status='captured')}}}
    def send(event, signature=True):
        raw = json.dumps(event).encode()
        return client.post('/api/v1/payments/gateway-webhook', data=raw, content_type='application/json', headers={'X-Razorpay-Signature': hmac.new(b'test-webhook-secret', raw, hashlib.sha256).hexdigest() if signature else 'bad'})
    assert send(event, False).status_code == 403
    event['payload']['payment']['entity']['amount'] = 1
    assert send(event).status_code == 400
    event['payload']['payment']['entity']['amount'] = 24950
    assert send(event).status_code == send(event).status_code == 200
    detail = call(client, 'GET', '/orders/' + order['order_number'], headers=auth)
    assert detail['status'] == 'cancelled' and detail['payment_status'] == 'paid' and detail['refund']['status'] == 'pending'
    with app.app_context(): assert db.session.get(Variant, ids['variant']).stock_qty == 15


def test_checkout_ownership_and_contact_validation(setup, app):
    client, _, auth, _, data = prepare(setup)
    order = call(client, 'POST', '/checkout', data, auth, 201)['order']
    other = call(client, 'POST', '/auth/signup', dict(full_name='Another Shopper', email='checkout@example.com', phone='9876500111', password='test-password'), status=201)
    second = {'Authorization': 'Bearer ' + other['access_token']}
    for suffix, method in [('', 'GET'), ('/cancel', 'POST'), ('/demo-payment', 'POST'), ('/payment-session', 'POST')]:
        call(client, method, '/orders/' + order['order_number'] + suffix, {'outcome': 'success'} if method == 'POST' else None, second, 404)
    assert call(client, 'GET', '/checkout/attempts/' + data['request_id'], headers=second)['order'] is None
    call(client, 'POST', '/contact', dict(full_name='Test Shopper', email='invalid', message='A delivery question'), status=400)
    assert call(client, 'POST', '/contact', dict(full_name='Test Shopper', email='test@example.com', message='A delivery question'))['demo']
    app.config['CONTACT_BACKEND'] = 'disabled'
    call(client, 'POST', '/contact', dict(full_name='Test Shopper', email='test@example.com', message='A delivery question'), status=503)


def test_provider_session_recovers_existing_receipt_and_callback_capture(setup, app, monkeypatch):
    client, _, auth, _, data = prepare(setup, 'card')
    order = call(client, 'POST', '/checkout', data, auth, 201)['order']
    app.config.update(RAZORPAY_KEY_ID='rzp_test_example', RAZORPAY_KEY_SECRET='test-secret', PUBLIC_API_URL='https://api.example')
    with app.app_context():
        db.session.get(CheckoutSession, order['id']).backend = 'razorpay'
        db.session.commit()
    calls = []
    def provider(path, data=None):
        calls.append(path)
        if path.startswith('orders?receipt='): return {'items': [dict(id='order_recovered', amount=24950, currency='INR')]}
        assert path == 'payments/pay_captured'
        return dict(id='pay_captured', order_id='order_recovered', amount=24950, currency='INR', method='card', status='captured')
    monkeypatch.setattr('backend.payments.gateway', provider)
    path = '/orders/' + order['order_number'] + '/payment-session'
    session = call(client, 'POST', path, {}, auth)
    call(client, 'POST', path, {}, auth)
    assert len(calls) == 1  # Recovery never creates a second provider order.
    page = client.get(session['url'].replace('https://api.example', ''))
    assert page.status_code == 200 and b'show_default_blocks' in page.data and b'test-secret' not in page.data
    signature = hmac.new(b'test-secret', b'order_recovered|pay_captured', hashlib.sha256).hexdigest()
    response = client.post('/api/v1/payments/callback', data=dict(razorpay_order_id='order_recovered', razorpay_payment_id='pay_captured', razorpay_signature=signature))
    assert response.status_code == 200
    assert call(client, 'GET', '/orders/' + order['order_number'], headers=auth)['status'] == 'confirmed'


def test_two_customers_cannot_purchase_the_same_last_stock(setup, app):
    from concurrent.futures import ThreadPoolExecutor
    client, ids, auth, _, first = prepare(setup)
    with app.app_context():
        db.session.get(Variant, ids['variant']).stock_qty = 3
        db.session.commit()
    other = call(client, 'POST', '/auth/signup', dict(full_name='Second Buyer', email='stock@example.com', phone='9876500222', password='test-password'), status=201)
    second_auth = {'Authorization': 'Bearer ' + other['access_token']}
    call(client, 'POST', '/cart/lines', dict(variant_id=ids['variant'], qty=2), second_auth, 201)
    quote = call(client, 'POST', '/checkout/quote', {'pincode': '400001'}, second_auth)
    second = {**first, 'request_id': str(uuid4()), 'quote_id': quote['quote_id']}
    def place(values):
        headers, payload = values
        with app.test_client() as client: return client.post('/api/v1/checkout', json=payload, headers=headers).status_code
    with ThreadPoolExecutor(max_workers=2) as pool: statuses = list(pool.map(place, [(auth, first), (second_auth, second)]))
    assert sorted(statuses) == [201, 422]
    with app.app_context():
        assert db.session.get(Variant, ids['variant']).stock_qty == 1
        assert len(db.session.scalars(select(Order)).all()) == 1
