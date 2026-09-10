# Grove & Stone — product requirements

**Document type:** Product requirements (website + Android customer app)  
**Product:** Direct-to-consumer e-commerce for exotic fruits, dry fruits, and seasonal natural mangoes  
**Market:** India  
**Brand (placeholder):** Grove & Stone — rename before launch  
**Related specs:** [README.md](README.md) (screens); [ARCHITECTURE.md](ARCHITECTURE.md) (system); [00-object-dictionary.md](00-object-dictionary.md) (objects); [ANDROID.md](ANDROID.md) (app); [BACKEND.md](BACKEND.md) / [API.md](API.md) (API — not implemented in this repo)

---

## 1. Purpose

Build a **mobile-first website** and an **Android customer app** (same backend) where households can buy:

1. **Exotic fruits** — limited or imported seasonal fruit, with availability badges and handling notes  
2. **Dry fruits** — year-round packs and gift tins  
3. **Natural mangoes** — variety-led (Alphonso, Kesar, Langra, Dasheri, and similar), sold in boxes during mango season, with origin and ripeness-at-delivery copy  

The mango-season experience is not a generic category page. It has a harvest calendar, pre-order/waitlist when boxes are not on sale, and pincode rules for perishable dispatch.

---

## 2. Goals

| Goal | How we know |
| --- | --- |
| Shoppers can complete a paid or COD order for in-stock packs | Checkout → confirmation with order number |
| Off-season mango demand is captured | Waitlist entries on C-06 |
| Perishable orders only go to serviceable pincodes | PincodeService gates cart/checkout |
| Staff can turn mango SKUs and banners on/off for the season | A-04, A-05, A-09 |
| Claims stay honest | Farm/origin copy is factual; no fake ripeness guarantee |

---

## 3. Users

| User | Needs |
| --- | --- |
| Guest shopper | Browse, search, pincode check, cart; must log in before checkout (MVP) |
| Customer | Account, saved addresses, order history, tracking |
| Gift / household buyer | Dry-fruit packs and mango boxes with clear pack size and price |
| Mango-season buyer | Variety, harvest window, box size, ripeness note, delivery date |
| Admin | Catalog, stock, pincodes, mango CMS |
| Packer | Order list, mark packed/shipped/delivered, stock tweaks |

No marketplace and no third-party sellers.

---

## 4. Scope

### 4.1 In scope (MVP)

- Catalog of three lines; product detail with pack variants (weight / box / tin)  
- Search, cart, checkout (UPI, card, COD where allowed)  
- Pincode serviceability, including mango-eligible flag  
- Delivery date on perishable checkout  
- Customer signup/login, profile, addresses, orders  
- Mango season hub, waitlist/pre-order capture (email/phone; no paid deposit in MVP)  
- Admin: products, inventory, orders, fulfillment, pincodes, mango banner + variety dates (**website only**)  
- Static: About, Shipping, Returns, Contact, FAQ  
- GST shown on price (inclusive); invoice fields on order snapshot  
- Android app: splash, onboarding, bottom nav, FCM push, same shop/checkout as web ([ANDROID.md](ANDROID.md))  

### 4.2 Out of scope (later)

- Hindi UI  
- Guest checkout  
- Paid mango pre-order / deposits  
- Subscribe-and-save for dry fruits  
- Gift wrap / message cards as SKUs  
- Multi-seller marketplace  
- Loyalty points, wallets, EMI  
- iOS app  
- Admin/packer Android app  
- Live chat  

---

## 5. Catalog rules

| Line | Typical packs | Season | Notes |
| --- | --- | --- | --- |
| Exotic fruits | Weight (g/kg) | `in_season` / `limited` / `coming_soon` / `off_season` | Handling notes; pincode may be perishable |
| Dry fruits | Weight or tin | Year-round | Gift-eligible flag; COD usually allowed |
| Mangoes | Box (dozen / piece count) | Harvest window on Product + MangoSeason | Ripeness note; COD often **off** for high-value boxes; `mango_eligible` pincode required |

**Product** is the item (name, origin, story). **Variant** is what the customer buys (SKU, pack, price, stock, COD). Exactly one default variant per product.

Staff set `is_active` and `season_status`. Off-season mangoes stay visible with “Notify me” → waitlist, not add-to-cart.

---

## 6. Functional requirements

IDs are for traceability. Screen files own layout and fields.

### 6.1 Browse and merchandising

| ID | Requirement | Screens |
| --- | --- | --- |
| FR-01 | Home shows hero (CMS), three category tiles, mango-season strip, featured products | [C-01](C-01-home.md) |
| FR-02 | Category listing filters by origin, pack type, season status; sort by featured/price/name | [C-02](C-02-category.md) |
| FR-03 | Search matches name, origin, variety; empty state offers category shortcuts | [C-03](C-03-search.md) |
| FR-04 | PDP shows gallery, pack selector, price incl. GST, stock, origin, optional ripeness/handling/farm story | [C-04](C-04-product-detail.md) |
| FR-05 | Mango hub lists varieties, harvest dates, status; CTA shop or waitlist | [C-05](C-05-mango-season-hub.md) |

### 6.2 Cart, delivery, checkout

| ID | Requirement | Screens |
| --- | --- | --- |
| FR-10 | Cart lines store product, variant, qty, price snapshot; qty 1–20 and ≤ stock | [C-07](C-07-cart.md) |
| FR-11 | Pincode check uses PincodeService: `serviceable`, `mango_eligible`, SLA days, area COD | [C-01](C-01-home.md), [C-04](C-04-product-detail.md), [C-07](C-07-cart.md), [C-16](C-16-shipping.md), [C-21](C-21-pincode-not-serviceable.md) |
| FR-12 | If cart has mango (or perishable exotic) and pincode is not mango-eligible, block checkout | [C-07](C-07-cart.md), [C-08](C-08-checkout.md) |
| FR-13 | Checkout requires login, address, serviceable pincode, delivery date, payment method | [C-08](C-08-checkout.md) |
| FR-14 | COD is hidden if any line has `Variant.cod_allowed=false` or pincode `cod_allowed=false` | [C-08](C-08-checkout.md) |
| FR-15 | Delivery date ≥ today + `delivery_days_min`, ≤ 14 days ahead | [C-08](C-08-checkout.md) |
| FR-16 | Place order snapshots address and lines; UPI/card via gateway; COD creates confirmed order | [C-08](C-08-checkout.md), [C-09](C-09-order-confirmation.md) |

### 6.3 Account and mango waitlist

| ID | Requirement | Screens |
| --- | --- | --- |
| FR-20 | Signup: name, email, phone, password; unique email and phone | [C-12](C-12-signup.md) |
| FR-21 | Login with email + password | [C-11](C-11-login.md) |
| FR-22 | Customer edits name/phone; email locked in MVP; CRUD addresses | [C-13](C-13-account-profile.md) |
| FR-23 | Order history and tracking; cancel only while `confirmed` | [C-14](C-14-account-orders.md), [C-10](C-10-order-tracking.md) |
| FR-24 | Waitlist stores email or phone against a mango product; duplicate is success-equivalent | [C-06](C-06-mango-preorder.md) |

### 6.4 Content and support

| ID | Requirement | Screens |
| --- | --- | --- |
| FR-30 | About, shipping, returns, FAQ, contact form | [C-15](C-15-about.md)–[C-19](C-19-faq.md) |
| FR-31 | Unknown product/order/path → 404 without leaking existence of others’ orders | [C-20](C-20-404.md) |

### 6.5 Admin

| ID | Requirement | Screens |
| --- | --- | --- |
| FR-40 | Separate admin login; inactive staff cannot sign in | [A-01](A-01-login.md) |
| FR-41 | Dashboard: orders today, pending pack, live mango varieties, low stock | [A-02](A-02-dashboard.md) |
| FR-42 | CRUD products and variants (packs, GST, COD, images, season flags) | [A-03](A-03-product-list.md), [A-04](A-04-product-edit.md) |
| FR-43 | Quick stock edit | [A-05](A-05-inventory.md) |
| FR-44 | Order list/filter; fulfillment: packed → shipped → delivered; cancel from confirmed | [A-06](A-06-order-list.md), [A-07](A-07-order-fulfillment.md) |
| FR-45 | Pincode table: city, state, serviceable, mango-eligible, SLA, COD | [A-08](A-08-pincode-calendar.md) |
| FR-46 | Publish mango banner; per-variety harvest, pre-order window, waitlist, live/upcoming/closed | [A-09](A-09-mango-season-cms.md) |

Packer role: dashboard, inventory, orders, fulfillment. No product create, pincode, or CMS.

### 6.6 Android app

| ID | Requirement | Screens |
| --- | --- | --- |
| FR-A01–FR-A09 | Splash, onboarding, bottom nav, push, offline banner, deep links | [ANDROID.md](ANDROID.md), [AN-01](AN-01-splash.md)–[AN-05](AN-05-notifications.md) |

Shop FR-01–FR-24 apply in the app with Android chrome ([AN-03](AN-03-bottom-nav.md)), not SiteHeader.

---

## 7. Non-functional requirements

| ID | Requirement |
| --- | --- |
| NFR-01 | Mobile-first; usable on 360px width; tap targets for qty and checkout |
| NFR-02 | Home and listing usable on 4G; lazy-load product images |
| NFR-03 | HTTPS; passwords hashed; admin and customer sessions separate |
| NFR-04 | Payment card data never stored on our servers (gateway only) |
| NFR-05 | Prices in INR; GST inclusive with breakup on checkout and order |
| NFR-06 | Accessibility: labels on inputs, contrast on badges, keyboard for forms |
| NFR-07 | Internal `next` / `cta_url` paths only (no open redirects) |
| NFR-A01–A06 | Android min SDK 26, encrypted session, UPI intent, app links — see [ANDROID.md](ANDROID.md) |

---

## 8. Payments, tax, shipping (business rules)

- Methods: UPI, card (gateway), COD when allowed.  
- Free shipping: configurable subtotal threshold; otherwise flat shipping (config).  
- Order number format: `GS-` + integer (example).  
- Perishable mango: dispatch tied to `delivery_date` and pincode `mango_eligible`.  
- Returns: sealed dry fruit per policy page; mango/exotic generally non-returnable except quality issue with photo window ([C-17](C-17-returns.md)).

---

## 9. MVP vs later (MoSCoW)

**Must (MVP):** FR-01–FR-05, FR-10–FR-16, FR-20–FR-24, FR-30–FR-31, FR-40–FR-46, FR-A01–FR-A08, NFR-01–NFR-05, NFR-A01–NFR-A05.

**Should (soon after):** guest checkout, Hindi, GST PDF invoice download, forgot-password, notification inbox (AN-05).

**Could:** subscriptions, gift message, paid pre-order deposits, WhatsApp order alerts.

**Won’t (this product):** marketplace, iOS, admin mobile app.

---

## 10. Screen index

Full wireframes, objects, and field tables: [README.md](README.md).

Customer web: C-01 Home → C-21 Pincode not serviceable.  
Admin web: A-01 Login → A-09 Mango-season CMS.  
Android: AN-01 Splash → AN-05 Notifications + reused C-screens ([ANDROID.md](ANDROID.md)).

Header/footer/mini-cart (web): [01-global-chrome.md](01-global-chrome.md).  
Bottom nav (Android): [AN-03-bottom-nav.md](AN-03-bottom-nav.md).

---

## 11. Assumptions and open items

- Legal entity, GSTIN, and support phone/email are config, not hardcoded in copy except footer placeholders.  
- Payment gateway (e.g. Razorpay) is chosen at implementation.  
- Default language English.  
- Brand name Grove & Stone is a placeholder.  
- **Backend is specified, not built:** [BACKEND.md](BACKEND.md), [API.md](API.md). No server folder exists in this repository.
