# Add CLI query flags and prove the production client-to-service path

Expose the contract on `notes list` and prove it end to end through the
production path: real CLI invocation → real `notes_client` → real running
service. Mocked-client tests support but do not replace that check.

Parent Task: tasks/20260925-notes-query-capability/000-main.md
Depends On: tasks/20260925-notes-query-capability/020-api-query-parameters.md, tasks/20260925-notes-query-capability/030-client-query-parameters.md

## Requirements checklist

- [ ] `notes list` accepts `--limit`, `--offset`, `--sort {id,title}`,
  `--order {asc,desc}`, and `--text`, forwarding provided values (and only
  those) to `client.list_notes(...)`.
- [ ] Unparameterized `notes list` output and behavior are unchanged.
- [ ] One automated end-to-end test drives the production path with no
  injected or mocked client/transport: a real server hosts `app.main:app`
  (temporary working directory so its SQLite file is isolated), notes are
  seeded through real HTTP POSTs, and the CLI runs via
  `notes_cli.cli:main(["list", "--sort", "title", "--limit", "2"],
  client=None)` with `NOTES_API_URL` pointed at the server, so production
  `NotesClient.from_environment()` and the real httpx transport are
  exercised; the test asserts exact paged/ordered stdout, including a
  no-flags invocation asserting the unchanged full listing.
- [ ] A cheap component test maps flags → client arguments using the
  existing fake-client harness (non-decisive support only).
- [ ] `apps/notes_cli/README.md` documents the flags, and the app version
  is bumped to 0.2.0 (recommended step), in the same change.

## Supporting facts

- Current CLI: apps/notes_cli/cli.py:5 `list_command(client)` prints
  `f"{note['id']}: {note['title']}"`; apps/notes_cli/tests/conftest.py
  injects a fake client whose `list_notes()` returns a fixed list.
- The service's SQLite path is CWD-relative (src/app/db.py:4), so running
  the end-to-end server with a temporary working directory isolates its
  database from the repository.
- The root `pyproject.toml` lists plain `fastapi`; `uvicorn` may not be
  installed. The end-to-end harness needs it available (add as a test
  dependency if missing).
- The decisive check must traverse the real components together: per-side
  tests (fake-client CLI tests plus direct API tests) do not satisfy the
  production-path requirement on their own, and the check may not be
  waived for harness convenience.

## Execution plan

Status: Draft

- Extend the `list` subparser with the five flags; `main` forwards
  provided values to `list_command` → `client.list_notes`, preserving the
  printing format.
- End-to-end test: spawn uvicorn for `app.main:app` with a temporary
  working directory on an ephemeral port; wait for readiness; seed three
  notes (one title containing a space) via real POSTs; point
  `NOTES_API_URL` at the server; call `notes_cli.cli:main([...],
  client=None)` (production client construction) and assert exact stdout
  against the contract; include a no-flags invocation asserting the
  unchanged full listing.
- Component test with the existing fake client for flag→argument mapping,
  including that no flags produce no arguments.
- README and version bump.

### Implementation decisions and open questions

- End-to-end harness: in-process `main(argv)` against a spawned real
  server (recommended) versus invoking the installed `notes` console
  script as a subprocess. Both traverse the production client and service;
  the console-script form additionally covers packaging and is an
  acceptable substitute if the script is installed in the test
  environment.
No other local decisions.

### Documentation

`apps/notes_cli/README.md` (CLI users), same change as the code.

### Task checklist

- [ ] Add flags + forwarding to the CLI
- [ ] Production-path end-to-end test (real server, seeded data,
  exact-output assertions)
- [ ] Component flag-mapping test
- [ ] README + version bump

### Requirement verification

- Decisive: the automated end-to-end test above — it is the single named
  check that traverses CLI → real client → real service over real HTTP;
  its exact invocation is stated in the test. Fake-client CLI tests do
  not substitute for it.
- Regression: the existing CLI test passes, and the unparameterized
  `notes list` output is asserted unchanged.
- Run: the `apps/notes_cli` suite collects and exits cleanly.

### Additional implementation verification

- Run all three suites (service, client, CLI) once at the end of this
  subtask to confirm no cross-boundary drift after the full capability is
  assembled.