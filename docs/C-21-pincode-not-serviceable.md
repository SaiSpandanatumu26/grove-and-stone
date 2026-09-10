# C-21 Pincode not serviceable

- **URL:** `/delivery/unavailable?pincode=`
- **Entry:** Header chip, cart, checkout, shipping check when PincodeService.serviceable=false or mango_eligible=false for mango cart
- **Users:** Guest, Customer
- **Purpose:** Explain why delivery cannot proceed and offer waitlist or dry-fruit-only path if applicable.

---

## ASCII wireframe

```
+------------------------------------------------------------------+
| SiteHeader                                                       |
+------------------------------------------------------------------+
| Title  “We don’t deliver there yet”                              |
| PincodeDisplay                                                   |
| Reason (not serviceable vs mango not eligible)                   |
| [ Try another pincode ]                                          |
| [ Browse dry fruits ]  (always)                                  |
| WaitlistLite (optional email for expansion)                      |
| SiteFooter                                                       |
+------------------------------------------------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | TitleBlock | Top | static |
| 2 | PincodeDisplay | Below | PincodeService.pincode |
| 3 | ReasonCopy | Below | serviceable / mango_eligible |
| 4 | RetryPincode | Form | Cart.pincode |
| 5 | DryFruitCta | Button | — |
| 6 | WaitlistLite | Optional | WaitlistEntry-like email only (coverage request) |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| pincode | PincodeService | display + query | yes | 6-digit from query |
| city | PincodeService | text if known | no | |
| serviceable | PincodeService | drives reason | yes | |
| mango_eligible | PincodeService | drives reason | yes | If serviceable but mango false: “We deliver dry fruits here, not mango boxes.” |
| pincode (retry) | Cart | 6-digit | no | |
| email | WaitlistEntry (coverage) | email | no | If submitted, valid email; product_id may be null — store variety_name “coverage” |

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| Try pincode | Check | Stay or back to referrer if now OK |
| Browse dry fruits | Dry fruits | C-02 dry-fruits |
| Home | Home | C-01 |

---

## Empty / error / loading

- **No pincode query:** ask to enter one (same field as retry).
- **Now serviceable:** “Good news — we deliver to {pincode}.” Link C-07 or C-01.
