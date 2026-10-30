# SwiftPost

**SwiftPost** is a secure, role-based **writer platform**: a **Django 5.2 + Django REST Framework** modular monolith (`blogging-system-yt/`) and a **Next.js 16 / React 19 / TypeScript** frontend (`source/`).

Signup creates an **author**. Authors write private drafts, review them with **Anna**, refine them with **Composer**, and click **Publish** themselves. **AI never publishes.** Admins can unpublish any live post and manage categories and users through Django admin.

[![Backend: Django 5.2 + DRF](https://img.shields.io/badge/backend-Django%205.2%20%2B%20DRF-blue)](blogging-system-yt/)
[![Frontend: Next.js 16](https://img.shields.io/badge/frontend-Next.js%2016-black)](source/)
[![Auth: Session + CSRF](https://img.shields.io/badge/auth-Session%20%2B%20CSRF-green)](blogging-system-yt/config/settings/)
[![Database: SQLite dev / PostgreSQL prod](https://img.shields.io/badge/db-SQLite%20%7C%20PostgreSQL-orange)](blogging-system-yt/)

---

## Table of contents

- [What SwiftPost is](#what-swiftpost-is)
- [Repository structure](#repository-structure)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Quick start (local development)](#quick-start-local-development)
- [Environment variables](#environment-variables)
- [Running with Docker services](#running-with-docker-services)
- [API overview](#api-overview)
- [Frontend](#frontend)
- [Testing](#testing)
- [Production deployment](#production-deployment)
- [Production deployment checklist](#production-deployment-checklist)
- [Security](#security)
- [Known issues](#known-issues)
- [Contributing](#contributing)
- [License](#license)

---

## What SwiftPost is

SwiftPost is a **single-platform, non-multi-tenant** publishing product for writers.

| Capability | Who | Behavior |
|---|---|---|
| Public discovery | Everyone | Only `published` posts appear on Discover, search, category, and post detail |
| Register / login / logout | Everyone | Self-registration creates an `author`; `admin` is assigned in Django admin |
| Author drafts | Author | Create, edit, save, unpublish, archive own drafts/posts (private) |
| Publish / unpublish | Author (own) or Admin (any) | Explicit action; creates a `PublishingEvent` audit row |
| Composer (AI writing) | Author | Conversation → private draft (Nemotron); optional Tavily image suggestions; never publishes |
| Anna review (AI) | Author | One-shot draft review (GPT-5.5); returns verdict/strengths/gaps/edits; never publishes |
| Comments + likes | Authenticated users | Comment on published posts (live immediately); like toggle |
| Media | Author | Featured image upload with MIME/size/dimension validation; server-controlled keys |

### Key trust boundaries

- **AI never publishes.** Save, Composer, and Anna all leave the post as `draft`. Only an explicit, authorized publish transition makes content public.
- **Ownership is server-enforced.** An author cannot read, edit, publish, or use another author's private draft, post, conversation, source, or artifact — even via a direct API call with a guessed ID.
- **The browser is not the security boundary.** Django enforces auth, role, ownership, object status, and transition validity on every sensitive request.

---

## Repository structure

```
H:\Blog_Webapp                 # One git repository (this root)
├── .gitignore                 # Python + Node + OS + secrets (never commit .env / media / db)
├── .env.example               # Combined names + placeholders (copy into local .env files)
├── README.md                  # This file
├── SECURITY.md                # Security policy, production checklist, vulnerability reporting
├── CONTRIBUTING.md            # Contribution conventions and required checks
├── AGENTS.md                  # Product conventions for agents and contributors
├── SWIFTPOST_REBUILD_PRD.md   # Product requirements & acceptance criteria
├── BACKEND_IMPLEMENTATION.md  # Backend implementation plan
├── docs/
│   └── AI_CONVERSATION_V1.md  # Composer chat + Anna one-shot review contract
├── blogging-system-yt/        # Django 5.2 + DRF API
│   ├── config/                # Settings (base/local/production), URLs, WSGI/ASGI
│   ├── apps/                  # accounts, users, blogs, categories, comments,
│   │                           publishing, moderation, media_assets, composer, anna, common
│   ├── tests/                 # integration + security tests
│   ├── TECH_STACK.md          # Architecture baseline
│   ├── BACKEND_STATUS.md      # Live API contract
│   ├── requirements.txt
│   ├── docker-compose.yml     # Optional PostgreSQL 16 + Redis 7
│   ├── manage.py
│   └── .env.example           # Backend env template (copy to .env locally)
└── source/                    # Next.js frontend
    ├── src/                   # App Router, features, components, lib
    ├── public/landing/        # Landing photography
    ├── package.json
    ├── next.config.ts         # API/media rewrite proxy to Django :8000
    └── .env.example           # Frontend env template (copy to .env.local locally)
```

Local `.env`, `.env.local`, SQLite, `venv` / `.venv`, `node_modules`, `.next`, and uploaded media stay on disk and are gitignored. Do not commit them.

---

## Architecture

SwiftPost is a **modular Django monolith**, not microservices. Django owns business logic, auth, authorization, models, migrations, publishing, media coordination, and AI orchestration. Next.js owns presentation and browser interaction and is **not** the security boundary.

```text
┌─────────────────────┐        /api/v1/*        ┌──────────────────────────┐
│  Next.js frontend   │  ──── (dev proxy) ─────▶ │  Django + DRF API        │
│  (source/)          │  ◀── session cookie ────  │  (blogging-system-yt)    │
└─────────────────────┘                          └───────────┬─────────────┘
                                                            │
                                          ┌─────────────────┴─────────────────┐
                                          ▼                                   ▼
                                    SQLite (dev)                     PostgreSQL (prod)
                                    local media/                     S3-compatible storage
                                                                           AICredits LLM + Tavily
```

Backend modules: `accounts`, `users`/`roles`, `blogs`, `categories`, `comments`, `publishing`, `moderation`, `media_assets`, `composer`, `anna`, `common`.

### Post lifecycle

```text
draft / unpublished / changes_requested / in_review
        │  owning author (or admin) Publish
        ▼
    published  ─── owner or admin Unpublish ───► unpublished

draft / in_review / changes_requested / unpublished ───► archived
```

- Saving a draft and AI generation do **not** make a post public.
- Publish requires title, excerpt, body, and an active category.
- Publishing actions write `PublishingEvent` rows (audit trail).

---

## Tech stack

**Backend**
- Python 3.10+, Django 5.2, Django REST Framework 3.15
- PostgreSQL (production) / SQLite (local dev)
- boto3 (S3-compatible storage), Pillow, httpx, python-dotenv
- Optional AI: LangChain, OpenAI-compatible providers (AICredits), Tavily search

**Frontend**
- Next.js 16.4, React 19.3, TypeScript 5
- Tailwind CSS 4, shadcn/ui, Radix UI
- lucide-react, tw-animate-css

**Infrastructure**
- Docker Compose for PostgreSQL 16 (and Redis 7 when V2 jobs exist)
- Gunicorn/WSGI for production behind a reverse proxy

---

## Prerequisites

- Python 3.10+
- Node.js 20+ (LTS recommended) and npm
- Git
- (Optional) Docker + Docker Compose for PostgreSQL/Redis

---

## Quick start (local development)

### 1. Backend (Django)

```powershell
cd blogging-system-yt
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a `.env` file in `blogging-system-yt/` from `.env.example`:

```env
DJANGO_ENV=dev
DJANGO_DEBUG=true
DJANGO_SECRET_KEY=dev-only-change-me
FRONTEND_ORIGIN=http://localhost:3000
```

Run migrations and start the server:

```powershell
python manage.py migrate
python manage.py createsuperuser   # creates an admin-role staff user
python manage.py runserver 8000
```

Backend is now at `http://127.0.0.1:8000`.

> `db.sqlite3` is gitignored and starts empty. You must run `migrate` before the public APIs will respond.

### 2. Frontend (Next.js)

```powershell
cd source
npm install
npm run dev
```

Frontend is now at `http://localhost:3000`. The dev server proxies `/api/*` and `/media/*` to the Django backend on `127.0.0.1:8000`.

Composer and Anna run **inline** in V1. Do not start Celery unless you are working on a V2 research-job slice.

---

## Environment variables

### Backend (`blogging-system-yt/.env`)

| Variable | Description | Default |
|---|---|---|
| `DJANGO_ENV` | `dev` or `prod` | `dev` |
| `DJANGO_DEBUG` | Enable debug mode | `true` (dev) |
| `DJANGO_SECRET_KEY` | Django secret key (required in prod) | — |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hosts | `localhost,127.0.0.1` |
| `FRONTEND_ORIGIN` | Frontend origin(s), comma-separated | `http://localhost:3000` |
| `DATABASE_URL` | PostgreSQL URL; empty → SQLite | (empty) |
| `MEDIA_STORAGE` | `local` or `s3` | `local` |
| `MAX_IMAGE_BYTES` | Max upload size in bytes | `5242880` |
| `MAX_IMAGE_EDGE` | Max image dimension | `4000` |
| `AWS_S3_BUCKET` | S3 bucket name | — |
| `AWS_REGION` | AWS region | — |
| `AWS_S3_ENDPOINT_URL` | S3-compatible endpoint | — |
| `AWS_S3_PUBLIC_BASE_URL` | Public base URL for media | — |
| `AWS_ACCESS_KEY_ID` | S3 access key | — |
| `AWS_SECRET_ACCESS_KEY` | S3 secret key | — |
| `DJANGO_CORS_ALLOWED_ORIGINS` | CORS origins | `FRONTEND_ORIGIN` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | CSRF trusted origins | `FRONTEND_ORIGIN` |
| `SESSION_COOKIE_SAMESITE` | Cookie SameSite | `Lax` |
| `CSRF_COOKIE_SAMESITE` | CSRF cookie SameSite | `Lax` |
| `AI_PROVIDER` | AI provider name | `openai_compatible` |
| `AI_MODEL` | Default model | — |
| `AI_MODEL_COMPOSE` | Composer model | `nvidia/nemotron-3-super-120b-a12b` |
| `AI_MODEL_REVIEW` | Review model | `openai/gpt-5.5` |
| `AI_PROVIDER_API_KEY` | Provider API key | — |
| `AI_PROVIDER_BASE_URL` | Provider base URL | `https://api.aicredits.in/v1` |
| `SEARCH_PROVIDER` | `tavily` or empty | `tavily` |
| `TAVILY_API_KEY` | Tavily API key | — |
| `TAVILY_MAX_RESULTS` | Max search results | `5` |

### Frontend (`source/.env.local`)

| Variable | Description | Default |
|---|---|---|
| `NEXT_PUBLIC_SITE_URL` | Public site URL | `http://localhost:3000` |
| `NEXT_PUBLIC_API_URL` | Backend API URL (empty in dev → proxy) | (empty) |

> Only `NEXT_PUBLIC_*` variables are exposed to the browser. Provider secrets and `DJANGO_SECRET_KEY` must remain backend-only.

---

## Running with Docker services

Start PostgreSQL and Redis:

```powershell
cd blogging-system-yt
docker compose up -d
```

Point the backend at them:

```env
DATABASE_URL=postgres://swiftpost:swiftpost@localhost:5432/swiftpost
```

Leave AI generation inline for V1. Redis/Celery are only needed for a future V2 research-job slice.

---

## API overview

All APIs live under `/api/v1/`. Authentication is session-based (cookie). Unsafe requests require CSRF. Errors follow a consistent envelope:

```json
{
  "error": {
    "code": "POST_NOT_FOUND",
    "message": "The requested post could not be found.",
    "details": {}
  }
}
```

| Group | Endpoints |
|---|---|
| Auth | `/api/v1/auth/` (register, login, logout, me, csrf, password change) |
| Users / Roles | `/api/v1/users/`, `/api/v1/roles/` |
| Blogs | `/api/v1/blogs/` (public published list, detail) |
| Drafts | `/api/v1/drafts/` (author drafts) |
| Categories | `/api/v1/categories/` |
| Comments | `/api/v1/comments/` |
| Likes | `/api/v1/blogs/{id}/likes/` |
| Media | `/api/v1/media/` (upload, search-images, suggestions) |
| Publishing | `POST /api/v1/blogs/{id}/publish/`, `/unpublish/`, `/archive/`, `/submit/` |
| Composer | `/api/v1/ai/compose/`, `/api/v1/ai/composer/conversations/` |
| Anna | `POST /api/v1/ai/reviews/` (current UI). Conversation APIs exist under `/api/v1/ai/anna/conversations/` |
| Health | `GET /api/v1/health/` → `{"status": "ok", "service": "swiftpost-api"}` |

Allowed browser origin defaults to `http://localhost:3000`. Trailing slashes are required.

---

## Frontend

The frontend is a separate Next.js app in `source/`. It consumes the backend APIs and is not the security boundary.

Key pages: landing, discover, post detail, auth, dashboard, Stories, editor, Composer, published desk, Anna review, admin, settings.

```powershell
cd source
npm install
npm run dev        # development (http://localhost:3000)
npm run build      # production build
npm run start      # production server
npm run lint       # eslint
npx tsc --noEmit   # type check
```

---

## Testing

### Backend

```powershell
cd blogging-system-yt
python manage.py check
python manage.py makemigrations --check
python manage.py test
```

Verified slice: `apps.comments apps.media_assets apps.composer apps.anna apps.blogs` — 17 passed. Live Tavily/LLM calls stay mocked in tests unless `ANNA_LIVE_PROVIDER_TEST=1`.

### Frontend

```powershell
cd source
npm run lint
npx tsc --noEmit
npm run build
```

### End-to-end matrix

| Journey | Verify |
|---|---|
| Signup/login/logout | CSRF, session, role response |
| Reader browsing | Published-only list/detail; drafts return 404 |
| Author draft lifecycle | Create/update/owner rejection/publish/unpublish |
| Images | Upload validation, cross-owner rejection, image selection |
| Composer | Owner-scoped conversation, private draft, never publishes |
| Anna review | Owned-draft review, no post-status change |
| Admin | Unpublish any live post; Django admin user/category/comment management |

Never claim production readiness from unit tests alone — verify in a deployed environment with secure cookies, PostgreSQL, storage, and controlled provider calls.

---

## Production deployment

### 1. Configure the backend

Set `DJANGO_ENV=prod` and provide these via secret manager / environment (never in source):

```env
DJANGO_ENV=prod
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=<generated-secret>
DJANGO_ALLOWED_HOSTS=api.yourdomain.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://yourdomain.com
DJANGO_CORS_ALLOWED_ORIGINS=https://yourdomain.com
DATABASE_URL=postgres://<user>:<pass>@<host>:5432/swiftpost
MEDIA_STORAGE=s3
AWS_S3_BUCKET=<bucket>
AWS_S3_PUBLIC_BASE_URL=https://media.yourdomain.com
AWS_ACCESS_KEY_ID=<key>
AWS_SECRET_ACCESS_KEY=<secret>
AWS_REGION=<region>
AI_PROVIDER_API_KEY=<key>
TAVILY_API_KEY=<key>
```

### 2. Deploy the backend

1. Run `python manage.py migrate` against PostgreSQL.
2. Run `python manage.py collectstatic` (if serving static files).
3. Serve via Gunicorn behind a reverse proxy (nginx/Cloudflare/ALB) with HTTPS.
4. Set secure cookies: `SESSION_COOKIE_SECURE=true`, `CSRF_COOKIE_SECURE=true`.
5. Add health monitoring on `GET /api/v1/health/`.
6. Configure backups and a rollback plan for PostgreSQL and media.

### 3. Deploy the frontend

```powershell
cd source
npm run build        # production build
npm run start        # production server (or deploy to a static/edge host)
```

Set `NEXT_PUBLIC_SITE_URL` and `NEXT_PUBLIC_API_URL` (the deployed Django base URL). No provider secrets may use the `NEXT_PUBLIC_` prefix.

### 4. Database & media cutover

- Production uses PostgreSQL (or AWS RDS). SQLite is local-dev only.
- Rehearse SQLite → PostgreSQL export/import on a disposable database before cutover.
- Back up the SQLite DB and `media/` before any migration.
- Never delete original data until the new database and media are verified.

### 5. CI / pre-merge (recommended)

On every pull request:

1. `python manage.py check`
2. `python manage.py makemigrations --check`
3. `python manage.py test`
4. `npm run lint`
5. `npx tsc --noEmit`
6. `npm run build`

Block merge if any check fails. Do not commit `.env`, `.env.local`, `db.sqlite3`, or `media/`.

---

## Production deployment checklist

- [ ] `DJANGO_ENV=prod`, `DJANGO_DEBUG=false`
- [ ] `DJANGO_SECRET_KEY` from secret manager (not hardcoded)
- [ ] `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` explicit (no wildcards)
- [ ] `DJANGO_CORS_ALLOWED_ORIGINS` restricted to deployed frontend origin(s)
- [ ] `DATABASE_URL` points to PostgreSQL (not SQLite)
- [ ] `MEDIA_STORAGE=s3` with bucket + public base URL
- [ ] `SESSION_COOKIE_SECURE=true`, `CSRF_COOKIE_SECURE=true`
- [ ] `.env` / `.env.local` gitignored and not committed
- [ ] Health endpoint `GET /api/v1/health/` reachable
- [ ] Migrations applied; `makemigrations --check` clean
- [ ] Backend tests + frontend lint/build pass
- [ ] Provider keys present but not in source control
- [ ] Backup and rollback runbook documented

---

## Security

- Session auth only; no JWT without an explicit product decision.
- CSRF protection on unsafe requests; narrow CORS.
- Object-level authorization on every sensitive operation.
- Upload validation (MIME, extension, size, dimensions) with server-controlled keys.
- Provider keys and session data are backend-only; never logged.
- Retrieved webpage text is never treated as trusted instructions (prompt-injection guard).
- Cross-author private access returns a safe 404.

See [`SECURITY.md`](SECURITY.md) for the full security policy, production checklist, and vulnerability reporting instructions.

---

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for required reading, product rules, test commands, and the pull-request checklist.

### Before changing product behavior

Read `AGENTS.md`, `SWIFTPOST_REBUILD_PRD.md`, `blogging-system-yt/TECH_STACK.md`, `BACKEND_IMPLEMENTATION.md`, and `blogging-system-yt/BACKEND_STATUS.md`. Keep changes small and coherent; add migrations and tests for behavior changes; run the checks above before submitting. Do not commit secrets or production credentials.

---

## License

This project is provided for educational and development purposes. See the repository owner for licensing terms.
