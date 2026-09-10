from flask import g, request
from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert

from .api import api, assign, body, fail, get_row, respond, text_value
from .auth import require
from .extensions import db
from .models import Address, Customer, DeviceToken, PushMessage

ADDRESS_FIELDS = set("full_name phone line1 line2 city state pincode landmark address_type is_default".split())
ADDRESS_REQUIRED = ADDRESS_FIELDS - {"line2", "landmark"}


@api.route("/me", methods=["GET", "PATCH"])
@require()
def profile():
    if request.method == "PATCH": assign(g.customer, body({"full_name", "phone"}), {"full_name", "phone"})
    return respond(g.customer)


@api.route("/me/addresses", methods=["GET", "POST"])
@require()
def addresses():
    if request.method == "GET": return respond({"items": g.customer.addresses})
    address = Address(customer_id=g.customer.id)
    save_address(address, body(ADDRESS_FIELDS, ADDRESS_REQUIRED))
    return respond(address, 201)


def save_address(address, data):
    get_row(Customer, g.customer.id, lock=True)
    assign(address, data, ADDRESS_FIELDS)
    if data.get("is_default"):
        # Suppress autoflush until the previous default has been cleared.
        with db.session.no_autoflush:
            db.session.execute(update(Address).where(Address.customer_id == g.customer.id, Address.id != address.id if address.id else True).values(is_default=False))
    db.session.add(address)


@api.route("/me/addresses/<uuid:key>", methods=["PATCH", "DELETE"])
@require()
def address_detail(key):
    get_row(Customer, g.customer.id, lock=True)
    address = get_row(Address, key, lock=True)
    if address.customer_id != g.customer.id: fail(404, "NOT_FOUND", "Not found.")
    if request.method == "DELETE":
        db.session.delete(address)
        return "", 204
    save_address(address, body(ADDRESS_FIELDS))
    return respond(address)


@api.route("/me/device-tokens", methods=["PUT", "DELETE"])
@require()
def device_tokens():
    fields = {"fcm_token", "platform", "notifications_enabled"} if request.method == "PUT" else {"fcm_token"}
    data = body(fields, fields)
    token = text_value(data["fcm_token"], "fcm_token", maximum=4096)
    data["fcm_token"] = token
    if request.method == "DELETE":
        db.session.execute(delete(DeviceToken).where(DeviceToken.customer_id == g.customer.id, DeviceToken.fcm_token == token))
        return "", 204
    assign(DeviceToken(), data, fields)
    statement = insert(DeviceToken).values(customer_id=g.customer.id, **data)
    statement = statement.on_conflict_do_update(index_elements=["fcm_token"], set_={"customer_id": g.customer.id, "notifications_enabled": data["notifications_enabled"], "platform": data["platform"]}).returning(DeviceToken)
    return respond(db.session.scalars(statement).one())


@api.get("/me/notifications")
@require()
def inbox():
    query = select(PushMessage).where(PushMessage.customer_id == g.customer.id).order_by(PushMessage.created_at.desc(), PushMessage.id).limit(50)
    return respond({"items": db.session.scalars(query).all()})


@api.patch("/me/notifications/<uuid:key>")
@require()
def read_notification(key):
    message = get_row(PushMessage, key)
    if message.customer_id != g.customer.id: fail(404, "NOT_FOUND", "Not found.")
    return respond(assign(message, body({"is_read"}, {"is_read"}), {"is_read"}))
