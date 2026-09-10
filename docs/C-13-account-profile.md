# C-13 Account — profile and addresses

- **URL:** `/account`
- **Entry:** AccountLink when logged in
- **Users:** Customer
- **Purpose:** Edit profile and manage saved addresses.

---

## ASCII wireframe

```
+------------------------------------------------------------------+
| SiteHeader                                                       |
+------------------------------------------------------------------+
| AccountNav  [ Profile ] [ Orders ]                               |
+------------------------------------------------------------------+
| ProfileForm  full_name, email (locked), phone                    |
| [ Save profile ]                                                 |
+------------------------------------------------------------------+
| AddressList                                                      |
|  AddressCard (type, default badge, lines, [ Edit ] [ Delete ])   |
| [ Add address ] → AddressForm (same fields as checkout)          |
| SiteFooter                                                       |
+------------------------------------------------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | AccountNav | Top of body | — |
| 2 | ProfileForm | Upper | Customer |
| 3 | AddressList | Lower | Address[] |
| 4 | AddressCard | List item | Address |
| 5 | AddressForm | Modal or inline | Address |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| full_name | Customer | text | yes | 2–80 |
| email | Customer | text disabled | yes | Not editable in MVP |
| phone | Customer | 10-digit | yes | Unique if changed |
| full_name | Address | text | yes | Receiver |
| phone | Address | 10-digit | yes | |
| line1 | Address | text | yes | 5–120 |
| line2 | Address | text | no | |
| city | Address | text | yes | |
| state | Address | dropdown | yes | |
| pincode | Address | 6-digit | yes | Format only here; serviceability at checkout |
| landmark | Address | text | no | |
| address_type | Address | radio | yes | home / office / other |
| is_default | Address | checkbox | yes | Setting true clears others |

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| Save profile | Save profile | Stay; toast |
| Orders tab | Orders | C-14 |
| Add address | Add address | Show AddressForm |
| Edit | Edit | AddressForm filled |
| Delete | Delete | Confirm; cannot delete last if needed — allow delete all |
| Set default | Set as default | Stay |

---

## Empty / error / loading

- **Not logged in:** C-11 `?next=/account`
- **No addresses:** “No saved addresses.” Add address CTA.
- **Phone conflict:** “This mobile is already registered.”
- **Loading:** form skeleton
