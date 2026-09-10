# A-07 Order fulfillment

- **URL:** `/admin/orders/{id}`
- **Entry:** A-06, A-02 recent
- **Users:** AdminUser admin or packer
- **Purpose:** View full order, pack/ship/deliver, cancel if allowed.

---

## ASCII wireframe

```
+------------------------------------------------------------------+
| AdminHeader                                                      |
+------------------------------------------------------------------+
| OrderMeta  number, created_at, status, payment                   |
| StatusActions  [ Mark packed ] [ Mark shipped ] [ Delivered ]    |
|                [ Cancel ]                                        |
+------------------------------------------------------------------+
| OrderLineTable  sku, name, pack, qty, prices                     |
| AddressBlock  snapshot                                           |
| DeliveryDate                                                     |
| CustomerNotes                                                    |
| TotalsBlock                                                      |
| PaymentBlock  method, status, gateway_ref                        |
+------------------------------------------------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | OrderMeta | Top | Order |
| 2 | StatusActions | Top right | Order.status |
| 3 | OrderLineTable | Main | OrderLine |
| 4 | AddressBlock | Side | Order.address |
| 5 | PaymentBlock | Below | Payment |
| 6 | TotalsBlock | Below | Order |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| order_number | Order | text | yes | |
| created_at | Order | datetime | yes | |
| status | Order | badge + actions | yes | Transitions: confirmed→packed→shipped→delivered; cancel from confirmed only |
| customer_id | Order | text / link | no | Display email if joined Customer |
| product_name | OrderLine | text | yes | Snapshot — do not live-edit catalog |
| variant_label | OrderLine | text | yes | |
| sku | OrderLine | text | yes | |
| qty | OrderLine | number | yes | Read-only |
| unit_price | OrderLine | INR | yes | |
| line_total | OrderLine | INR | yes | |
| full_name, phone, line1, line2, city, state, pincode, landmark, address_type | Order.address | read-only | yes | |
| delivery_date | Order | date | yes | Admin may edit if status confirmed (optional MVP: read-only) |
| customer_notes | Order | text | no | |
| payment_method | Payment | text | yes | |
| payment_status | Payment | badge | yes | |
| amount | Payment | INR | yes | |
| gateway_ref | Payment | text | no | |
| subtotal, shipping, gst, discount, grand_total | Order | INR | yes | |

---

## Actions

| Control | Label | Condition | Goes to |
| --- | --- | --- | --- |
| Mark packed | Mark packed | status=confirmed | Stay; status packed |
| Mark shipped | Mark shipped | status=packed | Stay |
| Mark delivered | Mark delivered | status=shipped | Stay |
| Cancel | Cancel | status=confirmed | Confirm dialog; cancelled |

---

## Empty / error / loading

- **Unknown id:** A-06
- **Illegal transition:** toast “Cannot change status.”
- **Loading:** page skeleton
