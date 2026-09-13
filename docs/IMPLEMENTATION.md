# Implementation guide

## Repository map

```text
backend/app/api/           HTTP route handlers
backend/app/schemas/       Pydantic request and response contracts
backend/app/services/      Business operations and provider orchestration
backend/app/repositories/  Database access helpers
backend/app/models/        SQLAlchemy entities
backend/app/analytics/     Baselines, patterns, evidence, insights
backend/app/ai/            Coach providers, prompts, and safety guard
backend/alembic/           Versioned database migrations
backend/tests/             API and service tests
mobile/lib/features/       User-facing Flutter screens and flows
mobile/lib/providers/      Session and state controllers
mobile/lib/repositories/   HTTP repositories
mobile/lib/services/       Health Connect integration
mobile/android/            Android, Firebase, and release signing setup
```

## Authentication implementation

- Password login uses bcrypt-sha256 hashes and app-issued JWTs.
- Google login uses `google_sign_in` and `firebase_auth` in Flutter.
- The backend verifies Firebase tokens with `firebase-admin`.
- New Google users are created with `password_hash=NULL` and
  `auth_provider="firebase"`.
- Existing users with the same verified email are reused.
- The backend then issues the same access and refresh token pair used by
  password login.
- Logout increments `token_version`, invalidating outstanding app JWTs.

## Data and migration rules

- Add schema changes as a new Alembic revision; do not edit an applied revision.
- Run `python -m alembic upgrade head` before production traffic.
- Keep SQLite for local tests only. Production uses managed PostgreSQL.
- Keep user ownership checks in services/repositories, not only in the mobile
  UI.

## API conventions

- Base path: `/api/v1`.
- Protected routes require `Authorization: Bearer <app-access-token>`.
- Refresh tokens are sent in JSON bodies, never query parameters.
- Errors use the standard `{ "error": { "code": ..., "message": ... } }`
  envelope.
- `/health` is a liveness check and does not touch the database.
- Interactive docs are disabled when `DEBUG=false`.

## Configuration precedence

Environment variables are loaded by `pydantic-settings`. Production values are
set in Vercel; local values belong in an ignored `backend/.env`. Firebase
service-account fields are provided individually so the host does not need a
full service-account JSON blob.

## Safe extension points

- Add providers behind the existing AI provider factory.
- Add analytics as deterministic functions over validated user data.
- Add API behavior through a schema, router, service, repository/model change,
  and focused test.
- Keep external integrations behind a service boundary so tests can replace
  them with fakes.
