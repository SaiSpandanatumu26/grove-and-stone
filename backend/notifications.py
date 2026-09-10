"""Transactional notification outbox; real Firebase adapter plus an isolated test mock."""
from datetime import datetime, timezone

import click
from flask import current_app
from sqlalchemy import select

from .extensions import db
from .models import DeviceToken, PushMessage, PushDelivery


def enqueue(customer_id, title, body, kind, **links):
    message = PushMessage(customer_id=customer_id, title=title, body=body, type=kind, **links)
    db.session.add(message)
    db.session.flush()
    tokens = db.session.scalars(select(DeviceToken).where(DeviceToken.customer_id == customer_id, DeviceToken.notifications_enabled.is_(True)))
    db.session.add_all(PushDelivery(message_id=message.id, device_id=token.id) for token in tokens)


def season_opened(season):
    customer_ids = db.session.scalars(select(DeviceToken.customer_id).where(DeviceToken.notifications_enabled.is_(True)).distinct())
    for customer_id in customer_ids:
        enqueue(customer_id, f"{season.variety_name} season is open", "Explore this season's mangoes.", "mango_season", product_slug=season.product.slug)


def order_changed(order):
    if order.customer_id:
        enqueue(order.customer_id, f"Order {order.order_number} {order.status}", f"Your order is now {order.status}.", "order", order_number=order.order_number)


def send_fcm(token, message):
    import firebase_admin
    from firebase_admin import messaging
    try: app = firebase_admin.get_app()
    except ValueError: app = firebase_admin.initialize_app()
    data = {"type": message.type, "notification_id": str(message.id)}
    data.update({key: getattr(message, key) for key in ("order_number", "product_slug") if getattr(message, key)})
    return messaging.send(messaging.Message(token=token, notification=messaging.Notification(title=message.title, body=message.body), data=data), app=app)


def dispatch(limit=100):
    """At-least-once delivery; retry failures on the next explicit worker run."""
    counts = dict(sent=0, failed=0, skipped=0)
    jobs = db.session.scalars(select(PushDelivery).where(PushDelivery.sent_at.is_(None), PushDelivery.attempts < 5)
                             .order_by(PushDelivery.id).limit(limit).with_for_update(skip_locked=True)).all()
    for job in jobs:
        db.session.refresh(job.device, with_for_update=True)
        # A device may have logged out, disabled notifications, or changed account.
        if not job.device.notifications_enabled or job.device.customer_id != job.message.customer_id:
            db.session.delete(job)
            counts["skipped"] += 1
            continue
        job.attempts += 1
        try:
            if current_app.config["PUSH_BACKEND"] == "mock":
                if not current_app.testing: raise RuntimeError("Mock delivery is test-only")
                current_app.extensions.setdefault("mock_pushes", []).append({"message_id": str(job.message_id), "device_id": str(job.device_id)})
            else: send_fcm(job.device.fcm_token, job.message)
            job.sent_at, job.last_error = datetime.now(timezone.utc), None
            counts["sent"] += 1
        except Exception as error:
            job.last_error = type(error).__name__[:80]
            counts["failed"] += 1
    db.session.commit()
    return counts


def install_commands(app):
    @app.cli.command("dispatch-push")
    @click.option("--limit", default=100, type=click.IntRange(1, 500))
    def dispatch_push(limit):
        """Send committed pending notifications via configured Firebase credentials."""
        click.echo(dispatch(limit))
