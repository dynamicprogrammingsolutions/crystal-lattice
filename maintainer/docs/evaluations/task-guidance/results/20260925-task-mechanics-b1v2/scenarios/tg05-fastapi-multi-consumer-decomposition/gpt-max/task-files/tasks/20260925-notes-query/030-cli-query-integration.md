# Expose and prove notes querying through the CLI

Add query controls to `notes list`, preserve its existing output, and prove
the production CLI-to-client-to-FastAPI path with real components.

Parent Task: tasks/20260925-notes-query/000-main.md

Depends On:

- tasks/20260925-notes-query/010-public-api-contract.md
- tasks/20260925-notes-query/020-reusable-client-query.md

## Requirements checklist

- [ ] Add CLI options that map one-to-one to the approved shared query
  contract, including bounded pagination, stable sorting, and optional text
  filtering.
- [ ] Keep `notes list` with no options equivalent to the current command:
  it retrieves the unparameterized collection and prints each note's ID and
  title.
- [ ] Keep all service communication in `NotesClient`; the CLI must not
  implement a second HTTP client or query algorithm.
- [ ] Ensure the installed CLI declares and can resolve its reusable
  `notes-client` dependency.
- [ ] The supported CLI distribution can resolve the reusable `notes-client`
  package and use it for the query path.

## Unresolved requirement questions

The exact flag names, response handling, and invalid-value behavior follow
the approved contract and client method from subtasks 010 and 020. Do not
make the CLI's defaults or output shape a separate design.

## Supporting facts

- `apps/notes_cli/cli.py` currently registers only a `list` subcommand and
  calls `client.list_notes()` with no arguments.
- `list_command` currently prints `"{id}: {title}"` for each returned note.
- Unit tests currently inject a fake object with only `list_notes()`, so they
  do not exercise `NotesClient` or the service.
- `apps/notes_cli/pyproject.toml` defines the `notes` entry point but does not
  currently declare a `notes-client` runtime dependency.

## Execution plan

Status: Draft

### Design and boundaries

Extend the `list` parser with the approved query controls and pass them to
`NotesClient.list_notes`. When no option is supplied, call the zero-argument
client method so the compatibility path remains observable. Keep rendering
the existing ID/title lines; pagination changes which notes are returned, not
the line format.

Use `argparse` for local syntax/type/range checks that are explicitly part of
the shared contract. The CLI must not clamp values, sort returned notes in
Python, or issue requests directly. Add the reusable client as a declared
runtime dependency and verify the installed console entry point.

### Dependencies and sequencing

Start only after subtasks 010 and 020 have fixed the HTTP and Python
contracts. Focused CLI tests may use a small fake client for rendering and
argument forwarding, but completion requires the real production-path check
below.

### Risks and mitigations

- Passing `None` values as query parameters could turn the old no-option
  command into a different request; omit all optional arguments when unused.
- A fake client test can hide a broken package dependency or wrong URL; make
  the real-service check mandatory.
- An output envelope could accidentally print metadata or reprs instead of
  notes; keep rendering tied to the approved client return type.
- Local CLI validation and service validation could disagree; derive both
  from the same bounds and error contract.

### Implementation decisions and open questions

The public flag names and error behavior are intentionally not final in this
Draft. The production-path check should use the approved names; under the
parent's provisional recommendation, its shape would be:

```text
NOTES_API_URL=http://127.0.0.1:8765 notes list --limit 2 --offset 0 --sort-by title --sort-order asc --query alpha
```

The service must be running on that disposable local port, and the command
must use the installed `notes` entry point with no injected fake client. If
the test environment lacks an ASGI server, add only the smallest
test/development support needed to start the real FastAPI app, or record the
equivalent exact manual command as the required acceptance evidence.

### Documentation

Update `apps/notes_cli/README.md` with the supported `notes list` options,
the unchanged no-option example, and one query example that matches the
approved contract. Document that results come through `notes-client` and the
configured `NOTES_API_URL`.

### Task checklist

- [ ] Consume the approved API and client contracts.
- [ ] Add CLI parsing and forwarding while preserving no-option behavior.
- [ ] Add or repair the declared `notes-client` package dependency.
- [ ] Add focused argument and rendering tests.
- [ ] Run the real CLI-to-service acceptance check using a disposable local
  service and the installed production entry point.
- [ ] Update the CLI README and report the decisive evidence to the parent.

### Requirement verification

- Focused CLI tests assert approved arguments reach `NotesClient` and that
  no-option invocation calls the zero-argument method and preserves the
  existing output lines.
- The decisive check starts the actual FastAPI app on a disposable local
  port, seeds notes through the service's public interface, sets
  `NOTES_API_URL`, and invokes the installed command in this form:

  ```text
  NOTES_API_URL=http://127.0.0.1:8765 notes list --limit 2 --offset 0 --sort-by title --sort-order asc --query alpha
  ```

  It must run `NotesClient.from_environment()` through the CLI, cross the
  real HTTP transport, reach the real `GET /notes/` route, and assert the
  filtered/sorted/bounded output. A fake client, mocked transport, or direct
  route call cannot replace this check.
- Run the same installed command without options and verify the current
  all-note ID/title output remains intact.

### Additional implementation verification

- Verify the console script resolves `notes-client` in a clean package
  installation or equivalent isolated environment.
- Exercise an invalid CLI bound and confirm the documented local failure
  path, then exercise a service-side validation response if the contract
  intentionally leaves any validation to the API.
- Cleanly stop the local service and remove disposable database state after
  the integration check.