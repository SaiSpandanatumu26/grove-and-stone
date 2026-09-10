# C-18 Contact

- **URL:** `/contact`
- **Entry:** Footer, C-10 Help
- **Users:** Guest, Customer
- **Purpose:** Let a shopper send a message; show support email and phone.

---

## ASCII wireframe

```
+------------------------------------------------------------------+
| SiteHeader                                                       |
+------------------------------------------------------------------+
| PageTitle                                                        |
| SupportDetails  email · phone                                    |
| ContactForm                                                      |
|   full_name, email, phone, order_number (optional), message      |
|   [ Send ]                                                       |
| SiteFooter                                                       |
+------------------------------------------------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | SupportDetails | Top | config |
| 2 | ContactForm | Main | (ticket; not in object dictionary — fields below) |

Contact ticket is form-only for MVP (email to support). Not a stored Order object.

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| support_email | config | mailto | yes | Display |
| support_phone | config | tel | yes | Display |
| full_name | Customer if logged in else form | text | yes | 2–80; pre-fill if logged in |
| email | Customer / form | email | yes | Valid email |
| phone | form | 10-digit | no | If present, 10 digits |
| order_number | Order (optional ref) | text | no | If filled, format like GS-##### |
| message | form | textarea | yes | 10–1000 chars |

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| Send | Send | Stay; success “We’ll reply by email.” |

---

## Empty / error / loading

- **Send fail:** “Could not send. Email us at {support_email}.”
- **Loading:** button disabled
