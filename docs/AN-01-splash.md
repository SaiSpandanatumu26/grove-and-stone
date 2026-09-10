# AN-01 Splash

- **Platform:** Android only
- **Entry:** App process start (cold/warm)
- **Users:** Guest, Customer
- **Purpose:** Brand flash while session and config load; then route.

---

## ASCII wireframe

```
+---------------------------+
|                           |
|        Logo               |
|        Grove & Stone      |
|        (spinner)          |
|                           |
+---------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | AppLogo | Center | — |
| 2 | LoadingIndicator | Below logo | — |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| — | — | none | — | No user input. Max display 2s or until config returns, whichever first (cap 5s). |

---

## Actions

| Condition | Goes to |
| --- | --- |
| First launch (no onboarding_done flag) | AN-02 |
| Else | Home (C-01 layout in app) |

---

## Empty / error / loading

- **No network after 5s:** still open Home with offline banner (FR-A08).
- **Force-update flag from config:** full-screen “Update required” + Play Store link (no skip if `force=true`).
