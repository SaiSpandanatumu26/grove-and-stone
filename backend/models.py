"""PostgreSQL models from docs/00-object-dictionary.md.

Screen specifications supply additional validation; see SCHEMA_REVIEW.md.
Prices are Decimal INR; API serialization uses decimal strings.
"""
import uuid

from email_validator import validate_email
from sqlalchemy import CheckConstraint as Check, Computed, ForeignKeyConstraint, Index, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import ARRAY, ENUM, JSONB, UUID
from sqlalchemy.orm import validates
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


def enum(name, *values):
    return ENUM(*values, name=name, metadata=db.metadata, validate_strings=True)


CATEGORY = enum("category", "exotic", "dry_fruit", "mango")
SEASON_STATUS = enum("season_status", "in_season", "limited", "coming_soon", "off_season")
PACK_TYPE = enum("pack_type", "weight", "box", "tin")
ADDRESS_TYPE = enum("address_type", "home", "office", "other")
PAYMENT_METHOD = enum("payment_method", "upi", "card", "cod")
ORDER_STATUS = enum("order_status", "pending_payment", "confirmed", "packed", "shipped", "delivered", "cancelled")
ORDER_PAYMENT_STATUS = enum("order_payment_status", "pending", "paid", "failed", "cod")
PAYMENT_STATUS = enum("payment_status", "pending", "paid", "failed", "cod_pending")
MANGO_STATUS = enum("mango_season_status", "upcoming", "live", "closed")
ADMIN_ROLE = enum("admin_role", "admin", "packer")
BANNER_STATE = enum("banner_season_state", "live", "coming_soon", "closed")
DEVICE_PLATFORM = enum("device_platform", "android")
PUSH_TYPE = enum("push_type", "order", "mango_season")
MONEY = db.Numeric(12, 2)


def pk():
    return db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))


def fk(target, *, nullable=False, ondelete="RESTRICT", unique=False):
    return db.Column(UUID(as_uuid=True), db.ForeignKey(target, ondelete=ondelete), nullable=nullable, index=True, unique=unique)


def required_text():
    return db.Column(db.Text, nullable=False)


def flag(default=False):
    return db.Column(db.Boolean, nullable=False, default=default, server_default=text("true" if default else "false"))


def timestamp():
    return db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())


def email_check():
    # Deliberately basic database guard; ORM uses email-validator for complete syntax.
    return Check("email ~ '^[^[:space:]@]+@[^[:space:]@]+[.][^[:space:]@]+$'", name="email_format")


def phone_check():
    return Check("phone ~ '^[0-9]{10}$'", name="phone_format")


def pincode_check():
    return Check("pincode ~ '^[0-9]{6}$'", name="pincode_format")


class EmailMixin:
    @validates("email")
    def normalize_email(self, key, value):
        if value is None:
            return None
        return validate_email(value.strip(), check_deliverability=False).normalized.lower()


class PasswordMixin:
    # Keep dictionary's physical column name; it stores only a Werkzeug scrypt hash.
    _password_hash = db.Column("password", db.Text, nullable=False)

    @property
    def password(self):
        raise AttributeError("Password is write-only")

    @password.setter
    def password(self, value):
        if not isinstance(value, str) or len(value) < 8:
            raise ValueError("Password must contain at least 8 characters")
        self._password_hash = generate_password_hash(value, method="scrypt")

    def check_password(self, value):
        return bool(self._password_hash) and check_password_hash(self._password_hash, value)


class Customer(EmailMixin, PasswordMixin, db.Model):
    __tablename__ = "customer"
    id = pk()
    full_name = db.Column(db.String(80), nullable=False)
    email = required_text()
    phone = db.Column(db.String(10), nullable=False, unique=True)
    created_at = timestamp()
    addresses = db.relationship("Address", back_populates="customer", cascade="all, delete-orphan", passive_deletes=True)
    cart = db.relationship("Cart", back_populates="customer", uselist=False, cascade="all, delete-orphan", passive_deletes=True)
    orders = db.relationship("Order", back_populates="customer", passive_deletes="all")
    device_tokens = db.relationship("DeviceToken", back_populates="customer", cascade="all, delete-orphan", passive_deletes=True)
    push_messages = db.relationship("PushMessage", back_populates="customer", cascade="all, delete-orphan", passive_deletes=True)
    __table_args__ = (
        Check("char_length(full_name) BETWEEN 2 AND 80", name="full_name_length"),
        email_check(), phone_check(),
        Check("password LIKE 'scrypt:%'", name="password_hash"),
        Index("uq_customer_email_ci", func.lower(email), unique=True),
    )


class PincodeService(db.Model):
    __tablename__ = "pincode_service"
    pincode = db.Column(db.String(6), primary_key=True)
    city = required_text()
    state = required_text()
    serviceable = flag()
    mango_eligible = flag()
    delivery_days_min = db.Column(db.Integer, nullable=False)
    delivery_days_max = db.Column(db.Integer, nullable=False)
    cod_allowed = flag()
    addresses = db.relationship("Address", back_populates="pincode_service", passive_deletes="all")
    __table_args__ = (pincode_check(),
        Check("delivery_days_min >= 1 AND delivery_days_max >= delivery_days_min", name="delivery_days"),
        Check("NOT mango_eligible OR serviceable", name="mango_serviceable"))


class Address(db.Model):
    __tablename__ = "address"
    id = pk()
    customer_id = fk("customer.id", ondelete="CASCADE")
    full_name = required_text()
    phone = db.Column(db.String(10), nullable=False)
    line1 = db.Column(db.String(120), nullable=False)
    line2 = db.Column(db.String(120))
    city = required_text()
    state = required_text()
    pincode = db.Column(db.String(6), db.ForeignKey("pincode_service.pincode", ondelete="RESTRICT"), nullable=False, index=True)
    landmark = db.Column(db.String(80))
    address_type = db.Column(ADDRESS_TYPE, nullable=False)
    is_default = flag()
    customer = db.relationship("Customer", back_populates="addresses")
    pincode_service = db.relationship("PincodeService", back_populates="addresses")
    __table_args__ = (phone_check(), pincode_check(),
        Check("char_length(line1) BETWEEN 5 AND 120", name="line1_length"),
        Index("uq_address_customer_default", "customer_id", unique=True, postgresql_where=text("is_default")))


class Product(db.Model):
    __tablename__ = "product"
    id = pk()
    name = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.Text, nullable=False, unique=True)
    category = db.Column(CATEGORY, nullable=False, index=True)
    origin = required_text()
    short_description = db.Column(db.String(160), nullable=False)
    long_description = required_text()
    images = db.Column(ARRAY(db.Text), nullable=False)
    season_status = db.Column(SEASON_STATUS, nullable=False, index=True)
    handling_notes = db.Column(db.Text)
    ripeness_note = db.Column(db.Text)
    farm_story = db.Column(db.Text)
    is_gift_eligible = flag()
    is_active = flag()
    harvest_window = db.Column(db.Text)
    variants = db.relationship("Variant", back_populates="product", cascade="all, delete-orphan", passive_deletes=True)
    mango_seasons = db.relationship("MangoSeason", back_populates="product", passive_deletes="all")
    waitlist_entries = db.relationship("WaitlistEntry", back_populates="product", cascade="all, delete-orphan", passive_deletes=True)
    __table_args__ = (
        Check("char_length(name) BETWEEN 2 AND 80", name="name_length"),
        Check("slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'", name="slug_format"),
        Check("cardinality(images) >= 1 AND array_ndims(images) = 1 AND array_position(images, NULL) IS NULL AND array_position(images, '') IS NULL", name="images_required"),
        Index("ix_product_name", "name"), Index("ix_product_origin", "origin"))


class Variant(db.Model):
    __tablename__ = "variant"
    id = pk()
    product_id = fk("product.id", ondelete="CASCADE")
    sku = db.Column(db.Text, nullable=False, unique=True)
    pack_label = required_text()
    pack_type = db.Column(PACK_TYPE, nullable=False)
    weight_grams = db.Column(db.Integer)
    unit_count = db.Column(db.Integer)
    price = db.Column(MONEY, nullable=False)
    gst_percent = db.Column(db.Numeric(5, 2), nullable=False)
    stock_qty = db.Column(db.Integer, nullable=False)
    cod_allowed = flag(True)
    is_default = flag()
    product = db.relationship("Product", back_populates="variants")
    cart_lines = db.relationship("CartLine", back_populates="variant", passive_deletes="all")
    __table_args__ = (
        UniqueConstraint("id", "product_id", name="uq_variant_id_product"),
        Index("uq_variant_product_default", "product_id", unique=True, postgresql_where=text("is_default")),
        Check("price > 0", name="positive_price"),
        Check("gst_percent BETWEEN 0 AND 28", name="gst_range"),
        Check("stock_qty >= 0", name="stock_nonnegative"),
        Check("weight_grams > 0", name="weight_positive"),
        Check("unit_count > 0", name="unit_count_positive"),
        Check("pack_type <> 'weight' OR weight_grams IS NOT NULL", name="weight_required"),
        Check("pack_type <> 'box' OR unit_count IS NOT NULL", name="box_count_required"))


class WishlistItem(db.Model):
    """Customer-saved products, added for the requested account wishlist."""
    __tablename__ = "wishlist_item"
    customer_id = db.Column(UUID(as_uuid=True), db.ForeignKey("customer.id", ondelete="CASCADE"), primary_key=True)
    product_id = db.Column(UUID(as_uuid=True), db.ForeignKey("product.id", ondelete="CASCADE"), primary_key=True)
    created_at = timestamp()
    product = db.relationship("Product")


class Cart(db.Model):
    __tablename__ = "cart"
    id = pk()
    customer_id = fk("customer.id", nullable=True, ondelete="CASCADE", unique=True)
    session_id = db.Column(db.Text, unique=True)
    pincode = db.Column(db.String(6))
    delivery_date = db.Column(db.Date)
    customer = db.relationship("Customer", back_populates="cart")
    lines = db.relationship("CartLine", back_populates="cart", cascade="all, delete-orphan", passive_deletes=True)
    __table_args__ = (pincode_check(),
        Check("(customer_id IS NOT NULL) <> (session_id IS NOT NULL)", name="one_owner"),
        Check("session_id IS NULL OR char_length(btrim(session_id)) > 0", name="session_nonempty"))


class CartLine(db.Model):
    __tablename__ = "cart_line"
    id = pk()
    cart_id = fk("cart.id", ondelete="CASCADE")
    product_id = fk("product.id")
    variant_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    qty = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(MONEY, nullable=False)
    line_total = db.Column(MONEY, Computed("qty * unit_price", persisted=True), nullable=False)
    cart = db.relationship("Cart", back_populates="lines")
    product = db.relationship("Product", viewonly=True)
    variant = db.relationship("Variant", back_populates="cart_lines")
    __table_args__ = (
        ForeignKeyConstraint(["variant_id", "product_id"], ["variant.id", "variant.product_id"], ondelete="RESTRICT", name="fk_cart_line_variant_product"),
        UniqueConstraint("cart_id", "variant_id"),
        Check("qty BETWEEN 1 AND 20", name="qty_range"),
        Check("unit_price > 0", name="price_positive"))


class MangoSeason(db.Model):
    __tablename__ = "mango_season"
    id = pk()
    variety_name = required_text()
    product_id = fk("product.id", nullable=True)
    harvest_start = db.Column(db.Date, nullable=False)
    harvest_end = db.Column(db.Date, nullable=False)
    preorder_open = db.Column(db.Date)
    preorder_close = db.Column(db.Date)
    waitlist_enabled = flag()
    status = db.Column(MANGO_STATUS, nullable=False)
    product = db.relationship("Product", back_populates="mango_seasons")
    __table_args__ = (
        Check("harvest_end >= harvest_start", name="harvest_dates"),
        Check("preorder_open <= harvest_start", name="preorder_start"),
        Check("preorder_close >= preorder_open", name="preorder_dates"),
        Check("status <> 'live' OR product_id IS NOT NULL", name="live_product"),
        Index("ix_mango_season_variety_name", "variety_name"))


class WaitlistEntry(EmailMixin, db.Model):
    __tablename__ = "waitlist_entry"
    id = pk()
    full_name = db.Column(db.String(80))
    email = db.Column(db.Text)
    phone = db.Column(db.String(10))
    product_id = fk("product.id", ondelete="CASCADE")
    variety_name = required_text()
    created_at = timestamp()
    product = db.relationship("Product", back_populates="waitlist_entries")
    __table_args__ = (
        Check("email IS NOT NULL OR phone IS NOT NULL", name="contact_required"),
        Check("char_length(full_name) BETWEEN 2 AND 80", name="full_name_length"),
        email_check(), phone_check(),
        Index("uq_waitlist_product_email_ci", "product_id", func.lower(email), unique=True),
        UniqueConstraint("product_id", "phone"))


class Order(db.Model):
    __tablename__ = "orders"
    id = pk()
    order_number = db.Column(db.Text, nullable=False, unique=True)
    customer_id = fk("customer.id", nullable=True)
    status = db.Column(ORDER_STATUS, nullable=False, index=True)
    address = db.Column(JSONB, nullable=False)
    pincode = db.Column(db.String(6), nullable=False)
    delivery_date = db.Column(db.Date, nullable=False)
    payment_method = db.Column(PAYMENT_METHOD, nullable=False)
    payment_status = db.Column(ORDER_PAYMENT_STATUS, nullable=False)
    subtotal = db.Column(MONEY, nullable=False)
    shipping = db.Column(MONEY, nullable=False)
    gst = db.Column(MONEY, nullable=False)
    discount = db.Column(MONEY, default=0, server_default=text("0"))
    grand_total = db.Column(MONEY, nullable=False)
    customer_notes = db.Column(db.String(200))
    created_at = timestamp()
    customer = db.relationship("Customer", back_populates="orders")
    lines = db.relationship("OrderLine", back_populates="order", cascade="all, delete-orphan", passive_deletes=True)
    payments = db.relationship("Payment", back_populates="order", cascade="all, delete-orphan", passive_deletes=True)
    __table_args__ = (
        pincode_check(), UniqueConstraint("id", "grand_total", name="uq_orders_id_total"),
        Check("order_number ~ '^GS-[0-9]+$'", name="order_number_format"),
        Check("jsonb_typeof(address) = 'object'", name="address_object"),
        Check("address ?& ARRAY['full_name','phone','line1','city','state','pincode','address_type']", name="address_keys"),
        Check("jsonb_typeof(address->'full_name') = 'string' AND char_length(address->>'full_name') > 0 AND "
              "jsonb_typeof(address->'phone') = 'string' AND (address->>'phone') ~ '^[0-9]{10}$' AND "
              "jsonb_typeof(address->'line1') = 'string' AND char_length(address->>'line1') BETWEEN 5 AND 120 AND "
              "jsonb_typeof(address->'city') = 'string' AND char_length(address->>'city') > 0 AND "
              "jsonb_typeof(address->'state') = 'string' AND char_length(address->>'state') > 0 AND "
              "jsonb_typeof(address->'pincode') = 'string' AND "
              "jsonb_typeof(address->'address_type') = 'string' AND (address->>'address_type') IN ('home','office','other')", name="address_fields"),
        Check("(address ->> 'pincode') IS NOT NULL AND (address ->> 'pincode') = pincode", name="address_pincode"),
        Check("subtotal >= 0 AND shipping >= 0 AND gst >= 0 AND COALESCE(discount, 0) >= 0 AND grand_total >= 0", name="amounts_nonnegative"),
        Check("grand_total = subtotal + shipping - COALESCE(discount, 0)", name="grand_total_formula"))


class OrderLine(db.Model):
    __tablename__ = "order_line"
    id = pk()
    order_id = fk("orders.id", ondelete="CASCADE")
    product_name = required_text()
    variant_label = required_text()
    sku = required_text()
    qty = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(MONEY, nullable=False)
    line_total = db.Column(MONEY, Computed("qty * unit_price", persisted=True), nullable=False)
    order = db.relationship("Order", back_populates="lines")
    __table_args__ = (Check("qty > 0 AND unit_price > 0", name="positive_line"),)


class Payment(db.Model):
    __tablename__ = "payment"
    id = pk()
    order_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    method = db.Column(PAYMENT_METHOD, nullable=False)
    status = db.Column(PAYMENT_STATUS, nullable=False)
    amount = db.Column(MONEY, nullable=False)
    gateway_ref = db.Column(db.Text)
    order = db.relationship("Order", back_populates="payments")
    __table_args__ = (
        ForeignKeyConstraint(["order_id", "amount"], ["orders.id", "orders.grand_total"], ondelete="CASCADE", name="fk_payment_order_amount"),
        Check("amount >= 0", name="amount_nonnegative"))


class CheckoutSession(db.Model):
    """Checkout retry identity and gateway metadata; domain snapshots stay on Order."""
    __tablename__ = "checkout_session"
    order_id = db.Column(UUID(as_uuid=True), db.ForeignKey("orders.id", ondelete="CASCADE"), primary_key=True)
    customer_id = fk("customer.id")
    request_id = db.Column(UUID(as_uuid=True), nullable=False)
    request_hash = required_text()
    backend = required_text()
    gateway_order_id = db.Column(db.Text, unique=True)
    gateway_payment_id = db.Column(db.Text, unique=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    released_at = db.Column(db.DateTime(timezone=True))
    order = db.relationship("Order")
    __table_args__ = (UniqueConstraint("customer_id", "request_id"), Check("backend IN ('cod','demo','razorpay')", name="backend_value"))


class StockReservation(db.Model):
    __tablename__ = "stock_reservation"
    order_id = db.Column(UUID(as_uuid=True), db.ForeignKey("orders.id", ondelete="CASCADE"), primary_key=True)
    variant_id = db.Column(UUID(as_uuid=True), db.ForeignKey("variant.id", ondelete="RESTRICT"), primary_key=True)
    qty = db.Column(db.Integer, nullable=False)
    __table_args__ = (Check("qty BETWEEN 1 AND 20", name="quantity"),)


class RefundRequest(db.Model):
    __tablename__ = "refund_request"
    order_id = db.Column(UUID(as_uuid=True), db.ForeignKey("orders.id", ondelete="CASCADE"), primary_key=True)
    amount = db.Column(MONEY, nullable=False)
    status = db.Column(db.Text, nullable=False, default="pending", server_default="pending")
    gateway_ref = db.Column(db.Text, unique=True)
    last_error = db.Column(db.String(80))
    created_at = timestamp()
    __table_args__ = (Check("amount > 0", name="positive_amount"), Check("status IN ('pending','submitted','processed')", name="status_value"))


class AdminUser(EmailMixin, PasswordMixin, db.Model):
    __tablename__ = "admin_user"
    id = pk()
    name = required_text()
    email = required_text()
    role = db.Column(ADMIN_ROLE, nullable=False)
    is_active = flag()
    __table_args__ = (email_check(), Check("password LIKE 'scrypt:%'", name="password_hash"),
        Index("uq_admin_user_email_ci", func.lower(email), unique=True))


class CMSBanner(db.Model):
    __tablename__ = "cms_banner"
    id = pk()
    title = required_text()
    subtitle = db.Column(db.Text)
    season_state = db.Column(BANNER_STATE, nullable=False)
    cta_label = required_text()
    cta_url = required_text()
    image = required_text()
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_published = flag()
    __table_args__ = (
        Check("end_date >= start_date", name="banner_dates"),
        Check("cta_url ~ '^/([^/\\\\]|$)' AND cta_url !~ '[[:cntrl:]]' AND cta_url !~* '%(2f|5c|0a|0d)'", name="internal_cta"),
        Check("char_length(btrim(image)) > 0", name="image_required"))


class DeviceToken(db.Model):
    __tablename__ = "device_token"
    id = pk()
    customer_id = fk("customer.id", ondelete="CASCADE")
    fcm_token = db.Column(db.Text, nullable=False, unique=True)
    platform = db.Column(DEVICE_PLATFORM, nullable=False)
    notifications_enabled = flag()
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    customer = db.relationship("Customer", back_populates="device_tokens")


class PushMessage(db.Model):
    __tablename__ = "push_message"
    id = pk()
    customer_id = fk("customer.id", ondelete="CASCADE")
    title = required_text()
    body = required_text()
    type = db.Column(PUSH_TYPE, nullable=False)
    order_number = db.Column(db.Text)
    product_slug = db.Column(db.Text)
    is_read = flag()
    created_at = timestamp()
    customer = db.relationship("Customer", back_populates="push_messages")


class AuthSession(db.Model):
    """Infrastructure extension: durable, revocable bearer/refresh sessions."""
    __tablename__ = "auth_session"
    id = pk()
    customer_id = fk("customer.id", nullable=True, ondelete="CASCADE")
    admin_id = fk("admin_user.id", nullable=True, ondelete="CASCADE")
    refresh_digest = db.Column(db.String(64), unique=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    __table_args__ = (Check("(customer_id IS NOT NULL) <> (admin_id IS NOT NULL)", name="one_identity"),)


class PushDelivery(db.Model):
    """Infrastructure extension: transactional FCM outbox, one row per device."""
    __tablename__ = "push_delivery"
    id = pk()
    message_id = fk("push_message.id", ondelete="CASCADE")
    device_id = fk("device_token.id", ondelete="CASCADE")
    attempts = db.Column(db.Integer, nullable=False, default=0, server_default=text("0"))
    sent_at = db.Column(db.DateTime(timezone=True))
    last_error = db.Column(db.String(80))
    message = db.relationship("PushMessage")
    device = db.relationship("DeviceToken")
    __table_args__ = (UniqueConstraint("message_id", "device_id"), Check("attempts >= 0", name="attempts_nonnegative"))


class OwnerAlert(db.Model):
    """Durable owner inbox and email outbox, committed with the order."""
    __tablename__ = "owner_alert"
    id = pk()
    order_id = fk("orders.id", ondelete="CASCADE")
    kind = db.Column(db.String(30), nullable=False)
    created_at = timestamp()
    seen_at = db.Column(db.DateTime(timezone=True))
    sent_at = db.Column(db.DateTime(timezone=True))
    next_attempt_at = timestamp()
    attempts = db.Column(db.Integer, nullable=False, default=0, server_default=text("0"))
    last_error = db.Column(db.String(120))
    order = db.relationship("Order")
    __table_args__ = (UniqueConstraint("order_id", "kind"), Check("attempts >= 0", name="attempts_nonnegative"))


class AdminInvite(db.Model):
    """One-use bootstrap invitation, issued only from the privileged CLI."""
    __tablename__ = "admin_invite"
    id = pk()
    email = db.Column(db.String(320), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    token_digest = db.Column(db.String(64), nullable=False, unique=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    used_at = db.Column(db.DateTime(timezone=True))


class Shipment(db.Model):
    __tablename__ = "shipment"
    order_id = fk("orders.id", ondelete="CASCADE", unique=True)
    id = pk()
    carrier = db.Column(db.String(100), nullable=False)
    tracking_number = db.Column(db.String(100), nullable=False)
    tracking_url = db.Column(db.String(2048))
    updated_at = timestamp()


class ShopSetting(db.Model):
    """Non-secret business settings. Provider secrets stay in environment variables."""
    __tablename__ = "shop_setting"
    key = db.Column(db.String(80), primary_key=True)
    value = db.Column(JSONB, nullable=False)


class AdminAudit(db.Model):
    __tablename__ = "admin_audit"
    id = pk()
    admin_id = fk("admin_user.id", nullable=True, ondelete="SET NULL")
    method = db.Column(db.String(10), nullable=False)
    path = db.Column(db.String(300), nullable=False)
    created_at = timestamp()


class PostalArea(db.Model):
    """Postal reference data; inclusion never enables delivery."""
    __tablename__ = "postal_area"
    pincode = db.Column(db.String(6), primary_key=True)
    district = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    offices = db.Column(ARRAY(db.Text), nullable=False)
    source = db.Column(db.String(500), nullable=False)
    updated_at = timestamp()
    __table_args__ = (pincode_check(),)


# PostgreSQL transaction-level invariants cannot be expressed by row CHECKs.
from .schema_invariants import register_invariants  # noqa: E402
register_invariants(db.metadata)
