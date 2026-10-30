# SwiftPost frontend

Follow [`docs/AGENTS.md`](../docs/AGENTS.md) and [`docs/FRONTEND.md`](../docs/FRONTEND.md).

This is the Next.js app (`source/`). Signup creates an **author**. Composer writes private drafts. Anna is a **one-shot review** (`POST /api/v1/ai/reviews/`). Do not add an Anna chat sidebar unless the user asks. Do not modify this frontend unless the user explicitly asks for UI work.

<!-- BEGIN:nextjs-agent-rules -->

## This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->
