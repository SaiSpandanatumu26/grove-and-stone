import pytest
from sqlalchemy.orm import configure_mappers

from backend import create_app
from backend.extensions import db
from backend.models import Customer, AdminUser, ORDER_PAYMENT_STATUS, PAYMENT_STATUS


def test_all_relationships_configure():
    configure_mappers()
    assert len(db.metadata.tables) == 28
    assert "search_query" not in db.metadata.tables


@pytest.mark.parametrize("model", [Customer, AdminUser])
def test_password_is_hashed_and_write_only(model):
    account = model(password="sample-test-passphrase")
    assert account._password_hash.startswith("scrypt:")
    assert "sample-test-passphrase" not in account._password_hash
    assert account.check_password("sample-test-passphrase")
    assert not account.check_password("incorrect")
    with pytest.raises(AttributeError):
        _ = account.password
    with pytest.raises(ValueError):
        account.password = "short"


def test_customer_email_validation():
    assert Customer(email="TEST@Example.COM").email == "test@example.com"
    with pytest.raises(ValueError):
        Customer(email="not-an-email")


def test_distinct_payment_status_enums():
    assert ORDER_PAYMENT_STATUS.enums == ["pending", "paid", "failed", "cod"]
    assert PAYMENT_STATUS.enums == ["pending", "paid", "failed", "cod_pending"]


def test_schema_export_and_api_routes(tmp_path):
    app = create_app({"TESTING": True})
    target = tmp_path / "schema.sql"
    result = app.test_cli_runner().invoke(args=["export-schema", str(target)])
    assert result.exit_code == 0, result.output
    sql = target.read_text(encoding="utf-8")
    assert "CREATE CONSTRAINT TRIGGER gs_product_default" in sql
    assert "GENERATED ALWAYS AS (qty * unit_price) STORED" in sql
    assert "fk_payment_order_amount" in sql
    assert "%(2f|5c|0a|0d)" in sql
    assert "%%" not in sql
    assert "/api/v1/cart" in {str(rule) for rule in app.url_map.iter_rules()}


def test_reject_sqlite():
    with pytest.raises(ValueError, match="PostgreSQL"):
        create_app({"SQLALCHEMY_DATABASE_URI": "sqlite://"})
