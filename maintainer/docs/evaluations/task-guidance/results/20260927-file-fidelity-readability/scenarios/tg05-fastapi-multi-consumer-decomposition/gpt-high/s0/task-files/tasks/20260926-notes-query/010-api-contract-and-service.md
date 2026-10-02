# Define and implement the notes-query API contract

Own the public HTTP contract and service implementation for bounded
pagination, stable sorting, and optional text filtering. This subtask is the
compatibility gate for all downstream consumers.

Parent Task: tasks/20260926-notes-query/000-main.md

## Requirements checklist

- [ ] The approved query contract names pagination, sorting, and text-filter
      parameters, defaults, bounds, allowed values, and validation behavior.
- [ ] `GET /notes/` supports the approved query behavior at the public route.
- [ ] Unparameterized `GET /notes/` retains its current JSON collection shape
      and has an explicit stable default ordering.
- [ ] Pagination is bounded at the HTTP boundary and cannot request an
      unbounded or above-maximum page.
- [ ] Sorting is deterministic, including a documented tie-breaker.
- [ ] Optional text filtering follows the approved field scope and matching
      rules.
- [ ] Route-level integration tests cover the approved behavior and regressions
      through the real FastAPI application and database boundary.
- [ ] The service-owned public documentation records the approved contract
      before client and CLI consumers are implemented.

## Open requirement questions

- Confirm the parent task's unresolved pagination, sort, filter, response
  shape, and invalid-input questions before implementation.
- Confirm whether the API should expose pagination metadata or preserve a JSON
  array for parameterized calls.

## Supporting facts

- The route is `src/app/api/notes.py`; query work will likely span its route
  parameters and `src/app/api/crud.py`'s database query.
- The existing route test only asserts a 200 response and list shape for
  `GET /notes/`; it does not seed or isolate data.
- The current database schema has `id`, `title`, and `description`, which are
  the available fields for an initial sort/filter contract unless the
  approved requirements expand scope.

## Execution plan

Status: Draft

Define the wire contract first, including exact query names, defaults, maximum
page size, response shape, sorting allowlist/direction, text matching scope,
and errors. Document that contract in the service-owned documentation before
downstream implementation. Then add the smallest service query abstraction
that applies filtering, explicit primary ordering plus deterministic `id`
tie-breaking, and bounded slicing in the database query. Preserve the
unparameterized route's collection representation and make its default
ordering explicit.

Use route integration tests with seeded records that include equal primary
sort values, mixed matching/nonmatching text, and enough records to cross
page boundaries. Cover default behavior, each approved query dimension,
combined dimensions, invalid bounds/values, and compatibility. These tests
are the decisive evidence that the public service boundary is ready for
consumers.

### Implementation decisions and open questions

- The API task owns all wire-level decisions; client and CLI tasks must not
  infer or redefine them.
- Stable sort behavior must be expressed in the production query and tested
  with ties.
- No response envelope or metadata is to be introduced unless the approved
  contract explicitly requires it, because the current client expects a list.
- The exact public choices remain open in the parent task until approved.

### Documentation

- Update the service-facing maintained documentation, likely the root
  `README.md` or a focused service-owned page only if the approved contract
  needs more detail.
- If a focused specification is created, update the existing development
  documentation index rather than leaving an undiscoverable page.
- Mark target behavior as current only after the implementation and route
  evidence are complete.

### Task checklist

- [ ] Resolve and record the HTTP query contract.
- [ ] Add/update route and query implementation.
- [ ] Add route integration coverage for all approved dimensions and
      unparameterized compatibility.
- [ ] Publish/update service documentation with verified behavior.
- [ ] Run the decisive service test command and record the result.
- [ ] Hand the settled contract to the client subtask.

### Requirement verification

- Contract and route behavior: a focused integration suite must issue real
  HTTP requests to the FastAPI app, seed through the supported API or
  controlled test fixture, and assert page bounds, deterministic ordering,
  filter results, response shape, and validation responses.
- Compatibility: the existing no-parameter route request must still return a
  JSON list with the approved stable default ordering.
- Contract readiness: the API tests and maintained documentation must be
  complete before `020-python-client.md` begins implementation.

### Additional implementation verification

- Inspect generated SQL/query composition to ensure filtering and ordering
  happen before pagination.
- Check behavior at zero, one, maximum, and maximum-plus-one page sizes, plus
  negative offsets or equivalent invalid pagination inputs as applicable.