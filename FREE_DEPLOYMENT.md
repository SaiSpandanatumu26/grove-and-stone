# Grove & Stone — free website and Android deployment

Android/repository status updated 19 September 2026; database provisioning figures below record the initial 11 September deployment. **This is the current deployment plan**, replacing the paid Azure proposal and the original expiring Render database. The owner requested a free provider and authorized proceeding.

## Current status

- Source is in the owner's [public GitHub repository](https://github.com/SaiSpandanatumu26/grove-and-stone), made public at the owner's request. Render is connected to this repository. Environment secrets and dependencies are excluded from Git.
- Supabase PostgreSQL 17.6 initialized successfully: 22 application tables, all 22 with row-level security enabled. The automatic Data API is disabled.
- Initial deployment snapshot (11 September): sample catalog imported and verified: 19 products (8 mango varieties), 38 packs and 4 hero banners, plus 8 harvest entries and 3 sample delivery pincodes. At that initial check, cloud customer and order counts were both zero; these are not current live counts. No local demo login or order was uploaded.
- Render services are live: [website](https://grove-and-stone-web.onrender.com) and [API health](https://grove-and-stone.onrender.com/api/v1/health). DATABASE_URL and SECRET_KEY are stored privately in Render. CORS allows the website origin; the static site has its SPA rewrite. Do not create duplicate services from the old Blueprint draft.
- Expo CLI authentication and the signed Android APK 1.0.0 build completed on 18 September. Installation, startup, home and Cart navigation were checked in the Windows Android 11 emulator on 19 September. [Install on a phone](output/android/README.md) or [use the Windows launcher](output/android/windows/README.md). Physical-phone testing and Play publication remain.

The Supabase project is the owner's existing project in Sydney; Render's existing API region is Oregon. No paid Azure resources or Render database were created.

## Selected services

| Part | Provider | What it does |
| --- | --- | --- |
| Public website | Render Static Site | Hosts the exported Expo website with an HTTPS URL. |
| Flask API | Render Free Web Service | Handles accounts, products, cart, checkout and stock requests. |
| PostgreSQL | Supabase Free | Stores the database used by Flask. Existing shop login stays in Flask. |
| Android APK | Expo EAS Free allowance | Builds the installable app, pointing to the same Flask API. |
| Source repository | Your GitHub account | Supplies source code to Render; no paid repository plan is needed for this setup. |

```mermaid
flowchart TD
  Web[Website on Render Static Site] -->|HTTPS JSON| API[Flask on Render Free]
  Phone[Installed Android APK] -->|HTTPS JSON| API
  API -->|Encrypted PostgreSQL session connection| DB[(Supabase Free PostgreSQL)]
  Source[GitHub source] --> Web
  Source --> API
  Expo[Expo EAS build] --> Phone
```

Supabase is used as PostgreSQL hosting, not as a replacement for the app's login or REST routes. Your website and Android app share accounts, catalog, stock and orders through Flask. Neither client receives a database password or Supabase service-role key.

## What “free” means here

The selected base plans cost $0 within their included limits, subject to account eligibility and provider changes. No paid plan, add-on, subscription upgrade, paid build, custom domain, or payment-card enrollment is authorized by this setup. If a provider requires payment details or an upgrade, stop and review the account options rather than accepting it automatically.

- Render's free API sleeps after 15 minutes without incoming traffic and can take roughly a minute to wake. Its allowance is 750 free instance hours per workspace each month, shared with any other free services. Static-site hosting has included bandwidth/build limits. If payment details are already attached, check billing/spend settings before creating services: some overages can be billed. [Render Free](https://render.com/docs/free).
- Supabase Free includes a 500 MB database, two active projects, and 5 GB egress; inactive projects can pause after one week. This is a $0 plan rather than Render's 30-day PostgreSQL trial, but it is not an unlimited or guaranteed-permanent service. [Supabase pricing](https://supabase.com/pricing).
- Expo currently lists up to 15 Android builds in the Free allowance. Check your account's remaining quota before starting; wait for renewal rather than upgrading if it is exhausted. [Expo pricing](https://expo.dev/pricing).

The static website can load while the API wakes. The app first waits up to 90 seconds for the health endpoint, then loads the catalog. Ordinary requests retain their 15-second timeout. If waking still fails, use Try again; writes are never automatically repeated. Ordinary active shopping keeps the API in use; no artificial keep-alive system is configured. The database can also require resuming in Supabase after inactivity.

This is a project-review setup, not reliable always-on hosting for a busy shop. Keep separate database exports for anything valuable. Payment processor fees, SMS/email services, app-store enrollment, and a purchased domain are separate from hosting. Downloading/testing an APK does not require Google Play publication.

Vercel was not selected because its Hobby plan restricts usage to personal/non-commercial projects and this project is a fruit shop. [Vercel Hobby](https://vercel.com/docs/plans/hobby). The selected arrangement also keeps the existing Flask/PostgreSQL stack without converting it to a different serverless architecture.

## Deployment steps

### 1. Sign in

Use your own accounts at [Render](https://dashboard.render.com/), [Supabase](https://supabase.com/dashboard), [GitHub](https://github.com/), and [Expo](https://expo.dev/). Sign into the in-app browser used for this task. Enter passwords and verification codes on the provider pages, never in chat. A browser login does not automatically sign the local Git/EAS command-line tools in.

If you need to create an account, complete its verification and terms acceptance yourself. Select Free. Your earlier deployment approval remains valid; selecting this zero-cost setup does not require another general approval.

### 2. Create the database first

1. In Supabase create a **new dedicated project** named Grove & Stone under a Free organization. Choose a nearby region, ideally Singapore to match the Render API; check availability. Keep its strong database password privately in a password manager.
2. **Before creating application tables, open the project's Data API settings and turn Enable Data API OFF.** Our code uses Flask authorization and direct SQL; exposing those same tables through an automatic API would bypass that design. Do not re-enable it without implementing and testing appropriate grants/RLS. Supabase documents disabling the Data API when it is not used: [securing your API](https://supabase.com/docs/guides/api/securing-your-api).
3. In **Connect**, choose the **Session pooler** string on port **5432**. Copy the actual hostname and username from that project. Do not use the transaction pooler on 6543; session mode supports the existing driver's prepared statements and session behavior over IPv4. [Supabase connection guide](https://supabase.com/docs/guides/database/connecting-to-postgres).
4. Replace the password placeholder with a correctly URL-encoded password and append `?sslmode=require` if there are no existing query parameters. Enter this privately into Render's `DATABASE_URL` setting. A typical shape is `postgresql://postgres.PROJECT_REF:ENCODED_PASSWORD@POOLER_HOST:5432/postgres?sslmode=require`; the uppercase placeholders are not real values. For server-certificate validation, use the project's downloaded root certificate and `sslmode=verify-full`/`sslrootcert` settings.

No database URL, password, secret key, customer record, or database dump goes into GitHub or the mobile app. Keep Supabase Data API disabled throughout initialization, catalog setup, testing, and operation. Verify it remains disabled before sharing the public website.

### 3. Connect the source and deploy the API

Upload the contents of the extracted `Grove-and-Stone/` source folder to your GitHub repository. The Grove & Stone repository is public at the owner's request. `render.yaml` must be at the repository root. Retain `.gitignore`; exclude local environments, databases, dependencies, caches, and `.azure-build/`.

The current `render.yaml` defines two services and **no Render database**. It accepts Supabase's connection string rather than creating the expiring database. For a first deployment, create services individually in the following order so their generated URLs can be entered without guessing:

| API setting | Value |
| --- | --- |
| Type/runtime | Web Service / Python |
| Name | `grove-and-stone-api` (availability checked in your account) |
| Region / instance | Oregon / **Free** |
| Build command | `pip install -r requirements.txt` |
| Start command | `python -m flask --app backend init-db && gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 60` |
| Health-check path | `/api/v1/health` |
| Automatic deploys | Off |
| `PYTHON_VERSION` | `3.14.7` |
| `DATABASE_URL` | Private Supabase session-pooler connection string |
| `SECRET_KEY` | At least 32 random characters, generated once and retained privately |
| `SHIPPING_FEE` / `FREE_SHIPPING_THRESHOLD` | Review samples `49` / `999`; approve business values before real sales |
| `PAYMENT_BACKEND` / `CONTACT_BACKEND` | `disabled` / `disabled` |
| `RATELIMIT_STORAGE_URI` | `memory://` (single-process review configuration) |
| `PUBLIC_API_URL` | Actual generated HTTPS API origin, without `/api/v1` |
| `CORS_ORIGINS` | Actual website HTTPS origin once the static site exists |

You can use the Blueprint instead, but prompted URLs must be corrected to the actual generated services before rebuilding/testing. Do not guess that service names guarantee a particular domain. `WEB_DIST_DIR` is unnecessary here because the website is a separate static service.

After initialization, verify `/api/v1/health` and `/api/v1/products`. An empty products response is expected until the catalog has been populated. Verify the Supabase Data API cannot read the application's tables; authenticated Flask routes remain the only client entry point.

For an empty review database, `infra/supabase/schema.sql` contains the initial schema and enables row-level security in one transaction. `infra/supabase/sample-catalog.sql` contains only sample products, packs, banners, harvest windows and delivery coverage. Both were applied to this project's Supabase database on 11 September 2026. Do not rerun the initial schema on an initialized database. Do not upload a local database dump or run the local demo-account seeder remotely. Replace sample inventory, tax, delivery and season values with approved business data before real sales.

### 4. Deploy the website

Create a **Static Site** in Render from the same repository:

| Setting | Value |
| --- | --- |
| Name | `grove-and-stone-web` |
| Build command | `bash infra/render/build-web.sh` |
| Publish directory | `mobile/dist` |
| `NODE_VERSION` | `24.20.0` |
| `EXPO_PUBLIC_API_URL` | Actual API origin plus `/api/v1` |
| Rewrite | `/*` → `/index.html` (supports refreshing nested screens) |
| Automatic deploys | Off |

The build script rejects an invalid/non-HTTPS API URL, installs the locked dependencies, and exports the web app. It does not include secrets. Set the API's `CORS_ORIGINS` to this site's actual HTTPS origin, then test both URLs together. Changing `EXPO_PUBLIC_API_URL` requires rebuilding the website because Expo embeds it at build time.

The rewrite serves the app for nested screen links; it does not create public product URLs with server-side rendering. Unknown static paths may also return the app shell, as with common single-page hosting.

### 5. Populate review content and validate

Cloud deployment does not automatically copy local data. Create a private administrator using the backend CLI through an authorized database connection, then populate the approved products, variants, banners, seasons and coverage through the existing staff API. Do not publish the local demo account/password or upload local orders/addresses. The existing local demo-seed guard stays in place.

Keep sample content labeled as a preview. Check catalog images, hero slides, account creation/login, wishlist, cart quantities/GST, pincode rules, live stock checks, waitlist and checkout. Online payments/contact remain disabled until configured and verified; COD order-taking still needs an approved review/fulfillment decision. Free hosting alone does not activate gateways, email/SMS alerts, couriers, or reliable refund/push workers.

### 6. Build the Android APK

From `mobile/`, sign into Expo CLI, retain the current project or link it with `eas init`, and create/update the **preview** environment variable `EXPO_PUBLIC_API_URL` with the same public Flask API URL. It is a public URL, not a secret.

```powershell
npx.cmd eas-cli@latest login
npx.cmd eas-cli@latest whoami
npx.cmd eas-cli@latest init
npx.cmd eas-cli@latest env:create --environment preview --name EXPO_PUBLIC_API_URL --value 'https://ACTUAL_API_HOST/api/v1' --visibility plaintext
npx.cmd eas-cli@latest build --platform android --profile preview
```

Replace the example URL. If the variable exists, update it in Expo instead of creating a duplicate. Check free build availability and decline upgrades. Download the resulting APK to an Android phone and test it against the shared cloud backend. The existing `preview` profile produces an APK; `production` produces a store-oriented AAB. Neither command publishes an app to Google Play automatically.

## Current verification and remaining work

The previous application verification passed 41 backend tests, TypeScript checking and Android/web export checks. This change updates hosting configuration and documentation; remote Render/Supabase connectivity, hosted website behavior, cloud catalog population and a signed physical-device build still need verification. See [BEGINNER_GUIDE.md](BEGINNER_GUIDE.md) for the shopping flow and [CATALOG_REVIEW.md](CATALOG_REVIEW.md) for feature tests.

The Azure deployment guide and infrastructure files have been removed. Use this guide for the current Render + Supabase deployment; the original Render database instructions are historical and should not be used for this setup.
