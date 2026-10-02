# Add supported notes querying across the API, client, and CLI

Plan the addition of one bounded, sortable, and text-filterable notes-query capability across the public HTTP API, reusable Python client, and CLI while preserving existing unparameterized behavior. This task records the contract-first sequencing and verification needed before implementation.

## Requirements checklist

- [ ] A reviewed public query contract defines bounded pagination, stable sorting, optional text filtering, validation/error behavior, response shape, defaults, and limits before consumer implementations begin.
- [ ] The notes collection endpoint supports the approved query contract, while an unparameterized request retains the current `200` raw JSON list behavior and current collection semantics.
- [ ] The reusable Python client exposes the approved query capability and serializes it to the HTTP contract; `list_notes()` with no arguments preserves its current request and list return behavior.
- [ ] The CLI exposes the approved query controls and continues to support the current unparameterized `notes list` behavior.
- [ ] The CLI has an integration path that uses the production `NotesClient` against the notes service, rather than a fake client standing in for the service boundary.
- [ ] Service, client, CLI, compatibility, and cross-boundary tests provide evidence at the boundary each requirement claims.
- [ ] Maintained documentation describes the supported contract and consumer usage in the owning service, client, and CLI locations in the same reviewed change as the behavior.

## Scope and workstreams

The work is intentionally split by public boundary:

1. Establish and review the wire and consumer contract.
2. Implement and test the HTTP service behavior.
3. Implement and test the reusable client mapping.
4. Implement and test CLI argument handling and output.
5. Run cross-boundary compatibility and production-path verification.

The scope excludes cursor pagination, changes to note create/update/delete behavior, new note fields, and breaking changes to the no-argument API or client call. Any response envelope, metadata, or additional query feature is out of scope unless explicitly added to the approved contract.

## Subtasks

- [ ] `tasks/20260919-notes-query/010-query-contract.md`
- [ ] `tasks/20260919-notes-query/020-api-query.md`
- [ ] `tasks/20260919-notes-query/030-client-query.md`
- [ ] `tasks/20260919-notes-query/040-cli-query.md`
- [ ] `tasks/20260919-notes-query/050-cross-boundary-verification.md`

## Unresolved requirement questions and material decisions

These questions must be resolved before the plan can move from `Draft` to `Approved` or implementation can start:

- What are the exact public query parameter and CLI option names, and is pagination expressed as `limit`/`offset` or another model?
- What are the default and maximum page bounds? Does a request that supplies only a filter or sort remain unbounded, or does it receive a default page limit?
- Which fields are sortable, what are the direction names, and what unique tie-breaker guarantees stable ordering when the selected values are equal?
- Does text filtering search title, description, or both; is it case-insensitive; and what matching operation is supported?
- Do parameterized API responses remain raw note lists, or do they include pagination metadata in an envelope? How does the client represent that result while keeping `list_notes()` with no arguments backward compatible?
- What validation and error status/body are part of the public contract for invalid, out-of-range, or unsupported query values?
- Which CLI output details are contractual when filtering or paginating, and should the CLI expose all query controls or a deliberately smaller supported subset?

Recommendation for review, not an approved requirement: use `limit` and `offset`, keep the response as a note list for both unparameterized and parameterized calls, use explicit sort fields with a unique `id` tie-breaker, and define a case-insensitive substring search over title and description. This minimizes compatibility surface while still providing the requested capability, but the exact bounds and names need agreement.

## Research and supporting facts

- `src/app/api/notes.py` currently exposes `GET /notes/` without query arguments and returns `crud.get_all()`.
- `src/app/api/crud.py` currently performs an unconstrained `notes.select()` with no explicit ordering, filtering, or pagination.
- `packages/notes_client/notes_client/client.py` currently calls `GET /notes/` without params and returns `response.json()` directly from `list_notes()`.
- `apps/notes_cli/cli.py` currently provides only `notes list`, and its command helper calls `client.list_notes()`.
- The CLI unit test injects a fake client; it does not currently cross the HTTP service boundary.
- Existing API and package tests only assert that the unparameterized result is a list. They do not establish order, paging, filtering, or compatibility details for a query contract.
- `README.md`, `packages/notes_client/README.md`, and `apps/notes_cli/README.md` describe current collection behavior. `docs/development/index.md` states that no notes-query specification exists.
- No nearest package-specific `AGENTS.md` or existing notes-query specification was found.

## Execution plan

Status: Draft

The contract subtask is the gate for all implementation subtasks. It must settle the public names, bounds, sorting and filtering semantics, result representation, and compatibility matrix. The service then owns query execution and endpoint validation; the client maps the approved public options without inventing a second contract; the CLI maps supported user-facing options through the real client. Cross-boundary verification follows only after those pieces are aligned.

The no-argument path must be tested explicitly at all three consumer boundaries. Parameterized service tests should use deterministic fixtures and assert the actual HTTP response. Client tests should capture the outgoing request and also exercise the approved response shape. CLI tests should retain focused formatting/parser coverage but add a real service integration that invokes the CLI without replacing the production client-to-service path with a fake.

Documentation is part of the contract gate: the target contract may be recorded as a clearly marked not-yet-implemented specification during planning, then maintained user/developer guidance is updated only when the implementation and verification make those claims true.

### Implementation decisions and open questions

Material decisions already made for planning:

- The contract is a separate first-class workstream because the HTTP API, Python package, and CLI are independently consumed public boundaries.
- No consumer implementation starts before the contract artifact and compatibility matrix are reviewed.
- The existing no-argument raw-list behavior is a preserved compatibility requirement, not an incidental test detail.
- The production-path CLI proof must use the real `NotesClient` and a real notes service instance or equivalent live service boundary; a fake client alone is insufficient.

Open questions are listed above and are intentionally not resolved by this draft. Resolving them changes the public contract and requires updating the affected subtask plans before approval.

### Documentation

The contract subtask will identify the smallest maintained location for the query specification. The service, client, and CLI README guidance will be updated in their owning packages once the behavior is implemented and verified. The existing statement that no notes-query specification exists must not remain after the contract is adopted.

### Task checklist

- [ ] Complete and review `tasks/20260919-notes-query/010-query-contract.md`.
- [ ] Complete the service work in `tasks/20260919-notes-query/020-api-query.md` after contract approval.
- [ ] Complete the client work in `tasks/20260919-notes-query/030-client-query.md` after the service contract is fixed.
- [ ] Complete the CLI work in `tasks/20260919-notes-query/040-cli-query.md` after the client and service paths are available.
- [ ] Complete cross-boundary verification in `tasks/20260919-notes-query/050-cross-boundary-verification.md`.
- [ ] Update maintained documentation and record evidence for every requirement.

### Requirement verification

| Requirement | Planned evidence |
| --- | --- |
| Stable public contract before consumers | Reviewed contract artifact and compatibility matrix showing the unparameterized API/client path and every approved query variant |
| HTTP query capability with compatibility | Endpoint integration tests against the FastAPI app and database, including no-query, each query dimension, invalid values, bounds, deterministic ties, and filter semantics |
| Reusable client capability with compatibility | Client tests that inspect the real outgoing path and params, plus an integration call against the service using the approved response representation |
| CLI capability with compatibility | Parser/output tests plus a live service integration that invokes the CLI through the production `NotesClient` |
| Cross-boundary consistency | Same fixtures and expected results asserted through HTTP, client, and CLI paths |
| Documentation | Review of the maintained contract and package guidance against implemented behavior |

### Additional implementation verification

- Run the repository’s relevant test commands with their normal gates enabled and report collection and exit status, not only individual assertions.
- Inspect the generated/open API surface after implementation to ensure the public query parameters and validation are represented as intended.
- Verify SQL ordering is explicit and deterministic rather than relying on database default order.
