# Notes Query CLI and Production Path

Expose the approved notes-query options in the CLI and verify the real CLI-to-service path.

Parent Task: `tasks/20261102-notes-query/000-main.md`
Depends On: `tasks/20261102-notes-query/020-reusable-client.md`

## Requirements checklist

- [ ] The `notes list` command exposes the finalized pagination, sorting, and text-filtering options and passes them through the reusable client.
- [ ] Running `notes list` without options preserves the existing all-notes output behavior.
- [ ] An automated integration test proves query behavior through the actual CLI, reusable client, HTTP transport, and running notes service.
- [ ] CLI documentation describes the supported options and preserved default behavior.

## Questions and decisions

- **Design decision:** CLI option names and accepted values mirror the finalized client/API contract rather than introducing CLI-only query semantics.

## Supporting details

- `apps/notes_cli/cli.py` currently has a `list` subcommand and delegates to `NotesClient.list_notes()`.
- Existing CLI tests inject a stub client and do not traverse the reusable client or service.
- The production client constructs an `httpx.Client` using `NOTES_API_URL`, defaulting to `http://127.0.0.1:8000`.

## Implementation plan

Status: Draft

After the reusable client exposes the finalized contract, add corresponding options to `notes list` and pass values directly to the client. Preserve the no-option command. Update the CLI README and test parsing/output behavior.

The client prerequisite blocks this task because CLI delegation must target the final reusable method surface. The decisive check is an integration test that starts the actual service on a reachable HTTP endpoint, configures `NOTES_API_URL`, and invokes the actual CLI command against seeded data. It must use the real client and network HTTP path, not a stub client or mocked transport. Focused CLI tests can validate parsing and option pass-through but cannot replace this path check.

The risk is a CLI surface that appears to work under its stub yet does not match the client or HTTP contract. The real-path test guards the connection end to end. If the integration path fails, retain the existing no-option command and revert only the new CLI option surface until it can be aligned with the approved client/API contract.

### Implementation decisions and open questions

CLI options mirror the stable public query contract. The integration test must use the same executable/entry point and environment-configured production client used by users; test shortcuts that skip an important connection are not acceptable.

### Documentation

Update `apps/notes_cli/README.md` with the approved `notes list` options, valid values/bounds, behavior, and the no-option behavior.

### Task checklist

- [ ] Add CLI options after client support is complete.
- [ ] Test parsing, pass-through, and no-option behavior.
- [ ] Verify the actual CLI-to-service path over HTTP.
- [ ] Document supported `notes list` options.

### Requirement verification

CLI component tests verify option parsing and pass-through to the real client interface and preserve the no-option output path. They do not verify HTTP or service execution.

The integration test starts the notes service on a reachable HTTP address, seeds notes that distinguish the approved sort/filter/page behavior, configures `NOTES_API_URL`, and invokes the actual `notes list` command. It asserts the resulting CLI output reflects the service query. The test must use the production `NotesClient` and HTTP transport and traverse the service route; mocks of the CLI, client, transport, or route are not decisive.

Documentation is verified against the approved CLI contract and executable behavior.

### Additional implementation verification

Run the focused CLI tests and the real-service integration test; report the latter as blocked rather than successful if its service or process setup cannot execute.