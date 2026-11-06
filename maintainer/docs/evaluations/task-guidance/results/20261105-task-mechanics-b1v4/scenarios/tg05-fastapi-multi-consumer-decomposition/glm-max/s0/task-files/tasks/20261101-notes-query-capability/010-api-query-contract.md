# API: define and stabilize the notes query contract

Add optional query parameters for bounded pagination, stable sorting, and
optional text filtering to `GET /notes/`, keep the unparameterized response
identical to today, write the contract into the maintained public docs, and
pin it with route tests. This subtask completes before either consumer builds
on the contract.

Parent Task: tasks/20261101-notes-query-capability/000-main.md

## Requirements checklist

- [ ] `GET /notes/` accepts the approved optional query parameters implementing bounded pagination, stable sorting, and optional text filtering; out-of-range or disallowed values are rejected with 422. Parameter specifics are the parent plan's proposed contract, binding once approved.
- [ ] When any query parameter is supplied, results return in a deterministic total order: the requested sort key with unique `id` as final tiebreaker, `id` ascending when sort is not given.
- [ ] The unparameterized `GET /notes/` response is unchanged — every note as a JSON array, content, shape, and ordering exactly as today — proven by regression evidence.
- [ ] The contract (parameters, defaults, bounds, ordering rule, response shape, error behavior) is documented in the root `README.md` in the same change, with OpenAPI reflecting it from route code.
- [ ] Route tests through the real app prove: page bounds and cap enforcement, deterministic ordering including the tiebreaker, text filtering, combined parameters, and the unparameterized regression case.

Depends On: none. Must complete before
`tasks/20261101-notes-query-capability/020-client-query-support.md` and
`tasks/20261101-notes-query-capability/030-cli-query-command.md` start.

## Supporting details

**Proposed contract slice (binding once the parent plan is approved).**
Optional parameters on `GET /notes/`: `limit` (int 1–100, default 20 when any
parameter is used), `offset` (int ≥ 0, default 0), `sort` (one of `id`,
`title`, `description`, optional leading `-` for descending, default `id`
ascending), `q` (case-insensitive substring on title or description). Response
stays a bare JSON array of note objects, up to `limit` items, empty array for
no matches; no envelope, no total. Supplying no parameters reproduces today's
behavior exactly.

**Current code facts.**

- `src/app/api/notes.py:8-10` — `read_all_notes()` returns `crud.get_all()`;
  no parameters, no ordering. `src/app/api/crud.py:4-5` — `get_all()` fetches
  the whole table.
- Schema (`src/app/db.py`): `id` (PK), `title` (String(50)),
  `description` (String(50)). No timestamps, so the sort whitelist is limited
  to these three columns.
- Stack: `databases` + SQLAlchemy core; selects support
  `.where()/.order_by()/.offset()/.limit()`; `ilike` is available for `q`.
- `fastapi.Query(ge=..., le=...)` produces the framework's standard 422
  responses; the app has no other custom error surface today.
- Router prefix is `/notes` (`src/app/main.py:15`).

**Harness facts.**

- `src/tests/conftest.py` builds `TestClient(app)` without a context manager
  while `database.connect()` runs in the lifespan hook; the connection may not
  be established in the current suite. Route tests should use
  `with TestClient(app)` or otherwise ensure connection — verify during
  execution.
- Importing `app.db` creates `./notes.db` in the process CWD at import time;
  the file is not gitignored. Keep it out of commits.
- The SQLite DB path is CWD-relative; irrelevant for in-process TestClient
  tests, critical for any subprocess-served run (020/030).
- `docs/development/index.md` records that no notes-query specification
  exists. Do not create a spec page under `docs/` unless the parent plan's
  documentation decision is changed by approval (smallest-structure rule).

## Implementation plan

Status: Draft

**Design.** Extend `read_all_notes` with the four optional `fastapi.Query`
parameters. Add a query path in `crud` that applies `where` (for `q`, as
`OR(ilike(title), ilike(description))`), `order_by` (whitelisted column,
descending on `-` prefix, then `id` ascending as tiebreaker), `offset`, and
`limit` — applied only when at least one parameter is supplied. The
unparameterized request keeps calling today's `get_all()` branch unchanged, so
preservation holds by construction, not by coincidence. Validate `sort`
against the whitelist in the handler (422 on unknown values) and bounds via
`Query` constraints.

**Order logic.** Implementation, tests, and README contract section land as
one reviewed change; the milestone is a stable, documented, pinned contract.
Nothing downstream may start until this subtask's requirements are checked.

**Verification.** Decisive evidence: route tests through `app.main.app` via
TestClient on a seeded temporary SQLite DB, crossing routing, validation,
handler, and serialization at the public boundary. Cases: unparameterized
response equals the full seeded set exactly; pagination across multiple pages
reconstructs the set without gaps or duplicates; `limit=100` accepted,
`limit=101`, `limit=0`, and negative rejected with 422; `sort=title` with
duplicate titles shows the `id` tiebreaker and is stable across repeated
requests; `sort=-title` reverses; `q` matches case-insensitively in either
field; `q` with no matches returns `[]`; combined `q`+`sort`+`limit`+`offset`
behaves as the intersection. Deliberately not covered here: real socket
transport (covered in 020/030) and consumer surfaces.

**Risks.** ASCII-only case folding for `q` (document, don't over-claim);
unparameterized regression (pinned by the exact-response test); import-time
`notes.db` artifact (keep out of commits); lifespan/connection harness
question (verify and use `with TestClient(app)`).

### Implementation decisions and open questions

Governed by the parent plan's decisions 1–6 and 12. Local reversible choices
(helper naming in `crud`, test file layout) resolve at execution.

### Documentation

Root `README.md` gains the query contract in this same change, replacing the
"returns every note as a JSON array" framing with current supported behavior.
OpenAPI updates itself from the route signature; never hand-edit generated
output.

### Task checklist

- [ ] Add query parameters to `read_all_notes` and the conditional query path in `crud`, preserving the unparameterized branch.
- [ ] Add route tests for the cases listed under Verification.
- [ ] Update root `README.md` with the contract.
- [ ] Existing API suite stays green.

### Requirement verification

- Query capability and its bounds/order/filter semantics → the route tests
  named above through the real app. Not covered: real network transport,
  consumer surfaces.
- Contract stability → README section plus OpenAPI parameters published in the
  same reviewed change, tests pinning behavior, and this subtask completing
  before 020/030 start. Not covered: release/versioning mechanics (the fixture
  has none).
- Unparameterized preservation → the exact-response regression test on seeded
  rows. Not covered: client request shape (020's evidence).
