# Notes Query Across API, Client, and CLI

Plan and deliver one notes-query capability across the public HTTP API, reusable Python client, and CLI.

## Requirements checklist

- [ ] The API, client, and CLI support bounded pagination, deterministic sorting, and optional text filtering through one consistent query contract.
- [ ] Requests without query options preserve the API's bare-array response and the client's existing `list_notes()` result.
- [ ] Consumer implementations depend on a reviewed and stable API contract.
- [ ] An automated check exercises the real CLI, reusable client, and running notes service together over HTTP.

## Questions and decisions

- **Requirement question:** What query parameter names and pagination model should be public, and what defaults and maximum bounds apply?
- **Requirement question:** Which note fields are sortable and searchable, what are the text matching semantics, and what tie-breaker guarantees stable ordering?
- **Requirement question:** Should filtered/paginated requests retain the API's bare-array response or return pagination metadata?
- **Design decision:** Keep API, independently published client, and CLI as separate deliverables. Make the HTTP contract the prerequisite for both consumers; make the CLI integration check traverse the running service through the real client.

## Supporting details

- The collection endpoint is `GET /notes/` and currently returns every note as a JSON array.
- `NotesClient.list_notes()` currently sends an unparameterized request to `/notes/` and returns the decoded response.
- The CLI's `notes list` calls `list_notes()` and prints note IDs and titles.
- Existing service/client/CLI tests use a service test client, a stub transport, and a stub client respectively; none proves the complete production path.
- Package READMEs are the maintained user documentation locations. No notes-query specification currently exists in `docs/development/index.md`.

## Subtasks

- [ ] `tasks/20261102-notes-query/010-api-contract-and-service.md`
- [ ] `tasks/20261102-notes-query/020-reusable-client.md`
- [ ] `tasks/20261102-notes-query/030-cli-and-production-path.md`

## Implementation plan

Status: Draft

The service owns query semantics and the public HTTP contract. The reusable client exposes those same options without changing the no-argument behavior. The CLI presents the supported options and passes them through the client without reimplementing filtering, pagination, or sorting. The API contract, including parameter names, valid values, defaults, bounds, stable tie-breaking, and response shape, must be resolved and documented before consumer implementations begin.

Run work in dependency order: first settle and implement the service contract; then extend the client against that finalized contract; then add CLI options and verify the complete real path. The API milestone is the safe stop point if contract questions remain unresolved. The final integration check must start the service on a real HTTP endpoint and invoke the actual CLI with its production environment-based client configuration; mocked client or transport checks are supplementary, not substitutes.

The compatibility risk is changing the existing unparameterized response or client return shape. Keep that path explicitly covered and make new parameters opt-in. Contract mistakes have cross-consumer impact, so freeze the reviewed API before client or CLI work. If a compatibility regression appears, revert the relevant consumer/API change while retaining the prior bare-array/no-argument behavior; do not ship a consumer against a changed or unsettled contract.

### Implementation decisions and open questions

The three packages have distinct compatibility surfaces and remain separate subtasks. The service is first because both consumers depend on its public HTTP contract. The CLI owns the end-to-end check because it is the user-facing path that joins CLI parsing, the reusable client, HTTP, and the service. Resolve the requirement questions above before implementation; do not invent public defaults, accepted sort keys, matching rules, or response metadata in code.

### Documentation

Update the service's maintained public API documentation (the repository README or an appropriately owned service document) with the finalized contract. Update `packages/notes_client/README.md` and `apps/notes_cli/README.md` to describe their supported options and preserved no-option behavior. Keep documentation changes with their owning deliverables and make claims only after the behavior exists.

### Task checklist

- [ ] Complete the API contract and service behavior.
- [ ] Extend the reusable client after the API contract is stable.
- [ ] Extend the CLI and prove the complete production path.

### Requirement verification

The bounded pagination, deterministic sorting, and filtering requirement is verified by service route tests that exercise the public HTTP contract, client tests that verify exact option forwarding and result behavior against that contract, and CLI option tests. These component checks do not prove the end-to-end connection.

The unparameterized compatibility requirement is verified at the API route and client public method boundaries, asserting the bare array and unchanged list result with no options.

The stable-contract prerequisite is verified by the reviewed service contract documentation and consumer implementation/tests matching it; it is not established by test success alone.

The complete-path requirement is verified by one automated integration test that starts the actual notes service on a reachable HTTP address, invokes the actual `notes list` command with the environment URL configured, and observes filtered/paginated/sorted output from seeded service data. This check must use the production `NotesClient` HTTP implementation and must not replace the CLI, client, HTTP transport, or service route with mocks.

### Additional implementation verification

Run the focused service, client, and CLI test suites after their corresponding work, followed by the end-to-end check. Do not claim the integration requirement complete if its real-service test cannot run or does not collect successfully.