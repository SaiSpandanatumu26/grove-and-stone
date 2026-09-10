# C-04 Product detail

- **URL:** `/p/{slug}`
- **Entry:** ProductCard, search, mango hub
- **Users:** Guest, Customer
- **Purpose:** Choose pack, understand origin/ripeness/shipping, add to cart.

---

## ASCII wireframe

```
+------------------------------------------------------------------+
| SiteHeader                                                       |
+------------------------------------------------------------------+
| ImageGallery          | Title, origin, season badge              |
| (main + thumbs)       | VariantSelector (pack radios)            |
|                       | PriceBlock  GST note                     |
|                       | QtyStepper                               |
|                       | PincodeCheck  delivery days / mango flag |
|                       | [ Add to cart ]  [ Buy now ]             |
|                       | COD note if Variant.cod_allowed = false  |
+------------------------------------------------------------------+
| OriginBlock | RipenessNote | HandlingNotes | FarmStory           |
| RelatedRow (same category)                                       |
| SiteFooter                                                       |
+------------------------------------------------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | ImageGallery | Left | Product.images |
| 2 | TitleBlock | Right top | Product |
| 3 | VariantSelector | Right | Variant list |
| 4 | PriceBlock | Right | selected Variant |
| 5 | QtyStepper | Right | CartLine.qty (pending) |
| 6 | PincodeCheck | Right | PincodeService |
| 7 | AddToCartButton | Right | Cart, CartLine |
| 8 | BuyNowButton | Right | Cart then C-08 |
| 9 | OriginBlock | Below | Product.origin, farm_story |
| 10 | RipenessNote | Below | Product.ripeness_note |
| 11 | HandlingNotes | Below | Product.handling_notes |
| 12 | RelatedRow | Bottom | other Product in category |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| name | Product | H1 | yes | |
| slug | Product | URL | yes | 404 if missing / inactive |
| origin | Product | text | yes | |
| category | Product | breadcrumb | yes | |
| season_status | Product | badge | yes | If `off_season` / `coming_soon`, hide Add, show Notify → C-06 |
| images | Product | gallery | yes | Click thumb → main |
| long_description | Product | body text | yes | |
| farm_story | Product | paragraph | no | Hide object if empty |
| handling_notes | Product | paragraph | no | Hide if empty |
| ripeness_note | Product | callout | no | Mango category; hide if empty |
| harvest_window | Product | text | no | Mangoes |
| pack_label | Variant | radio / chips | yes | One selected; default is_default |
| pack_type | Variant | display | yes | |
| price | Variant | INR large | yes | Updates on pack change |
| gst_percent | Variant | “Incl. {n}% GST” | yes | |
| stock_qty | Variant | “In stock” / “Sold out” | yes | Add disabled if 0 |
| sku | Variant | small text | yes | Display |
| cod_allowed | Variant | warning if false | yes | “COD not available for this box” |
| qty | CartLine | stepper 1–20 | yes | Default 1; cannot exceed stock_qty |
| pincode | PincodeService | 6-digit | no | If mango and mango_eligible=false, block add with message |

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| Add to cart | Add to cart | Stay; MiniCart or toast; line written |
| Buy now | Buy now | C-08 (cart = this line) |
| Notify me | Notify me | C-06 when not purchasable |
| Related card | — | C-04 other slug |
| Breadcrumb category | category name | C-02 or C-05 for mango |

---

## Empty / error / loading

- **Inactive / unknown slug:** C-20.
- **Sold out selected pack:** Add disabled; other packs still selectable.
- **Pincode mango not eligible:** “We cannot dispatch mangoes to this pincode.” Link C-21.
- **Add without pincode (mango/exotic perishable):** allow add, but Checkout will require pincode.
- **Loading:** image and title skeletons.
