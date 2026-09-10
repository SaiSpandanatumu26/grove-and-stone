# Grove & Stone — checkout review

Open **http://localhost:8081/** while the local servers are running. The earlier Foodwagon-inspired storefront remains in place.

## Try the new flow

1. Log in through Account. The sample account is `review@example.com`, password `GroveReview2026!`; or create your own local review account.
2. Add products to your basket and choose **Continue to checkout**.
3. Enter a delivery address with sample pincode `500001`, `400001` or `560001`. Select **Check delivery & total**. Save the address if desired.
4. Select a delivery date and UPI, card or cash on delivery. COD is shown only when eligible.
5. Online methods open the clearly labeled local simulator. Try failure, then success on the same order. No money is charged. COD confirms immediately.
6. Review the order lines, delivery address, included GST and total. Open Account → Orders to return to the tracking screen. Confirmed orders can be cancelled before packing; paid cancellations display a pending refund.
7. Use Reorder to add earlier items at today's price. Open the home footer for About, Shipping, Returns, Contact and searchable FAQ pages.

Local sample shipping is **₹49**, free from **₹999 subtotal**. The sample policy reports quality issues within **24 hours**. These are review assumptions because the documents require configuration but do not supply values. They require business approval before launch. The local Contact form validates without sending email.

## Implementation

Checkout recalculates prices/GST, verifies fresh-fruit eligibility, stock, COD rules and delivery dates in Indian time, reserves stock and creates immutable order snapshots in one PostgreSQL transaction. The browser retains only a random checkout request ID to recover an order after a lost response; retrying the same request cannot place it twice. A changed quote requires review before ordering.

The original domain enums are unchanged. Three infrastructure tables add checkout retry/gateway metadata, inventory reservations and refund requests (22 total tables). Cancellation releases recorded reservations once. Payment callbacks validate HMAC signatures and exact amount/currency/method. Late captures after expiry are queued for refund instead of fulfillment. Notification records are queued with state changes.

Unpaid reservations expire after 30 minutes. A request-driven sweep releases them when traffic resumes; `flask --app backend expire-payments` can also run manually. Local simulated refunds can be processed with `flask --app backend dispatch-refunds` under the same local database/demo environment. Real refund and notification delivery need a reliable worker; see `DEPLOYMENT.md`.

Real Razorpay transactions, support emails, FCM device delivery, EAS builds and deployment have not been run. The live adapters require credentials and provider testing. Administrative JSON APIs exist; a separate admin website is outside these five implementation prompts.

## Validation completed

- 34 Python tests passed across the existing suite and the expanded checkout suite, including concurrent purchases of the last available stock, retry identity, ownership, signature/amount checks, provider order recovery and expiry/cancellation inventory restoration.
- 57 standalone PostgreSQL schema checks passed against the newly exported 22-table schema.
- TypeScript checks and the Android Hermes bundle export passed. The export is not a signed APK; no EAS build was requested remotely.
- Render YAML passed Render's official JSON schema. Provider creation was not attempted.
- Browser review passed for saving/editing an address, free-shipping totals, demo payment failure then success, cancellation/refund status, order history, FAQ filtering and a contact submission that explicitly sent no email. The support form fits a 390-pixel page without horizontal overflow.

The pre-existing Firebase token deprecation and mobile transitive dependency advisories remain documented in the earlier review. Live gateway/email/FCM and physical-device testing remain unperformed.
