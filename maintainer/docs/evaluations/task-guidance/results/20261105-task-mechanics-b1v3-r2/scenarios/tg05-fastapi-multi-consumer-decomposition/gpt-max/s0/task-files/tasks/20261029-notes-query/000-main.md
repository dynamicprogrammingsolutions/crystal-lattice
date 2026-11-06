# Notes Query Capability

Plan one supported notes-query capability across the public API, reusable Python client, and CLI.

## Requirements checklist

- [ ] The public notes collection supports bounded pagination, stable sorting, and optional text filtering under a documented, stable contract.
- [ ] Requests without query parameters preserve current API behavior and response shape.
- [ ] The reusable Python client exposes the query capability and preserves the current no-argument `list_notes()` behavior.
- [ ] The CLI exposes the query capability through the reusable client and proves the production client-to-service path.

## Scope

The API, independently consumable client package, and CLI each own a public compatibility boundary. Keep their implementation and focused documentation with their owners. The CLI's decisive integration check must use the production CLI and client against the real service; mocked unit checks alone are insufficient.

## Unresolved questions

- **Requirement question:** What query parameter names and semantics define pagination (for example, offset/limit versus page/page-size), including defaults, maximum bounds, and out-of-range behavior?
- **Requirement question:** Which sort keys and direction syntax are supported, and what tie-breaker/order guarantees make results stable?
- **Requirement question:** What text does the optional filter search (title, description, or both), and what matching/case semantics apply?
- **Requirement question:** Which of these options should the CLI expose, and what CLI flag names should it use?

These affect the public contract and must be answered before execution. The API contract is a prerequisite for client and CLI integration.

## Supporting details

- **Fact:** `GET /notes/` currently returns the full collection as a JSON array; API tests only assert that it is a list.
- **Fact:** `NotesClient.list_notes()` currently requests `/notes/` without parameters, and its package test only checks a list result.
- **Fact:** `notes list` uses the client, but its test injects a fake client; no current test exercises CLI → production client → service.
- **Fact:** The root README, client README, and CLI README each describe current unparameterized behavior.
- **Decision:** Use three owner-aligned subtasks so API contract, client compatibility, and CLI production-path acceptance each have a clear owner.

## Subtasks

- [ ] `tasks/20261029-notes-query/010-public-api.md`
- [ ] `tasks/20261029-notes-query/020-python-client.md`
- [ ] `tasks/20261029-notes-query/030-cli.md`

## Execution plan
Status: Draft

The API owns the query contract, filtering, ordering, pagination bounds, and preservation of the current unparameterized array response. The independently maintained Python package maps optional query arguments to that contract while leaving calls with no arguments behaviorally unchanged. The CLI maps its approved options to the client. The CLI acceptance check traverses the production CLI entry point and client transport into a running notes service; fake-client tests may supplement but cannot replace it. The API contract must be agreed before implementing either consumer.

Execution proceeds API first, then the client, then the CLI. Update audience-appropriate maintained README guidance in the same change that makes each behavior supported. Validate API behavior at the HTTP boundary, client serialization against the agreed HTTP query contract, and CLI behavior through the real service path. Preserve current no-parameter behavior at each boundary.

### Implementation decisions and open questions

- Resolve all requirement questions above before execution; do not infer public names, defaults, bounds, sorting tie-breakers, or filtering semantics.
- Once the contract is approved, local implementation choices may remain with each owner as long as they preserve that contract.

### Documentation

- Update the root README for the supported public API query contract.
- Update `packages/notes_client/README.md` for client method arguments and compatibility behavior.
- Update `apps/notes_cli/README.md` for approved CLI options and usage.

### Task checklist

- [ ] Complete `tasks/20261029-notes-query/010-public-api.md`.
- [ ] Complete `tasks/20261029-notes-query/020-python-client.md` after the API contract is fixed.
- [ ] Complete `tasks/20261029-notes-query/030-cli.md` after the API/client contract is fixed.

### Requirement verification

- Requirement 1: API HTTP-boundary tests exercise pagination bounds, stable sorting, filtering, and the agreed contract.
- Requirement 2: API HTTP-boundary regression test verifies the no-query response remains the full JSON array.
- Requirement 3: Client tests verify request query encoding against the actual API contract and preserve no-argument invocation behavior.
- Requirement 4: An automated CLI integration test runs the production CLI and `NotesClient` against a real running service and verifies resulting output; mocked CLI tests do not satisfy this check.

### Additional implementation verification

- Run focused API, client, and CLI suites after their respective changes; run the full available suite at completion.
- Verify the CLI integration check starts and tears down a real service/database path without replacing the production client or route.