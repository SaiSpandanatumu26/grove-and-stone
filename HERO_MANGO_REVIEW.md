# Grove & Stone — hero and mango update

Updated 11 September 2026.

## What changed

The catalog now has **19 products and 38 packs**, including **8 mango varieties**: Alphonso, Kesar, Langra, Dasheri, Banganapalli, Totapuri, Chausa and Neelum. Each mango has boxes of 6 and 12. The four new varieties are marked upcoming, have zero sample stock, and open the existing waitlist instead of allowing unavailable purchases. Existing stock, prices, customer records and orders are preserved by repeated seeding.

The new variety names and regional examples were checked against [APEDA's mango variety information](https://farmerconnect.apeda.gov.in/Home/Seasonfavorites?CropID=9). All catalog origins, prices, inventory and harvest windows remain illustrative review data. Mango pictures use the existing generated illustration, not a photograph identifying each cultivar.

The redesigned hero keeps the Foodwagon-inspired yellow and orange palette. Dark headlines improve readability; an arched fruit image, floating mango collection card and decorative badge give the promotion more depth. Four published banners include the new mango slide. Content still comes from the Flask banner endpoint, so future promotions can use the existing CMS data model.

| Control | Behaviour |
| --- | --- |
| Main promotion button | Opens the mango hub for mango content, or filters and scrolls to the featured collection. |
| Browse all fruits | Resets the catalog to all products and scrolls to it. |
| Mango collection card | Displays the actual catalog variety count and opens the mango hub. |
| Slide dots / previous / next | Select a slide and pause automatic rotation. |
| Play / pause | Starts or stops the 6.5-second rotation and floating image motion. Automatic motion stays off when reduced motion is enabled. |
| Progress line | Shows the current automatic slide interval. |
| Collection shortcuts | Open the mango hub or filter the exotic/dry-fruit catalog. |

Animations stop when the app is backgrounded or Home loses focus. The layout stacks for narrow screens, and slideshow controls wrap to avoid horizontal overflow.

## Validation

- All **41 backend tests passed**, including repeatable catalog seeding, preservation of existing stock, valid mango packs and waitlist regressions. The existing Firebase token deprecation remains a warning.
- TypeScript checking and production web/Android exports passed (942 KB web bundle, 2.1 MB Android bundle). The Android export validates bundling; it is not a signed APK or a physical-device test.
- Browser checks passed for manual slide changes, mango collection navigation, the new Banganapalli waitlist form and dry-fruit filtering (3 products).
- Desktop composition reviewed; at a 320-pixel viewport there was no horizontal document overflow and hero controls stayed within the viewport.
- Supabase import succeeded and returned **19 products, 8 mangoes, 38 packs, 4 banners**. It inserted only catalog records and did not reset stock or upload local demo accounts.

## Deployment status

The source repository remains private. The updated local website runs at [localhost:8081](http://localhost:8081/) while its local servers are running. Render's deployment form still needs the owner's private Supabase session-pooler connection string in `DATABASE_URL`. The correct connection option is open in Supabase. No public website link or signed Android APK exists yet; share a public link only after successful deployment and hosted checks. Expo CLI sign-in is also still needed for a signed APK.

See [FREE_DEPLOYMENT.md](FREE_DEPLOYMENT.md) for current hosting instructions and limitations.
