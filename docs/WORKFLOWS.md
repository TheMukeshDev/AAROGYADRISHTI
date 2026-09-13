# Product and system workflows

## Google sign-in

```mermaid
sequenceDiagram
    actor User
    participant App as Flutter app
    participant Google as Google/Firebase Auth
    participant API as FastAPI /auth/firebase
    participant DB as PostgreSQL

    User->>App: Tap Continue with Google
    App->>Google: Sign in with Google credential
    Google-->>App: Firebase ID token
    App->>API: POST /api/v1/auth/firebase
    API->>Google: Verify ID token with Firebase Admin
    Google-->>API: Trusted email, name, verified claims
    API->>DB: Find or provision user
    API-->>App: AarogyaDrishti access + refresh JWTs
    App->>App: Store tokens securely
```

The API accepts only a verified Firebase ID token at this exchange endpoint. All
subsequent protected requests use the app-issued bearer token.

## Daily check-in and insight flow

```mermaid
flowchart TD
    Start[User opens check-in] --> Input[Enter sleep, energy, stress, food, water, mood, or exercise]
    Input --> Save[POST /api/v1/daily-logs]
    Save --> Store[(User-scoped daily log)]
    Store --> Baseline[Compute baseline window]
    Baseline --> Patterns[Consistency, adherence, and pattern analysis]
    Patterns --> Dashboard[Dashboard aggregates and insights]
    Dashboard --> Experiment[Recommend or evaluate personal experiment]
    Experiment --> Learning[Personal learning candidate]
    Learning --> Coach[Optional coach summary/action]
```

Unknown values remain `NULL`; the analytics layer does not convert missing data
to zero.

## Health Connect sync

1. The user grants selected Android Health Connect permissions.
2. The app reads supported observations only after consent.
3. The app sends normalized values to the API.
4. The API merges device values into the user's daily row without overwriting a
   known manual value with an unknown value.
5. Analytics recompute from the resulting user-scoped dataset.

Health Connect is best-effort. Manual tracking remains available when the
provider is unavailable or permission is denied.

## Session lifecycle

```mermaid
stateDiagram-v2
    [*] --> Unknown: App starts
    Unknown --> Authenticated: Secure tokens restored
    Unknown --> Unauthenticated: No tokens
    Unauthenticated --> Authenticated: Password or Google login
    Authenticated --> Authenticated: Refresh token rotation
    Authenticated --> Unauthenticated: Logout, reset, invalid token
```

## Release flow

```mermaid
flowchart LR
    Commit[Git commit] --> Backend[Vercel backend deployment]
    Backend --> Migrate[Run Alembic migrations]
    Migrate --> Health[Verify /health]
    Commit --> Flutter[Flutter release build]
    Flutter --> Play[Google Play AAB]
    Flutter --> APK[GitHub Release APK]
    Health --> App[Mobile points to HTTPS API]
    Play --> User[Public users]
    APK --> User
```
