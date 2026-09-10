> Historical checkpoint. See `STOREFRONT_REVIEW.md` for current changes and verification.

# Stage 1 API review

The database foundation is approved and the API stage is implemented. Document requirements take precedence over the original prompts, following your latest instruction. Source documents under the supplied OneDrive folder remain unchanged.

## Implemented

All paths below use `/api/v1`. Response money is decimal INR strings; timestamps are UTC ISO-8601. Errors return `{code, message, fields}`. Product pages use `{items, total, page, page_size}` with a default size of 20 and maximum 50.

| Capability | Routes |
| --- | --- |
| Customer sessions | POST `/auth/signup`, `/auth/login`, `/auth/refresh`, `/auth/logout` |
| Admin sessions | POST `/admin/auth/login`; active admin/packer accounts only |
| Catalog/search | GET `/products`, `/products/{slug}`, `/products/{slug}/related`, `/search` |
| Product management | GET/POST `/admin/products`; GET/PATCH `/admin/products/{id}` |
| Guest/customer carts | GET `/cart`; PUT `/cart/pincode`; POST `/cart/lines`; PATCH/DELETE `/cart/lines/{id}` |
| Customer profile | GET/PATCH `/me` |
| Saved addresses | GET/POST `/me/addresses`; PATCH/DELETE `/me/addresses/{id}` |
| Pincode coverage | GET `/pincodes/{pincode}`; GET/POST `/admin/pincodes`; PATCH/DELETE `/admin/pincodes/{pincode}` |
| Inventory | GET/PATCH `/admin/inventory` |
| Mango campaigns | GET `/mango-season`; POST `/mango-season/waitlist`; GET/POST `/admin/mango-seasons`; PATCH/DELETE `/admin/mango-seasons/{id}` |
| Banners | GET `/banners/current`; GET/PUT `/admin/cms/banner` |
| Order reading | GET `/orders`, `/orders/{order_number}`, `/admin/orders`, `/admin/orders/{id}` |
| Fulfillment/dashboard | POST `/admin/orders/{id}/status`; GET `/admin/dashboard` |
| Android registration | PUT/DELETE `/me/device-tokens` |
| Optional inbox | GET `/me/notifications`; PATCH `/me/notifications/{id}` with `is_read` |

Checkout, gateway webhooks, customer cancellation, static content, and contact submission are not implemented yet. Their documents remain authoritative for the upcoming shopping/content integration. Existing seeded orders can be read and advanced through documented fulfillment transitions; this stage does not create paid orders, reserve/release inventory for checkout, or process refunds.

## Important behavior

- Product removal follows the documented visibility flag: PATCH `is_active=false`. There is no hard-delete product endpoint. Pack removal uses the nested variant list and is blocked if a cart references the pack.
- Product PATCH with `variants` supplies the complete desired variant list. Existing rows carry `id`; new rows omit it; omitted rows are removed. Existing variants may supply only changed fields. The final list must contain exactly one default. PATCH without `variants` preserves packs.
- Catalog creation/editing is admin-only, matching A-03's MVP rule. Packers can access inventory, dashboard, orders, and fulfillment. Customer/admin bearer tokens cannot be interchanged.
- Access tokens last 15 minutes; customer refresh sessions last 30 days. Refresh token digests are stored in PostgreSQL. Logout deletes that login session, revoking its refresh and access tokens. Other device sessions remain active. Inactive staff are rejected even if they hold a signed token.
- Guest carts require client-generated UUID `X-Session-Id`. Login/signup can include it to merge carts. Merge caps quantity at stock and 20, removes unavailable merged lines, refreshes merged prices, and returns `cart_merge.adjustments` so the app can explain changes. This response extension resolves conflicts left unspecified by the documents.
- Per-owner transaction locks serialize cart creation/edits. Prices come from Variant; clients cannot supply unit prices. Stock and season checks run on mutation. Existing cart prices remain snapshots until changed/merged; checkout must revalidate them in its stage.
- Unknown pincodes return 200 with serviceability false. Saved addresses require known coverage. The cart exposes checkout blockers and COD eligibility. Mango/exotic products currently use perishable coverage checks, following REQUIREMENTS FR-12 conservatively without inventing a perishable field.
- Shop search matches active product name, origin, and linked mango variety, ranking exact/name matches before origin matches. It excludes SKU; admin search supports name/SKU. No manual featured-order field exists, so ties use name and UUID.
- Passwords/hashes are excluded from output. Writable fields are explicitly allowed. Authentication and waitlist requests are rate-limited. CORS uses configured origins. The local limiter uses process memory; shared storage is needed before multiple workers are deployed.
- Status changes and newly-live campaigns enqueue persisted inbox messages and device deliveries. The worker checks current ownership/permission. Failures retain the exception class and retry on the next worker invocation, up to five attempts. Delivery is at-least-once: interrupted acknowledgement can produce duplicates; `notification_id` supports client deduplication.
- The real Firebase Admin adapter is implemented, with sending mocked in tests. No real notification was sent. The pinned SDK accepts the documented registration token but emits a deprecation warning; installation IDs are different identifiers and would require updating the mobile contract before migration.

## Compact implementation

`api.py` shares JSON conversion, field validation, errors, pagination, transactions, and CORS. `require()` shares role checks, and a small factory handles repeated pincode/season CRUD. Product/cart rules remain explicit.

`AuthSession` and `PushDelivery` support required refresh revocation and durable FCM work. The local `docs/00-object-dictionary.md` appendix documents these infrastructure tables; the 16 original domain objects and enums are retained. Run `init-db` on the Prompt 1 database to add them. `schema.sql` is a complete initial schema, not an incremental migration.

## Try the API (PowerShell)

Start the server and create an admin using the README commands. Create catalog data through authenticated `/admin/products`; `backend/tests/test_api.py` contains a complete valid product payload. Then:

```powershell
$api = 'http://127.0.0.1:5000/api/v1'
Invoke-RestMethod "$api/products"
$session = @{ 'X-Session-Id' = [guid]::NewGuid().ToString() }
Invoke-RestMethod "$api/cart" -Headers $session
$pack = (Invoke-RestMethod "$api/products").items[0].default_variant.id
$line = @{ variant_id = $pack; qty = 2 } | ConvertTo-Json
Invoke-RestMethod "$api/cart/lines" -Method Post -Headers $session -ContentType 'application/json' -Body $line
```

No commercial catalog, live customer data, or payment credentials were seeded into an application database.

## Validation

23 Python tests pass, including PostgreSQL 18.4 integration, concurrent cart updates, account isolation, roles, refresh revocation, address defaults, stock validation, merge adjustments, JSON errors, CORS, rate limits, outbox retries, and Firebase payload construction. 54 standalone PostgreSQL schema checks also pass. Dependency validation reports no broken requirements.

The PGlite socket wrapper showed protocol limitations, so Flask/psycopg integration tests use actual PostgreSQL, bound only to localhost in a temporary workspace cluster. The server is stopped after verification. PGlite remains the standalone SQL harness.

**API checkpoint approved; the current review is the mobile foundation described in MOBILE_REVIEW.md. Deployment requires separate explicit approval.**
