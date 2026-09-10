# AN-02 Onboarding

- **Platform:** Android only (first launch)
- **Entry:** AN-01 when `onboarding_done` is false
- **Users:** Guest
- **Purpose:** Explain three shop lines and capture pincode early.

---

## ASCII wireframe

```
+---------------------------+
| Skip                      |
| [ Card image ]            |
| Title                     |
| Body                      |
| PageDots  1 2 3           |
| PincodeField (page 3)     |
| [ Next ] / [ Start shopping ]
+---------------------------+
```

---

## Wireframe objects

| # | Object | Position | Binds to |
| --- | --- | --- | --- |
| 1 | SkipLink | Top right | — |
| 2 | OnboardingCard | Center | static (3 pages) |
| 3 | PageDots | Below card | page index |
| 4 | PincodeField | Page 3 | Cart.pincode / PincodeService |
| 5 | PrimaryButton | Bottom | — |

---

## Fields

| Field | Object | Control | Required | Validation |
| --- | --- | --- | --- | --- |
| page_title | static | text | yes | Page1 Exotic & dry fruits; Page2 Mango season; Page3 Delivery pincode |
| page_body | static | text | yes | |
| pincode | PincodeService | 6-digit | no | If filled: numeric length 6; invalid shows error but Start still allowed |
| onboarding_done | local flag | hidden | yes | Set true on Skip or Start |

---

## Actions

| Control | Label | Goes to |
| --- | --- | --- |
| Skip | Skip | Home (C-01); flag true |
| Next | Next | Next card |
| Start shopping | Start shopping | Home; save pincode if valid |

---

## Empty / error / loading

- **Invalid pincode:** “Enter a valid 6-digit pincode or skip.”
- **Not serviceable:** save anyway, later C-21 when they add mangoes.
