# Freeze the notes-query public contract

Define and obtain approval for the stable notes-query contract that the
FastAPI service, reusable Python client, and CLI will all consume.

## Requirements checklist

- [ ] C1. The contract specifies query parameter names, types, bounds,
  defaults, and invalid-input behavior for bounded pagination.
- [ ] C2. The contract specifies sortable fields, direction syntax, default
  ordering, and a deterministic tie-breaker.
- [ ] C3. The contract specifies text-filter scope, matching and
  case-sensitivity rules, empty values, and the public parameter name.
- [ ] C4. The contract specifies the response shape and compatibility behavior
  for both unparameterized and parameterized requests.
- [ ] C5. The contract maps the HTTP options to the client method and CLI
  surface and is human-approved before dependent implementation begins.

Parent Task: `tasks/20260926-notes-query/000-main.md`

Depends On: None

## Scope

This task owns the public decision boundary and its documentation. It does
not implement the route, client, or CLI. It may draft a target contract, but
the document must not be presented as current supported behavior until the
dependent implementation is shipped.

## Supporting facts

- No notes-query specification currently exists.
- The current service route returns a JSON array for `GET /notes/` without
  parameters.
- The current client method has no arguments and returns the decoded JSON
  directly.
- The current CLI has one `list` command and prints one line per note.

## Execution plan

Status: Draft

Resolve the open public choices from the parent task, then write a compact
contract at `docs/development/notes-query.md`. It should include concrete
request examples, response examples, validation/error examples, a
compatibility matrix, and the client/CLI naming map. Keep the contract
independent of internal module names so it remains useful to HTTP consumers.

Review the document as a public API proposal. Once approved, treat parameter
names, response shape, and compatibility rules as frozen for the dependent
service, client, and CLI tasks. If a later implementation discovery requires a
public change, stop dependent work and return this task and the parent to
Draft before changing the document.

### Implementation decisions and open questions

The document must explicitly resolve pagination model and bounds, sorting and
tie-breaking, text matching, response envelope versus array, invalid-input
behavior, and CLI option names. Do not choose a value merely because it is
convenient for the current SQLite implementation; each choice is part of the
consumer-facing contract.

The compatibility recommendation in the parent—array responses, explicit
pagination, bounded `limit`/`offset`, case-insensitive title/description
substring matching, and an `id` tie-breaker—can be used as a review starting
point but requires approval before it becomes binding.

### Documentation

- Create `docs/development/notes-query.md` as the maintained contract source.
- Update `docs/development/index.md` to link to the specification only after
  the contract has been reviewed; while the feature is not shipped, label the
  target behavior `Not implemented`.
- Do not update package or CLI user guidance in this task; those owners will
  document shipped behavior after implementation.

### Task checklist

- [ ] Resolve the public questions recorded in the parent task.
- [ ] Draft the contract with examples and compatibility matrix.
- [ ] Review and approve the contract.
- [ ] Record approval and unlock `020-api.md`, `030-python-client.md`, and
  `040-cli.md`.

### Requirement verification

- C1–C4: Inspect the reviewed contract for complete request, response,
  validation, and compatibility examples; unresolved public choices leave the
  requirements incomplete.
- C5: Human approval is the decisive gate. The dependent task files must not
  move to execution until the approved contract is available.