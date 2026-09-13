# Feasibility and delivery status

## Current feasibility

| Area | Status | Evidence or dependency |
| --- | --- | --- |
| Flutter Android client | Implemented | `mobile/` screens, repositories, providers, and tests |
| Password authentication | Implemented | Backend auth routes and JWT tests |
| Google sign-in | Implemented, requires Firebase setup | Firebase project, SHA fingerprints, and service account values |
| FastAPI hosting | Implemented | `backend/vercel.json` and `backend/api/index.py` |
| Durable production data | Ready | Managed PostgreSQL and Alembic migrations required |
| Health Connect | Implemented, device-dependent | Android Health Connect availability and permission |
| Deterministic analytics | Implemented | Backend analytics modules and test data |
| AI coach | Implemented with deterministic default | Remote provider is optional and requires secrets |
| Public app distribution | Release-ready | Play Console account and release signing key required |

## Delivery sequence

1. Create Firebase project and enable Google provider.
2. Register the Android package and add debug/release SHA fingerprints.
3. Configure Vercel backend variables and managed PostgreSQL.
4. Run Alembic migrations and verify `/health`.
5. Build a signed internal-test AAB.
6. Verify password login, Google login, onboarding, daily logs, and logout on a
   real Android device.
7. Release to Google Play production or publish a signed APK through GitHub
   Releases.

## Known constraints

- Vercel functions are stateless and request-based; they are not a background
  worker or a file server for durable data.
- The in-memory rate limiter is per process. Use gateway-level protection for
  high-volume traffic.
- Health Connect is Android-specific and permission-dependent.
- Password reset still needs a production email delivery provider.
- Firebase and release signing credentials must be managed outside Git.
- The current app is Android-focused; iOS or web distribution needs platform
  configuration and separate QA.

## Go/no-go checklist

A production release is feasible when all of these are true:

- [ ] Vercel production deployment passes `/health`.
- [ ] PostgreSQL migrations are at the latest revision.
- [ ] Firebase Google sign-in succeeds on a release-signed build.
- [ ] API base URL uses a stable HTTPS domain.
- [ ] Token refresh and logout invalidate sessions correctly.
- [ ] Release APK/AAB is signed with the non-debug keystore.
- [ ] Backups, logs, error alerts, and rollback ownership are defined.
