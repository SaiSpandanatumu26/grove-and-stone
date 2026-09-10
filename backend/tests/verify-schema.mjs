// Runs exported PostgreSQL DDL against PGlite, including deferred triggers.
// npm ci; node verify-schema.mjs ../schema.sql
import { PGlite } from '@electric-sql/pglite';
import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';

const db = new PGlite();
let passed = 0;
async function succeeds(name, sql, verify) {
  await db.exec('BEGIN');
  try {
    await db.exec(sql);
    await db.exec('SET CONSTRAINTS ALL IMMEDIATE');
    if (verify) await verify();
    passed++;
    console.log(`PASS ${name}`);
  } finally { await db.exec('ROLLBACK'); }
}
async function rejects(name, sql, code, constraint) {
  await db.exec('BEGIN');
  let failure;
  try {
    await db.exec(sql);
    await db.exec('SET CONSTRAINTS ALL IMMEDIATE');
  } catch (error) { failure = error; }
  finally { await db.exec('ROLLBACK'); }
  assert.ok(failure, `${name}: unexpected success`);
  assert.equal(failure.code, code, `${name}: ${failure.message}`);
  if (constraint) assert.equal(failure.constraint, constraint, name);
  passed++;
  console.log(`PASS ${name}`);
}
const p1 = '00000000-0000-4000-8000-000000000001';
const p2 = '00000000-0000-4000-8000-000000000002';
const v1 = '00000000-0000-4000-8000-000000000011';
const v2 = '00000000-0000-4000-8000-000000000012';
const c1 = '00000000-0000-4000-8000-000000000021';
const cart = '00000000-0000-4000-8000-000000000031';
const order = '00000000-0000-4000-8000-000000000041';
const product = (id, slug, category = 'mango') => `INSERT INTO product
  (id,name,slug,category,origin,short_description,long_description,images,season_status)
  VALUES ('${id}','Test fruit','${slug}','${category}','Test farm','Test copy','Test body',ARRAY['/test.jpg'],'in_season');`;
const variant = (id, productId, sku, isDefault = true) => `INSERT INTO variant
  (id,product_id,sku,pack_label,pack_type,unit_count,price,gst_percent,stock_qty,is_default)
  VALUES ('${id}','${productId}','${sku}','6 pieces','box',6,100.25,5,10,${isDefault});`;
const address = `INSERT INTO address(customer_id,full_name,phone,line1,city,state,pincode,address_type,is_default)
  VALUES ('${c1}','Test Shopper','9876543210','Test street','Mumbai','Maharashtra','400001','home',true);`;

try {
  await db.exec(readFileSync(process.argv[2] ?? '../schema.sql', 'utf8'));
  const tables = await db.query("SELECT count(*)::int AS n FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'");
  assert.equal(tables.rows[0].n, 22);
  passed++; console.log('PASS initial schema creates 17 domain and 5 infrastructure tables');
  await db.exec(`BEGIN;
    INSERT INTO customer(id,full_name,email,phone,password) VALUES
      ('${c1}','Test Shopper','test@example.com','9876543210','scrypt:test-fixture');
    INSERT INTO pincode_service(pincode,city,state,serviceable,mango_eligible,delivery_days_min,delivery_days_max)
      VALUES ('400001','Mumbai','Maharashtra',true,true,1,3);
    ${address}
    ${product(p1, 'test-mango')}${variant(v1, p1, 'MANGO')}
    ${product(p2, 'test-almond', 'dry_fruit')}${variant(v2, p2, 'ALMOND')}
    INSERT INTO cart(id,customer_id) VALUES ('${cart}','${c1}');
    INSERT INTO cart_line(cart_id,product_id,variant_id,qty,unit_price)
      VALUES ('${cart}','${p1}','${v1}',2,100.25);
    INSERT INTO orders(id,order_number,customer_id,status,address,pincode,delivery_date,payment_method,payment_status,subtotal,shipping,gst,grand_total)
      VALUES ('${order}','GS-10482','${c1}','confirmed',
        '{"full_name":"Test Shopper","phone":"9876543210","line1":"Test street","city":"Mumbai","state":"Maharashtra","pincode":"400001","address_type":"home"}',
        '400001',CURRENT_DATE+2,'cod','cod',200.50,0,9.55,200.50);
    INSERT INTO order_line(order_id,product_name,variant_label,sku,qty,unit_price)
      VALUES ('${order}','Test fruit','6 pieces','MANGO',2,100.25);
    INSERT INTO payment(order_id,method,status,amount) VALUES ('${order}','cod','cod_pending',200.50);
    COMMIT;`);
  passed++; console.log('PASS complete valid customer/catalog/cart/order/payment transaction');
  const wishlist = `INSERT INTO wishlist_item(customer_id,product_id) VALUES('${c1}','${p1}');`;
  await succeeds('wishlist entry', wishlist);
  await rejects('duplicate wishlist entry', wishlist + wishlist, '23505');
  await rejects('wishlist requires an existing product', `INSERT INTO wishlist_item(customer_id,product_id) VALUES('${c1}','00000000-0000-4000-8000-000000000099')`, '23503');

  await succeeds('decimal line totals', `UPDATE cart_line SET qty=3`, async () => {
    assert.equal((await db.query('SELECT line_total::text AS total FROM cart_line')).rows[0].total, '300.75');
  });
  await rejects('quantity zero', 'UPDATE cart_line SET qty=0', '23514', 'ck_cart_line_qty_range');
  await rejects('quantity above 20', 'UPDATE cart_line SET qty=21', '23514', 'ck_cart_line_qty_range');
  await rejects('quantity NULL', 'UPDATE cart_line SET qty=NULL', '23502');
  await rejects('variant/product mismatch', `UPDATE cart_line SET product_id='${p2}'`, '23503', 'fk_cart_line_variant_product');
  await rejects('duplicate line', `INSERT INTO cart_line(cart_id,product_id,variant_id,qty,unit_price) VALUES('${cart}','${p1}','${v1}',1,100.25)`, '23505');
  await rejects('generated line total cannot be overridden', 'UPDATE cart_line SET line_total=1', '428C9');
  await rejects('negative stock', 'UPDATE variant SET stock_qty=-1', '23514', 'ck_variant_stock_nonnegative');
  await rejects('zero price', 'UPDATE variant SET price=0', '23514', 'ck_variant_positive_price');
  await rejects('GST outside 0 to 28', 'UPDATE variant SET gst_percent=29', '23514', 'ck_variant_gst_range');
  await rejects('weight pack needs grams', "UPDATE variant SET pack_type='weight'", '23514', 'ck_variant_weight_required');
  await rejects('box pack needs count', 'UPDATE variant SET unit_count=NULL', '23514', 'ck_variant_box_count_required');
  await rejects('invalid enum', "UPDATE product SET category='vegetable'", '22P02');
  await rejects('empty gallery', "UPDATE product SET images=ARRAY[]::text[]", '23514', 'ck_product_images_required');
  await rejects('null image entry', 'UPDATE product SET images=ARRAY[NULL]::text[]', '23514', 'ck_product_images_required');
  await rejects('invalid product name length', "UPDATE product SET name='A'", '23514', 'ck_product_name_length');
  await rejects('duplicate SKU', "UPDATE variant SET sku='MANGO'", '23505');
  await rejects('duplicate slug', "UPDATE product SET slug='test-mango'", '23505');
  await rejects('duplicate default pack', variant('00000000-0000-4000-8000-000000000013', p1, 'NEW'), '23505');
  await rejects('removing only default pack', 'UPDATE variant SET is_default=false', '23514', 'ck_product_exactly_one_default_variant');
  await rejects('creating product without pack', product('00000000-0000-4000-8000-000000000003', 'new-mango'), '23514', 'ck_product_exactly_one_default_variant');
  await succeeds('default pack can switch in one transaction', `UPDATE variant SET is_default=false WHERE id='${v1}'; ${variant('00000000-0000-4000-8000-000000000013', p1, 'NEW')}`);
  await succeeds('delete unreferenced product cascades variants', `DELETE FROM product WHERE id='${p2}'`);
  await rejects('customer has only one cart', `INSERT INTO cart(customer_id) VALUES ('${c1}')`, '23505');
  await rejects('ownerless cart', 'INSERT INTO cart DEFAULT VALUES', '23514', 'ck_cart_one_owner');
  await rejects('cart cannot have two owners', "UPDATE cart SET session_id='guest'", '23514', 'ck_cart_one_owner');
  await succeeds('guest cart may store unknown pincode', "INSERT INTO cart(session_id,pincode) VALUES('guest','999999')");
  await rejects('duplicate guest cart', "INSERT INTO cart(session_id) VALUES('guest'),('guest')", '23505');
  await rejects('duplicate default address', address, '23505');
  await rejects('address requires known pincode', "UPDATE address SET pincode='999999'", '23503');
  await rejects('phone format', "UPDATE customer SET phone='123'", '23514', 'ck_customer_phone_format');
  await rejects('case insensitive email uniqueness', "INSERT INTO customer(full_name,email,phone,password) VALUES('Other Person','TEST@example.com','9876543211','scrypt:test-fixture')", '23505');
  await rejects('raw passwords blocked', "UPDATE customer SET password='plaintext'", '23514', 'ck_customer_password_hash');
  await rejects('coverage format', "UPDATE pincode_service SET pincode='40AB01'", '23514', 'ck_pincode_service_pincode_format');
  await rejects('mango serviceability requires coverage', 'UPDATE pincode_service SET serviceable=false', '23514', 'ck_pincode_service_mango_serviceable');
  await rejects('delivery interval ordering', 'UPDATE pincode_service SET delivery_days_max=0', '23514', 'ck_pincode_service_delivery_days');
  const waitlist = `INSERT INTO waitlist_entry(product_id,variety_name,phone) VALUES('${p1}','Alphonso','9876543210')`;
  await succeeds('phone-only waitlist', waitlist);
  await rejects('waitlist needs contact', `INSERT INTO waitlist_entry(product_id,variety_name) VALUES('${p1}','Alphonso')`, '23514', 'ck_waitlist_entry_contact_required');
  await rejects('duplicate waitlist contact', `${waitlist};${waitlist}`, '23505');
  await rejects('waitlist requires mango product', `INSERT INTO waitlist_entry(product_id,variety_name,phone) VALUES('${p2}','Alphonso','9876543210')`, '23514', 'ck_mango_product_category');
  const season = `INSERT INTO mango_season(product_id,variety_name,harvest_start,harvest_end,status) VALUES('${p1}','Alphonso',CURRENT_DATE,CURRENT_DATE+30,'live')`;
  await succeeds('valid mango season', season);
  await rejects('live mango season requires product', `INSERT INTO mango_season(variety_name,harvest_start,harvest_end,status) VALUES('Alphonso',CURRENT_DATE,CURRENT_DATE+30,'live')`, '23514', 'ck_mango_season_live_product');
  await rejects('linked mango cannot become dry fruit', `${season}; UPDATE product SET category='dry_fruit' WHERE id='${p1}'`, '23514', 'ck_mango_product_category');
  await rejects('payment must equal order total', 'UPDATE payment SET amount=1', '23503', 'fk_payment_order_amount');
  await rejects('order totals cannot double count GST', 'UPDATE orders SET grand_total=210.05', '23514', 'ck_orders_grand_total_formula');
  await rejects('placed address is immutable', `UPDATE orders SET address=jsonb_set(address,'{line1}','"New street"')`, '23514', 'ck_order_address_immutable');
  await succeeds('later catalog/address edits preserve order snapshots', `UPDATE product SET name='Renamed'; UPDATE address SET line1='New street'`, async () => {
    assert.equal((await db.query('SELECT product_name FROM order_line')).rows[0].product_name, 'Test fruit');
    assert.equal((await db.query("SELECT address->>'line1' AS line FROM orders")).rows[0].line, 'Test street');
  });
  const banner = (url) => `INSERT INTO cms_banner(title,season_state,cta_label,cta_url,image,start_date,end_date) VALUES('Mangoes','live','Shop','${url}','/hero.jpg',CURRENT_DATE,CURRENT_DATE+1)`;
  await succeeds('internal campaign URL', banner('/mango-season'));
  await rejects('external campaign URL', banner('https://example.com'), '23514', 'ck_cms_banner_internal_cta');
  await rejects('protocol relative campaign URL', banner('//example.com'), '23514', 'ck_cms_banner_internal_cta');
  await rejects('encoded slash campaign URL', banner('/%2fexample.com'), '23514', 'ck_cms_banner_internal_cta');
  await rejects('only Android devices allowed', `INSERT INTO device_token(customer_id,fcm_token,platform) VALUES('${c1}','test','ios')`, '22P02');
  console.log(`\n${passed} PostgreSQL schema checks passed.`);
} finally { await db.close(); }
