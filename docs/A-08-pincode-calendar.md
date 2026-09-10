# A-08 Pincode and delivery calendar

- **URL:** `/admin/delivery`
- **Entry:** AdminHeader
- **Users:** AdminUser role admin
- **Purpose:** Maintain PincodeService rows (coverage, mango flag, COD, SLA days).

---

## ASCII wireframe

```
+------------------------------------------------------------------+
| AdminHeader                                                      |
+------------------------------------------------------------------+
| Toolbar  search pincode/city  [ Add pincode ]                    |
| PincodeTable                                                     |
|  pincode | city | state | serviceable | mango | days | COD       |
| EditDrawer / row inline                                          |
+------------------------------------------------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | Toolbar | Top | — |
| 2 | AddButton | Toolbar | PincodeService |
| 3 | PincodeTable | Main | PincodeService |
| 4 | PincodeForm | Drawer or inline | PincodeService |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| search | — | text | no | pincode or city |
| pincode | PincodeService | 6-digit | yes | Unique; numeric length 6 |
| city | PincodeService | text | yes | |
| state | PincodeService | dropdown | yes | Indian state |
| serviceable | PincodeService | checkbox | yes | If false, mango_eligible should be false |
| mango_eligible | PincodeService | checkbox | yes | Cannot be true if serviceable false |
| delivery_days_min | PincodeService | integer | yes | ≥ 1 |
| delivery_days_max | PincodeService | integer | yes | ≥ min |
| cod_allowed | PincodeService | checkbox | yes | Area-level COD |

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| Add pincode | Add pincode | Open PincodeForm |
| Save | Save | Stay; table refresh |
| Delete | Delete | Confirm; block if referenced by open orders (optional: allow anyway) |

---

## Empty / error / loading

- **Duplicate pincode:** field error
- **mango_eligible vs serviceable:** “Turn off mango if not serviceable.”
- **Empty table:** “No pincodes yet.” Add CTA
- **Loading:** table skeleton
