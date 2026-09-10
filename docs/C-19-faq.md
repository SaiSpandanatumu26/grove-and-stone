# C-19 FAQ

- **URL:** `/faq`
- **Entry:** Footer
- **Users:** Guest, Customer
- **Purpose:** Answer mango season, pincode, COD, ripeness, dry-fruit storage.

---

## ASCII wireframe

```
+------------------------------------------------------------------+
| SiteHeader                                                       |
+------------------------------------------------------------------+
| PageTitle                                                        |
| FaqSearch  [ query ]                                             |
| FaqList  accordion items                                         |
| SiteFooter                                                       |
+------------------------------------------------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | PageTitle | Top | static |
| 2 | FaqSearch | Below | local filter |
| 3 | FaqList | Main | static Q&A |
| 4 | FaqItem | Accordion | static |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| faq_query | — | text | no | Filter questions client-side |
| question | — | accordion header | yes | |
| answer | — | accordion body | yes | |

MVP FAQ topics (content, not extra objects): mango harvest window, pre-order vs waitlist, pincode, COD on mango boxes, ripeness at delivery, dry fruit shelf life, GST invoice.

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| Accordion | Expand | Stay |
| Still need help | Contact | C-18 |

---

## Empty / error / loading

- **No FAQ match:** “No matching questions.” Link C-18.
