# Expose notes-query through the CLI

Add supported notes-query controls to `notes list` and prove the production
CLI-to-client-to-service path.

Parent Task: tasks/20260919-notes-query/000-main.md
Depends On: tasks/20260919-notes-query/010-contract-and-specification.md
Depends On: tasks/20260919-notes-query/030-client-query.md

## Requirements checklist

- [ ] Add CLI options for the approved pagination, sorting, and filtering
      controls.
- [ ] Map CLI values to the production `NotesClient` interface.
- [ ] Preserve the current unparameterized `notes list` behavior and output.
- [ ] Define and test user-visible handling for invalid query values and empty
      results.
- [ ] Add an integration test invoking the CLI with the production client
      against a real HTTP notes service.

## Supporting facts

`apps/notes_cli/cli.py` currently creates `NotesClient.from_environment()` for
the command path and allows an injected client for unit tests. The existing
CLI test uses a fake client and therefore does not prove the production
transport or service route.

## Execution plan

Status: Draft

1. Add parser options and help text using the names and validation defined by
   the approved contract.
2. Pass parsed values through the production `NotesClient` interface while
   retaining the existing injectable seam for focused rendering tests.
3. Preserve output for an unparameterized `notes list` invocation.
4. Start or attach to a real HTTP service instance in an integration fixture,
   configure the production client path, invoke the CLI, and assert the
   service-backed filtered/paginated/sorted output.
5. Update the CLI README with verified command examples and option behavior.

### Implementation decisions and open questions

- Decision: fake-client tests remain useful for rendering/parser isolation,
  but they are not the acceptance evidence for the production path.
- Decision: acceptance must exercise `NotesClient.from_environment()` or an
  equivalent production construction path and actual HTTP transport.
- Open: exact option names, output metadata, and invalid-input behavior depend
  on the approved contract.

### Documentation

Update `apps/notes_cli/README.md` with the supported `notes list` options,
examples, compatibility behavior, and any documented error/empty-result
output. Do not claim service-backed behavior until the integration test passes.

### Task checklist

- [ ] Implement approved CLI options and mapping.
- [ ] Preserve and test unparameterized output.
- [ ] Add the real HTTP service integration test.
- [ ] Update and review the CLI README.

### Requirement verification

- CLI options are proven through parser/command tests.
- Unparameterized output is proven against the existing command behavior.
- The production path is proven by invoking the CLI with the real
  `NotesClient` and observing results from an actual running HTTP service,
  including at least one query using pagination, sorting, and filtering.

### Additional implementation verification

- Verify the integration fixture does not replace the production client with a
  fake transport or call application internals directly.
- Verify service startup/shutdown and environment configuration are exercised
  as a real consumer would use them.