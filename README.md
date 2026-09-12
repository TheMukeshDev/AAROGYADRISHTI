# AarogyaDrishti

> See Your Habits. Shape Your Health.

A privacy-first personal lifestyle observation platform that collects clean,
longitudinal data about sleep, exercise, energy, stress, food, water and mood —
then runs a personal experiment engine and an offline-first lifestyle coach on
top of *only the user's own aggregates*.

**Phases 1–6** are implemented in the backend; Phases 2–6 are UI-integrated in
the Flutter app (screens written, but not yet `flutter analyze`-clean because a
Flutter SDK is not installed in this workspace).

It intentionally has **no disease risk predictions, no diagnosis, no
treatments and no causal claims**. Anything derived from the data is an
*observed correlation* (`causality_proven` is always `False`), and missing data
stays `NULL` — never fabricated.

```
backend/   FastAPI + SQLAlchemy + PostgreSQL (auth, check-ins, analytics,
           experiment engine, evaluation, personal learning, AI coach)
mobile/    Flutter + Material 3 app (auth, onboarding, dashboard, check-in,
           experiments, coach, learning profile, history)
```

---

## 1. Backend (FastAPI)

### Requirements
- Python 3.12+ (tested on 3.14)
- PostgreSQL 15+ (a version is required; local dev can use Docker)

### Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt

# Configure environment
Copy-Item .env.example .env   # then edit DATABASE_URL / JWT_SECRET

# Create the schema (idempotent) and run migrations
.\.venv\Scripts\python scripts\init_db.py
.\.venv\Scripts\python -m alembic upgrade head

# Optional: seed demo users + demo data (requires ALLOW_DEMO_DATA=true)
.\.venv\Scripts\python scripts\seed_demo.py

# Run the API
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

Interactive docs: `http://localhost:8000/docs`

### Environment variables (`.env`)

| Variable                  | Description |
|---------------------------|-------------|
| `DATABASE_URL`            | PostgreSQL DSN, e.g. `postgresql+psycopg://postgres:postgres@localhost:5432/aarogya` |
| `JWT_SECRET`              | Secret for signing tokens (>= 32 chars in production) |
| `ACCESS_TOKEN_EXPIRY`     | Access token minutes (default 30) |
| `REFRESH_TOKEN_EXPIRY`    | Refresh token days (default 7) |
| `AUTH_PROVIDER`           | `internal` (JWT password auth) |
| `ALLOW_DEMO_DATA`         | `true`/`false` — gated demo endpoints + seeding |
| `BASELINE_TARGET_DAYS`    | Days to complete a baseline (default 7) |
| `EXPERIMENT_COOLDOWN_DAYS`| Days after completing before the same pattern is re-suggested (default 14) |
| `AI_PROVIDER`             | `deterministic` (offline, default) or `openai_compatible` |
| `AI_API_KEY`              | Set only when using `openai_compatible` |
| `AI_BASE_URL`             | Base URL for the OpenAI-compatible endpoint |
| `AI_MODEL`                | Model name for `openai_compatible` |
| `AI_MAX_COACH_NUMBER`     | Max allowed number in suggested lifestyle targets |
| `LOG_LEVEL`               | `INFO` / `DEBUG` |

### API overview (`/api/v1`)

Phase 1 (auth + tracking):
- `POST /auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/demo`
- `GET/PUT /profile`, `GET /profile/onboarding-status`
- `GET/POST /daily-logs`, `GET/PUT /daily-logs/{date}`
- `GET /dashboard/today`, `/dashboard/baseline`
- `GET /health/status`, `POST /health/connect`, `POST /health/sync`
- `POST /consent/records`

Phase 2 (analytics):
- `GET /analytics/patterns` — deterministic correlation patterns from your own data
- `GET /analytics/daily-summaries`, `GET /analytics/metric-summaries`, `GET /analytics/timeseries`

Phase 3 (experiment engine):
- `GET /experiments/recommended` — analytics-driven suggestion (never hardcoded)
- `POST /experiments` (start), `GET /experiments/active`, `GET /experiments/history`, `GET /experiments/{id}`
- `POST /experiments/{id}/daily-log`, `POST /experiments/{id}/complete`, `POST /experiments/{id}/cancel`
- `GET /experiment-templates`

Phase 4 (evaluation + evidence):
- `POST /experiments/{id}/evaluate`, `GET /experiments/{id}/result`, `/evaluation`, `/metrics`, `/evidence`
- `GET /experiments/{id}/learning-candidate`, `GET /learning-candidates`
- `POST /learning-candidates/{id}/accept` / `/reject` — feeds the personal learning profile

Phase 5 (personal learning profile):
- `GET /learnings/personal/summary`, `GET /learnings/personal`
- `POST /learnings/personal` (recompute), `GET /learnings/personal/{id}`
- `DELETE /learnings/personal/{id}` (dismiss), `PATCH /learnings/personal/{id}` (reopen)

Phase 6 (AI coach):
- `POST /coach/conversations`, `GET /coach/conversations`
- `GET /coach/conversations/{id}/messages`, `POST /coach/conversations/{id}/messages`
- `GET /coach/next-action`, `GET /coach/weekly-summary`

### Data-quality rules (phase invariants)

- Unknown values are stored as **NULL**, never fabricated as zero.
- Health Connect values are blended into the user's existing day row.
- Demo data is explicitly flagged (`source = 'demo'`) and dev-only.
- Consent for each Health Connect data type is recorded as a row.
- Experiment results are evaluated against a real baseline window
  (`EXPERIMENT_BASELINE_WINDOW_DAYS=14`, minimum 3 valid days); comparisons are
  computed with the same feature columns the rest of the system uses.
- `causality_proven` is **always False**. Evidence levels are capped
  (`INSUFFICIENT → EARLY_OBSERVATION → PROMISING_OBSERVATION →
  REPEATED_OBSERVATION`), consistency is bounded at 0–100, and summaries end
  with "not a proof of cause and effect".
- The coach (including the LLM path) only ever receives **aggregates**
  (patterns, evidence, learning summaries, next action) — raw daily-log rows are
  never sent. The safety guard strips dose-like and phone-like digit runs and
  appends an explicit "not a doctor" disclaimer.

### Migrations

Migrations live in `backend/alembic/versions/`:
`0001_phase1`, `0002_experiments`, `0003_evaluation`, `0004_personal_learnings`,
`0005_coach` (current head).

```powershell
.\.venv\Scripts\python -m alembic revision --autogenerate -m "message"
.\.venv\Scripts\python -m alembic upgrade head
```

### Tests

```powershell
.\.venv\Scripts\python -m pytest -q -p no:cacheprovider
```

90 passing: 51 (Phase 1) + 20 (scoped suites for phases 3/4) + 9 (Phase 5) +
10 (Phase 6). Tests use an in-memory SQLite database (see `tests/conftest.py`).

> The `-p no:cacheprovider` flag avoids a Windows access-denied error writing
> `.pytest_cache`.

---

## 2. Mobile (Flutter)

### Requirements
- Flutter SDK 3.22+ (Dart `>=3.3.0`)
- Android device/emulator with **Health Connect** app from Play Store (or `--dart-define` fallback to manual-only).

### Setup

```powershell
cd mobile
flutter pub get
flutter run
```

> Health Connect API permissions (<30) and queries are declared in
> `android/app/src/main/AndroidManifest.xml`. Health data sync is **best-effort**:
> if Health Connect is unavailable or permission is denied, the app continues
> with manual-only tracking.

### Architecture

```
lib/
  core/        constants, strings, theme, network (ApiClient), storage, utils
  models/      API DTOs (daily_log, dashboard, experiment, learning, coach, ...)
  repositories/ thin HTTP clients (auth, profile, daily_log, health, consent,
                  experiment, learning, coach)
  providers/   AuthProvider (ChangeNotifier)
  services/    HealthConnectService
  widgets/     PrimaryButton, CheckinOption, MetricCard, ProgressCard, AppScaffold
  features/    auth, onboarding, dashboard, checkin, experiments, learning,
               coach, history, profile, root_gate
  app.dart     AppServices composition root + AarogyaDrishtiApp
```

Bottom navigation: Home / Check-in / **Experiments** / **Coach** / History /
Profile. Experiments opens the "What works for me" learning profile; the coach
chat offers "What should I do next?" and "Weekly summary" quick actions.

> Written without a local Flutter SDK, so these Phase 2–6 screens are
> **unverified** — they must be `flutter analyze`d and `flutter test`ed on a
> machine with the SDK before release.

---

## 3. Phase completion checklist

Phase 1 — Tracking infrastructure
- [x] Auth (register / login / refresh / logout / demo)
- [x] JWT-secured profile, check-in, dashboard, health-sync, consent APIs
- [x] Baseline progress tracking (no AI)
- [x] Health Connect sync + consent records
- [x] Backend tests (51 passing) + Flutter unit/widget tests

Phase 2 — Personal analytics
- [x] Pattern detection (deterministic correlation/regression on own data only)
- [x] Daily summaries, metric summaries, timeseries
- [x] Scikit-learn/SHAP behind guarded optional imports (blocked by App Control)

Phase 3 — Personal experiment engine
- [x] Template-driven experiments, analytics-driven recommendations
- [x] Active-experiment daily logging, completion, cancel, history

Phase 4 — Experiment evaluation & evidence
- [x] Baseline vs experiment metric comparison, adherence, consistency score
- [x] Evidence levels + permanent evidence row (evaluations are immutable, appended)
- [x] Learning candidates with accept/reject
- [x] Cooldown so a completed pattern is not immediately re-suggested

Phase 5 — "What Works For Me" personal learning profile
- [x] Personal learnings + evidence rows, deterministic recalculation
- [x] Consistency score (0.5 alignment + 0.3 magnitude + 0.2 coverage)
- [x] Dismiss / reopen, top-observation summary

Phase 6 — AI preventive lifestyle coach
- [x] Provider abstraction (deterministic offline default, OpenAI-compatible via httpx)
- [x] Safety guard + disclaimer + aggregates-only context
- [x] Conversations/messages API, next-action, weekly summary
- [x] Coach tests (10 passing)

Known follow-ups
- [ ] Verify Flutter Phase 2–6 screens on a machine with the Flutter SDK
- [ ] Manual device QA on Android (Health Connect grant flow)
- [ ] Production: real error observability, rate limiting, email verification