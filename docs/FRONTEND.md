# SwiftPost frontend

The SwiftPost frontend is a Next.js application for the public publication experience and the signed-in author workspace. It talks to the Django REST API with session cookies and CSRF protection; it does not store credentials, provider keys, or publishing rules in the browser.

## What is available in the live workspace

- Public landing with **live** featured/published posts, Discover (`/discover`) for everyone’s live stories, category/search browsing, and story detail pages. Dummy marketing cards are no longer used for Featured stories.
- Session-aware sign-up and sign-in flows.
- An author workspace: Overview, **Stories**, published desk, editor, Composer, Anna, admin, and settings.
- Signup creates a writer. Authors publish and unpublish their own complete posts from the editor.
- Composer conversations: a title creates a detailed private draft (Nemotron), later messages refine it, and 2–3 live photos are attached automatically. The article is rendered in the chat. Composer does not publish.
- Draft editing, seeded categories, featured-image upload or live-image selection.
- Anna one-shot draft review with a loading pipeline. Anna never publishes. There is no Anna chat sidebar.
- Workspace search, notifications affordance, and account-menu navigation.

The product requires the Django backend for real content, sessions, AI responses, images, and permissions. The UI should always reflect API errors or unavailable backend services instead of presenting them as successful live data.

## Routes

| Route | Purpose |
| --- | --- |
| `/` | Public landing page |
| `/discover` | Published-story discovery |
| `/posts/[slug]` | Published-story detail |
| `/login`, `/signup` | Authentication |
| `/dashboard` | Author overview |
| `/stories` | All of the author's drafts and posts; opens the editor |
| `/published` | The author's live posts |
| `/editor/new`, `/editor/[id]` | Create/edit; **Publish** / **Unpublish** |
| `/compose` | Composer chat, private draft, right-side images |
| `/anna` | One-shot Anna review |
| `/admin` | Admin workspace |
| `/settings` | Account settings |

## Local development

Prerequisites: Node.js 20+ and npm. Start the Django API separately from `../blogging-system-yt` when testing authenticated or content-backed flows.

```powershell
cd source
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The frontend expects the backend at the same origin through its development proxy unless `NEXT_PUBLIC_API_URL` is set.

## Environment

Copy `.env.example` to `.env.local` if you need overrides. Create `source/.env.local` only when the API is not reached through the local proxy:

```env
NEXT_PUBLIC_SITE_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

`NEXT_PUBLIC_API_URL` is intentionally limited to an API origin. AI provider keys, search keys, and storage credentials belong only in the Django backend environment.

## API/session behaviour

The typed client is in `src/lib/api.ts`.

- Requests include cookies with `credentials: "include"`.
- Unsafe requests obtain a CSRF token from `/api/v1/auth/csrf/` and send it as `X-CSRFToken`.
- Authentication is Django-session based; there is no JWT handling in the frontend.
- Relative media paths are resolved against `NEXT_PUBLIC_API_URL` when it is configured.

See [`BACKEND_STATUS.md`](BACKEND_STATUS.md) for the current API behaviour and deployment status.

## Checks

```powershell
npm run lint
npx tsc --noEmit
npm run build
```

Run the relevant browser flow after a UI change, including small viewports, keyboard navigation, API-unavailable states, and author/admin permission failures.
