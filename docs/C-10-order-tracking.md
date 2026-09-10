# C-10 Order detail / tracking

- **URL:** `/order/{order_number}`
- **Entry:** C-09, C-14, email link
- **Users:** Customer (owner)
- **Purpose:** Show status timeline, lines, address, payment.

---

## ASCII wireframe

```
+------------------------------------------------------------------+
| SiteHeader                                                       |
+------------------------------------------------------------------+
| OrderHeader  number · placed date · status                       |
| StatusTimeline  confirmed → packed → shipped → delivered         |
+------------------------------------------------------------------+
| OrderLineList                                                    |
| DeliveryBlock (address + delivery_date)                          |
| PaymentBlock                                                     |
| TotalsBlock                                                      |
| [ Help / Contact ]                                               |
| SiteFooter                                                       |
+------------------------------------------------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | OrderHeader | Top | Order |
| 2 | StatusTimeline | Below | Order.status |
| 3 | OrderLineList | Main | OrderLine |
| 4 | DeliveryBlock | Side / below | Order.address, delivery_date |
| 5 | PaymentBlock | Below | Payment, Order |
| 6 | TotalsBlock | Below | Order |
| 7 | HelpLink | Bottom | — |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| order_number | Order | text | yes | |
| created_at | Order | datetime | yes | |
| status | Order | timeline step | yes | Current step highlighted |
| product_name | OrderLine | text | yes | |
| variant_label | OrderLine | text | yes | |
| sku | OrderLine | text | yes | |
| qty | OrderLine | number | yes | |
| unit_price | OrderLine | INR | yes | |
| line_total | OrderLine | INR | yes | |
| full_name, phone, line1, line2, city, state, pincode, landmark | Order.address | read-only | yes | Snapshot |
| delivery_date | Order | date | yes | |
| payment_method | Payment / Order | text | yes | |
| payment_status | Payment / Order | badge | yes | |
| gateway_ref | Payment | text | no | Hide if empty / COD |
| subtotal, shipping, gst, discount, grand_total | Order | INR | yes | |
| customer_notes | Order | text | no | Hide if empty |

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| Contact | Need help | C-18 |
| Back to orders | My orders | C-14 |
| Cancel | Cancel order | Stay; only if status is confirmed and not packed; confirm dialog. Sets cancelled. |

Cancel is MVP for confirmed-only, not after packed.

---

## Empty / error / loading

- **Not owner / missing:** C-20.
- **Cancelled:** timeline shows cancelled; no cancel button.
- **Loading:** header + line skeletons.
