"""DDL hooks included in both init-db and export-schema.

Future Alembic migrations must explicitly preserve these functions/triggers.
"""
from sqlalchemy import DDL, event


STATEMENTS = [
    """CREATE OR REPLACE FUNCTION gs_lock_variant_product() RETURNS trigger
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
    END $$""",
    """CREATE OR REPLACE FUNCTION gs_check_default_variant() RETURNS trigger
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
    END $$""",
    """CREATE OR REPLACE FUNCTION gs_check_mango_link() RETURNS trigger
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
    END $$""",
    """CREATE OR REPLACE FUNCTION gs_guard_product_category() RETURNS trigger
    LANGUAGE plpgsql AS $$
    BEGIN
      IF NEW.category <> 'mango' AND
         (EXISTS (SELECT 1 FROM mango_season WHERE product_id = OLD.id) OR
          EXISTS (SELECT 1 FROM waitlist_entry WHERE product_id = OLD.id)) THEN
        RAISE EXCEPTION 'Product with mango seasons or waitlist must remain mango'
          USING ERRCODE = '23514', CONSTRAINT = 'ck_mango_product_category';
      END IF;
      RETURN NEW;
    END $$""",
    """CREATE OR REPLACE FUNCTION gs_freeze_order_address() RETURNS trigger
    LANGUAGE plpgsql AS $$
    BEGIN
      IF NEW.address IS DISTINCT FROM OLD.address OR NEW.pincode IS DISTINCT FROM OLD.pincode THEN
        RAISE EXCEPTION 'Placed order address is immutable'
          USING ERRCODE = '23514', CONSTRAINT = 'ck_order_address_immutable';
      END IF;
      RETURN NEW;
    END $$""",
    """CREATE OR REPLACE FUNCTION gs_touch_device_token() RETURNS trigger
    LANGUAGE plpgsql AS $$
    BEGIN NEW.updated_at := statement_timestamp(); RETURN NEW; END $$""",
    "DROP TRIGGER IF EXISTS gs_variant_lock ON variant",
    "CREATE TRIGGER gs_variant_lock BEFORE INSERT OR UPDATE OR DELETE ON variant FOR EACH ROW EXECUTE FUNCTION gs_lock_variant_product()",
    "DROP TRIGGER IF EXISTS gs_product_default ON product",
    "CREATE CONSTRAINT TRIGGER gs_product_default AFTER INSERT OR UPDATE ON product DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION gs_check_default_variant()",
    "DROP TRIGGER IF EXISTS gs_variant_default ON variant",
    "CREATE CONSTRAINT TRIGGER gs_variant_default AFTER INSERT OR UPDATE OR DELETE ON variant DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION gs_check_default_variant()",
    "DROP TRIGGER IF EXISTS gs_mango_link ON mango_season",
    "CREATE TRIGGER gs_mango_link BEFORE INSERT OR UPDATE ON mango_season FOR EACH ROW EXECUTE FUNCTION gs_check_mango_link()",
    "DROP TRIGGER IF EXISTS gs_waitlist_link ON waitlist_entry",
    "CREATE TRIGGER gs_waitlist_link BEFORE INSERT OR UPDATE ON waitlist_entry FOR EACH ROW EXECUTE FUNCTION gs_check_mango_link()",
    "DROP TRIGGER IF EXISTS gs_product_category ON product",
    "CREATE TRIGGER gs_product_category BEFORE UPDATE OF category ON product FOR EACH ROW EXECUTE FUNCTION gs_guard_product_category()",
    "DROP TRIGGER IF EXISTS gs_order_address ON orders",
    "CREATE TRIGGER gs_order_address BEFORE UPDATE ON orders FOR EACH ROW EXECUTE FUNCTION gs_freeze_order_address()",
    "DROP TRIGGER IF EXISTS gs_device_updated ON device_token",
    "CREATE TRIGGER gs_device_updated BEFORE UPDATE ON device_token FOR EACH ROW EXECUTE FUNCTION gs_touch_device_token()",
]


def register_invariants(metadata):
    for statement in STATEMENTS:
        event.listen(metadata, "after_create", DDL(statement).execute_if(dialect="postgresql"))
