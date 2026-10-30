# SwiftPost — End-to-End Backend Implementation Plan

**Status:** Implementation blueprint with delivered conversation-history slice  
**Product:** SwiftPost  
**Target path:** `H:\Blog_Webapp\blogging-system-yt`  
**Backend style:** Modular Django monolith  
**API:** Django REST Framework under `/api/v1/`  
**Development database:** SQLite  
**Production database:** PostgreSQL / AWS RDS  
**Background work:** Deferred to V2; V1 AI conversation requests are synchronous and bounded
**Date:** 30 October 2026

> **30 October 2026 implementation status:** The Django API and Next.js workspace are a writer platform. Registration creates `author`. Authors publish and unpublish their own complete posts; admins can unpublish any live post. Composer conversations create/refine private drafts (Nemotron) with optional Tavily images. Anna's live UI is one-shot review (`POST /api/v1/ai/reviews/`); conversation APIs exist but the chat sidebar was removed by product request. Do not introduce Celery, Redis, research jobs, retries, polling, or Anna live research unless asked. Full in-app user-management remains planned. See `docs/AI_CONVERSATION_V1.md` and `docs/BACKEND_STATUS.md`.

---

## 1. Purpose and implementation boundary

This document translates the SwiftPost PRD and `TECH_STACK.md` into an executable backend implementation plan. It defines the backend modules, domain boundaries, data model, API contract, authentication model, background jobs, Anna workflow, migration strategy, tests, and delivery phases.

This document covers the Django backend only. The Next.js/React frontend is a separate consumer of the API. Frontend source code, layout, styling, and component implementation are outside this document and must not be changed as part of backend work unless explicitly requested.

### Required architecture

- Django only; Flask is prohibited.
- Modular Django monolith; do not create microservices.
- Django REST Framework from the first implementation version.
- SQLite for local development only; PostgreSQL, including AWS RDS if selected, for production.
- Django session authentication with secure HTTP-only cookies; do not switch to JWT without a new product decision.
- Celery and Redis for long-running and retryable work in V2; do not add them to the current V1 conversation-history slice.
- S3-compatible object storage for uploaded files.
- Anna as an internal Django module.
- Provider adapters for live search and LLM access.
- Single-platform, non-multi-tenant data and authorization model.
- Human-controlled publishing; Anna never publishes automatically.

### Implementation rule

Before each major phase:

1. Inspect the current repository and preserve unrelated work.
2. Explain the planned changes and affected modules.
3. Identify migration, security, and compatibility risks.
4. Implement one complete vertical slice.
5. Add or update tests for that slice.
6. Run the relevant checks.
7. Report what changed, what was verified, and what remains.

## 2. Current repository audit

The backend under `blogging-system-yt/` **is already** the DRF modular monolith. The Next.js app is `source/`. Do not recreate `blog_main` templates.

### What exists now

- `config/` settings, URLs, WSGI/ASGI.
- Custom `User` (`USERNAME_FIELD=email`, default role `author`).
- Apps: `accounts`, `users`, `blogs`, `categories`, `comments`, `publishing`, `moderation`, `media_assets`, `composer`, `anna`, `common`.
- `/api/v1/` session+CSRF JSON API, consistent error envelope.
- SQLite locally; PostgreSQL when `DATABASE_URL` is set.
- Composer conversations + title-to-draft; Anna review; Tavily image suggestions.
- Seeded editorial categories.

### Remaining gaps (do not treat as a greenfield rebuild)

- Full in-app admin user-management APIs/UI (Django admin still used to assign `admin` and deactivate users).
- Anna live research, sources, Celery/Redis (V2).
- Production S3 cutover and PostgreSQL cutover when deploying.

### Reuse versus replacement policy

Do not delete existing models or migrations blindly. Preserve valid user, post, category, comment, and media data unless the user authorizes destructive changes.

## 3. Implemented backend structure

The live package names are under `config/` and `apps/`. Keep these boundaries. Do not recreate a `blog_main` layout.

```text
blogging-system-yt/
  manage.py
  config/
    settings/
      base.py
      local.py
      production.py
    urls.py
    asgi.py
    wsgi.py
  apps/
    accounts/
      models.py
      serializers.py
      views.py
      urls.py
      services.py
      permissions.py
      tests/
    users/
    blogs/
    categories/
    comments/
    publishing/
    moderation/
    media_assets/
    anna/
      models.py
      serializers.py
      views.py
      urls.py
      permissions.py
      services.py
      tasks.py
      interfaces/
      orchestration/
      prompts/
      providers/
      tools/
      validators/
      tests/
    common/
      api_errors.py
      permissions.py
      pagination.py
      observability.py
      types.py
  tests/
    integration/
    security/
  requirements.txt or pyproject.toml
  .env.example
  docker-compose.yml
```

The existing app names can be migrated gradually. A package rename is not required if it creates unnecessary migration risk; responsibility boundaries matter more than directory names.

## 4. Module ownership and seams

### Accounts

Owns registration, login, logout, current-user identity, session behavior, password validation, and authentication-facing API responses.

Must not decide whether a user may edit a particular post. That belongs to object-level authorization and the relevant domain policy.

### Users and roles

Owns the user role model, account state, staff/admin management, and role policy. The initial roles are Reader, Author, and Admin.

Must not rely on frontend navigation or submitted role fields for security.

### Blogs

Owns post content, slug, category relationship, author relationship, draft data, public read queries, and content validation that is independent of publishing authority.

Must not call LLM/search providers or implement admin moderation decisions.

### Categories

Owns category lifecycle, uniqueness, slugs, and category-scoped queries.

### Comments

Owns comment creation, visibility state, and comment-specific moderation behavior.

### Publishing

Owns legal post state transitions. Authors and admins publish complete posts; owners and admins unpublish; archive is allowed from non-published statuses. Every transition must validate actor permission and current state.

### Moderation

Owns admin review queues, flags, moderation decisions, and audit events. It may call publishing services but must not duplicate transition rules.

### Media

Owns upload validation, storage adapter interaction, asset metadata, replacement, and cleanup. It must not store large binary files in PostgreSQL.

### Composer

Owns title/conversation draft generation. It calls the shared LLM adapter, creates or updates a private `draft` through `blogs.services`, and stores a provenance snapshot. After a draft exists it may request Tavily image suggestions. It must not call publishing transitions.

### Anna

Owns draft review and (later) research conversations. V1 is one-shot review of an owned draft. Live research jobs and source collections are V2. It must use application interfaces for search and LLM calls. She must not publish.

### Common

Owns small cross-cutting utilities such as API error formatting, shared permission helpers, pagination, IDs, correlation IDs, and observability. It must not become an unbounded business-logic dumping ground.

## 5. Configuration and environment foundation

Split settings by environment or use an equivalent explicit configuration strategy. Do not keep production settings mixed into a development-only file.

### Required configuration groups

```text
DJANGO_SECRET_KEY
DJANGO_DEBUG
DJANGO_ALLOWED_HOSTS
DJANGO_CSRF_TRUSTED_ORIGINS
DJANGO_CORS_ALLOWED_ORIGINS
DATABASE_URL
REDIS_URL
CELERY_BROKER_URL
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION
AWS_S3_BUCKET
AWS_S3_ENDPOINT_URL
AI_PROVIDER
AI_MODEL
AI_PROVIDER_API_KEY
SEARCH_PROVIDER
TAVILY_API_KEY
FRONTEND_ORIGIN
```

### Configuration rules

- Real secrets must never be committed.
- `.env.example` contains names and safe placeholder values only.
- `DEBUG=False` is required in production.
- `ALLOWED_HOSTS`, CORS, and CSRF trusted origins must be explicit.
- Provider credentials are backend-only.
- The frontend receives only its public API base URL and no provider secret.
- Configuration errors should fail early in deployment rather than during a user request.

## 6. User model, roles, and authentication

### Custom-user decision

**Decided and shipped.** `apps.accounts.User` is a custom user (`USERNAME_FIELD=email`, unique username, `role` field). Registration creates `author`. Superuser creation creates `admin`. Do not introduce a second user model or silently switch `AUTH_USER_MODEL`.

### Roles

- **Reader:** leftover role for demotion and tests; not the signup default.
- **Author:** created on registration. Owns drafts/posts, Composer, Anna, and may publish/unpublish their own complete posts.
- **Admin:** assigned in Django admin. Can unpublish any live post, manage categories, and deactivate users.

Do not treat `is_staff` or `is_superuser` as the only product role model. They may support infrastructure/admin behavior, but product authorization should be explicit and tested.

### Session authentication flow

1. The frontend submits credentials to `POST /api/v1/auth/login/`.
2. Django authenticates the user.
3. Django creates a server-side session.
4. Django returns a secure HTTP-only session cookie.
5. The Next.js frontend sends requests with credentials included.
6. DRF resolves the session to `request.user`.
7. The API evaluates role and object-level permissions.
8. Logout invalidates the server session.

Cookie settings in production must include `Secure=True`, `HttpOnly=True`, intentional `SameSite`, bounded expiry, and a correct domain/path. Unsafe cookie-authenticated requests require CSRF protection.

### Authentication endpoints

```text
POST /api/v1/auth/register/
POST /api/v1/auth/login/
POST /api/v1/auth/logout/
GET  /api/v1/auth/me/
POST /api/v1/auth/password/change/
```

Password reset/email verification may be added if confirmed for the release; do not invent an external identity provider.

### Authorization rules

Every sensitive endpoint must enforce:

1. Authentication.
2. Role permission.
3. Object ownership or explicit admin scope.
4. Current object status.
5. Input and state-transition validation.

The check must happen on direct API requests, not only through the frontend. An author must not be able to use an ID or guessed URL to access another author's private draft, post, conversation, source, job, or artifact.

## 7. Domain data model

Use explicit relationships in both development SQLite and production PostgreSQL. SQLite is the local development database; PostgreSQL/AWS RDS is the production database target. Names below describe behavior; final field names may be adapted to project conventions.

### User

Recommended fields:

- `id`
- `email`
- `username` if product still requires it
- password hash managed by Django
- `role`
- `first_name`
- `last_name`
- `is_active`
- `is_staff`
- `is_superuser`
- `created_at`
- `updated_at`

Email/username uniqueness and normalization must be decided before migration. Do not use email text as an authorization identity; use the authenticated user relation.

### Category

- `id`
- `name` (unique)
- `slug` (unique if exposed in URLs)
- `description`
- `is_active` or archival state
- `created_at`
- `updated_at`

### BlogPost

- `id`
- `author`
- `category`
- `title`
- `slug`
- `excerpt`
- `body`
- `featured_image`/media relation
- `status`
- `created_at`
- `updated_at`
- `published_at`
- optional `submitted_at`, `unpublished_at`, and review metadata

Target status values should be stable machine values such as:

```text
draft
in_review
changes_requested
published
unpublished
archived
```

Only valid transitions are allowed. Public querysets must filter to `published` and any other explicit visibility requirements.

### Comment

- `id`
- `user`
- `post`
- `body`
- `status`: `pending`, `approved`, `rejected`, optionally `hidden`
- `created_at`
- `updated_at`
- moderation actor/time if required

### Publishing history

Use a separate history model if auditability or moderation review requires it:

- post
- actor
- previous status
- new status
- action/reason
- timestamp

### MediaAsset

- owner/context
- storage key
- original filename (display metadata only)
- safe MIME/content type
- file size
- validation status
- width/height where applicable
- created/updated timestamps
- deletion/orphan state

### AIConversation

- owner
- selected post/draft context, nullable
- title/label
- status
- created/updated timestamps

Only the owner may access a private conversation unless an explicit admin policy says otherwise.

### AIMessage

- conversation
- role: `user`, `assistant`, `system`, or `tool`
- content
- sequence number
- safe metadata JSON
- created timestamp

Do not expose internal system messages or provider-sensitive metadata to ordinary clients unless explicitly required.

### AIResearchJob

- conversation
- query/brief reference
- status: `queued`, `running`, `completed`, `failed`, `cancelled`
- retry count
- provider metadata safe to retain
- error code/message safe for display
- started/completed/created/updated timestamps

### AISource

- research job
- canonical URL
- title
- domain
- snippet
- extracted content or a bounded source representation
- retrieved timestamp
- source status
- provider reference
- metadata JSON

Store only the source data required by the product and permitted by applicable provider/copyright constraints. Retention policy remains an open decision.

### AIGenerationRun

- conversation
- generation type: title, outline, draft, revision, summary, metadata
- input snapshot or safe reference
- output snapshot or artifact reference
- model name
- status
- token/usage metadata
- retry count
- error code/message
- created/completed timestamps

### AI artifact and approval provenance

Generated titles, outlines, drafts, and revisions must be distinguishable from the final author-approved post. Use an artifact/provenance relation or an equivalent explicit record. A generation run must not directly mutate a published post.

## 8. Domain services and business workflows

Views and ViewSets coordinate HTTP requests. They must not contain the complete workflow.

### Recommended service boundaries

```text
accounts.services
  register_user()
  authenticate_user()
  logout_user()

blogs.services
  create_draft()
  update_owned_post()
  delete_owned_post()

publishing.services
  save_draft()
  submit_for_review()
  publish_post()
  unpublish_post()
  archive_post()
  request_changes()

moderation.services
  approve_comment()
  reject_comment()
  moderate_post()

media.services
  validate_upload()
  store_asset()
  remove_asset()

composer.services
  compose_from_title()

anna.services
  review_owned_draft()
  start_conversation()
  add_message()
  select_context()
  start_research()
  generate_title()
  generate_outline()
  generate_draft()
  revise_content()
  approve_into_draft()
```

Services should receive authenticated actor/context explicitly, perform authorization through policy functions, use transactions for multi-record mutations, and return domain results or typed errors.

### Deep-module principles

- Keep public interfaces small.
- Hide provider SDKs inside adapters.
- Hide state-transition rules inside publishing services.
- Hide ownership queries inside policies/query services.
- Avoid passing ORM internals through every layer.
- Keep serializers focused on transport validation.
- Keep URL files declarative.
- Keep views thin enough to read as use-case coordination.

## 9. API implementation

All new API routes are under `/api/v1/`. Use consistent JSON responses and errors.

### Error envelope

```json
{
  "error": {
    "code": "POST_NOT_FOUND",
    "message": "The requested post could not be found.",
    "details": {}
  }
}
```

Do not leak model names, SQL, stack traces, provider responses, API keys, or private data. Validation details may include field-level errors safe for the current user.

### Content endpoints

```text
GET    /api/v1/blogs/
POST   /api/v1/blogs/
GET    /api/v1/blogs/{id}/
PATCH  /api/v1/blogs/{id}/
DELETE /api/v1/blogs/{id}/

GET    /api/v1/drafts/
POST   /api/v1/drafts/
GET    /api/v1/drafts/{id}/
PATCH  /api/v1/drafts/{id}/
DELETE /api/v1/drafts/{id}/

POST   /api/v1/blogs/{id}/submit/
POST   /api/v1/blogs/{id}/publish/
POST   /api/v1/blogs/{id}/unpublish/
POST   /api/v1/blogs/{id}/archive/
```

Whether blogs and drafts are separate resources or one resource filtered by status should be decided before implementation. The external behavior must make draft privacy and publishing transitions unambiguous.

### Category endpoints

```text
GET    /api/v1/categories/
GET    /api/v1/categories/{id}/
POST   /api/v1/categories/              # admin
PATCH  /api/v1/categories/{id}/         # admin
DELETE /api/v1/categories/{id}/         # admin/archive policy
```

### Comment endpoints

```text
GET    /api/v1/blogs/{id}/comments/
POST   /api/v1/blogs/{id}/comments/
DELETE /api/v1/comments/{id}/            # owner/admin policy
POST   /api/v1/comments/{id}/approve/    # admin
POST   /api/v1/comments/{id}/reject/     # admin
```

### Like endpoints (confirmed addition)

Likes are not in the original PRD. Authors and readers may like a published post. The like toggles per user.

```text
GET    /api/v1/blogs/{id}/likes/
POST   /api/v1/blogs/{id}/likes/
```

### Media endpoints

```text
POST   /api/v1/media/upload/
GET    /api/v1/media/{id}/
DELETE /api/v1/media/{id}/
GET    /api/v1/media/search-images/?post_id={id}
POST   /api/v1/media/search-images/
POST   /api/v1/media/suggestions/{id}/attach/
POST   /api/v1/media/suggestions/save/
```

The upload endpoint must validate content type, size, ownership context, and safe storage behavior. Large binary data must not be placed in PostgreSQL.

### Composer endpoints

```text
POST   /api/v1/ai/compose/
GET    /api/v1/ai/compose/{id}/
GET    /api/v1/ai/composer/conversations/
POST   /api/v1/ai/composer/conversations/
```

Composer conversations create or refine a private draft. A successful compose is not a publish. Image suggestions may follow the draft.

### Anna endpoints (V1 live UI)

```text
POST   /api/v1/ai/reviews/
```

Body: `{ "post_id": 1 }`. Returns notes. Does not change post status.

Django also has `/api/v1/ai/anna/conversations/` from an earlier slice. The current product UI does not use a chat sidebar. Do not add `/api/v1/ai/jobs/` or research polling in V1.

## 10. Publishing implementation

### State machine

```text
draft / unpublished / changes_requested / in_review
        → owning author or admin Publish → published
published → owner or admin Unpublish → unpublished

draft / in_review / changes_requested / unpublished → archived
```

Exact transitions must be encoded in one publishing service, not duplicated in serializers, views, and admin actions.

### Rules

- Saving a draft does not make it public.
- AI generation does not publish or mutate public state.
- Submission validates required content and author permission.
- Publishing is an explicit action and creates an audit/history event.
- Unpublishing is restricted to authorized actors.
- Archived content is not public.
- Public querysets include only explicitly public statuses.
- Authors publish and unpublish their own complete posts. Admins can unpublish any live post. AI never publishes.

### Explicit approval boundary

Anna may create generated artifacts and an author may approve a result into a normal draft. Only the normal draft/publishing workflow can publish it. This prevents an AI endpoint from becoming an authorization bypass.

## 11. Media implementation

### Storage boundary

Use an object-storage adapter so media code does not depend directly on one vendor SDK throughout the application.

```text
Media service
  → Storage interface
      → S3 adapter
      → Local development adapter, if needed
```

### Upload rules

- Authenticate the request.
- Authorize the target post/context.
- Validate MIME type and extension.
- Enforce maximum file size and image dimensions.
- Generate a server-controlled object key.
- Store only metadata and key in PostgreSQL.
- Return safe metadata to the client.
- Clean up failed or orphaned objects through a defined process.
- Do not trust the original filename as a path.

## 12. Celery and Redis implementation (V2; not part of the current V1 slice)

### Task categories

```text
anna.tasks.run_research_job
anna.tasks.run_title_generation
anna.tasks.run_outline_generation
anna.tasks.run_draft_generation
anna.tasks.run_revision_generation
anna.tasks.retry_failed_generation
media_tasks.process_uploaded_media
notifications_tasks.send_notification       # future, only if approved
```

### Task rules

- Create the job/generation record before enqueueing work.
- Pass stable IDs, not large ORM objects, through the queue.
- Re-load and re-authorize relevant records inside the task.
- Use idempotency keys or state checks to prevent duplicate artifacts.
- Store `queued`, `running`, `succeeded`, `failed`, `retrying`, or `cancelled` state.
- Retry only transient failures.
- Do not retry invalid input, unauthorized context, or permanent provider errors indefinitely.
- Bound retries and record the final error safely.
- Keep the HTTP request responsive.

### Example research flow

1. API validates the author and creates `AIResearchJob(status=queued)`.
2. API enqueues a Celery task with the job ID.
3. Worker loads the job and conversation, re-checks ownership, and sets `running`.
4. Worker calls the search adapter.
5. Adapter returns normalized source records or a mapped error.
6. Worker persists sources and marks the job `completed` or `failed`.
7. Frontend reads the job endpoint.

## 13. Anna implementation

### Suggested internal package

```text
anna/
  models.py
  serializers.py
  views.py
  urls.py
  permissions.py
  services.py
  tasks.py
  interfaces/
    search.py
    llm.py
    storage.py
  orchestration/
    conversation.py
    research.py
    generation.py
    revision.py
  prompts/
  tools/
  providers/
    tavily.py
    selected_llm.py
  validators/
  tests/
```

### Small public interface

The rest of the application should depend on a small service API:

```text
start_conversation(actor, payload)
add_message(actor, conversation_id, payload)
select_context(actor, conversation_id, post_id)
start_research(actor, conversation_id, payload)
generate_title(actor, conversation_id, payload)
generate_outline(actor, conversation_id, payload)
generate_draft(actor, conversation_id, payload)
revise_content(actor, conversation_id, payload)
approve_to_draft(actor, conversation_id, artifact_id, payload)
```

Views should not instantiate provider SDK clients or build prompts directly.

### Provider interfaces

```python
class SearchProvider(Protocol):
    def search(self, query: str, *, limit: int) -> list[SearchResult]: ...


class LLMProvider(Protocol):
    def generate(self, request: GenerationRequest) -> ProviderGenerationResult: ...
```

The exact Python types may vary. The important boundary is that provider-specific response objects are converted into application-owned types before persistence.

### LangChain boundary

LangChain is used in `anna/orchestration` and the LLM adapter for prompt templates, ChatOpenAI, and JSON article parsing. Do not expose LangChain chains or message classes through the public API or domain models. Tavily remains a `SearchProvider` adapter, including live image search.

### Context selection

When an author selects an existing post/draft:

1. API authenticates the actor.
2. Policy checks ownership or explicit admin scope.
3. Policy checks whether the post status is eligible as context.
4. Conversation context relation is persisted.
5. Every later job re-checks that the context remains accessible.

An earlier valid selection must not grant permanent access after ownership, status, or account permissions change.

### Source and prompt safety

- Retrieved webpage content is untrusted data.
- External text must not override system/application instructions.
- Fetches must have bounded size, time, redirects, and domain/network safety.
- Source URLs and retrieval times are preserved.
- Conflicting or low-quality results are surfaced where detectable.
- Generated citations must be based on stored source metadata; invented URLs are not acceptable.

## 14. Migration strategy

### Current-to-target mapping

| Legacy data (old `blog_main` app) | Current concept | Note |
|---|---|---|
| Django default `User` | `apps.accounts.User` (email login, `role`) | Custom user is already live. Do not switch identity again |
| `blogs.Category.category_name` | `Category.name` | Seeded editorial categories exist |
| `blogs.Blog` | `BlogPost` | `excerpt` / `body` / `status` |
| `Blog.status` Draft/Published | `draft` / `published` plus unpublished, archived, leftover `in_review` | Authors publish directly |
| `Blog.featured_image` | `MediaAsset` | Local files in dev; S3 adapter ready for production |
| `blogs.Comment` | `Comment` | Pending unless the commenter is the post author or an admin |
| Local `media/` files | Local or S3 objects | Keep local media until a verified production cutover |
| SQLite database | SQLite locally; PostgreSQL when `DATABASE_URL` is set | Rehearse export/import before production |

### Development and production database rules

- Use SQLite for local development and early feature work.
- Keep Django migrations and query behavior compatible with PostgreSQL.
- Do not rely on SQLite-only behavior, loose typing, or SQLite-specific SQL.
- Use PostgreSQL locally when production-parity testing is required before release.
- Production runs on PostgreSQL, hosted directly or through AWS RDS.
- The move from SQLite to PostgreSQL must use a repeatable export/import or migration process and be verified before cutover.

### Migration rules

- Back up the SQLite database and media before any migration.
- Inventory users, posts, categories, comments, status values, slugs, and media.
- Create a mapping report before importing.
- Preserve ownership; never assign content by email string alone without verified identity mapping.
- Handle duplicate/invalid slugs deterministically.
- Verify relationships and row counts after import.
- Rehearse rollback or restore on a disposable PostgreSQL database before production cutover.
- Do not delete the original data until the new database and media are verified.

## 15. Testing strategy

### Authentication and identity

- Registration success and invalid input.
- Duplicate identity rejection.
- Login success and invalid login.
- Logout invalidation.
- Current-user response.
- Session expiry behavior.
- CSRF behavior for unsafe requests.
- Role assignment and forbidden role escalation.

### Authorization and ownership

- Reader cannot access author/admin mutations.
- Author can access own draft/post.
- Author cannot read, edit, delete, publish, or use another author's private post.
- Admin can perform approved platform operations.
- Direct API requests enforce the same rules as UI flows.
- Conversation, source, job, and artifact ownership is enforced.

### Blogs and publishing

- Public listing includes only published content.
- Drafts are not discoverable by search or direct public URL.
- Create/update/delete ownership rules.
- Slug uniqueness and stable URLs.
- Category filtering, search, and pagination.
- Valid and invalid state transitions.
- Explicit publish/unpublish/archive behavior.
- Publishing history/audit event creation.

### Comments and media

- Authenticated comment creation.
- Moderation states and public visibility.
- Admin approval/rejection protection.
- Valid image upload.
- Invalid type and oversized file rejection.
- Safe filename/key handling.
- Storage failure recovery.
- Orphan/cleanup behavior.

### Anna and background jobs

- Conversation creation, listing, and resume.
- Message persistence and ordering.
- Eligible context selection.
- Unauthorized private-context rejection.
- Research job creation/status transitions.
- Search provider failure, empty results, timeout, and retry.
- Source persistence and retrieval timestamps.
- Title, outline, draft, and revision generation.
- Malformed provider output handling.
- LLM failure and retry behavior.
- Idempotent task execution.
- No automatic publishing.
- Explicit approval into a normal draft.

All external providers must be mocked or replaced with deterministic test adapters in automated tests. Tests must prove workflow safety, not claim that generated content is factually correct.

## 16. API contract verification

The backend implementation must be verified against the separate Next.js frontend expectations before integration is declared complete.

Verify:

- Base URL and `/api/v1/` prefix.
- Cookie credential behavior.
- CSRF token flow.
- Login/logout/current-user response shapes.
- Role and permission fields.
- Post/draft status names.
- Pagination shape.
- Search and category query parameters.
- Media upload encoding and response.
- Job ID/status shape.
- Source metadata shape.
- Generated artifact/provenance shape.
- Error envelope and field validation format.

Do not change backend semantics merely to match an accidental frontend assumption. Resolve contract mismatches explicitly and document the chosen contract.

## 17. Observability and operations

Log and measure:

- Request route, method, status, duration, correlation ID.
- Authentication failures and permission denials.
- Publishing/moderation actions.
- Upload validation and storage failures.
- Celery queue depth, task duration, retries, and terminal failures.
- AI research/generation success, timeout, provider error, cancellation, and cost metadata.
- Database and application health.

Never log passwords, session cookies, API keys, full private drafts, or unnecessary raw prompts/source content.

Required operational capabilities:

- Health endpoint for application readiness.
- Database migration command/runbook.
- Celery worker startup and health procedure.
- Redis connectivity check.
- S3 connectivity/configuration check.
- Structured error reporting.
- Backup and restore procedure.
- Deployment rollback procedure.

## 18. Security checklist

- [ ] Production `DEBUG=False`.
- [ ] Secret key and provider keys come from environment/secret manager.
- [ ] Secure HTTP-only session cookies configured.
- [ ] CSRF protection enabled and tested.
- [ ] CORS restricted to the approved frontend origin(s).
- [ ] PostgreSQL credentials not hardcoded.
- [ ] Ownership checks cover posts, drafts, conversations, messages, contexts, jobs, sources, and artifacts.
- [ ] Role escalation is prevented.
- [ ] Public querysets exclude drafts and private moderation data.
- [ ] Rich text/HTML is sanitized or safely rendered.
- [ ] Upload type/size/content validation is implemented.
- [ ] Server-side URL fetches are bounded and protected against SSRF.
- [ ] Retrieved webpage instructions cannot override Anna's system/application policy.
- [ ] Login, comment, upload, and AI endpoints have abuse controls.
- [ ] API errors do not expose stack traces or secrets.
- [ ] Publishing and moderation actions are auditable.

## 19. Implementation phases

**Status, 30 October 2026:** Phases 1–5 and the writer-platform frontend contract are delivered. Composer conversations and Anna one-shot review are delivered. Anna live research and Celery/Redis remain V2 (phases 6 and 8 research jobs). Phase 10 (production cutover) is not done.

### Phase 1 — Audit and decision gate — **done**

Deliver:

- Repository and instruction inventory.
- Current model/view/URL/settings audit.
- Current Git status captured.
- Frontend API expectation inventory.
- Migration map and data-risk report.
- Custom-user decision.
- Target module map.

Exit criteria: the team knows what is reused, what is replaced, and what migrations are required.

### Phase 2 — Backend foundation — **done**

Deliver:

- Environment-separated settings.
- SQLite development configuration and production-compatible PostgreSQL configuration.
- DRF installation and `/api/v1/` routing.
- Consistent error envelope.
- Session authentication.
- CSRF/CORS configuration.
- Logging/correlation IDs.
- Base test setup.

Exit criteria: a protected `me` endpoint works against SQLite in development, with production PostgreSQL/AWS RDS settings defined and tested for configuration compatibility.

### Phase 3 — Accounts and roles — **done** (signup = author)

Deliver:

- User model decision and migrations.
- Registration, login, logout, current-user endpoint.
- Reader/Author/Admin role policy.
- Permission classes and policy helpers.
- Authentication/authorization tests.

Exit criteria: identity and permission boundaries are verified through direct API calls.

### Phase 4 — Content foundation — **done**

Deliver:

- Categories.
- BlogPost/draft data model.
- Slugs, search, filtering, pagination.
- Author ownership services.
- Public published-only querysets.
- Blog/draft API endpoints.

Exit criteria: authors can manage only their own drafts and public readers cannot see private content.

### Phase 5 — Publishing, comments, moderation, and media — **done** for author self-publish, comments, local media. Production S3 cutover is still a deploy task.

Deliver:

- Publishing state machine and history.
- Explicit publish/unpublish/archive actions.
- Comments and moderation states.
- Admin moderation policy.
- S3-compatible media adapter and upload validation.

Exit criteria: the content lifecycle is safe and auditable, and media does not depend on local production disk.

### Phase 6 — Celery and Redis foundation (V2)

Deliver:

- Broker configuration.
- Worker configuration.
- Persisted job status conventions.
- Retry/idempotency helpers.
- Health and observability.

Exit criteria: a deterministic sample task runs, reports status, retries safely, and is covered by tests.

### Phase 7 — Anna data and provider boundaries — **partial**

Composer/Anna conversation models, LLM + Tavily adapters, and mock-provider tests exist. Research job/source models for live web research are V2.

Deliver:

- Conversation/message/context models.
- Research job/source models.
- Generation/artifact/provenance models.
- SearchProvider and LLMProvider interfaces.
- Mock providers.
- Anna permission policies.

Exit criteria: an author can persist a conversation, messages, and authorized post context without any external provider dependency.

### Phase 8 — Anna workflow

Deliver:

- Research adapter and Celery job.
- Source normalization and persistence.
- Title/outline/draft generation.
- Revision operations.
- Structured output validation.
- Failure, retry, timeout, and empty-result behavior.
- Approval into a normal draft.

Exit criteria: the complete author workflow works with mock providers and cannot publish automatically.

### Phase 9 — Frontend integration verification — **in progress**

The Next.js workspace consumes auth, drafts, publish/unpublish, Composer, Anna review, media, and public discovery.

Deliver:

- Contract check against the Next.js frontend.
- Session/cookie verification.
- Content and publishing flow verification.
- Anna conversation/job/source/artifact verification.
- Error and permission contract fixes.

Exit criteria: the frontend can consume the API without backend assumptions being hidden or inconsistent.

### Phase 10 — Hardening and release readiness

Deliver:

- Full migration rehearsal.
- Full test suite.
- Security and ownership audit.
- Provider failure tests.
- Task retry and duplicate-execution tests.
- Upload/file-limit tests.
- Production configuration check.
- Backup/restore and rollback runbook.
- Deployment documentation.

Exit criteria: release acceptance criteria are evidence-backed; no critical authorization or data-integrity issues remain.

## 20. Definition of done

The backend implementation is not complete when endpoints exist. It is complete when:

- It runs against SQLite in development.
- It is configured and verified for production migration to PostgreSQL/AWS RDS.
- APIs are available under `/api/v1/`.
- Registration, login, logout, current-user, and session expiry behavior work.
- Reader, author, and admin authorization is enforced server-side.
- Authors can manage only their own content and AI context.
- Public readers see only published content.
- Categories, search, pagination, comments, moderation, and media work.
- Publishing transitions are explicit, validated, and auditable.
- S3-compatible media storage works with validation and cleanup behavior.
- In V2, Celery and Redis process long-running jobs.
- Anna conversations and messages persist.
- Research jobs persist status and sources.
- Titles, outlines, drafts, and revisions are represented as generated artifacts.
- AI failures are safe, observable, retryable where appropriate, and do not overwrite saved work.
- AI never publishes without explicit human approval.
- External providers are mocked in automated tests.
- API errors are consistent and safe.
- Secrets use environment variables.
- No hardcoded credentials exist.
- Frontend code is not overwritten.
- No Flask, microservices, multi-tenancy, reader-side AI, vector database, or unrequested frontend work is added.

## 21. Explicit non-goals

- Flask backend or Flask sidecar.
- Microservices.
- Multi-tenant organizations.
- Reader-side AI assistant or reader chat.
- Autonomous publishing.
- AI output without human review.
- Vector database without a confirmed retrieval requirement.
- LangGraph or complex agent architecture without a concrete requirement.
- Payments or subscriptions.
- Social messaging.
- Native mobile applications.
- Video hosting.
- Blockchain/Web3 functionality.
- Advanced recommendations or enterprise analytics.
- Unrequested frontend redesign.

## 22. Open implementation decisions

**Settled in code:** custom `User`; one `BlogPost` table with status; authors publish/unpublish their own complete posts; signed-in comments are public immediately; LLM via AICredits with Composer Nemotron and Anna GPT-5.5; Tavily for images; no leftover `blog_main` routes.

Still open:

1. Exact PostgreSQL, Redis, Celery, and object-storage deployment provider.
2. Budget limits and retention/deletion for prompts, conversations, and artifacts.
3. Rich-text editor storage/rendering format.
4. API schema publication beyond `/api/v1/`.
5. In-app admin user-management beyond Django admin.
6. Whether email verification / password reset is required before production.

These decisions must be resolved before the implementation phase that depends on them. Do not silently choose a value that changes authorization, data retention, migration safety, or provider cost.

