# SwiftPost Agent Instructions

These instructions apply to work inside `H:\Blog_Webapp`. Backend code lives in `blogging-system-yt/`. Frontend code lives in `source/`.

## Current product (follow this, not old magazine-queue docs)

SwiftPost is a **writer platform**, not an invite-only magazine queue.

Confirmed in code:

- Django 5.2 + DRF modular monolith under `blogging-system-yt/apps/`. Custom `User` with `USERNAME_FIELD=email`.
- Next.js / React / TypeScript frontend in `source/`. Do not change frontend unless the user asks.
- Session cookies + CSRF. No JWT unless the user explicitly decides otherwise.
- SQLite locally. PostgreSQL in production when `DATABASE_URL` is set.
- **Signup creates `author`.** `admin` is assigned in Django admin. `reader` remains for demotion/tests only.
- Authors create private drafts, then **publish and unpublish their own complete posts**.
- Admins can **unpublish any live post**, manage categories, and disable users in Django admin.
- **AI never publishes.** Save, Composer, and Anna leave the post as `draft`.
- Composer uses `AI_MODEL_COMPOSE` (default `nvidia/nemotron-3-super-120b-a12b`). Anna review uses `AI_MODEL_REVIEW` (default `openai/gpt-5.5`).
- Composer browser UI is a conversation that creates/refines a private draft, renders it as an article, and auto-attaches 2–3 Tavily images.
- Anna browser UI is a **one-shot draft review** with a loading pipeline. Do not add a new Anna chat UI unless the user asks.
- Anna live research, Celery, Redis workers, retries, and job polling are **V2**. Do not add them unless asked.
- Public pages show only `published` posts. Cross-author private access returns a safe 404.

If a document and a user instruction conflict, follow the user's latest explicit instruction and update the docs.

## Required reading

Before backend changes, read:

- `docs/SWIFTPOST_REBUILD_PRD.md`
- `docs/TECH_STACK.md`
- `docs/BACKEND_IMPLEMENTATION.md`
- `docs/BACKEND_STATUS.md` — live API contract
- The current repository code and migrations for the change

## Repository layout

```text
H:\Blog_Webapp\
  README.md                    Short GitHub landing; full docs in docs/
  AGENTS.md                    Pointer to docs/AGENTS.md
  docs/                        All project markdown
  blogging-system-yt/          Django API
    config/
    apps/accounts, users, blogs, categories, comments,
         publishing, moderation, media_assets, composer, anna, common
  source/                      Next.js UI
```

The old `blog_main`, `dashboards`, `assignments`, and server-rendered templates are gone.

## Scope

### In scope now

- Public discovery, categories, search, pagination.
- Register/login/logout/`/me`, session security.
- Author drafts, editor, Stories list, publish/unpublish, archive.
- Comments and likes on published posts. Any signed-in user can comment; comments are public immediately.
- Featured image upload and Tavily live-image suggestions (Composer auto-attaches 2–3; authors can still multi-select save).
- Composer conversations → private draft. Anna one-shot review.
- DRF under `/api/v1/`.

### Out of scope unless asked

- Flask, microservices, multi-tenant workspaces.
- Reader-side AI.
- Autonomous publishing.
- LangGraph / Celery / Redis / Anna live research (V2).
- Payments, native apps, video, Web3.
- Unrequested frontend redesign.
- Re-adding Anna chat sidebar after the user asked it removed.

## Architecture

Django owns business rules, auth, authorization, models, publishing, media, and AI adapters. Next.js owns presentation. The browser is not the security boundary.

Keep a small public interface. Put workflows in application services, not views/serializers. Provider SDKs stay in adapters (`LLMProvider`, `SearchProvider`).

## AuthZ checks (every sensitive operation)

1. Authentication
2. Role
3. Object ownership (or explicit admin scope)
4. Current object status
5. Input / transition validity

Authors may manage only their own posts, drafts, conversations, sources, and artifacts. UI hiding is never a security control.

## API

New APIs stay under `/api/v1/`. JSON errors:

```json
{"error": {"code": "POST_NOT_FOUND", "message": "The requested post could not be found.", "details": {}}}
```

Do not expose stack traces, SQL, provider payloads, API keys, or private records.

Live groups (see `docs/BACKEND_STATUS.md` for the contract):

- `/api/v1/auth/`
- `/api/v1/blogs/`, `/api/v1/drafts/`
- `/api/v1/categories/`
- `/api/v1/comments/`, likes on `/api/v1/blogs/{id}/likes/`
- `/api/v1/media/`
- `POST /api/v1/blogs/{id}/publish|unpublish|submit|archive/`
- `/api/v1/ai/compose/`, `/api/v1/ai/composer/conversations/`
- `/api/v1/ai/reviews/`, `/api/v1/ai/anna/conversations/` (Anna conversation API exists; current UI uses `/reviews/`)

Do not invent `/api/v1/ai/jobs/` or research job polling in V1.

## Publishing

```text
draft / unpublished / changes_requested / in_review
        │  owning author (or admin) Publish
        ▼
    published  ── owner or admin Unpublish ──► unpublished

draft / in_review / changes_requested / unpublished → archived
```

- Save and AI generation do not make a post public.
- Publish requires title, excerpt, body, and an active category.
- `submit` / `in_review` still exist in the API for leftover rows; the writer UI publishes directly.
- Publishing actions write `PublishingEvent` rows.

## Anna and Composer

Composer may create and refine a detailed private draft from a title or follow-up. After the draft exists it searches Tavily and auto-attaches 2–3 relevant live images. It must not publish.

Anna may review an owned draft and return notes. She must not publish, rewrite the live post silently, or read another author's draft.

LangChain stays behind the LLM adapter. Tavily stays behind the search adapter. Never call providers from frontend code. Re-check ownership inside every AI request.

## Media

- Local files in development; S3-compatible storage in production.
- Validate MIME, extension, size, dimensions. Server-controlled keys.
- One featured image per post plus up to two extra story images (three total). Composer auto-attaches 2–3 Tavily hits; the first becomes featured. Authors can still search, upload, or replace them.

## Security

Protect passwords, sessions, DB credentials, AI/search keys, private drafts, uploads. Never log secrets or full private drafts. CSRF on unsafe requests. Narrow CORS.

## Workflow

Before editing: read the docs above, inspect current code/migrations, check git status, plan large changes.

During editing: smallest coherent change, no unrelated rewrites, no hardcoded secrets, migrations + tests for behavior changes.

After editing, prefer `rtk` in PowerShell:

```powershell
rtk python manage.py check
rtk python manage.py makemigrations --check
rtk python manage.py test
```

Use the project `venv` if it is the user's environment. Do not claim browser E2E from unit tests alone.

## Tests

Cover auth, role and object authorization, cross-author 404/403, public vs draft privacy, publish/unpublish, validation, mocked provider failures, and **no automatic publishing**.

Do not require live Tavily/LLM unless `ANNA_LIVE_PROVIDER_TEST=1`.

## Docs

When behavior changes, update `docs/SWIFTPOST_REBUILD_PRD.md`, `docs/TECH_STACK.md`, `docs/BACKEND_IMPLEMENTATION.md`, `docs/BACKEND_STATUS.md`, and `.env.example` (names only). Keep confirmed decisions separate from recommendations.

## Completion report

1. What changed
2. Files changed
3. Tests/checks and results
4. Migration or deploy notes
5. Unresolved risks / next steps
