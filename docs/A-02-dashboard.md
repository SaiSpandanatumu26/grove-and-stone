# A-02 Dashboard

- **URL:** `/admin`
- **Entry:** After A-01
- **Users:** AdminUser role admin or packer
- **Purpose:** Snapshot of orders, stock, mango season.

---

## ASCII wireframe

```
+------------------------------------------------------------------+
| AdminHeader  nav: Dashboard Products Inventory Orders Delivery CMS |
+------------------------------------------------------------------+
| StatCards  orders_today | pending_pack | mango_live | low_stock  |
| RecentOrders table (subset of A-06)                              |
| SeasonStatus  MangoSeason list compact                           |
+------------------------------------------------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | AdminHeader | Top | AdminUser.name, role |
| 2 | StatCards | Row | derived from Order, Variant, MangoSeason |
| 3 | RecentOrders | Table | Order (last 10) |
| 4 | SeasonStatus | Side | MangoSeason[] |

AdminHeader on A-02–A-09: logo text, nav links, AdminUser.name, Sign out.

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| name | AdminUser | header text | yes | |
| role | AdminUser | badge | yes | packer: hide Products create? packer can fulfill; hide A-04 create if packer — packer sees Orders + Inventory |
| orders_today | derived Order | number | yes | Count created_at = today |
| pending_pack | derived Order | number | yes | status confirmed |
| mango_live | derived MangoSeason | number | yes | status live |
| low_stock | derived Variant | number | yes | stock_qty ≤ 5 and Product.is_active |
| order_number | Order | link | yes | → A-07 |
| status | Order | badge | yes | |
| grand_total | Order | INR | yes | |
| created_at | Order | datetime | yes | |
| variety_name | MangoSeason | text | yes | |
| status | MangoSeason | badge | yes | |

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| Stat pending pack | — | A-06 `?status=confirmed` |
| Order row | — | A-07 |
| Nav Products | Products | A-03 |
| Sign out | Sign out | A-01 |

---

## Empty / error / loading

- **Unauthorized:** A-01
- **Zero orders:** RecentOrders empty “No orders yet.”
- **Loading:** stat and table skeletons
