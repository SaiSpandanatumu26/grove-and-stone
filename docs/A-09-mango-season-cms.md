# A-09 Mango-season CMS

- **URL:** `/admin/mango-season`
- **Entry:** AdminHeader
- **Users:** AdminUser role admin
- **Purpose:** Publish home/hub banner and per-variety harvest / pre-order / waitlist windows.

---

## ASCII wireframe

```
+------------------------------------------------------------------+
| AdminHeader                                                      |
+------------------------------------------------------------------+
| BannerForm  CMSBanner                                            |
|  title, subtitle, season_state, cta_label, cta_url               |
|  image, start_date, end_date, is_published                       |
| [ Save banner ]                                                  |
+------------------------------------------------------------------+
| VarietyTable  MangoSeason rows                                   |
|  variety_name, product link, harvest dates,                      |
|  preorder_open/close, waitlist_enabled, status                   |
| [ Add variety ]  [ Save varieties ]                              |
+------------------------------------------------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | BannerForm | Upper | CMSBanner (home + hub can share one published row, or two rows: slot=home\|hub — MVP one published banner reused on C-01 and C-05) |
| 2 | VarietyTable | Lower | MangoSeason[] |
| 3 | VarietyRow | Table | MangoSeason |
| 4 | ProductPicker | In row | Product (category mango) |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| title | CMSBanner | text | yes | |
| subtitle | CMSBanner | text | no | |
| season_state | CMSBanner | dropdown | yes | live / coming_soon / closed |
| cta_label | CMSBanner | text | yes | |
| cta_url | CMSBanner | text | yes | Internal path e.g. `/mango-season` |
| image | CMSBanner | upload | yes | If is_published |
| start_date | CMSBanner | date | yes | |
| end_date | CMSBanner | date | yes | ≥ start_date |
| is_published | CMSBanner | checkbox | yes | Unpublished → C-01 hides hero |
| variety_name | MangoSeason | text | yes | |
| product_id | MangoSeason | dropdown of mango Products | no | Required if status=live |
| harvest_start | MangoSeason | date | yes | |
| harvest_end | MangoSeason | date | yes | ≥ harvest_start |
| preorder_open | MangoSeason | date | no | If set, ≤ harvest_start |
| preorder_close | MangoSeason | date | no | ≥ preorder_open |
| waitlist_enabled | MangoSeason | checkbox | yes | Enables C-06 |
| status | MangoSeason | dropdown | yes | upcoming / live / closed |

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| Save banner | Save banner | Stay; toast |
| Add variety | Add variety | New VarietyRow |
| Save varieties | Save varieties | Stay |
| Open product | Product name | A-04 |
| Preview hub | Preview | C-05 (new tab) |

---

## Empty / error / loading

- **Publish without image:** “Add a banner image.”
- **Live variety without product_id:** “Link a product before setting Live.”
- **Date order invalid:** field errors
- **No varieties:** table empty + Add variety
- **Loading:** form + table skeletons
