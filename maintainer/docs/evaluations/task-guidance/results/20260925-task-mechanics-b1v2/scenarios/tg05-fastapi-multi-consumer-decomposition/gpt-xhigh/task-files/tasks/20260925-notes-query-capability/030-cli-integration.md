# Expose notes querying in the CLI and prove the production path

Add the approved query controls to `notes list`, preserve the current
no-option invocation, and provide the decisive integration evidence that the
CLI reaches the FastAPI service through the reusable production client.

## Requirements checklist

- [ ] `notes list` exposes user-facing controls corresponding to the approved
  pagination, sorting, and text-filter contract.
- [ ] `notes list` without those controls preserves the current usable output
  behavior.
- [ ] CLI tests cover argument translation and rendered results.
- [ ] A real integration test crosses `main` → `NotesClient` → HTTP transport
  → FastAPI route → database and verifies query behavior; it does not use a
  fake client as the decisive connection check.
- [ ] CLI documentation describes the supported options and examples.

Parent Task: tasks/20260925-notes-query-capability/000-main.md

Depends On:

- tasks/20260925-notes-query-capability/010-api-contract-service.md
- tasks/20260925-notes-query-capability/020-python-client.md

## Research and supporting facts

- `apps/notes_cli/cli.py` currently registers only the `list` subcommand and
  calls `client.list_notes()` without arguments.
- `list_command` prints each note as `<id>: <title>`.
- `apps/notes_cli/tests/test_cli.py` injects a fake client, so its current
  passing test does not cross the reusable client or service boundary.
- The CLI README currently documents only `notes list`.

## Execution plan

Status: Draft

After the HTTP and client contracts are approved, add CLI flags that map
one-to-one to the client capability and retain the existing output format
unless the approved response shape requires a documented extension. Keep
focused parser/formatting tests for local behavior, then add a decisive
integration test that seeds notes through the public FastAPI app, constructs a
real `NotesClient` around the app's actual HTTP test transport, invokes the
CLI entry point with query arguments, and asserts the filtered, bounded,
stably ordered output.

### Implementation decisions and open questions

Flag names, defaults, and whether output displays pagination metadata are
dependent on the approved service/client contract. The injected-client
argument already exists as a test seam, but the decisive test must inject a
real `NotesClient`, not a fake object implementing `list_notes()`.

### Documentation

Update `apps/notes_cli/README.md` with the supported flags, no-option
compatibility, and at least one query example. Keep output claims aligned
with the actual integration test.

### Task checklist

- [ ] Confirm the approved service and client contracts.
- [ ] Add CLI options and translate them to the reusable client call.
- [ ] Preserve and test the no-option list output.
- [ ] Add the real CLI-to-service integration test with public-path seeding.
- [ ] Update the CLI README.
- [ ] Update the parent task with the decisive end-to-end evidence.

### Requirement verification

- CLI behavior: parser and rendering tests verify approved flags and output
  formatting with a focused test double where that is sufficient.
- Production connection: an integration test invokes `main` with the approved
  CLI arguments and a real `NotesClient` backed by FastAPI's actual HTTP test
  transport. It creates notes through `POST /notes/`, then asserts the
  `GET /notes/` query result as rendered by the CLI. This single check is the
  named decisive evidence for the complete consumer-to-service connection.
- Compatibility: an invocation with only `list` asserts the existing
  `<id>: <title>` style remains usable.

### Additional implementation verification

- Verify CLI validation and service validation do not diverge in ways that
  produce confusing errors.
- Verify the integration fixture uses the app/database lifespan and does not
  replace the HTTP route or client with a test-only shortcut.