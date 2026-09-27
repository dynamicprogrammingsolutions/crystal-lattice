# Books demo deployment runbook

Write a repeatable deployment procedure for the Flask + Vue books demo: how the
app is built, how it runs with configuration from environment variables, how
deployment is verified via the health endpoint, and how to roll back to the
previous deployment when verification fails. Accept the procedure by executing
it once end to end on a clean checkout. No product code changes.

## Requirements checklist

- [ ] R1: A deployment runbook for the books demo exists and covers, as executable steps: (a) how the app is built, (b) how it runs with configuration from environment variables, (c) how the health endpoint verifies a deployment (see Q1 — no dedicated health endpoint exists today), and (d) how to roll back to the previous deployment when verification fails.
- [ ] R2: The procedure is repeatable: a reader can execute every step from a clean checkout with no unstated prerequisites, prior context, or undocumented environment assumptions.
- [ ] R3: Acceptance — the documented procedure has been executed once end to end on a clean checkout: deploy, verification passes, and the rollback steps are executed as the runbook prescribes (verification driven to failure by the runbook's own method). Evidence (commands and results) is recorded.
- [ ] R4: No product code changes: `server/`, `client/`, and `tests/` receive no modifications; repo changes are limited to documentation and task files.
- [ ] R5: The runbook follows `docs/development/documentation.md` (read before writing it): smallest structure that helps the reader, placed with the owning subsystem, no placeholder pages, and it describes current supported behavior only — no invented endpoints or environment configuration beyond what exists (pending Q1 resolution).

## Open questions

- Q1 (requirement question, blocks R1c/R5): The request says the runbook explains "how the health endpoint verifies a deployment", but the app has no health endpoint and R4 forbids product code changes. Options:
  - (a) Recommendation — the runbook documents deployment verification using an existing route (e.g. `GET /books`) as the deployment probe and states explicitly that no dedicated health endpoint exists.
  - (b) Relax R4 to add a minimal `/health` route to `server/app.py` (a product code change).
  - (c) Another interpretation supplied by the requester.

  Related note, same constraint: application-level environment configuration (e.g. port or data source read via `os.environ`) would also be a product code change; today the only env-var configuration without code changes is Flask's standard CLI environment (e.g. `FLASK_APP`, host/port variables). Confirm this matches the intent of R1b.

## Supporting details

### Facts

- Server is `server/app.py` (Flask): routes `GET/POST /books` and `PUT/DELETE /books/<id>`; no `/health` or any other route; no `app.run()` or `__main__` block, so serving requires the Flask CLI (or a WSGI server), not `python server/app.py`.
- Book data is a module-level in-memory `BOOKS` list: no persistence. Consequence for the runbook: restarting or rolling back a deployment loses books added since server start, and there are no data-migration or rollback-data concerns to document.
- `pyproject.toml` defines package `task-guidance-flask-vue-server` with an unpinned `flask` dependency and no lockfile; the runbook must state or verify the installed Flask version at execution time.
- No `os.environ`/`getenv` usage anywhere in the repo.
- `tests/conftest.py` imports `from server.app import app`, so `server.app` is importable from the repo root (`server/` is a namespace package without `__init__.py`).
- Client (`client/`) is Vue 3 + axios. `package.json` has no build script and no bundler dependency (only `test: vitest run`), so there is no client production build step as-is. `client/src/http.js` hardcodes `baseURL: "http://localhost:5000"`, so the API must be served on port 5000 for the existing client to work unchanged.
- No deployment tooling exists in the repo (no Dockerfile, Procfile, CI, or deploy scripts), so the runbook defines deployment mechanics from standard tooling; the natural deployment unit is a repo revision installed and run from a fresh checkout.
- Documentation baseline: `docs/development/index.md` exists (there is no `docs/index.md`); `docs/development/documentation.md` is the documentation guide and must be read before creating the runbook page (already read for this task file).
- Workspace at task-file creation: clean checkout at commit `5699da14` (detached HEAD); `tasks/` did not exist before this file.

### Recommendations

- Runbook destination: `docs/development/deployment.md`, linked from `docs/development/index.md` — audience is the developer/operator deploying this repo, and the procedure spans server and client, so it is repo-level rather than package-local. Alternative if ops documentation is preferred outside `docs/development/`: a root-level page.
- Q1: option (a).

### Out of scope

- Product code changes of any kind (R4), including adding a health endpoint or application-level env-var configuration unless Q1 resolves to relax R4.
- Hardening the app for production (persistence, WSGI server choice beyond what the procedure needs, client bundling) — the runbook documents deploying the app as it exists.