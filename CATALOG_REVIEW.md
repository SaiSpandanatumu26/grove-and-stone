# Grove & Stone — catalog and debugging review

Reviewed 9 September 2026. Open [the local shop](http://localhost:8081/) while its database, Flask, and Expo servers are running. Start with [BEGINNER_GUIDE.md](BEGINNER_GUIDE.md) for a plain-language walkthrough.

## Catalog changes

The supplied specifications cover exotic fruits, dry fruits, and seasonal mangoes; they do not limit the catalog to the original four products. The local sample now contains **15 products and 30 purchasable pack definitions**: eight exotic fruits, three dry fruits, and four mango varieties.

Added strawberries, blueberries, avocado, passion fruit, lychee, pears, whole cashews, pistachios, and Kesar, Langra, and Dasheri mangoes. Eight new generated product illustrations follow the existing warm background style. Mango varieties reuse the illustrative mango image; these are not variety-specific supplier photographs.

Mango packs are boxes of 6/12 pieces, as required by the documents. The seed corrects the original demo Alphonso weight packs while preserving their IDs, prices, and stock. Existing catalog records are preserved on subsequent seeding. Upcoming sample varieties have zero stock and a working Notify me form. Harvest windows, origins, prices, taxes, and stock are review values needing business verification before launch.

## Bugs fixed

- Upcoming mango cards previously led to unavailable purchasing without a usable registration flow. They now open the matching waitlist from both the catalog and season hub.
- Duplicate waitlist entries now return the same generic success message without disclosing another registration. Database conflict handling also prevents concurrent duplicates. Closed campaigns without an enabled waitlist reject registration.
- Reordering could leave the Cart tab on an old checkout/order screen. It now opens the basket, including when a checkout screen was already open.
- The old local Alphonso seed used weight packs. Re-seeding now corrects only those known demo packs to documented box packs.

## Verification

| Check | Result |
| --- | --- |
| Python tests against a separate PostgreSQL test database | **39 passed**. Includes catalog/image coverage, repeatable seeding, retained stock, box constraints, waitlist validation/privacy/concurrent duplicates, and existing account/cart/checkout/payment tests. |
| TypeScript | `npx.cmd tsc --noEmit` passed. |
| Android bundle export | Passed: 884 modules, approximately 2.1 MB JavaScript bundle. This is a local export, not a signed APK or installed-device test. |
| Earlier standalone schema suite | 57 checks passed in the previous schema review. Schema is unchanged; those checks were not rerun for these catalog/UI changes. |
| Homepage/catalog | All 15 cards and images loaded; category counts 8/3/4; hero slide selection, pause, and collection navigation exercised. |
| New-fruit search | Searching `blueberries` returned the correct new product, pack, price, image, and stock. |
| Waitlist | Empty-form validation, successful guest registration, and repeat registration exercised through both product and season-hub entry points. |
| Account/product | Login, strawberry wishlist action, 500 g pack selection, and add-to-cart exercised. |
| Cart/checkout | Quantity increase/decrease, included GST, saved-address quote, delivery days, and UPI/CARD/COD selection exercised. The strawberry example quoted ₹398 + ₹49 delivery = ₹447. |
| Stock while checkout stays open | Changed the selected sample pack from 40 to 0: the UI automatically showed Review cart and disabled payment. Restoring 40 re-enabled it without page reload. Test stock was restored. |
| Demo online payment | Failed payment, retry, successful payment, cancellation, and requested-refund status exercised. No real payment or refund occurred. |
| Reorder | Reproduced the stale-screen bug; after the fix, reorder opened the basket from order history and with an existing checkout stack. |
| Clear cart/session recovery | Keep-items confirmation checked. A later transient connection failure was followed by access-token refresh and successful clear-cart response, confirmed in the local server log. |
| Phone-size browser | Homepage, new-product search, and mango waitlist visually reviewed at 390 × 844. No browser errors were reported in this fresh session. This checks the web layout, not a physical Android installation. |

The review created a synthetic cancelled order and sample waitlist registration. No customer payment, courier booking, contact email, or harvest alert was sent. Local review data is separate from the disposable integration-test database.

## Practical limits

The tested local shopping flows work. This is not proof that every possible device, interaction, network condition, or external provider works. Previous FAQ/contact checks are in [CHECKOUT_REVIEW.md](CHECKOUT_REVIEW.md). Existing development style/Firebase-token warnings and dependency advisories remain documented in earlier reviews.

The waitlist stores interest; automatic email/SMS harvest alerts are not implemented. Shop authentication currently uses email/password; mobile OTP/social login is not implemented. Real payment/contact/push credentials, provider callbacks, refund/push workers, and a physical Android build still need configuration and end-to-end validation.

## Deployment status

The owner approved proceeding. Deployment files and instructions are prepared, but no remote resources or EAS build have been created. On the latest check, accessible Render/GitHub sessions still required sign-in; Expo's Google flow also requested an email address. Chrome authentication is not shared with the accessible in-app browser. The website remains local, and the backend Render recipe does not separately publish the web frontend.

See [DEPLOYMENT.md](DEPLOYMENT.md) for the remaining account/repository configuration and free-preview limitations. No additional general deployment approval is required.
