# C-01 Home

- **URL:** `/`
- **Entry:** Logo, first visit, marketing links
- **Users:** Guest, Customer
- **Purpose:** Show the three shop lines, mango-season status, and a path to shop or pre-order.

Chrome: [SiteHeader](01-global-chrome.md), [SiteFooter](01-global-chrome.md)

---

## ASCII wireframe

```
+------------------------------------------------------------------+
| SiteHeader                                                       |
+------------------------------------------------------------------+
| HeroBanner (CMSBanner image + title + CTA)                       |
+------------------------------------------------------------------+
| PincodeStrip  [ pincode ] [ Check ]   city · days                |
+------------------------------------------------------------------+
| CategoryTiles:  [ Exotic fruits ] [ Dry fruits ] [ Mangoes ]     |
+------------------------------------------------------------------+
| MangoSeasonStrip  status · harvest window · [ Shop / Pre-order ] |
+------------------------------------------------------------------+
| FeaturedRow title: This week                                     |
| [ ProductCard ] [ ProductCard ] [ ProductCard ] [ ProductCard ]  |
+------------------------------------------------------------------+
| TrustStrip: origin · natural harvest · perishable dispatch       |
+------------------------------------------------------------------+
| SiteFooter                                                       |
+------------------------------------------------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | SiteHeader | Top | see global chrome |
| 2 | HeroBanner | Below header | CMSBanner |
| 3 | PincodeStrip | Below hero | PincodeService, Cart.pincode |
| 4 | CategoryTiles | Three tiles | Product.category |
| 5 | MangoSeasonStrip | Mid page | MangoSeason (aggregate / featured variety) |
| 6 | FeaturedRow | Product cards | Product, Variant (default) |
| 7 | ProductCard | Inside FeaturedRow | Product, Variant |
| 8 | TrustStrip | Above footer | static copy |
| 9 | SiteFooter | Bottom | global chrome |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| title | CMSBanner | heading | yes | Display |
| subtitle | CMSBanner | subheading | no | Display |
| season_state | CMSBanner | badge: Live / Coming soon / Closed | yes | Enum |
| cta_label | CMSBanner | primary button | yes | |
| cta_url | CMSBanner | button href | yes | Internal path |
| image | CMSBanner | full-width image | yes | |
| pincode | Cart / PincodeService | text, 6 digit | no | Numeric, length 6 |
| city | PincodeService | text after check | — | Display if serviceable |
| delivery_days_min | PincodeService | text “2–4 days” | — | With max |
| delivery_days_max | PincodeService | text | — | |
| category | Product | tile label + image | yes | exotic / dry_fruit / mango |
| variety_name | MangoSeason | text | yes | On strip |
| harvest_start | MangoSeason | date text | yes | |
| harvest_end | MangoSeason | date text | yes | |
| status | MangoSeason | badge | yes | upcoming / live / closed |
| name | Product | card title | yes | |
| origin | Product | card caption | yes | |
| season_status | Product | badge | yes | Hide if in_season |
| images[0] | Product | card image | yes | |
| price | Variant | INR (default variant) | yes | “From ₹…” if multiple |
| pack_label | Variant | small text | yes | |

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| Hero CTA | CMSBanner.cta_label | C-05 or C-02 as configured |
| Category tile Exotic | Exotic fruits | C-02 `?category=exotic` |
| Category tile Dry | Dry fruits | C-02 `?category=dry_fruit` |
| Category tile Mango | Mangoes | C-05 |
| MangoSeasonStrip CTA (live) | Shop mangoes | C-05 |
| MangoSeasonStrip CTA (upcoming) | Pre-order / Notify me | C-06 |
| ProductCard | card click | C-04 `/p/{slug}` |
| Pincode Check | Check | Stay; update Cart.pincode |

---

## Empty / error / loading

- **No published banner:** skip HeroBanner; page starts at PincodeStrip (do not show a blank hero).
- **No featured products:** skip FeaturedRow.
- **Pincode invalid:** “Enter a valid 6-digit pincode.”
- **Pincode not serviceable:** message + link to C-21.
- **Loading:** skeleton for banner and four product cards.
