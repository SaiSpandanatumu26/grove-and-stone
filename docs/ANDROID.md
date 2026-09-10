# Android app requirements

Customer shopping app for **Grove & Stone** on Android. Same catalog, cart, checkout, and accounts as the website. **Admin and packer stay on the website only** ([A-01](A-01-login.md)–[A-09](A-09-mango-season-cms.md)).

Shared objects: [00-object-dictionary.md](00-object-dictionary.md)  
Website screens reused on Android: [C-01](C-01-home.md)–[C-21](C-21-pincode-not-serviceable.md) (same fields and rules; chrome is BottomNav, not SiteHeader).

---

## 1. Purpose

Ship a Google Play app so shoppers can browse exotic fruits, dry fruits, and mango season, place orders (UPI / card / COD), and get status push notifications.

The app is a **client of the same backend** as the website. Prices, stock, pincodes, and orders must match the web shop.

---

## 2. Platform

| Item | MVP |
| --- | --- |
| OS | Android 8.0 (API 26) and above |
| Form | Phone portrait; tablets not optimized |
| Distribution | Google Play |
| Auth | Same Customer email/phone/password as website |
| Payments | Same gateway as web (UPI intent / cards); COD in-app |
| Push | FCM for order packed/shipped/delivered and mango season open |

---

## 3. What is in the app vs website

| Capability | Website | Android |
| --- | --- | --- |
| Shop, search, PDP, mango hub, waitlist, cart, checkout | Yes | Yes (same FR-01–FR-24) |
| About, shipping, returns, FAQ, contact | Yes | Yes (in-app WebView or native copies of C-15–C-19) |
| Admin / packer | Yes | **No** |
| Splash, onboarding, bottom nav, OS push permission | No | Yes (AN screens) |
| Deep links | URLs | App links: `/p/{slug}`, `/order/{order_number}`, `/mango-season` |

---

## 4. Android functional requirements

| ID | Requirement | Screens |
| --- | --- | --- |
| FR-A01 | Cold start shows splash then home or last session | [AN-01](AN-01-splash.md) |
| FR-A02 | First launch: optional 1–3 onboarding cards + pincode | [AN-02](AN-02-onboarding.md) |
| FR-A03 | Bottom nav: Home, Mangoes, Cart (badge), Account | [AN-03](AN-03-bottom-nav.md) |
| FR-A04 | After login (or first order), request notification permission | [AN-04](AN-04-push-permission.md) |
| FR-A05 | Register FCM token on Customer session | object DeviceToken |
| FR-A06 | Push: order status change, mango season live (opt-in) | [AN-05](AN-05-notifications.md) |
| FR-A07 | Hardware/system back follows Android back stack; checkout back → cart | — |
| FR-A08 | Offline: show cached catalog with banner “You’re offline”; block checkout | — |
| FR-A09 | Play Integrity / no rooted-device hard block in MVP (optional later) | — |

Website FR-01–FR-24 and NFR-03–NFR-05 apply inside the app.

---

## 5. Navigation (Android)

```
Splash → (first run) Onboarding → Home
BottomNav: Home | Mangoes | Cart | Account
Home → Category / Search / PDP
Mangoes → C-05 hub
Account → login or profile + orders
Push tap → C-10 order or C-05 hub
```

Search is an icon on Home (not a fifth tab). Shop categories sit on Home tiles, not in a website header menu.

---

## 6. Screen mapping (website → app)

| Website | Android |
| --- | --- |
| SiteHeader / Footer | [AN-03](AN-03-bottom-nav.md) + screen title bar |
| C-01 Home | Same objects/fields; hero + tiles; no footer columns |
| C-02–C-21 | Same fields and business rules |
| C-11 / C-12 | Full-screen; no website Logo-only chrome — use app toolbar |
| A-01–A-09 | Not in the app |

---

## 7. Non-functional (Android)

| ID | Requirement |
| --- | --- |
| NFR-A01 | Target / compile current Play-required API; min SDK 26 |
| NFR-A02 | Images cached; listing usable on 4G |
| NFR-A03 | Store Customer session in encrypted prefs / datastore |
| NFR-A04 | UPI: Android intent to installed UPI apps; fallback to gateway |
| NFR-A05 | Accessibility: content descriptions on nav and product images |
| NFR-A06 | Deep links verified for `https` host of the shop |

---

## 8. Out of scope (Android MVP)

- iOS  
- Admin app  
- In-app chat / WhatsApp SDK  
- Offline checkout  
- Widget / Wear OS  
