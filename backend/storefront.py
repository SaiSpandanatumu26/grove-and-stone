"""Published hero slides, customer wishlists and atomic reorder into the current cart."""
from datetime import date
from pathlib import Path

from flask import g, send_from_directory
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from .api import api, body, fail, get_row, respond
from .auth import require
from .carts import cart_json, current_cart, locked_variant, purchasable
from .catalog import product_json
from .extensions import db
from .models import CMSBanner, CartLine, Order, Product, Variant, WishlistItem


@api.get("/banners")
def banners():
    rows = db.session.scalars(select(CMSBanner).where(CMSBanner.is_published.is_(True), CMSBanner.start_date <= date.today(), CMSBanner.end_date >= date.today()).order_by(CMSBanner.start_date.desc(), CMSBanner.id))
    return respond({"items": list(rows)})


@api.get("/media/<path:filename>")
def media(filename):
    return send_from_directory(Path(__file__).resolve().parents[1] / "mobile/assets/catalog", filename, max_age=86400, conditional=True)


@api.get("/me/wishlist")
@require()
def wishlist():
    rows = db.session.scalars(select(WishlistItem).where(WishlistItem.customer_id == g.customer.id).order_by(WishlistItem.created_at.desc()))
    return respond({"items": [product_json(row.product) for row in rows if row.product.is_active]})


@api.put("/me/wishlist/<uuid:key>")
@require()
def save_wishlist(key):
    if not get_row(Product, key).is_active: fail(404, "NOT_FOUND", "Not found.")
    db.session.execute(insert(WishlistItem).values(customer_id=g.customer.id, product_id=key).on_conflict_do_nothing())
    return respond({"saved": True})


@api.delete("/me/wishlist/<uuid:key>")
@require()
def remove_wishlist(key):
    row = db.session.get(WishlistItem, (g.customer.id, key))
    if row: db.session.delete(row)
    return "", 204


@api.post("/orders/<number>/reorder")
@require()
def reorder(number):
    body(set())
    order = db.session.scalar(select(Order).where(Order.order_number == number, Order.customer_id == g.customer.id))
    if order is None: fail(404, "NOT_FOUND", "Not found.")
    if not order.lines: fail(422, "ORDER_EMPTY", "There are no items to reorder.")
    cart, requests = current_cart(), {}
    for line in order.lines:
        variant = db.session.scalar(select(Variant).where(Variant.sku == line.sku))
        if not variant: fail(422, "PRODUCT_UNAVAILABLE", f"{line.product_name} is no longer available.")
        requests[variant.id] = (variant, requests.get(variant.id, (None, 0))[1] + line.qty)
    for variant, _ in sorted(requests.values(), key=lambda item: (str(item[0].product_id), str(item[0].id))):
        locked_variant(variant.id)
    existing = {line.variant_id: line for line in cart.lines}
    for variant, qty in requests.values():
        line = existing.get(variant.id)
        qty += line.qty if line else 0
        if qty > 20: fail(422, "QUANTITY_LIMIT", "A reorder would exceed 20 packs. Adjust your cart first.")
        purchasable(variant, qty)
        if not line:
            line = CartLine(cart=cart, product_id=variant.product_id, variant_id=variant.id)
            db.session.add(line)
        line.qty, line.unit_price = qty, variant.price
    return respond(cart_json(cart), 201)
