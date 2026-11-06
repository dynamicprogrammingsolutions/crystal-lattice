# Books demo deployment runbook

Write and validate a repeatable deployment procedure for the Flask + Vue books
demo: how the app is built, how it runs with configuration from environment
variables, how the health endpoint verifies a deployment, and how to roll back
to the previous deployment when verification fails.

## Requirements checklist

- [ ] A single repeatable deployment runbook for the books demo exists in the
  repository's maintained documentation.
- [ ] The runbook documents how the app is built.
- [ ] The runbook documents how the app runs with configuration from
  environment variables.
- [ ] The runbook documents how the health endpoint verifies a deployment.
- [ ] The runbook documents how to roll back to the previous deployment when
  verification fails.
- [ ] Acceptance: the procedure has been executed once end-to-end on a clean
  checkout.
- [ ] Constraint: no product code changes; the runbook's claims hold for the
  code that exists when it is executed.

## Questions and decisions

The requested content assumes deployment surface that a repo-wide search does
not find, while the request forbids product code changes. Each item below is a
requirement question: its answer changes an accepted outcome above.

1. **Health endpoint does not exist.** `server/app.py` defines only
   `/books` and `/books/<book_id>`; no `health` match exists anywhere in the
   repo. Options:
   - (a) Runbook uses an existing route (e.g. `GET /books`) as the deployment
     verification check, and notes `/health` as future work.
   - (b) Approve a minimal product change adding `/health` (relaxes the
     no-code-change constraint).
   - (c) Runbook documents `/health` as target behavior with a visible
     `Not implemented` marker; the end-to-end execution cannot then include the
     health check step.
   - Recommendation: (a). Keeps the acceptance execution truthful without code
     changes.
2. **No environment-variable configuration exists.** No `os.environ`/`getenv`
   anywhere; the only env surface is Flask's own CLI (`FLASK_APP`,
   `FLASK_DEBUG`). Options:
   - (a) Document the env vars that actually exist at the tooling level and
     state explicitly that the app itself reads no configuration.
   - (b) Approve app-level env config as a product change.
   - Recommendation: (a).
3. **"How the app is built" has little to document.** The Flask API has no
   build step beyond installing `flask`. The Vue client has no build script,
   no bundler, and no served entry point (`client/package.json` has only a
   `test` script); nothing in the repo serves the client. Options:
   - (a) Document dependency installation and what is deployable today
     (the JSON API), noting the client is currently test-only.
   - (b) Approve adding a real client build and static serving (product
     change).
   - Recommendation: (a).
4. **No previous deployment exists to roll back to.** There are no release
   artifacts, registry, or deploy history. On a clean checkout the only
   meaningful "previous deployment" is the previous git revision. Options:
   - (a) Define rollback as redeploying the previous git revision with the
     same procedure.
   - (b) Approve introducing release artifacts (infra/product change).
   - Recommendation: (a); the in-memory book store means rollback carries no
     data-migration concern.

Resolution of these questions requires user approval before planning is
completed and the runbook is written.

## Supporting details

- **Server** (fact): `server/app.py` is a single-file Flask app — in-memory
  `BOOKS` list (`server/app.py:4`), `GET/POST /books` (`server/app.py:10`),
  `PUT/DELETE /books/<book_id>` (`server/app.py:23`). No `app.run`, no WSGI
  entry point, no gunicorn config. Sole dependency is `flask`
  (`pyproject.toml`).
- **Client** (fact): `client/package.json` declares vue, vue-router, axios and
  only a `test` script (vitest); no bundler or build output. The axios base
  URL is hardcoded to `http://localhost:5000` (`client/src/http.js:3`). No
  HTML entry point and no server serves the client.
- **No deployment machinery** (fact): no Dockerfile, compose file, Makefile,
  scripts, or CI anywhere in the repo; root contains only `client/`, `server/`,
  `tests/`, `docs/`, and project files.
- **Docs state** (fact): only `docs/development/index.md` and
  `docs/development/documentation.md` exist. `docs/development/documentation.md`
  governs placement (smallest structure that helps the reader, documentation
  with the owning subsystem), requires user/developer docs to describe current
  supported behavior, and allows target-only text only behind a visible
  `Not implemented` marker. The runbook's destination and claims must follow
  these rules.
- **Existing tests** (fact): `tests/test_books_api.py` (Flask test client) and
  `client/tests/Books.spec.js` (vitest) do not cross a deployment boundary and
  cannot substitute for the acceptance execution.
- **Clean checkout** (fact): the acceptance run starts from a fresh clone, so
  the runbook must be self-contained — every command it gives must work with
  nothing but the checkout and standard tooling.
- **Data** (fact): the book store is in-memory only, so rollback has no
  persisted-state or migration dimension.

No implementation plan is recorded yet: the questions above decide what the
runbook may truthfully claim and what the acceptance execution can traverse.
