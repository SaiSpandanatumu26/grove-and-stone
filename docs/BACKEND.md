# Backend requirements

There is **no backend codebase** in this repo yet. This file is the backend/API spec. Website and Android use the **same API**. Admin uses the same API with admin auth. Payment card data never hits this server (gateway + webhook).

**Objects:** [00-object-dictionary.md](00-object-dictionary.md)  
**Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)  
**Endpoint list:** [API.md](API.md)  
**Clients:** website screens C-/A-; Android [ANDROID.md](ANDROID.md)

---

## 1. Role

| Client | Uses |
| --- | --- |
| Website (shop) | Public + customer APIs |
| Android app | Same public + customer APIs + DeviceToken |
| Website admin | Admin APIs only (`/api/v1/admin/...`) |

One catalog, one cart model, one order store. Prices and stock must not differ by client.

---

## 2. Style (implementation-agnostic)

| Item | Rule |
| --- | --- |
| Protocol | HTTPS JSON REST |
| Base URL | `https://{host}/api/v1` |
| Time | ISO-8601 UTC |
| Money | Integer **paise** in JSON (`price_paise`) or decimal INR strings — pick one in implementation; screens show INR. Spec below uses INR numbers for readability (`price`: 499.00) |
| IDs | UUID except `order_number` (human) and `pincode` (6-digit) |
| Pagination | `page` (1-based), `page_size` (default 20, max 50), response `{ items, total, page, page_size }` |
| Auth customer | `Authorization: Bearer {access_token}` after login/signup |
| Auth admin | Separate Bearer from `POST /admin/auth/login` |
| Guest cart | `X-Session-Id` header (UUID created by client) until login; on login merge session cart into Customer cart |

Stack (Django, Node, etc.) is **not** fixed in this doc.

---

## 3. Error body (all 4xx/5xx)

```json
{
  "code": "PINCODE_NOT_SERVICEABLE",
  "message": "We don’t deliver to this pincode.",
  "fields": { "pincode": "Enter a serviceable pincode." }
}
```

| HTTP | When |
| --- | --- |
| 400 | Validation (`fields` set) |
| 401 | Missing/expired token |
| 403 | Admin route with customer token, or packer hitting CMS |
| 404 | Unknown slug/id; **do not** reveal other customers’ orders (same 404) |
| 409 | Duplicate email/phone, duplicate waitlist (treat waitlist 409 as success-equivalent on client) |
| 422 | Business rule (COD not allowed, mango not eligible, sold out) |

---

## 4. Security

- Passwords hashed; never returned  
- Customer and admin tokens must not be interchangeable  
- CORS: shop origins + Android does not use CORS  
- Webhook from payment gateway: signature verify  
- Rate-limit login, signup, waitlist, contact  

---

## 5. Jobs / side effects (not HTTP screens)

| Event | Backend does |
| --- | --- |
| Order paid / COD confirmed | Email (optional MVP); FCM if DeviceToken |
| Order status packed/shipped/delivered | FCM `type=order` |
| MangoSeason status → live | FCM `type=mango_season` to opted-in tokens (batch) |
| Waitlist | Store WaitlistEntry; notify when Product becomes purchasable (email later) |

---

## 6. Out of scope for this backend spec

- Source code, Docker, DB migrations  
- Choosing PostgreSQL vs MySQL  
- iOS APNs (Android FCM only)  
