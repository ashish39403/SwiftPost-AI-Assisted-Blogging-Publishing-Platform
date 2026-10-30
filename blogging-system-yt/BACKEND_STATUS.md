# SwiftPost backend status

**Updated:** 30 October 2026

Living record of the Django API. Only behavior listed under **Working now** is implemented. Signup creates `author`. Authors publish/unpublish their own complete posts. Composer writes private drafts. Anna reviews them. AI never publishes.

## Layout

```text
blogging-system-yt/
  manage.py
  config/
    settings/base.py
    settings/local.py
    settings/production.py
    urls.py
    asgi.py
    wsgi.py
  apps/
    accounts/        identity, session auth, registration, login
    users/           Reader, Author, and Admin permission policy
    blogs/
    categories/
    comments/
    publishing/
    moderation/
    media_assets/
    composer/        conversation drafts + Tavily image suggestions
    anna/            one-shot draft review; live research is V2
    common/          error envelope, CSRF failure, health
  tests/integration/
  tests/security/
  docker-compose.yml
  requirements.txt
  .env.example
```

The old `blog_main`, `blogs`, `dashboards`, and `assignments` packages were removed. Full moderation queues and admin user-management APIs remain planned. Durable Composer and Anna conversation history is implemented in Django. Anna live research conversations and all background processing are explicitly deferred to V2.

## Working now

| Item | State |
| --- | --- |
| Django | 5.2.18, Django REST Framework, JSON only |
| Local database | SQLite. Migrations applied for accounts, categories, blogs, and publishing |
| Production database | PostgreSQL when `DATABASE_URL` is set and `DJANGO_ENV=prod` |
| Accounts | Register, login, logout, current user, password change |
| Roles | Registration creates an `author`. `admin` is assigned in Django admin. `reader` remains for demotion and tests |
| Categories | Seeded editorial categories. Admin creates and edits them. Delete deactivates a category. Public lists show active categories |
| Posts | Authors create private drafts. Public lists and detail show `published` posts only |
| Publishing | Authors publish and unpublish their own complete drafts. Admins can unpublish any live post. AI never publishes |
| Media | Authors attach one JPEG, PNG, or WebP featured image to an editable draft. They can also search live photos through Tavily and attach a suggestion after a server-side download |
| Composer | Authors can create, resume, list, and archive owner-scoped chats under `/api/v1/ai/composer/conversations/`. The first message creates a private draft; later messages persist refinement responses. Composer never publishes |
| Anna review | `POST /api/v1/ai/reviews/` reviews an owned draft and returns notes. The current frontend is a one-shot review with a loading pipeline and an explicit handoff to Composer. Anna does not publish |
| Comments | Authenticated users comment on published posts. Comments are approved immediately and show on the public post |
| Likes | Confirmed addition. Authenticated users can like a published post. The like toggles. Counts appear on post payloads |
| Composer conversation history | Implemented: owner-scoped create, list, resume, rename, and archive under `/api/v1/ai/composer/conversations/`; the browser workspace exposes this flow |
| Anna conversation history | Django APIs exist under `/api/v1/ai/anna/conversations/`. The live browser UI is one-shot review only; do not rebuild an Anna chat sidebar unless asked |
| Anna research conversations and background jobs | Explicitly deferred to V2 |

Verified this slice: `python manage.py test apps.comments apps.media_assets apps.composer apps.anna apps.blogs` — 17 passed. Browser E2E was not re-run in this slice. Live Tavily/LLM calls stay mocked in tests.

## API contract

Base URL: `http://127.0.0.1:8000`

Send cookies on every request. For `POST`, `PUT`, `PATCH`, and `DELETE` on login, register, and authenticated routes, first call the CSRF endpoint and send that token in `X-CSRFToken`. Anonymous writes to author APIs such as drafts return `401 AUTHENTICATION_REQUIRED` instead of `CSRF_FAILED`.

Each browser tab may also send `X-Session-Key` (the Django session key, stored in `sessionStorage`). That header wins over the shared `sessionid` cookie, so login or logout in another tab does not take over this tab. Responses echo the active key on `X-Session-Key`.

### `GET /api/v1/auth/csrf/`

- Auth: none
- Success `200`: `{"csrfToken": "<token>"}`
- Also sets the `csrftoken` cookie

### `POST /api/v1/auth/register/`

- Auth: none
- CSRF: required
- Body: `username`, `email`, `password`
- `role`, `is_staff`, `is_superuser`, and `is_active` are rejected
- Success `201`:

```json
{"user": {"id": 1, "username": "Ada", "email": "ada@example.com", "role": "author", "first_name": "", "last_name": ""}}
```

Email is stored in lowercase. Registration does not start a session. The client must call login afterwards.

### `POST /api/v1/auth/login/`

- Auth: none
- CSRF: required
- Body: `email`, `password`
- Username is not accepted as the login identity
- Success `200`: same `user` object, plus the `sessionid` cookie
- Bad credentials `401`: `AUTHENTICATION_FAILED`. The message does not say whether the email exists

### `POST /api/v1/auth/logout/`

- Auth: session
- CSRF: required
- Success `200`: `{"status": "ok"}`

### `GET /api/v1/auth/me/`

- Auth: session
- Success `200`: the same `user` object for the signed-in account only
- Missing session `401`: `AUTHENTICATION_REQUIRED`

### `POST /api/v1/auth/password/change/`

- Auth: session
- CSRF: required
- Body: `current_password`, `new_password`
- Success `200`: `{"status": "ok"}`

### Categories

`GET /api/v1/categories/` and `GET /api/v1/categories/{id}/` are public and return only active categories.

`POST` and `PATCH` are admin only. Body fields are `name` and `description`. `slug` is generated. `DELETE` deactivates the category and returns it with `"is_active": false`.

List responses are paginated:

```json
{"count": 1, "next": null, "previous": null, "results": []}
```

`page` and `page_size` are supported. `page_size` defaults to 10 and cannot exceed 50. An admin may pass `include_inactive=true`.

### Drafts and published posts

`POST /api/v1/drafts/` is author only. Body: `title`, `excerpt`, `body`, `category_id`. All are optional. `status`, `author`, and `slug` are rejected. A new post is always `draft`.

`GET /api/v1/drafts/` returns the signed-in author's posts, excluding archived posts unless `status` is passed. An admin sees every author's posts. Readers receive `403`.

`GET`, `PATCH`, and `DELETE /api/v1/drafts/{id}/` are limited to the author. Another author's id returns `404` `POST_NOT_FOUND`. `PATCH` is allowed for `draft`, `changes_requested`, and `unpublished`. `DELETE` is allowed only for `draft`.

`GET /api/v1/blogs/` and `GET /api/v1/blogs/{id}/` are public and return `published` posts only. Filters: `search` and `category` (the category slug). A draft id returns `404` `POST_NOT_FOUND`.

Post object:

```json
{"id": 1, "title": "Clean energy", "slug": "clean-energy", "excerpt": "", "body": "", "status": "draft", "category": {"id": 1, "name": "Energy", "slug": "energy"}, "author": {"id": 2, "username": "ada"}, "published_at": null, "created_at": "", "updated_at": ""}
```

### Publishing actions

All require CSRF and a session.

| Endpoint | Who | Effect |
| --- | --- | --- |
| `POST /api/v1/blogs/{id}/publish/` | Owning author or admin | `draft`, `unpublished`, `changes_requested`, or leftover `in_review` becomes `published`. Title, excerpt, body, and an active category are required |
| `POST /api/v1/blogs/{id}/unpublish/` | Owning author or admin | `published` becomes `unpublished`. Admins may unpublish any live post |
| `POST /api/v1/blogs/{id}/submit/` | Owning author | Optional leftover path to `in_review`. The writer UI publishes directly |
| `POST /api/v1/blogs/{id}/archive/` | Owning author or admin | Allowed from `draft`, `in_review`, `changes_requested`, or `unpublished` |

An illegal status change returns `400` `INVALID_TRANSITION`. Another author's id returns `404`. Optional body field: `reason`.

A published or draft post includes `featured_image`. It is `null` until an image is attached.

### Featured image

`POST /api/v1/media/upload/` is multipart form data with `post_id` and `file`. The signed-in author must own the post, and the post must be `draft`, `changes_requested`, or `unpublished`. Another author's post id returns `404` `POST_NOT_FOUND`.

Allowed images are JPEG, PNG, and WebP. The file contents, declared type, and extension must agree. The default limit is 5 MB and 4000 pixels on the longest side. The stored object key is server-generated. The original filename is display metadata only.

Success `201`:

```json
{"id": 1, "post_id": 3, "content_type": "image/png", "byte_size": 120, "width": 12, "height": 8, "original_filename": "photo.png", "url": "http://127.0.0.1:8000/media/uploads/<key>.png"}
```

Uploading again replaces the previous image and deletes the old file. `DELETE /api/v1/media/{id}/` removes the image from an editable draft owned by that author.

`GET /api/v1/media/{id}/` is public only when the image belongs to a published post. A draft image is visible to its owner and to an admin.

Local development stores files under `media/`. Production requires `MEDIA_STORAGE=s3`.

### Composer

`POST /api/v1/ai/compose/` is author-only. Body: `{ "title": "..." }`. Composer calls the LLM adapter and creates a private `draft`. It does not publish. After the draft is saved it may call Tavily once for live image suggestions. A Tavily failure does not fail the compose. The Next.js `/api` rewrite waits up to five minutes (`experimental.proxyTimeout`). If that POST still drops, the Composer and Anna UIs keep polling the saved conversation or review so the result appears without a full-page refresh. Illegal or harmful briefs are refused: the conversation still stores a polite no, and **no draft is created**. The model is `AI_MODEL_COMPOSE` (default `nvidia/nemotron-3-super-120b-a12b`), then `AI_MODEL`. `.env` overrides process env. GPT-5 models omit `temperature` and JSON-mode, use `max_completion_tokens`, and stay on Chat Completions (`use_responses_api=false`). NVIDIA Composer calls also skip JSON-mode and rely on the article JSON parser. The AICredits base URL is `https://api.aicredits.in/v1`.

### Comments and likes

`GET /api/v1/blogs/{id}/comments/` is public on published posts and returns approved comments only.

`POST /api/v1/blogs/{id}/comments/` requires an authenticated account. The comment is `approved` immediately and appears on the public post. `POST /api/v1/comments/{id}/approve/` remains for leftover `pending` rows.

`GET` and `POST /api/v1/blogs/{id}/likes/` read or toggle a like on a published post. Post payloads include `like_count`, `comment_count`, and `liked`.

### Live image search

`POST /api/v1/media/search-images/` is author-only for an owned draft. Body: `{ "post_id": 1, "query": "optional" }`. It uses the Tavily adapter and stores suggestion URLs, not image bytes.

`POST /api/v1/media/suggestions/{id}/attach/` downloads that suggestion on the server, validates it as an image, and saves it as the featured image. `POST /api/v1/media/suggestions/save/` accepts `{ "ids": [1,2] }`, marks them selected, and uses the first successful download as the featured image. Private and loopback URLs are rejected.

Composer success `201` includes `id`, `status`, `title_input`, and `post`. `GET /api/v1/ai/compose/{id}/` returns the same run to its owner. Another author receives `404`.

### Anna review

`POST /api/v1/ai/reviews/` is author-only. Body: `{ "post_id": 1 }`. Anna reads the owned draft and returns structured notes (Verdict, Strengths, Gaps, Suggested edits, Do this first). The post status does not change. Harmful drafts are refused rather than improved. Another author's post id returns `404`. The browser uses this one-shot review, not a chat sidebar. The model is `AI_MODEL_REVIEW` (default `openai/gpt-5.5`), then `AI_MODEL`.

### `GET /api/v1/health/`

- Auth: none
- Success `200`: `{"status": "ok", "service": "swiftpost-api"}`

### Errors

```json
{"error": {"code": "NOT_FOUND", "message": "The requested resource could not be found.", "details": {}}}
```

Codes in use: `VALIDATION_ERROR`, `INVALID_TRANSITION`, `AUTHENTICATION_REQUIRED`, `AUTHENTICATION_FAILED`, `PERMISSION_DENIED`, `CSRF_FAILED`, `NOT_FOUND`, `POST_NOT_FOUND`, `CATEGORY_NOT_FOUND`, `COMMENT_NOT_FOUND`, `MEDIA_NOT_FOUND`, `METHOD_NOT_ALLOWED`, `SERVER_ERROR`.

Allowed browser origin defaults to `http://localhost:3000`. Trailing slashes are required.

## Django admin

No superuser is seeded. From `blogging-system-yt`, with the project `venv` active:

```powershell
.\venv\Scripts\python manage.py createsuperuser
```

The prompt asks for email first, then username. That command creates an admin-role staff user.

## Not built

Moderation queues beyond comment approve/reject; admin user-management APIs; the dedicated Anna conversation browser UI; and Anna research/background jobs (V2).
