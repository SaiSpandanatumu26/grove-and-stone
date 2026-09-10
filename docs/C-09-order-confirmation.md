# C-09 Order confirmation

- **URL:** `/order/{order_number}/thanks`
- **Entry:** Successful place order (C-08)
- **Users:** Customer (owner of order)
- **Purpose:** Confirm the order was placed and show next steps.

---

## ASCII wireframe

```
+------------------------------------------------------------------+
| SiteHeader                                                       |
+------------------------------------------------------------------+
| SuccessTitle  “Order placed”                                     |
| OrderNumber                                                      |
| PaymentStatus                                                    |
| AddressSnapshot + delivery_date                                  |
| OrderLineList                                                    |
| Totals                                                           |
| [ Track order ]  [ Continue shopping ]                           |
| SiteFooter                                                       |
+------------------------------------------------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | SuccessTitle | Top | Order.status |
| 2 | OrderNumberBlock | Below | Order.order_number |
| 3 | PaymentStatusBadge | Below | Order.payment_status, Payment.method |
| 4 | DeliveryBlock | Mid | Order.address, delivery_date |
| 5 | OrderLineList | Mid | OrderLine |
| 6 | TotalsBlock | Mid | Order |
| 7 | NextActions | Bottom | — |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| order_number | Order | text large | yes | |
| status | Order | badge | yes | |
| payment_method | Order | text | yes | |
| payment_status | Order | badge | yes | |
| address (all snapshot fields) | Order.address | read-only | yes | |
| delivery_date | Order | date | yes | |
| product_name | OrderLine | text | yes | |
| variant_label | OrderLine | text | yes | |
| qty | OrderLine | number | yes | |
| line_total | OrderLine | INR | yes | |
| subtotal | Order | INR | yes | |
| shipping | Order | INR | yes | |
| gst | Order | INR | yes | |
| grand_total | Order | INR | yes | |

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| Track order | Track order | C-10 |
| Continue shopping | Continue shopping | C-01 |
| View in account | My orders | C-14 |

---

## Empty / error / loading

- **Wrong customer / unknown number:** C-20.
- **Landed without placing (bookmark):** still show if order exists.
- **Loading:** short skeleton then content.
