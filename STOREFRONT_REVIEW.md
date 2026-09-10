# Grove & Stone — storefront review

> Historical checkpoint: checkout, shipping quotes, payment adapters, cancellation/refunds and support pages are now implemented. See CHECKOUT_REVIEW.md for current scope and DEPLOYMENT.md for the prepared, undeployed infrastructure.
Open **http://localhost:8081/**. Flask runs at **http://127.0.0.1:5000/api/v1**. Both servers are running locally in this workspace. Nothing has been deployed.

## What changed

- Foodwagon-inspired golden hero, orange buttons, category tiles, product cards, “How does it work?” section and dark footer. The store retains the Grove & Stone name and the three documented shop lines: exotic fruits, dry fruits and seasonal mangoes.
- Published hero slides with fruit artwork, a floating animation, manual controls and pause. Reduced-motion preferences stop automatic movement. Publication dates control visibility; unpublished/expired banners are hidden. A published offer or new-arrival banner uses this same flow. No real discounts are invented.
- Icon-based top titles for Home, Mangoes, Cart and Account; accessible bottom-tab labels remain.
- Server-connected category browsing, search, product details and pack selection.
- Email/password signup/login, with name and mobile number collected at signup as specified in C-11/C-12. Phone OTP and social login are outside this version.
- Profile editing, database-backed wishlist, order history and Reorder. Reorder uses current prices and checks stock atomically before modifying the cart.
- Persistent guest carts; signup/login merges items into the customer cart. Quantity changes, removal and confirmed clearing update the server. GST is included in prices and displayed separately, never added twice. Delivery is quoted at checkout.
- Pincode format and serviceability checks use Flask.

## Try it

1. Open California Almonds, select 500 g and add it to the cart. Change quantity and reload: the cart remains.
2. Use **Account → Create account** with test information, or use the local demo below. No verification email or SMS is sent.
3. Tap a product heart, then open **Account → Wishlist**.
4. In the demo account, open **Orders** or **Reorder** and use **Reorder GS-900001**. It adds sample almonds to the cart without placing an order or collecting payment.
5. Check **500001**, **400001** or **560001** for sample delivery coverage. Unknown pincodes return unavailable.

Local demo login: **review@example.com** / **GroveReview2026!**. It contains one synthetic past order. These are test-only credentials from the opt-in local seeder, which refuses non-loopback hosts and databases not ending in `_local`. It never runs on startup. A separate Browser Review account was created during UI testing.

Sample prices, stock, origins, GST rates, availability and harvest dates are review data, not production business settings. Replace them before release. Artwork is generated and illustrative; prompts and paths are in `ASSETS.md`.

## Validation

- 27 backend tests pass against a separate disposable native PostgreSQL database, including tax math, clearing carts, wishlist ownership/idempotence, banner visibility, and reorder stock/ownership/current-price checks.
- 57 standalone PostgreSQL schema checks pass, including wishlist uniqueness and references.
- TypeScript passes; Android Metro/Hermes export passes; Expo Doctor passes all 21 checks.
- Browser checks cover pack selection, quantity totals, persistence after reload, signup/cart merge, login/logout, wishlist, demo reorder and serviceable pincode.
- Desktop (1366px) and phone (390px) layouts were inspected. Android device installation/hardware behavior still needs device testing.
- Existing moderate upstream dependency advisories and the Firebase token deprecation warning remain; no forced dependency downgrades were applied.

## Remaining work

Checkout, payment gateways, shipping quotes, cancellation/refunds and production notifications remain subsequent integration work. Cart/reorder operations do not place orders. Customer/admin websites beyond this Expo browser preview are outside this update. Deployment requires your explicit approval.
