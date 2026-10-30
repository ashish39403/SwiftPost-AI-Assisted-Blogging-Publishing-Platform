# SwiftPost

Writer platform: Django REST API in `blogging-system-yt/` and Next.js app in `source/`.

Signup creates an **author**. Authors publish their own posts. **AI never publishes.**

All documentation lives in [`docs/`](docs/):

| Doc | What it is |
| --- | --- |
| [README](docs/README.md) | Full setup, API overview, deploy |
| [Product requirements](docs/SWIFTPOST_REBUILD_PRD.md) | Scope and acceptance criteria |
| [API contract](docs/BACKEND_STATUS.md) | Live `/api/v1/` behavior |
| [Tech stack](docs/TECH_STACK.md) | Architecture baseline |
| [Backend plan](docs/BACKEND_IMPLEMENTATION.md) | Implementation notes |
| [Backend setup](docs/BACKEND.md) | Django local setup |
| [Frontend setup](docs/FRONTEND.md) | Next.js local setup |
| [Contributing](docs/CONTRIBUTING.md) | How to change the project |
| [Security](docs/SECURITY.md) | Trust boundaries and secrets |
| [Agent instructions](docs/AGENTS.md) | Product rules for contributors and agents |
| [AI conversation V1](docs/AI_CONVERSATION_V1.md) | Composer chat and Anna review |

## Quick start

```powershell
cd blogging-system-yt
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

```powershell
cd source
npm install
npm run dev
```

Open http://localhost:3000. Put provider keys only in `blogging-system-yt/.env`. Never commit `.env` or `.env.local`.
