# Deploy the backend to Vercel

This project deploys the FastAPI backend to Vercel as a Python serverless
function. The Flutter app is a separate client and is released independently.

## Before you start

You need:

- A GitHub repository containing this project.
- A Vercel account.
- A managed PostgreSQL database, such as Neon, Supabase, or Vercel Postgres.
- Python 3.12+ locally if you will run migrations from your machine.

SQLite is not suitable for production because Vercel function storage is
ephemeral and cannot provide reliable persistent database storage.

## Create the Vercel project

1. Import the GitHub repository in Vercel.
2. Set **Root Directory** to `backend` in **Project Settings > General**.
3. Use the **Other** framework preset.
4. Leave **Build Command** and **Output Directory** empty.
5. Deploy the project.

The `backend/vercel.json` file configures the Python runtime and routes every
request to `backend/api/index.py`, which exposes the existing FastAPI app.

## Configure environment variables

Add these in **Project Settings > Environment Variables**. Select **Production**
(and **Preview** too if preview deployments need a database).

```dotenv
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE
JWT_SECRET=<generate a unique random value of at least 32 characters>
ALLOW_DEMO_DATA=false
CORS_ORIGINS=https://your-web-client.example
RATE_LIMIT_ENABLED=true
AUTH_PROVIDER=firebase
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-firebase-project-id.iam.gserviceaccount.com
FIREBASE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\n<private-key-content>\n-----END PRIVATE KEY-----\n
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
```

Generate a secret locally:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Also configure these only when needed:

```dotenv
AI_PROVIDER=deterministic
AI_API_KEY=
AI_BASE_URL=
AI_MODEL=gpt-4o-mini
```

Set `AI_PROVIDER=openai_compatible` and provide the three AI values only when
a remote AI coach provider is intentionally enabled. Never commit secrets or
put them in `vercel.json`.

`CORS_ORIGINS` is a comma-separated list. Use the actual origin of any browser
client; a Flutter Android app does not require CORS. Do not use `*` with the
API's credentialed CORS configuration.

### Firebase Google sign-in setup

1. Create or open a project in the [Firebase Console](https://console.firebase.google.com/).
2. Enable **Authentication > Sign-in method > Google**.
3. Add an Android app with package name `com.aarogyadrishti.app`.
4. Add the SHA-1 and SHA-256 fingerprints for the debug and release signing
  keys, then download `google-services.json` into
  `mobile/android/app/google-services.json`.
5. Create a Firebase Admin service account in **Project settings > Service
  accounts**, generate a private key, and copy its fields into the separate
  `FIREBASE_*` Vercel variables above. In `FIREBASE_PRIVATE_KEY`, preserve the
  `\n` characters between certificate lines. The other service-account JSON
  fields are not required by this deployment. Never commit the key.
6. Keep `AUTH_PROVIDER=firebase` and redeploy the backend.

The mobile app signs in with Google through Firebase, obtains a Firebase ID
token, and sends it to `POST /api/v1/auth/firebase`. The backend verifies the
token with Firebase Admin and returns the app's normal access and refresh JWTs.
The Firebase ID token is never accepted as an AarogyaDrishti API bearer token.

## Run database migrations

Vercel does not run Alembic automatically. Apply migrations before using the
production API and after each migration release:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DATABASE_URL = "postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE"
python -m alembic upgrade head
```

Use a secure shell or CI secret for `DATABASE_URL`; do not save the production
value in `.env` or commit it.

## Verify the deployment

After deployment, test the liveness endpoint:

```text
https://<your-project>.vercel.app/health
```

A healthy response contains `"status":"ok"`. With `DEBUG=false`, `/docs`,
`/redoc`, and the OpenAPI document are intentionally disabled.

For a stable mobile release, add a custom domain in **Project Settings >
Domains** and use that HTTPS URL as the API base URL:

```powershell
cd mobile
flutter build apk --release --dart-define=API_BASE_URL=https://api.example.com
```

Do not use a Vercel preview URL in a published mobile build.

## Deploy from the Vercel CLI (optional)

```powershell
npm install -g vercel
vercel login
cd backend
vercel
vercel --prod
```

When prompted, link the command to the existing Vercel project. The CLI runs
from `backend`, so it automatically uses the correct root and `vercel.json`.

## Troubleshooting

- **404 for every route:** confirm the Vercel Root Directory is `backend` and
  that `backend/api/index.py` is present.
- **Function fails during startup:** check `DATABASE_URL`, `JWT_SECRET`, and
  that `ENVIRONMENT=production` has `DEBUG=false`, `ALLOW_DEMO_DATA=false`,
  `AUTH_PROVIDER=firebase`, and valid Firebase credentials.
- **Google sign-in fails on Android:** verify `google-services.json` matches
  `com.aarogyadrishti.app` and that the signing-key SHA fingerprints are added
  in Firebase.
- **Firebase token exchange fails:** verify `FIREBASE_PROJECT_ID` matches the
  Firebase project and that all Firebase service-account fields are present.
- **Database connection errors:** verify the database is reachable from Vercel
  and that the URL uses the `postgresql+psycopg://` SQLAlchemy scheme.
- **CORS errors in a browser:** add the exact browser origin to `CORS_ORIGINS`,
  then redeploy. Native Flutter requests are not subject to browser CORS.
- **Slow or unreliable requests:** Vercel functions are request-based and the
  rate limiter is per process. Use a managed database pooler and an upstream
  rate limiter for higher traffic.
