# Grove & Stone — mobile foundation review

> Historical checkpoint. The latest implementation and verification are in `STOREFRONT_REVIEW.md`.

The API stage is approved. Stage 2 / Prompt 3 now adds the Expo project under mobile/ using a blank TypeScript template and React Navigation.

| Document requirement | Current implementation |
| --- | --- |
| ANDROID / AN-03: four destinations | Home, Mangoes, Cart, Account, in that order |
| App chrome replaces website chrome | App toolbar and bottom navigation; no SiteHeader/SiteFooter |
| Search toolbar action | Opens a Search placeholder inside the current tab stack |
| Pincode chip | Opens an accessible dialog; six-digit format validation |
| Cart badge | Sum of supplied CartLine quantities; hidden at zero |
| Account while logged out | Login placeholder |
| Back behavior | Native stack first, then previous tab history; Home is initial root |
| Android platform | Portrait; minimum API 26; optional browser preview for local review |
| Accessibility | Labeled buttons/inputs, readable colors, 48px minimum action targets |

Code shares the tab/stack layout and placeholder rendering. Only the used Ionicons font is imported directly. The generated package lock records installed dependency versions.

## Scope

This is the requested navigation checkpoint, not the full shopping app. Search/pincode are local placeholder interactions. No catalog results, stock, coverage or payment outcomes are fabricated. Login forms, API integration, saved session/pincode, onboarding/splash behavior, offline caching, push registration and verified deep links remain for integration. The documents continue to govern these later features.

## Verification

- TypeScript compilation passes.
- Local browser preview renders the four tabs successfully at http://127.0.0.1:8081; the Flask catalog endpoint responds successfully on port 5000. Shopping screens are not connected yet.
- Android Metro/Hermes bundle export passes.
- Expo Doctor passes all 21 checks after adding the required expo-font peer dependency.
- No Android device/emulator was available, so native rendering, hardware back and installation have not been device-tested. This archive is source, not an APK.
- npm audit reports 17 moderate transitive dependency advisories. Available automatic fixes include incompatible Expo/React Navigation downgrades or no fix. No forced downgrade or unverified override was applied. Resolve compatible upstream fixes before release; the app remains local and undeployed.

The previously verified backend remains included: 23 Python tests and 54 PostgreSQL schema checks passed in its stage. No backend behavior was changed for this navigation work.

Grove-and-Stone.zip contains the current backend, mobile source, lockfiles, tests and documentation. It excludes dependency folders, local databases, caches, credentials and build intermediates.

Paused for the requested mobile-navigation review before full shopping integration. Deployment still requires your explicit approval.
