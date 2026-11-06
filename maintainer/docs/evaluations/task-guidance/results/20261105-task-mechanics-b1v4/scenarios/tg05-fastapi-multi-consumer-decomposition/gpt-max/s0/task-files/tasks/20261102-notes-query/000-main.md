# Supported Notes Query

Plan a single supported notes-query capability across the public API, reusable Python client, and CLI.

## Requirements checklist
- [ ] The public notes collection supports bounded pagination, stable sorting, and optional text filtering.
- [ ] Requests without query parameters preserve the existing public API collection response and the existing no-argument `NotesClient.list_notes()` behavior.
- [ ] The public query contract is defined and documented before client and CLI behavior depends on it.
- [ ] The reusable Python client exposes the supported query options.
- [ ] The CLI exposes the supported query options and demonstrates the production client-to-service path.

## Questions and decisions
- **Question — API contract:** Decide the parameter names, page bounds/defaults, sorting fields and direction syntax, stable tie-breaker, filter matching fields and semantics, and whether filtered/paginated results use an envelope or retain a bare array. These choices affect public compatibility. Recommendation: preserve the bare-array response when parameters are absent and use explicit documented pagination parameters with a bounded maximum; settle the parameterized response shape before consumer work.
- **Question — text matching:** Decide whether matching is case-sensitive and whether the query searches title, description, or both. Do not infer behavior while implementing.

## Supporting details
- The current FastAPI collection route returns `crud.get_all()` directly, with no query parameters.
- `NotesClient.list_notes()` currently issues `GET /notes/` and returns decoded JSON.
- The CLI currently offers `notes list` and prints each note's ID and title through `NotesClient`.
- The API, client package, and CLI have independently maintained readmes and test suites. The public HTTP contract, reusable package interface, and CLI interface are separate compatibility boundaries.

## Subtasks
- [ ] `tasks/20261102-notes-query/010-public-api.md`
- [ ] `tasks/20261102-notes-query/020-python-client.md`
- [ ] `tasks/20261102-notes-query/030-cli.md`

## Implementation plan
Status: Draft

The public HTTP API owns query semantics and its compatibility boundary. It must settle and document the query contract before consumers adopt it; the existing no-parameter collection request remains a bare list. The client owns a reusable Python interface that maps its supported options onto that contract while retaining no-argument behavior. The CLI owns argument parsing and presentation, delegating the query to the real client rather than reproducing query logic.

Execution order follows the contract dependency: first define and implement the API contract, then implement the client mapping, then expose those options in the CLI. Keep focused API and client evidence with their respective deliverables. For the CLI, the decisive integration check must invoke the actual CLI command with the production `NotesClient` against the actual FastAPI application and verify that query arguments affect the notes returned; tests that mock the client or route separately do not prove this connection.

The main risk is a mismatched or prematurely relied-upon query contract across the three boundaries. Mitigate it by resolving the open contract questions before consumer implementation and keeping contract documentation and API tests aligned. The no-parameter API/client behavior is a required regression check. If the parameterized contract proves incompatible with the established API, stop before consumer rollout and revise the proposed contract for review; do not silently change the compatibility boundary. Changes remain additive and can be reverted by removing the query implementation and consumer options while retaining the original unparameterized path.

### Implementation decisions and open questions
- Resolve the API and text-matching questions above before execution; no parameter names, defaults, bounds, ordering fields, matching rules, or parameterized response shape are approved yet.
- Keep implementation and documentation within the subsystem that owns each behavior.

### Documentation
- Update the root API documentation and package readmes that describe current behavior as part of the implementation that makes the claims true.
- Add or update maintained API documentation only after the query contract is approved; do not present target-only behavior as currently supported.

### Task checklist
- [ ] Resolve the public API and filter-semantics questions with the user.
- [ ] Complete the public API contract and implementation.
- [ ] Add the client interface after the API contract is stable.
- [ ] Add CLI options and the real client-to-service integration check.

### Requirement verification
- Bounded pagination, stable sorting, and text filtering: exercise the actual public collection route with representative parameterized requests; do not rely only on mocked query logic.
- Preserved unparameterized behavior: verify the public route still returns a bare list and `list_notes()` without arguments still calls the collection route without query parameters.
- Stable contract before consumers: review the documented API contract before client/CLI changes rely on it.
- Client query support: verify the real client constructs requests matching the approved contract and decodes the supported result.
- CLI and production path: run the actual CLI command with the production client connected to the actual FastAPI application and assert query behavior in the output. Mocked-client CLI tests alone are not decisive.

### Additional implementation verification
- Run the focused API, client, and CLI suites after their respective changes, plus repository-level checks available for the completed change.

## Implementation notes