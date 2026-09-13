# AarogyaDrishti

> See Your Habits. Shape Your Health.

A privacy-first personal lifestyle observation platform. It collects
longitudinal data about sleep, exercise, energy, stress, food, water, and mood,
then runs personal analytics, experiments, and an offline-first lifestyle
coach using only the user's own aggregates.

The project does not diagnose disease, provide treatment, predict disease risk,
or make causal claims. Missing data remains `NULL` and is never fabricated.

## Project structure

```text
backend/   FastAPI, SQLAlchemy, PostgreSQL API, migrations, and tests
mobile/    Flutter Android client
docs/      Deployment and operational guides
```

## Backend local setup

Requirements: Python 3.12+ and PostgreSQL 15+.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Set `DATABASE_URL` and `JWT_SECRET` in `.env`. For local development,
PostgreSQL can be started with Docker:

```powershell
docker run --name aarogya-db -e POSTGRES_USER=aarogya -e POSTGRES_PASSWORD=aarogya `
  -e POSTGRES_DB=aarogyadrishti -p 5432:5432 -d postgres:16-alpine
```

Initialize and run the API:

```powershell
python scripts/init_db.py
python -m alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

The local API is available at `http://localhost:8000`. The health check is
`http://localhost:8000/health`; interactive docs are available at
`http://localhost:8000/docs` while `DEBUG=true`.

Run backend tests with:

```powershell
pytest -q -p no:cacheprovider
```

## Mobile local setup

Requirements: Flutter 3.22+ and the Android toolchain.

```powershell
cd mobile
flutter pub get
flutter run
```

The Android emulator uses `http://10.0.2.2:8000` by default. Override the API
for a physical device or a deployed backend:

```powershell
flutter run --dart-define=API_BASE_URL=https://api.example.com
```

Build and test the mobile app with:

```powershell
flutter analyze
flutter test
flutter build apk --release --dart-define=API_BASE_URL=https://api.example.com
```

Production Android builds must use HTTPS and a release keystore.

## Production release build

Run the backend tests before building the production Android App Bundle:

```powershell
cd backend
pytest -q -p no:cacheprovider

cd ..\mobile
flutter pub get
flutter build appbundle --release `
  --dart-define=API_BASE_URL=https://aarogyadrishti.vercel.app `
  --dart-define=ENVIRONMENT=production
```

The signed App Bundle is created at
`mobile/build/app/outputs/bundle/release/app-release.aab`. Configure the
release keystore in `mobile/android/key.properties` before distributing it.

## Deploy the backend to Vercel

The Vercel deployment files are already included:

- `backend/vercel.json` configures the Python serverless runtime.
- `backend/api/index.py` exposes the FastAPI application.

Quick start:

1. Import the repository into Vercel.
2. Set the Vercel **Root Directory** to `backend`.
3. Select the **Other** framework preset. Leave build and output commands empty.
4. Add production environment variables: `ENVIRONMENT=production`,
  `DEBUG=false`, `DATABASE_URL`, `JWT_SECRET`, `ALLOW_DEMO_DATA=false`,
  `RATE_LIMIT_ENABLED=true`, `AUTH_PROVIDER=firebase`, `FIREBASE_PROJECT_ID`,
  and the separate `FIREBASE_*` service-account fields.
5. Run Alembic migrations against the managed PostgreSQL database.
6. Verify `https://<your-project>.vercel.app/health`.

Read the complete [Vercel deployment guide](docs/VERCEL.md) for dashboard
settings, secrets, migrations, custom domains, CLI deployment, mobile release
configuration, Firebase Google sign-in, and troubleshooting.

Vercel hosts the backend API, not the Android application. For public mobile
downloads, follow the [Flutter release guide](docs/MOBILE_RELEASE.md).

For the complete project design, workflows, implementation notes, feasibility,
and operations guidance, see the [documentation hub](docs/README.md).

## API and security

The API base path is `/api/v1`. It provides authentication, profiles, daily
logs, dashboards, experiments, personal learning, consent, and the lifestyle
coach. Production API documentation is disabled when `DEBUG=false`.

See [SECURITY.md](SECURITY.md) for authentication, privacy, rate limiting, and
production hardening details.
