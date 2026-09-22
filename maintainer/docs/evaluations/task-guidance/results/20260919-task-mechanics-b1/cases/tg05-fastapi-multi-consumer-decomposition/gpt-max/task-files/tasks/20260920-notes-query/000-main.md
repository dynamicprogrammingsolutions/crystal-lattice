# Notes query across the API, reusable client, and CLI

Plan and coordinate one supported notes-collection query capability across the
FastAPI service, `notes-client`, and `notes` CLI. This handoff is planning-only:
the plan is Draft and no product implementation is included.

## Requirements checklist

- [ ] A reviewed public notes-query contract is finalized and documented before
  client or CLI consumers depend on it. The contract covers bounded
  pagination, stable sorting, optional text filtering, validation/error
  behavior, response shape, and unparameterized compatibility.
- [ ] The public notes collection API implements the approved contract,
  including bounded page requests, deterministic ordering with an explicit
  tie-break rule, and optional text filtering.
- [ ] The reusable Python client exposes the approved query controls while a
  no-argument `list_notes()` call preserves its current request and list
  response behavior.
- [ ] The CLI exposes the approved query controls while an unparameterized
  `notes list` invocation preserves its current output behavior. Its decisive
  evidence uses the production `NotesClient` against the FastAPI service,
  rather than a fake client or a test-only shortcut.

## Scope and workstreams

- The API workstream owns the contract gate, collection-query implementation,
  service-boundary tests, and API-facing documentation.
- The client workstream owns query argument modeling/encoding, compatibility
  behavior, client tests, and package documentation.
- The CLI workstream owns command-line controls, output behavior, the
  production client-to-service check, and application documentation.
- Existing create, read-by-id, update, and delete behavior is outside scope
  unless the approved collection contract exposes a necessary shared
  validation or model change. No persisted-schema change is planned by
  default.
- The child tasks are ordered by public compatibility dependency, not merely
  by source directory: the client and CLI must not consume an unstable API
  contract.

## Unresolved requirement questions

These questions change the public contract and must be answered before the
first consumer task is approved. They are intentionally not resolved by this
Draft.

1. Which pagination vocabulary and shape are required: `limit`/`offset`,
   `page`/`page_size`, or another pair? What are the inclusive bounds,
   defaults, and behavior for invalid or over-limit values? Does a request
   with no pagination parameters retain the current all-record result?
2. Should parameterized responses remain bare JSON arrays, or should they
   include page metadata? Preserving the current client return type favors a
   list response, but this needs an explicit contract decision.
3. Which sort keys and direction controls are public? What is the default
   order, and what unique secondary key makes equal primary sort values
   deterministic?
4. What is the filter parameter name and matching rule? In particular, should
   text search cover title, description, or both; be case-insensitive; match
   substrings; and treat an empty value as absent?
5. Which CLI option names and rendering rules should mirror the API, and
   should every API query control be available from `notes list`?

## Research and supporting facts

- `src/app/api/notes.py` currently exposes `GET /notes/` without query
  parameters and returns `crud.get_all()` directly.
- `src/app/api/crud.py` currently issues an unconstrained `notes.select()`;
  `src/app/db.py` defines `id`, `title`, and `description` but no explicit
  collection ordering.
- `src/tests/test_notes.py` only establishes that the unparameterized
  collection response is a list; it does not seed or assert query semantics.
- `packages/notes_client/notes_client/client.py` currently calls
  `transport.get("/notes/").json()` and returns the decoded value unchanged.
  Its transport seam accepts keyword arguments, which can carry approved
  query parameters without changing the no-argument call.
- `apps/notes_cli/cli.py` currently supports only `notes list`; `list_command`
  calls `client.list_notes()` and prints `id: title`. Its existing test injects
  a fake client, so it cannot prove the required client-to-service path.
- `docs/development/index.md` states that no notes-query specification exists.
  Current user-facing descriptions live in the root README, the client
  README, and the CLI README.

## Subtasks

- [ ] `tasks/20260920-notes-query/010-public-api-contract.md`
- [ ] `tasks/20260920-notes-query/020-reusable-client.md`
- [ ] `tasks/20260920-notes-query/030-cli-integration.md`

The API/contract task has no child dependency. The client task depends on its
reviewed contract and implemented service boundary. The CLI task depends on
both the contract/API task and the reusable-client task.

## Execution plan

Status: Draft

Resolve the public-contract questions as a review gate, then execute the
children in dependency order:

1. Finalize the query vocabulary, bounds, defaults, sort/filter semantics,
   response shape, validation errors, and compatibility guarantees. Record
   the approved contract in a maintained development specification before
   client or CLI code is changed.
2. Implement and test the API collection query through the real FastAPI
   route and database adapter. Keep the no-parameter route behavior intact,
   add explicit SQL ordering and a deterministic tie-breaker, and enforce
   the approved bounds and filter semantics at the public boundary.
3. Extend the reusable client only after the API contract is stable. Encode
   only supplied query controls, preserve the exact no-argument request and
   list return behavior, and add service-facing compatibility evidence in
   addition to transport-shape tests.
4. Add CLI options that map to the approved client controls. Preserve the
   existing no-option output and add a decisive integration test that invokes
   the CLI with a real `NotesClient` configured against the FastAPI service,
   then verifies the filtered/paginated/sorted output.
5. Update maintained documentation only when the corresponding behavior is
   implemented and verified; target-only contract text may be marked
   `Not implemented` if it must be reviewed before implementation.

Execution is waiting for explicit approval of this Draft and answers to the
unresolved contract questions.

### Implementation decisions and open questions

- The material public decisions are listed above and remain open. Child
  tasks must not choose parameter names, response envelopes, bounds, sort
  keys, or filter semantics locally.
- Recommended contract direction for review, not an approved decision: keep
  the collection response as a JSON list for both unparameterized and
  parameterized calls, use an explicit bounded page-size control plus an
  offset/page position, expose a small allow-list of sort keys, and append
  `id` as a unique tie-breaker. This minimizes disruption to the current
  client while still making ordering deterministic.
- The production-path test may use a real test service process or a faithful
  HTTP transport to the FastAPI application, but it must instantiate the
  production `NotesClient` and cross the service route. A mocked
  `list_notes()` method is not decisive evidence.
- No migration, new endpoint, or response-envelope change is authorized by
  this Draft unless the contract review establishes that it is necessary.

### Documentation

- Create and review a maintained notes-query specification under
  `docs/development/`, linked from `docs/development/index.md`, before
  consumer implementation. If it describes a target before execution, mark
  the target behavior `Not implemented`.
- After implementation, update the root API README, the
  `packages/notes_client` README, and the `apps/notes_cli` README so current
  guidance matches the verified contract. Keep ownership-specific details in
  the owning subsystem.
- Do not create placeholder documentation during this planning-only step.

### Task checklist

- [ ] Resolve the requirement questions and approve the public contract.
- [ ] Complete `010-public-api-contract.md` and its API-boundary evidence.
- [ ] Complete `020-reusable-client.md` after the API contract is stable.
- [ ] Complete `030-cli-integration.md` after the client contract is stable.
- [ ] Run the cross-surface verification in dependency order.
- [ ] Update maintained documentation and record final requirement evidence.

### Requirement verification

- **Contract-before-consumers:** review/approval of the maintained
  notes-query specification, followed by the API task’s contract tests, is
  the gate that permits client and CLI implementation.
- **Public API query behavior:** FastAPI integration tests with controlled
  notes assert bounded pagination, invalid-bound handling, explicit ordering
  including equal-key tie cases, optional filtering, and the unchanged
  unparameterized list response through `GET /notes/`.
- **Reusable client compatibility:** client tests inspect the generated
  request for each approved option and the no-argument call; a service-facing
  test uses the real client against the API to prove the encoded contract is
  consumable.
- **CLI and production path:** a CLI integration test invokes the command
  with approved options, a real `NotesClient`, and the FastAPI service, then
  asserts the service-derived output. Separate CLI parsing/output tests cover
  user-facing errors and preserve the existing no-option rendering.