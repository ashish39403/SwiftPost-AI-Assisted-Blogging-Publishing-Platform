# Contributing to SwiftPost

SwiftPost is a Django REST Framework backend (`blogging-system-yt/`) and a Next.js frontend (`source/`). Follow these conventions before opening a pull request.

## Required reading (before any change)

1. `docs/AGENTS.md` — product conventions and authz rules.
2. `docs/SWIFTPOST_REBUILD_PRD.md` — product scope and acceptance criteria.
3. `docs/BACKEND_IMPLEMENTATION.md` — backend implementation plan.
4. `docs/TECH_STACK.md` — architecture baseline.
5. `docs/BACKEND_STATUS.md` — live API contract.

## Product rules (non-negotiable)

- Signup creates `author`. `admin` is assigned in Django admin; `reader` is for demotion/tests.
- AI never publishes. Composer and Anna leave posts as `draft`.
- Session cookies + CSRF. No JWT unless the user decides otherwise.
- SQLite locally; PostgreSQL in production when `DATABASE_URL` is set.
- New APIs stay under `/api/v1/`. Errors use the `{"error": {"code": ..., "message": ..., "details": {}}}` envelope.
- Provider SDKs stay in adapters (`LLMProvider`, `SearchProvider`). Never call providers from the frontend.
- Authors manage only their own posts, drafts, conversations, sources, and artifacts. UI hiding is not a security control.

## How to contribute

1. Fork the repository and create a feature branch from `master`.
2. Make the smallest coherent change. No unrelated rewrites.
3. Add or update migrations and tests for behavior changes.
4. Run the checks below. All must pass.
5. Update docs when behavior changes (`docs/SWIFTPOST_REBUILD_PRD.md`, `docs/TECH_STACK.md`, `docs/BACKEND_IMPLEMENTATION.md`, `docs/BACKEND_STATUS.md`, `.env.example` names only).
6. Open a pull request linking the issue and describing what changed, how it was tested, and any deploy notes.

## Backend checks (run in `blogging-system-yt`)

```powershell
python manage.py check
python manage.py makemigrations --check
python manage.py test
```

Tests cover auth, role and object authorization, cross-author 404/403, public vs draft privacy, publish/unpublish, validation, mocked provider failures, and no automatic publishing. Do not require live Tavily/LLM unless `ANNA_LIVE_PROVIDER_TEST=1`.

## Frontend checks (run in `source`)

```powershell
npm run lint
npx tsc --noEmit
npm run build
```

## Secrets

- Never commit `.env`, `.env.local`, or real provider keys.
- `.env.example` contains names and placeholders only.
- If you add a new env var, add its name (no real value) to `.env.example`.

## Pull request checklist

- [ ] Tests added/updated for behavior changes
- [ ] `python manage.py check`, `makemigrations --check`, `test` pass
- [ ] `npm run lint`, `tsc --noEmit`, `npm run build` pass
- [ ] Docs updated for any behavior change
- [ ] No secrets or real credentials committed
- [ ] No Flask, microservices, multi-tenancy, reader-side AI, or unrequested frontend redesign (out of scope unless asked)

## Code of conduct

Be respectful, keep changes small and reviewable, and follow the authorization-first principle: every sensitive operation checks authentication, role, ownership, object status, and input validity — on direct API requests, not only through the UI.
