# Define the notes-query public contract

Parent Task: tasks/20260919-notes-query/000-main.md

Define and review the single query contract that the FastAPI service, reusable Python client, and CLI will share. This subtask is a prerequisite for implementation and does not authorize code changes by itself.

## Requirements checklist

- [ ] The contract names the HTTP query parameters and corresponding client arguments and CLI options.
- [ ] The contract defines bounded pagination, including defaults, maximums, indexing, and invalid-value behavior.
- [ ] The contract defines supported sort fields, direction values, default ordering, and a unique tie-breaker for stable results.
- [ ] The contract defines text-filter scope, matching semantics, empty-input behavior, and encoding expectations.
- [ ] The contract defines response shape and explains how parameterized results coexist with the current unparameterized raw list.
- [ ] The contract defines the compatibility behavior of `GET /notes/`, `NotesClient.list_notes()` with no arguments, and `notes list` with no options.
- [ ] The contract is reviewed and treated as stable before service, client, or CLI consumer implementation begins.

## Unresolved requirement questions and material decisions

- Decide whether the page model is `limit`/`offset` or another public form.
- Decide whether metadata is required for a page response; preserving a list return from the existing client is the compatibility-preserving default recommendation.
- Decide whether sort and filter controls are fully shared across HTTP, client, and CLI or whether the CLI intentionally exposes a documented subset.
- Decide the exact error representation for invalid query values and whether it relies on FastAPI’s standard validation response.

## Research and supporting facts

- The current endpoint is a raw list at `src/app/api/notes.py`.
- The current client method has no parameters and returns decoded JSON directly at `packages/notes_client/notes_client/client.py`.
- The current CLI has one list command and no options at `apps/notes_cli/cli.py`.
- The service has no explicit order in `src/app/api/crud.py`, so stable sorting must be an explicit contract and implementation concern.
- `docs/development/index.md` currently records that no notes-query specification exists.

## Execution plan

Status: Draft

Write the smallest contract artifact that can be reviewed by service, package, and CLI maintainers. Include a compatibility table for no-query calls and concrete examples for each approved query dimension. Record whether query parameters are omitted, sent with defaults, or sent with explicit values by the client. Include invalid and boundary examples so downstream tests do not infer behavior from implementation details.

The contract review is a hard gate: the service subtask may not choose its own parameter names or response envelope, and client/CLI subtasks may not narrow or reinterpret the service behavior without an explicit contract decision. If a target specification is stored before implementation, label it as not yet implemented so it is not mistaken for current supported guidance.

### Implementation decisions and open questions

Planning decision: this subtask owns public semantics, not database or parser implementation. Any change to names, bounds, response shape, or compatibility behavior after review reopens this subtask and requires downstream plans to be reassessed.

The unresolved questions above remain open pending stakeholder review. Recommended baseline: raw note-list responses, optional `limit`/`offset`, explicit sort field and direction, `id` as the final tie-breaker, and case-insensitive substring matching over title and description.

### Documentation

Create or update one maintained contract/specification location only after selecting it under the repository documentation guidance. Link it from the appropriate development index if a new specification is needed. Keep target-only text visibly marked not implemented until the service and consumers are complete.

### Task checklist

- [ ] Draft the wire-level query contract and compatibility matrix.
- [ ] Draft the client and CLI mapping portion.
- [ ] Review and resolve all material contract questions.
- [ ] Mark the contract stable and hand it off to the implementation subtasks.

### Requirement verification

| Requirement | Planned evidence |
| --- | --- |
| Names and mappings | Reviewed table mapping HTTP parameters to client arguments and CLI options |
| Pagination contract | Examples and boundary cases for defaults, maximums, indexing, and invalid values |
| Stable sorting | Contract statement covering supported keys, direction, default, and unique tie-breaker |
| Filtering | Examples demonstrating fields, matching, case handling, and empty input |
| Response compatibility | Compatibility matrix showing no-query raw-list behavior at all three public boundaries |
| Stability gate | Maintainer review recorded before dependent subtasks are approved |

### Additional implementation verification

- Check the planned contract against FastAPI’s generated schema capabilities and the current client transport interface before approval.
- Confirm every public claim has one owning documentation location and is not duplicated as conflicting guidance.
