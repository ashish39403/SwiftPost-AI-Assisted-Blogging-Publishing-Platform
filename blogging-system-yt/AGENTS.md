# SwiftPost Agent Instructions

These instructions apply to work inside `H:\Blog_Webapp\blogging-system-yt` and its descendants. The Next.js frontend is `H:\Blog_Webapp\source`. Do not modify frontend code unless the user explicitly requests it.

## Current product (follow this)

SwiftPost is a writer platform. Signup creates an **author**. Authors publish and unpublish their own complete posts. Admins can unpublish any live post. AI never publishes.

Backend: Django 5.2 + DRF modular monolith (`config/` + `apps/`). Custom email-login `User`. SQLite locally, PostgreSQL in production. Session cookies + CSRF. No JWT unless the user decides otherwise.

Composer (`AI_MODEL_COMPOSE`, default `nvidia/nemotron-3-super-120b-a12b`) writes/refines a private draft and may attach Tavily image suggestions. Anna (`AI_MODEL_REVIEW`, default `openai/gpt-5.5`) is a one-shot draft review in the current UI. Anna live research, Celery, and Redis are V2.

If a document and a user instruction conflict, follow the user's latest explicit instruction and update the docs.

## Required reading

- `../SWIFTPOST_REBUILD_PRD.md`
- `TECH_STACK.md`
- `../BACKEND_IMPLEMENTATION.md`
- `BACKEND_STATUS.md`
- Current code and migrations for the change

## Repository context

This is **not** the old server-rendered `blog_main` project. That layout is gone.

```text
blogging-system-yt/
  manage.py
  config/
  apps/accounts, users, blogs, categories, comments,
       publishing, moderation, media_assets, composer, anna, common
  tests/
```

Preserve existing user, post, category, comment, and media data unless the user authorizes destructive changes.

## Scope

In scope: readers/authors/admins, session auth, ownership, public published discovery, author drafts, publish/unpublish, comments/likes, media + live image search, Composer conversations, Anna review, `/api/v1/`.

Out of scope unless asked: Flask, microservices, multi-tenant, reader AI, autonomous publishing, LangGraph, Celery/Redis/Anna research (V2), payments, native apps, unrequested frontend redesign, re-adding Anna chat UI.

## Architecture

Django owns rules, authz, models, publishing, media, and AI adapters. Views coordinate. Services hold workflows. Serializers validate transport. Provider SDKs stay in adapters.

Every sensitive operation checks authentication, role, ownership or admin scope, object status, and transition validity. Authors only touch their own posts and AI records. UI hiding is not a security control.

## API

`/api/v1/` only for new endpoints. Errors:

```json
{"error": {"code": "POST_NOT_FOUND", "message": "The requested post could not be found.", "details": {}}}
```

Live contract is `BACKEND_STATUS.md`. Do not add V1 job-polling APIs.

Publishing:

```text
draft / unpublished / changes_requested / in_review
        →  author or admin Publish  →  published
published → owner or admin Unpublish → unpublished
non-published (except published) → archive
```

Publish requires title, excerpt, body, and an active category. Composer/Anna/save never change public state.

## Anna / Composer

Composer may generate and revise a private draft. Anna may review an owned draft. Neither publishes. Neither reads another author's private content. LangChain and Tavily stay behind adapters. Re-check ownership on every call.

## Media, security, workflow, tests, docs

Same rules as `H:\Blog_Webapp\AGENTS.md`: validate uploads, never log secrets, CSRF + narrow CORS, `rtk python manage.py check|makemigrations --check|test`, mock providers in tests, update docs when behavior changes, completion report with real test results.
