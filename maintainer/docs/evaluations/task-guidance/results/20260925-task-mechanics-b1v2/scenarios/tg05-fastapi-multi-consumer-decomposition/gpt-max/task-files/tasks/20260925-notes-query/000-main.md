# Notes-query capability across the service, client, and CLI

Draft execution handoff for one supported notes-query capability spanning the
FastAPI service, the reusable Python client, and the `notes` CLI. This task
records the plan only; it does not authorize implementation.

## Requirements checklist

- [ ] Define one stable, reviewed public query contract shared by the HTTP
  endpoint, `NotesClient`, and the CLI. The contract must specify parameter
  names and types, defaults and maximum bounds, sorting and tie-breaking,
  text-filter semantics, validation failures, and response shape.
- [ ] Add bounded pagination, deterministic stable sorting, and optional text
  filtering to the public notes collection API.
- [ ] Preserve the current unparameterized API behavior: a request to
  `GET /notes/` with no query parameters still returns the current JSON list
  of notes.
- [ ] Expose the same query capability through optional `NotesClient` inputs
  while preserving the zero-argument `list_notes()` call and its list result.
- [ ] Expose the same query capability through `notes list`, while preserving
  the no-option command's current output and routing all service access through
  the reusable production client.

## Workstreams and ownership

The public boundaries justify separate subtasks. The shared contract is owned
by the API subtask first; the client and CLI subtasks consume that contract
after it is approved.

- `010-public-api-contract.md` owns the contract specification, FastAPI
  collection behavior, database query semantics, and public API evidence.
- `020-reusable-client-query.md` owns the Python package method signature,
  request construction, compatibility behavior, and client documentation.
- `030-cli-query-integration.md` owns CLI arguments, rendering compatibility,
  package wiring, and the decisive CLI-to-service production-path check.

Requirement ownership is explicit: the shared contract and HTTP behavior are
owned by 010; the reusable-client behavior is owned by 020; the CLI behavior
and the connected three-boundary compatibility check are owned by 030. The
component evidence from 010 and 020 supports, but does not replace, 030's
real client-to-service check.

## Subtasks

- [ ] tasks/20260925-notes-query/010-public-api-contract.md
- [ ] tasks/20260925-notes-query/020-reusable-client-query.md
- [ ] tasks/20260925-notes-query/030-cli-query-integration.md

## Unresolved requirement questions and material decisions

These questions affect public compatibility and must be answered before this
draft becomes `Approved`. The suggested defaults are recommendations, not
decisions.

1. **Pagination vocabulary and bounds:** Should the contract use
   `limit`/`offset` or page-number/page-size parameters? What are the default
   and maximum page sizes, and does a request that filters or sorts without an
   explicit limit receive a bounded default? The recommended starting point
   is `limit` plus `offset`, with a documented positive maximum and
   `offset >= 0`; the no-query request remains the compatibility exception.
2. **Response shape:** Should parameterized requests continue to return a
   JSON list, or return an envelope containing items and pagination metadata?
   Returning a list for both forms best preserves the current API and client
   return type; an envelope would require a separate compatibility decision
   for `NotesClient` and the CLI.
3. **Sort contract:** Which existing fields may be selected (`id`, `title`,
   and/or `description`), how is direction expressed, and what is the
   default? A useful recommendation is an allow-listed `sort_by` plus
   `sort_order`, defaulting to `id` ascending, with `id` as a deterministic
   secondary key for every other sort.
4. **Text-filter semantics:** What parameter name and matching scope are
   required? The current schema has only `title` and `description`. A
   reasonable recommendation is a `q`/query value that performs a documented
   substring match across both fields, with explicit case-sensitivity and
   empty-string behavior.
5. **CLI surface and failures:** Should the CLI flags mirror the HTTP names
   exactly, and should invalid values be rejected locally by `argparse` or
   returned as service validation errors? The recommendation is user-facing
   flags such as `--limit`, `--offset`, `--sort-by`, `--sort-order`, and
   `--query`, with local type/range validation that follows the HTTP
   contract.
6. **Production-path harness:** The decisive check must exercise the CLI,
   real `NotesClient`, real HTTP transport, and FastAPI application together.
   Confirm whether a local ASGI server such as `uvicorn` may be added as
   test/development support if the existing environment does not provide
   one. An in-process route test plus a mocked client is not sufficient
   evidence for this requirement.

## Research and supporting facts

- `src/app/api/notes.py` currently exposes `GET /notes/` with no query
  parameters and returns `crud.get_all()` directly.
- `src/app/api/crud.py` currently selects every row without ordering,
  filtering, limit, or offset. The table has only `id`, `title`, and
  `description` columns.
- `packages/notes_client/notes_client/client.py` currently calls
  `transport.get("/notes/").json()` from a zero-argument `list_notes()`.
- `apps/notes_cli/cli.py` currently has one `list` subcommand, prints each
  note's ID and title, and uses `NotesClient.from_environment()` when no
  client is injected.
- The existing CLI tests inject a small fake client, and the client tests use
  a recording-free transport stub. Neither proves the client-to-service
  connection.
- `apps/notes_cli/pyproject.toml` does not currently declare
  `notes-client` as an install dependency, so the production-path work must
  verify or repair package wiring.
- The root README, package READMEs, and `docs/development/index.md` describe
  the current unparameterized behavior; no notes-query specification exists.

## Execution plan

Status: Draft

Execution waits until the public-contract questions are resolved, this plan
is explicitly approved, and the status is changed to `Approved`.

### Design and boundaries

The API remains the owner of query semantics and executes filtering, ordering,
and pagination in the database query. The client is a thin, typed request
builder that forwards only the approved parameters. The CLI parses the same
concepts, delegates to `NotesClient`, and keeps its existing one-line note
rendering unless the approved response contract requires otherwise.

The no-parameter path is a compatibility path throughout the stack:

- the API keeps its current list response and all-note behavior;
- the client makes the same collection request and returns a list;
- the CLI calls the client without query arguments and prints the same fields.

For parameterized requests, the API must validate bounds and allow-listed
sort values before constructing the SQL query. Every non-`id` sort must include
an explicit `id` tie-breaker so repeated requests over unchanged data have a
deterministic order. The client and CLI must not implement a second,
inconsistent filtering or sorting algorithm.

### Dependencies and sequencing

1. Resolve the questions above and write the reviewed target contract before
   implementing consumer-facing method arguments or CLI flags.
2. Complete `010-public-api-contract.md`, including public-route tests and the
   target/current documentation boundary.
3. Complete `020-reusable-client-query.md` after the API contract is fixed.
4. Complete `030-cli-query-integration.md` after both the API and client
   contracts are fixed. Its end-to-end check is the release gate for the
   connected path.
5. Run the boundary tests, the full relevant test set, the production-path
   check, and documentation review before marking requirements complete.

### Risks and mitigations

- Ambiguous parameter names or defaults could make the three consumers
  incompatible. Resolve and review one contract first.
- Database engines may return different implicit row orders. Always specify
  the primary order and deterministic ID tie-break.
- SQLite text matching can have surprising case behavior. Define the
  semantics publicly and test mixed-case title and description values.
- A client mock can make an otherwise disconnected CLI appear correct. Make
  the real CLI-to-service invocation a named, non-waivable acceptance check.
- The CLI currently relies on an undeclared sibling package. Verify install
  metadata and the actual CLI entry point as part of the integration work.
- Persistent SQLite state can make pagination tests order-dependent. Seed
  isolated test data and clean it up through the existing test harness or a
  disposable database.

### Implementation decisions and open questions

No material public decision is final in this Draft. The six questions above
must be answered before implementation begins. The provisional interface used
in examples is `limit`, `offset`, `sort_by`, `sort_order`, and `q`; it must
not be documented as supported or consumed by the client/CLI until approved.

The implementation may resolve local choices such as helper placement and
fixture organization, but it may not silently change response shape,
parameter names, bounds, matching semantics, or compatibility behavior.

### Documentation

- Create or update one cross-boundary contract source at
  `docs/development/notes-query.md`, clearly marked `Not implemented` while
  it describes the target during planning. Remove that marker only when the
  API, client, and CLI all satisfy the reviewed contract.
- Update `docs/development/index.md` to link the contract once it exists.
- Update the root, client, and CLI READMEs with current supported examples
  and the preserved no-argument behavior after implementation.
- Keep target-only claims out of current user guidance until the production
  path and boundary tests pass.

### Task checklist

- [ ] Resolve the public-contract questions and record the approved choices.
- [ ] Change this plan to `Status: Approved` before execution.
- [ ] Complete tasks/20260925-notes-query/010-public-api-contract.md.
- [ ] Complete tasks/20260925-notes-query/020-reusable-client-query.md.
- [ ] Complete tasks/20260925-notes-query/030-cli-query-integration.md.
- [ ] Run focused boundary tests and the full relevant test set.
- [ ] Run the decisive real CLI-to-service check.
- [ ] Update maintained documentation and append completion evidence.

### Requirement verification

- **Shared stable contract:** reviewed `docs/development/notes-query.md`
  plus API, client, and CLI mappings in the completed subtasks; no consumer
  implementation starts before the contract gate.
- **API query behavior:** public `TestClient` requests to `GET /notes/` with
  seeded notes prove filtering, bounded pagination, ordering, tie-breaking,
  validation, and the unchanged no-query list response.
- **Reusable client behavior:** client tests prove exact parameter forwarding
  and zero-argument compatibility; the connected CLI check proves those
  requests reach the real service.
- **CLI behavior and connection:** the decisive check invokes the production
  CLI path with `NOTES_API_URL` set to a running FastAPI service, uses
  `NotesClient.from_environment()`, supplies query options, and verifies the
  resulting rendered notes. It must not inject a fake client or mock the
  service route.
- **Documentation:** the three maintained READMEs and development index
  describe only the implemented contract, including bounds and examples.

### Additional implementation verification

- Run the service, client-package, and CLI test suites with their actual
  package import/install setup rather than relying only on a repository-wide
  path coincidence.
- Verify the installed `notes` entry point can locate the reusable client and
  that the service can be started on a disposable local port for the decisive
  check.
- Review the final diff for accidental changes to no-query requests, list
  return types, default output, and unsupported query parameters.