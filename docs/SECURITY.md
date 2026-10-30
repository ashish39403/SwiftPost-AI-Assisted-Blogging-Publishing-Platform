# SwiftPost Security Policy

## Supported versions

| Version | Status | Notes |
|---------|--------|-------|
| V1 (current) | Supported | Session-auth Django REST API + Next.js frontend |

## Security basics

SwiftPost is a **writer platform**, not a magazine queue. Security boundaries:

- **Django is the security boundary.** The Next.js browser is presentation only and never receives database, Tavily, LLM, or object-storage credentials.
- **Authentication:** Django session cookies (`sessionid`, `csrftoken`), HTTP-only, CSRF on unsafe requests. No JWT unless a product decision explicitly adds it.
- **Authorization:** authentication → role → object ownership/admin scope → current object status → input/transition validity. Enforced server-side on every sensitive endpoint; UI hiding is never a security control.
- **Secrets:** backend-only, injected via environment or secret manager. Never committed, never logged, never bundled to the frontend.
- **Public data:** only `published` posts are discoverable. Drafts and private AI records return a safe 404 to non-owners.

## Secrets that must never be committed

These live only in local `.env` files (gitignored) or a production secret manager:

- `DJANGO_SECRET_KEY`
- `AI_PROVIDER_API_KEY` (LLM provider)
- `TAVILY_API_KEY` (search / live image suggestions)
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (object storage)
- `DATABASE_URL` (production PostgreSQL credentials)
- Session cookies / CSRF tokens

If a secret is accidentally committed, **rotate it immediately** and remove it from git history (e.g. `git filter-repo` or BFG Repo-Cleaner) before pushing.

## Production checklist

- [ ] `DJANGO_ENV=prod`, `DJANGO_DEBUG=False`
- [ ] `DJANGO_SECRET_KEY` set from secret manager (never hardcoded)
- [ ] `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` explicit (no wildcards)
- [ ] `DJANGO_CORS_ALLOWED_ORIGINS` restricted to deployed frontend origin(s)
- [ ] `DATABASE_URL` points to PostgreSQL (never SQLite in production)
- [ ] `MEDIA_STORAGE=s3` with `AWS_S3_BUCKET` and `AWS_S3_PUBLIC_BASE_URL`
- [ ] `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`
- [ ] `SECRET_KEY` differs from the development value
- [ ] Provider keys present but not in source control
- [ ] `.env` and `.env.local` are gitignored
- [ ] Health endpoint `GET /api/v1/health/` reachable
- [ ] Migrations applied; `makemigrations --check` clean
- [ ] Backend tests and frontend `lint`/`build` pass

## Reporting a vulnerability

Do **not** open a public issue for security vulnerabilities.

Contact the repository maintainer through GitHub private vulnerability reporting (Security tab → "Report a security vulnerability") or email the maintainer directly.

Include:
- Affected component and version
- Steps to reproduce
- Impact assessment
- Suggested fix (if you have one)

## Disclosure

We will acknowledge receipt within 5 business days and provide an initial assessment within 10 business days. Coordinated public disclosure is preferred after a fix is released.

## Additional reading

- `docs/AGENTS.md` — agent/product conventions
- `docs/SWIFTPOST_REBUILD_PRD.md` — product requirements and trust boundaries
- `docs/BACKEND_STATUS.md` — live API contract
- `docs/TECH_STACK.md` — architecture and security requirements
