# SwiftPost Rebuild — Product Requirements Document

**Status:** Aligned with the live writer-platform implementation  
**Product:** SwiftPost  
**Document owner:** Product / Engineering  
**Date:** 30 October 2026  
**Release target:** First production-ready rebuild  

> **Implementation note, 30 October 2026:** Signup creates an author. Authors publish and unpublish their own complete posts. Admins can unpublish any live post. Composer conversations create and refine private drafts (Nemotron) with optional Tavily image suggestions. Anna's current UI is a one-shot draft review with a loading pipeline, not a chat sidebar. Anna live research, Celery, and Redis remain V2. AI never publishes.  

---

## 1. Executive summary

SwiftPost is a secure, role-based, AI-assisted **writer platform**. Anyone who registers becomes an author and can write, review with Anna, and publish their own blogs. The first release covers public discovery, categories, search, accounts, comments, media, the author desk, Composer, and Anna review. Anna's source-aware live research workflow is V2.

Anna is an assistive reviewer, not a publisher. Composer writes a private draft the author can edit. The author remains responsible for editing, approving claims, and clicking Publish.

This release is a single-platform product. It is not a multi-tenant SaaS product, does not include a reader-side AI assistant, and does not attempt fully automated fact-checking.

## 2. Problem

The current SwiftPost application can publish and organize blog content, but its role boundaries, ownership checks, and production-readiness are inconsistent. Authors also lack an integrated way to research a topic, shape an article, and preserve the sources behind important claims. They must move between unrelated tools, which increases drafting time and makes source quality and author accountability difficult to verify.

Readers need a dependable way to discover and read organized articles. Authors need a safe, efficient drafting workflow. Administrators need platform-level control over users, content, categories, comments, and publishing quality.

The core problem is therefore not simply “add AI.” It is to make publishing trustworthy and efficient while keeping authority and accountability with the right human role.

## 3. Product outcome

After the rebuild:

- A reader can discover, search, and read published posts with clear metadata and source context.
- An authenticated author can securely create, edit, save, publish, unpublish, and manage only their own content.
- Composer retains author-owned conversations that create and refine private drafts. Anna reviews an owned draft in a one-shot review UI; Django still has Anna conversation APIs, but the browser does not expose a chat sidebar.
- Every AI-assisted result is visibly distinct from author-approved content and can be accepted, edited, or rejected.
- No AI-generated or unreviewed research is published automatically.
- Admins can manage platform users, categories, posts, comments, publishing permissions, and flagged content.
- Protected operations reject unauthorized access consistently, including direct endpoint access.
- The application has a maintainable production foundation rather than relying on development-only assumptions such as SQLite.

## 4. Goals and non-goals

### Goals for the first release

1. Rebuild the core public blogging experience.
2. Establish explicit reader, author, and admin permissions.
3. Establish secure post ownership and moderation rules.
4. Provide a complete draft-to-publish workflow.
5. Add persistent Composer chats that create private drafts, plus Anna one-shot review, with explicit human Publish.
6. Preserve AI message provenance and visibly distinguish AI suggestions from author-approved content.
7. Move the persistence and deployment design toward production readiness.
8. Provide validation, error handling, auditability, logging, and tests for critical paths.
9. Give authors durable, owner-scoped Composer chat history so they can resume a drafting session after refresh or a later sign-in. Anna review remains one-shot in the current UI.

### Explicit non-goals

- Reader-side AI chat, summaries, or explanations.
- Multi-tenant organizations or separate customer workspaces.
- Payments, subscriptions, or monetization.
- Native mobile applications.
- Real-time collaborative editing or live chat.
- Social followers, direct messaging, or social feeds.
- Video hosting.
- Autonomous publishing.
- Fully automated fact-checking or a guarantee that AI output is true.
- Advanced enterprise analytics or complex recommendations.
- Blockchain/Web3 features.
- A general-purpose unrestricted chatbot.
- Anna live research, research jobs, source collection, Celery/Redis workers, retries, cancellation, and job polling in V1. These are explicitly deferred to V2.

## 5. Users and roles

### Reader / anonymous visitor

Can browse public content, filter by category, search, open a published post, inspect its metadata and sources, and view approved comments. A reader may be required to authenticate before commenting.

### Authenticated reader

Has all visitor capabilities and may submit comments subject to moderation. New self-serve signups are **authors**, not readers. `reader` is retained for demotion and tests. A reader must not receive another author's private drafts.

### Author

Created on registration. Can create and manage their own drafts and posts, use Composer and Anna, upload or select featured images, and **publish or unpublish their own complete posts**. They cannot access another author's private content.

### Admin

Assigned in Django admin, not via the register form. Can manage categories, unpublish any live post, deactivate users, and approve comments. Admin permissions are platform-level and must be protected separately from author ownership rules. Admins do not have to approve every post before it goes live.

### Permission principle

Authentication proves who the user is. Authorization determines what that user can do. Email address alone must not be treated as an authorization identity. Every protected action must check both the user's role and the object's ownership or moderation scope.

## 6. Core user journeys

### Journey A — Discover and read

1. Visitor lands on the homepage.
2. Visitor sees published posts, featured content, categories, and useful metadata.
3. Visitor searches or filters by category.
4. Visitor opens a post detail page.
5. Visitor reads the article, sees author/date/category information, and can inspect source references when present.
6. Visitor views approved comments.
7. Authenticated reader submits a comment, receives a clear status, and understands whether moderation is pending.

### Journey B — Register and become an author

1. Visitor opens registration.
2. System validates input and creates an **author** account. Role, staff, and superuser fields in the body are rejected.
3. User logs in and is routed to the author desk (`/dashboard`).
4. Composer, Anna, Stories, and the editor are available immediately.
5. Unauthorized users attempting another author's private routes receive a safe 404/403 and are not shown privileged data.

### Journey C — Create a manual draft

1. Author opens **New story** or **Stories**, or continues from Overview.
2. Author enters title, body, category, featured image, metadata, and optional sources.
3. System validates required fields, media type/size, and content state.
4. Author saves a draft.
5. Draft remains private to the author and authorized admins.
6. Author reopens and edits the draft later.

### Journey D0 — Create and continue a Composer draft chat

1. Author opens Composer from the workspace navbar.
2. Author selects an existing Composer chat or creates a new one from a title or writing request.
3. Composer stores the author message and writes a complete private draft: title, excerpt, and body.
4. The author can continue the same chat with refinement requests and reopen it after refresh or a later sign-in.
5. The result stays in `draft`. Featured-image suggestions may appear beside the draft. It is not published.
6. Author opens the draft from **Stories** or **Open in editor**, or sends it to Anna for a review pass.
7. Author remains responsible for editing and clicking **Publish**.

### Journey D — Review with Anna

1. Author opens Anna from the navbar or the editor (`/anna?post={id}`).
2. Author chooses one owned saved draft.
3. Anna shows a loading pipeline, then returns strengths, gaps, and suggested edits. The post status does not change.
4. Author copies notes as needed and edits in the normal editor.
5. Live research, sources, and a chat sidebar are V2 / not current UI. Django may still persist Anna conversation rows from the review action.

### Journey E — Publish and take down

1. Author completes title, excerpt, body, and an active category, then clicks **Publish**.
2. The post appears on Discover.
3. The author can **Unpublish** their own live post. An admin can unpublish any live post.
4. Only `published` posts appear on public discovery surfaces.

## 7. Functional requirements

### 7.1 Public content discovery

The system must:

- Show only posts in the public “published” state on public discovery surfaces.
- Support homepage listing, featured/recent content, pagination or an equivalent bounded loading strategy, and empty states.
- Support category listing and category-filtered results.
- Support search over the agreed post fields, with the user's search term retained in the interface.
- Provide a stable, human-readable post URL.
- Provide a useful not-found page for missing, deleted, or unpublished posts.
- Prevent draft content from being discoverable through search, direct URLs, feeds, or related-content queries.

### 7.2 Post content and lifecycle

Each post must support, at minimum:

- Author ownership.
- Title and stable slug.
- Body content.
- Category.
- Optional tags or keywords if retained during shaping.
- Featured image/media.
- Summary/excerpt.
- Publication metadata.
- Content status.
- Created, updated, and published timestamps.
- Source references where applicable.
- Moderation or review notes where applicable.

Live lifecycle:

```text
draft / unpublished / changes_requested / leftover in_review
        → owning author or admin Publish → published
published → owner or admin Unpublish → unpublished
non-published statuses → archived
```

A post cannot become public merely because an AI request completed or because a draft was saved. `submit` / `in_review` remain in the API for leftover rows; the writer UI publishes directly.

### 7.3 Author dashboard

The dashboard must provide:

- A list of the author's own drafts, published posts, and other statuses (**Stories** plus Overview).
- Clear status labels and last-updated timestamps.
- Create, edit, save, publish, unpublish, and delete/archive actions subject to state and permission rules.
- Ownership-safe detail and edit routes.
- Validation errors associated with the relevant field or action.
- Safe recovery from failed saves and failed AI operations without silently losing the author's work.

### 7.4 Comments

The system must:

- Allow authenticated users to comment on eligible published posts.
- Validate and normalize comment input.
- Apply a defined initial moderation policy: approved immediately, pending moderation, or a hybrid configured by admin.
- Show only approved comments publicly.
- Allow admins to approve, hide, delete, or otherwise moderate comments.
- Prevent comments on posts that are not eligible for public interaction.
- Avoid exposing private user or moderation data in public responses.
- Confirmed addition: authenticated users may like a published post. Likes toggle per user and never publish a post.

### 7.5 Media uploads

The system must:

- Accept only explicitly allowed image types.
- Enforce file-size and dimension limits.
- Generate safe storage names rather than trusting client-provided paths.
- Validate uploaded content beyond filename extension where practical.
- Avoid serving executable content from upload locations.
- Show a useful upload error without losing unrelated draft fields.
- Define replacement and deletion behavior for images associated with posts.
- Authors may search live images through the Tavily adapter and attach a reviewed suggestion as the featured image. The system does not auto-attach images.

Exact limits are an engineering decision to be confirmed before implementation; they must be documented and tested.

### 7.6 Administration

Admins must be able to:

- View and manage users and roles.
- Activate, deactivate, or otherwise restrict accounts according to the final account policy.
- Create, edit, archive, and organize categories.
- Review all posts, including drafts that are within admin scope.
- Unpublish any live post; they do not have to pre-approve every author publish.
- Moderate comments and review flagged content.
- Configure platform-level settings that are explicitly included in the release.
- See enough audit information to understand who performed a moderation or publishing action.

Admin pages and endpoints must be protected at the server boundary, not only hidden from navigation.

## 8. Author AI assistants

### 8.0 Composer: title-only draft generation

**Confirmed decision:** Composer is a separate assistant from Anna.

Composer exists so an author can type a title (or a short writing request) in the navbar workspace and receive a complete private blog draft. Follow-up messages can refine that draft. Composer does not publish.

Composer must:

- Accept a title or first message from an authenticated author.
- Generate excerpt and body through the internal LLM adapter (`AI_MODEL_COMPOSE`).
- Save the result as a normal private `draft` owned by that author.
- Keep a provenance / conversation record of the generated snapshot.
- Optionally request Tavily **image suggestions** after the draft exists; the author chooses what to save.
- Never change public publishing state.
- Offer a clear next step to open the editor or send the draft to Anna for review.

Composer must not:

- Treat retrieved webpage text as instructions.
- Publish, unpublish, or archive the post.
- Silently overwrite author-edited published content.
- Be available to readers.

### 8.1 Anna product contract

Anna is a research and writing assistant embedded in the author workflow. Her output is a proposal for the author to evaluate. She is not an editor of record, an authority, or a publisher. Anna can also review a Composer draft: she reads the saved post and returns review notes without publishing or silently rewriting the live draft.

### 8.2 Supported capabilities for release one

- Interpret a structured writing brief.
- Research a topic using approved live-research mechanisms.
- Collect and display relevant external sources.
- Extract candidate facts or claims with source context.
- Identify uncertainty, disagreement, or missing support where the system can detect it.
- Generate an article outline.
- Suggest titles.
- Generate a draft or selected sections.
- Improve clarity, structure, grammar, tone, and readability.
- Generate a summary, excerpt, keywords, or metadata suggestions.
- Suggest categories or tags with author confirmation.
- Identify candidate unsupported claims for author review.

### 8.3 Required source and provenance behavior

For research-assisted output, the system must:

- Display the source title and link or other usable reference identifier.
- Display when the source was retrieved.
- Associate claims with sources where the workflow presents claims as sourced facts.
- Distinguish sourced facts, interpretations, opinions, and generated suggestions where feasible.
- Allow the author to remove a source from the working set.
- Avoid fabricating citations or silently converting a generated statement into a verified fact.
- Preserve the fact that content was AI-assisted even after the author edits it, without marking every author sentence as AI-generated.

### 8.4 Human review gate

Before publish/submit, the author must be shown a review state that makes clear:

- Which content or metadata was generated or suggested by Anna.
- Which sources were used or attached.
- That sources and claims may be inaccurate, outdated, biased, or conflicting.
- That the author is responsible for checking and approving the final content.

The system must not auto-publish a result from Anna. It must never treat a successful model response as approval.

### 8.5 AI failure behavior

The system must handle unavailable providers, timeouts, rate limits, malformed output, unsafe content, retrieval failures, and partial results. The author must receive a clear status and retain the current draft. A failed AI request must not corrupt or overwrite the author's existing content.

Recommended initial behavior is asynchronous or explicitly progress-aware for long research/generation requests, with retry limits, cancellation where practical, and server-side logging that excludes secrets and unnecessary sensitive content.

### 8.6 Safety and trust boundaries

External pages and retrieved text are untrusted input. The system must treat source content as data, not instructions to Anna or the application. The design must account for prompt injection, malicious links, excessive content, copyright concerns, biased sources, conflicting claims, and provider/API cost controls.

The first release does not promise factual correctness. Its promise is transparent assistance with visible sources and human review.

## 9. Information architecture

### Public surface

- Home
- All posts / browse
- Category results
- Search results
- Post detail
- Login
- Registration
- Comment interaction
- About / platform information if retained from the current application

### Authenticated author surface

- Dashboard overview
- My posts
- New post
- Composer (title-only AI draft)
- Edit post
- Draft review state
- Anna workspace
- Source/research panel
- Account/profile area if retained in the shaped scope

### Admin surface

- Admin overview
- Users and roles
- Posts and review queue
- Categories
- Comments and flags
- Platform settings
- Audit activity where included

Navigation must be role-aware, but route protection must remain server-enforced.

## 10. Data and domain model

The final schema is an engineering responsibility, but the product model must support these concepts:

- **User:** identity, account state, role/permissions, timestamps.
- **Role/permission:** explicit authorization policy; do not infer permissions from UI location.
- **Category:** name, slug, description/metadata as needed, active/archive state.
- **Post:** owner, content, slug, category, media, status, timestamps, publication data, review data.
- **Comment:** post, author, body, moderation status, timestamps, moderation actor.
- **Media asset:** owner/context, storage key, type, size, validation state, lifecycle.
- **Source reference:** canonical URL or provider reference, title, retrieval time, trust/selection state, optional extracted citation details.
- **AI assistance session/request:** author, input brief, capability, status, timestamps, provider/request metadata safe to retain, output references.
- **AI output/provenance record:** generated artifact or linkage needed to distinguish suggestions from approved post content.
- **Moderation/audit event:** actor, action, object, previous/new state where appropriate, timestamp, safe reason/note.

The schema should support soft deletion or archival where the product needs recovery, moderation history, or stable references. Deletion semantics must be explicitly decided before implementation.

## 11. Security, privacy, and reliability requirements

### Authentication and authorization

- Use a supported, secure authentication flow with password handling delegated to the framework or approved identity provider.
- Protect login, registration, session, password-reset, and logout behavior against common abuse.
- Enforce authorization on every dashboard and mutation endpoint.
- Check object ownership for author operations.
- Apply least privilege by default.
- Prevent privilege escalation through submitted role fields, object IDs, or forged form/API requests.
- Use CSRF protection where cookie-based sessions are used.

### Content and input safety

- Validate and normalize all user input server-side.
- Sanitize or safely render rich text according to the chosen editor/content format.
- Prevent XSS through post bodies, comments, titles, metadata, filenames, and AI output.
- Rate-limit or otherwise protect comment and AI request abuse.
- Protect external fetches against SSRF and unsafe redirects if the server retrieves URLs.
- Do not expose provider keys, session secrets, internal stack traces, or private source metadata.

### Data and deployment

- Use a production-capable relational database for production; SQLite may remain a local development option only if behavior is kept compatible and documented.
- Store secrets in environment/configuration management, never in source code.
- Separate static assets, user media, and application code according to deployment needs.
- Define backup, restore, migration, and rollback expectations before production launch.
- Log security-relevant failures and moderation/publishing actions without logging sensitive secrets.

### Reliability

- A failed external AI or research provider must not make the core blog editor unusable.
- Core read and write flows must provide clear error states and preserve user work.
- AI requests must have bounded timeouts, retries, and cost controls.
- Health checks and actionable logs must exist for the web application and any background worker or provider integration.

## 12. Recommended technical direction

These are recommended defaults, not final product decisions:

- Keep Django as the application framework during the rebuild unless a deliberate migration decision is approved.
- Separate domain responsibilities into clear application modules rather than allowing dashboard views to own all business rules.
- Use a production relational database, preferably PostgreSQL, for deployed environments.
- Use Django's built-in authentication/authorization primitives or a deliberately selected identity provider; document the choice and migration path.
- Keep public rendering and author/admin workflows consistent with the selected frontend strategy; do not introduce a second frontend stack unless it materially improves the product outcome.
- Isolate Anna behind a provider-agnostic service boundary so model/provider changes do not leak across the post domain.
- Prefer structured AI outputs validated against schemas over parsing free-form model text.
- Treat external retrieval as a separate, observable service step with source records and timeouts.
- Add automated tests around permissions, state transitions, public visibility, source/provenance rules, and AI failure recovery.

Engineering should confirm these defaults during shaping. The PRD defines behavior and boundaries; it does not mandate every class, endpoint, library, or visual component.

## 13. Success metrics

Metrics should be instrumented only after event names and definitions are agreed. Initial targets below are proposed working targets for the first release and should be baselined during pilot use.

### User outcome metrics

- At least 80% of pilot authors can create and save a draft without assistance from the team.
- At least 70% of pilot authors can complete the Anna workflow from brief to reviewed draft on their first attempt.
- Median time from writing brief to first usable draft is reduced by at least 30% compared with the author's existing manual workflow.
- At least 80% of pilot authors report that source visibility improves their ability to review AI output.
- Public readers can reach a desired post from homepage, category, or search without encountering unauthorized or unpublished content.

### Quality and trust metrics

- 100% of tested publish paths require explicit author/admin approval according to the configured workflow.
- 100% of tested author mutation paths reject cross-author access.
- 100% of AI research results shown to authors include retrieval context and source references when sources were used.
- Zero known critical or high-severity authorization defects at release.
- AI failure recovery preserves the last saved author draft in all tested failure scenarios.

### Operational metrics

- Track AI request success, timeout, provider error, retry, cancellation, and cost-related events.
- Track draft save failures and publish/review transition failures.
- Track public page error rate and search/category empty-result behavior.
- Track moderation backlog and time from submission to decision during pilot.

The metrics are decision filters, not vanity targets. If a feature does not improve the author, reader, admin, trust, or operational outcomes above, it should require explicit justification to enter this release.

## 14. Acceptance criteria

### Release-level acceptance

- A new or migrated user can authenticate and is routed to the correct authorized experience.
- Anonymous users can browse only published public content.
- Readers can browse, search, filter, and open post details.
- Authors can create, save, edit, and manage their permitted posts.
- An author cannot view, edit, delete, submit, or publish another author's private post through UI or direct request.
- Admins can manage users, categories, posts, comments, and review decisions.
- Comments follow the agreed moderation policy and only approved comments are public.
- Media uploads enforce the agreed type, size, and storage rules.
- Anna can complete the supported brief → research → source review → outline/title/draft assistance flow.
- Anna output is visibly marked as requiring author review.
- Anna cannot publish a post or bypass post permissions.
- Source references are visible, removable, and linked to the relevant research result where applicable.
- AI/provider failures produce recoverable error states and do not overwrite saved work.
- Production configuration does not require SQLite or hardcoded secrets.
- Critical tests cover authentication, authorization, post visibility, lifecycle transitions, comments, uploads, and AI failure/provenance behavior.
- Logging and health checks are sufficient to diagnose failed requests without exposing secrets.

### Definition of done for a feature

A feature is not complete when the happy-path screen works. It is complete when the behavior is implemented, permission boundaries are tested, error and empty states are handled, observability is present where relevant, documentation is updated, and the behavior has been verified in the supported deployment configuration.

## 15. Delivery shape

The work should be shaped into vertical slices that each produce a demonstrable outcome:

### Slice 1 — Foundation and authorization

Production configuration, database direction, authentication, role model, permission helpers/policies, base layout, error handling, and test harness.

### Slice 2 — Public publishing experience

Post domain cleanup, published visibility, homepage, categories, search, detail pages, pagination, metadata, and media handling.

### Slice 3 — Author workflow

Dashboard, ownership-safe CRUD, draft states, submit/review behavior, author feedback, and safe deletion/archive semantics.

### Slice 4 — Admin moderation

User/role management, category administration, post review queue, comment moderation, flags, and audit events.

### Slice 5 — Anna research foundation

Provider boundary, structured requests, source retrieval, source records, timeouts, failure handling, logging, cost controls, and prompt-injection safeguards.

### Slice 6 — Anna author experience

Brief capture, research view, source review, outline/title/draft actions, improvement actions, provenance display, and insertion into the editor.

### Slice 7 — Hardening and release

Migration strategy, backup/restore rehearsal, security review, performance checks, browser verification, accessibility pass, monitoring, documentation, and pilot release.

Each slice should be reviewed with product, design, and engineering before the next slice expands scope.

## 16. Risks and mitigations

| Risk | Impact | Mitigation / release rule |
|---|---|---|
| AI produces incorrect or outdated claims | Readers lose trust | Show sources and retrieval time; require human review; do not claim factual guarantees |
| External pages contain prompt injection or malicious content | Anna or the application behaves unsafely | Treat retrieved text as untrusted data; isolate tools; validate output; restrict fetch behavior |
| Source quality is inconsistent | Authors accept weak evidence | Let authors inspect/remove sources; show source metadata; document limitations |
| AI cost or latency grows unexpectedly | Poor UX or unsustainable operation | Set timeouts, quotas, retries, request budgets, and monitoring before pilot |
| Permission bugs expose private content | Severe security and trust failure | Centralize policy checks; test direct endpoint access and cross-author cases |
| Rebuild changes too much at once | Delivery stalls | Use vertical slices; define migration boundaries; keep non-goals explicit |
| Rich text or uploads create security vulnerabilities | XSS, malware, or storage abuse | Constrain formats, validate server-side, sanitize output, isolate media, and test malicious inputs |
| Existing data migration is incomplete | Lost or inconsistent content | Inventory current data; write migration mapping; rehearse backup and rollback |
| AI output is mistaken for approved authorship | Accountability becomes unclear | Persist provenance and show review gate; keep final post approval explicit |

## 17. Migration and rollout principles

The rebuild must begin with an inventory of current users, roles, posts, categories, comments, media, and status values. Existing data should be mapped to the new domain model before implementation commits to destructive changes.

Recommended rollout:

1. Build and test the new domain behavior against a non-production database.
2. Rehearse a repeatable data migration and verify counts, relationships, slugs, media, and permissions.
3. Run security and authorization checks against direct routes and submitted IDs.
4. Pilot the author workflow with a small set of authors before enabling Anna broadly.
5. Observe AI success, source quality, latency, cost, and author review behavior.
6. Release publicly only after rollback, backup, health check, and moderation procedures are documented.

The migration strategy may be in-place, staged, or greenfield with import. Engineering should choose based on data integrity and rollback safety; the product requirement is that existing valid content is not silently exposed, lost, or assigned to the wrong owner.

## 18. Confirmed decisions, recommended defaults, and open questions

### Confirmed by the brief

- SwiftPost remains a single-platform product.
- Anna is author-facing only in the first release.
- Reader-side AI is out of scope.
- AI must not publish automatically.
- Authors remain responsible for reviewing and editing output.
- Source visibility and research context are required for live-research output.
- Core blogging, dashboard, comments, media, role-based permissions, and admin moderation are in scope.
- Production engineering quality and secure ownership checks are release requirements.

### Confirmed in the live implementation (30 October 2026)

- Registration creates `author`. `admin` is not self-assigned. `reader` is not the signup default.
- Authors publish and unpublish their own complete posts. Admins can unpublish any live post.
- Any signed-in user can comment on a published post. Comments are public immediately; they do not wait for admin review.
- Composer model: `AI_MODEL_COMPOSE` / `nvidia/nemotron-3-super-120b-a12b`. Anna review: `AI_MODEL_REVIEW` / `openai/gpt-5.5`. Search: Tavily behind an adapter.
- Composer and Anna refuse illegal or harmful how-to requests. A Composer refusal does not create or overwrite a draft. Anna's review uses Verdict, Strengths, Gaps, Suggested edits, and Do this first.
- Anna's current browser UI is one-shot review, not a chat product.
- Auth stays Django sessions (not JWT). Each browser tab may send `X-Session-Key` from `sessionStorage` so login or logout in another tab does not take over this tab.

### Recommended defaults still open

- PostgreSQL is the production database direction.
- A structured rich-text format with safe rendering is preferred over storing arbitrary HTML.
- Anna live research remains asynchronous / V2.
- AI provenance is retained at the assistance/session level.

### Open questions requiring a product/engineering decision

1. Should an additional Editor/Manager role exist later?
2. What in-app user disable / ban UI is needed beyond Django admin?
3. What exact comment moderation policy is preferred for later revisions?
4. Which content editor and storage format should be used?
5. Which search behavior is required for launch: basic database search or a dedicated search system?
6. What budget limits apply? (Composer Nemotron, Anna GPT-5.5, and Tavily images are already wired.)
7. What source types are acceptable, and should paywalled or low-quality sources be filtered?
8. What exact media limits, image processing, and storage provider are required?
9. What existing data must be migrated, and what data can be archived?
10. What retention policy applies to AI prompts, generated outputs, source snapshots, and audit logs?
11. Is account email verification/password reset required for the first release?
12. What accessibility and browser support baseline will be enforced?
13. What target deployment environment, uptime expectation, and backup/restore objective apply?
14. Should authors be able to edit AI-assisted text directly in the main editor, or must they explicitly insert accepted blocks?

## 19. Product review checklist

Before changing product behavior, the team should be able to answer “yes” to the following:

- Is the core problem understandable without reading the technical solution?
- Can we describe the first release in one sentence?
- Are the non-goals visible enough to prevent scope creep?
- Are public, author, and admin permissions explicit?
- Can we explain the post lifecycle from draft to public and back?
- Can we explain where Anna stops and the author takes responsibility?
- Can an engineer see the end-to-end boundary of each delivery slice?
- Can design explore the workflow without being locked into premature visual details?
- Can we test the important security and trust behaviors directly?
- Can we measure whether the rebuild is faster, safer, and more trustworthy?

## 20. One-sentence product definition

SwiftPost is a secure, role-based publishing platform where authors use Anna to research and prepare source-aware blog content, admins protect publishing quality, and readers discover and consume organized articles with confidence.

---

## 21. Targeted product-context update

This section is an additive update to the existing PRD. It supersedes only the affected assumptions and requirements below; all other confirmed decisions remain in force.

### 21.1 Affected existing sections

The following sections are affected by the updated product context:

- **Section 1 — Executive summary:** Anna is now a persistent conversation-based authoring workspace, not only a set of isolated writing actions.
- **Section 3 — Product outcome:** authors must be able to continue conversations and attach eligible existing posts or drafts as context.
- **Section 4 — Goals and non-goals:** persistent AI workflow and first-version API delivery are explicit goals; Anna remains bounded to authoring.
- **Section 6 — Core user journeys:** Journey D must include starting/resuming chat, selecting post context, iterative chat refinement, and explicit final confirmation.
- **Section 7 — Functional requirements:** add requirements for the AI workspace, conversation selection, context selection, API-backed workflow, and final-content transfer.
- **Section 8 — Anna: author AI workflow:** replace the isolated action model with a full conversation-based workflow.
- **Section 9 — Information architecture:** add the AI conversation sidebar and the main editor/chat workspace.
- **Section 10 — Data and domain model:** persist conversations, messages, context selections, research jobs, sources, generated artifacts, revisions, statuses, errors, retries, and approval state.
- **Section 11 — Security, privacy, and reliability:** enforce ownership checks for AI context selection and protect API/session boundaries.
- **Section 12 — Recommended technical direction:** the proposed Next.js/React frontend, Django REST Framework API, PostgreSQL, Celery, Redis, S3-compatible storage, and replaceable AI/search adapters become the working technical direction.
- **Section 14 — Acceptance criteria:** add API, persistence, conversation resume, context authorization, and explicit confirmation criteria.
- **Section 15 — Delivery shape:** split Anna work into persistent conversation/API foundations and the workspace experience.
- **Section 18 — Decisions and open questions:** remove Flask and deferred-DRF assumptions; retain only unresolved product choices.

### 21.2 Removed or outdated assumptions

- Flask is not part of the architecture and must not be introduced.
- Django REST Framework is not deferred; it is required from the first version.
- Anna is not limited to one-shot brief-to-draft actions. The release includes persistent, resumable conversations.
- A single temporary AI request record is insufficient. The system must persist the conversation and its related research and generation work.
- The AI workflow is not limited to starting from a new post. An author may select an eligible existing draft, unpublished post, permitted published post, or prior AI-generated draft as context.
- The exact frontend layout remains open, but the existence of an AI workspace, conversation list, and context-selection capability is no longer optional.

### 21.3 Updated feature scope

The first release includes:

- Public discovery, category browsing, search, post details, registration, login/logout, comments, media, dashboards, moderation, and publishing workflow.
- Role-based access for readers, authors, and admins.
- Author-owned post and draft management.
- A persistent Anna workspace with a main writing/editor area, AI chat panel, and selectable conversation sidebar.
- Starting a new AI conversation and resuming an existing conversation.
- Live web research, source collection, source metadata, source URLs, retrieval timestamps, and source review.
- Multiple title suggestions, outline generation, draft generation, and chat-based revision requests.
- Requests to improve, shorten, expand, restructure, or rewrite selected content.
- Selecting an eligible existing post or draft as conversation context.
- Transfer of reviewed generated content into the normal blog editor.
- Explicit final author confirmation before save-as-draft or normal publishing workflow.

The release continues to exclude reader-side AI, multi-tenancy, payments, mobile apps, real-time social chat, autonomous publishing, human-review bypasses, advanced recommendations/analytics, video hosting, live collaborative editing, and Web3 functionality.

### 21.4 Updated Journey D — conversation-based Anna authoring

1. Author opens the Anna workspace and starts a new conversation or resumes an existing one.
2. Author provides a topic or structured writing brief.
3. Author optionally selects an eligible draft or post as context.
4. The API creates or resumes the conversation and records the selected context.
5. Anna runs a research job through the approved search-provider adapter.
6. The workspace displays research status, retrieved sources, URLs, retrieval time, and source-quality/conflict warnings where available.
7. Anna suggests multiple titles and generates an outline.
8. Anna generates a draft or selected sections.
9. Author continues refining the result through chat, including improve, shorten, expand, restructure, and rewrite requests.
10. The system persists messages, generated artifacts, revisions, statuses, errors, and retries without treating every response as a blog post.
11. Author reviews sources and generated content, edits the result, and explicitly confirms the final content.
12. Confirmed content is transferred into the normal editor and can then be saved as a draft or published through the normal permission and publishing workflow.

### 21.5 New AI workspace requirements

The authoring experience must provide:

- A main writing/editor area for the working blog content.
- An AI chat panel for the active conversation.
- A left-side panel or sidebar listing existing AI conversations.
- Conversation selection and continuation.
- A control for selecting or changing the eligible post/draft used as context.
- Organized views for chat history, sources, outlines, titles, drafts, and revisions.
- Clear separation between generated suggestions, author edits, and final approved content.
- A recoverable state when research or generation fails.
- A final review/confirmation state before content enters the standard save or publish flow.

The exact panel arrangement, responsive behavior, and visual treatment remain design decisions. The workflow capabilities above are product requirements.

### 21.6 Updated Anna workflow contract

Anna's first-release workflow is:

```text
Start/resume conversation
        ↓
Provide topic or writing brief
        ↓
Select eligible post/draft context (optional)
        ↓
Run live web research
        ↓
Collect, organize, and display sources
        ↓
Suggest titles
        ↓
Generate outline
        ↓
Generate draft or sections
        ↓
Refine through conversation
        ↓
Review sources and generated content
        ↓
Explicitly confirm final content
        ↓
Transfer to normal editor
        ↓
Save draft or publish through normal workflow
```

Anna must never publish silently. A successful generation response is not an approval event. The final publishing action must use the same authorization, validation, status-transition, and audit rules as manually authored content.

### 21.7 Updated API/backend requirements

The backend architecture is Django only, with Django REST Framework required from the first version. The API must expose authenticated, validated, permission-checked endpoints for:

- Authentication and user identity.
- Blogs, drafts, post details, and post lifecycle transitions.
- Categories.
- Comments and moderation.
- Media uploads.
- Publishing and explicit final-content approval.
- AI conversation creation, listing, retrieval, resume, and archival/deletion behavior where approved.
- Chat messages and assistant responses.
- Existing post/draft context selection.
- Research job creation, status, retry, and failure reporting.
- Source listing, selection, removal, and metadata.
- Generated titles, outlines, drafts, and revision artifacts.
- Generation requests and generation status.

Every API mutation must enforce authentication, role authorization, object ownership, input validation, safe error responses, and auditability where the action changes publishing or moderation state. Direct API access must enforce the same rules as the UI.

Recommended API behavior is resource-oriented and status-aware. Long-running research and generation should be represented by persisted jobs or requests rather than relying on an unbounded synchronous HTTP request.

### 21.8 New persistence requirements

The data model must support, at minimum:

- **AI conversation:** owner, title/label, lifecycle status, timestamps, and optional active post/draft context.
- **Chat message:** conversation, sender type, content, sequence, status, timestamps, and safe error metadata.
- **Conversation context selection:** conversation, selected post/draft, selecting user, validity state, and timestamps.
- **Research job:** conversation/request, query or brief reference, provider status, progress/status, retry count, error state, timestamps, and cost/usage metadata safe to retain.
- **Source:** canonical URL, title, provider reference, retrieved timestamp, content metadata, selection/trust state, and relationship to research jobs or generated artifacts.
- **Generated artifact:** conversation/request, artifact type (title, outline, draft, section, summary, revision), content, status, source references, and timestamps.
- **Revision request:** requested operation, target artifact or selected content, author instruction, result status, and generated artifact relationship.
- **Approval/provenance:** what was generated, what was accepted or rejected, author confirmation, and relationship to the final post content.
- **Generation request/status:** provider-neutral request state, queued/running/succeeded/failed/cancelled state, retries, safe error information, and timestamps.

Intermediate AI artifacts must not automatically become posts. Author-approved content must remain distinguishable from generated suggestions even after transfer into the normal editor. Retention and deletion rules for prompts, messages, source data, and generated artifacts remain product decisions.

### 21.9 Updated architecture implications

The proposed working technology direction is:

- **Frontend:** Next.js, React, and TypeScript.
- **Backend:** Django only.
- **API:** Django REST Framework from version one.
- **Authentication:** Django authentication with secure HTTP-only session cookies.
- **Database:** PostgreSQL.
- **Background jobs:** Celery.
- **Queue/broker:** Redis.
- **File storage:** AWS S3 or another S3-compatible object-storage service.
- **AI orchestration:** Anna module inside the Django backend.
- **AI framework:** LangChain may be used for tools, prompts, structured output, and workflow composition.
- **Web research:** Tavily or a replaceable search-provider adapter.
- **LLM provider:** replaceable through an internal provider adapter.

This is a modular application architecture, not a microservices architecture. Do not introduce Flask, multi-tenancy, a vector database, or reader-side AI unless separately approved. Anna must be isolated behind internal service boundaries so provider changes do not leak into blog, authorization, or publishing code.

### 21.10 New security and authorization requirements

- Only the conversation owner may list, read, resume, modify, or delete their private AI conversations unless an explicit admin policy grants access.
- Authors may select only their own eligible drafts/posts as AI context.
- Admin context access must follow the admin's moderation scope and must not accidentally expose unrelated private drafts.
- API object IDs, post IDs, conversation IDs, and research job IDs must not bypass ownership checks.
- A selected post/draft must be re-authorized on every context read and generation request; an earlier valid selection must not grant permanent access after ownership or status changes.
- Conversation history and source data must not leak into another user's conversation or generation request.
- AI tools must treat retrieved webpages and source text as untrusted data, never as executable instructions.
- Provider keys, session secrets, internal prompts where sensitive, and private source metadata must not be returned to the client.
- Publishing and final approval must remain ordinary authorized domain operations, never a side effect of an AI endpoint.

### 21.11 Updated acceptance criteria

Add these criteria to Section 14:

- The API is implemented with Django REST Framework from the first version; no Flask service is required or introduced.
- An author can start a new AI conversation, see it in the conversation list, leave it, and resume it with its history intact.
- An author can select an eligible owned draft or post as context, and the selected context is persisted and visible in the workspace.
- A user cannot read or use another author's private post/draft as AI context through either the UI or direct API request.
- Research runs through a persisted job/status model and exposes source URLs, metadata, and retrieval timestamps to the author.
- The system persists chat messages, research jobs, sources, generated titles, outlines, drafts, revision requests, generation status, errors, and retries as applicable.
- Authors can request improve, shorten, expand, restructure, and rewrite operations through chat without overwriting the last saved approved content.
- Generated artifacts remain distinguishable from author-approved content.
- The author must explicitly confirm final content before it can enter the normal save or publishing workflow.
- Anna cannot publish, change post ownership, bypass moderation, or access unauthorized context.
- A failed search, model call, retry, or background job leaves the author’s latest saved post/draft intact and exposes a recoverable error state.
- All new API endpoints enforce authentication, authorization, ownership, validation, safe errors, and relevant audit events.

### 21.12 Updated delivery shape

Adjust the existing delivery slices as follows:

- **Slice 5 — Anna API and persistence foundation:** DRF resources, conversation/message models, context-selection authorization, research jobs, sources, generated artifacts, statuses, retries, and provider adapters.
- **Slice 6 — Anna workspace:** Next.js/React editor and chat layout, conversation sidebar, context selection, source review, titles, outlines, draft generation, and chat-based revisions.
- **Slice 7 — Approval and publishing integration:** provenance display, explicit final confirmation, transfer into the normal editor, normal save/publish workflow, moderation rules, and audit events.
- **Slice 8 — Hardening and release:** migration, backup/restore, security review, API/browser verification, background-job monitoring, cost controls, accessibility, and pilot release.

The earlier slices for foundation, public publishing, author CRUD, and admin moderation remain unchanged.

### 21.13 Decisions and remaining open questions

Confirmed by this update:

- Django is the only backend framework.
- Django REST Framework is required from version one.
- The working frontend direction is Next.js, React, and TypeScript.
- PostgreSQL, Celery, Redis, and S3-compatible storage are the proposed platform services.
- Anna conversations, research jobs, sources, generated artifacts, revisions, errors, retries, and statuses must persist.
- Existing eligible posts/drafts can be selected as AI context under ownership rules.
- Live web research is part of the first AI workflow.
- Final approval and publishing remain explicit human-controlled actions.

Remaining product decisions:

1. Which exact roles and permissions are enabled at launch: Reader, Author, Admin only, or additional editorial roles?
2. Which authors may publish directly, and which require admin review?
3. How long should conversations, messages, source data, prompts, and generated artifacts be retained?
4. Can an author attach a published post as context if they can edit it, and what happens when its edit permission changes mid-conversation?
5. What is the maximum number/size of selected posts, messages, and source documents allowed in one context window?
6. Which search provider and LLM provider are approved for the first release, and what are the per-user and platform budget limits?
7. Should source snapshots be stored, or only source metadata and URLs?
8. Which generated artifacts are editable independently, and which are only chat results?
9. Should the author explicitly accept individual blocks, or can the confirmed result replace the editor working copy?
10. What are the exact media limits, S3-compatible provider, and upload processing rules?
11. What API versioning and browser support baseline will be used?
12. What are the deployment, backup/restore, uptime, and background-job recovery targets?

