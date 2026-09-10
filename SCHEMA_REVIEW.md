# Schema review

> Historical checkpoint: checkout, shipping quotes, payment adapters, cancellation/refunds and support pages are now implemented. See CHECKOUT_REVIEW.md for current scope and DEPLOYMENT.md for the prepared, undeployed infrastructure.
The Prompt 1 foundation is approved. Prompt 2 preserves all 16 domain models and 13 enum types and adds two infrastructure tables, recorded in the local object-dictionary appendix.

The supplied documents take precedence over prompts, per your latest instruction. Original OneDrive documents are unchanged.

| Decision | Implementation |
| --- | --- |
| Waitlist contact | Email OR phone, following the dictionary note, C-06, API, and REQUIREMENTS FR-24 despite the dictionary's email Required=yes cell |
| Default variants | Exactly one per product, enforced by a unique partial index and deferred database triggers |
| Default addresses | At most one per customer; API clears the previous default transactionally |
| Cart ownership | Exactly one customer or session owner; unique per owner; UUID session header validated by API |
| Pincodes | Saved addresses reference coverage; cart can retain unknown checked pincodes; orders store independent snapshots |
| Passwords | The dictionary's physical password column stores a scrypt hash; write-only Python property; excluded from JSON |
| Money | Decimal INR in NUMERIC(12,2), sent as strings; generated line totals; GST-inclusive grand total formula |
| Pack validation | Positive prices/grams/counts, nonnegative stock, GST 0–28, conditional grams/counts from A-04 |
| Mango seasons | Ordered harvest/preorder dates, live product required, mango-only product links |
| Deletion/history | Order lines have no catalog FK; address snapshots cannot be updated; referenced historical data is protected |
| Navigation | Home, Mangoes, Cart, Account per Android documents |
| Product removal | API sets is_active=false; no hard-delete route, following the documented admin flow |
| AuthSession | Durable access-session identity, hashed customer refresh token and expiry; logout revokes the login session |
| PushDelivery | Transactional per-device FCM queue, attempts, completion time and failure class |

SearchQuery remains a request object, not a table. Order.payment_status uses cod; Payment.status uses cod_pending, exactly as documented.

Where the documents leave implementation choices open, emails compare case-insensitively, slugs use lowercase hyphen-separated characters, FCM tokens are unique, UUIDs have Python/server generators, and timestamps carry time zones. Payment can hold multiple attempts because the dictionary specifies no unique order_id constraint. Default booleans remain conservative; Variant.cod_allowed defaults true per A-04.

Stock reservation, final checkout validation, payment webhooks and cancellation inventory/refund behavior remain in the shopping integration stage. Image validity, factual farm claims and safe rich-text rendering also require later content/UI work.

Validation: 23 Python tests pass, including native PostgreSQL 18.4 integration and concurrent cart updates. The 54 standalone SQL checks pass. Real Firebase delivery is untested; only the SDK payload and mocked sends were exercised. See API_REVIEW.md for precise API scope.

The exported schema is for initial creation. init-db adds missing tables to the earlier foundation, but does not migrate existing columns. Future migrations must explicitly preserve the PostgreSQL functions/triggers in schema_invariants.py.

