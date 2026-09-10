# C-02 Category

- **URL:** `/c/exotic` · `/c/dry-fruits` · `/c/mangoes` (query `?category=` also allowed)
- **Entry:** Shop menu, home tiles, footer
- **Users:** Guest, Customer
- **Purpose:** Browse one catalog line with filters and open a product.

---

## ASCII wireframe

```
+------------------------------------------------------------------+
| SiteHeader                                                       |
+------------------------------------------------------------------+
| PageTitle  (Exotic fruits | Dry fruits | Mangoes)                |
| ResultCount                                                      |
+------------------------------------------------------------------+
| FilterBar: origin | pack_type | season_status | sort             |
+------------------------------------------------------------------+
| ProductGrid                                                      |
| [ ProductCard ] [ ProductCard ] [ ProductCard ]                  |
| [ ProductCard ] [ ProductCard ] [ ProductCard ]                  |
+------------------------------------------------------------------+
| Pagination                                                       |
| SiteFooter                                                       |
+------------------------------------------------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | PageTitle | Top of body | Product.category |
| 2 | ResultCount | Under title | filtered Product count |
| 3 | FilterBar | Below count | Product, Variant |
| 4 | ProductGrid | Main | Product, Variant |
| 5 | ProductCard | Grid cell | Product, default Variant |
| 6 | Pagination | Bottom | page index |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| category | Product | page title (from URL) | yes | Must be one of three |
| origin | Product | filter dropdown (multi) | no | Values from catalog |
| pack_type | Variant | filter: weight / box / tin | no | Enum |
| season_status | Product | filter chips | no | in_season, limited, coming_soon, off_season |
| sort | — | dropdown | no | default `featured`; also `price_asc`, `price_desc`, `name` |
| name | Product | card title | yes | |
| slug | Product | card link | yes | |
| origin | Product | card caption | yes | |
| season_status | Product | badge | yes | |
| images[0] | Product | image | yes | |
| price | Variant | INR default pack | yes | |
| pack_label | Variant | text | yes | |
| stock_qty | Variant | “Sold out” if 0 | yes | |
| page | — | pagination | no | Integer ≥ 1 |

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| ProductCard | — | C-04 |
| Filter change | Apply | Same URL, query updated |
| Pagination | Next / Prev | Same listing, `?page=` |
| Notify on off-season card | Notify me | C-06 |

---

## Empty / error / loading

- **No products:** “Nothing in this line right now.” CTA to Home.
- **Filters too tight:** “No matches. Clear filters.”
- **Mango off-season:** list with `coming_soon` / `off_season`; Notify → C-06.
- **Loading:** grid of card skeletons.
