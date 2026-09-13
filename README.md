# AarogyaDrishti

> See Your Habits. Shape Your Health.

A privacy-first personal lifestyle observation platform. It collects clean,
longitudinal data about sleep, exercise, energy, stress, food, water and mood —
then runs a personal experiment engine and an offline-first lifestyle coach on
top of **only the user's own aggregates**.

AarogyaDrishti intentionally provides **no disease risk predictions, no
diagnosis, no treatments and no causal claims**. Anything derived from the data
is an *observed correlation* (`causality_proven` is always `False`), and missing
data stays `NULL` — it is never fabricated.

---

## 1. Repository layout

```
AAROGYADRISHTI/
├── backend/                 # FastAPI + SQLAlchemy + PostgreSQL API
│   ├── app/
│   │   ├── api/             # Route handlers (auth, profile, daily-logs, ...)
│   │   ├── ai/              # Coach providers + safety guard (Phase 6)
│   │   ├── analytics/       # Deterministic personal analytics (Phase 2)
│   │   ├── core/            # Config, security, logging, errors, middleware
│   │   ├── database/        # SQLAlchemy engine/session + base models
│   │   ├── models/          # ORM models
│   │   ├── repositories/    # Data access helpers
│   │   ├── schemas/         # Pydantic request/response models
│   │   └── services/        # Business logic (auth, experiments, coach, ...)
│   ├── alembic/             # Database migrations
│   ├── scripts/             # init_db.py, seed_demo.py
│   ├── tests/               # pytest suite (in-memory SQLite)
│   ├── .env.example         # Environment template (copy to .env)
│   └── requirements.txt
└── mobile/                  # Flutter + Material 3 app
    ├── lib/
    │   ├── core/            # Constants, theme, network, storage, utils
    │   ├── features/        # auth, onboarding, dashboard, checkin, ...
    │   ├── models/          # API DTOs
    │   ├── repositories/    # Thin HTTP clients
    │   ├── services/        # HealthConnectService
    │   └── app.dart         # Composition root
    ├── android/             # Android host project
    └── test/                # Flutter unit/widget tests
```

---

## 2. Backend (FastAPI)

### 2.1 Prerequisites

- **Python 3.12+** (developed against 3.14)
- **PostgreSQL 15+** — or Docker with a Postgres container (see below)
- Optional but recommended on Windows: no special tools; PowerShell commands below.

### 2.2 One-time setup

```powershell
cd backend

# 1. Create + activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1        # bash: source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt   # pytest + coverage (for tests)

# 3. Create your local environment file
Copy-Item .env.example .env
```

### 2.3 Database

**Option A — Docker (easiest, recommended for locals)**

```powershell
docker run --name aarogya-db -e POSTGRES_USER=aarogya -e POSTGRES_PASSWORD=aarogya `
  -e POSTGRES_DB=aarogyadrishti -p 5432:5432 -d postgres:16-alpine
```

**Option B — local PostgreSQL**

Create a database and user matching `DATABASE_URL` in `.env`, or edit
`DATABASE_URL` to match your local instance.

> Developers in a hurry can run the API against an in-memory SQLite database by
> setting `DATABASE_URL=sqlite:///./aarogya-local.db` in `.env` — the schema is
> created by `scripts/init_db.py`. Real deployments should use PostgreSQL.

### 2.4 Configure environment

Edit `.env` (never commit it — it is git-ignored). **Critical items**:

```dotenv
ENVIRONMENT=development       # switch to "production" on a real deployment
DEBUG=true                    # false in production (refused at startup if true)
JWT_SECRET=<a long random string>   # REQUIRED in production
ALLOW_DEMO_DATA=false         # leave false unless you are demoing the app
```

Generate a JWT secret with:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 2.5 Create schema + run migrations

```powershell
# Idempotent schema creation (dev convenience)
.\.venv\Scripts\python.exe scripts\init_db.py

# Apply Alembic migrations (kept authoritative for real environments)
.\.venv\Scripts\python.exe -m alembic upgrade head
```

### 2.6 Seed demo data (optional, dev only)

```powershell
# Requires ALLOW_DEMO_DATA=true in .env
.\.venv\Scripts\python.exe scripts\seed_demo.py
```

This creates a `demo` user with 7 days of clearly-labelled demo data. The
`POST /api/v1/auth/demo` endpoint does the same on demand. Demo data is flagged
`source="demo"` and is refused in production.

### 2.7 Run the API

```powershell
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

- Interactive API docs (development only): <http://localhost:8000/docs>
- Liveness probe: <http://localhost:8000/health>

### 2.8 Run the tests

```powershell
.\.venv\Scripts\pytest -q -p no:cacheprovider
```

Tests run against an in-memory SQLite database (see `tests/conftest.py`).

> **Windows note:** `-p no:cacheprovider` avoids a known access-denied error on
> `.pytest_cache`. On some locked-down Windows machines (App Control policies)
> the numpy/pandas DLLs are blocked at import time; if you hit `DLL load failed
> while importing _generator`, run the suites that don't need analytics:
>
> ```powershell
> .\.venv\Scripts\pytest -q -p no:cacheprovider tests\test_security.py tests\test_config_guards.py tests\test_rate_limit.py
> ```
>
> and run the full suite on an unrestricted machine.

---

## 3. Mobile (Flutter)

### 3.1 Prerequisites

- **Flutter SDK 3.22+** (Dart `>=3.3.0`), with Android toolchain:
  - Android Studio (or `flutter doctor`-clean setup)
  - Android SDK `platform-tools`, a connected device or emulator
- For Health Connect sync: the **Health Connect** app installed from the Play
  Store on the device. The app works without it (manual-only tracking).

### 3.2 Configure the API base URL

The app defaults to the Android emulator loopback
(`http://10.0.2.2:8000`), which matches a backend running locally on your
machine. Point it anywhere else at build/run time:

```powershell
cd mobile
flutter pub get

# Point at a local backend on a physical device (substitute your LAN IP):
flutter run --dart-define=API_BASE_URL=http://192.168.1.20:8000

# Point at a production API over HTTPS:
flutter run --dart-define=API_BASE_URL=https://api.your-domain.in
```

### 3.3 Run on an emulator / device

```powershell
flutter pub get
flutter run
```

Health data sync is **best-effort**: if Health Connect is unavailable or
permission is denied, the app continues with manual-only check-ins.

### 3.4 Build a release APK

```powershell
flutter build apk --release --dart-define=API_BASE_URL=https://api.your-domain.in
```

**Release signing.** Before shipping, create `mobile/android/key.properties`
(never commit it):

```properties
storePassword=<store password>
keyPassword=<key password>
keyAlias=<key alias>
storeFile=../key.jks
```

Generate a keystore first, for example with `keytool`. If `key.properties` is
missing the Gradle build falls back to the debug keystore with an explicit
warning — fine for development, **never** publish that APK.

### 3.5 Security note: cleartext traffic

Android cleartext (plain `http://`) is **blocked** by default via
`res/xml/network_security_config.xml`. Only the emulator/loopback hosts
(`10.0.2.2`, `localhost`, `127.0.0.1`) are allowed cleartext for local
development. Production builds must use `https://`.

### 3.6 Quality gates

```powershell
flutter analyze
flutter test
```

---

## 4. Deploy the backend to Vercel

Vercel hosts the FastAPI backend as a Python serverless function. The Flutter
application remains a mobile client and is released separately. The Vercel
project must use `backend/` as its **Root Directory**; that directory contains
`vercel.json`, `api/index.py`, and the backend `requirements.txt`.

### 4.1 Create the Vercel project

1. Push this repository to GitHub and import it into Vercel.
2. In **Project Settings > General**, set **Root Directory** to `backend`.
3. Leave the framework preset as **Other**. No build command or output
  directory is required.
4. Add the production environment variables below in **Settings > Environment
  Variables**. Add them for **Production** (and Preview if you use preview
  deployments).

Required production values:

```dotenv
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE
JWT_SECRET=<output of: python -c "import secrets; print(secrets.token_urlsafe(64))">
ALLOW_DEMO_DATA=false
CORS_ORIGINS=https://your-mobile-web-origin.example
RATE_LIMIT_ENABLED=true
```

Use a managed PostgreSQL database that accepts connections from Vercel. Do not
use SQLite for this deployment: serverless instances are ephemeral and cannot
provide reliable persistent storage. Keep `AI_PROVIDER=deterministic` unless a
remote provider is configured with `AI_API_KEY`, `AI_BASE_URL`, and `AI_MODEL`.

### 4.2 Run database migrations

Run migrations against the production database before sending mobile traffic.
From a local checkout with the production `DATABASE_URL` supplied securely:

```powershell
cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Do not commit the production connection string. Vercel deployments do not run
Alembic automatically, so repeat this command whenever a new migration is
released.

### 4.3 Verify the deployment

After the first deployment, check the liveness endpoint:

```text
https://<your-vercel-domain>/health
```

It should return `{"status":"ok",...}`. With `DEBUG=false`, `/docs` and
`/redoc` intentionally return 404. Point the mobile release build at the
deployed API (without a trailing slash):

```powershell
cd mobile
flutter build apk --release --dart-define=API_BASE_URL=https://<your-vercel-domain>
```

Vercel preview URLs are not suitable for a production mobile build. Use a
stable custom domain for the API and add that domain to `CORS_ORIGINS` when a
browser-based client is introduced.

---

## 5. Environment variables (backend)

| Variable                            | Default                    | Description |
|-------------------------------------|----------------------------|-------------|
| `ENVIRONMENT`                       | `development`              | `development` \| `staging` \| `production`. In production the guards below are enforced at startup. |
| `DEBUG`                             | `true`                     | `false` in production (refused at startup if `true`); controls `/docs`, `/redoc`, OpenAPI. |
| `DATABASE_URL`                      | *(local Postgres)*         | SQLAlchemy DSN, e.g. `postgresql+psycopg://user:pass@host:5432/db` |
| `JWT_SECRET`                        | `*committed placeholder*`  | **Required in production**, >= 32 chars, not the placeholder. |
| `JWT_ALGORITHM` / `JWT_ISSUER`      | `HS256` / `aarogyadrishti-api` | Token signing + issuer validation |
| `ACCESS_TOKEN_EXPIRE_MINUTES`       | `60`                       | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS`         | `30`                       | Refresh token lifetime |
| `PASSWORD_RESET_EXPIRE_MINUTES`     | `30`                       | Reset token lifetime |
| `PASSWORD_MIN_LENGTH`               | `8`                        | Minimum password length |
| `AUTH_PROVIDER`                     | `jwt`                      | `jwt` (internal) — Firebase reserved for future |
| `CORS_ORIGINS`                      | `http://localhost:8080,http://localhost:3000` | Comma separated; never `*` with credentials |
| `RATE_LIMIT_ENABLED`                | `false`                    | Enable in-memory per-IP limits |
| `RATE_LIMIT_GENERAL_PER_MINUTE`     | `120`                      | Non-auth requests / IP / minute |
| `RATE_LIMIT_AUTH_PER_MINUTE`        | `10`                       | `/auth/*` requests / IP / minute |
| `RATE_LIMIT_TRUSTED_PROXY_COUNT`    | `0`                        | Set to `1` behind one reverse proxy (uses `X-Forwarded-For`) |
| `ALLOW_DEMO_DATA`                   | `false`                    | Demo endpoints + seeding; **refused in production** |
| `AI_PROVIDER`                       | `deterministic`            | `deterministic` (offline, default) or `openai_compatible` |
| `AI_API_KEY` / `AI_BASE_URL` / `AI_MODEL` | *(empty)*          | Remote coach credentials (only when using a remote provider) |
| `LOG_LEVEL`                         | `INFO`                     | `INFO` / `DEBUG` |

---

## 5. API overview (`/api/v1`)

All endpoints other than auth/register/login/refresh and experiment-templates are
behind a bearer access token and are scoped to the authenticated user only.

```
# Auth
POST /auth/register          POST /auth/login          POST /auth/refresh
POST /auth/logout            POST /auth/forgot-password
POST /auth/reset-password    POST /auth/demo            (dev-only, gated)

# Profile & onboarding
GET  /profile                POST /profile             PUT /profile

# Daily check-ins & dashboard
GET  /daily-logs             POST /daily-logs
GET  /daily-logs/{date}      PUT  /daily-logs/{date}
GET  /dashboard/today        GET  /dashboard/baseline

# Health Connect
GET  /health/status          POST /health/connect      POST /health/sync

# Consent
GET  /consent                POST /consent

# Experiments, evaluation & learning candidates
GET  /experiment-templates
GET  /experiments/recommended
POST /experiments            GET  /experiments/active  GET /experiments/history
GET  /experiments/{id}
POST /experiments/{id}/daily-log   POST /experiments/{id}/complete
POST /experiments/{id}/cancel      POST /experiments/{id}/evaluate
GET  /experiments/{id}/result | /evaluation | /metrics | /evidence
GET  /experiments/{id}/learning-candidate
GET  /learning-candidates
POST /learning-candidates/{id}/accept | /reject

# Personal learning profile (Phase 5)
GET  /learnings/personal/summary
GET  /learnings/personal            POST /learnings/personal   (recompute)
GET  /learnings/personal/{id}
DELETE /learnings/personal/{id}     PATCH /learnings/personal/{id}

# AI coach (Phase 6)
POST /coach/conversations    GET /coach/conversations
GET|POST /coach/conversations/{id}/messages
GET  /coach/next-action      GET /coach/weekly-summary
```

---

## 7. Security quick-reference

Hardening is documented in [SECURITY.md](SECURITY.md). The short version:

- Passwords are bcrypt-hashed (bcrypt-sha256, cost 12) and never stored in plaintext.
- JWTs are HS256 with an issuer check and a `token_version` claim; logout and
  password reset invalidate outstanding tokens.
- Refresh tokens travel in the **JSON body** (never in URLs), rotate on every use.
- Production startup **fails fast** if `DEBUG=true`, `ALLOW_DEMO_DATA=true`, a
  weak `JWT_SECRET`, and under a few other unsafe settings.
- Auth endpoints are rate-limited per IP (opt-in via `RATE_LIMIT_ENABLED`).
- The coach (including the LLM path) only ever receives **aggregates**; a
  safety guard strips contact/dose-like patterns and appends a "not a doctor"
  disclaimer.
- Android builds block cleartext traffic except for dev loopback hosts.
- Response headers (`X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`, HSTS over HTTPS) are added by middleware.

---

## 8. Data-quality invariants

- Unknown values are stored as **NULL**, never fabricated as zero.
- Health Connect values are blended into the user's existing day row.
- Demo data is explicitly flagged (`source = 'demo'`) and dev-only.
- Consent for each Health Connect data type is recorded as a row.
- Experiment results are evaluated against a real baseline window;
  `causality_proven` is **always False** and evidence levels are capped at
  `REPEATED_OBSERVATION`.
- The coach never receives raw daily-log rows — only derived aggregates.

---

## 9. Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Database connection refused` | Start Postgres (see 2.3) and confirm `DATABASE_URL` in `.env`. |
| `InsecureKeyLengthWarning` | Set a `JWT_SECRET` of 32+ characters. |
| Worker starts but `/docs` 404s | You set `DEBUG=false` — docs are dev-only by design. |
| `SurefireReport`... no | Not a thing; see `flutter doctor`. |
| `DLL load failed ... _generator` | App Control blocks numpy/pandas on this Windows machine — run the non-analytics test suites (2.8) and full suite elsewhere. |
| Emulator can't reach backend | Use `http://10.0.2.2:8000` (default) on Android emulators; on a physical device use your LAN IP with `--dart-define`. |
| Release APK is blocked by Play | You shipped without a release keystore (`key.properties`) — configure 3.4 signing. |

---

## 10. Phase status

| Phase | Area | Status |
|-------|------|--------|
| 1 | Auth, tracking, baseline, Health Connect, consent | Implemented + tested |
| 2 | Deterministic personal analytics | Implemented + tested |
| 3 | Experiment engine + recommendations | Implemented + tested |
| 4 | Evaluation, evidence, learning candidates | Implemented + tested |
| 5 | "What works for me" personal learning profile | Implemented + tested |
| 6 | AI preventive lifestyle coach (aggregates only) | Implemented + tested |

Known follow-ups: verify Phase 2–6 Flutter screens on a machine with the Flutter
SDK, manual device QA of the Health Connect grant flow, and production items
(error observability, gateway-level rate limiting, email verification for
password reset).