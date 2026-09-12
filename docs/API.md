# API endpoints

Base: `/api/v1`. Objects: [00-object-dictionary.md](00-object-dictionary.md). Errors: [BACKEND.md](BACKEND.md).

Auth column: **Pub** = no token; **Cust** = customer Bearer; **Sess** = customer Bearer **or** `X-Session-Id`; **Adm** = admin Bearer.

---

## Auth (customer)

### `POST /auth/signup`

Creates Customer; returns tokens. Body fields: Customer `full_name`, `email`, `phone`, `password`.  
201: `{ customer: { id, full_name, email, phone }, access_token, refresh_token }`  
409 if email or phone taken.

### `POST /auth/login`

Body: `email`, `password`.  
200: same as signup. 401 generic “incorrect”.

### `POST /auth/logout`

Cust. Invalidates refresh token. 204.

### `POST /auth/refresh`

Body: `refresh_token`. 200: new `access_token`.

---

## Customer profile and addresses

### `GET /me` · `PATCH /me`

Cust. GET returns Customer (no password). PATCH: `full_name`, `phone` (email locked). 409 phone taken.

### `GET /me/addresses`

Cust. `{ items: Address[] }`.

### `POST /me/addresses`

Cust. Body: Address fields except `id`, `customer_id`. If `is_default=true`, unset others.

### `PATCH /me/addresses/{id}` · `DELETE /me/addresses/{id}`

Cust. 404 if not owner.

---

## Catalog (public)

### `GET /banners/current`

Pub. Published CMSBanner if `now` in start/end. 200 banner object or 204 empty (home hides hero).

### `GET /products`

Pub. Query: `category` (`exotic`\|`dry_fruit`\|`mango`), `origin`, `pack_type`, `season_status`, `sort` (`featured`\|`price_asc`\|`price_desc`\|`name`), `page`.  
Only `is_active=true`. Each item: Product + `default_variant` (Variant).

### `GET /products/{slug}`

Pub. Product + `variants[]`. 404 if missing or inactive.

### `GET /search`

Pub. Full spec: [SEARCH.md](SEARCH.md). Query: `q` (1–80), plus same filters as product list. Search `name`, `origin`, mango `variety_name`.

### `GET /products/{slug}/related`

Pub. Same category, exclude self, max 8.

---

## Mango season

### `GET /mango-season`

Pub. `{ banner: CMSBanner | null, varieties: MangoSeason[] }` with nested Product summary if `product_id` set.

### `POST /mango-season/waitlist`

Pub or Cust. Body: WaitlistEntry `full_name`, `email`, `phone`, `product_id` (or `slug`). Require email or phone.  
201 created; 409 already listed (client shows success). 400 if waitlist disabled and status live (client should shop PDP).

---

## Pincode

### `GET /pincodes/{pincode}`

Pub. `pincode` exactly 6 digits. 200 PincodeService. If unknown row, 200 with `serviceable: false`, `mango_eligible: false` (do not 404).

---

## Cart

Cart is one per Customer or session.

### `GET /cart`

Sess. Cart + `lines[]` (CartLine + Product summary + Variant). Totals: `subtotal`.

### `PUT /cart/pincode`

Sess. Body: `{ pincode }`. Stores Cart.pincode; returns PincodeService + cart (checkout blockers: `can_checkout`, `block_reason`).

### `POST /cart/lines`

Sess. Body: `{ variant_id, qty }`. Qty 1–20, ≤ `stock_qty`. 422 if Product not purchasable (`off_season` / `coming_soon` / inactive). Merges qty if same variant exists.

### `PATCH /cart/lines/{id}`

Sess. Body: `{ qty }`. Same qty rules.

### `DELETE /cart/lines/{id}`

Sess. 204.

---

## Checkout and orders

### `POST /checkout`

Cust. Cart must be non-empty. Body:

| Field | Object | Required |
| --- | --- | --- |
| address_id | Address | yes if not sending address |
| address | Address fields | yes if no address_id |
| delivery_date | Order | yes |
| payment_method | Order | yes `upi` / `card` / `cod` |
| customer_notes | Order | no |

Server re-checks pincode, mango_eligible, COD flags, stock, delivery_date window.  
201: `{ order, payment: { method, status, gateway_order_id? } }`  
For UPI/card: `payment.status=pending`; client opens gateway with `gateway_order_id`.  
For COD: `order.status=confirmed`, `payment_status=cod`.

### `POST /payments/gateway-webhook`

Pub (gateway signature). Marks Payment paid/failed; Order confirmed or pending_payment.

### `GET /orders`

Cust. Paginated Order summaries (this customer only).

### `GET /orders/{order_number}`

Cust. Order + OrderLine[] + Payment. 404 if not owner.

### `POST /orders/{order_number}/cancel`

Cust. Only `status=confirmed`. Sets `cancelled`. 422 otherwise.

---

## Device tokens (Android)

### `PUT /me/device-tokens`

Cust. Body: `{ fcm_token, platform: "android", notifications_enabled }`. Upsert DeviceToken.

### `DELETE /me/device-tokens`

Cust. Body: `{ fcm_token }`. Logout / disable push.

---

## Content / contact

### `GET /pages/{key}`

Pub. `key`: `about` \| `shipping` \| `returns` \| `faq`. Body: `{ title, body }` or FAQ `{ items: [{ question, answer }] }`.

### `POST /contact`

Pub. Body: `full_name`, `email`, `phone?`, `order_number?`, `message`. 204. Rate-limit.

---

## Admin auth

### `POST /admin/auth/login`

Body: AdminUser `email`, `password`. 200: `{ admin: { id, name, email, role }, access_token }`. Inactive → 401 same message as bad password.

---

## Admin dashboard and catalog

Packer: dashboard, inventory, orders. Admin: all below.

### `GET /admin/dashboard`

Adm. `{ orders_today, pending_pack, mango_live, low_stock, recent_orders[], seasons[] }`.

### `GET /admin/products` · `POST /admin/products`

Adm (POST admin role only). List query: `search`, `category`, `season_status`, `is_active`, `page`.  
POST body: Product fields + `variants[]` (at least one).

### `GET /admin/products/{id}` · `PATCH /admin/products/{id}`

Adm. PATCH Product; nested variant create/update/delete as in [A-04](A-04-product-edit.md).

### `GET /admin/inventory` · `PATCH /admin/inventory`

Adm or packer. PATCH body: `{ items: [{ variant_id, stock_qty }] }`.

---

## Admin orders

### `GET /admin/orders`

Adm or packer. Query: `order_number`, `status`, `payment_method`, `date_from`, `date_to`, `page`.

### `GET /admin/orders/{id}`

Adm or packer. Full Order + lines + address snapshot + Payment.

### `POST /admin/orders/{id}/status`

Adm or packer. Body: `{ status }` allowed transitions: confirmed→packed→shipped→delivered; confirmed→cancelled. 422 illegal.

---

## Admin delivery and mango CMS

Admin role only (not packer).

### `GET /admin/pincodes` · `POST /admin/pincodes`

### `PATCH /admin/pincodes/{pincode}` · `DELETE /admin/pincodes/{pincode}`

Body: PincodeService fields. `mango_eligible` cannot be true if `serviceable` is false.

### `GET /admin/cms/banner` · `PUT /admin/cms/banner`

CMSBanner.

### `GET /admin/mango-seasons` · `POST /admin/mango-seasons`

### `PATCH /admin/mango-seasons/{id}` · `DELETE /admin/mango-seasons/{id}`

MangoSeason. Live status requires `product_id`.

---

## Screen → API map (shop)

| Screen | Primary APIs |
| --- | --- |
| C-01 | `GET /banners/current`, `GET /products`, `GET /pincodes/{pincode}`, `GET /mango-season` |
| C-02 | `GET /products` |
| C-03 | `GET /search` |
| C-04 | `GET /products/{slug}`, `POST /cart/lines`, `GET /pincodes/{pincode}` |
| C-05 | `GET /mango-season` |
| C-06 | `POST /mango-season/waitlist` |
| C-07 | `GET /cart`, `PATCH/DELETE /cart/lines`, `PUT /cart/pincode` |
| C-08 | `GET /me/addresses`, `POST /checkout` |
| C-09 / C-10 / C-14 | `GET /orders/{order_number}`, `GET /orders`, `POST .../cancel` |
| C-11 / C-12 | `/auth/login`, `/auth/signup` |
| C-13 | `/me`, `/me/addresses` |
| C-16 / C-21 | `GET /pincodes/{pincode}` |
| C-18 | `POST /contact` |
| AN-04 | `PUT /me/device-tokens` |

## User-requested storefront extensions (7 September 2026)

- `GET /banners`: `{items: CMSBanner[]}` for all current published slides, newest start date first. Existing `/banners/current` remains compatible.
- `GET /media/{filename}`: bundled illustrative catalog and hero assets.
- `GET /me/wishlist`: customer-owned `{items: Product[]}` with default variants; inactive products hidden.
- `PUT /me/wishlist/{product_id}` / `DELETE /me/wishlist/{product_id}`: idempotently save/remove for the authenticated customer.
- `POST /orders/{order_number}/reorder` with `{}`: customer-only, returns updated cart and 201. Resolves original SKUs, uses current prices and checks stock and quantity limits atomically. Missing/foreign orders return 404; unavailable packs return 422 without changing the cart.
- `DELETE /cart/lines`: atomically clear the current guest/customer cart; 204.
- Cart JSON additionally includes `included_gst` and `total_before_shipping` as decimal strings. GST is extracted from inclusive line amounts, rounded per line to two decimal places; it is not added to subtotal. Shipping is now quoted by POST /checkout/quote.

## Implemented checkout extensions (8 September 2026)

- `POST /checkout/quote` (customer), body `{pincode}`: refreshed cart, `shipping`, `grand_total`, `delivery_dates`, coverage, Indian `states`, payment backend and `quote_id`. Decimal amounts serialize as strings.
- `POST /checkout` retains the documented fields and adds required UUID `request_id` and `quote_id`. Supply exactly one of `address_id` or `address`. It returns `{order, payment}`; identical retries return the original order.
- `GET /checkout/attempts/{request_id}` returns `{order: null}` or the calling customer's saved order for uncertain-response recovery.
- `POST /orders/{number}/payment-session` returns the hosted Razorpay payment URL or local `{backend: "demo"}`.
- `POST /orders/{number}/demo-payment`, body `{outcome: "success" | "failure"}`, is restricted to the authenticated owner and explicit loopback demo mode.
- `GET /pay/{signed_token}` hosts provider checkout; `POST /payments/callback` validates its signed provider form. `POST /payments/gateway-webhook` verifies the raw request HMAC.
- Order detail adds `payment_backend`, `payment_expires_at` and `refund`. Refund statuses pending/submitted/processed are separate from the unchanged domain payment enums.
- `GET /shop-info` exposes configured public support/pricing/policy values. `POST /contact` validates and rate-limits the documented contact form, sending through configured Resend HTTPS or explicitly validating only in local demo mode.
- `GET /health` checks PostgreSQL availability.

## Live stock check

`POST /stock/check` is public. Body: `{product_ids: [UUID, ...]}` with 1–100 IDs, deduplicated by the server. Returns `{items: [{id, is_active, season_status, variants: [{id, stock_qty}]}], checked_at, poll_after_seconds: 5}`. Unknown/inactive products are explicitly unavailable with no variant details. A single SQL statement reads product and pack availability together; responses are `Cache-Control: no-store`. No carts, prices, reservations or inventory are changed by this endpoint.

The Expo client batches larger subscriptions, checks visible screens and cart products every five seconds after successful responses, stops when hidden/backgrounded, retries failures with bounded backoff, and cancels obsolete requests. Inventory is still locked and checked when adding quantities and placing orders.


## Owner operations and postal lookup (13 September 2026)

The same-origin owner website is served at `/admin`. Its API uses existing short-lived staff bearer sessions; admin and packer scopes are enforced on the server.

- Public: `GET /delivery/places?q=town` returns at most 20 postal reference matches. `GET /shop-info` includes `ordering_enabled` and business/support details. Coverage checks suppress unapproved sample coverage in production; checkout returns `503 SHOP_NOT_OPEN` until enabled by the owner.
- Activation: `POST /admin/auth/activate` accepts a one-use, expiring invitation token and a password of at least 12 characters. Only a privileged CLI/database operator can issue invitations. `GET /admin/auth/me` and `POST /admin/auth/logout` inspect/revoke the session.
- Orders: `PUT /admin/orders/:id/shipment` records courier details; `POST /admin/orders/:id/collect-cod` records the exact amount collected for a delivered COD order.
- Alerts: `GET /admin/alerts`, `POST /admin/alerts/:id/read`, and admin-only `POST /admin/alerts/:id/retry` expose durable delivery state. Jobs enqueue in the order transaction; HTTPS email sending requires a configured provider.
- Setup: admin-only `GET/PATCH /admin/settings` contains non-secret details and readiness confirmations. Opening orders validates business details, approved coverage, catalog and policies.
- Staff: admin-only `GET/POST /admin/staff`, `PATCH /admin/staff/:id`; changes to password, role or status revoke existing sessions. Self-demotion/deactivation is blocked.
- Delivery: paginated `GET /admin/pincodes?search=...`; `POST /admin/pincodes/import` accepts `{csv: string}` (maximum 3,000 rows, atomic validation). `GET /admin/postal-directory?search=...` searches reference data without activating delivery.
- Content: `GET/POST /admin/banners`, `PATCH /admin/banners/:id` manage multiple home offers alongside the existing CMS routes.
- Operations: `GET /admin/refunds`, `POST /admin/refunds/process`, `GET /admin/audit` are admin-only.

See [OWNER_GUIDE.md](../OWNER_GUIDE.md) for daily operation, email setup, command examples and remaining launch requirements. Live payments remain deferred at the owner's request.
