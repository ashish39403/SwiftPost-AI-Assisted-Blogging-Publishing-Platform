# SwiftPost E2E Deployment Plan

Status: deployment runbook and release gate plan. This is not a claim that production is already deployed.

This runbook is for the current SwiftPost V1: Django REST API + Next.js web app, session authentication, PostgreSQL in production, S3-compatible media, Composer drafting, and one-shot Anna review. Celery/Redis research/background jobs, persisted Anna chat UI, moderation expansion, and other V2 work are intentionally not deployment prerequisites for V1.

## 1. Target production topology

```text
Browser (HTTPS)
    |
    +--> Next.js server (web UI)
    |        |
    |        +--> same-origin /api and /media proxy, or explicit API origin
    |
    +--> Django WSGI process (Gunicorn, behind TLS reverse proxy)
              |
              +--> PostgreSQL / RDS
              +--> S3-compatible object storage (media)
              +--> AI Credits provider (Composer + Anna)
              +--> Tavily/search provider (only where the current V1 path uses it)
```

The hosting vendor, domain names, CDN, and secret manager are not fixed by the product documents. Select them before the release candidate and record the decision in the deployment ticket. Do not expose Django, PostgreSQL, S3 credentials, or provider keys to the browser.

## 2. Current release boundary

### Deploy in V1

- Registration, login, logout, session/current-user behavior.
- Author-owned drafts, editor updates, category assignment, image selection, save, submit/review, publish, unpublish, archive/delete behavior supported by the current API.
- Public published-story discovery, search/categories, comments/likes where enabled by the current build.
- Composer durable author conversation and private-draft generation. Composer never publishes.
- Anna’s current browser review flow. Anna never publishes.
- Admin access and explicit object-level authorization.

### Do not accidentally make V1 a dependency on

- Celery/Redis research jobs, retries, polling, or a job queue that the current V1 does not require.
- Autonomous publishing, reader-side AI, multi-tenancy, payments, or vector search.
- A frontend-only security decision. Django remains the authorization boundary.

## 3. Release blockers to close before production

1. **Production server command:** `requirements.txt` currently does not pin Gunicorn even though the deployment docs specify Gunicorn/WSGI. Add and lock the chosen WSGI server (or explicitly choose and document another production server) before deploying.
2. **Settings selection:** set `DJANGO_ENV=prod`/`production`; `config.settings` then imports strict production settings. Never run the development server in production.
3. **Database:** provision PostgreSQL, rehearse the SQLite-to-PostgreSQL migration, verify counts/relationships/owners/slugs/statuses, and take a restore-tested backup.
4. **Media:** provision an S3-compatible bucket, private credentials, safe public/read URL strategy, upload limits, and orphan/deletion handling. Local `MEDIA_ROOT` is not a production media strategy.
5. **Origin and cookies:** decide whether the web app and API are same-origin or separate origins. Configure exact HTTPS `FRONTEND_ORIGIN`, CORS origins, CSRF trusted origins, allowed hosts, cookie SameSite, and secure cookies.
6. **Frontend routing:** `source/next.config.ts` currently rewrites `/api/*` and `/media/*` to `127.0.0.1:8000`. Keep that only when Next and Django share the same host/network. Otherwise replace the production routing with the selected API origin/proxy configuration and test cookies plus CSRF.
7. **AI provider:** configure the production AI Credits base URL/key and the intended model values. Confirm Composer uses the configured Nemotron model and Anna uses the configured review model; never hardcode keys.
8. **Browser E2E:** run the release smoke matrix below against the deployed candidate with real author, reader, and admin test accounts. Unit tests alone are not E2E verification.
9. **Operations:** define error monitoring, access-log retention, database backup alerts, uptime checks, key rotation, and an owner for rollback. Rate limiting and abuse controls remain a production hardening item if not yet implemented.

## 4. Environment contract

Set secrets through the host secret manager, not committed files. Values below are names and examples only.

### Django/backend

| Variable | Production requirement |
|---|---|
| `DJANGO_ENV` | `prod` or `production` |
| `DJANGO_DEBUG` | `false` |
| `DJANGO_SECRET_KEY` | long, random, unique secret; rotate if exposed |
| `DJANGO_ALLOWED_HOSTS` | exact API/web hostnames, comma-separated |
| `FRONTEND_ORIGIN` | exact HTTPS browser origin |
| `DJANGO_CORS_ALLOWED_ORIGINS` | exact frontend origin(s), no wildcard with cookies |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | exact HTTPS origin(s) that submit unsafe requests |
| `DATABASE_URL` | managed PostgreSQL/RDS URL; TLS as required by provider |
| `MEDIA_STORAGE` | `s3` |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | backend-only least-privilege credentials |
| `AWS_REGION`, `AWS_S3_BUCKET` | production bucket/region |
| `AWS_S3_ENDPOINT_URL` | set for non-AWS S3-compatible storage, otherwise blank |
| `AWS_S3_PUBLIC_BASE_URL` | approved public/read base URL |
| `MAX_IMAGE_BYTES`, `MAX_IMAGE_EDGE` | retain validated upload limits |
| `AI_PROVIDER`, `AI_PROVIDER_BASE_URL`, `AI_PROVIDER_API_KEY` | production AI Credits connection |
| `AI_MODEL_COMPOSE` | approved NVIDIA Nemotron model identifier |
| `AI_MODEL_REVIEW` | approved Anna review model identifier |
| `SEARCH_PROVIDER`, `TAVILY_API_KEY`, `TAVILY_MAX_RESULTS` | only if enabled by the deployed V1 path |

`REDIS_URL`, `CELERY_BROKER_URL`, and job-inline flags are V2 infrastructure unless the deployed code path explicitly enables them. Do not make them an accidental V1 outage dependency.

### Next.js/frontend

| Variable | Production requirement |
|---|---|
| `NEXT_PUBLIC_SITE_URL` | final HTTPS web URL |
| `NEXT_PUBLIC_API_URL` | API origin when not using same-origin `/api` proxy; otherwise intentionally blank/relative |

Set public variables before `npm run build` when they are compiled into the Next bundle. Do not put private provider/database credentials in `NEXT_PUBLIC_*` variables.

## 5. Pre-release source and dependency checks

Run from the repository roots and save the outputs as CI artifacts:

```powershell
rtk python manage.py check
rtk python manage.py check --deploy
rtk python manage.py makemigrations --check
rtk python manage.py test
rtk npm ci
rtk npm run lint
rtk npx tsc --noEmit
rtk npm run build
```

Run Django commands from `H:\Blog_Webapp\blogging-system-yt` and npm commands from `H:\Blog_Webapp\source`. Use the project virtual environment. If a check cannot run because a service or dependency is absent, record it as pending rather than marking the release green.

Before the release candidate, inspect `git status`, confirm no `.env`, database dump, uploaded media, or provider response is tracked, and review the dependency diff. Add the pinned production web server before building the backend artifact.

## 6. Database migration and cutover

1. Freeze schema-changing work for the release candidate and create a timestamped backup of the current SQLite database and `media/` directory.
2. Provision a disposable PostgreSQL database matching production major version.
3. Apply Django migrations to the disposable database.
4. Import a scrubbed copy of current data using a repeatable export/import procedure. Preserve users, ownership, categories, post statuses, slugs, conversations, messages, and media references.
5. Verify row counts, foreign-key relationships, author ownership, draft privacy, published visibility, unique slugs, and media object keys.
6. Run the complete test suite against PostgreSQL as well as SQLite.
7. Take a final production backup, put the app in maintenance/read-only mode if needed, run `migrate --noinput`, and deploy the matching application artifact.
8. Keep the original backup until post-cutover verification and the rollback window have passed. Never delete source data to force a migration through.

Production migration command:

```powershell
rtk python manage.py migrate --noinput
```

## 7. Backend build, static files, and process

From `H:\Blog_Webapp\blogging-system-yt`:

```powershell
rtk python -m pip install -r requirements.txt
rtk python manage.py check --deploy
rtk python manage.py collectstatic --noinput
rtk python manage.py migrate --noinput
rtk gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 180
```

The final command is valid only after Gunicorn is added to the pinned backend dependencies. Run it behind an HTTPS reverse proxy with health checks, graceful restart, request size limits at least as large as the configured image limit, and forwarded-proto handling that preserves secure-cookie behavior.

Health probes:

- `GET /health/`
- `GET /api/v1/health/`

Both should return a safe success response without exposing configuration or secrets. Serve collected static files through the chosen web server/CDN. Serve media through the configured S3 strategy, not Django’s development `static()` helper.

## 8. Frontend build and process

From `H:\Blog_Webapp\source`:

```powershell
rtk npm ci
rtk npm run lint
rtk npx tsc --noEmit
rtk npm run build
rtk npm run start
```

Run Next behind HTTPS and the selected reverse proxy. Verify that `/api` and `/media` resolve to the real backend/storage path in production; the local `127.0.0.1:8000` rewrite must not silently point at the wrong container or host. Verify that session cookies and CSRF tokens survive navigation, refresh, and an unsafe request.

## 9. Reverse proxy and TLS requirements

- Redirect HTTP to HTTPS and enable HSTS only after HTTPS is confirmed everywhere.
- Route web traffic to Next and API traffic to Django according to the same-origin/separate-origin decision.
- Preserve `Host`, `X-Forwarded-Proto`, and client request IDs.
- Allow the maximum configured image upload size and return bounded, safe errors.
- Do not cache authenticated HTML/API responses or private draft/media responses publicly.
- Terminate TLS with an automatically renewed certificate and test expiry alerts.

## 10. E2E release smoke matrix

Use a fresh test author, reader, and admin. Capture request IDs, screenshots, and pass/fail evidence.

| Area | Required verification |
|---|---|
| Public | Anonymous user can load the site, browse published stories, search/filter, and cannot see drafts. |
| Auth | Signup creates the expected author role; login establishes a session; refresh retains it; logout invalidates it. |
| CSRF | Safe GET works; unsafe POST/PATCH/DELETE with the app’s CSRF flow works; a missing/invalid token is rejected safely. |
| Author draft | Author creates a draft, selects a valid category, uploads/selects one or more allowed images, saves, refreshes, and sees the same content. |
| Ownership | Author A cannot read or mutate Author B’s private draft, Composer conversation, Anna context, or media. |
| Composer | Title creates a durable author-owned conversation and private draft; follow-up continues the same conversation; Composer never publishes automatically. |
| Anna | Review opens for eligible author content, returns a bounded result/error state, preserves the draft, and does not publish. |
| Publishing | Complete draft follows the documented state transition; publish makes it public; unpublish removes it from public queries; edit/save remains owner-scoped. |
| Admin | Admin can access admin-only operations and unpublish/moderate according to the current API; ordinary authors cannot. |
| Media | Uploaded image is validated, stored in S3, readable through the approved URL, and remains linked after refresh. |
| Failure recovery | Provider timeout, invalid AI output, expired session, duplicate submit, and unavailable media return safe errors and do not overwrite approved content. |
| Mobile | Test the primary author flow at phone width: nav, editor, Composer results/images, Anna review, save, publish, and back/refresh. |

The release is not E2E-green until every required row has an observed result in the deployed environment.

## 11. Rollback plan

1. Stop promotion and mark the release unhealthy if health checks or smoke tests fail.
2. Roll back Next to the previous known-good build and Django to the previous application artifact.
3. Do not automatically reverse migrations. Use a tested backward migration only when it is explicitly safe; otherwise restore the database backup into a controlled rollback database and switch traffic.
4. Keep media objects immutable during rollback; restore only missing objects from the media backup.
5. Disable or rotate the affected AI/search credential if a provider integration is the failure source.
6. Re-run health probes and the critical auth/draft/publish smoke tests before reopening traffic.
7. Record the incident, failing request IDs, data impact, and the corrective release gate.

## 12. CI/CD promotion order

1. Pull request: lint, type-check, Django checks, migration check, unit/integration tests, and secret scan.
2. Build immutable backend and frontend artifacts with a version/commit identifier.
3. Deploy to a staging environment with PostgreSQL, S3-compatible storage, and non-production provider keys.
4. Run the E2E smoke matrix and a migration/restore rehearsal in staging.
5. Approve production promotion only when all blockers are closed and the checklist is signed.
6. Run database migration, deploy backend, deploy frontend, probe health, then run smoke tests.
7. Monitor error rate, latency, login failures, publish failures, AI provider failures, database health, storage failures, and 5xx responses for the rollback window.

## 13. Final go/no-go checklist

- [ ] Hosting, domain, TLS, proxy routes, and rollback owner are recorded.
- [ ] Gunicorn (or the chosen production server) is pinned and built.
- [ ] Production settings load with `DJANGO_ENV=prod` and `DJANGO_DEBUG=false`.
- [ ] `DJANGO_SECRET_KEY`, database, AI, search, and S3 secrets come from a secret manager.
- [ ] Allowed hosts, CORS, CSRF, cookie SameSite, and secure cookies were tested from the real HTTPS origin.
- [ ] PostgreSQL migration and restore rehearsal passed.
- [ ] S3 upload/read/delete/orphan behavior passed.
- [ ] Static collection and frontend production build passed.
- [ ] `/health/` and `/api/v1/health/` pass through the proxy.
- [ ] Author, reader, admin, Composer, Anna, draft, publish, unpublish, media, and mobile smoke tests passed.
- [ ] Monitoring, backups, key rotation, and rollback procedure have named owners.
- [ ] No unresolved blocker is being waived silently.

If any unchecked item is required for the chosen hosting topology, do not deploy yet; resolve it or record an explicit, approved exception with a rollback date.

