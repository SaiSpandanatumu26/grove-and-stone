# C-16 Shipping and delivery

- **URL:** `/shipping`
- **Entry:** Footer, C-05 HowWeShip
- **Users:** Guest, Customer
- **Purpose:** Explain pincode check, perishable mango dispatch, delivery dates, COD limits.

---

## ASCII wireframe

```
+------------------------------------------------------------------+
| SiteHeader                                                       |
+------------------------------------------------------------------+
| PageTitle                                                        |
| PincodeTry  [ pincode ] [ Check ]  result                        |
| PolicyCopy (SLA, mango boxes, dry fruit post)                    |
| SiteFooter                                                       |
+------------------------------------------------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | PageTitle | Top | static |
| 2 | PincodeTry | Below title | PincodeService |
| 3 | PolicyCopy | Main | static |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| pincode | PincodeService | 6-digit | no | Length 6 numeric |
| city | PincodeService | result text | — | |
| serviceable | PincodeService | yes/no | — | |
| mango_eligible | PincodeService | yes/no | — | |
| delivery_days_min | PincodeService | number | — | |
| delivery_days_max | PincodeService | number | — | |
| cod_allowed | PincodeService | yes/no | — | |
| policy_body | — | rich text | yes | Include perishable and GST invoice note |

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| Check | Check | Stay; show result |
| Unserviceable | See unavailable | C-21 |

---

## Empty / error / loading

- **Invalid pincode:** “Enter a valid 6-digit pincode.”
- **Not in table:** treat as not serviceable → C-21 copy on-page.
