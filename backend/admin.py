"""Inventory, delivery coverage, campaigns, order reading and fulfillment."""
from datetime import date

from flask import g, request
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from .api import api, assign, body, fail, get_row, integer, invalid, json_value, paginated, respond, uid
from .auth import require
from .carts import locked_variant
from .extensions import db, limiter
from .models import CMSBanner, MangoSeason, Order, PincodeService, Product, Variant, WaitlistEntry
from .notifications import order_changed, season_opened


def current_banner():
    return db.session.scalar(select(CMSBanner).where(CMSBanner.is_published.is_(True), CMSBanner.start_date <= date.today(), CMSBanner.end_date >= date.today()).order_by(CMSBanner.start_date.desc(), CMSBanner.id).limit(1))


@api.get("/banners/current")
def banner():
    row = current_banner()
    return respond(row) if row else ("", 204)


@api.get("/mango-season")
def seasons():
    rows = db.session.scalars(select(MangoSeason).order_by(MangoSeason.harvest_start, MangoSeason.id))
    return respond({"banner": current_banner(), "varieties": [{**json_value(row), "product": json_value(row.product) if row.product and row.product.is_active else None} for row in rows]})


@api.post("/mango-season/waitlist")
@limiter.limit("5/minute")
def waitlist():
    fields = {"full_name", "email", "phone", "product_id", "slug"}
    data = body(fields)
    if bool(data.get("product_id")) == bool(data.get("slug")): invalid("product_id", "Supply product_id or slug.")
    product = get_row(Product, data.pop("product_id")) if "product_id" in data else db.session.scalar(select(Product).where(Product.slug == data.pop("slug")))
    if not product or not product.is_active or product.category != "mango": fail(404, "NOT_FOUND", "Not found.")
    season = db.session.scalar(select(MangoSeason).where(MangoSeason.product_id == product.id).order_by(MangoSeason.harvest_start.desc()).limit(1))
    if not season or not (season.waitlist_enabled or season.status == "upcoming"): fail(400, "WAITLIST_UNAVAILABLE", "This variety is not accepting waitlist entries.")
    data = {key: value for key, value in data.items() if value not in (None, "")}
    entry = assign(WaitlistEntry(product_id=product.id, variety_name=season.variety_name), data, {"full_name", "email", "phone"})
    if not entry.email and not entry.phone: invalid("email", "Enter email or mobile.")
    if entry.full_name is not None and not 2 <= len(entry.full_name) <= 80: invalid("full_name", "Expected 2–80 characters.")
    if entry.phone is not None and (not entry.phone.isascii() or not entry.phone.isdigit() or len(entry.phone) != 10): invalid("phone", "Expected 10 digits.")
    # Both unique contact indexes handle concurrent retries without exposing another entry's details.
    created = db.session.scalar(insert(WaitlistEntry).values(product_id=product.id, variety_name=season.variety_name,
                                full_name=entry.full_name, email=entry.email, phone=entry.phone).on_conflict_do_nothing().returning(WaitlistEntry.id))
    return respond({"registered": True, "message": "You're on the list. No payment is required."}, 201 if created else 200)


@api.route("/admin/inventory", methods=["GET", "PATCH"])
@require("admin", {"admin", "packer"})
def inventory():
    if request.method == "GET": return respond(paginated(select(Variant).order_by(Variant.sku)))
    items = body({"items"}, {"items"})["items"]
    if not isinstance(items, list) or not 1 <= len(items) <= 100: invalid("items", "Supply 1–100 stock updates.")
    rows, seen = [], set()
    for item in items:
        if not isinstance(item, dict) or set(item) != {"variant_id", "stock_qty"}: invalid("items", "Supply variant_id and stock_qty.")
        key = uid(item["variant_id"], "variant_id")
        if key in seen: invalid("variant_id", "Duplicate variant.")
        seen.add(key)
        rows.append((get_row(Variant, key), integer(item["stock_qty"], "stock_qty", 0)))
    for key in sorted({row.product_id for row, _ in rows}): get_row(Product, key, lock=True)
    for row, qty in rows: locked_variant(row.id).stock_qty = qty
    return respond({"items": [row for row, _ in rows]})


def register_resource(path, model, fields, required):
    """Same validated CRUD contract for the two small admin configuration resources."""
    def listing():
        if request.method == "GET": return respond({"items": db.session.scalars(select(model).order_by(*model.__table__.primary_key.columns)).all()})
        row = assign(model(), body(fields, required), fields, required)
        db.session.add(row)
        db.session.flush()
        if isinstance(row, MangoSeason) and row.status == "live": season_opened(row)
        return respond(row, 201)

    def detail(key):
        row = db.session.get(model, key) if model is PincodeService else get_row(model, key, lock=True)
        if row is None: fail(404, "NOT_FOUND", "Not found.")
        if request.method == "DELETE":
            db.session.delete(row)
            return "", 204
        before = row.status if isinstance(row, MangoSeason) else None
        assign(row, body(fields - {"pincode"}), fields - {"pincode"})
        db.session.flush()
        if isinstance(row, MangoSeason) and before != "live" and row.status == "live": season_opened(row)
        return respond(row)

    api.add_url_rule(path, model.__tablename__ + "_list", require("admin", {"admin"})(listing), methods=["GET", "POST"])
    api.add_url_rule(path + ("/<key>" if model is PincodeService else "/<uuid:key>"), model.__tablename__ + "_detail", require("admin", {"admin"})(detail), methods=["PATCH", "DELETE"])


PIN_FIELDS = set("pincode city state serviceable mango_eligible delivery_days_min delivery_days_max cod_allowed".split())
SEASON_FIELDS = set("variety_name product_id harvest_start harvest_end preorder_open preorder_close waitlist_enabled status".split())
register_resource("/admin/pincodes", PincodeService, PIN_FIELDS, PIN_FIELDS)
register_resource("/admin/mango-seasons", MangoSeason, SEASON_FIELDS, SEASON_FIELDS - {"product_id", "preorder_open", "preorder_close"})


@api.route("/admin/cms/banner", methods=["GET", "PUT"])
@require("admin", {"admin"})
def cms_banner():
    # The documented MVP has one banner, reused by home and the mango hub.
    from .carts import lock_owners
    lock_owners("cms:banner")
    row = db.session.scalar(select(CMSBanner).order_by(CMSBanner.start_date.desc(), CMSBanner.id).limit(1))
    if request.method == "GET": return respond(row) if row else ("", 204)
    fields = set("title subtitle season_state cta_label cta_url image start_date end_date is_published".split())
    row = assign(row or CMSBanner(), body(fields, fields - {"subtitle"}), fields)
    db.session.add(row)
    return respond(row)


def order_json(order):
    from .checkout import detail
    return detail(order)


@api.get("/orders")
@require()
def orders(): return respond(paginated(select(Order).where(Order.customer_id == g.customer.id).order_by(Order.created_at.desc(), Order.id)))


@api.get("/orders/<number>")
@require()
def order_detail(number):
    row = db.session.scalar(select(Order).where(Order.order_number == number, Order.customer_id == g.customer.id))
    if row is None: fail(404, "NOT_FOUND", "Not found.")
    return respond(order_json(row))


@api.get("/admin/orders")
@require("admin", {"admin", "packer"})
def admin_orders():
    query = select(Order)
    for key in ("order_number", "status", "payment_method"):
        if value := request.args.get(key):
            column = Order.__table__.c[key]
            if hasattr(column.type, "enums") and value not in column.type.enums: invalid(key, "Invalid filter.")
            query = query.where(getattr(Order, key) == value)
    for key in ("date_from", "date_to"):
        if value := request.args.get(key):
            try: day = date.fromisoformat(value)
            except ValueError: invalid(key, "Expected YYYY-MM-DD.")
            query = query.where(func.date(Order.created_at) >= day if key == "date_from" else func.date(Order.created_at) <= day)
    return respond(paginated(query.order_by(Order.created_at.desc(), Order.id)))


@api.get("/admin/orders/<uuid:key>")
@require("admin", {"admin", "packer"})
def admin_order(key): return respond(order_json(get_row(Order, key)))


@api.post("/admin/orders/<uuid:key>/status")
@require("admin", {"admin", "packer"})
def fulfillment(key):
    row = get_row(Order, key, lock=True)
    status = body({"status"}, {"status"})["status"]
    transitions = {"confirmed": {"packed", "cancelled"}, "packed": {"shipped"}, "shipped": {"delivered"}}
    if not isinstance(status, str) or status not in transitions.get(row.status, set()): fail(422, "INVALID_TRANSITION", "This status change is not allowed.")
    if status == 'cancelled':
        from .checkout import cancel_order
        cancel_order(row)
    else:
        row.status = status
        order_changed(row)
    return respond(order_json(row))


@api.get("/admin/dashboard")
@require("admin", {"admin", "packer"})
def dashboard():
    count = lambda model, condition: db.session.scalar(select(func.count()).select_from(model).where(condition))
    return respond(dict(orders_today=count(Order, func.date(Order.created_at) == date.today()),
                        pending_pack=count(Order, Order.status == "confirmed"), mango_live=count(MangoSeason, MangoSeason.status == "live"),
                        low_stock=count(Variant, Variant.stock_qty < 10), recent_orders=db.session.scalars(select(Order).order_by(Order.created_at.desc()).limit(10)).all(),
                        seasons=db.session.scalars(select(MangoSeason).order_by(MangoSeason.harvest_start)).all()))
