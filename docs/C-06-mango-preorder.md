# C-06 Mango pre-order / waitlist

- **URL:** `/mango-season/preorder/{slug}`
- **Entry:** C-04 Notify, C-05 VarietyCard CTA when not live
- **Users:** Guest, Customer
- **Purpose:** Capture demand for a variety before harvest or when sold out. Pre-order (pay later / pay now is phase 2 — MVP is waitlist + optional deposit note).

MVP: collect WaitlistEntry only. Paid pre-order is later.

---

## ASCII wireframe

```
+------------------------------------------------------------------+
| SiteHeader                                                       |
+------------------------------------------------------------------+
| VarietySummary  image · name · origin · harvest window · status  |
| Copy: “We’ll email when boxes open”                              |
+------------------------------------------------------------------+
| WaitlistForm                                                     |
|   full_name                                                      |
|   email *                                                        |
|   phone                                                          |
|   [ Notify me ]                                                  |
| SuccessMessage (after submit)                                    |
| SiteFooter                                                       |
+------------------------------------------------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | VarietySummary | Top | Product, MangoSeason |
| 2 | WaitlistForm | Center | WaitlistEntry |
| 3 | SubmitButton | Form footer | WaitlistEntry |
| 4 | SuccessMessage | Replaces form | WaitlistEntry |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| name | Product | heading | yes | From slug |
| origin | Product | text | yes | |
| images[0] | Product | image | yes | |
| variety_name | MangoSeason / WaitlistEntry | display + stored | yes | |
| harvest_start | MangoSeason | date text | yes | |
| harvest_end | MangoSeason | date text | yes | |
| status | MangoSeason | badge | yes | Form only if waitlist_enabled or upcoming |
| product_id | WaitlistEntry | hidden | yes | From URL slug |
| full_name | WaitlistEntry | text | no | 2–80 chars |
| email | WaitlistEntry | email | yes if phone empty | Valid email; at least email or phone |
| phone | WaitlistEntry | 10-digit | yes if email empty | Indian mobile |

If Customer is logged in, pre-fill full_name, email, phone.

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| Notify me | Notify me | Stay; SuccessMessage |
| Back to season | Mango season | C-05 |
| Shop if status becomes live | Shop | C-04 |

---

## Empty / error / loading

- **Unknown slug:** C-20.
- **waitlist_enabled false and status live:** redirect C-04.
- **Duplicate email+product:** “You’re already on the list.” (success-equivalent)
- **Neither email nor phone:** “Enter email or mobile.”
- **Submit loading:** button disabled, “Saving…”
