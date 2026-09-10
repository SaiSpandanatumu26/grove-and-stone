"""Serialized cart changes, server prices and guest-to-customer merge."""
from decimal import Decimal, ROUND_HALF_UP

from flask import g, request
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert

from .api import api, body, fail, get_row, integer, invalid, json_value, respond, uid
from .auth import require
from .extensions import db
from .models import Cart, CartLine, Product, Variant, PincodeService


def lock_owners(*owners):
    for owner in sorted(set(owners)):
        db.session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:owner, 0))"), {"owner": owner})


def owned_cart(customer=None, session_id=None):
    field, value = ("customer_id", customer.id) if customer else ("session_id", session_id)
    db.session.execute(insert(Cart).values(**{field: value}).on_conflict_do_nothing(index_elements=[field]))
    return db.session.scalar(select(Cart).where(getattr(Cart, field) == value).with_for_update())


def current_cart():
    customer = getattr(g, "customer", None)
    session_id = None if customer else g.session_id
    lock_owners(f"customer:{customer.id}" if customer else f"guest:{session_id}")
    return owned_cart(customer, session_id)


def locked_variant(key):
    variant = get_row(Variant, key)
    # Match catalog/inventory lock order: product before variant.
    get_row(Product, variant.product_id, lock=True)
    return db.session.scalar(select(Variant).where(Variant.id == variant.id).with_for_update().execution_options(populate_existing=True))


def purchasable(variant, qty):
    if not variant.product.is_active or variant.product.season_status in {"off_season", "coming_soon"}:
        fail(422, "PRODUCT_UNAVAILABLE", "This product is not available to buy.")
    if qty > variant.stock_qty: fail(422, "INSUFFICIENT_STOCK", "There is not enough stock.", qty=f"Available: {variant.stock_qty}.")


def coverage(pincode):
    if not isinstance(pincode, str) or len(pincode) != 6 or not pincode.isascii() or not pincode.isdigit(): invalid("pincode", "Enter a valid 6-digit pincode.")
    row = db.session.get(PincodeService, pincode)
    return json_value(row) if row else {"pincode": pincode, "serviceable": False, "mango_eligible": False, "cod_allowed": False}


def cart_json(cart):
    db.session.flush()
    area = coverage(cart.pincode) if cart.pincode else {}
    lines = [{**json_value(line), "product": json_value(line.product), "variant": json_value(line.variant)} for line in cart.lines]
    reason = "CART_EMPTY" if not lines else "PINCODE_REQUIRED" if not area else "PINCODE_NOT_SERVICEABLE" if not area.get("serviceable") else None
    for line in cart.lines:
        if not line.product.is_active or line.product.season_status in {"off_season", "coming_soon"}: reason = "PRODUCT_UNAVAILABLE"
        elif line.qty > line.variant.stock_qty: reason = "INSUFFICIENT_STOCK"
        elif line.product.category in {"mango", "exotic"} and area.get("serviceable") and not area.get("mango_eligible"): reason = "MANGO_NOT_ELIGIBLE"
    if not reason and not cart.customer_id: reason = "LOGIN_REQUIRED"
    subtotal = sum((line.unit_price * line.qty for line in cart.lines), Decimal(0))
    gst = sum(((line.unit_price * line.qty * line.variant.gst_percent / (100 + line.variant.gst_percent)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) for line in cart.lines), Decimal(0))
    return {**json_value(cart), "lines": lines, "subtotal": subtotal, "included_gst": gst, "total_before_shipping": subtotal,
            "can_checkout": reason is None, "block_reason": reason,
            "cod_allowed": bool(lines) and area.get("cod_allowed", False) and all(line.variant.cod_allowed for line in cart.lines)}


def merge_guest(customer, session_id):
    if not session_id: return {"adjustments": []}
    session_id = str(uid(session_id, "X-Session-Id"))
    lock_owners(f"customer:{customer.id}", f"guest:{session_id}")
    guest = db.session.scalar(select(Cart).where(Cart.session_id == session_id).with_for_update())
    if not guest: return {"adjustments": []}
    target, adjustments = owned_cart(customer), []
    existing = {line.variant_id: line for line in target.lines}
    # Sorted product locks prevent two cart merges from locking products in opposite orders.
    for key in sorted({line.product_id for line in guest.lines}): get_row(Product, key, lock=True)
    for line in list(guest.lines):
        variant = locked_variant(line.variant_id)
        old = existing.get(variant.id)
        requested = line.qty + (old.qty if old else 0)
        available = variant.stock_qty if variant.product.is_active and variant.product.season_status not in {"coming_soon", "off_season"} else 0
        qty = min(requested, available, 20)
        if qty != requested: adjustments.append({"variant_id": str(variant.id), "requested_qty": requested, "qty": qty})
        if qty:
            if not old:
                old = CartLine(cart=target, product_id=variant.product_id, variant_id=variant.id)
                db.session.add(old)
            old.qty, old.unit_price = qty, variant.price
        elif old: db.session.delete(old)
    if not target.pincode: target.pincode = guest.pincode
    if not target.delivery_date: target.delivery_date = guest.delivery_date
    db.session.delete(guest)
    return {"adjustments": adjustments}


@api.get("/pincodes/<pincode>")
def pincode_lookup(pincode): return respond(coverage(pincode))


@api.get("/cart")
@require("session")
def show_cart(): return respond(cart_json(current_cart()))


@api.put("/cart/pincode")
@require("session")
def cart_pincode():
    data = body({"pincode"}, {"pincode"})
    area, cart = coverage(data["pincode"]), current_cart()
    cart.pincode = data["pincode"]
    return respond({"pincode_service": area, "cart": cart_json(cart)})


@api.post("/cart/lines")
@require("session")
def add_line():
    data = body({"variant_id", "qty"}, {"variant_id", "qty"})
    cart, qty = current_cart(), integer(data["qty"], "qty", 1, 20)
    variant = locked_variant(uid(data["variant_id"], "variant_id"))
    line = next((line for line in cart.lines if line.variant_id == variant.id), None)
    qty = integer(qty + (line.qty if line else 0), "qty", 1, 20)
    purchasable(variant, qty)
    if not line:
        line = CartLine(cart=cart, product_id=variant.product_id, variant_id=variant.id)
        db.session.add(line)
    line.qty, line.unit_price = qty, variant.price
    return respond(cart_json(cart), 201)


@api.route("/cart/lines/<uuid:key>", methods=["PATCH", "DELETE"])
@require("session")
def edit_line(key):
    cart = current_cart()
    line = next((line for line in cart.lines if line.id == key), None)
    if not line: fail(404, "NOT_FOUND", "Not found.")
    if request.method == "DELETE":
        db.session.delete(line)
        return "", 204
    qty = integer(body({"qty"}, {"qty"})["qty"], "qty", 1, 20)
    variant = locked_variant(line.variant_id)
    purchasable(variant, qty)
    line.qty, line.unit_price = qty, variant.price
    return respond(cart_json(cart))


@api.delete("/cart/lines")
@require("session")
def clear_cart():
    for line in current_cart().lines: db.session.delete(line)
    return "", 204
