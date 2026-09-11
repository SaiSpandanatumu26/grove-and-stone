# Grove & Stone

**Live website: [grove-and-stone-web.onrender.com](https://grove-and-stone-web.onrender.com).** The Flask API runs on Render Free and uses Supabase Free PostgreSQL. The source repository is private. Read [FREE_DEPLOYMENT.md](FREE_DEPLOYMENT.md) for operations and limitations. The Android source exports successfully; a signed APK remains to be built with Expo EAS.

Latest validation: **41 backend tests passed** after adding optional website hosting. The Azure Bicep template compiles, the Expo web export builds, and its HTML/JavaScript/nested routes were verified through Flask. Earlier test counts below are historical.

**New to this project? Start with [the beginner guide](BEGINNER_GUIDE.md).** It explains every main website screen/control, the complete shopping flow, each technology and code file, all 22 database models, API requests, local setup, troubleshooting, and deployment. No programming background is assumed. Flow diagrams show how the parts connect.

Open [the local website](http://localhost:8081/) while its servers are running. Latest additions and test evidence: [CATALOG_REVIEW.md](CATALOG_REVIEW.md). Developer commands are below and in [DEVELOPMENT.md](DEVELOPMENT.md).

India-focused fruit commerce: exotic fruits, dry fruits, and seasonal mangoes. Flask/PostgreSQL provide the shared backend; the Expo Android app uses JSON REST APIs.

**The storefront is ready for local review.** Open http://localhost:8081/ while the local servers are running. The Foodwagon-inspired Expo app now connects catalog, pack selection, cart, signup/login, profile, wishlist and reorder to Flask. See `STOREFRONT_REVIEW.md` for the demo account, sample pincodes and validation. The documents govern business rules; the latest wishlist, reorder and carousel requests are explicit extensions.

The complete source and artwork package is **Grove-and-Stone.zip**. Extract it and start Flask below. For the browser preview, open a second terminal in `mobile/`, run `npm.cmd ci`, then `npm.cmd run web`, and visit http://localhost:8081/. See `mobile/README.md` for Android commands. Checkout, delivery selection, demo payments, tracking, cancellation and support pages are now available. See `CHECKOUT_REVIEW.md` and `DEPLOYMENT.md`.

## Local setup (PowerShell)

Run from this `grove-and-stone` folder. Verified on Python 3.14.7 and PostgreSQL 18.4.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r backend/requirements-dev.txt
createuser -U postgres --pwprompt grove_stone
createdb -U postgres --owner=grove_stone grove_stone
$env:DATABASE_URL = 'postgresql+psycopg://grove_stone:YOUR_URL_ENCODED_PASSWORD@localhost:5432/grove_stone'
$env:SECRET_KEY = .venv/Scripts/python.exe -c "import secrets; print(secrets.token_hex(32))"
$env:CORS_ORIGINS = 'http://localhost:8081,http://127.0.0.1:8081'
.venv/Scripts/python.exe -m flask --app backend init-db
.venv/Scripts/python.exe -m flask --app backend create-admin
.venv/Scripts/python.exe -m flask --app backend run
```

Retain the generated secret securely for subsequent starts; changing it invalidates access tokens. `.env.example` is a template, not automatically loaded. The local development server uses port 5000 and the API prefix is `/api/v1`.

`init-db` creates missing schema objects, including wishlist, checkout, reservation, refund and authentication/push infrastructure tables on earlier databases. It does not alter existing columns. Future alterations require versioned migrations that include the explicit DDL in `schema_invariants.py`.

For optional sample data, use a separate loopback PostgreSQL database named `grove_stone_local`, set `DATABASE_URL` accordingly, then run `.venv/Scripts/python.exe -m backend.demo_seed --confirm-local-demo`. This preserves existing records and adds review catalog data, banners, coverage and a synthetic past order. It never sends notifications or processes payments. Test account details are in `STOREFRONT_REVIEW.md`.

## Tests

```powershell
# API tests skip unless a disposable test database is configured.
.venv/Scripts/python.exe -m pytest backend/tests -q
.venv/Scripts/python.exe -m flask --app backend export-schema backend/schema.sql

# Tests TRUNCATE this database: keep it separate from application data.
createdb -U postgres grove_stone_test
$env:TEST_DATABASE_URL = 'postgresql+psycopg://postgres:YOUR_URL_ENCODED_PASSWORD@localhost:5432/grove_stone_test'
.venv/Scripts/python.exe -m pip install -r backend/requirements-fcm.txt
.venv/Scripts/python.exe -m pytest backend/tests -q

# Optional standalone SQL harness; Node is only required for this.
Set-Location backend/tests
npm.cmd ci
npm.cmd test
```

Results: **41 Python tests passed**, including native PostgreSQL API integration, simultaneous cart additions, repeatable catalog expansion, concurrent waitlist submissions and optional website serving; **57 standalone schema checks passed previously**. Firebase payload construction is tested with its network send mocked. Real-device delivery and payment processing have not been exercised.

## Push delivery

Notification jobs are stored in the same transaction as their triggering order/campaign change. Tests use an isolated mock log; runtime delivery uses Firebase Admin, as required by the documents.

Install `backend/requirements-fcm.txt`, configure `GOOGLE_APPLICATION_CREDENTIALS`, and run `flask --app backend dispatch-push` when ready to send queued notifications. No credentials were loaded and no real notifications were sent during implementation. Worker hosting/scheduling belongs to deployment preparation.

## Remaining checkpoints

1. Review the running storefront and account/cart flows described in `STOREFRONT_REVIEW.md`. Device testing and existing upstream dependency advisories remain outstanding.
2. Review the completed checkout and support flows in `CHECKOUT_REVIEW.md`; approve shipping charges and policy values.
3. Deployment is approved and GitHub/Render are connected. Enter the Supabase session-pooler connection string privately in Render to continue the steps in `FREE_DEPLOYMENT.md`. Live gateway/email/device tests still need credentials.

The cloud database, public website and API are live. The signed Android build remains pending. The customer storefront is implemented; a separate visual admin website remains outstanding.

References: [Flask factories](https://flask.palletsprojects.com/en/stable/patterns/appfactories/), [SQLAlchemy PostgreSQL](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html), [Firebase Admin](https://firebase.google.com/docs/cloud-messaging/send/admin-sdk), [PGlite](https://pglite.dev/docs/).


## Local checkout configuration

For the loopback `grove_stone_local` demo database, set these before starting Flask:

```powershell
$env:PAYMENT_BACKEND = 'demo'
$env:CONTACT_BACKEND = 'demo'
$env:SHIPPING_FEE = '49'
$env:FREE_SHIPPING_THRESHOLD = '999'
```

Demo modes are rejected for remote or non-`_local` databases. Production defaults disable online payments/contact until configured. Delivery pricing must be supplied for checkout. See `FREE_DEPLOYMENT.md` for the current deployment steps.

## Live stock availability

Stock is checked automatically every five seconds on visible product lists and product pages, and for items in the cart. Low-stock/sold-out labels, selected pack counts and cart/checkout controls update without reloading. Checks pause while the app is backgrounded, resume immediately on return, and retry connection failures with a clear stale-stock message. See `REALTIME_STOCK_REVIEW.md`.

## Expanded catalog and mango waitlist

The documents allow additional products within the three catalog categories. The local seed now provides 19 products (8 exotic fruits, 3 dry fruits, 8 mango varieties), each with two packs. Mangoes use boxes of 6 or 12. Upcoming varieties remain visible with a working email/mobile waitlist; repeat submissions succeed without duplicate records or exposing contact details. Sample origins, prices, GST, inventory and harvest windows are review data, not live supplier information. See `CATALOG_REVIEW.md` for the latest checks.

## Latest hero and mango update

The homepage now has a redesigned four-slide hero, motion-aware animation, previous/next and pause controls, collection shortcuts and an eight-variety mango feature. Added Banganapalli, Totapuri, Chausa and Neelum; new varieties are upcoming with waitlists and sample prices. See [HERO_MANGO_REVIEW.md](HERO_MANGO_REVIEW.md) for validation and deployment status.
