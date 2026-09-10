# Grove & Stone — deployment review

**Historical instructions:** the current request is free hosting for both website and Android, using Render + Supabase + Expo. Follow [FREE_DEPLOYMENT.md](FREE_DEPLOYMENT.md). The current `render.yaml` has been updated to that setup and no longer creates the Render database described below. No Render resources were created by these earlier instructions.

Updated 9 September 2026. Render YAML has passed the official Render JSON schema; the Android bundle and TypeScript checks pass locally. **The owner approved proceeding to deployment. Nothing has been deployed or submitted to EAS yet:** Render, GitHub and Expo currently show sign-in pages. Provider sign-in and repository/account selection remain necessary; no further general deployment approval is requested.

## What is prepared

- `render.yaml`: one Flask web service and one PostgreSQL database, both `plan: free`, in Singapore. Automatic code deployments are disabled.
- `requirements.txt` and `wsgi.py`: pinned Python dependencies and Gunicorn entry point. The single worker uses four threads. Initial schema creation runs before serving traffic, under a PostgreSQL transaction/advisory lock.
- `mobile/eas.json`: internal preview APK and production Android App Bundle, using the medium build resource class. EAS account quotas determine free usage; there is no `freeTier` JSON switch.
- Online payment and contact delivery default to disabled. No demo customer, sample catalog, credentials, or database is imported automatically.

Render's free web service sleeps after 15 idle minutes and can take about a minute to wake. Its free PostgreSQL database has 1 GB storage, **expires after 30 days**, and has no managed backups. It is suitable for a temporary review, not a lasting commerce database. Only one free PostgreSQL database is allowed per workspace. Free services also have usage limits, and SMTP ports are blocked. See [Render free instances](https://render.com/docs/free). Check the account's current included usage before deploying.

## 1. Prepare the repository

Extract `Grove-and-Stone.zip`. Work from the extracted project root. Install Git and the official [Render CLI](https://render.com/docs/cli); put `render.exe` on PATH on Windows.

```powershell
Set-Location 'C:/path/to/Grove-and-Stone'
git init
git add .
git diff --cached --stat
git commit -m 'Prepare Grove and Stone review build'
git branch -M main
$repositoryUrl = Read-Host 'Paste the URL of your empty private Git repository'
git remote add origin $repositoryUrl
git push -u origin main
render login
render blueprints validate render.yaml
```

If this is already a Git repository, keep its existing remote and branch. Confirm staged files contain only this project's source. `.env`, caches and local runtimes are excluded. Never commit gateway secrets, Firebase credentials, tokens or database exports.

## 2. Create the Render Blueprint

In Render Dashboard choose **New → Blueprint**, connect the repository and choose `render.yaml`. This initial dashboard step creates and deploys the resources; it is not performed by `blueprints validate`.

Set prompted values before confirming:

| Variable | Value |
| --- | --- |
| `CORS_ORIGINS` | Exact approved web origins, comma-separated. For local web review against the hosted API: `http://localhost:8081`. Native Android does not require a browser origin. |
| `SHIPPING_FEE` | Approved INR delivery charge. Local sample is `49`; this is not an approved business rate. |
| `FREE_SHIPPING_THRESHOLD` | Approved INR subtotal threshold. Local sample is `999`. |

Render supplies the internal database connection and generated secret. Retain that secret across deploys. Keep both plans Free and online payment/contact disabled for the first review. `init-db` adds missing tables; existing-column changes require a versioned migration, not `create_all`.

The database blocks external connections by default. For initial administration, temporarily allow **only your public IP /32** in the database's external access settings, use its External Database URL with TLS locally, then remove that access rule:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
$secureDatabaseUrl = Read-Host 'External database URL with sslmode=require' -AsSecureString
$env:DATABASE_URL = [System.Net.NetworkCredential]::new('', $secureDatabaseUrl).Password
.venv/Scripts/python.exe -m flask --app backend create-admin
```

The admin command prompts for credentials without displaying the password. Use the documented admin API to populate real products, variants, prices/GST, coverage and banners. The local demo seed deliberately refuses remote databases. Keep real secrets out of terminal recordings. Do not point the test suite at this database: tests truncate their configured database.

Confirm the backend is healthy:

```powershell
$apiOrigin = Read-Host 'Deployed API origin, e.g. https://your-api.onrender.com'
Invoke-RestMethod "$apiOrigin/api/v1/health"
Invoke-RestMethod "$apiOrigin/api/v1/products"
render services
# Copy the actual service ID from the list for later manual deploys:
$serviceId = Read-Host 'Render service ID'
render deploys create $serviceId --wait
```

The final command triggers another deployment and is only needed for later approved changes. See [Flask deployment](https://render.com/docs/deploy-flask), [Blueprint specification](https://render.com/docs/blueprint-spec) and [Render CLI](https://render.com/docs/cli).

## 3. Build the Android preview with EAS

Check that `com.groveandstone.app` is the package identifier you want before the first build. The EAS project ID must be created under your Expo account; none is fabricated in source.

```powershell
Set-Location mobile
npm.cmd ci
npx.cmd eas-cli@latest login
npx.cmd eas-cli@latest init
$apiUrl = Read-Host 'HTTPS API URL including /api/v1'
npx.cmd eas-cli@latest env:create --environment preview --name EXPO_PUBLIC_API_URL --value $apiUrl --visibility plaintext
npx.cmd eas-cli@latest build --platform android --profile preview
```

Accept EAS-managed Android signing credentials if appropriate for your account. Download the resulting APK from the build link and install it on your Android test phone. This consumes your available EAS build allowance; check the Expo dashboard first. `EXPO_PUBLIC_API_URL` is deliberately public and must never contain credentials.

To run the web app locally against that backend:

```powershell
$env:EXPO_PUBLIC_API_URL = $apiUrl
node --dns-result-order=ipv4first node_modules/expo/bin/cli start --web --localhost --port 8081
```

For a later approved store build:

```powershell
npx.cmd eas-cli@latest env:create --environment production --name EXPO_PUBLIC_API_URL --value $apiUrl --visibility plaintext
npx.cmd eas-cli@latest build --platform android --profile production
```

An AAB build does not publish to Google Play. Store submission and any Play account fees are separate. If the environment variable already exists, update it through Expo's environment-variable editor instead of creating a duplicate. See [EAS build profiles](https://docs.expo.dev/build/eas-json/) and [APK builds](https://docs.expo.dev/build-reference/apk/).

## 4. Live integrations require a separate review

For Razorpay, first use test-mode credentials and configure `PAYMENT_BACKEND=razorpay`, `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`, and `PUBLIC_API_URL` (HTTPS API origin without `/api/v1`). Configure automatic payment capture in Razorpay. Subscribe the signed webhook at `/api/v1/payments/gateway-webhook` to `payment.captured`, `payment.failed`, `order.paid`, and `refund.processed`. Hosted checkout collects payment details; this backend never accepts card numbers or CVVs. Verify test-mode success, failure, delayed callbacks and refunds before changing to live credentials. See [Razorpay standard checkout](https://razorpay.com/docs/payments/payment-gateway/web-integration/standard/integration-steps/).

Pending orders reserve stock for 30 minutes. Expired reservations are released on the next request, at most once per minute per process, and can also be swept explicitly. Refunds are queued durably and require the explicit worker command below; a queued refund is not reported as completed. Existing historical orders without reservation metadata are not automatically restocked.

```powershell
# From the project root in an authorized environment with database/provider secrets:
python -m flask --app backend expire-payments
python -m flask --app backend dispatch-refunds
python -m pip install -r backend/requirements-fcm.txt
python -m flask --app backend dispatch-push
```

Free Render web services have no shell, one-off jobs or free background workers. For a real launch, arrange a reliable worker host/scheduler and database access for refund/push processing, a durable database and backups, and shared rate-limit storage if adding web workers. Do not use artificial keep-alive traffic as a substitute.

For contact email, set `CONTACT_BACKEND=resend`, `RESEND_API_KEY`, a verified `CONTACT_FROM` sender and the real `SUPPORT_EMAIL` recipient. Set `SUPPORT_PHONE` if needed. This uses the [Resend HTTPS API](https://resend.com/docs/api-reference/emails/send-email); no email was sent during development. Approve the draft quality-report window (`QUALITY_REPORT_HOURS`, local sample 24) and returns copy before launch. Contact content is not stored in the order database.

## Remaining configuration

Deployment approval is recorded. Finish provider sign-in/repository connection, review the sample shipping/policy values before real sales, confirm the Expo account/package identifier, and provide service credentials through the provider's secret settings. The current plan is the requested temporary free preview; paid resources require a separate decision. Actual deployment, remote builds and live transactions remain unperformed. This recipe hosts the API; publicly hosting the Expo web frontend is a separate web-export/hosting step.
