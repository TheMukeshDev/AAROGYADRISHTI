# Security

AarogyaDrishti stores and processes personal health-lifestyle data, so security
and privacy are treated as product features, not an afterthought.

## 1. Security model

- **Single-tenant-by-user scoping.** Every authenticated endpoint is scoped to
  the current user (via `get_current_user` in `app/api/deps.py` and ownership
  checks in repositories/services). There are no cross-user reads or global
  aggregates.
- **Aggregates-only coaching.** The AI coach — including the remote LLM path —
  only ever receives derived summaries (pattern snapshots, evidence levels,
  learning summaries, next action). Raw daily-log rows or health vitals are
  never sent off-device to the coach provider.
- **No fabricated data.** Unknown values remain `NULL`. `causality_proven` is
  always `False`. The coach's safety guard strips phone/contact-like digit runs,
  rewrites dose-like phrasing, blocks causal claims, and appends an explicit
  "not a doctor" disclaimer.
- **Demo data is isolated.** Demo accounts are flagged `is_demo=True`, use
  clearly-labelled `source="demo"` rows, only exist when `ALLOW_DEMO_DATA=true`,
  and are refused at startup in production.

## 2. Authentication & tokens

- Passwords are hashed with **bcrypt-sha256** (SHA-256 pre-digest + bcrypt cost
  12), never stored in plaintext. The stored hash carries a scheme prefix so a
  future migration to another KDF can be detected.
- JWTs use HS256 with an `iss` check and a `ver` (`token_version`) claim.
  Logout and password reset bump `token_version`, invalidating outstanding
  tokens.
- Refresh tokens **rotate on every use**, travel only in JSON request bodies
  (never URLs — see `app/schemas/auth.py::RefreshTokenRequest`), and are stored
  on-device in `flutter_secure_storage` (Keychain/Keystore-backed).
- A minimum password policy (length + mixed character classes) is enforced both
  by the API schema and by the client validators.

## 3. Startup guards (fail fast in production)

When `ENVIRONMENT=production`, the API **refuses to boot** if any of these are
set (`app/core/config.py::_production_guards`):

| Setting | Why it is refused |
|---------|-------------------|
| `DEBUG=true` | Exposes `/docs`, `/redoc`, and `openapi.json`. |
| `ALLOW_DEMO_DATA=true` | The demo account uses a well-known password and contains seeded health data. |
| `JWT_SECRET` missing / `< 32` chars / the committed placeholder | Tokens would be forgeable. |

This makes unsafe deployments fail loudly at startup instead of silently
serving real data.

## 4. Request hardening

- **Rate limiting** (`app/core/rate_limit.py`, opt-in via `RATE_LIMIT_ENABLED`):
  per-IP fixed window, with a tighter budget for `/auth/*` endpoints
  (`RATE_LIMIT_AUTH_PER_MINUTE`) to blunt brute-force / credential-stuffing.
  Returns `429` with code `rate_limited` and a `Retry-After` header. In
  production, additionally rate-limit at your load balancer / reverse proxy.
- **Security response headers** (`SecurityHeadersMiddleware`):
  `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
  `Referrer-Policy: no-referrer`, `Permissions-Policy` and
  `Strict-Transport-Security` over HTTPS.
- **Error envelope** (`app/core/errors.py`): clients only ever receive the
  `{error: {code, message, details}}` shape. Stack traces, SQL and driver
  messages are logged server-side, never returned.
- **Log hygiene** (`RequestContextMiddleware`): every request gets a
  `X-Request-ID`, and health payloads are never logged (paths in
  `UNLOGGED_PATHS` are metadata-only).
- **CORS**: explicit origin allow-list (defaults to localhost). Never use `*`
  together with `allow_credentials`.

## 5. Client (mobile) security

- **Cleartext is blocked** by default (`network_security_config.xml`); only the
  emulator/loopback dev hosts are exceptions. Production builds must point
  `API_BASE_URL` at `https://`.
- **Tokens** live in `flutter_secure_storage`, not SharedPreferences. Sensitive
  health values are never persisted in plaintext prefs.
- **Release signing** reads `android/key.properties` (git-ignored). Shipping a
  debug-signed release APK is disabled by policy — the Gradle config warns and
  falls back only to keep local `--release` builds compilable.

## 6. Production checklist

- [ ] `ENVIRONMENT=production`, `DEBUG=false`
- [ ] Strong `JWT_SECRET` (>= 32 chars, unique per environment)
- [ ] `ALLOW_DEMO_DATA=false`
- [ ] `CORS_ORIGINS` set to your real origins
- [ ] `RATE_LIMIT_ENABLED=true` (plus gateway-level limiting)
- [ ] PostgreSQL with a dedicated, least-privilege user; encrypted at rest
- [ ] HTTPS everywhere (TLS at the reverse proxy) + HSTS
- [ ] Mobile built with `--dart-define=API_BASE_URL=https://...` and a real
      release keystore
- [ ] Backups of the database encrypted; retain health data per your privacy
      policy / applicable law
- [ ] No `.env` or `key.properties` committed

## 7. Known limitations / future work

- Rate limiter is **in-memory and single-process**; multi-process deployments
  should add Redis-backed limiting at the gateway.
- Password reset returns a token to the caller (Phase 1 has no SMTP); wire real
  email delivery before production and never serve reset tokens over unauthenticated channels.
- `email_verified` is not enforced yet — planned with email verification.
- No CSRF risk (bearer-token API clients, not cookies), but API clients should
  pin certificates for additional transport assurance.
- JWT access tokens are stateless (no server-side revocation); logout relies on
  `token_version` and a short access-token lifetime.

## 8. Reporting a vulnerability

If you find a security issue, open a private issue or contact the maintainers
directly. Include reproduction steps and impact; please do not disclose the
details publicly before they are addressed. We will acknowledge and fix
priority issues promptly.