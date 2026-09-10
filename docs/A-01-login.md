# A-01 Admin login

- **URL:** `/admin/login`
- **Entry:** Direct URL, session expired
- **Users:** AdminUser (unauthenticated)
- **Purpose:** Authenticate staff. Separate from customer login.

No SiteHeader. Admin brand bar only.

---

## ASCII wireframe

```
+------------------------------------------------------------------+
| “Grove & Stone admin”                                            |
| AdminLoginForm                                                   |
|   email                                                          |
|   password                                                       |
|   [ Sign in ]                                                    |
+------------------------------------------------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | AdminBrand | Top | — |
| 2 | AdminLoginForm | Center | AdminUser |
| 3 | SubmitButton | Form | — |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| email | AdminUser | email | yes | Valid email |
| password | AdminUser | password | yes | Non-empty |

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| Sign in | Sign in | A-02 if is_active |

---

## Empty / error / loading

- **Wrong credentials / inactive:** “Cannot sign in.” (same message)
- **Already signed in:** A-02
- **Customer session does not grant admin**
- **Loading:** button disabled
