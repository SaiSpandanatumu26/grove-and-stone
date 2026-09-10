# A-06 Order list

- **URL:** `/admin/orders`
- **Entry:** AdminHeader, dashboard stats
- **Users:** AdminUser admin or packer
- **Purpose:** Find orders by number, status, pincode, date.

---

## ASCII wireframe

```
+------------------------------------------------------------------+
| AdminHeader                                                      |
+------------------------------------------------------------------+
| Filters  order_number  status  payment_method  date_from/to      |
| OrderTable                                                       |
|  number | created_at | status | payment | pincode | total | View |
| Pagination                                                       |
+------------------------------------------------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | FilterBar | Top | Order, Payment |
| 2 | OrderTable | Main | Order |
| 3 | Pagination | Bottom | — |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| order_number | Order | search text | no | Partial match |
| status | Order | dropdown | no | Enum + All |
| payment_method | Order | dropdown | no | upi / card / cod |
| date_from | Order.created_at | date | no | |
| date_to | Order.created_at | date | no | ≥ from |
| order_number | Order | link | yes | → A-07 |
| created_at | Order | datetime | yes | |
| status | Order | badge | yes | |
| payment_method | Order | text | yes | |
| payment_status | Order | badge | yes | |
| pincode | Order | text | yes | |
| delivery_date | Order | date | yes | |
| grand_total | Order | INR | yes | |
| page | — | pagination | no | |

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| View | View | A-07 |
| Filters | Apply | Same URL query |

---

## Empty / error / loading

- **No matches:** “No orders for these filters.”
- **Loading:** table skeleton
