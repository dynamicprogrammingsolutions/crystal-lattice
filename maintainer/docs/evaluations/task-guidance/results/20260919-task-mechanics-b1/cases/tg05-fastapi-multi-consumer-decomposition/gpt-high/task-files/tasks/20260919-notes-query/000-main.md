# Notes query capability across API, client, and CLI

Plan and coordinate one supported notes-query capability across the public
FastAPI service, the reusable `notes-client` package, and the `notes` CLI.
Execution is intentionally not authorized by this planning handoff.

## Requirements checklist

- [ ] Establish one stable, documented query contract before client or CLI
      consumers depend on it. The contract must cover bounded pagination,
      deterministic sorting, optional text filtering, validation/error behavior,
      and compatibility behavior.
- [ ] Extend the public notes collection API with bounded pagination, stable
      sorting, and optional text filtering while preserving the current
      unparameterized response and request behavior.
- [ ] Expose the same capability through `NotesClient.list_notes()` without
      changing the no-argument call or its returned list shape.
- [ ] Expose the capability through `notes list`, preserve the existing
      no-argument command, and prove the CLI uses the production client-to-
      service path rather than a test-only client shortcut.
- [ ] Update maintained user-facing documentation for the service, client,
      and CLI in the same reviewed implementation.
- [ ] Add boundary-appropriate tests for the service, client, and CLI,
      including regression coverage for unparameterized behavior and an
      end-to-end CLI-to-service check.

## Scope and workstreams

The service owns the HTTP contract, query validation, filtering, ordering,
pagination, and API integration evidence. The client owns the typed/public
Python method surface and HTTP parameter encoding. The CLI owns user-facing
flags, command validation, output compatibility, and the production-path
integration test. The work is deliberately sequenced so the client consumes
the service contract and the CLI consumes the client surface.

## Open requirement questions and material design decisions

The request establishes the capability but not all public contract details.
These questions must be answered before the Draft plan becomes Approved:

- What are the canonical HTTP and Python names for pagination, filtering,
  sorting field, and sorting direction? Recommendation: use `limit`, `offset`,
  `q`, `sort`, and `order` consistently, with client keyword names matching
  the HTTP names where that remains idiomatic.
- What are the default and maximum page sizes, and does an explicit `limit`
  need to be positive while `offset` may be zero? Recommendation: choose a
  documented finite maximum and reject out-of-range values with the API's
  normal validation response.
- Should `/notes/` with no query parameters continue returning every note as
  the current JSON array, with bounded behavior activated by query options?
  Recommendation: yes, to preserve existing API and client behavior; an
  explicitly paginated request returns the same array-of-note shape.
- What fields are sortable, what is the default order, and how are ties
  resolved? Recommendation: expose only existing note fields and always append
  `id` as a deterministic tie-breaker.
- What does text filtering search and how is it matched? Recommendation:
  case-insensitive substring matching across both `title` and `description`,
  with empty/whitespace-only input treated as no filter.
- Which CLI option spellings and invalid-input messages are part of the
  supported application contract? Recommendation: expose long options that
  map one-to-one to the approved query names and let argparse reject invalid
  values before making a request.

These are public compatibility decisions, not implementation details. The
executor must update the checklist and subtask plans after the user resolves
them.

## Research and supporting facts

- `src/app/api/notes.py` currently serves `GET /notes/` with no parameters and
  returns `crud.get_all()` directly as a JSON array.
- `packages/notes_client/notes_client/client.py` currently calls
  `transport.get("/notes/")` with no parameters; `list_notes()` returns the
  decoded JSON unchanged.
- `apps/notes_cli/cli.py` currently supports only `notes list`, iterates the
  client's list, and prints `id: title`.
- Existing tests only establish list-shaped responses and command output; they
  do not inspect query encoding, ordering/filter semantics, validation, or a
  real service boundary.
- The repository has no existing notes-query specification. The maintained
  documentation is currently limited to the root README and the package
  READMEs, with `docs/development/index.md` stating that no specification
  exists.

## Subtasks

- [ ] `tasks/20260919-notes-query/010-service-contract-and-api.md` — establish
      the contract and implement/verify the public service behavior.
- [ ] `tasks/20260919-notes-query/020-reusable-client.md` — map the approved
      contract into `NotesClient` after the service contract is fixed.
      Depends on `tasks/20260919-notes-query/010-service-contract-and-api.md`.
- [ ] `tasks/20260919-notes-query/030-cli-production-path.md` — add CLI
      controls and prove the real CLI → client → HTTP service path.
      Depends on
      `tasks/20260919-notes-query/020-reusable-client.md`.

## Execution plan

Status: Draft

Complete the service contract first, including its compatibility rule and
examples, then implement the API and its integration tests. Use that contract
as the only source for client parameter names and semantics. Extend the
client while retaining the no-argument request exactly, then add CLI options
that pass through the client. Finish with an integration test that invokes
the CLI against a running FastAPI service through the real `NotesClient`, and
run the focused suites for all three boundaries.

### Implementation decisions and open questions

The decomposition and dependency order are decided. The public parameter
names, defaults, bounds, filter semantics, sorting fields/order, and CLI
spelling remain open as listed above. No implementation should begin until
those choices are confirmed and copied into the service and consumer
subtasks.

### Documentation

The implementation should update the smallest maintained documentation
surfaces that own each claim: the root service README for the HTTP contract,
`packages/notes_client/README.md` for Python usage, and
`apps/notes_cli/README.md` for command usage. Remove or replace the
“no notes-query specification” statement in `docs/development/index.md` if
the approved contract is maintained there or linked from there; do not create
an empty specification hierarchy.

### Task checklist

- [ ] Resolve the open public-contract questions and update all affected
      requirements and subtask plans.
- [ ] Execute and complete the service/API subtask.
- [ ] Execute and complete the reusable-client subtask.
- [ ] Execute and complete the CLI production-path subtask.
- [ ] Run the required focused and cross-boundary verification, recording
      evidence at the boundary it proves.
- [ ] Confirm documentation claims match the implemented, tested behavior.

### Requirement verification

- [ ] Stable contract: a reviewed service contract and examples define the
      exact parameters, bounds, defaults, validation, matching, ordering, and
      compatibility behavior before consumer implementation starts.
- [ ] Public API capability and compatibility: FastAPI integration tests issue
      real `GET /notes/` requests covering pagination, filter, deterministic
      order/tie-breaking, invalid values, and the no-parameter array response.
- [ ] Reusable client: client tests inspect the actual transport request for
      encoded options and verify that `list_notes()` with no arguments still
      makes the existing request and returns the decoded list.
- [ ] CLI production path: an integration test invokes the command with query
      options against a running FastAPI service through `NotesClient`, and
      verifies the resulting output; a mocked client remains only for local
      rendering/argument tests.
- [ ] Documentation: review each maintained README/index claim against the
      approved contract and passing boundary tests.