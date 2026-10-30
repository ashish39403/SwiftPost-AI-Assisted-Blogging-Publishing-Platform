# SwiftPost backend

Django REST API for SwiftPost. Signup creates an **author**. Authors publish and unpublish their own complete posts. Composer writes private drafts. Anna reviews them. Neither agent publishes.

The Next.js frontend is the sibling `source/` app.

## Stack

- Django 5.2 + Django REST Framework
- Session cookies + CSRF (`/api/v1/auth/csrf/`)
- Custom `User` (`USERNAME_FIELD=email`), default role `author`
- SQLite locally, PostgreSQL in production
- LangChain `ChatOpenAI` behind an LLM adapter (AICredits)
- Composer model: `AI_MODEL_COMPOSE` / `nvidia/nemotron-3-super-120b-a12b`
- Anna review model: `AI_MODEL_REVIEW` / `openai/gpt-5.5`
- Tavily behind a search adapter for live images only in V1

## Local setup

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Put provider keys only in `.env`. Never commit `.env`.

## API

Base URL: `http://127.0.0.1:8000/api/v1/`

Send cookies on every request. For unsafe methods, fetch CSRF first and send `X-CSRFToken`.

| Area | Path |
| --- | --- |
| Auth | `/api/v1/auth/` |
| Blogs / drafts | `/api/v1/blogs/`, `/api/v1/drafts/` |
| Publish | `POST /api/v1/blogs/{id}/publish/` |
| Unpublish | `POST /api/v1/blogs/{id}/unpublish/` |
| Composer | `/api/v1/ai/compose/`, `/api/v1/ai/composer/conversations/` |
| Anna review | `POST /api/v1/ai/reviews/` |

See `docs/BACKEND_STATUS.md` for the live contract.

## Tests

```powershell
python manage.py test
```

Live LLM and Tavily calls stay mocked unless `ANNA_LIVE_PROVIDER_TEST=1`.
