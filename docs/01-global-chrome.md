# Global chrome

Objects and fields that appear on every customer page unless a screen says otherwise. Admin pages use AdminHeader instead (see [A-01-login.md](A-01-login.md) and [A-02-dashboard.md](A-02-dashboard.md)).

Bound objects: [00-object-dictionary.md](00-object-dictionary.md)

---

## SiteHeader

Present on all customer screens except full-bleed auth if a screen opts out (login/signup still show a compact header with Logo only).

```
+------------------------------------------------------------------+
| Logo | Shop v | SearchBar              | PincodeChip | Account | Cart(n) |
+------------------------------------------------------------------+
```

### Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | Logo | Far left | — (links to C-01) |
| 2 | ShopMenu | Left of search | Product.category |
| 3 | SearchBar | Center | query string |
| 4 | PincodeChip | Right | Cart.pincode / PincodeService |
| 5 | AccountLink | Right | Customer (or “Login”) |
| 6 | CartIcon | Far right | Cart + CartLine count |

ShopMenu items: Exotic Fruits → C-02 `?category=exotic`, Dry Fruits → C-02 `?category=dry_fruit`, Mangoes → C-05, Mango season hub → C-05.

### Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| search_query | — (query) | text input, placeholder “Search Alphonso, almonds…” | no | 1–80 chars on submit; empty submit does nothing |
| pincode | Cart / PincodeService | 6-digit; chip opens inline input | no | Numeric, exactly 6; on valid check show city + days |
| cart_count | CartLine | badge number | — | Sum of qty; hide badge if 0 |

### Actions

| Control | Label | Goes to |
| --- | --- | --- |
| Logo | Grove & Stone | C-01 Home |
| SearchBar submit | Search | C-03 Search results |
| PincodeChip save | Check | Stays; updates chip text “Deliver to 400001” or error |
| AccountLink | Login / Account | C-11 or C-13 |
| CartIcon | Cart | C-07 |

### States

- Pincode invalid: chip text “Enter pincode”, error “Enter a valid 6-digit pincode”
- Pincode not serviceable: chip stays, toast + link to C-21
- Search loading: spinner inside SearchBar

---

## SiteFooter

All customer screens.

```
+------------------------------------------------------------------+
| Shop: Exotic | Dry fruits | Mangoes                               |
| Help: Shipping | Returns | FAQ | Contact                          |
| Grove & Stone · GSTIN · email · phone                             |
+------------------------------------------------------------------+
```

### Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | FooterNavShop | Left column | categories |
| 2 | FooterNavHelp | Middle | static screens |
| 3 | FooterLegal | Right / bottom | — |
| 4 | FooterContact | Right | — |

### Fields (display only)

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| gstin | — (config) | text | yes | Display |
| support_email | — (config) | mailto link | yes | |
| support_phone | — (config) | tel link | yes | |
| copyright_year | — | text | yes | |

### Actions

| Control | Goes to |
| --- | --- |
| About | C-15 |
| Shipping | C-16 |
| Returns | C-17 |
| Contact | C-18 |
| FAQ | C-19 |

---

## MiniCart (optional overlay)

Opens from CartIcon on C-01, C-02, C-04 (not on C-07 or C-08).

### Wireframe objects

| # | Object | Binds to |
| --- | --- | --- |
| 1 | MiniCartLineList | CartLine, Product, Variant |
| 2 | MiniCartTotals | Cart |
| 3 | ViewCartButton | — |
| 4 | CheckoutButton | — |

### Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| product_name | Product | text | yes | Truncate 40 chars |
| pack_label | Variant | text | yes | |
| qty | CartLine | stepper 1–20 | yes | Integer |
| line_total | CartLine | INR | yes | |
| grand_total | derived | INR | yes | Sum of lines (ex-shipping until checkout) |

Empty: “Your cart is empty” + Shop mangoes → C-05

---

## Android

Customer app does not use SiteHeader/SiteFooter. Use [AN-03-bottom-nav.md](AN-03-bottom-nav.md). MiniCart is optional; Cart tab is the primary cart entry.
