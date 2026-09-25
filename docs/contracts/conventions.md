# Conventions — Global AI Missions

> Owner: `tech-lead`. Frozen at G0 (2026-09-24); changes through [`CHANGE_REQUESTS.md`](CHANGE_REQUESTS.md).
> Goal: code the candidate can explain line by line in the interview. Boring beats clever. Ownership of folders: `SHARED_CONTEXT.md` §11.

## 1. Backend layering

```
HTTP ──▶ app/api/routers ──▶ app/services ──▶ app/repositories   (SQLAlchemy, Postgres)
         (+ app/schemas)          │         ──▶ app/engine         (pure Python story graph)
                                  │         ──▶ app/ai             (coach port + adapters)
                                  └── raises app/core/errors.DomainError
```

| Layer | May import | Must not import | Job |
|---|---|---|---|
| `api/routers` | fastapi, schemas, services, core | repositories, engine, models, sqlalchemy (except the `Session` dependency type) | Parse, call **one** service function, return a schema. ~15 lines per handler, no business logic, no SQL. |
| `api/error_handlers.py`, `api/deps.py` | fastapi, core | services' internals | Error envelope; `get_session`, `current_user`, `require_role`. |
| `schemas` | pydantic | fastapi, sqlalchemy | Request DTOs (`model_config = ConfigDict(extra="forbid")`) and response DTOs, kept separate. |
| `services` | repositories, engine, ai, schemas, core, `sqlalchemy.orm.Session` (type + commit/rollback) | **fastapi** | Use cases. Own the transaction boundaries (e.g. the two-phase submit). Raise `DomainError`. `to_state_view` lives here. |
| `repositories` | sqlalchemy, models | fastapi, services, engine, ai | Small explicit query functions. No scoring, no levels, no Maya decisions. Answer keys only through `get_answer_key(...)`. |
| `models` | sqlalchemy | everything else | Typed SQLAlchemy 2.0 models (`Mapped[...]`). No logic. |
| `engine` | **standard library only** | fastapi, sqlalchemy, pydantic, I/O (except its CLI) | Pure, deterministic search engine. Public API in `engine/__init__.py`. |
| `ai` | pydantic, httpx, provider SDKs, core | fastapi, sqlalchemy, repositories | `CoachProvider` port, adapters, prompts. Provider SDK imports exist **only** here. |
| `core` | pydantic, pydantic-settings, stdlib, PyJWT, argon2 | fastapi, sqlalchemy, services | `config.py` (the only reader of env vars), `errors.py` (pure), `security.py`, `demo.py`. |

Rules:

- The session is created per request by `get_session` (router dependency) and passed down as an argument. Services commit; repositories never commit.
- Synchronous FastAPI endpoints with synchronous SQLAlchemy (a thread pool serves them). Documented choice: simpler to explain; async is a later scaling step.
- Time: `datetime.now(UTC)` only; store `timestamptz`. Never naive datetimes.
- Configuration: `from app.core.config import get_settings`. Nobody reads `os.environ`.
- Logging: `logging.getLogger(__name__)`; no `print` outside CLIs. Never log passwords, tokens, cookies or answer keys.

## 2. Python style

- Python ≥ 3.12, dependencies with **uv** (`backend/pyproject.toml`, `uv.lock`). Run everything with `uv run …` from `backend/`.
- `ruff check` + `ruff format` (line length 100, rules E, W, F, I, B, UP, SIM, ANN). **Type hints everywhere** in `app/` (enforced by `ANN`); tests are exempt.
- Naming: modules and functions `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE`. Verbs for functions (`get_owned_attempt`, `grade_attempt`), nouns for data.
- Pydantic v2 for DTOs; `dataclasses(frozen=True)` inside the engine.
- Errors: raise `DomainError(ErrorCode.X, "message", details)`. Never `HTTPException` outside routers/deps; never return error dicts by hand.
- Prefer plain functions over classes; a class only when it holds state or implements a port.
- Tests: `backend/tests/<layer>/test_<module>.py`, pytest with plain `assert`, deterministic (seeded simulator, mock coach, fixed time). Suite under 60 s.

## 3. Frontend

- React + TypeScript (`strict`) + Vite + Tailwind CSS v4. Scripts: `npm run dev | build | test | lint | typecheck | format | gen:api`.
- Folders (`frontend/src/`):
  - `app/` — providers (QueryClient), router, layout.
  - `routes/` — one file per route; thin, composes features.
  - `features/{auth,world,mission,report,progress}/` — each feature owns its components, hooks, reducer and tests.
  - `components/` — shared presentational components (buttons, Maya avatar, skeletons).
  - `api/` — the typed fetch wrapper, the generated `schema.d.ts` (`npm run gen:api` from `docs/contracts/openapi.json`) and the mock adapter (mock mode only, excluded from the production build).
  - `lib/` — small pure helpers. `styles/tokens.css` — design tokens as CSS variables and a Tailwind `@theme` block (ux-ui-designer).
- Naming: components `PascalCase.tsx`, hooks `useThing.ts`, everything else `camelCase.ts`; tests next to the code as `*.test.ts(x)`.
- Server state only through TanStack Query; local UI state through `useState`/`useReducer`. No other state library.
- `fetch` with `credentials: "include"`; the error envelope becomes a typed `ApiError { status, code, message, details }`; UI copy is chosen by `code`.
- Never: `localStorage`/`sessionStorage` (ESLint blocks it), answer keys or scoring logic, hard-coded questions or story text, "Question N/10", correctness colors during the mission, hard-coded provider names.
- ESLint (typescript-eslint, react-hooks) + Prettier (no semicolons, single quotes, width 100). `no-explicit-any` is an error.

## 4. Content

- Content is data: `content/catalog.json`, `content/missions/<id>/{items,mission}.json`, validated against `docs/contracts/*.schema.json` with `cd backend && uv run python scripts/validate_content.py`, then by the engine validator (graph and integrity) before any seed.
- Ids: missions `kebab-case`; items `q01…`; nodes, flags, endings, backdrops `snake_case`.
- In-app text is English, plain text only (no Markdown/HTML), no emojis.

## 5. Git and reviewable changes

- Conventional commits, small and phase-shaped: `feat(engine): …`, `feat(api): …`, `test(api): …`, `docs(contracts): …`, `chore: …`, `fix(mission): …`. Scope = folder or feature.
- One commit = one reason to change. A reviewable change:
  - touches only the owner's folders (SHARED_CONTEXT §11), or links a CHANGE_REQUESTS entry;
  - builds, lints and passes the tests it affects;
  - adds or updates the tests for the behaviour it adds;
  - is small enough to read in 10 minutes (aim under ~300 changed lines, generated files and content excluded);
  - says in its message *why*, not only what.
- Never commit `.env`, secrets, `node_modules`, `.venv`, `dist` or generated caches. The human commits; agents leave changes in the working tree unless told otherwise.
- Every agent delivery gets an entry in `docs/AI_USAGE_LOG.md`.
