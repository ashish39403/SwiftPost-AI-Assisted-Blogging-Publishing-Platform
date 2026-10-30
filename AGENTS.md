# SwiftPost Agent Instructions

Full instructions: [`docs/AGENTS.md`](docs/AGENTS.md).

Backend code: `blogging-system-yt/`. Frontend code: `source/`. Do not change the frontend unless the user asks.

Signup creates **author**. Authors publish and unpublish their own complete posts. Admins can unpublish any live post. **AI never publishes.** Session cookies + CSRF. SQLite locally.

Before backend changes, read:

- `docs/SWIFTPOST_REBUILD_PRD.md`
- `docs/TECH_STACK.md`
- `docs/BACKEND_IMPLEMENTATION.md`
- `docs/BACKEND_STATUS.md`
- The current repository code and migrations for the change
