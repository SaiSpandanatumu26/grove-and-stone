"""Integration tests. TEST_DATABASE_URL must point to a disposable PostgreSQL database."""
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select, text

from backend import create_app
from backend.extensions import db
from backend.models import AdminUser, AuthSession, CMSBanner, Customer, DeviceToken, MangoSeason, Order, OrderLine, Payment, PincodeService, Product, PushDelivery, PushMessage, Variant


def test_cart_included_gst_is_not_added_twice(setup):
    client, ids = setup
    session = guest()
    cart = call(client, "POST", "/cart/lines", {"variant_id": ids["variant"], "qty": 3}, session, 201)
    assert cart["included_gst"] == "14.32"
    assert cart["subtotal"] == cart["total_before_shipping"] == "300.75"
    call(client, "DELETE", "/cart/lines", headers=session, status=204)
    assert call(client, "GET", "/cart", headers=session)["lines"] == []


def test_wishlist_is_private_idempotent_and_persistent(setup):
    client, ids = setup
    auth, _ = login(client)
    path = "/me/wishlist/" + ids["product"]
    call(client, "PUT", path, headers=auth)
    call(client, "PUT", path, headers=auth)
    assert len(call(client, "GET", "/me/wishlist", headers=auth)["items"]) == 1
    other = call(client, "POST", "/auth/signup", dict(full_name="Other Shopper", email="wish@example.com", phone="9876543218", password="test-password"), status=201)
    second = {"Authorization": "Bearer " + other["access_token"]}
    assert call(client, "GET", "/me/wishlist", headers=second)["items"] == []
    call(client, "DELETE", path, headers=second, status=204)
    assert len(call(client, "GET", "/me/wishlist", headers=auth)["items"]) == 1
    call(client, "DELETE", path, headers=auth, status=204)
    assert call(client, "GET", "/me/wishlist", headers=auth)["items"] == []
    call(client, "GET", "/me/wishlist", headers=guest(), status=401)


def test_hero_slides_only_include_current_published_banners(setup, app):
    client, _ = setup
    with app.app_context():
        for title, published, end in [("Current", True, date.today()), ("Draft", False, date.today()), ("Expired", True, date.today() - timedelta(days=1))]:
            db.session.add(CMSBanner(title=title, season_state="live", cta_label="Shop", cta_url="/category", image="/fruit.png", is_published=published, start_date=date.today() - timedelta(days=2), end_date=end))
        db.session.commit()
    assert [item["title"] for item in call(client, "GET", "/banners")["items"]] == ["Current"]


def test_reorder_current_prices_ownership_and_atomic_stock_failure(setup, app):
    client, ids = setup
    with app.app_context():
        variant = db.session.get(Variant, ids["variant"])
        variant.price = Decimal("125.00")
        order = Order(order_number="GS-555", customer_id=ids["customer"], status="delivered", address=address_payload(), pincode="400001", delivery_date=date.today(),
                      payment_method="cod", payment_status="paid", subtotal=Decimal("200.50"), shipping=0, gst=Decimal("9.55"), grand_total=Decimal("200.50"),
                      lines=[OrderLine(product_name="Alphonso Mango", variant_label="6 pieces", sku="MANGO-6", qty=2, unit_price=Decimal("100.25"))])
        db.session.add(order); db.session.commit()
    auth, _ = login(client)
    cart = call(client, "POST", "/orders/GS-555/reorder", {}, auth, 201)
    assert cart["subtotal"] == "250.00" and cart["lines"][0]["qty"] == 2
    with app.app_context():
        db.session.get(Variant, ids["variant"]).stock_qty = 3
        db.session.commit()
    call(client, "POST", "/orders/GS-555/reorder", {}, auth, 422)
    assert call(client, "GET", "/cart", headers=auth)["lines"][0]["qty"] == 2
    other = call(client, "POST", "/auth/signup", dict(full_name="Another Shopper", email="order@example.com", phone="9876543217", password="test-password"), status=201)
    call(client, "POST", "/orders/GS-555/reorder", {}, {"Authorization": "Bearer " + other["access_token"]}, 404)
from backend.notifications import dispatch, enqueue


@pytest.fixture(scope="module")
def app():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url: pytest.skip("Set TEST_DATABASE_URL to a disposable PostgreSQL database")
    app = create_app(dict(TESTING=True, SQLALCHEMY_DATABASE_URI=url, SECRET_KEY="integration-test-secret-32-characters", RATELIMIT_ENABLED=False,
                          PUSH_BACKEND="mock", CORS_ORIGINS=["https://shop.example"]))
    with app.app_context(): db.create_all()
    yield app
    with app.app_context(): db.engine.dispose()


@pytest.fixture()
def setup(app):
    with app.app_context():
        names = ", ".join(f'"{name}"' for name in db.metadata.tables)
        db.session.execute(text(f"TRUNCATE TABLE {names} CASCADE"))
        admin = AdminUser(name="Admin", email="admin@example.com", password="admin-test-password", role="admin", is_active=True)
        packer = AdminUser(name="Packer", email="packer@example.com", password="packer-test-password", role="packer", is_active=True)
        customer = Customer(full_name="Test Shopper", email="customer@example.com", phone="9876543210", password="customer-test-password")
        product = Product(name="Alphonso Mango", slug="alphonso", category="mango", origin="Ratnagiri", short_description="Test copy", long_description="Test body",
                          images=["/mango.jpg"], season_status="in_season", is_active=True, is_gift_eligible=False,
                          variants=[Variant(sku="MANGO-6", pack_label="6 pieces", pack_type="box", unit_count=6, price=Decimal("100.25"), gst_percent=5, stock_qty=15, is_default=True)])
        area = PincodeService(pincode="400001", city="Mumbai", state="Maharashtra", serviceable=True, mango_eligible=True, delivery_days_min=1, delivery_days_max=3, cod_allowed=True)
        db.session.add_all([admin, packer, customer, product, area])
        db.session.commit()
        ids = dict(product=str(product.id), variant=str(product.variants[0].id), customer=str(customer.id), admin=str(admin.id))
    app.extensions["mock_pushes"] = []
    return app.test_client(), ids


def call(client, method, path, data=None, headers=None, status=200):
    response = client.open("/api/v1" + path, method=method, json=data, headers=headers)
    assert response.status_code == status, (path, response.status_code, response.get_json())
    return response.get_json()


def login(client, kind="customer"):
    data = call(client, "POST", "/admin/auth/login" if kind != "customer" else "/auth/login", {"email": f"{kind}@example.com", "password": f"{kind}-test-password"})
    return {"Authorization": "Bearer " + data["access_token"]}, data


def guest(): return {"X-Session-Id": str(uuid4())}


def test_catalog_search_money_and_filter_validation(setup):
    client, ids = setup
    data = call(client, "GET", "/products")
    assert data["items"][0]["default_variant"]["price"] == "100.25"
    assert data["total"] == 1 and data["page_size"] == 20
    assert len(call(client, "GET", "/products/alphonso")["variants"]) == 1
    assert call(client, "GET", "/search?q=ratnagiri")["total"] == 1
    assert call(client, "GET", "/search?q=%25")["total"] == 0
    assert call(client, "GET", "/search?q=unknown")["items"] == []
    for path in ("/search", "/search?q=", "/products?category=bad", "/products?pack_type=bad", "/products?page_size=51", "/products?page=0", "/products?sort=bad"):
        assert call(client, "GET", path, status=400)["fields"]


def test_auth_separation_hashes_and_refresh_revocation(setup, app):
    client, _ = setup
    header, payload = login(client)
    assert "password" not in str(payload) and "scrypt" not in str(payload)
    call(client, "GET", "/admin/products", headers=header, status=403)
    admin, _ = login(client, "admin")
    call(client, "GET", "/me", headers=admin, status=403)
    assert call(client, "POST", "/auth/refresh", {"refresh_token": payload["refresh_token"]})["access_token"]
    with app.app_context():
        assert db.session.scalar(select(AuthSession).where(AuthSession.customer_id.is_not(None))).refresh_digest != payload["refresh_token"]
    call(client, "POST", "/auth/logout", headers=header, status=204)
    call(client, "GET", "/me", headers=header, status=401)
    call(client, "POST", "/auth/refresh", {"refresh_token": payload["refresh_token"]}, status=401)


def test_signup_and_validation_rollback(setup):
    client, _ = setup
    data = dict(full_name="New Customer", email="new@example.com", phone="9876543211", password=" spaced password ")
    created = call(client, "POST", "/auth/signup", data, status=201)
    assert created["customer"]["email"] == data["email"]
    call(client, "POST", "/auth/login", {"email": data["email"], "password": data["password"]})
    call(client, "POST", "/auth/signup", {**data, "email": "NEW@example.com"}, status=409)
    call(client, "POST", "/auth/signup", {**data, "role": "admin"}, status=400)
    call(client, "POST", "/auth/signup", {**data, "password": "short"}, status=400)
    assert call(client, "GET", "/products")["total"] == 1


def test_cart_ownership_quantities_and_pincode(setup):
    client, ids = setup
    first, second = guest(), guest()
    call(client, "GET", "/cart", status=401)
    call(client, "GET", "/cart", headers={"X-Session-Id": "bad"}, status=400)
    data = call(client, "POST", "/cart/lines", {"variant_id": ids["variant"], "qty": 2}, first, 201)
    assert data["subtotal"] == "200.50"
    key = data["lines"][0]["id"]
    call(client, "PATCH", f"/cart/lines/{key}", {"qty": 3}, second, 404)
    call(client, "DELETE", f"/cart/lines/{key}", headers=second, status=404)
    assert call(client, "GET", "/cart", headers=second)["lines"] == []
    for qty in (0, 21, True, "2", 1.5): call(client, "PATCH", f"/cart/lines/{key}", {"qty": qty}, first, 400)
    call(client, "PATCH", f"/cart/lines/{key}", {"qty": 16}, first, 422)
    assert call(client, "POST", "/cart/lines", {"variant_id": ids["variant"], "qty": 1}, first, 201)["lines"][0]["qty"] == 3
    data = call(client, "PUT", "/cart/pincode", {"pincode": "400001"}, first)
    assert data["cart"]["block_reason"] == "LOGIN_REQUIRED" and data["cart"]["cod_allowed"]
    assert not call(client, "GET", "/pincodes/999999")["serviceable"]
    assert call(client, "PUT", "/cart/pincode", {"pincode": "999999"}, first)["cart"]["block_reason"] == "PINCODE_NOT_SERVICEABLE"
    call(client, "DELETE", f"/cart/lines/{key}", headers=first, status=204)
    assert call(client, "GET", "/cart", headers=first)["lines"] == []


def test_cart_merge_is_bounded_and_reported(setup):
    client, ids = setup
    auth, _ = login(client)
    call(client, "POST", "/cart/lines", {"variant_id": ids["variant"], "qty": 10}, auth, 201)
    session = guest()
    call(client, "POST", "/cart/lines", {"variant_id": ids["variant"], "qty": 10}, session, 201)
    payload = call(client, "POST", "/auth/login", {"email": "customer@example.com", "password": "customer-test-password"}, session)
    assert payload["cart_merge"]["adjustments"][0]["qty"] == 15
    assert call(client, "GET", "/cart", headers=auth)["lines"][0]["qty"] == 15
    assert call(client, "GET", "/cart", headers=session)["lines"] == []


def product_payload():
    return dict(name="Mamra Almonds", slug="mamra", category="dry_fruit", origin="Kashmir", short_description="Test", long_description="Test details", images=["/almond.jpg"],
                season_status="in_season", is_gift_eligible=True, is_active=True,
                variants=[dict(sku="MAMRA-500", pack_label="500g", pack_type="weight", weight_grams=500, price="199.99", gst_percent="5", stock_qty=20, cod_allowed=True, is_default=True)])


def test_admin_product_create_edit_archive_and_packer_scope(setup):
    client, ids = setup
    admin, _ = login(client, "admin")
    packer, _ = login(client, "packer")
    call(client, "POST", "/admin/products", product_payload(), packer, 403)
    call(client, "GET", "/admin/products", headers=packer, status=403)
    data = call(client, "POST", "/admin/products", product_payload(), admin, 201)
    path, variant_id = "/admin/products/" + data["id"], data["variants"][0]["id"]
    updated = call(client, "PATCH", path, {"variants": [{"id": variant_id, "price": "210.00"}]}, admin)
    assert updated["variants"][0]["is_default"] and updated["variants"][0]["price"] == "210.00"
    call(client, "PATCH", path, {"variants": []}, admin, 400)
    call(client, "PATCH", path, {"variants": [{"id": ids["variant"], "is_default": True}]}, admin, 400)
    call(client, "PATCH", path, {"is_active": False}, admin)
    call(client, "GET", "/products/mamra", status=404)
    assert call(client, "GET", "/admin/products?search=MAMRA-500", headers=admin)["total"] == 1
    call(client, "DELETE", path, headers=admin, status=405)


def test_inventory_and_server_price_source(setup):
    client, ids = setup
    packer, _ = login(client, "packer")
    call(client, "PATCH", "/admin/inventory", {"items": [{"variant_id": ids["variant"], "stock_qty": 2}]}, packer)
    call(client, "POST", "/cart/lines", {"variant_id": ids["variant"], "qty": 3}, guest(), 422)
    call(client, "POST", "/cart/lines", {"variant_id": ids["variant"], "qty": 1, "unit_price": "0.01"}, guest(), 400)
    admin, _ = login(client, "admin")
    call(client, "PATCH", "/admin/products/" + ids["product"], {"season_status": "off_season"}, admin)
    call(client, "POST", "/cart/lines", {"variant_id": ids["variant"], "qty": 1}, guest(), 422)


def address_payload():
    return dict(full_name="Test Shopper", phone="9876543210", line1="Test street", city="Mumbai", state="Maharashtra", pincode="400001", address_type="home", is_default=True)


def test_addresses_default_and_ownership(setup):
    client, _ = setup
    auth, _ = login(client)
    first = call(client, "POST", "/me/addresses", address_payload(), auth, 201)
    second = call(client, "POST", "/me/addresses", {**address_payload(), "line1": "Other street"}, auth, 201)
    rows = call(client, "GET", "/me/addresses", headers=auth)["items"]
    assert sum(row["is_default"] for row in rows) == 1
    call(client, "PATCH", "/me/addresses/" + first["id"], {"is_default": True}, auth)
    data = call(client, "POST", "/auth/signup", dict(full_name="Another Customer", email="other@example.com", phone="9876543211", password="test-password"), status=201)
    other = {"Authorization": "Bearer " + data["access_token"]}
    call(client, "DELETE", "/me/addresses/" + first["id"], headers=other, status=404)
    call(client, "PATCH", "/me", {"email": "changed@example.com"}, auth, 400)
    call(client, "DELETE", "/me/addresses/" + second["id"], headers=auth, status=204)


def test_campaigns_waitlist_and_outbox(setup, app):
    client, ids = setup
    auth, _ = login(client)
    admin, _ = login(client, "admin")
    call(client, "PUT", "/me/device-tokens", dict(fcm_token="test-fcm-token", platform="android", notifications_enabled=True), auth)
    data = dict(variety_name="Alphonso", product_id=ids["product"], harvest_start="2026-04-01", harvest_end="2026-06-30", waitlist_enabled=True, status="upcoming")
    season = call(client, "POST", "/admin/mango-seasons", data, admin, 201)
    call(client, "POST", "/mango-season/waitlist", {"product_id": ids["product"], "phone": "9876543210"}, status=201)
    assert call(client, "POST", "/mango-season/waitlist", {"slug": "alphonso", "phone": "9876543210"})["registered"]
    call(client, "POST", "/mango-season/waitlist", {"product_id": ids["product"]}, status=400)
    call(client, "PATCH", "/admin/mango-seasons/" + season["id"], {"status": "live"}, admin)
    inbox = call(client, "GET", "/me/notifications", headers=auth)["items"]
    assert len(inbox) == 1 and inbox[0]["product_slug"] == "alphonso"
    with app.app_context(): assert dispatch()["sent"] == 1
    assert len(app.extensions["mock_pushes"]) == 1
    call(client, "PATCH", "/admin/mango-seasons/" + season["id"], {"status": "live"}, admin)
    assert len(call(client, "GET", "/me/notifications", headers=auth)["items"]) == 1
    call(client, "PATCH", "/me/notifications/" + inbox[0]["id"], {"is_read": True}, auth)


def test_push_failure_retry_and_opt_out(setup, app, monkeypatch):
    client, ids = setup
    auth, _ = login(client)
    call(client, "PUT", "/me/device-tokens", dict(fcm_token="test-token", platform="android", notifications_enabled=True), auth)
    with app.app_context():
        enqueue(ids["customer"], "Order update", "Packed", "order", order_number="GS-1")
        db.session.commit()
        app.config["PUSH_BACKEND"] = "firebase"
        monkeypatch.setattr("backend.notifications.send_fcm", lambda *args: (_ for _ in ()).throw(RuntimeError("test transport failure")))
        assert dispatch()["failed"] == 1
        job = db.session.scalar(select(PushDelivery))
        assert job.attempts == 1 and job.sent_at is None and job.last_error == "RuntimeError"
        app.config["PUSH_BACKEND"] = "mock"
        db.session.remove()
    call(client, "PUT", "/me/device-tokens", dict(fcm_token="test-token", platform="android", notifications_enabled=False), auth)
    with app.app_context(): assert dispatch()["skipped"] == 1


def test_json_errors_cors_and_bad_credentials(setup):
    client, _ = setup
    call(client, "POST", "/auth/login", {"email": "absent@example.com", "password": "incorrect"}, status=401)
    call(client, "GET", "/me", headers={"Authorization": "Bearer invalid"}, status=401)
    assert set(call(client, "GET", "/missing", status=404)) == {"code", "message", "fields"}
    assert client.post("/api/v1/auth/login", data="{", content_type="application/json").status_code == 400
    response = client.options("/api/v1/cart", headers={"Origin": "https://shop.example"})
    assert response.headers["Access-Control-Allow-Origin"] == "https://shop.example"
    assert "Access-Control-Allow-Origin" not in client.get("/api/v1/products", headers={"Origin": "https://untrusted.example"}).headers


def test_fulfillment_transition_and_customer_order_isolation(setup, app):
    client, ids = setup
    with app.app_context():
        order = Order(order_number="GS-123", customer_id=ids["customer"], status="confirmed", address=address_payload(), pincode="400001", delivery_date=date.today() + timedelta(days=2),
                      payment_method="cod", payment_status="cod", subtotal=Decimal("100.25"), shipping=0, gst=Decimal("4.77"), grand_total=Decimal("100.25"),
                      lines=[OrderLine(product_name="Alphonso Mango", variant_label="6 pieces", sku="MANGO-6", qty=1, unit_price=Decimal("100.25"))])
        db.session.add(order)
        db.session.commit()
        key = str(order.id)
    auth, _ = login(client)
    assert call(client, "GET", "/orders/GS-123", headers=auth)["lines"][0]["sku"] == "MANGO-6"
    other = call(client, "POST", "/auth/signup", dict(full_name="Other Customer", email="other@example.com", phone="9876543211", password="test-password"), status=201)
    call(client, "GET", "/orders/GS-123", headers={"Authorization": "Bearer " + other["access_token"]}, status=404)
    packer, _ = login(client, "packer")
    call(client, "POST", f"/admin/orders/{key}/status", {"status": "delivered"}, packer, 422)
    call(client, "POST", f"/admin/orders/{key}/status", {"status": "packed"}, packer)
    assert call(client, "GET", "/me/notifications", headers=auth)["items"][0]["order_number"] == "GS-123"


def test_concurrent_cart_updates_do_not_lose_quantities(setup, app):
    client, ids = setup
    session = guest()
    def add(_):
        with app.test_client() as concurrent:
            return concurrent.post("/api/v1/cart/lines", json={"variant_id": ids["variant"], "qty": 1}, headers=session).status_code
    with ThreadPoolExecutor(max_workers=5) as workers: assert list(workers.map(add, range(10))) == [201] * 10
    cart = call(client, "GET", "/cart", headers=session)
    assert len(cart["lines"]) == 1 and cart["lines"][0]["qty"] == 10 and cart["subtotal"] == "1002.50"


def test_expired_and_inactive_sessions(setup, app):
    from backend.auth import now
    client, ids = setup
    auth, _ = login(client)
    admin, _ = login(client, "admin")
    with app.app_context():
        db.session.scalar(select(AuthSession).where(AuthSession.customer_id.is_not(None))).expires_at = now() - timedelta(seconds=1)
        db.session.get(AdminUser, ids["admin"]).is_active = False
        db.session.commit()
    call(client, "GET", "/me", headers=auth, status=401)
    call(client, "GET", "/admin/products", headers=admin, status=401)


def test_rate_limit_returns_json(app):
    limited = create_app(dict(TESTING=True, SECRET_KEY="test-secret-for-rate-limits-32-chars", RATELIMIT_ENABLED=True))
    with limited.test_client() as client:
        for _ in range(10): call(client, "POST", "/auth/login", {}, status=400)
        assert call(client, "POST", "/auth/login", {}, status=429)["code"] == "TOO_MANY_REQUESTS"


def test_firebase_adapter_builds_documented_payload(monkeypatch):
    firebase = pytest.importorskip("firebase_admin")
    from firebase_admin import messaging
    from backend.notifications import send_fcm
    captured = []
    monkeypatch.setattr(firebase, "get_app", lambda: "test-app")
    monkeypatch.setattr(messaging, "send", lambda message, app: captured.append(message) or "test-message-id")
    message = PushMessage(id=uuid4(), title="Order shipped", body="Your order shipped", type="order", order_number="GS-1")
    assert send_fcm("test-token", message) == "test-message-id"
    assert captured[0].data["order_number"] == "GS-1" and captured[0].data["type"] == "order"
