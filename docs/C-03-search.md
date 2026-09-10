# C-03 Search results

- **URL:** `/search?q={search_query}`
- **Entry:** SiteHeader SearchBar submit
- **Users:** Guest, Customer
- **Purpose:** Show products matching name, origin, or variety.

---

## ASCII wireframe

```
+------------------------------------------------------------------+
| SiteHeader (query remains in SearchBar)                          |
+------------------------------------------------------------------+
| “Results for {search_query}”   ResultCount                       |
| FilterBar (same as C-02, optional)                               |
+------------------------------------------------------------------+
| ProductGrid  [ ProductCard … ]                                   |
+------------------------------------------------------------------+
| SiteFooter                                                       |
+------------------------------------------------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | SearchSummary | Top of body | search_query |
| 2 | FilterBar | Optional | Product, Variant |
| 3 | ProductGrid | Main | Product, Variant |
| 4 | ProductCard | Grid | Product, default Variant |
| 5 | EmptySearch | Replaces grid | — |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| search_query | — | from URL / SearchBar | yes | 1–80 chars; trim |
| name | Product | card title, highlight match | yes | |
| origin | Product | caption | yes | |
| category | Product | small label | yes | |
| season_status | Product | badge | yes | |
| images[0] | Product | image | yes | |
| price | Variant | INR | yes | |
| pack_label | Variant | text | yes | |
| slug | Product | link | yes | |

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| ProductCard | — | C-04 |
| New search | Search | C-03 with new `q` |
| Clear | Clear search | C-01 |

---

## Empty / error / loading

- **Empty query:** do not land here; SearchBar ignores empty submit.
- **Zero hits:** “No fruits match '{query}'.” Suggestions: Exotic / Dry / Mangoes tiles.
- **Loading:** skeleton grid.
