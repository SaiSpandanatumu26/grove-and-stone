"""Owner access, durable notifications and safe delivery rollout integration tests."""
import io
import json
from datetime import timedelta
from urllib.error import URLError

import pytest
from sqlalchemy import select, func

from backend.extensions import db
from backend.models import OwnerAlert, Order, Shipment, ShopSetting, AdminAudit, PostalArea, PincodeService
from backend.notifications import order_changed
from backend.operations import dispatch_owner_alerts, now
from backend.tests.test_api import app, setup, call, login
from backend.tests.test_checkout import prepare


@pytest.fixture(autouse=True)
def settings(app):
    original = app.config.copy()
    app.config.update(PAYMENT_BACKEND='demo', SHIPPING_FEE='49', FREE_SHIPPING_THRESHOLD='999')
    yield
    app.config.update(original)


def placed(setup):
    client, ids, auth, quote, data = prepare(setup, 'cod')
    return client, auth, call(client, 'POST', '/checkout', data, auth, 201)['order']


def test_owner_inbox_is_private_durable_and_idempotent(setup, app):
    client, customer, order = placed(setup)
    admin, _ = login(client, 'admin')
    call(client, 'GET', '/admin/alerts', headers=customer, status=403)
    call(client, 'GET', '/admin/alerts', status=401)
    with app.app_context():
        row = db.session.get(Order, order['id'])
        order_changed(row)
        db.session.commit()
    alerts = call(client, 'GET', '/admin/alerts', headers=admin)
    assert alerts['total'] == 1 and alerts['unread'] == 1
    key = alerts['items'][0]['id']
    call(client, 'POST', '/admin/alerts/' + key + '/read', {}, admin)
    assert call(client, 'GET', '/admin/alerts', headers=admin)['unread'] == 0
    call(client, 'POST', '/orders/' + order['order_number'] + '/cancel', {}, customer)
    assert call(client, 'GET', '/admin/alerts', headers=admin)['total'] == 2


def test_owner_email_retry_and_provider_idempotency(setup, app, monkeypatch):
    placed(setup)
    app.config.update(RESEND_API_KEY='test-secret', CONTACT_FROM='Store <store@example.com>')
    with app.app_context():
        db.session.add_all([ShopSetting(key='owner_email', value='owner@example.com'), ShopSetting(key='email_alerts_enabled', value=True)])
        db.session.commit()
        monkeypatch.setattr('backend.operations.urlopen', lambda *a, **k: (_ for _ in ()).throw(URLError('offline')))
        assert dispatch_owner_alerts()['failed'] == 1
        row = db.session.scalar(select(OwnerAlert))
        assert row.sent_at is None and row.attempts == 1
        row.next_attempt_at = now() - timedelta(seconds=1)
        db.session.commit()
        requests = []
        def send(req, **kwargs):
            requests.append(req)
            return io.BytesIO(b'{"id":"email-receipt"}')
        monkeypatch.setattr('backend.operations.urlopen', send)
        assert dispatch_owner_alerts()['sent'] == 1
        assert dispatch_owner_alerts()['sent'] == 0
        assert requests[0].get_header('Idempotency-key') == 'owner-alert-' + str(row.id)
        payload = json.loads(requests[0].data)
        assert payload['to'] == ['owner@example.com'] and 'line1' not in payload['text']


def test_shipment_cod_collection_and_audit(setup, app):
    client, customer, order = placed(setup)
    staff, _ = login(client, 'packer')
    path = '/admin/orders/' + order['id']
    call(client, 'POST', path + '/collect-cod', {'amount': order['grand_total']}, staff, 422)
    call(client, 'PUT', path + '/shipment', dict(carrier='Delivery team', tracking_number='ABC-123', tracking_url='javascript:alert(1)'), staff, 400)
    call(client, 'PUT', path + '/shipment', dict(carrier='Delivery team', tracking_number='ABC-123', tracking_url='https://example.com/tracking/123'), staff)
    detail = call(client, 'GET', '/orders/' + order['order_number'], headers=customer)
    assert detail['shipment']['tracking_number'] == 'ABC-123'
    for status in ('packed', 'shipped', 'delivered'): call(client, 'POST', path + '/status', {'status': status}, staff)
    call(client, 'POST', path + '/collect-cod', {'amount': '1.00'}, staff, 400)
    assert call(client, 'POST', path + '/collect-cod', {'amount': order['grand_total']}, staff)['payment_status'] == 'paid'
    with app.app_context(): assert db.session.scalar(select(func.count()).select_from(AdminAudit)) >= 5


def test_staff_role_scope_revocation_and_logout(setup):
    client, _ = setup
    admin, _ = login(client, 'admin')
    packer, _ = login(client, 'packer')
    for path in ('settings', 'staff', 'postal-directory', 'banners', 'audit', 'refunds'):
        call(client, 'GET', '/admin/' + path, headers=packer, status=403)
    user = call(client, 'POST', '/admin/staff', dict(name='Operations', email='ops@example.com', password='long-staff-password', role='packer', is_active=True), admin, 201)
    result = call(client, 'POST', '/admin/auth/login', dict(email='ops@example.com', password='long-staff-password'))
    auth = {'Authorization': 'Bearer ' + result['access_token']}
    call(client, 'PATCH', '/admin/staff/' + user['id'], {'is_active': False}, admin)
    call(client, 'GET', '/admin/dashboard', headers=auth, status=401)
    call(client, 'POST', '/admin/auth/logout', {}, packer, 204)
    call(client, 'GET', '/admin/dashboard', headers=packer, status=401)


def test_delivery_csv_import_rolls_back_invalid_rows(setup, app):
    client, _ = setup
    admin, _ = login(client, 'admin')
    header = 'pincode,city,state,serviceable,mango_eligible,delivery_days_min,delivery_days_max,cod_allowed\n'
    good = '500001,Hyderabad,Telangana,true,true,1,3,true\n'
    bad = '500002,Town,Telangana,false,true,1,3,false\n'
    call(client, 'POST', '/admin/pincodes/import', {'csv': header + good + bad}, admin, 400)
    with app.app_context(): assert db.session.get(PincodeService, '500001') is None
    assert call(client, 'POST', '/admin/pincodes/import', {'csv': header + good}, admin)['imported'] == 1
    rows = call(client, 'GET', '/admin/pincodes?search=Hyderabad', headers=admin)
    assert rows['total'] == 1 and rows['items'][0]['pincode'] == '500001'


def test_postal_directory_does_not_enable_delivery(setup, app, tmp_path):
    path = tmp_path / 'directory.csv'
    path.write_text('pincode,district,state,office\n500001,Hyderabad,Telangana,Hyderabad GPO\n500001,Hyderabad,Telangana,Abids\n', encoding='utf-8')
    result = app.test_cli_runner().invoke(args=['import-postal-directory', str(path), '--source', 'https://www.indiapost.gov.in/rti/pincodelist'])
    assert result.exit_code == 0, result.output
    with app.app_context():
        assert len(db.session.get(PostalArea, '500001').offices) == 2
        assert db.session.get(PincodeService, '500001') is None


def test_shop_cannot_open_with_unreviewed_coverage(setup, app):
    client, _ = setup
    admin, _ = login(client, 'admin')
    call(client, 'PATCH', '/admin/settings', {'orders_enabled': True}, admin, 422)
    call(client, 'PATCH', '/admin/settings', {'orders_enabled': False}, admin)
    # Even the existing sample coverage cannot bypass a closed shop.
    from backend.tests.test_api import guest
    with app.app_context(): assert db.session.get(ShopSetting, 'orders_enabled').value is False
    customer, _ = login(client)
    call(client, 'POST', '/checkout/quote', {'pincode': '400001'}, customer, 503)
    result = call(client, 'PATCH', '/admin/settings', dict(business_name='Grove and Stone', business_address='Owner supplied address', support_email='support@example.com',
                 coverage_reviewed=True, catalog_reviewed=True, policies_reviewed=True, orders_enabled=True), admin)
    assert result['readiness']['orders_enabled'] is True
    assert 'RAZORPAY_KEY_SECRET' not in json.dumps(result)


def test_admin_html_security_and_asset_paths(setup):
    client, _ = setup
    response = client.get('/admin')
    assert response.status_code == 200 and b'Owner workspace' in response.data
    assert "frame-ancestors 'none'" in response.headers['Content-Security-Policy']
    assert client.get('/admin/app.js').mimetype in {'text/javascript', 'application/javascript'}
    assert b'DATABASE_URL' not in client.get('/admin/../../.env').data


def test_owner_invitation_is_one_use_and_expiring(setup, app):
    from backend.models import AdminInvite
    client, _ = setup
    result = app.test_cli_runner().invoke(args=['invite-owner', '--email', 'invited@example.com', '--name', 'Invited owner', '--url', 'https://api.example.com'])
    assert result.exit_code == 0, result.output
    token = result.output.strip().split('#invite=')[1]
    call(client, 'POST', '/admin/auth/activate', {'token': token, 'password': 'short'}, status=400)
    result = call(client, 'POST', '/admin/auth/activate', {'token': token, 'password': 'private-owner-password'}, status=201)
    assert result['admin']['email'] == 'invited@example.com'
    call(client, 'POST', '/admin/auth/activate', {'token': token, 'password': 'private-owner-password'}, status=403)
    with app.app_context():
        row = db.session.scalar(select(AdminInvite))
        assert row.token_digest != token and row.used_at is not None


def test_public_postal_search_is_bounded_without_enabling_coverage(setup, app):
    client, _ = setup
    with app.app_context():
        db.session.add(PostalArea(pincode='500001', district='Hyderabad', state='Telangana', offices=['Abids', 'Hyderabad GPO'], source='https://www.geonames.org/'))
        db.session.commit()
    result = call(client, 'GET', '/delivery/places?q=Abids')
    assert result['items'][0]['pincode'] == '500001' and not result['items'][0]['serviceable']
    assert call(client, 'GET', '/delivery/places?q=%25%25')['items'] == []
