# Public notes-query contract and service

Define the canonical HTTP contract first, then implement bounded pagination,
stable sorting, and optional text filtering in the FastAPI notes collection
without breaking unparameterized callers.

Parent Task: `tasks/20260926-notes-query/000-main.md`

Depends On: None

## Requirements checklist

- [ ] Establish a reviewed, documented HTTP query contract before downstream
  client or CLI implementation begins.
- [ ] Support bounded pagination on the public notes collection.
- [ ] Support deterministic sorting, including an explicit tie-breaker for
  equal primary sort values.
- [ ] Support the agreed optional text filter with documented matching scope
  and semantics.
- [ ] Preserve the current unparameterized `GET /notes/` response shape and
  all-notes behavior.
- [ ] Verify the behavior through the public API and storage boundary.

## Requirement questions and scope decisions

- Resolve the parent task's route, response-shape, parameter-name, bounds,
  filter, and invalid-input questions before implementation.
- Confirm whether the no-parameter route is deliberately unbounded for
  compatibility while explicitly paginated requests are bounded.
- Confirm the allow-listed sortable fields and the required direction syntax.

## Research and supporting facts

- The collection route is `GET /notes/` in `src/app/api/notes.py`.
- Querying currently delegates to `crud.get_all()` and returns a bare list.
- The SQL table has `id`, `title`, and `description`; it has no timestamp
  column suitable for ordering.
- Existing service tests only assert a 200 response and list type, so focused
  query and compatibility evidence is needed.

## Execution plan

Status: Draft

The service task is the source of truth for HTTP behavior. First record the
accepted contract, including examples, bounds, sorting/tie behavior, filter
scope, response shape, and validation errors. Then implement the query at the
service/storage boundary so filtering, ordering, limit, and offset are applied
before rows are returned. Keep the no-argument code path compatible with the
existing list response.

Verification should seed deterministic notes through supported service setup,
exercise the collection route through `TestClient`, and cover:

- no parameters returning the existing list shape and complete current result;
- each page respecting the agreed bound and offset semantics;
- repeated requests producing the same order, including equal primary sort
  values resolved by the agreed tie-breaker;
- title/description filter cases required by the contract;
- accepted boundary values and rejected out-of-range or invalid values.

Update the service README/development documentation only after the behavior
and contract are true. The API task is the gate that makes the downstream
client and CLI tasks executable.

### Implementation decisions and open questions

- This task owns the canonical public contract and should use the existing
  collection route unless the parent contract review chooses otherwise.
- The recommended response remains a JSON array to preserve the client and
  CLI list interfaces, but this requires approval.
- `id` is the recommended secondary key because it is the only existing
  schema field guaranteed to identify a row uniquely.
- Exact parameter vocabulary and validation rules remain open from the parent
  task.

### Documentation

- Maintain the notes-query contract in `docs/development/` and link it from
  `docs/development/index.md`.
- Update the root README's public API description after implementation.
- If the contract is written before the endpoint is implemented, mark it
  visibly as `Not implemented` until the API evidence passes.

### Task checklist

- [ ] Resolve and record the accepted HTTP contract.
- [ ] Implement service/storage query behavior.
- [ ] Add API compatibility, query, validation, and ordering tests.
- [ ] Update maintained service documentation.
- [ ] Report the API evidence and unblock downstream tasks.

### Requirement verification

- Public contract and service behavior: one API integration suite through
  `TestClient`, the FastAPI route, CRUD layer, and database adapter must
  exercise the complete query behavior.
- Unparameterized compatibility: the same public-route suite must assert a
  bare list and the expected complete result when no query parameters are
  supplied.
- Stability: the public-route suite must include tied sort values and assert
  the agreed deterministic secondary order.

### Additional implementation verification

- Run the focused service tests and inspect the generated OpenAPI/query
  declarations if the framework exposes them as part of the contract.
