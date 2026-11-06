# Books demo deployment runbook

Write a repeatable deployment procedure for the books demo (Flask JSON API + Vue
client): how the app is built, how it runs with configuration from environment
variables, how the health endpoint verifies a deployment, and how to roll back
to the previous deployment when verification fails. Acceptance is one
end-to-end execution of the procedure on a clean checkout. No product code
changes.

## Requirements checklist

- [ ] The books demo has a deployment runbook as maintained documentation that
  an operator can follow start to finish on a clean checkout without
  undocumented knowledge. (R1)
- [ ] The runbook documents how the app is built from a clean checkout:
  dependency installation and every build step that exists today, with an
  explicit statement for any part that has no build path. (R2)
- [ ] The runbook documents how the app runs with configuration supplied
  through environment variables: which variables exist, what each controls,
  and which are required versus optional. (R3)
- [ ] The runbook documents deployment verification via the health endpoint:
  the exact request, the expected response, and the pass/fail criteria applied
  after each deploy. (R4)
- [ ] The runbook documents how to roll back to the previous deployment when
  verification fails, including how the previous deployment is identified and
  re-activated and the effect of the restart on in-memory data. (R5)
- [ ] Acceptance: the procedure is executed once end to end on a clean
  checkout — build, run, health verification, a verification failure, rollback
  to the previous deployment, and renewed verification — and the runbook is
  corrected until the recorded steps pass exactly as written. (R6)
- [ ] Constraint: no product code changes. Sources under `server/` and
  `client/`, tests, and packaging manifests (`pyproject.toml`,
  `client/package.json`) stay unchanged by this work. (R7)

## Requirement questions

Blocking; the runbook cannot be written truthfully or pass R6 until these are
decided.

- **Q1 (blocks R4 against R7).** No health endpoint exists at HEAD
  (`server/app.py` defines only `/books` and `/books/<book_id>`). Options:
  - (a) Amend R7 to allow one minimal health route (e.g. `GET /health`
    returning `{"status": "ok"}`), added as a prerequisite change before the
    runbook is written. Smallest change that makes R4 true as worded.
  - (b) Keep R7 absolute and restate R4 to verify deployments through an
    existing endpoint's observable behavior (e.g. `GET /books` returning the
    two seeded books), with the runbook calling it the verification check
    rather than a health endpoint.
  - Recommendation: (a) if "no product code changes" means "no product
    rework for this runbook"; (b) if the constraint is absolute.
- **Q2 (affects R2 scope).** The client has no production build path:
  `client/package.json` has no build or dev scripts and no bundler
  dependency, so the UI cannot be built or served from a clean checkout.
  Options: (a) document backend-only deployment with an explicit "client
  build: not implemented" statement (no code changes), or (b) add client
  build tooling, which violates R7. Recommendation: (a).
- **Q3 (assumption to confirm).** The deployment target is assumed to be a
  single local host running the Flask server directly; the client's axios
  `baseURL` is hardcoded to `http://localhost:5000`, so any UI serving would
  need to co-locate with or proxy the API. A container, process manager, or
  remote-host target would change the procedure materially.
- **Q4 (default stated).** The runbook is assumed to consist of documented
  commands only; creating deploy/rollback scripts under the repo is not
  required and is treated as out of scope unless requested (they would not be
  product code, but the smallest structure that satisfies R1 omits them).

## Facts (verified 2026-10-29 at HEAD `79449c52`, clean tree)

- Backend is `server/app.py`: module-level Flask `app` with `GET/POST /books`
  and `PUT/DELETE /books/<book_id>`; no health route; no `__main__` entry
  point, so `python server/app.py` does nothing — the app must run through
  `flask run` or a WSGI server.
- Application state is the module-level in-memory `BOOKS` list (two seed
  books). Every process restart — including a rollback restart — resets to
  the seed data and discards runtime mutations. There are no data migrations,
  but restart data loss must be stated in the runbook (R5).
- Python packaging: `pyproject.toml`, project `task-guidance-flask-vue-server`,
  single runtime dependency `flask`. No WSGI server (e.g. gunicorn) is a
  declared dependency.
- The only environment-variable configuration available today is Flask CLI
  configuration: `FLASK_APP`, `FLASK_RUN_HOST`, `FLASK_RUN_PORT`,
  `FLASK_DEBUG`. The application code itself reads no environment variables.
- Client sources: `client/src/components/Books.vue`,
  `client/src/api/books.js`, `client/src/http.js` (axios `baseURL` hardcoded
  to `http://localhost:5000`). `client/package.json` scripts contain only
  `test: vitest run`.
- Existing automated checks are development-time, not deployment verification:
  `tests/test_books_api.py` (pytest, in-process test client) and
  `client/tests/Books.spec.js` (vitest).
- Documentation rules in root `AGENTS.md` and
  `docs/development/documentation.md` were read during planning; the executor
  must honor them when choosing the runbook's location and structure
  (smallest structure that serves the operator; no placeholder pages).

## Execution plan

Not yet drafted. The blocking questions Q1 and Q2 change the required
outcomes (R4 wording, R2 scope), so the plan will be written once they are
resolved and then presented for approval before execution begins.
