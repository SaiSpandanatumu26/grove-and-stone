# A-05 Inventory

- **URL:** `/admin/inventory`
- **Entry:** AdminHeader
- **Users:** AdminUser admin or packer
- **Purpose:** Adjust Variant.stock_qty quickly without full product edit.

---

## ASCII wireframe

```
+------------------------------------------------------------------+
| AdminHeader                                                      |
+------------------------------------------------------------------+
| Filters  search sku/name  category  low_stock_only               |
| InventoryTable                                                   |
|  product name | sku | pack_label | stock_qty [edit] | season     |
| [ Save changes ]                                                 |
+------------------------------------------------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | FilterBar | Top | Product, Variant |
| 2 | InventoryTable | Main | Product, Variant |
| 3 | StockInput | Cell | Variant.stock_qty |
| 4 | SaveButton | Bottom | Variant[] dirty rows |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| search | — | text | no | name or sku |
| category | Product | dropdown | no | |
| low_stock_only | — | checkbox | no | stock_qty ≤ 5 |
| name | Product | text | yes | Link A-04 for admin |
| sku | Variant | text | yes | |
| pack_label | Variant | text | yes | |
| stock_qty | Variant | integer input | yes | ≥ 0; integer |
| season_status | Product | badge | yes | |
| is_active | Product | badge | yes | |

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| Save changes | Save changes | Stay; persist dirty stock_qty |
| Product name | — | A-04 (admin only) |

---

## Empty / error / loading

- **No variants:** “No packs to stock.”
- **Invalid qty:** row error, no save for that row
- **Loading:** table skeleton
