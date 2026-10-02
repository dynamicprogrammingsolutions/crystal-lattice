# Add one notes-query capability across service, client, and CLI

Plan and coordinate a supported notes collection query capability across the
public FastAPI service, reusable Python client, and CLI. The capability must
provide bounded pagination, deterministic sorting, and optional text
filtering while preserving the existing no-argument behavior.

## Requirements checklist

- [ ] An approved, maintained public contract defines the notes query
  parameters and result behavior before the client and CLI depend on it. The
  contract covers bounded pagination, stable sorting, optional text filtering,
  defaults, invalid values, and the response shape.
- [ ] `GET /notes/` implements the approved query contract, including bounded
  pagination, stable ordering, and optional text filtering.
- [ ] A request to `GET /notes/` without query parameters remains compatible
  with the current public behavior: it succeeds and returns the existing JSON
  array representation containing the unparameterized collection.
- [ ] `NotesClient.list_notes()` exposes the approved query capability and
  forwards it through the real HTTP request while preserving its current
  no-argument behavior and return shape.
- [ ] `notes list` exposes the approved query controls, keeps the current
  no-argument invocation usable, and renders the returned notes.
- [ ] Evidence crosses the relevant public boundaries, including a decisive
  CLI test that uses the production client against the real notes service
  path rather than a fake client or a test-only shortcut.
- [ ] Maintained documentation describes the supported contract and each
  consumer's usage after the behavior is implemented.

## Scope and workstreams

- Public API contract and service implementation: own the HTTP query
  vocabulary, validation, database filtering/order/pagination, and API
  compatibility evidence.
- Reusable client: mirror the approved HTTP contract as optional Python
  arguments and keep the existing transport boundary.
- CLI and cross-boundary verification: expose the client capability through
  `notes list` and prove the production CLI-to-service path.
- Documentation and verification stay with the subsystem that owns each
  public surface; the parent task coordinates the shared contract and
  compatibility claims.

## Subtasks

- [ ] tasks/20260925-notes-query-capability/010-api-contract-service.md
- [ ] tasks/20260925-notes-query-capability/020-python-client.md
- [ ] tasks/20260925-notes-query-capability/030-cli-integration.md

## Unresolved requirement questions and decisions

These are material public-contract questions and must be answered before the
Draft can become Approved:

- What pagination vocabulary and shape are required: page/page-size, offset/
  limit, or another model? Is the parameterized response still an array, or
  does it include pagination metadata?
- What are the allowed sort fields, direction syntax, default order, and
  deterministic tie-breaker? The current schema exposes only `id`, `title`,
  and `description`; no timestamp field exists.
- Does text filtering search `title`, `description`, or both? Is matching
  substring-based, case-insensitive, and represented by a `q`, `search`, or
  other parameter?
- What exact server bounds and invalid-input responses apply to pagination,
  sorting, and filtering?
- What CLI flag names and output expectations should mirror the HTTP/client
  contract?

Planning decisions already made:

- Use a parent task with three subtasks because the service, reusable package,
  and CLI are separate public compatibility boundaries.
- Make the service contract the dependency for both consumers.
- Make the CLI subtask own the decisive end-to-end check through a real
  `NotesClient` and the FastAPI application.
- Do not implement code, change dependencies, or alter current behavior while
  this handoff remains a Draft.

## Research and supporting facts

- The collection route is `GET /notes/` in `src/app/api/notes.py` and
  currently returns `crud.get_all()` directly.
- `src/app/api/crud.py` currently executes `notes.select()` with no explicit
  filter, order, or pagination.
- `src/app/db.py` defines only `id`, `title`, and `description` columns.
- `packages/notes_client/notes_client/client.py` currently calls
  `transport.get("/notes/").json()` from a no-argument `list_notes()`.
- `apps/notes_cli/cli.py` currently provides `notes list` with no options and
  prints each returned note's id and title.
- Existing service and client tests assert that the unparameterized result is
  a list. The existing CLI test injects a fake client, so it does not prove
  the production client-to-service connection.
- `docs/development/index.md` currently records that no notes-query
  specification exists. The root, client, and CLI READMEs describe the
  current unparameterized behavior.

## Execution plan

Status: Draft

The service-owned contract is the source of truth for parameter names,
defaults, bounds, ordering guarantees, filtering semantics, errors, and
response shape. It must be settled and documented before consumer
implementations are treated as supported. The service will apply the
contract at the HTTP and database boundary, retaining the existing array
response for the no-argument request unless the approved contract explicitly
requires another compatible treatment. The client will translate optional
Python arguments into query parameters without bypassing the HTTP contract.
The CLI will translate user-facing options into the client call and will
retain the current no-option output path.

The ordered execution is:

1. Resolve the public-contract questions, add the maintained contract
   documentation, and record the approved compatibility/default behavior.
2. Implement and test the service query behavior against the real route and
   database, including validation, bounds, deterministic order, filtering,
   pagination, and the no-argument regression.
3. Implement and test the reusable client's optional query arguments and
   request encoding, then update its README.
4. Implement and test CLI options and output. Add the decisive integration
   test that invokes the CLI with a real `NotesClient` whose transport is the
   service's actual FastAPI test transport, with data created through the
   public service path.
5. Run the service, client, and CLI test suites together with any repository
   gates, inspect the final documentation, and close each requirement only
   when its public-boundary evidence succeeds.

### Implementation decisions and open questions

The task remains Draft until the unresolved contract questions above are
answered. A recommended low-disruption direction for review is to preserve
the array response and no-argument behavior, use an explicitly bounded
offset/limit-style query, allow an explicit sort field plus direction with a
fixed id tie-breaker, and search title and description case-insensitively.
This is a recommendation only, not an approved requirement or implementation
decision.

No schema migration is assumed. If the approved sort contract requires a
field not present in the current schema, the scope and compatibility impact
must be revisited before approval.

### Documentation

The execution should add the smallest maintained service-owned query contract
document under `docs/development/` and link it from
`docs/development/index.md`. It should update the root README, client README,
and CLI README only where each audience needs current supported usage. Any
contract text written before implementation must be clearly marked as
not implemented; the marker is removed in the same reviewed change that
delivers the behavior.

### Task checklist

- [ ] Resolve and approve the public query contract.
- [ ] Complete `tasks/20260925-notes-query-capability/010-api-contract-service.md`.
- [ ] Complete `tasks/20260925-notes-query-capability/020-python-client.md`.
- [ ] Complete `tasks/20260925-notes-query-capability/030-cli-integration.md`.
- [ ] Update maintained documentation at the owning boundaries.
- [ ] Run and record all required service, client, CLI, and cross-boundary
  verification.

### Requirement verification

- Contract stability: human approval of the documented query contract,
  followed by inspection that the service, client, and CLI use the same
  vocabulary and semantics.
- Service query behavior and compatibility: route-level tests through
  `TestClient` with seeded notes verify filtering, bounded pagination,
  deterministic sorting, validation, and `GET /notes/` with no parameters
  still returning the current array behavior.
- Reusable client behavior: client tests verify optional arguments become the
  approved query string and that `list_notes()` with no arguments preserves
  the current request and return shape.
- CLI behavior and production connection: an integration test invokes
  `notes_cli.cli.main` with query options and a real `NotesClient` backed by
  the FastAPI application's actual HTTP test transport. Notes are created
  through the public service route, and assertions cover the filtered,
  paginated, stably ordered output. This is the decisive check for the
  consumer-to-service connection.
- Documentation: inspect the maintained contract and consumer READMEs for
  current, consistent names and examples after implementation.

### Additional implementation verification

- Check boundary values and rejected values for every bounded input.
- Check deterministic ordering when multiple notes share the primary sort
  value.
- Check that omitted optional parameters do not change the existing
  unparameterized code path's externally visible result.
- Check that CLI tests do not replace `NotesClient` with a fake for the
  decisive end-to-end assertion.