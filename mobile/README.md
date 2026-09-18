# Grove & Stone — Expo storefront

Android app and responsive browser preview, following ANDROID.md and AN-03. Start Flask using the root README, then use these commands in this folder.

```powershell
npm.cmd ci
npm.cmd run typecheck
npm.cmd start
# Browser preview for local review:
npm.cmd run web
# Local native build (requires Android SDK and Java):
npm.cmd run android
# Generate the Android JavaScript bundle locally:
npm.cmd run export:android
```

Use Node.js 22.13+; this project was checked with Node.js 24.20.0. Expo SDK 57 targets React Native 0.86. The Android minimum is explicitly set to API 26, matching the documents. No EAS or hosting deployment is needed for these local commands.

Home, Mangoes, Cart and Account now connect to Flask. Each tab has its own native stack. Search and product details open within it. Account supports signup/login, profile, wishlist, previous orders and reorder. The cart badge sums actual quantities and hides zero.

Pincode and search controls validate input and call the API. Guest identifiers persist in AsyncStorage; native authentication tokens use SecureStore, while browser authentication uses sessionStorage. Passwords are never persisted. Customer carts and wishlists live in PostgreSQL; guest carts merge at signup/login. Access tokens refresh and logout revokes the server session.

The browser preview opens at http://localhost:8081 and defaults to the same hostname on port 5000 for Flask. Android defaults to the emulator's host address, 10.0.2.2:5000. For a physical phone, set `EXPO_PUBLIC_API_URL` to your computer's LAN API address before starting Expo, bind Flask to that LAN interface, and connect both devices to the same network. Keep browser origins in Flask's CORS configuration.

```powershell
$env:EXPO_PUBLIC_API_URL = 'http://YOUR_COMPUTER_LAN_IP:5000/api/v1'
npm.cmd start
```

Optimized catalog images are bundled with the Android app and exported as static assets for the website. Tiny Base64 previews render while needed; remote Android images use disk/memory caching. See [Android and performance](../ANDROID_AND_PERFORMANCE.md) for APK builds, architecture and measurements. Browser review does not verify native Android behavior.

See the project-root STOREFRONT_REVIEW.md for test accounts, validation and remaining work. Checkout, delivery, local demo payments, tracking, cancellation and support pages are implemented; see CHECKOUT_REVIEW.md and DEPLOYMENT.md in the project root. Live provider and physical-device testing remain. [Download the signed Android APK separately](../output/android/README.md).
