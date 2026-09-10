# Grove & Stone — documentation index

E-commerce **website** plus **Android customer app** for exotic fruits, dry fruits, and natural mangoes. Market: India.

**Start here:** [REQUIREMENTS.md](REQUIREMENTS.md) · **Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md) · **Android:** [ANDROID.md](ANDROID.md) · **Backend:** [BACKEND.md](BACKEND.md)

All files in this folder. Objects are defined once in the dictionary; each screen lists wireframe objects and fields.

## Shared

| File | What it is |
| --- | --- |
| [REQUIREMENTS.md](REQUIREMENTS.md) | Product requirements (website + Android) |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System context, clients, API modules, checkout, auth, data |
| [SEARCH.md](SEARCH.md) | Search query, indexed fields, `GET /search`, C-03 |
| [BACKEND.md](BACKEND.md) | Backend role, auth, errors — **no server code in this repo** |
| [API.md](API.md) | REST endpoints `/api/v1` for web + Android + admin |
| [ANDROID.md](ANDROID.md) | Android app: platform, nav, FR-A, mapping to C-screens |
| [00-object-dictionary.md](00-object-dictionary.md) | Customer, Address, Product, Variant, Cart, Order, DeviceToken, … |
| [01-global-chrome.md](01-global-chrome.md) | Website SiteHeader, SiteFooter, MiniCart |

## Customer screens

| ID | File | URL |
| --- | --- | --- |
| C-01 | [C-01-home.md](C-01-home.md) | `/` |
| C-02 | [C-02-category.md](C-02-category.md) | `/c/{exotic\|dry-fruits\|mangoes}` |
| C-03 | [C-03-search.md](C-03-search.md) | `/search?q=` — see also [SEARCH.md](SEARCH.md) |
| C-04 | [C-04-product-detail.md](C-04-product-detail.md) | `/p/{slug}` |
| C-05 | [C-05-mango-season-hub.md](C-05-mango-season-hub.md) | `/mango-season` |
| C-06 | [C-06-mango-preorder.md](C-06-mango-preorder.md) | `/mango-season/preorder/{slug}` |
| C-07 | [C-07-cart.md](C-07-cart.md) | `/cart` |
| C-08 | [C-08-checkout.md](C-08-checkout.md) | `/checkout` |
| C-09 | [C-09-order-confirmation.md](C-09-order-confirmation.md) | `/order/{order_number}/thanks` |
| C-10 | [C-10-order-tracking.md](C-10-order-tracking.md) | `/order/{order_number}` |
| C-11 | [C-11-login.md](C-11-login.md) | `/login` |
| C-12 | [C-12-signup.md](C-12-signup.md) | `/signup` |
| C-13 | [C-13-account-profile.md](C-13-account-profile.md) | `/account` |
| C-14 | [C-14-account-orders.md](C-14-account-orders.md) | `/account/orders` |
| C-15 | [C-15-about.md](C-15-about.md) | `/about` |
| C-16 | [C-16-shipping.md](C-16-shipping.md) | `/shipping` |
| C-17 | [C-17-returns.md](C-17-returns.md) | `/returns` |
| C-18 | [C-18-contact.md](C-18-contact.md) | `/contact` |
| C-19 | [C-19-faq.md](C-19-faq.md) | `/faq` |
| C-20 | [C-20-404.md](C-20-404.md) | unmatched routes |
| C-21 | [C-21-pincode-not-serviceable.md](C-21-pincode-not-serviceable.md) | `/delivery/unavailable` |

## Admin screens

| ID | File | URL |
| --- | --- | --- |
| A-01 | [A-01-login.md](A-01-login.md) | `/admin/login` |
| A-02 | [A-02-dashboard.md](A-02-dashboard.md) | `/admin` |
| A-03 | [A-03-product-list.md](A-03-product-list.md) | `/admin/products` |
| A-04 | [A-04-product-edit.md](A-04-product-edit.md) | `/admin/products/new` and `/admin/products/{id}` |
| A-05 | [A-05-inventory.md](A-05-inventory.md) | `/admin/inventory` |
| A-06 | [A-06-order-list.md](A-06-order-list.md) | `/admin/orders` |
| A-07 | [A-07-order-fulfillment.md](A-07-order-fulfillment.md) | `/admin/orders/{id}` |
| A-08 | [A-08-pincode-calendar.md](A-08-pincode-calendar.md) | `/admin/delivery` |
| A-09 | [A-09-mango-season-cms.md](A-09-mango-season-cms.md) | `/admin/mango-season` |

## Android screens (app-only chrome)

Shop pages C-01–C-21 are reused in the app. These files are Android-only:

| ID | File | Role |
| --- | --- | --- |
| AN-01 | [AN-01-splash.md](AN-01-splash.md) | Splash |
| AN-02 | [AN-02-onboarding.md](AN-02-onboarding.md) | First-run |
| AN-03 | [AN-03-bottom-nav.md](AN-03-bottom-nav.md) | Bottom nav + toolbar |
| AN-04 | [AN-04-push-permission.md](AN-04-push-permission.md) | Notification permission |
| AN-05 | [AN-05-notifications.md](AN-05-notifications.md) | In-app inbox |

## Screen template (every C-/A-/AN- file)

1. Screen ID, name, URL  
2. Purpose  
3. ASCII wireframe  
4. Wireframe objects  
5. Fields table (Field \| Object \| Control \| Required \| Validation)  
6. Actions  
7. Empty / error / loading  
