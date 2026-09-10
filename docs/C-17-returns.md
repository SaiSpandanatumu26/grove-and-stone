# C-17 Returns

- **URL:** `/returns`
- **Entry:** Footer
- **Users:** Guest, Customer
- **Purpose:** State perishable vs dry-fruit return rules (mangoes generally non-returnable except quality issue).

---

## ASCII wireframe

```
+------------------------------------------------------------------+
| SiteHeader                                                       |
+------------------------------------------------------------------+
| PageTitle                                                        |
| PolicyCopy                                                       |
| ContactCta                                                       |
| SiteFooter                                                       |
+------------------------------------------------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | PageTitle | Top | static |
| 2 | PolicyCopy | Main | static |
| 3 | ContactCta | Bottom | — |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| page_title | — | H1 | yes | |
| policy_body | — | rich text | yes | Must cover: mango/exotic perishable, dry fruit sealed packs, photo evidence window |

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| Contact | Contact us | C-18 |

---

## Empty / error / loading

- Always show default policy if CMS empty.
