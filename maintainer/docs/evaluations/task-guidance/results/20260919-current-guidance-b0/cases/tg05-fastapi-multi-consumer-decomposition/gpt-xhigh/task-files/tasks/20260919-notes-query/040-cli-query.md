# Expose notes querying in the CLI

Parent Task: tasks/20260919-notes-query/000-main.md

Depends On: tasks/20260919-notes-query/010-query-contract.md, tasks/20260919-notes-query/030-client-query.md

Add the approved query controls to `notes list` and prove that the CLI uses the production reusable client against the notes service.

## Requirements checklist

- [ ] `notes list` accepts the contract-approved pagination, sorting, and text-filter controls with clear help text.
- [ ] The CLI maps those controls through the production `NotesClient` API rather than reimplementing HTTP requests.
- [ ] `notes list` with no options preserves the current output behavior and continues to list the unparameterized collection.
- [ ] CLI validation and service errors are surfaced according to the approved user-facing behavior.
- [ ] An integration test invokes the CLI with the production client path against a real notes service instance; a fake client is not the only evidence.
- [ ] CLI documentation describes the supported options and compatibility behavior.

## Unresolved requirement questions and material decisions

This subtask inherits the exact option names, supported subset, output expectations, and error behavior from `tasks/20260919-notes-query/010-query-contract.md`. It must not invent CLI-only query semantics.

## Research and supporting facts

- `apps/notes_cli/cli.py` currently registers only a `list` subcommand and calls `list_command(selected)`.
- `list_command()` currently prints each note as `id: title`.
- `main()` supports an injected client, which is useful for focused formatting tests but does not prove the production client-to-service path.
- `apps/notes_cli/tests/test_cli.py` currently tests only that a fake-client list command prints output.
- `apps/notes_cli/README.md` currently documents only `notes list`.

## Execution plan

Status: Draft

Add the contract-approved options to the `list` parser, convert parsed values to the reusable client call, and retain the existing line-oriented output unless the approved contract requires a documented change. Keep parser/formatting tests with a small fake client for local concerns, but add a separate integration test that does not inject a fake client: start or connect to an ephemeral real notes service, configure `NOTES_API_URL`, invoke `main(["list", ...])`, and let `NotesClient.from_environment()` perform the HTTP request.

The integration harness must cross the actual service route and database-backed query behavior. If the repository needs a test-only server runner, record the dependency and lifecycle in the verification plan; do not replace the HTTP boundary with a method stub that can pass while query serialization or endpoint behavior is broken.

### Implementation decisions and open questions

The contract subtask owns which options are exposed and what output/error behavior means. A local choice remains whether the CLI parses all constraints itself or lets the client/service validate them; it must follow the approved error contract and avoid silently changing values.

The production-path test should use environment configuration and the normal `NotesClient.from_environment()` construction. Client injection remains allowed for focused unit tests but cannot be the sole CLI evidence.

### Documentation

Update `apps/notes_cli/README.md` with the supported command options and examples, including the unchanged no-option invocation. Ensure help text, README examples, and the public contract use the same names and defaults.

### Task checklist

- [ ] Add approved query options to `notes list`.
- [ ] Forward parsed values through `NotesClient`.
- [ ] Preserve and test no-option output.
- [ ] Add a live service integration for the production client-to-service path.
- [ ] Update CLI help and README documentation.

### Requirement verification

| Requirement | Planned evidence |
| --- | --- |
| CLI controls | Parser/help tests for every approved option and boundary |
| Client reuse | Code/test path shows CLI invokes `NotesClient.list_notes()` rather than a direct HTTP implementation |
| No-option compatibility | Existing output assertion plus an integration invocation without options |
| Error behavior | Tests for parser-level and service-level invalid input according to the contract |
| Production path | CLI run with no injected client, environment-configured `NotesClient`, and a real service endpoint |

### Additional implementation verification

- Run the CLI from its package boundary so the installed entry point/import layout is covered where practical.
- Confirm output ordering is the service/client result order and that the CLI does not resort or filter locally.
