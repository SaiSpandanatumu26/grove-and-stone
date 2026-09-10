from uuid import uuid4

from backend.extensions import db
from backend.models import Product, Variant
from backend.tests.test_api import app, setup, call, login
from backend.tests.test_checkout import prepare


def test_stock_follows_inventory_reservations_and_cancellation(setup, app):
    client, ids = setup
    admin, _ = login(client, 'admin')
    check = lambda: call(client, 'POST', '/stock/check', {'product_ids': [ids['product']]})['items'][0]['variants'][0]['stock_qty']
    assert check() == 15
    call(client, 'PATCH', '/admin/inventory', {'items': [{'variant_id': ids['variant'], 'stock_qty': 2}]}, admin)
    assert check() == 2
    original = app.config.copy()
    try:
        app.config.update(SHIPPING_FEE='49', FREE_SHIPPING_THRESHOLD='999')
        client, _, auth, _, data = prepare(setup, 'cod')
        assert check() == 2  # Adding to cart does not reserve inventory.
        order = call(client, 'POST', '/checkout', data, auth, 201)['order']
        assert check() == 0
        call(client, 'POST', '/orders/' + order['order_number'] + '/cancel', {}, auth)
        assert check() == 2
    finally: app.config.update(original)


def test_stock_missing_inactive_and_season_changes_are_explicit(setup, app):
    client, ids = setup
    missing = str(uuid4())
    path = '/api/v1/stock/check'
    response = client.post(path, json={'product_ids': [ids['product'], missing, ids['product']]})
    result = response.get_json()
    assert response.status_code == 200 and response.headers['Cache-Control'] == 'no-store'
    assert len(result['items']) == 2 and result['checked_at'].endswith('Z') and result['poll_after_seconds'] == 5
    assert result['items'][1] == dict(id=missing, is_active=False, season_status='off_season', variants=[])
    assert set(result['items'][0]['variants'][0]) == {'id', 'stock_qty'}
    with app.app_context():
        db.session.get(Product, ids['product']).season_status = 'off_season'
        db.session.commit()
    assert call(client, 'POST', '/stock/check', {'product_ids': [ids['product']]})['items'][0]['season_status'] == 'off_season'
    with app.app_context():
        db.session.get(Product, ids['product']).is_active = False
        db.session.commit()
    assert call(client, 'POST', '/stock/check', {'product_ids': [ids['product']]})['items'][0]['variants'] == []


def test_stock_input_is_bounded_and_read_only(setup, app):
    client, ids = setup
    for value in [[], [str(uuid4())] * 101, ['invalid'], 'invalid', [None]]:
        call(client, 'POST', '/stock/check', {'product_ids': value}, status=400)
    call(client, 'POST', '/stock/check', {'product_ids': [ids['product']], 'stock_qty': 999}, status=400)
    with app.app_context(): assert db.session.get(Variant, ids['variant']).stock_qty == 15
