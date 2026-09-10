# C-07 Cart

- **URL:** `/cart`
- **Entry:** CartIcon, MiniCart “View cart”
- **Users:** Guest, Customer
- **Purpose:** Review lines, qty, pincode, and continue to checkout.

---

## ASCII wireframe

```
+------------------------------------------------------------------+
| SiteHeader                                                       |
+------------------------------------------------------------------+
| CartLineTable                                                    |
|  image | name | pack | qty | unit_price | line_total | remove    |
|  …                                                               |
+------------------------------------------------------------------+
| PincodeRow  [ pincode ] [ Check ]  mango_eligible note           |
| DeliveryDateHint (if perishable lines)                           |
+------------------------------------------------------------------+
| Summary  subtotal · (shipping TBD) · note                        |
| [ Continue shopping ]  [ Checkout ]                              |
| SiteFooter                                                       |
+------------------------------------------------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | CartLineTable | Main | CartLine, Product, Variant |
| 2 | QtyStepper | Per line | CartLine.qty |
| 3 | RemoveLink | Per line | CartLine |
| 4 | PincodeRow | Below table | Cart.pincode, PincodeService |
| 5 | DeliveryDateHint | Below pincode | Cart.delivery_date (set on C-08) |
| 6 | CartSummary | Right or below | derived totals |
| 7 | CheckoutButton | Summary | — |
| 8 | EmptyCart | Replaces table | — |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| images[0] | Product | thumb | yes | |
| name | Product | link | yes | → C-04 |
| pack_label | Variant | text | yes | |
| sku | Variant | hidden/display | yes | |
| qty | CartLine | stepper 1–20 | yes | ≤ stock_qty; 0 not allowed (use remove) |
| unit_price | CartLine | INR | yes | Snapshot; refresh if still in stock rule: keep snapshot |
| line_total | CartLine | INR | yes | qty × unit_price |
| stock_qty | Variant | “Only n left” if qty > stock | — | Clamp qty |
| pincode | Cart | 6-digit | no on cart | Required before Checkout if any mango/exotic line |
| mango_eligible | PincodeService | warning | — | Block checkout if mango line and false |
| serviceable | PincodeService | warning | — | Block checkout if false |
| subtotal | derived | INR | yes | Sum line_total |

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| Qty change | — | Stay; recalc |
| Remove | Remove | Stay; drop line |
| Check pincode | Check | Stay |
| Continue shopping | Continue shopping | C-01 |
| Checkout | Checkout | C-08; if guest → C-11 with return=/checkout |
| Product name | — | C-04 |

---

## Empty / error / loading

- **Empty cart:** “Your cart is empty.” Buttons: Shop mangoes (C-05), Dry fruits (C-02 dry).
- **Line sold out:** highlight, force qty 0 / remove, “This pack is gone.”
- **Checkout blocked (pincode):** inline error, no navigation.
- **Loading:** table skeleton.
