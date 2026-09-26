# Notes CLI query support and production path

Expose the shared notes-query capability through `notes list`, preserve the
existing no-option command, and prove the real CLI-to-client-to-service path.

Parent Task: `tasks/20260926-notes-query/000-main.md`

Depends On:

- `tasks/20260926-notes-query/010-public-api-contract-and-service.md`
- `tasks/20260926-notes-query/020-reusable-client.md`

## Requirements checklist

- [ ] Add CLI options for the reviewed pagination, sorting, and optional text
  filtering contract.
- [ ] Map CLI options to the reusable client without duplicating query
  semantics.
- [ ] Preserve the existing no-option `notes list` output and invocation
  behavior.
- [ ] Prove a parameterized query through the CLI, production
  `NotesClient.from_environment()`, live HTTP, the FastAPI service, and its
  storage boundary without injecting a fake client.
- [ ] Document the supported CLI options and output.

## Requirement questions and scope decisions

- The API and client tasks must settle the canonical option names before CLI
  flags are finalized.
- Confirm whether flags should mirror the client/API vocabulary exactly or use
  CLI-specific aliases.
- Confirm whether the existing one-line `id: title` output is sufficient for
  filtered and paginated results; it is the recommended compatibility output.
- The decisive integration check must use a running local service and the
  production client construction path, not only the current injected-client
  unit fixture.

## Research and supporting facts

- `apps/notes_cli/cli.py` currently has only a `list` subcommand and prints
  each result as `id: title`.
- `main(argv=None, client=None)` allows tests to inject a fake client, but the
  default path constructs `NotesClient.from_environment()`.
- The current CLI fixture implements only `list_notes()` with no arguments,
  so the no-option path must not require new arguments from legacy-like
  clients.
- `apps/notes_cli/README.md` currently documents only `notes list`.

## Execution plan

Status: Draft

After both upstream contract gates pass, add flags that map directly to the
agreed client arguments. When no query flags are present, invoke
`list_notes()` with no arguments and retain the existing output. When flags
are present, pass only the selected values to the client; the CLI should not
reimplement filtering, ordering, or pagination.

The decisive check will start a local notes service on an available port with
the real FastAPI application and database, configure `NOTES_API_URL`, and
invoke the CLI entry path without supplying `client`. It must seed notes that
make the selected page, stable order, and text filter observable, then assert
the printed output. This crosses the actual CLI, `NotesClient.from_environment`,
`httpx.Client`, HTTP service, query implementation, and storage. Keep the
existing injected-client tests as local rendering/regression coverage, but do
not count them as the production-path proof.

Update the CLI README only after the end-to-end check passes.

### Implementation decisions and open questions

- The CLI consumes the API/client contract and owns only argument parsing and
  presentation.
- The no-option branch should call the client with no arguments to preserve
  the current seam and output.
- The recommended output remains one `id: title` line per returned note.
- The exact flag spelling and live-server test harness remain subject to the
  upstream contract decision; the production-path boundary itself is fixed.

### Documentation

- Update `apps/notes_cli/README.md` with all supported flags, compatibility
  behavior, output, and one parameterized example.
- Document the live production-path verification command or test entry point
  for future maintainers.

### Task checklist

- [ ] Confirm both API and client dependencies are complete.
- [ ] Implement CLI flags and client mapping.
- [ ] Preserve and update injected-client unit coverage as needed.
- [ ] Add and pass the live service/client/CLI integration check with no
  injected client.
- [ ] Update the CLI README.
- [ ] Report the full-path evidence to the parent task.

### Requirement verification

- CLI interface: parser and rendering tests must verify each supported option
  is passed to the client and that the no-option command retains its output.
- Production connection: one integration test must invoke the CLI without a
  supplied client, use `NOTES_API_URL` with a running FastAPI service, and
  assert the response produced by a parameterized query. This is the decisive
  evidence for the CLI-to-client-to-service requirement.

### Additional implementation verification

- Run the CLI-focused tests plus the live integration test in an environment
  where the service process and package import paths match supported usage.
