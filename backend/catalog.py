"""Documented public catalog/search and admin product editing."""
from flask import request
from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import selectinload

from .api import api, assign, body, fail, get_row, invalid, json_value, paginated, respond, text_value, uid
from .auth import require
from .extensions import db
from .models import Product, Variant, MangoSeason

PRODUCT_FIELDS = set("name slug category origin short_description long_description images season_status handling_notes ripeness_note farm_story is_gift_eligible is_active harvest_window".split())
PRODUCT_REQUIRED = set("name slug category origin short_description long_description images season_status is_gift_eligible is_active".split())
VARIANT_FIELDS = set("sku pack_label pack_type weight_grams unit_count price gst_percent stock_qty cod_allowed is_default".split())
VARIANT_REQUIRED = VARIANT_FIELDS - {"weight_grams", "unit_count"}


def product_json(product, detail=False):
    return {**json_value(product), **({"variants": json_value(sorted(product.variants, key=lambda v: (not v.is_default, v.sku)))} if detail else
            {"default_variant": json_value(next((v for v in product.variants if v.is_default), None))})}


def catalog_query(admin=False, search=False):
    query = select(Product).options(selectinload(Product.variants))
    if not admin: query = query.where(Product.is_active.is_(True))
    for key in ("category", "season_status"):
        if value := request.args.get(key):
            if value not in Product.__table__.c[key].type.enums: invalid(key, "Invalid filter.")
            query = query.where(getattr(Product, key) == value)
    if value := request.args.get("origin"): query = query.where(Product.origin == value)
    if value := request.args.get("pack_type"):
        if value not in Variant.pack_type.type.enums: invalid("pack_type", "Invalid filter.")
        query = query.where(Product.variants.any(Variant.pack_type == value))
    if admin and "is_active" in request.args:
        if request.args["is_active"] not in {"true", "false"}: invalid("is_active", "Use true or false.")
        query = query.where(Product.is_active.is_(request.args["is_active"] == "true"))
    term = request.args.get("search" if admin else "q")
    ranking = []
    if search or admin and term:
        term = text_value(term, "search" if admin else "q", 1, 80)
        name, origin = Product.name.icontains(term, autoescape=True), Product.origin.icontains(term, autoescape=True)
        linked = Product.variants.any(Variant.sku.icontains(term, autoescape=True)) if admin else Product.mango_seasons.any(MangoSeason.variety_name.icontains(term, autoescape=True))
        query = query.where(or_(name, linked) if admin else or_(name, origin, linked))
        ranking = [case((func.lower(Product.name) == term.lower(), 0), (name, 1), (origin, 2), else_=3)]
    sort = request.args.get("sort", "featured")
    price = select(Variant.price).where(Variant.product_id == Product.id, Variant.is_default.is_(True)).scalar_subquery()
    if sort not in {"featured", "price_asc", "price_desc", "name"}: invalid("sort", "Invalid sort.")
    ordering = [price.asc() if sort == "price_asc" else price.desc()] if sort.startswith("price_") else ranking if sort == "featured" else []
    return query.order_by(*ordering, Product.name, Product.id)


@api.get("/products")
@api.get("/search")
def products(): return respond(paginated(catalog_query(search=request.path.endswith("/search")), product_json))


@api.post('/stock/check')
def stock_check():
    """Small, uncached public snapshot; reservations already reduce stock_qty."""
    from datetime import datetime, timezone
    keys = body({'product_ids'}, {'product_ids'})['product_ids']
    if not isinstance(keys, list) or not 1 <= len(keys) <= 100: invalid('product_ids', 'Supply 1–100 product UUIDs.')
    keys = list(dict.fromkeys(uid(key, 'product_ids') for key in keys))
    # One statement keeps product availability and variant stock in the same snapshot.
    rows = db.session.execute(select(Product.id, Product.is_active, Product.season_status, Variant.id, Variant.stock_qty)
                              .outerjoin(Variant, Variant.product_id == Product.id).where(Product.id.in_(keys)).order_by(Product.id, Variant.id))
    items = {key: dict(id=key, is_active=False, season_status='off_season', variants=[]) for key in keys}
    for product_id, active, season, variant_id, qty in rows:
        item = items[product_id]
        item.update(is_active=active, season_status=season if active else 'off_season')
        if active and variant_id: item['variants'].append(dict(id=variant_id, stock_qty=qty))
    return respond(dict(items=list(items.values()), checked_at=datetime.now(timezone.utc), poll_after_seconds=5))


def public_product(slug):
    product = db.session.scalar(select(Product).where(Product.slug == slug, Product.is_active.is_(True)))
    if not product: fail(404, "NOT_FOUND", "Not found.")
    return product


@api.get("/products/<slug>")
def product_detail(slug): return respond(product_json(public_product(slug), True))


@api.get("/products/<slug>/related")
def related(slug):
    product = public_product(slug)
    query = select(Product).where(Product.category == product.category, Product.is_active.is_(True), Product.id != product.id).order_by(Product.name, Product.id).limit(8)
    return respond({"items": [product_json(p) for p in db.session.scalars(query)]})


def save_product(product, data):
    packs = data.pop("variants", None)
    assign(product, data, PRODUCT_FIELDS, PRODUCT_REQUIRED if product.id is None else ())
    if product.id is None and packs is None: invalid("variants", "At least one variant is required.")
    if packs is not None:
        if not isinstance(packs, list) or not 1 <= len(packs) <= 100: invalid("variants", "Supply 1–100 variants as the complete desired list.")
        existing, desired, seen = {str(v.id): v for v in product.variants}, [], set()
        for pack in packs:
            if not isinstance(pack, dict): invalid("variants", "Expected variant objects.")
            pack = dict(pack)
            key = str(uid(pack.pop("id"), "variants.id")) if "id" in pack else None
            if key and (key not in existing or key in seen): invalid("variants.id", "Unknown, foreign, or repeated variant.")
            seen.add(key) if key else None
            variant = existing[key] if key else Variant()
            if key: pack.setdefault("is_default", variant.is_default)
            desired.append((variant, pack))
        if sum(pack.get("is_default", variant.is_default or False) is True for variant, pack in desired) != 1: invalid("variants", "Select exactly one default variant.")
        # Clear and flush existing defaults before replacement to satisfy the unique index.
        if product.id:
            for variant in product.variants: variant.is_default = False
            db.session.flush()
        for variant, pack in desired: assign(variant, pack, VARIANT_FIELDS, () if variant.id else VARIANT_REQUIRED)
        product.variants = [variant for variant, _ in desired]
    db.session.add(product)
    db.session.flush()
    return product


@api.route("/admin/products", methods=["GET", "POST"])
@require("admin", {"admin"})
def admin_products():
    if request.method == "GET": return respond(paginated(catalog_query(admin=True), lambda p: product_json(p, True)))
    return respond(product_json(save_product(Product(), body(PRODUCT_FIELDS | {"variants"})), True), 201)


@api.route("/admin/products/<uuid:key>", methods=["GET", "PATCH"])
@require("admin", {"admin"})
def admin_product(key):
    product = get_row(Product, key, lock=request.method == "PATCH")
    if request.method == "PATCH": save_product(product, body(PRODUCT_FIELDS | {"variants"}))
    return respond(product_json(product, True))
