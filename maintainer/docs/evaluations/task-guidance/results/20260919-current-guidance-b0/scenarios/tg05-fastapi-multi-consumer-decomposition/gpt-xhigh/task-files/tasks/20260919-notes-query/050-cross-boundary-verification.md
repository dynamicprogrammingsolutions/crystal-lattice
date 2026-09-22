# Verify notes-query compatibility across all consumers

Parent Task: tasks/20260919-notes-query/000-main.md

Depends On: tasks/20260919-notes-query/020-api-query.md, tasks/20260919-notes-query/030-client-query.md, tasks/20260919-notes-query/040-cli-query.md

Run the final evidence pass across the HTTP API, reusable client, and CLI, with explicit compatibility checks and a production client-to-service path.

## Requirements checklist

- [ ] The same deterministic fixture expectations are verified through the approved API, client, and CLI paths.
- [ ] Unparameterized API, client, and CLI behavior is shown to remain compatible.
- [ ] Bounded pagination, stable sorting, and text filtering are each verified at the public boundary and in at least one combined scenario.
- [ ] Invalid and boundary inputs are verified according to the stable contract.
- [ ] The CLI integration uses the production `NotesClient` against a real notes service instance without a fake client replacing the service.
- [ ] Relevant repository tests and package-level checks collect and exit successfully, or blocked checks are explicitly recorded.
- [ ] Documentation and generated API descriptions agree with the implemented contract.

## Unresolved requirement questions and material decisions

No new public behavior may be decided here. Any mismatch discovered between consumers and the approved contract must return to `tasks/20260919-notes-query/010-query-contract.md` before changing implementation expectations.

## Research and supporting facts

- Existing tests are split across `src/tests`, `packages/notes_client/tests`, and `apps/notes_cli/tests`.
- Current API and client tests establish only list-shaped unparameterized results.
- Current CLI tests use an injected fake client and therefore do not establish the required service integration.
- The root and package READMEs are the currently maintained user-facing descriptions of collection behavior.

## Execution plan

Status: Draft

Create a small cross-boundary fixture with records that expose ordering ties, page boundaries, matching and nonmatching text, and case differences. Assert the expected note IDs and display lines through the HTTP response, the production client, and the CLI. Include a no-argument run at each layer before exercising options. Verify that the CLI’s live integration configures the normal environment-based client and reaches the actual service route and database.

Run the least expensive focused tests first, then the full relevant suite with normal gates. Inspect test collection and process exit status. Compare the final OpenAPI schema, contract artifact, README examples, and CLI help for drift. Record any environmental limitation, such as inability to launch a live service runner, as an unresolved verification gap rather than treating a mocked transport as equivalent evidence.

### Implementation decisions and open questions

Verification is subordinate to the approved contract. The only allowed local decisions are fixture shape, test ordering, and safe service lifecycle setup. A failed cross-boundary expectation is evidence of a contract or implementation mismatch and must not be papered over by weakening the assertion.

### Documentation

Confirm the service contract, client README, CLI README, and any development index link describe the same names, defaults, bounds, sorting, filtering, response shape, and no-argument compatibility behavior. Remove or replace the current “no notes-query specification exists” statement once the supported contract is complete.

### Task checklist

- [ ] Build deterministic cross-boundary fixtures.
- [ ] Verify no-argument compatibility at all public boundaries.
- [ ] Verify each query dimension and a combined query.
- [ ] Run the production client-to-service CLI integration.
- [ ] Run focused and full relevant test gates.
- [ ] Inspect generated API/documentation surfaces and record any gaps.

### Requirement verification

| Requirement | Planned evidence |
| --- | --- |
| Shared capability | Matching expected IDs/results across HTTP, client, and CLI for the same fixture |
| Compatibility | No-option requests/calls/commands retain the prior list/output behavior |
| Pagination/sorting/filtering | Public-boundary assertions for individual and combined query cases |
| Validation | Contract-defined invalid and boundary cases at API and CLI entry points |
| Production path | Live service run through `NotesClient.from_environment()` and CLI invocation without injected client |
| Test evidence | Focused and full relevant test commands with clean collection and exit |
| Documentation/schema | Final review against the approved contract |

### Additional implementation verification

- Check for accidental client-side resorting/filtering that could hide service defects.
- Check that repeated requests over an unchanged dataset return the same order.
- Check that no compatibility test depends on pre-existing database rows or insertion-order accidents.
