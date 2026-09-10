# AN-05 Notifications

- **Platform:** Android
- **Entry:** Push tray tap, or Account → Notifications (optional inbox)
- **Users:** Customer
- **Purpose:** List in-app notification history (MVP: last 50) and open the right screen.

OS push still works if this inbox is empty (server may not persist). MVP inbox is nice-to-have; **Must** is FCM display + tap target.

---

## ASCII wireframe

```
+---------------------------+
| Toolbar: Notifications    |
| NotificationRow           |
|  title, body, time, unread|
| …                         |
+---------------------------+
| BottomNav                 |
+---------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | NotificationList | Main | PushMessage[] |
| 2 | NotificationRow | Row | PushMessage |
| 3 | EmptyInbox | Replaces list | — |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| title | PushMessage | text | yes | e.g. “Order GS-10482 shipped” |
| body | PushMessage | text | yes | |
| created_at | PushMessage | relative time | yes | |
| is_read | PushMessage | unread dot | yes | |
| type | PushMessage | hidden | yes | `order` / `mango_season` |
| order_number | PushMessage | hidden | if type=order | Deep link C-10 |
| product_slug | PushMessage | hidden | if mango | Deep link C-05 or C-04 |

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| Row order | — | C-10 |
| Row mango | — | C-05 |
| System tray tap | — | Same as row type |

---

## Empty / error / loading

- **Empty:** “No notifications yet. We’ll tell you when an order ships or mango season opens.”
- **Logged out:** do not show inbox; pushes not registered.
- **Loading:** row skeletons.
