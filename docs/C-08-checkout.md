# C-08 Checkout

- **URL:** `/checkout`
- **Entry:** C-07 Checkout (login required for MVP)
- **Users:** Customer
- **Purpose:** Collect address, pincode serviceability, delivery date, payment method, place order.

---

## ASCII wireframe

```
+------------------------------------------------------------------+
| SiteHeader (compact; no MiniCart)                                |
+------------------------------------------------------------------+
| LEFT                                              | RIGHT        |
| SavedAddressList or DeliveryAddressForm           | OrderSummary |
|   full_name, phone, line1, line2,                 |  lines       |
|   city, state, pincode, landmark, type            |  subtotal    |
| PincodeChecker (locked to address pincode)        |  shipping    |
| DeliveryDatePicker                                |  gst         |
| CustomerNotes                                     |  grand_total |
| PaymentMethodGroup  UPI | Card | COD              |              |
| COD hidden if not allowed                         |              |
| [ Place order ]                                   |              |
+------------------------------------------------------------------+
| SiteFooter                                                       |
+------------------------------------------------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | SavedAddressList | Left top | Address[] |
| 2 | DeliveryAddressForm | Left (new / edit) | Address |
| 3 | PincodeChecker | Left | PincodeService (Address.pincode) |
| 4 | DeliveryDatePicker | Left | Order.delivery_date |
| 5 | CustomerNotes | Left | Order.customer_notes |
| 6 | PaymentMethodGroup | Left | Payment / Order.payment_method |
| 7 | OrderSummary | Right | CartLine, Product, Variant, Order totals |
| 8 | PlaceOrderButton | Left bottom | Order, Payment |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| address id select | Address | radio of saved | no | If none, form required |
| full_name | Address | text | yes | 2–80 |
| phone | Address | 10-digit | yes | Indian mobile |
| line1 | Address | text | yes | 5–120 |
| line2 | Address | text | no | ≤120 |
| city | Address | text | yes | |
| state | Address | dropdown (Indian states) | yes | |
| pincode | Address | 6-digit | yes | Must be PincodeService.serviceable |
| landmark | Address | text | no | ≤80 |
| address_type | Address | radio home/office/other | yes | |
| serviceable | PincodeService | read-only status | yes | Block place if false |
| mango_eligible | PincodeService | read-only | if mango lines | Block if false |
| delivery_days_min / max | PincodeService | help text | yes | Date picker min = today + min days |
| delivery_date | Order | date picker | yes | ≥ min dispatch; not beyond 14 days; no past |
| customer_notes | Order | textarea | no | ≤200 |
| payment_method | Order / Payment | radio upi / card / cod | yes | COD hidden if any Variant.cod_allowed=false OR PincodeService.cod_allowed=false |
| product_name | OrderLine preview | text | yes | From cart |
| variant_label | OrderLine preview | text | yes | |
| qty | OrderLine preview | number | yes | |
| line_total | OrderLine preview | INR | yes | |
| subtotal | Order | INR | yes | |
| shipping | Order | INR | yes | 0 if subtotal ≥ free-ship threshold (config) |
| gst | Order | INR | yes | Display breakup |
| grand_total | Order | INR | yes | subtotal + shipping (prices already GST-incl: show included GST) |

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| Use this address | — | Stay; fill form |
| Add new address | Add address | Expand form |
| Place order (UPI/card) | Place order | Payment gateway; then C-09 on paid |
| Place order (COD) | Place order | Create Order status confirmed, payment_status cod; C-09 |
| Back | Cart | C-07 |

---

## Empty / error / loading

- **Empty cart:** redirect C-07.
- **Guest:** redirect C-11 `?next=/checkout`.
- **Pincode fail:** “We don’t deliver to this pincode.” Link C-21.
- **Payment failed:** stay, “Payment failed. Try again.” Order pending_payment.
- **Place loading:** button locked.
- **Date missing:** “Pick a delivery date.”
