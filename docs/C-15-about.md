# C-15 About

- **URL:** `/about`
- **Entry:** Footer
- **Users:** Guest, Customer
- **Purpose:** Explain Grove & Stone, farm/natural mango positioning (factual, no false claims).

---

## ASCII wireframe

```
+------------------------------------------------------------------+
| SiteHeader                                                       |
+------------------------------------------------------------------+
| PageTitle                                                        |
| BodyCopy (who we are, three lines, mango season)                 |
| OriginNote                                                       |
| SiteFooter                                                       |
+------------------------------------------------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | PageTitle | Top | static |
| 2 | BodyCopy | Main | CMS or static |
| 3 | OriginNote | Below | static |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| page_title | — (CMS/static) | H1 | yes | “About Grove & Stone” |
| body | — | rich text | yes | Must not claim certifications not held |
| origin_note | — | text | no | How mango origin is described |

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| Shop mangoes | Shop mango season | C-05 |

---

## Empty / error / loading

- **Missing CMS body:** show default static paragraphs (never a blank page).
