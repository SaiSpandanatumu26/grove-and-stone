-- Generated from backend.models; initial schema only.
BEGIN;

CREATE TYPE category AS ENUM ('exotic', 'dry_fruit', 'mango');

CREATE TYPE season_status AS ENUM ('in_season', 'limited', 'coming_soon', 'off_season');

CREATE TYPE pack_type AS ENUM ('weight', 'box', 'tin');

CREATE TYPE address_type AS ENUM ('home', 'office', 'other');

CREATE TYPE payment_method AS ENUM ('upi', 'card', 'cod');

CREATE TYPE order_status AS ENUM ('pending_payment', 'confirmed', 'packed', 'shipped', 'delivered', 'cancelled');

CREATE TYPE order_payment_status AS ENUM ('pending', 'paid', 'failed', 'cod');

CREATE TYPE payment_status AS ENUM ('pending', 'paid', 'failed', 'cod_pending');

CREATE TYPE mango_season_status AS ENUM ('upcoming', 'live', 'closed');

CREATE TYPE admin_role AS ENUM ('admin', 'packer');

CREATE TYPE banner_season_state AS ENUM ('live', 'coming_soon', 'closed');

CREATE TYPE device_platform AS ENUM ('android');

CREATE TYPE push_type AS ENUM ('order', 'mango_season');

CREATE TABLE customer (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	full_name VARCHAR(80) NOT NULL,
	email TEXT NOT NULL,
	phone VARCHAR(10) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	password TEXT NOT NULL,
	CONSTRAINT pk_customer PRIMARY KEY (id),
	CONSTRAINT ck_customer_full_name_length CHECK (char_length(full_name) BETWEEN 2 AND 80),
	CONSTRAINT ck_customer_email_format CHECK (email ~ '^[^[:space:]@]+@[^[:space:]@]+[.][^[:space:]@]+$'),
	CONSTRAINT ck_customer_phone_format CHECK (phone ~ '^[0-9]{10}$'),
	CONSTRAINT ck_customer_password_hash CHECK (password LIKE 'scrypt:%'),
	CONSTRAINT uq_customer_phone UNIQUE (phone)
);

CREATE UNIQUE INDEX uq_customer_email_ci ON customer (lower(email));

CREATE TABLE pincode_service (
	pincode VARCHAR(6) NOT NULL,
	city TEXT NOT NULL,
	state TEXT NOT NULL,
	serviceable BOOLEAN DEFAULT false NOT NULL,
	mango_eligible BOOLEAN DEFAULT false NOT NULL,
	delivery_days_min INTEGER NOT NULL,
	delivery_days_max INTEGER NOT NULL,
	cod_allowed BOOLEAN DEFAULT false NOT NULL,
	CONSTRAINT pk_pincode_service PRIMARY KEY (pincode),
	CONSTRAINT ck_pincode_service_pincode_format CHECK (pincode ~ '^[0-9]{6}$'),
	CONSTRAINT ck_pincode_service_delivery_days CHECK (delivery_days_min >= 1 AND delivery_days_max >= delivery_days_min),
	CONSTRAINT ck_pincode_service_mango_serviceable CHECK (NOT mango_eligible OR serviceable)
);

CREATE TABLE product (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	name VARCHAR(80) NOT NULL,
	slug TEXT NOT NULL,
	category category NOT NULL,
	origin TEXT NOT NULL,
	short_description VARCHAR(160) NOT NULL,
	long_description TEXT NOT NULL,
	images TEXT[] NOT NULL,
	season_status season_status NOT NULL,
	handling_notes TEXT,
	ripeness_note TEXT,
	farm_story TEXT,
	is_gift_eligible BOOLEAN DEFAULT false NOT NULL,
	is_active BOOLEAN DEFAULT false NOT NULL,
	harvest_window TEXT,
	CONSTRAINT pk_product PRIMARY KEY (id),
	CONSTRAINT ck_product_name_length CHECK (char_length(name) BETWEEN 2 AND 80),
	CONSTRAINT ck_product_slug_format CHECK (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
	CONSTRAINT ck_product_images_required CHECK (cardinality(images) >= 1 AND array_ndims(images) = 1 AND array_position(images, NULL) IS NULL AND array_position(images, '') IS NULL),
	CONSTRAINT uq_product_slug UNIQUE (slug)
);

CREATE INDEX ix_product_category ON product (category);

CREATE INDEX ix_product_name ON product (name);

CREATE INDEX ix_product_origin ON product (origin);

CREATE INDEX ix_product_season_status ON product (season_status);

CREATE TABLE admin_user (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	name TEXT NOT NULL,
	email TEXT NOT NULL,
	role admin_role NOT NULL,
	is_active BOOLEAN DEFAULT false NOT NULL,
	password TEXT NOT NULL,
	CONSTRAINT pk_admin_user PRIMARY KEY (id),
	CONSTRAINT ck_admin_user_email_format CHECK (email ~ '^[^[:space:]@]+@[^[:space:]@]+[.][^[:space:]@]+$'),
	CONSTRAINT ck_admin_user_password_hash CHECK (password LIKE 'scrypt:%')
);

CREATE UNIQUE INDEX uq_admin_user_email_ci ON admin_user (lower(email));

CREATE TABLE cms_banner (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	title TEXT NOT NULL,
	subtitle TEXT,
	season_state banner_season_state NOT NULL,
	cta_label TEXT NOT NULL,
	cta_url TEXT NOT NULL,
	image TEXT NOT NULL,
	start_date DATE NOT NULL,
	end_date DATE NOT NULL,
	is_published BOOLEAN DEFAULT false NOT NULL,
	CONSTRAINT pk_cms_banner PRIMARY KEY (id),
	CONSTRAINT ck_cms_banner_banner_dates CHECK (end_date >= start_date),
	CONSTRAINT ck_cms_banner_internal_cta CHECK (cta_url ~ '^/([^/\\]|$)' AND cta_url !~ '[[:cntrl:]]' AND cta_url !~* '%(2f|5c|0a|0d)'),
	CONSTRAINT ck_cms_banner_image_required CHECK (char_length(btrim(image)) > 0)
);

CREATE TABLE admin_invite (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	email VARCHAR(320) NOT NULL,
	name VARCHAR(100) NOT NULL,
	token_digest VARCHAR(64) NOT NULL,
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
	used_at TIMESTAMP WITH TIME ZONE,
	CONSTRAINT pk_admin_invite PRIMARY KEY (id),
	CONSTRAINT uq_admin_invite_token_digest UNIQUE (token_digest)
);

CREATE TABLE shop_setting (
	key VARCHAR(80) NOT NULL,
	value JSONB NOT NULL,
	CONSTRAINT pk_shop_setting PRIMARY KEY (key)
);

CREATE TABLE postal_area (
	pincode VARCHAR(6) NOT NULL,
	district VARCHAR(120) NOT NULL,
	state VARCHAR(120) NOT NULL,
	offices TEXT[] NOT NULL,
	source VARCHAR(500) NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_postal_area PRIMARY KEY (pincode),
	CONSTRAINT ck_postal_area_pincode_format CHECK (pincode ~ '^[0-9]{6}$')
);

CREATE TABLE address (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	customer_id UUID NOT NULL,
	full_name TEXT NOT NULL,
	phone VARCHAR(10) NOT NULL,
	line1 VARCHAR(120) NOT NULL,
	line2 VARCHAR(120),
	city TEXT NOT NULL,
	state TEXT NOT NULL,
	pincode VARCHAR(6) NOT NULL,
	landmark VARCHAR(80),
	address_type address_type NOT NULL,
	is_default BOOLEAN DEFAULT false NOT NULL,
	CONSTRAINT pk_address PRIMARY KEY (id),
	CONSTRAINT ck_address_phone_format CHECK (phone ~ '^[0-9]{10}$'),
	CONSTRAINT ck_address_pincode_format CHECK (pincode ~ '^[0-9]{6}$'),
	CONSTRAINT ck_address_line1_length CHECK (char_length(line1) BETWEEN 5 AND 120),
	CONSTRAINT fk_address_customer_id_customer FOREIGN KEY(customer_id) REFERENCES customer (id) ON DELETE CASCADE,
	CONSTRAINT fk_address_pincode_pincode_service FOREIGN KEY(pincode) REFERENCES pincode_service (pincode) ON DELETE RESTRICT
);

CREATE UNIQUE INDEX uq_address_customer_default ON address (customer_id) WHERE is_default;

CREATE INDEX ix_address_pincode ON address (pincode);

CREATE INDEX ix_address_customer_id ON address (customer_id);

CREATE TABLE variant (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	product_id UUID NOT NULL,
	sku TEXT NOT NULL,
	pack_label TEXT NOT NULL,
	pack_type pack_type NOT NULL,
	weight_grams INTEGER,
	unit_count INTEGER,
	price NUMERIC(12, 2) NOT NULL,
	gst_percent NUMERIC(5, 2) NOT NULL,
	stock_qty INTEGER NOT NULL,
	cod_allowed BOOLEAN DEFAULT true NOT NULL,
	is_default BOOLEAN DEFAULT false NOT NULL,
	CONSTRAINT pk_variant PRIMARY KEY (id),
	CONSTRAINT uq_variant_id_product UNIQUE (id, product_id),
	CONSTRAINT ck_variant_positive_price CHECK (price > 0),
	CONSTRAINT ck_variant_gst_range CHECK (gst_percent BETWEEN 0 AND 28),
	CONSTRAINT ck_variant_stock_nonnegative CHECK (stock_qty >= 0),
	CONSTRAINT ck_variant_weight_positive CHECK (weight_grams > 0),
	CONSTRAINT ck_variant_unit_count_positive CHECK (unit_count > 0),
	CONSTRAINT ck_variant_weight_required CHECK (pack_type <> 'weight' OR weight_grams IS NOT NULL),
	CONSTRAINT ck_variant_box_count_required CHECK (pack_type <> 'box' OR unit_count IS NOT NULL),
	CONSTRAINT fk_variant_product_id_product FOREIGN KEY(product_id) REFERENCES product (id) ON DELETE CASCADE,
	CONSTRAINT uq_variant_sku UNIQUE (sku)
);

CREATE INDEX ix_variant_product_id ON variant (product_id);

CREATE UNIQUE INDEX uq_variant_product_default ON variant (product_id) WHERE is_default;

CREATE TABLE wishlist_item (
	customer_id UUID NOT NULL,
	product_id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_wishlist_item PRIMARY KEY (customer_id, product_id),
	CONSTRAINT fk_wishlist_item_customer_id_customer FOREIGN KEY(customer_id) REFERENCES customer (id) ON DELETE CASCADE,
	CONSTRAINT fk_wishlist_item_product_id_product FOREIGN KEY(product_id) REFERENCES product (id) ON DELETE CASCADE
);

CREATE TABLE cart (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	customer_id UUID,
	session_id TEXT,
	pincode VARCHAR(6),
	delivery_date DATE,
	CONSTRAINT pk_cart PRIMARY KEY (id),
	CONSTRAINT ck_cart_pincode_format CHECK (pincode ~ '^[0-9]{6}$'),
	CONSTRAINT ck_cart_one_owner CHECK ((customer_id IS NOT NULL) <> (session_id IS NOT NULL)),
	CONSTRAINT ck_cart_session_nonempty CHECK (session_id IS NULL OR char_length(btrim(session_id)) > 0),
	CONSTRAINT fk_cart_customer_id_customer FOREIGN KEY(customer_id) REFERENCES customer (id) ON DELETE CASCADE,
	CONSTRAINT uq_cart_session_id UNIQUE (session_id)
);

CREATE UNIQUE INDEX ix_cart_customer_id ON cart (customer_id);

CREATE TABLE mango_season (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	variety_name TEXT NOT NULL,
	product_id UUID,
	harvest_start DATE NOT NULL,
	harvest_end DATE NOT NULL,
	preorder_open DATE,
	preorder_close DATE,
	waitlist_enabled BOOLEAN DEFAULT false NOT NULL,
	status mango_season_status NOT NULL,
	CONSTRAINT pk_mango_season PRIMARY KEY (id),
	CONSTRAINT ck_mango_season_harvest_dates CHECK (harvest_end >= harvest_start),
	CONSTRAINT ck_mango_season_preorder_start CHECK (preorder_open <= harvest_start),
	CONSTRAINT ck_mango_season_preorder_dates CHECK (preorder_close >= preorder_open),
	CONSTRAINT ck_mango_season_live_product CHECK (status <> 'live' OR product_id IS NOT NULL),
	CONSTRAINT fk_mango_season_product_id_product FOREIGN KEY(product_id) REFERENCES product (id) ON DELETE RESTRICT
);

CREATE INDEX ix_mango_season_product_id ON mango_season (product_id);

CREATE INDEX ix_mango_season_variety_name ON mango_season (variety_name);

CREATE TABLE waitlist_entry (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	full_name VARCHAR(80),
	email TEXT,
	phone VARCHAR(10),
	product_id UUID NOT NULL,
	variety_name TEXT NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_waitlist_entry PRIMARY KEY (id),
	CONSTRAINT ck_waitlist_entry_contact_required CHECK (email IS NOT NULL OR phone IS NOT NULL),
	CONSTRAINT ck_waitlist_entry_full_name_length CHECK (char_length(full_name) BETWEEN 2 AND 80),
	CONSTRAINT ck_waitlist_entry_email_format CHECK (email ~ '^[^[:space:]@]+@[^[:space:]@]+[.][^[:space:]@]+$'),
	CONSTRAINT ck_waitlist_entry_phone_format CHECK (phone ~ '^[0-9]{10}$'),
	CONSTRAINT uq_waitlist_entry_product_id UNIQUE (product_id, phone),
	CONSTRAINT fk_waitlist_entry_product_id_product FOREIGN KEY(product_id) REFERENCES product (id) ON DELETE CASCADE
);

CREATE INDEX ix_waitlist_entry_product_id ON waitlist_entry (product_id);

CREATE UNIQUE INDEX uq_waitlist_product_email_ci ON waitlist_entry (product_id, lower(email));

CREATE TABLE orders (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	order_number TEXT NOT NULL,
	customer_id UUID,
	status order_status NOT NULL,
	address JSONB NOT NULL,
	pincode VARCHAR(6) NOT NULL,
	delivery_date DATE NOT NULL,
	payment_method payment_method NOT NULL,
	payment_status order_payment_status NOT NULL,
	subtotal NUMERIC(12, 2) NOT NULL,
	shipping NUMERIC(12, 2) NOT NULL,
	gst NUMERIC(12, 2) NOT NULL,
	discount NUMERIC(12, 2) DEFAULT 0,
	grand_total NUMERIC(12, 2) NOT NULL,
	customer_notes VARCHAR(200),
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_orders PRIMARY KEY (id),
	CONSTRAINT ck_orders_pincode_format CHECK (pincode ~ '^[0-9]{6}$'),
	CONSTRAINT uq_orders_id_total UNIQUE (id, grand_total),
	CONSTRAINT ck_orders_order_number_format CHECK (order_number ~ '^GS-[0-9]+$'),
	CONSTRAINT ck_orders_address_object CHECK (jsonb_typeof(address) = 'object'),
	CONSTRAINT ck_orders_address_keys CHECK (address ?& ARRAY['full_name','phone','line1','city','state','pincode','address_type']),
	CONSTRAINT ck_orders_address_fields CHECK (jsonb_typeof(address->'full_name') = 'string' AND char_length(address->>'full_name') > 0 AND jsonb_typeof(address->'phone') = 'string' AND (address->>'phone') ~ '^[0-9]{10}$' AND jsonb_typeof(address->'line1') = 'string' AND char_length(address->>'line1') BETWEEN 5 AND 120 AND jsonb_typeof(address->'city') = 'string' AND char_length(address->>'city') > 0 AND jsonb_typeof(address->'state') = 'string' AND char_length(address->>'state') > 0 AND jsonb_typeof(address->'pincode') = 'string' AND jsonb_typeof(address->'address_type') = 'string' AND (address->>'address_type') IN ('home','office','other')),
	CONSTRAINT ck_orders_address_pincode CHECK ((address ->> 'pincode') IS NOT NULL AND (address ->> 'pincode') = pincode),
	CONSTRAINT ck_orders_amounts_nonnegative CHECK (subtotal >= 0 AND shipping >= 0 AND gst >= 0 AND COALESCE(discount, 0) >= 0 AND grand_total >= 0),
	CONSTRAINT ck_orders_grand_total_formula CHECK (grand_total = subtotal + shipping - COALESCE(discount, 0)),
	CONSTRAINT uq_orders_order_number UNIQUE (order_number),
	CONSTRAINT fk_orders_customer_id_customer FOREIGN KEY(customer_id) REFERENCES customer (id) ON DELETE RESTRICT
);

CREATE INDEX ix_orders_customer_id ON orders (customer_id);

CREATE INDEX ix_orders_status ON orders (status);

CREATE TABLE device_token (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	customer_id UUID NOT NULL,
	fcm_token TEXT NOT NULL,
	platform device_platform NOT NULL,
	notifications_enabled BOOLEAN DEFAULT false NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_device_token PRIMARY KEY (id),
	CONSTRAINT fk_device_token_customer_id_customer FOREIGN KEY(customer_id) REFERENCES customer (id) ON DELETE CASCADE,
	CONSTRAINT uq_device_token_fcm_token UNIQUE (fcm_token)
);

CREATE INDEX ix_device_token_customer_id ON device_token (customer_id);

CREATE TABLE push_message (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	customer_id UUID NOT NULL,
	title TEXT NOT NULL,
	body TEXT NOT NULL,
	type push_type NOT NULL,
	order_number TEXT,
	product_slug TEXT,
	is_read BOOLEAN DEFAULT false NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_push_message PRIMARY KEY (id),
	CONSTRAINT fk_push_message_customer_id_customer FOREIGN KEY(customer_id) REFERENCES customer (id) ON DELETE CASCADE
);

CREATE INDEX ix_push_message_customer_id ON push_message (customer_id);

CREATE TABLE auth_session (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	customer_id UUID,
	admin_id UUID,
	refresh_digest VARCHAR(64),
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
	CONSTRAINT pk_auth_session PRIMARY KEY (id),
	CONSTRAINT ck_auth_session_one_identity CHECK ((customer_id IS NOT NULL) <> (admin_id IS NOT NULL)),
	CONSTRAINT fk_auth_session_customer_id_customer FOREIGN KEY(customer_id) REFERENCES customer (id) ON DELETE CASCADE,
	CONSTRAINT fk_auth_session_admin_id_admin_user FOREIGN KEY(admin_id) REFERENCES admin_user (id) ON DELETE CASCADE,
	CONSTRAINT uq_auth_session_refresh_digest UNIQUE (refresh_digest)
);

CREATE INDEX ix_auth_session_customer_id ON auth_session (customer_id);

CREATE INDEX ix_auth_session_admin_id ON auth_session (admin_id);

CREATE TABLE admin_audit (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	admin_id UUID,
	method VARCHAR(10) NOT NULL,
	path VARCHAR(300) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_admin_audit PRIMARY KEY (id),
	CONSTRAINT fk_admin_audit_admin_id_admin_user FOREIGN KEY(admin_id) REFERENCES admin_user (id) ON DELETE SET NULL
);

CREATE INDEX ix_admin_audit_admin_id ON admin_audit (admin_id);

CREATE TABLE cart_line (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	cart_id UUID NOT NULL,
	product_id UUID NOT NULL,
	variant_id UUID NOT NULL,
	qty INTEGER NOT NULL,
	unit_price NUMERIC(12, 2) NOT NULL,
	line_total NUMERIC(12, 2) GENERATED ALWAYS AS (qty * unit_price) STORED NOT NULL,
	CONSTRAINT pk_cart_line PRIMARY KEY (id),
	CONSTRAINT fk_cart_line_variant_product FOREIGN KEY(variant_id, product_id) REFERENCES variant (id, product_id) ON DELETE RESTRICT,
	CONSTRAINT uq_cart_line_cart_id UNIQUE (cart_id, variant_id),
	CONSTRAINT ck_cart_line_qty_range CHECK (qty BETWEEN 1 AND 20),
	CONSTRAINT ck_cart_line_price_positive CHECK (unit_price > 0),
	CONSTRAINT fk_cart_line_cart_id_cart FOREIGN KEY(cart_id) REFERENCES cart (id) ON DELETE CASCADE,
	CONSTRAINT fk_cart_line_product_id_product FOREIGN KEY(product_id) REFERENCES product (id) ON DELETE RESTRICT
);

CREATE INDEX ix_cart_line_product_id ON cart_line (product_id);

CREATE INDEX ix_cart_line_variant_id ON cart_line (variant_id);

CREATE INDEX ix_cart_line_cart_id ON cart_line (cart_id);

CREATE TABLE order_line (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	order_id UUID NOT NULL,
	product_name TEXT NOT NULL,
	variant_label TEXT NOT NULL,
	sku TEXT NOT NULL,
	qty INTEGER NOT NULL,
	unit_price NUMERIC(12, 2) NOT NULL,
	line_total NUMERIC(12, 2) GENERATED ALWAYS AS (qty * unit_price) STORED NOT NULL,
	CONSTRAINT pk_order_line PRIMARY KEY (id),
	CONSTRAINT ck_order_line_positive_line CHECK (qty > 0 AND unit_price > 0),
	CONSTRAINT fk_order_line_order_id_orders FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE
);

CREATE INDEX ix_order_line_order_id ON order_line (order_id);

CREATE TABLE payment (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	order_id UUID NOT NULL,
	method payment_method NOT NULL,
	status payment_status NOT NULL,
	amount NUMERIC(12, 2) NOT NULL,
	gateway_ref TEXT,
	CONSTRAINT pk_payment PRIMARY KEY (id),
	CONSTRAINT fk_payment_order_amount FOREIGN KEY(order_id, amount) REFERENCES orders (id, grand_total) ON DELETE CASCADE,
	CONSTRAINT ck_payment_amount_nonnegative CHECK (amount >= 0)
);

CREATE INDEX ix_payment_order_id ON payment (order_id);

CREATE TABLE checkout_session (
	order_id UUID NOT NULL,
	customer_id UUID NOT NULL,
	request_id UUID NOT NULL,
	request_hash TEXT NOT NULL,
	backend TEXT NOT NULL,
	gateway_order_id TEXT,
	gateway_payment_id TEXT,
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
	released_at TIMESTAMP WITH TIME ZONE,
	CONSTRAINT pk_checkout_session PRIMARY KEY (order_id),
	CONSTRAINT uq_checkout_session_customer_id UNIQUE (customer_id, request_id),
	CONSTRAINT ck_checkout_session_backend_value CHECK (backend IN ('cod','demo','razorpay')),
	CONSTRAINT fk_checkout_session_order_id_orders FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE,
	CONSTRAINT fk_checkout_session_customer_id_customer FOREIGN KEY(customer_id) REFERENCES customer (id) ON DELETE RESTRICT,
	CONSTRAINT uq_checkout_session_gateway_order_id UNIQUE (gateway_order_id),
	CONSTRAINT uq_checkout_session_gateway_payment_id UNIQUE (gateway_payment_id)
);

CREATE INDEX ix_checkout_session_customer_id ON checkout_session (customer_id);

CREATE TABLE stock_reservation (
	order_id UUID NOT NULL,
	variant_id UUID NOT NULL,
	qty INTEGER NOT NULL,
	CONSTRAINT pk_stock_reservation PRIMARY KEY (order_id, variant_id),
	CONSTRAINT ck_stock_reservation_quantity CHECK (qty BETWEEN 1 AND 20),
	CONSTRAINT fk_stock_reservation_order_id_orders FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE,
	CONSTRAINT fk_stock_reservation_variant_id_variant FOREIGN KEY(variant_id) REFERENCES variant (id) ON DELETE RESTRICT
);

CREATE TABLE refund_request (
	order_id UUID NOT NULL,
	amount NUMERIC(12, 2) NOT NULL,
	status TEXT DEFAULT 'pending' NOT NULL,
	gateway_ref TEXT,
	last_error VARCHAR(80),
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_refund_request PRIMARY KEY (order_id),
	CONSTRAINT ck_refund_request_positive_amount CHECK (amount > 0),
	CONSTRAINT ck_refund_request_status_value CHECK (status IN ('pending','submitted','processed')),
	CONSTRAINT fk_refund_request_order_id_orders FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE,
	CONSTRAINT uq_refund_request_gateway_ref UNIQUE (gateway_ref)
);

CREATE TABLE push_delivery (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	message_id UUID NOT NULL,
	device_id UUID NOT NULL,
	attempts INTEGER DEFAULT 0 NOT NULL,
	sent_at TIMESTAMP WITH TIME ZONE,
	last_error VARCHAR(80),
	CONSTRAINT pk_push_delivery PRIMARY KEY (id),
	CONSTRAINT uq_push_delivery_message_id UNIQUE (message_id, device_id),
	CONSTRAINT ck_push_delivery_attempts_nonnegative CHECK (attempts >= 0),
	CONSTRAINT fk_push_delivery_message_id_push_message FOREIGN KEY(message_id) REFERENCES push_message (id) ON DELETE CASCADE,
	CONSTRAINT fk_push_delivery_device_id_device_token FOREIGN KEY(device_id) REFERENCES device_token (id) ON DELETE CASCADE
);

CREATE INDEX ix_push_delivery_device_id ON push_delivery (device_id);

CREATE INDEX ix_push_delivery_message_id ON push_delivery (message_id);

CREATE TABLE owner_alert (
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	order_id UUID NOT NULL,
	kind VARCHAR(30) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	seen_at TIMESTAMP WITH TIME ZONE,
	sent_at TIMESTAMP WITH TIME ZONE,
	next_attempt_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	attempts INTEGER DEFAULT 0 NOT NULL,
	last_error VARCHAR(120),
	CONSTRAINT pk_owner_alert PRIMARY KEY (id),
	CONSTRAINT uq_owner_alert_order_id UNIQUE (order_id, kind),
	CONSTRAINT ck_owner_alert_attempts_nonnegative CHECK (attempts >= 0),
	CONSTRAINT fk_owner_alert_order_id_orders FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE
);

CREATE INDEX ix_owner_alert_order_id ON owner_alert (order_id);

CREATE TABLE shipment (
	order_id UUID NOT NULL,
	id UUID DEFAULT gen_random_uuid() NOT NULL,
	carrier VARCHAR(100) NOT NULL,
	tracking_number VARCHAR(100) NOT NULL,
	tracking_url VARCHAR(2048),
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	CONSTRAINT pk_shipment PRIMARY KEY (id),
	CONSTRAINT fk_shipment_order_id_orders FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX ix_shipment_order_id ON shipment (order_id);

CREATE OR REPLACE FUNCTION gs_lock_variant_product() RETURNS trigger
    LANGUAGE plpgsql AS $$
    BEGIN
      -- Serialize variant/default changes for each product, in stable UUID order.
      IF TG_OP = 'INSERT' THEN
        PERFORM id FROM product WHERE id = NEW.product_id FOR UPDATE;
      ELSIF TG_OP = 'DELETE' THEN
        PERFORM id FROM product WHERE id = OLD.product_id FOR UPDATE;
      ELSE
        PERFORM id FROM product WHERE id IN (OLD.product_id, NEW.product_id) ORDER BY id FOR UPDATE;
      END IF;
      IF TG_OP = 'DELETE' THEN RETURN OLD; ELSE RETURN NEW; END IF;
    END $$;

CREATE OR REPLACE FUNCTION gs_check_default_variant() RETURNS trigger
    LANGUAGE plpgsql AS $$
    DECLARE ids uuid[]; target uuid;
    BEGIN
      IF TG_TABLE_NAME = 'product' THEN
        ids := ARRAY[NEW.id];
      ELSIF TG_OP = 'DELETE' THEN
        ids := ARRAY[OLD.product_id];
      ELSIF TG_OP = 'INSERT' THEN
        ids := ARRAY[NEW.product_id];
      ELSE
        ids := ARRAY[OLD.product_id, NEW.product_id];
      END IF;
      FOREACH target IN ARRAY ids LOOP
        IF EXISTS (SELECT 1 FROM product WHERE id = target) AND
           (SELECT count(*) FROM variant WHERE product_id = target AND is_default) <> 1 THEN
          RAISE EXCEPTION 'Product must have exactly one default variant'
            USING ERRCODE = '23514', CONSTRAINT = 'ck_product_exactly_one_default_variant';
        END IF;
      END LOOP;
      RETURN NULL;
    END $$;

CREATE OR REPLACE FUNCTION gs_check_mango_link() RETURNS trigger
    LANGUAGE plpgsql AS $$
    DECLARE linked_category category;
    BEGIN
      IF NEW.product_id IS NOT NULL THEN
        SELECT category INTO linked_category FROM product WHERE id = NEW.product_id FOR SHARE;
        IF linked_category IS NOT NULL AND linked_category <> 'mango' THEN
          RAISE EXCEPTION 'Mango seasons and waitlists require a mango product'
            USING ERRCODE = '23514', CONSTRAINT = 'ck_mango_product_category';
        END IF;
      END IF;
      RETURN NEW;
    END $$;

CREATE OR REPLACE FUNCTION gs_guard_product_category() RETURNS trigger
    LANGUAGE plpgsql AS $$
    BEGIN
      IF NEW.category <> 'mango' AND
         (EXISTS (SELECT 1 FROM mango_season WHERE product_id = OLD.id) OR
          EXISTS (SELECT 1 FROM waitlist_entry WHERE product_id = OLD.id)) THEN
        RAISE EXCEPTION 'Product with mango seasons or waitlist must remain mango'
          USING ERRCODE = '23514', CONSTRAINT = 'ck_mango_product_category';
      END IF;
      RETURN NEW;
    END $$;

CREATE OR REPLACE FUNCTION gs_freeze_order_address() RETURNS trigger
    LANGUAGE plpgsql AS $$
    BEGIN
      IF NEW.address IS DISTINCT FROM OLD.address OR NEW.pincode IS DISTINCT FROM OLD.pincode THEN
        RAISE EXCEPTION 'Placed order address is immutable'
          USING ERRCODE = '23514', CONSTRAINT = 'ck_order_address_immutable';
      END IF;
      RETURN NEW;
    END $$;

CREATE OR REPLACE FUNCTION gs_touch_device_token() RETURNS trigger
    LANGUAGE plpgsql AS $$
    BEGIN NEW.updated_at := statement_timestamp(); RETURN NEW; END $$;

DROP TRIGGER IF EXISTS gs_variant_lock ON variant;

CREATE TRIGGER gs_variant_lock BEFORE INSERT OR UPDATE OR DELETE ON variant FOR EACH ROW EXECUTE FUNCTION gs_lock_variant_product();

DROP TRIGGER IF EXISTS gs_product_default ON product;

CREATE CONSTRAINT TRIGGER gs_product_default AFTER INSERT OR UPDATE ON product DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION gs_check_default_variant();

DROP TRIGGER IF EXISTS gs_variant_default ON variant;

CREATE CONSTRAINT TRIGGER gs_variant_default AFTER INSERT OR UPDATE OR DELETE ON variant DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION gs_check_default_variant();

DROP TRIGGER IF EXISTS gs_mango_link ON mango_season;

CREATE TRIGGER gs_mango_link BEFORE INSERT OR UPDATE ON mango_season FOR EACH ROW EXECUTE FUNCTION gs_check_mango_link();

DROP TRIGGER IF EXISTS gs_waitlist_link ON waitlist_entry;

CREATE TRIGGER gs_waitlist_link BEFORE INSERT OR UPDATE ON waitlist_entry FOR EACH ROW EXECUTE FUNCTION gs_check_mango_link();

DROP TRIGGER IF EXISTS gs_product_category ON product;

CREATE TRIGGER gs_product_category BEFORE UPDATE OF category ON product FOR EACH ROW EXECUTE FUNCTION gs_guard_product_category();

DROP TRIGGER IF EXISTS gs_order_address ON orders;

CREATE TRIGGER gs_order_address BEFORE UPDATE ON orders FOR EACH ROW EXECUTE FUNCTION gs_freeze_order_address();

DROP TRIGGER IF EXISTS gs_device_updated ON device_token;

CREATE TRIGGER gs_device_updated BEFORE UPDATE ON device_token FOR EACH ROW EXECUTE FUNCTION gs_touch_device_token();

COMMIT;
