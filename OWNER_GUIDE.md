# Grove & Stone — running your store

The shop and owner workspace are different entrances to the same business. Shoppers cannot enter owner tools using their customer accounts.

## Your links

- Shop: https://grove-and-stone-web.onrender.com/
- Owner workspace: https://grove-and-stone.onrender.com/admin

The owner workspace is served by Flask on the API domain. `/admin` on the separate storefront domain is not the owner application.

## First-time owner access

An owner invitation lasts 24 hours and works once. Open the private activation link and choose a unique password of at least 12 characters. Do not share the link or password. After activation, sign in using your email and password at the owner link above.

An authorized maintainer can issue that invitation with the production environment loaded privately:

```powershell
python -m flask --app backend invite-owner --email YOUR_OWNER_EMAIL --name "Store owner" --url https://grove-and-stone.onrender.com
```

The command prints a private activation link. Keep it outside Git and ordinary shared documentation. Existing staff accounts are managed under Team. Admin sessions last 15 minutes; reloading or closing the browser tab signs out. No staff password is stored in browser storage.

## What each section does

| Section | How to use it |
| --- | --- |
| Overview | Check orders placed today in Indian time, orders ready to pack, low stock and unread alerts. |
| Orders | Search order numbers, filter dates/status, inspect items/address/amounts, and print a packing slip. Export filtered order summaries as CSV. |
| Inventory | Set the number of packs available for sale. Reserved checkout stock is already excluded. |
| Order alerts | Review new confirmed orders and cancellations. Mark inbox entries read and see email acceptance/failure status. |
| Products | Add/edit products, descriptions, image references, packs, prices, GST rate, stock, COD eligibility and shop visibility. Choose exactly one default pack. |
| Delivery areas | Add confirmed pincodes, delivery days, fresh-fruit eligibility and COD rules. CSV import updates listed areas without deleting others. |
| Postal directory | Search nationwide reference pincodes/localities, then configure confirmed delivery areas separately. |
| Home offers | Create or edit dated hero offers and publish/unpublish them. |
| Mango seasons | Set variety harvest dates, waitlist and season status. |
| Refunds | Inspect cancelled paid orders awaiting refunds. Processing the queue sends eligible requests to the configured gateway. |
| Business setup | Save business details, alert email and review confirmations; open or pause ordering. Support phone is optional. |
| Team | Create staff accounts, choose admin/packer permissions, disable access, or reset a staff password. |
| Activity log | See successful staff changes with time and account ID. Passwords and request bodies are not logged. |

## From a customer order to delivery

1. The customer signs in, adds available packs, checks their pincode and reviews the delivery date and total.
2. A COD order becomes confirmed immediately. Online orders remain pending until a verified captured payment is received; live online payments are currently deferred.
3. A confirmed order creates a durable owner alert in the same database transaction. Open **Order alerts** or **Orders** to review it.
4. Print a packing slip, pack the exact items, and mark the order **packed**.
5. Add the courier/delivery team's name and tracking reference. An optional HTTPS tracking link is shown to the customer.
6. Mark **shipped** when physically dispatched and **delivered** after delivery is confirmed.
7. For COD, use **Record cash collected** after delivery and confirm the full amount received. Marking delivered alone does not mark cash as received.

These actions update the customer's order screen. The customer screen refreshes active orders every 10 seconds while open. This is status/tracking-link support, not a live rider GPS map or courier booking integration.

Cancel only confirmed orders before packing. Cancellation releases reserved stock. Captured online payments are queued for a refund. Packing slips are not GST tax invoices.

## Pincodes and actual delivery

The bundled GeoNames India snapshot contains 19,238 unique pincodes and 155,570 locality records, downloaded on 12 September 2026. It is attributed under CC BY 4.0. See `backend/data/README.md` and `postal-source.json` for provenance and checksum.

This is a nationwide reference snapshot, not a guarantee of completeness or a courier contract. Historical district/state names may occur. Several localities can share one pincode. New postal data can be imported without enabling delivery.

The earlier Hyderabad, Mumbai and Bengaluru rows were review data. Public delivery checks remain disabled until an owner confirms actual coverage. Do not enable all postal entries merely because they exist. Obtain serviceability, fresh-fruit suitability, COD support and delivery times from the fulfilment team first.

For bulk coverage, download the header-only template in **Delivery areas**, populate it using verified operational data, and import up to 3,000 rows per file. Booleans must be `true` or `false`. An invalid row rejects the entire file; it does not partially update coverage.

## Owner email alerts

The requested recipient is `saispandanatumu@gmail.com`. Business name: Grove and Stone. A support phone has not been supplied and is optional. Provider activation is still required before real emails can be sent.

Use an HTTPS email service such as Resend. Render Free blocks normal SMTP ports, so a Gmail app password is not a working deployment solution on this plan.

1. Set up Resend and verify a sending domain you control. Its `resend.dev` sender is for testing only.
2. In Render backend environment settings, add `RESEND_API_KEY` and `CONTACT_FROM` using that verified sender. Keep them out of Git and never paste the API key into chat.
3. In **Business setup**, save the owner email and enable owner emails.
4. Run a controlled COD order and check both **Order alerts** and the recipient inbox/spam folder.

The mail loop checks queued jobs about every 30 seconds while the backend process is active. Failed sends retry with increasing delay. Sent means provider acceptance, not guaranteed inbox placement. The provider idempotency key helps prevent duplicate retries; uncertain old deliveries need provider review before manual retry.

Free Render can sleep or restart. Durable database jobs survive restarts, but unattended timing needs an always-on service or worker. An optional worker command is:

```sh
python -m flask --app backend operations-worker
```

Alternatively schedule `python -m flask --app backend dispatch-owner-alerts` on an appropriate trusted scheduler. No paid worker was created automatically.

## Live payments — intentionally deferred

UPI/card code uses Razorpay hosted checkout, server verification, signed webhooks, stock reservations and a refund queue. It is not activated for live transactions. Keep `PAYMENT_BACKEND=disabled` until the merchant account is ready.

When ready, configure `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`, `PUBLIC_API_URL`, and `PAYMENT_BACKEND=razorpay` privately. Test mode and live mode use different credentials.

- Callback: `https://grove-and-stone.onrender.com/api/v1/payments/callback`
- Webhook: `https://grove-and-stone.onrender.com/api/v1/payments/gateway-webhook`
- Events: `payment.captured`, `order.paid`, `payment.failed`, `refund.processed`

Enable appropriate payment capture settings in the merchant dashboard, test success/failure/retry/refund flows, and verify a controlled live payment before enabling it for customers. Do not fulfil a pending or merely authorized online payment.

## Before opening the store

Complete the real dispatch address, customer support email, actual stock and selling prices, approved courier coverage, delivery charges and reviewed policies. Set the review confirmations in **Business setup** only after verifying them, then enable **Accept customer orders**. Keep the shop paused if fulfilment is not ready.

Outstanding business-dependent work includes supplier-approved catalog content and harvest dates, courier fulfilment/serviceability integration if desired, email provider activation, and real-order acceptance testing. Live payments are deferred at the owner's request. Customer email/phone verification, self-service forgotten-password recovery, support-ticket management, legally reviewed business policies/invoices, monitoring/backups and a signed Android release are further release gaps; the application must not be described as fully production-ready until these are addressed and tested.

## Validation for this update

Backend integration tests cover admin/customer separation, staff revocation, one-use owner invitations, order lifecycle, stock, payment mocks/signatures, delivery import rollback, postal lookup, durable email jobs and retry handling. Browser review includes owner login, session expiry, product saving, town search and setup screens. Real email delivery, real courier fulfilment and live payment capture still require the owner's provider accounts and operational details.

## Sources

- Instamart flow reference: https://mcp.swiggy.com/builders/docs/build/recipes/order-groceries/
- Postal data: https://download.geonames.org/export/zip/readme.txt
- Hosting limits: https://render.com/docs/free
- Verified email senders: https://resend.com/docs/knowledge-base/how-do-I-create-an-email-address-or-sender-in-resend
- Razorpay payment capture: https://razorpay.com/docs/payments/payments/capture-settings/
