# AarogyaDrishti documentation

This folder contains the project guides that are too detailed for the root
README.

## Start here

| Need | Guide |
| --- | --- |
| Understand the system | [Architecture](ARCHITECTURE.md) |
| Follow user and data flows | [Workflows](WORKFLOWS.md) |
| Understand the implementation | [Implementation](IMPLEMENTATION.md) |
| Deploy the FastAPI backend | [Backend hosting on Vercel](VERCEL.md) |
| Publish the Flutter app | [Frontend/mobile hosting](MOBILE_RELEASE.md) |
| Evaluate scope and delivery risk | [Feasibility](FEASIBILITY.md) |
| Operate and inspect the system | [Visibility and operations](OPERATIONS.md) |

## Runtime boundary

- `backend/` is the production API. It runs FastAPI through Vercel's Python
  serverless runtime and connects to managed PostgreSQL.
- `mobile/` is the Flutter Android client. It is distributed through Google
  Play for public users or GitHub Releases for direct APK downloads.
- Firebase provides Google identity verification. AarogyaDrishti exchanges the
  Firebase ID token for its own short-lived access and refresh tokens.

## Documentation conventions

- Deployment secrets are represented as placeholders only. Never commit real
  Firebase service-account keys, signing keys, database URLs, or JWT secrets.
- Mermaid diagrams describe the implemented direction, not future marketing
  architecture.
- `README.md` remains the short onboarding guide; update the focused document
  when operational details change.
