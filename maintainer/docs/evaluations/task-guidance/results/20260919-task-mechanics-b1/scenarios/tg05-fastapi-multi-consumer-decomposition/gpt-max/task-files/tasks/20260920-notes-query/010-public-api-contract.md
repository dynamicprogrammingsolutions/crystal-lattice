# Public notes-query contract and API

Define the stable notes-query contract and implement it at the public
FastAPI collection endpoint. This is the compatibility gate for the reusable
client and CLI; it is a Draft planning handoff and contains no implementation.

## Requirements checklist

- [ ] A reviewed, maintained contract defines the query parameters, pagination
  bounds/defaults, sort keys/direction and tie-break behavior, filter
  matching, response shape, validation errors, and no-parameter compatibility.
- [ ] `GET /notes/` implements the approved bounded pagination, stable sorting,
  and optional text filtering semantics through the real database path.
- [ ] A request with no query parameters preserves the current public
  collection shape and all-record behavior required by the approved contract.

Parent Task: `tasks/20260920-notes-query/000-main.md`

## Scope and workstreams

- Own the HTTP contract, route-to-database implementation, API integration
  tests, and API/root documentation.
- Establish the reviewed contract before the client and CLI subtasks begin.
- Do not change item CRUD routes or add a new query endpoint unless the
  approved contract explicitly requires it.

## Unresolved requirement questions

Do not resolve these locally; the parent task must approve them first:

- The pagination parameter names, response shape, bounds, defaults, and
  invalid-value status/body.
- The public sort-key allow-list, direction syntax, default order, and unique
  tie-breaker.
- The filter parameter name, searchable fields, case/substring semantics, and
  empty-value behavior.

## Research and supporting facts

- `src/app/api/notes.py` delegates the collection route to
  `src/app/api/crud.py::get_all`.
- `get_all()` currently uses an unconstrained SQLAlchemy select, so stable
  ordering is not currently guaranteed by the implementation.
- The existing API test only asserts that `GET /notes/` returns a list; a
  query-focused fixture will need deterministic seed data, including
  duplicate primary sort values and nonmatching text.
- The maintained development index explicitly says no notes-query
  specification exists, making the contract document a new owned artifact.

## Execution plan

Status: Draft

1. Resolve the parent contract questions in review and write the approved
   target in a maintained `docs/development/` specification. Include examples
   and compatibility notes; mark target-only behavior `Not implemented` if
   the document is published before code execution.
2. Add route/query validation and database query construction according to
   that specification. Use an allow-listed sort expression and an explicit
   unique secondary key so equal primary values have repeatable order.
3. Preserve the unparameterized collection response and test it separately
   from parameterized calls, including the exact list shape expected by the
   existing client.
4. Exercise the public FastAPI route with seeded data for pagination,
   boundaries, sort ties, filter matches/nonmatches, invalid inputs, and
   compatibility. Update API documentation only after those checks pass.

Execution waits for approval of the parent Draft and the unresolved public
contract decisions.

### Implementation decisions and open questions

- The API task owns the contract gate, but it must not invent unresolved
  public names or error behavior.
- The implementation should keep filtering and pagination in the database
  query rather than fetching every row into application memory, subject to
  the approved contract and the existing database adapter.
- Whether the contract returns a bare list or metadata envelope is a
  compatibility decision, not a local serialization choice.

### Documentation

- Add the reviewed notes-query contract to `docs/development/` and link it
  from `docs/development/index.md`.
- Update the root README’s collection-route description after the API is
  implemented and verified. Do not present target-only behavior as current
  guidance.

### Task checklist

- [ ] Receive parent approval for all public contract questions.
- [ ] Write/review the maintained notes-query specification.
- [ ] Implement the approved collection query through the API/database path.
- [ ] Add and run API boundary tests, including unparameterized compatibility.
- [ ] Update API documentation and report the contract gate complete.

### Requirement verification

- **Stable contract:** approved specification plus review record; no client or
  CLI task starts before this evidence exists.
- **API query capability:** FastAPI integration tests against seeded database
  rows cover every approved query control and invalid boundary through
  `GET /notes/`.
- **Compatibility:** the no-parameter `GET /notes/` test asserts the
  unchanged public response shape and all-record behavior.