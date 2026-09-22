# Expose notes queries through the CLI and prove the production path

Parent Task: `tasks/20260919-notes-query-capability/000-main.md`

Depends On:
`tasks/20260919-notes-query-capability/010-public-contract.md`,
`tasks/20260919-notes-query-capability/020-api-query.md`,
`tasks/20260919-notes-query-capability/030-client-query.md`

Expose the approved notes-query controls in `notes list` and verify that the
CLI reaches the real reusable client and notes service. Preserve the current
no-flag command behavior and output expectations.

## Requirements checklist

- [ ] `notes list` exposes the approved pagination, sorting, and text-filter
  controls with the contract's public names and defaults.
- [ ] The CLI passes supplied controls to the production `NotesClient` rather
  than implementing query behavior or filtering locally.
- [ ] `notes list` without query flags remains valid and preserves the current
  list output behavior.
- [ ] An integration test invokes the CLI through the production client
  against the notes service and verifies query results end to end.
- [ ] The CLI package can declare and resolve its runtime client dependency in
  the supported installation path.

## Unresolved requirement questions

CLI flag names, output for parameterized responses, and invalid-input handling
remain blocked on the public contract in
`tasks/20260919-notes-query-capability/010-public-contract.md`.

## Research and supporting facts

- `apps/notes_cli/cli.py` currently has one `list` subcommand, injects or
  constructs `NotesClient`, and prints each returned note's id and title.
- The current CLI test injects a fake object with `list_notes()` and therefore
  does not prove the client-to-service path.
- `apps/notes_cli/pyproject.toml` declares the CLI entry point but no explicit
  dependency on `notes-client`.
- The current CLI README only documents `notes list`.

## Execution plan

Status: Draft

After the contract and client surface are approved, add the corresponding
query flags to the `list` subcommand and pass them unchanged through
`NotesClient`. Keep formatting concerns separate from query semantics. Retain a
narrow fake-client test for output formatting if useful, but add a stronger
integration test that invokes the CLI with a real `NotesClient` configured
against the real FastAPI service boundary. Use the repository's supported
service harness; if no live HTTP harness exists, a service-backed test client
may provide the ASGI boundary while still forbidding a fake client in this
acceptance path.

### Implementation decisions and open questions

- The CLI should expose the same capability, not a second set of local
  semantics or post-fetch filtering.
- No query flags must preserve the existing call and output path.
- The end-to-end test must construct/use `NotesClient`, create or seed notes
  through the service boundary, invoke the CLI operation, and assert the
  filtered, sorted, bounded result. It must not substitute the current fake
  `Client` fixture for this check.
- The final choice between an in-process ASGI service harness and a spawned
  local HTTP service should be made based on the repository's supported test
  tooling; either must cross the real client and service code paths.

### Documentation

- Update `apps/notes_cli/README.md` with the approved flags, examples,
  output behavior, and a note that the CLI delegates to `notes_client`.
- Update CLI packaging metadata if required to make the client dependency
  explicit and installable.
- Link the CLI guidance to the shared notes-query contract after the feature is
  implemented and verified.

### Task checklist

- [ ] Add the approved query flags and defaults to `notes list`.
- [ ] Pass flags through the production `NotesClient` surface.
- [ ] Preserve no-flag output and retain any narrow formatter unit test.
- [ ] Add an end-to-end CLI test using the real client and service.
- [ ] Verify/install the CLI with its client dependency.
- [ ] Update CLI documentation after the production path passes.

### Requirement verification

- [ ] CLI argument tests prove the approved pagination, sorting, and filter
  controls are passed to the client exactly as specified.
- [ ] A no-flag CLI test proves current output remains available.
- [ ] A service-backed end-to-end test invokes the CLI and real
  `NotesClient`, reaches the FastAPI service, and proves the resulting output
  reflects server-side filtering, stable sorting, and bounded pagination.
- [ ] An install/import check proves the supported CLI package can find the
  reusable client at runtime.

### Additional implementation verification

- [ ] Verify CLI errors for invalid query values match the approved user-facing
  behavior and do not hide service validation failures.
- [ ] Verify output remains deterministic and readable when a page is empty or
  contains tied sort values.