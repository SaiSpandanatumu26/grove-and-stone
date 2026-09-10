# A-03 Product list

- **URL:** `/admin/products`
- **Entry:** AdminHeader
- **Users:** AdminUser role admin (packer: read-only optional; MVP admin only)
- **Purpose:** Find products, filter by category/season, open edit.

---

## ASCII wireframe

```
+------------------------------------------------------------------+
| AdminHeader                                                      |
+------------------------------------------------------------------+
| Toolbar  [ New product ]  search  category  season_status        |
| ProductTable                                                     |
|  name | category | origin | season_status | active | variants    |
| Pagination                                                       |
+------------------------------------------------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | Toolbar | Top | filters |
| 2 | NewProductButton | Toolbar | — |
| 3 | ProductTable | Main | Product |
| 4 | Pagination | Bottom | — |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| search | — | text | no | Matches name, sku via variants |
| category | Product | dropdown filter | no | All / exotic / dry_fruit / mango |
| season_status | Product | dropdown | no | |
| is_active | Product | dropdown | no | All / yes / no |
| name | Product | link | yes | → A-04 |
| category | Product | text | yes | |
| origin | Product | text | yes | |
| season_status | Product | badge | yes | |
| is_active | Product | yes/no | yes | |
| variant_count | derived | number | yes | Count Variant |
| page | — | pagination | no | |

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| New product | New product | A-04 new |
| Row name | — | A-04 edit |
| Filters | Apply | Same page query |

---

## Empty / error / loading

- **No rows:** “No products.” CTA New product.
- **Loading:** table skeleton
