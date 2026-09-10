# C-11 Login

- **URL:** `/login` (optional `?next=`)
- **Entry:** AccountLink, checkout gate, C-12 link
- **Users:** Guest
- **Purpose:** Authenticate Customer.

Compact header: Logo only. Footer optional.

---

## ASCII wireframe

```
+------------------------------------------------------------------+
| Logo                                                             |
+------------------------------------------------------------------+
| LoginForm                                                        |
|   email                                                          |
|   password                                                       |
|   [ Log in ]                                                     |
| Link: Create account  ·  (forgot password: later)                |
+------------------------------------------------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | Logo | Top | — |
| 2 | LoginForm | Center | Customer |
| 3 | SubmitButton | Form | — |
| 4 | SignupLink | Below | — |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| email | Customer | email | yes | Valid email format |
| password | Customer | password | yes | Non-empty; do not echo |
| next | — | hidden query | no | Internal path only |

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| Log in | Log in | `next` or C-01 |
| Create account | Create account | C-12 (preserve next) |

---

## Empty / error / loading

- **Unknown email / wrong password:** “Email or password is incorrect.” (same message)
- **Already logged in:** redirect C-13 or next
- **Submit loading:** button disabled
