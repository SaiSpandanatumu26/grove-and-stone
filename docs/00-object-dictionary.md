# Object dictionary

Brand: **Grove & Stone**. Market: India. Catalog: exotic fruits, dry fruits, natural mangoes (seasonal).

Screen files reuse these object names. Do not invent new field names on a screen unless the field is added here first.

---

## Customer

Shopper account.

| Attribute | Type | Required | Notes |
| --- | --- | --- | --- |
| id | uuid | yes | System generated |
| full_name | text (2–80) | yes | Display name |
| email | email | yes | Unique, login id |
| phone | 10-digit mobile | yes | Indian mobile, unique |
| password | password | yes | Min 8 chars; never shown back |
| created_at | datetime | yes | System generated |

---

## Address

Shipping address. Belongs to Customer. Copied onto Order at checkout.

| Attribute | Type | Required | Notes |
| --- | --- | --- | --- |
| id | uuid | yes | |
| customer_id | uuid | yes | FK Customer |
| full_name | text | yes | Receiver name |
| phone | 10-digit mobile | yes | Receiver phone |
| line1 | text (5–120) | yes | House / street |
| line2 | text (0–120) | no | Area / society |
| city | text | yes | |
| state | text / dropdown | yes | Indian state |
| pincode | 6-digit | yes | Must match PincodeService |
| landmark | text (0–80) | no | |
| address_type | enum | yes | `home` / `office` / `other` |
| is_default | boolean | yes | One default per customer |

---

## Product

Sellable item. Category is one of `exotic`, `dry_fruit`, `mango`.

| Attribute | Type | Required | Notes |
| --- | --- | --- | --- |
| id | uuid | yes | |
| name | text (2–80) | yes | e.g. Alphonso Mango, Mamra Almonds |
| slug | slug | yes | URL key |
| category | enum | yes | `exotic` / `dry_fruit` / `mango` |
| origin | text | yes | Farm / region, e.g. Ratnagiri, Kashmir |
| short_description | text (≤160) | yes | Card copy |
| long_description | rich text | yes | PDP body |
| images | image list | yes | At least 1; first is primary |
| season_status | enum | yes | `in_season` / `limited` / `coming_soon` / `off_season` |
| handling_notes | text | no | Ripen / store / wash |
| ripeness_note | text | no | Mangoes: ripeness at delivery |
| farm_story | text | no | Natural / farm claim — must be factual |
| is_gift_eligible | boolean | yes | Dry fruits / gift tins |
| is_active | boolean | yes | Hidden if false |
| harvest_window | text | no | Mangoes: e.g. Apr–Jun |

---

## Variant

Buyable pack of a Product (weight, box, or tin).

| Attribute | Type | Required | Notes |
| --- | --- | --- | --- |
| id | uuid | yes | |
| product_id | uuid | yes | FK Product |
| sku | text | yes | Unique |
| pack_label | text | yes | e.g. 500 g, 1 kg, 3-dozen box |
| pack_type | enum | yes | `weight` / `box` / `tin` |
| weight_grams | integer | no | For `weight` packs |
| unit_count | integer | no | For mango boxes (dozen / piece) |
| price | INR | yes | Inclusive of GST unless noted |
| gst_percent | decimal | yes | Typical 5 or 12 |
| stock_qty | integer | yes | 0 = sold out |
| cod_allowed | boolean | yes | False for high-value mango boxes |
| is_default | boolean | yes | Pre-selected on PDP |

---

## Cart

Guest (session) or logged-in cart. One active cart.

| Attribute | Type | Required | Notes |
| --- | --- | --- | --- |
| id | uuid | yes | |
| customer_id | uuid | no | Null for guest |
| session_id | text | no | Guest cart |
| pincode | 6-digit | no | Last checked pincode |
| delivery_date | date | no | Preferred perishable date |

---

## CartLine

Line in a Cart.

| Attribute | Type | Required | Notes |
| --- | --- | --- | --- |
| id | uuid | yes | |
| cart_id | uuid | yes | |
| product_id | uuid | yes | |
| variant_id | uuid | yes | |
| qty | integer (1–20) | yes | |
| unit_price | INR | yes | Snapshot of Variant.price |
| line_total | INR | yes | qty × unit_price |

---

## PincodeService

Delivery coverage for a pincode.

| Attribute | Type | Required | Notes |
| --- | --- | --- | --- |
| pincode | 6-digit | yes | PK |
| city | text | yes | |
| state | text | yes | |
| serviceable | boolean | yes | If false, block checkout |
| mango_eligible | boolean | yes | Perishable mango dispatch |
| delivery_days_min | integer | yes | |
| delivery_days_max | integer | yes | |
| cod_allowed | boolean | yes | Area-level COD |

---

## MangoSeason

Season campaign for a variety (Alphonso, Kesar, Langra, Dasheri, etc.).

| Attribute | Type | Required | Notes |
| --- | --- | --- | --- |
| id | uuid | yes | |
| variety_name | text | yes | |
| product_id | uuid | no | Linked Product if live |
| harvest_start | date | yes | |
| harvest_end | date | yes | |
| preorder_open | date | no | |
| preorder_close | date | no | |
| waitlist_enabled | boolean | yes | Off-season capture |
| status | enum | yes | `upcoming` / `live` / `closed` |

---

## WaitlistEntry

Off-season or sold-out mango notify list.

| Attribute | Type | Required | Notes |
| --- | --- | --- | --- |
| id | uuid | yes | |
| full_name | text | no | |
| email | email | yes | One of email or phone required |
| phone | 10-digit | no | |
| product_id | uuid | yes | |
| variety_name | text | yes | |
| created_at | datetime | yes | |

---

## Order

Placed order. Address and amounts are snapshots.

| Attribute | Type | Required | Notes |
| --- | --- | --- | --- |
| id | uuid | yes | |
| order_number | text | yes | Human id, e.g. GS-10482 |
| customer_id | uuid | no | Null if guest checkout (MVP: login required) |
| status | enum | yes | `pending_payment` / `confirmed` / `packed` / `shipped` / `delivered` / `cancelled` |
| address | Address snapshot | yes | Frozen at place-order |
| pincode | 6-digit | yes | |
| delivery_date | date | yes | Perishable slot |
| payment_method | enum | yes | `upi` / `card` / `cod` |
| payment_status | enum | yes | `pending` / `paid` / `failed` / `cod` |
| subtotal | INR | yes | |
| shipping | INR | yes | 0 if free-ship threshold met |
| gst | INR | yes | Display breakup |
| discount | INR | no | Default 0 |
| grand_total | INR | yes | |
| customer_notes | text (≤200) | no | |
| created_at | datetime | yes | |

---

## OrderLine

| Attribute | Type | Required | Notes |
| --- | --- | --- | --- |
| id | uuid | yes | |
| order_id | uuid | yes | |
| product_name | text | yes | Snapshot |
| variant_label | text | yes | Snapshot |
| sku | text | yes | |
| qty | integer | yes | |
| unit_price | INR | yes | |
| line_total | INR | yes | |

---

## Payment

| Attribute | Type | Required | Notes |
| --- | --- | --- | --- |
| id | uuid | yes | |
| order_id | uuid | yes | |
| method | enum | yes | `upi` / `card` / `cod` |
| status | enum | yes | `pending` / `paid` / `failed` / `cod_pending` |
| amount | INR | yes | Equals Order.grand_total |
| gateway_ref | text | no | Razorpay / similar |

---

## AdminUser

| Attribute | Type | Required | Notes |
| --- | --- | --- | --- |
| id | uuid | yes | |
| name | text | yes | |
| email | email | yes | Login |
| role | enum | yes | `admin` / `packer` |
| is_active | boolean | yes | |
| password | password | yes | Never shown |

---

## CMSBanner

Home and mango-hub campaign block.

| Attribute | Type | Required | Notes |
| --- | --- | --- | --- |
| id | uuid | yes | |
| title | text | yes | |
| subtitle | text | no | |
| season_state | enum | yes | `live` / `coming_soon` / `closed` |
| cta_label | text | yes | |
| cta_url | url | yes | |
| image | image | yes | |
| start_date | date | yes | |
| end_date | date | yes | |
| is_published | boolean | yes | |

---

## DeviceToken

Android push registration. Website does not use this.

| Attribute | Type | Required | Notes |
| --- | --- | --- | --- |
| id | uuid | yes | |
| customer_id | uuid | yes | FK Customer |
| fcm_token | text | yes | From Firebase |
| platform | enum | yes | `android` |
| notifications_enabled | boolean | yes | OS permission |
| updated_at | datetime | yes | |

---

## PushMessage

In-app notification inbox (AN-05). Optional persist; FCM still required.

| Attribute | Type | Required | Notes |
| --- | --- | --- | --- |
| id | uuid | yes | |
| customer_id | uuid | yes | |
| title | text | yes | |
| body | text | yes | |
| type | enum | yes | `order` / `mango_season` |
| order_number | text | no | If type=order |
| product_slug | text | no | If mango |
| is_read | boolean | yes | |
| created_at | datetime | yes | |

---

## SearchQuery

Not stored. Request fields for shop search. Spec: [SEARCH.md](SEARCH.md).

| Attribute | Type | Required | Notes |
| --- | --- | --- | --- |
| q | text | yes | 1–80 chars; maps to C-03 `search_query` |
| category | enum | no | Same as Product.category |
| origin | text | no | Filter |
| pack_type | enum | no | Filter |
| season_status | enum | no | Filter |
| sort | enum | no | featured / price_asc / price_desc / name |
| page | integer | no | Default 1 |

---

## Shared enums (quick reference)

| Name | Values |
| --- | --- |
| category | exotic, dry_fruit, mango |
| season_status | in_season, limited, coming_soon, off_season |
| pack_type | weight, box, tin |
| address_type | home, office, other |
| payment method | upi, card, cod |
| order status | pending_payment, confirmed, packed, shipped, delivered, cancelled |
| mango season status | upcoming, live, closed |
| push type | order, mango_season |
| device platform | android |

---

## Implementation appendix — Stage 1 API infrastructure

Added locally for the documented refresh-token revocation and FCM delivery requirements. These are internal persistence objects, not mobile request fields. The original domain tables above are unchanged.

### AuthSession

| Attribute | Type | Required | Notes |
| --- | --- | --- | --- |
| id | uuid | yes | System-generated primary key |
| customer_id | uuid | no | FK Customer, delete cascade |
| admin_id | uuid | no | FK AdminUser, delete cascade |
| refresh_digest | text (64) | no | Unique SHA-256 digest; no plaintext refresh token stored |
| expires_at | datetime with timezone | yes | Session expiry |

Exactly one customer_id/admin_id is present. Customer sessions expire after 30 days; admin sessions after the 15-minute access lifetime. Logout deletes the current session. Customer access tokens are also bounded to 15 minutes.

### PushDelivery

| Attribute | Type | Required | Notes |
| --- | --- | --- | --- |
| id | uuid | yes | System-generated primary key |
| message_id | uuid | yes | FK PushMessage, delete cascade |
| device_id | uuid | yes | FK DeviceToken, delete cascade |
| attempts | integer | yes | Default 0, nonnegative |
| sent_at | datetime with timezone | no | Null until delivered |
| last_error | text (80) | no | Exception class only; no credentials or message payload |

Unique message_id/device_id pair. Queue writes share the triggering business transaction. Dispatch uses row locks, current device ownership/permission, and at most five attempts. Pending jobs require the explicitly run Firebase worker.


## User-requested extension — WishlistItem (7 September 2026)

Added after the initial dictionary at the user's explicit request for account wishlists. Existing domain enums and constraints remain unchanged.

| Field | Type | Required | Constraint |
| --- | --- | --- | --- |
| customer_id | UUID | yes | FK Customer; cascades on deletion; composite primary key with product_id |
| product_id | UUID | yes | FK Product; cascades on deletion |
| created_at | timestamptz | yes | Server default now() |

Every wishlist endpoint enforces customer ownership. Inactive products are hidden. Reorder resolves OrderLine SKU snapshots against current variants, adds to the cart at current prices and never places an order. The requested carousel uses multiple existing CMSBanner records without adding fields.

## Checkout infrastructure extensions (8 September 2026)

These support the documented checkout/cancellation flow without changing the domain objects or enums above.

| Table | Purpose | Constraints |
| --- | --- | --- |
| CheckoutSession | Order/customer link, UUID request ID and request-body hash, backend, unique provider IDs, expiry/release timestamps | Order PK/FK; customer FK; unique customer/request pair; backend cod/demo/razorpay |
| StockReservation | Variant quantities reserved by an order | Composite order/variant PK and FKs; quantity 1–20; variant deletion restricted |
| RefundRequest | Durable full-order refund queue | Order PK/FK; positive amount; pending/submitted/processed status; unique optional gateway reference |

All three use UUID order foreign keys with cascade deletion. Snapshots remain on Order and OrderLine. The refund table stores operational metadata, not card/UPI credentials. Total implemented tables: 22.
