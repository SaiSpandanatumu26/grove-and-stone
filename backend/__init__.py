"""Grove & Stone Flask application factory."""
import os

import click
from flask import Flask
from sqlalchemy import create_mock_engine

from .extensions import db, limiter


def create_app(config=None):
    app = Flask(__name__, static_folder=None)
    uri = os.environ.get("DATABASE_URL", "postgresql+psycopg://localhost/grove_stone")
    if uri.startswith(("postgres://", "postgresql://")):
        uri = "postgresql+psycopg://" + uri.split("://", 1)[1]
    app.config.from_mapping(SQLALCHEMY_DATABASE_URI=uri, SQLALCHEMY_TRACK_MODIFICATIONS=False, WEB_DIST_DIR=os.environ.get("WEB_DIST_DIR"),
                            SECRET_KEY=os.environ.get("SECRET_KEY"), ACCESS_TOKEN_SECONDS=900, REFRESH_TOKEN_SECONDS=2_592_000,
                            MAX_CONTENT_LENGTH=1_048_576, CORS_ORIGINS=os.environ.get("CORS_ORIGINS", "").split(","),
                            RATELIMIT_STORAGE_URI=os.environ.get("RATELIMIT_STORAGE_URI", "memory://"), PUSH_BACKEND="firebase",
                            PAYMENT_BACKEND=os.environ.get("PAYMENT_BACKEND", "disabled"), SHIPPING_FEE=os.environ.get("SHIPPING_FEE"),
                            FREE_SHIPPING_THRESHOLD=os.environ.get("FREE_SHIPPING_THRESHOLD"), PUBLIC_API_URL=os.environ.get("PUBLIC_API_URL", ""),
                            RAZORPAY_KEY_ID=os.environ.get("RAZORPAY_KEY_ID"), RAZORPAY_KEY_SECRET=os.environ.get("RAZORPAY_KEY_SECRET"),
                            RAZORPAY_WEBHOOK_SECRET=os.environ.get("RAZORPAY_WEBHOOK_SECRET"), SUPPORT_EMAIL=os.environ.get("SUPPORT_EMAIL"),
                            SUPPORT_PHONE=os.environ.get("SUPPORT_PHONE"), RESEND_API_KEY=os.environ.get("RESEND_API_KEY"),
                            CONTACT_FROM=os.environ.get("CONTACT_FROM"), CONTACT_BACKEND=os.environ.get("CONTACT_BACKEND", "disabled"),
                            QUALITY_REPORT_HOURS=os.environ.get("QUALITY_REPORT_HOURS", "24"))
    if config:
        app.config.update(config)
    if not app.config["SQLALCHEMY_DATABASE_URI"].startswith("postgresql+"):
        raise ValueError("This schema requires PostgreSQL; SQLite is not supported.")
    if app.config["PAYMENT_BACKEND"] == "demo" or app.config["CONTACT_BACKEND"] == "demo":
        from sqlalchemy.engine import make_url
        url = make_url(app.config["SQLALCHEMY_DATABASE_URI"])
        if not app.testing and (url.host not in {"localhost", "127.0.0.1", "::1"} or not (url.database or "").endswith("_local")):
            raise ValueError("Demo mode requires a loopback *_local database.")
    db.init_app(app)
    limiter.init_app(app)
    from . import models  # noqa: F401 - register tables and database invariants
    from .api import install_api
    from .notifications import install_commands
    install_api(app)
    from .web import install_web
    install_web(app)
    install_commands(app)
    from .checkout import install_checkout_commands
    install_checkout_commands(app)

    @app.cli.command("create-admin")
    @click.option("--name", prompt=True)
    @click.option("--email", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin(name, email, password):
        """Create an active administrator locally; never expose public admin signup."""
        db.session.add(models.AdminUser(name=name, email=email, password=password, role="admin", is_active=True))
        db.session.commit()
        click.echo("Administrator created.")

    @app.cli.command("init-db")
    def init_db():
        """Create the initial schema in the configured, existing PostgreSQL database."""
        from sqlalchemy import text
        db.session.execute(text("SELECT pg_advisory_xact_lock(741805231)"))
        db.metadata.create_all(bind=db.session.connection())
        db.session.commit()
        click.echo("Grove & Stone schema created. Existing tables are not migrated.")

    @app.cli.command("export-schema")
    @click.argument("path", type=click.Path(dir_okay=False))
    def export_schema(path):
        """Export complete initial PostgreSQL DDL without connecting to a database."""
        statements = []
        # Plain SQL files must not contain DBAPI's doubled percent escapes.
        engine = create_mock_engine("postgresql+psycopg://", lambda sql, *a, **kw:
                                    statements.append(str(sql.compile(dialect=engine.dialect)).strip() + ";"),
                                    paramstyle="named")
        db.metadata.create_all(engine, checkfirst=False)
        with open(path, "w", encoding="utf-8") as output:
            output.write("-- Generated from backend.models; initial schema only.\nBEGIN;\n\n")
            output.write("\n\n".join(statements))
            output.write("\n\nCOMMIT;\n")
        click.echo(f"Schema exported to {path}")

    return app
