"""Separate customer/admin bearer sessions with hashed, revocable refresh tokens."""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import current_app, g, request
from itsdangerous import BadData, URLSafeTimedSerializer
from sqlalchemy import select, func
from werkzeug.security import check_password_hash, generate_password_hash

from .api import api, assign, body, fail, invalid, respond, text_value, uid
from .extensions import db, limiter
from .models import AdminUser, AuthSession, Customer

DUMMY_HASH = generate_password_hash("invalid-login-placeholder")
now = lambda: datetime.now(timezone.utc)
digest = lambda token: hashlib.sha256(token.encode()).hexdigest()


def signer():
    key = current_app.config.get("SECRET_KEY")
    if not key or len(key) < 32: fail(503, "AUTH_NOT_CONFIGURED", "Authentication is not configured.")
    return URLSafeTimedSerializer(key, salt="grove-stone-access-v1")


def access(session):
    return signer().dumps({"sid": str(session.id), "kind": "customer" if session.customer_id else "admin"})


def require(kind="customer", roles=()):
    def decorate(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            header = request.headers.get("Authorization", "")
            if not header and kind == "session":
                if not request.headers.get("X-Session-Id"): fail(401, "UNAUTHORIZED", "Supply a bearer token or X-Session-Id.")
                g.customer, g.session_id = None, str(uid(request.headers.get("X-Session-Id"), "X-Session-Id"))
                return view(*args, **kwargs)
            try:
                if not header.startswith("Bearer "): raise BadData("Missing bearer")
                data = signer().loads(header[7:], max_age=current_app.config["ACCESS_TOKEN_SECONDS"])
                session = db.session.get(AuthSession, uid(data["sid"]))
            except (BadData, KeyError, TypeError): fail(401, "UNAUTHORIZED", "Sign in to continue.")
            if session is None or session.expires_at <= now(): fail(401, "UNAUTHORIZED", "Session expired.")
            expected = "admin" if kind == "admin" else "customer"
            actual = "customer" if session.customer_id else "admin"
            if actual != expected or data["kind"] != actual: fail(403, "FORBIDDEN", "This account cannot access this resource.")
            actor = db.session.get(Customer if actual == "customer" else AdminUser, session.customer_id or session.admin_id)
            if actor is None or actual == "admin" and not actor.is_active: fail(401, "UNAUTHORIZED", "Sign in to continue.")
            if roles and actor.role not in roles: fail(403, "FORBIDDEN", "Your role cannot perform this action.")
            g.auth_session, g.actor = session, actor
            if actual == "customer": g.customer = actor
            return view(*args, **kwargs)
        return wrapped
    return decorate


def issue(actor):
    customer = isinstance(actor, Customer)
    refresh = secrets.token_urlsafe(48) if customer else None
    session = AuthSession(customer_id=actor.id if customer else None, admin_id=None if customer else actor.id,
                          refresh_digest=digest(refresh) if refresh else None,
                          expires_at=now() + timedelta(seconds=current_app.config["REFRESH_TOKEN_SECONDS"] if customer else current_app.config["ACCESS_TOKEN_SECONDS"]))
    db.session.add(session)
    db.session.flush()
    payload = {"customer" if customer else "admin": actor, "access_token": access(session)}
    if customer:
        from .carts import merge_guest
        payload.update(refresh_token=refresh, cart_merge=merge_guest(actor, request.headers.get("X-Session-Id")))
    return payload


@api.post("/auth/signup")
@limiter.limit("5/minute")
def signup():
    fields = {"full_name", "email", "phone", "password"}
    data = body(fields, fields)
    customer = assign(Customer(), data, fields, fields)
    db.session.add(customer)
    db.session.flush()
    return respond(issue(customer), 201)


@api.post("/auth/login")
@api.post("/admin/auth/login")
@limiter.limit("10/minute")
def login():
    data = body({"email", "password"}, {"email", "password"})
    email, password = text_value(data["email"], "email", maximum=320).lower(), data["password"]
    if not isinstance(password, str) or not 1 <= len(password) <= 1024: invalid("password", "Expected a password.")
    model = AdminUser if "/admin/" in request.path else Customer
    actor = db.session.scalar(select(model).where(func.lower(model.email) == email))
    valid = check_password_hash(actor._password_hash if actor else DUMMY_HASH, password)
    if not actor or not valid or isinstance(actor, AdminUser) and not actor.is_active: fail(401, "INCORRECT_CREDENTIALS", "Email or password is incorrect.")
    return respond(issue(actor))


@api.post("/auth/refresh")
@limiter.limit("30/minute")
def refresh():
    data = body({"refresh_token"}, {"refresh_token"})
    token = text_value(data["refresh_token"], "refresh_token", maximum=256)
    session = db.session.scalar(select(AuthSession).where(AuthSession.refresh_digest == digest(token)).with_for_update())
    if not session or not session.customer_id or session.expires_at <= now(): fail(401, "UNAUTHORIZED", "Session expired.")
    return respond({"access_token": access(session)})


@api.post("/auth/logout")
@require()
def logout():
    db.session.delete(g.auth_session)
    return "", 204
