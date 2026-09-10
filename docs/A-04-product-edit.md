# A-04 Product create / edit

- **URL:** `/admin/products/new` · `/admin/products/{id}`
- **Entry:** A-03
- **Users:** AdminUser role admin
- **Purpose:** Create or update Product and its Variants (packs).

---

## ASCII wireframe

```
+------------------------------------------------------------------+
| AdminHeader                                                      |
+------------------------------------------------------------------+
| ProductForm                                                      |
|  name, slug, category, origin                                    |
|  short_description, long_description                             |
|  season_status, harvest_window                                   |
|  handling_notes, ripeness_note, farm_story                       |
|  is_gift_eligible, is_active                                     |
|  images (upload list)                                            |
+------------------------------------------------------------------+
| VariantTable  add row                                            |
|  sku, pack_label, pack_type, weight_grams, unit_count            |
|  price, gst_percent, stock_qty, cod_allowed, is_default          |
| [ Save ]  [ Cancel ]                                             |
+------------------------------------------------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | ProductForm | Upper | Product |
| 2 | ImageUploader | In form | Product.images |
| 3 | VariantTable | Lower | Variant[] |
| 4 | VariantRow | Table | Variant |
| 5 | SaveButton | Bottom | Product + Variant |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| name | Product | text | yes | 2–80 |
| slug | Product | text | yes | Unique slug; auto from name, editable |
| category | Product | dropdown | yes | exotic / dry_fruit / mango |
| origin | Product | text | yes | |
| short_description | Product | text | yes | ≤160 |
| long_description | Product | textarea | yes | |
| season_status | Product | dropdown | yes | Enum |
| harvest_window | Product | text | no | Shown extra if category=mango |
| handling_notes | Product | textarea | no | |
| ripeness_note | Product | textarea | no | Mango |
| farm_story | Product | textarea | no | Factual only |
| is_gift_eligible | Product | checkbox | yes | Default false |
| is_active | Product | checkbox | yes | Unchecked = hidden on site |
| images | Product | multi upload | yes | ≥1 image on save |
| sku | Variant | text | yes | Unique |
| pack_label | Variant | text | yes | |
| pack_type | Variant | dropdown | yes | weight / box / tin |
| weight_grams | Variant | integer | if weight | > 0 |
| unit_count | Variant | integer | if box | > 0 (dozen/pieces) |
| price | Variant | INR | yes | > 0 |
| gst_percent | Variant | decimal | yes | 0–28 typical 5/12 |
| stock_qty | Variant | integer | yes | ≥ 0 |
| cod_allowed | Variant | checkbox | yes | Default true; mango boxes often false |
| is_default | Variant | radio per product | yes | Exactly one default |

Must have ≥1 variant on save.

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| Add pack | Add pack | New VariantRow |
| Delete pack | Delete | Remove row (block if last) |
| Save | Save | A-03; toast |
| Cancel | Cancel | A-03 |

---

## Empty / error / loading

- **Unknown id:** A-03 with error toast
- **Duplicate slug/sku:** field error
- **No image:** “Add at least one image.”
- **Loading:** form skeleton
