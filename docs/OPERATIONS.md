# Visibility and operations

## Health and deployment checks

- `GET /health` confirms the Vercel function is alive without querying the
  database.
- Check Vercel function logs after each deployment.
- Check database connectivity by running a migration or a protected API smoke
  test.
- Keep `/docs` disabled in production with `DEBUG=false`.

## Minimum production visibility

| Signal | Source | Action |
| --- | --- | --- |
| Function errors and latency | Vercel logs/metrics | Investigate deployment or dependency errors |
| Database availability | Managed PostgreSQL provider | Check connections, pool limits, and backups |
| Authentication failures | API logs and rate limits | Look for abuse or Firebase configuration errors |
| 5xx responses | Vercel/API monitoring | Roll back or disable the affected feature |
| Mobile crashes | Play Console or release tester reports | Reproduce with the same app version |

Do not log passwords, Firebase service-account values, access tokens, refresh
tokens, raw health records, or full request bodies.

## Backup and recovery

- Enable managed PostgreSQL automated backups and point-in-time recovery when
  available.
- Test restoring a backup before the first public release.
- Keep migration files in Git and record the deployed revision.
- Roll back the Vercel deployment if application code is faulty; do not delete
  database data to recover from an application rollback.

## Incident response

1. Confirm the issue with `/health`, Vercel logs, and the database provider.
2. If authentication is affected, check Firebase provider status and the
   service-account environment variables.
3. Roll back the last Vercel deployment when the regression is code-related.
4. Rotate JWT/Firebase credentials if a secret may have been exposed.
5. Record the incident, affected versions, root cause, and recovery action.

## Release smoke test

```text
1. Open the release app.
2. Sign in with Google.
3. Complete onboarding.
4. Submit a daily check-in.
5. Reload and confirm the session persists.
6. Check the dashboard and one analytics view.
7. Log out and confirm protected routes require sign-in.
8. Verify the backend /health endpoint.
```
