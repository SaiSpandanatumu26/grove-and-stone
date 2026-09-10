# C-05 Mango season hub

- **URL:** `/mango-season`
- **Entry:** Header Shop → Mangoes, home tile, hero CTA
- **Users:** Guest, Customer
- **Purpose:** Explain the season, list varieties, send users to shop (live) or pre-order/waitlist (not live).

---

## ASCII wireframe

```
+------------------------------------------------------------------+
| SiteHeader                                                       |
+------------------------------------------------------------------+
| SeasonHero  CMSBanner + status badge                             |
| HarvestCalendar  (variety · start · end)                         |
+------------------------------------------------------------------+
| VarietyGrid                                                      |
| [ VarietyCard: name, origin, status, CTA ] …                     |
+------------------------------------------------------------------+
| HowWeShip  (ripeness, box sizes, pincode)                        |
| SiteFooter                                                       |
+------------------------------------------------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | SeasonHero | Top | CMSBanner, MangoSeason.status |
| 2 | HarvestCalendar | Below hero | list of MangoSeason |
| 3 | VarietyGrid | Main | MangoSeason + Product |
| 4 | VarietyCard | Grid | MangoSeason, Product |
| 5 | HowWeShip | Below grid | static + link C-16 |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| title | CMSBanner | H1 | yes | |
| subtitle | CMSBanner | text | no | |
| season_state | CMSBanner | badge | yes | live / coming_soon / closed |
| image | CMSBanner | hero image | yes | |
| variety_name | MangoSeason | calendar + card title | yes | |
| harvest_start | MangoSeason | date | yes | |
| harvest_end | MangoSeason | date | yes | |
| status | MangoSeason | badge on card | yes | upcoming / live / closed |
| waitlist_enabled | MangoSeason | show Notify if true and not live | yes | |
| name | Product | card (if linked) | no | |
| origin | Product | card | no | |
| images[0] | Product | card image | no | |
| slug | Product | link when live | no | |

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| VarietyCard CTA live | Shop {variety} | C-04 Product |
| VarietyCard CTA upcoming | Pre-order | C-06 |
| VarietyCard CTA closed + waitlist | Notify me | C-06 |
| HowWeShip link | Shipping | C-16 |

---

## Empty / error / loading

- **No varieties configured:** show SeasonHero only plus “Season details coming soon.”
- **Season closed, waitlist off:** cards display-only, no CTA.
- **Loading:** calendar and card skeletons.
