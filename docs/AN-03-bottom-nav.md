# AN-03 Bottom navigation

- **Platform:** Android only (replaces [SiteHeader](01-global-chrome.md) shop menu and footer)
- **Entry:** All main shop screens except splash, onboarding, checkout payment sheet
- **Users:** Guest, Customer
- **Purpose:** Switch Home, Mango season, Cart, Account.

Hide bottom nav on: checkout payment, full-screen login/signup (optional: keep nav on login). MVP: hide on C-08 Place order payment overlay and AN-01/AN-02.

---

## ASCII wireframe

```
+---------------------------+
| Toolbar: title | Search | PincodeChip
| … screen body …           |
+---------------------------+
| Home | Mangoes | Cart(n) | Account |
+---------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | AppToolbar | Top | screen title |
| 2 | SearchIcon | Toolbar | — |
| 3 | PincodeChip | Toolbar | Cart.pincode |
| 4 | BottomNav | Bottom | — |
| 5 | CartBadge | Cart tab | CartLine qty sum |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| tab | — | 4 destinations | yes | home, mangoes, cart, account |
| cart_count | CartLine | badge | — | Hide if 0 |
| pincode | Cart | chip | no | Same validation as website header |
| search_query | — | opens search screen | no | Same as C-03 |

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| Home | Home | C-01 |
| Mangoes | Mangoes | C-05 |
| Cart | Cart | C-07 |
| Account (logged out) | Account | C-11 |
| Account (logged in) | Account | C-13 |
| Search icon | — | C-03 (empty query shows recent/suggestions; submit required to search) |
| Pincode chip | — | Inline dialog; same as website PincodeChip |

---

## Empty / error / loading

- **Cart tab with empty cart:** still open C-07 empty state.
- **Back from tab:** system back leaves the tab’s stack, then previous tab, then exit app from Home root.
