"""Shared JSON, validation and transaction handling for /api/v1."""
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from uuid import UUID

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import Boolean, Date, Integer, Numeric, String, inspect, select, func
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

from .extensions import db

api = Blueprint("api", __name__, url_prefix="/api/v1")


class APIError(Exception):
    def __init__(self, status, code, message, fields=None):
        self.status, self.body = status, dict(code=code, message=message, fields=fields or {})


def fail(status, code, message, **fields):
    raise APIError(status, code, message, fields)


def invalid(field, message):
    fail(400, "VALIDATION_ERROR", "Check the supplied fields.", **{field: message})


def body(allowed, required=()):
    data = request.get_json()
    if not isinstance(data, dict): invalid("body", "Expected a JSON object.")
    if unknown := data.keys() - set(allowed): invalid(sorted(unknown)[0], "Unknown or read-only field.")
    if missing := set(required) - data.keys(): invalid(sorted(missing)[0], "Required.")
    return data


def uid(value, field="id"):
    try: return UUID(str(value))
    except (ValueError, TypeError, AttributeError): invalid(field, "Expected a UUID.")


def integer(value, field, minimum=1, maximum=2_147_483_647):
    if type(value) is not int or not minimum <= value <= maximum: invalid(field, f"Expected an integer from {minimum} to {maximum}.")
    return value


def text_value(value, field, minimum=1, maximum=10000):
    if not isinstance(value, str) or not minimum <= len(value.strip()) <= maximum: invalid(field, f"Expected {minimum}–{maximum} characters.")
    return value.strip()


def assign(row, data, fields, required=()):
    """Validate only explicitly writable fields; database checks enforce domain rules."""
    if unknown := data.keys() - set(fields): invalid(sorted(unknown)[0], "Unknown or read-only field.")
    if missing := set(required) - data.keys(): invalid(sorted(missing)[0], "Required.")
    for key, value in data.items():
        column = row.__table__.c[key]
        kind = column.type
        if value is None:
            if not column.nullable: invalid(key, "Required.")
        elif isinstance(kind, Boolean):
            if type(value) is not bool: invalid(key, "Expected true or false.")
        elif isinstance(kind, Integer): value = integer(value, key, 0)
        elif isinstance(kind, Numeric):
            try:
                if isinstance(value, bool): raise ValueError()
                value = Decimal(str(value))
                if not value.is_finite() or value < 0 or value >= 10 ** (kind.precision - kind.scale) or value != value.quantize(Decimal("0.01")): raise ValueError()
            except (ValueError, InvalidOperation): invalid(key, "Expected a nonnegative amount with at most 2 decimals.")
        elif isinstance(kind, Date):
            try: value = date.fromisoformat(value)
            except (ValueError, TypeError): invalid(key, "Expected YYYY-MM-DD.")
        elif hasattr(kind, "enums"):
            if value not in kind.enums: invalid(key, f"Choose: {', '.join(kind.enums)}.")
        elif isinstance(kind, String):
            if key == "password":
                if not isinstance(value, str) or not 8 <= len(value) <= 1024: invalid(key, "Expected 8–1024 characters.")
            else: value = text_value(value, key, 0 if column.nullable else 1, kind.length or 10000)
        elif hasattr(kind, "as_uuid"): value = uid(value, key)
        elif key == "images":
            if not isinstance(value, list) or not 1 <= len(value) <= 20: invalid(key, "Add 1–20 image references.")
            value = [text_value(item, key, 1, 2048) for item in value]
        try: setattr(row, key, value)
        except ValueError: invalid(key, "Invalid value.")
    return row


def json_value(value):
    if isinstance(value, Decimal): return format(value, ".2f")
    if isinstance(value, UUID): return str(value)
    if isinstance(value, datetime): return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, date): return value.isoformat()
    if isinstance(value, dict): return {key: json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)): return [json_value(item) for item in value]
    if isinstance(value, db.Model): return json_value({attr.key: getattr(value, attr.key) for attr in inspect(value).mapper.column_attrs if not attr.key.startswith("_")})
    return value


def respond(value, status=200):
    db.session.flush()
    return jsonify(json_value(value)), status


def get_row(model, key, *, lock=False):
    query = select(model).where(model.id == uid(key))
    row = db.session.scalar(query.with_for_update() if lock else query)
    if row is None: fail(404, "NOT_FOUND", "Not found.")
    return row


def paginated(query, serialize=json_value):
    def number(key, default, maximum):
        raw = request.args.get(key, str(default))
        if not raw.isascii() or not raw.isdigit(): invalid(key, "Expected a positive integer.")
        return integer(int(raw), key, 1, maximum)
    page, size = number("page", 1, 1_000_000), number("page_size", 20, 50)
    total = db.session.scalar(select(func.count()).select_from(query.order_by(None).subquery()))
    items = db.session.scalars(query.offset((page - 1) * size).limit(size)).unique().all()
    return dict(items=[serialize(item) for item in items], total=total, page=page, page_size=size)


def database_error(error):
    db.session.rollback()
    code = getattr(getattr(error, "orig", None), "sqlstate", "")
    if code == "23505": return jsonify(code="CONFLICT", message="This value already exists.", fields={}), 409
    if code in {"23503", "23514", "23502", "22001", "22003", "22P02"}:
        return jsonify(code="VALIDATION_ERROR", message="A field violates a data constraint.", fields={"body": "Check field values and references."}), 400
    if code in {"40P01", "40001"}: return jsonify(code="RETRY_TRANSACTION", message="Please retry the request.", fields={}), 409
    current_app.logger.error("Database request failed: %s (SQLSTATE %s)", type(error).__name__, code)
    return jsonify(code="SERVICE_UNAVAILABLE", message="Service temporarily unavailable.", fields={}), 503


def install_api(app):
    from . import auth, catalog, carts, customers, admin, notifications, storefront, checkout, content  # noqa: F401
    app.register_blueprint(api)

    @app.errorhandler(APIError)
    def api_error(error):
        db.session.rollback()
        return jsonify(error.body), error.status

    @app.errorhandler(SQLAlchemyError)
    def sql_error(error): return database_error(error)

    @app.errorhandler(HTTPException)
    def http_error(error):
        db.session.rollback()
        return jsonify(code=error.name.upper().replace(" ", "_"), message=error.description, fields={}), error.code

    @app.errorhandler(Exception)
    def unexpected(error):
        db.session.rollback()
        current_app.logger.error("Request failed: %s", type(error).__name__)
        return jsonify(code="INTERNAL_ERROR", message="An unexpected error occurred.", fields={}), 500

    @app.after_request
    def finish(response):
        try:
            if response.status_code < 400: db.session.commit()
            else: db.session.rollback()
        except SQLAlchemyError as error: response = app.make_response(database_error(error))
        response.headers["Cache-Control"] = "no-store"
        origin = request.headers.get("Origin")
        if origin and origin in app.config["CORS_ORIGINS"]:
            response.headers.update({"Access-Control-Allow-Origin": origin, "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Session-Id", "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS"})
            response.vary.add("Origin")
        return response
