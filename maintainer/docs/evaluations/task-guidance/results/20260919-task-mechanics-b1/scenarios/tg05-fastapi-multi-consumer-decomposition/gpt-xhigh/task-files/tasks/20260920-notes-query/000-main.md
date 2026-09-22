# Notes query across API, reusable client, and CLI

Plan the coordinated delivery of one supported notes-query capability through
the FastAPI service, the independently packaged Python client, and the CLI.
This task records the contract and execution boundaries only; it does not
implement the capability.

## Requirements checklist

- [ ] A single public notes-query contract is agreed and documented before the
  reusable client or CLI begins relying on it.
- [ ] The supported query capability provides bounded pagination, deterministic
  stable sorting, and optional text filtering across the public API, reusable
  Python client, and CLI.
- [ ] An unparameterized `GET /notes/` request continues to return the current
  JSON-array collection behavior.
- [ ] An unparameterized `NotesClient.list_notes()` call continues to return
  the current list behavior.
- [ ] The CLI exposes the supported query capability through its public
  `notes list` command and retains its current unparameterized listing behavior.
- [ ] The CLI has decisive integration evidence that crosses the production
  CLI-to-`NotesClient`-to-service path.

## Scope and workstreams

The work is divided by independently maintained public boundaries:

1. `010-api-contract.md` owns the contract-first API delivery and service
   behavior.
2. `020-reusable-client.md` owns the Python package surface and wire mapping.
3. `030-cli.md` owns CLI argument and output behavior plus the production-path
   integration proof.

The API/contract work is the prerequisite for both consumers. The CLI depends
on the client surface as well as the API contract. Tests and documentation stay
with the boundary whose behavior they prove, while the parent retains the
cross-boundary acceptance view.

## Unresolved requirement questions

These choices materially change the public HTTP, Python, or CLI contract and
must be answered before the Draft plan becomes Approved:

- Which HTTP parameter names and Python keyword arguments represent page size,
  page position, sorting, and text filtering?
- What are the default and maximum page sizes, what pagination model is used
  (for example, offset plus limit), and how are invalid or out-of-range values
  reported?
- Which sort key and direction are supported, and what tie-breaker makes the
  ordering stable when records compare equally?
- Does text filtering search title, description, or both; is it substring or
  token matching; and is matching case-sensitive?
- Does the query response remain a bare JSON array/list for every query, or is
  metadata such as total count required? Which CLI flags and output behavior
  correspond to the settled contract?

## Research and supporting facts

- `src/app/api/notes.py` currently exposes `GET /notes/` with no query
  parameters and returns `crud.get_all()` directly. The collection response is
  therefore a JSON array; item routes and CRUD operations are separate.
- `src/app/api/crud.py` currently uses `notes.select()` without an explicit
  ordering or pagination/filtering clause.
- `packages/notes_client/notes_client/client.py` currently implements
  `NotesClient.list_notes()` with no arguments and calls
  `transport.get("/notes/").json()`.
- `apps/notes_cli/cli.py` currently exposes only `notes list`; `list_command`
  calls `client.list_notes()` and prints each note as
  `<id>: <title>`.
- Existing API, client, and CLI tests are minimal. The API test uses FastAPI's
  `TestClient`; the client and CLI tests use small local transport/client
  doubles. No existing notes-query specification is present.
- Maintained user/developer documentation is split among the root README, the
  client README, the CLI README, and `docs/development/index.md`. The
  documentation guidance has been read before planning a new contract
  document.

## Execution plan

Status: Draft

First settle the public contract questions and capture the result in a
developer-facing specification. Then implement and verify the service at the
HTTP boundary. Only after that contract is stable should the reusable client
adopt the query arguments, followed by the CLI flags and its real
client-to-service proof. Preserve the no-argument paths throughout and update
maintained documentation in the same reviewed implementation change.

The planned dependency order is:

`010-api-contract.md` → `020-reusable-client.md` → `030-cli.md`

The client can be developed after the API contract is fixed; the CLI's
decisive integration check must use a real `NotesClient` connected to the
application rather than the existing CLI-only fake.

### Implementation decisions and open questions

- Decision: use a parent task with three subtasks because the HTTP API, Python
  package, and CLI are separate public ownership and compatibility boundaries.
- Decision: keep this work at `Status: Draft`; the user requested planning and
  task structure without implementation.
- Decision: make the API contract/specification the first executable workstream
  so consumer signatures and flags cannot drift from the wire behavior.
- Open: the five contract questions above remain unresolved. They affect
  requirements, so execution must wait for answers rather than selecting
  defaults in a task file.

### Documentation

- Create a maintained `docs/development/notes-query.md` contract/specification
  owned by the API workstream, and link it from
  `docs/development/index.md`. If the specification is staged before the
  implementation is complete, mark it visibly as proposed/not implemented
  until the public behavior is verified.
- Update `README.md`, `packages/notes_client/README.md`, and
  `apps/notes_cli/README.md` in the implementation change so each audience
  describes the supported query behavior and the preserved no-argument path.
- Do not add documentation claims during this planning-only task.

### Task checklist

- [ ] Resolve the public contract questions and record the approved decisions
  in the API subtask and specification.
- [ ] Complete `tasks/20260920-notes-query/010-api-contract.md`.
- [ ] Complete `tasks/20260920-notes-query/020-reusable-client.md` after the
  API contract is stable.
- [ ] Complete `tasks/20260920-notes-query/030-cli.md` after the API and client
  surfaces are stable.
- [ ] Update the parent evidence and completion notes only after all approved
  requirements have decisive verification.

### Requirement verification

- The API contract, pagination bounds, stable ordering, text filtering, and
  unparameterized HTTP compatibility are decisively verified at the real
  `GET /notes/` boundary in the API subtask.
- The reusable-client mapping and no-argument behavior are verified through
  the package's public `NotesClient` method, with request-parameter assertions
  and a real service-backed check where needed.
- The CLI capability and preserved no-argument output are verified through the
  public `notes list` entry point.
- The CLI requirement is decisively verified by invoking the CLI with a real
  `NotesClient` connected to the FastAPI application, then asserting output
  produced from service data; a fake CLI client alone is not sufficient.

### Additional implementation verification

- Run the API, client, and CLI test suites with their intended import paths
  and confirm collection and clean exit.
- Check that invalid query values are rejected consistently at the documented
  boundary and that existing CRUD route tests remain green.
- Review the final API/client/CLI documentation together for matching names,
  defaults, limits, sorting semantics, filter semantics, and response shape.

## Subtasks

- [ ] `tasks/20260920-notes-query/010-api-contract.md`
- [ ] `tasks/20260920-notes-query/020-reusable-client.md`
- [ ] `tasks/20260920-notes-query/030-cli.md`