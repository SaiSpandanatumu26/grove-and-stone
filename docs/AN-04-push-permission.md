# AN-04 Push permission

- **Platform:** Android 13+ runtime permission; older: app settings / default granted
- **Entry:** After successful C-12 signup, C-11 login, or first C-09 confirmation — whichever comes first; once per install unless denied
- **Users:** Customer
- **Purpose:** Ask for notifications for order tracking and mango season.

---

## ASCII wireframe

```
+---------------------------+
| Title: Stay updated       |
| Body: Order packed/shipped
|        and mango season   |
| [ Enable notifications ]  |
| [ Not now ]               |
+---------------------------+
```

System permission dialog follows Enable.

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | PermissionCopy | Center | static |
| 2 | EnableButton | Bottom | OS permission |
| 3 | SkipButton | Text button | — |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| fcm_token | DeviceToken | hidden | yes after grant | Register to backend with Customer.id |
| notifications_enabled | DeviceToken | — | yes | true if granted |

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| Enable notifications | Enable notifications | OS sheet; then previous screen |
| Not now | Not now | Dismiss; do not ask again until Settings in Account |

Account (C-13) later: “Notifications” row opens system app settings.

---

## Empty / error / loading

- **Denied:** stay in app; no crash. Token not sent.
- **Already granted:** skip this screen.
