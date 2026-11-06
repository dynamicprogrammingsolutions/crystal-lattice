# Notes Query Across API, Client, and CLI

Plan a supported notes-query capability across the public service, reusable Python client, and CLI.

## Requirements checklist

- [ ] The public notes collection supports bounded pagination, stable sorting, and optional text filtering under a defined contract.
- [ ] Requests that omit query options retain the current API response and `NotesClient.list_notes()` behavior.
- [ ] The reusable Python client and CLI expose the capability using the finalized public contract.
- [ ] The public API contract is established before client and CLI implementations rely on it.
- [ ] The CLI is verified through the production client against a running notes service, without substituting a fake client or fake service.

## Questions and decisions

- **Question — pagination contract:** What parameter names, default page size, maximum page size, and behavior for requests that specify sorting/filtering but omit a page size should apply? Recommendation: `limit` and `offset`, with a bounded default and hard maximum on parameterized requests; keep the exact no-query request unbounded for backward compatibility.
- **Question — sort contract:** Which note fields are sortable, which directions are supported, and what is the default? Recommendation: use `sort_by` and `order`, allow `id` and `title`, and use `id` as a deterministic tie-breaker.
- **Question — text-filter contract:** Which fields and matching semantics should the optional search cover? Recommendation: `q` performs a case-insensitive substring match over `title` and `description`.
- **Question — consumer interfaces:** Should client arguments and CLI flags mirror the HTTP names? Recommendation: client keyword arguments for `limit`, `offset`, `sort_by`, `order`, and `q`, with corresponding CLI options such as `--limit`, `--offset`, `--sort-by`, `--order`, and `--query`.
- These are public-interface decisions. Keep this plan in Draft and do not begin implementation until they are resolved and the plan is approved.

## Supporting details

- **Fact:** `GET /notes/` currently returns the complete collection as a JSON array through `crud.get_all()`.
- **Fact:** `NotesClient.list_notes()` currently makes an unparameterized `GET /notes/` request and returns decoded JSON.
- **Fact:** `notes list` currently prints each note's ID and title through the client.
- **Fact:** Existing API tests cover the unparameterized collection route; client and CLI tests use lightweight test doubles.
- **Fact:** The CLI project declares a `notes_cli.cli:main` console entry point, while the visible source is `apps/notes_cli/cli.py`. The production command's package/install path must be confirmed when designing its end-to-end check.
- **Fact:** Existing maintained documentation is in the root README and the client and CLI READMEs. `docs/development/index.md` says no notes-query specification exists.
- **Constraint:** The documentation guide favors updating the owning package documentation and avoiding placeholder pages. No task implementation or documentation changes have been made.

## Subtasks

- [ ] `tasks/20261102-notes-query/010-public-api.md` — Establish and deliver the public API contract first.
- [ ] `tasks/20261102-notes-query/020-python-client.md` — Add the reusable client interface after the API contract is delivered.
- [ ] `tasks/20261102-notes-query/030-cli.md` — Add CLI support and prove the real client-to-service path after the API and client are ready.

## Implementation plan

Status: Draft

The service owns the public query contract and applies filtering, ordering, and pagination at the collection route/database boundary. The exact parameter names, defaults, accepted sort values, and text matching behavior remain open in **Questions and decisions**; do not let the consumer interfaces invent or diverge from those semantics. Preserve the existing unparameterized route as a complete JSON-array response.

The independently reusable client maps its public method arguments to the finalized API query parameters. Its no-argument call remains the current bare collection request. The CLI maps its options to the client and retains the existing `notes list` output behavior when no options are supplied. The CLI deliverable owns one real HTTP integration check that exercises its production invocation, the production `NotesClient`, and a running notes service together.

Execution order is contract/API first, client second, CLI third. The API milestone must have a reviewed contract represented by the route behavior, OpenAPI schema, focused tests, and maintained API documentation before consumer implementation starts. This order prevents downstream packages from relying on a provisional interface. The client and CLI remain independently owned deliverables because they have separate package/application interfaces and compatibility expectations.

The change should be additive and require no schema migration: query computation should use the existing note fields and database table. The main risks are contract drift across three surfaces, unstable page boundaries from non-deterministic ordering, and an integration check that accidentally bypasses the real client or HTTP service. The API test should assert deterministic ordering and page boundaries; the CLI integration test should use a real listener and the actual configured client path. If a consumer fails, revert or disable that consumer before considering rollback of the additive API; preserve the existing no-parameter route throughout.

### Implementation decisions and open questions

The material public-contract and consumer-interface questions are listed above. Resolve them before execution; no behavior is selected by this draft plan.

### Documentation

Update the root README with the finalized public collection-query contract, `packages/notes_client/README.md` with client usage and compatibility, and `apps/notes_cli/README.md` with supported command options and invocation. Keep each description current with the behavior implemented in its owner. Do not create a separate specification page unless the contract cannot be documented clearly in the existing maintained locations.

### Task checklist

- [ ] Resolve the public contract and consumer-interface questions.
- [ ] Deliver and verify the public API before consumer work starts.
- [ ] Deliver the reusable client against the established contract.
- [ ] Deliver the CLI and its real client-to-service integration check.
- [ ] Update each owning README with supported behavior.

### Requirement verification

- **API query and compatibility requirements:** Focused tests through the public FastAPI collection route and the real database verify the approved pagination bounds, sort stability, filtering semantics, and unchanged no-query array behavior. These tests do not establish the reusable package or CLI invocation path.
- **Client and CLI requirements:** Client unit tests verify parameter mapping and no-argument compatibility. The decisive cross-component check belongs to the CLI subtask: run the actual CLI command against a live service using the production `NotesClient` configuration and known notes, and verify returned output reflects the requested query. It must not inject a fake client, mock HTTP responses, or call a route directly in place of the client.
- **Contract-before-consumers requirement:** Verify the API contract is documented and represented in route/OpenAPI tests before the client and CLI implementation milestones begin. This is an execution-order gate, not a test-only claim.

### Additional implementation verification

Confirm the CLI package's registered console entry point can be invoked in the integration environment. If its current source/package layout prevents that, make only the minimal CLI packaging adjustment necessary for the production invocation and include it in the CLI deliverable.