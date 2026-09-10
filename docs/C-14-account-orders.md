# C-14 Account — order history

- **URL:** `/account/orders`
- **Entry:** AccountNav Orders, C-09
- **Users:** Customer
- **Purpose:** List this customer’s orders and open tracking.

---

## ASCII wireframe

```
+------------------------------------------------------------------+
| SiteHeader                                                       |
+------------------------------------------------------------------+
| AccountNav  [ Profile ] [ Orders ]                               |
+------------------------------------------------------------------+
| OrderList                                                        |
|  OrderRow: number, created_at, status, grand_total, [ View ]     |
| Pagination                                                       |
| SiteFooter                                                       |
+------------------------------------------------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | AccountNav | Top | — |
| 2 | OrderList | Main | Order[] |
| 3 | OrderRow | Row | Order |
| 4 | EmptyOrders | Replaces list | — |
| 5 | Pagination | Bottom | — |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| order_number | Order | link text | yes | |
| created_at | Order | date | yes | |
| status | Order | badge | yes | |
| grand_total | Order | INR | yes | |
| payment_status | Order | small text | yes | |
| page | — | pagination | no | |

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| View | View | C-10 |
| Order number | — | C-10 |
| Profile tab | Profile | C-13 |
| Shop CTA when empty | Shop mangoes | C-05 |

---

## Empty / error / loading

- **Not logged in:** C-11
- **No orders:** “You have no orders yet.” CTA C-05 / C-02
- **Loading:** row skeletons
