# C-12 Sign up

- **URL:** `/signup`
- **Entry:** C-11 Create account
- **Users:** Guest
- **Purpose:** Create Customer account.

---

## ASCII wireframe

```
+------------------------------------------------------------------+
| Logo                                                             |
+------------------------------------------------------------------+
| SignupForm                                                       |
|   full_name                                                      |
|   email                                                          |
|   phone                                                          |
|   password                                                       |
|   [ Create account ]                                             |
| Link: Log in                                                     |
+------------------------------------------------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | Logo | Top | — |
| 2 | SignupForm | Center | Customer |
| 3 | SubmitButton | Form | — |
| 4 | LoginLink | Below | — |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| full_name | Customer | text | yes | 2–80 chars |
| email | Customer | email | yes | Unique; valid email |
| phone | Customer | 10-digit | yes | Unique Indian mobile |
| password | Customer | password | yes | Min 8 chars |

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| Create account | Create account | C-01 or `next` (logged in) |
| Log in | Log in | C-11 |

---

## Empty / error / loading

- **Email taken:** “An account with this email already exists.”
- **Phone taken:** “This mobile is already registered.”
- **Weak password:** “Use at least 8 characters.”
- **Loading:** button disabled
