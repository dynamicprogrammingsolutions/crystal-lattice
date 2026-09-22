# Add CLI query options and prove the production client-to-service path

Extend the `notes` CLI so users can exercise the approved query capability,
preserving the default `notes list` behavior exactly, and add the end-to-end
test that proves the production path — real CLI code, real
`notes_client.NotesClient`, live notes service over HTTP — with no stubs on
that path. CLI README updated in the same change.

Parent Task: `tasks/20260919-notes-query-capability/000-main.md`

Depends On:
- `tasks/20260919-notes-query-capability/010-query-contract.md` (flag names
  and semantics mirror the approved contract),
- `tasks/20260919-notes-query-capability/020-api-query-capability.md` (the
  live service must exist for the end-to-end proof),
- `tasks/20260919-notes-query-capability/030-client-query-capability.md` (the
  CLI calls the real client method).

## Requirements checklist

- [ ] P1: The CLI exposes the query capability with optional flags mapping to
      the client capability per the approved contract; default invocation
      (no flags) preserves current output behavior exactly.
- [ ] P2: CLI-level unit tests cover flag→parameter mapping and the unchanged
      default behavior, using the existing stubbed-client harness (extended,
      still the cheap layer).
- [ ] P3: An end-to-end test proves the production client-to-service path:
      the real CLI entry point (`main`), the real `NotesClient` (no test
      stubs), and a live notes service reached over HTTP, exercising
      pagination, sorting, and filtering (R8).
- [ ] P4: `apps/notes_cli/README.md` describes the capability as current
      supported behavior, updated in the same reviewed change as the code.

## Supporting facts

- CLI today (`apps/notes_cli/cli.py`): argparse with a required `list`
  subcommand; `list_command(client)` prints `id: title` per note from
  `client.list_notes()`. `main(argv, client)` allows test injection.
- Current CLI tests stub the client entirely (`apps/notes_cli/tests/conftest.py`);
  the end-to-end proof is therefore new test infrastructure, owned by the CLI
  application because it proves the CLI's user path (top of the consumer
  stack).
- Environment: single workspace Python environment; the server is importable
  the same way `src/tests` imports `app.main`. The e2e test may import
  `app.main` for the server process without making the CLI depend on the
  server at runtime — the dependency edge exists only in tests.
- Server options for the e2e proof (decision below):
  - A real `uvicorn` server subprocess on an ephemeral loopback port — proves
    the full production path including sockets; `uvicorn` is not currently a
    dependency, so this adds one (test-scope).
  - `httpx.ASGITransport(app=app)` under the real `httpx.Client` inside
    `NotesClient` — crosses the real client and the real FastAPI app but
    bypasses the network stack.
- Shared-state risk: the server writes `./notes.db` (cwd-relative). Running
  the server with a temporary working directory gives the e2e test an
  isolated database without product changes.
- The requirement "the CLI must prove the production client-to-service path"
  makes this an important path that lower layers cannot represent faithfully —
  exactly the case the fixture's testing guidance reserves for end-to-end
  tests. One test, real components, no test-only shortcuts in product code.

## Execution plan

Status: Draft

1. Extend the CLI surface (open questions below): flags `--limit`, `--offset`,
   `--sort`, `--q` (names per the approved contract) on the chosen command;
   when no flags are given, the client is called with no query arguments at
   all, preserving current behavior (P1) — the CLI must not invent defaults.
2. Extend the stubbed-client unit harness to record calls and assert:
   each flag forwarded as the contracted parameter, combined flags, and the
   default invocation calling the client with no arguments (P2). Rendering of
   existing output (`id: title`) is covered by the existing test, kept
   unmodified.
3. Add the end-to-end test in `apps/notes_cli/tests/`:
   - Start the real service (chosen server option) with an isolated temporary
     working directory and an ephemeral port.
   - Seed notes through the public API (`POST /notes/`) — realistic public
     path, no direct DB writes.
   - Build the real client via `NotesClient.from_environment()` with
     `NOTES_API_URL` pointed at the running server (the production
     configuration mechanism, exercised as in production).
   - Invoke `main([...])` with query flags; assert the printed lines match
     the expected paginated/sorted/filtered window seeded above.
   - Terminate the server and clean up (no leaked process, socket, or files).
4. Update `apps/notes_cli/README.md` (P4) in the same change.
5. Run the CLI suite; then the full three-suite pass for the parent task.

### Implementation decisions and open questions

- Server option for the e2e proof (material to what the evidence proves;
  needs approval with this plan): real `uvicorn` subprocess (recommendation —
  proves the production path including the network hop; accepts `uvicorn` as
  a test dependency) vs `httpx.ASGITransport` (no new dependency, weaker
  evidence — bypasses sockets). If approved as ASGITransport, the README/task
  record must describe the evidence by the boundary actually crossed.
- CLI surface (material, user-visible; needs approval): extend `notes list`
  with optional flags (recommendation — one verb for the collection operation,
  default unchanged) vs a new `notes query` subcommand.
- Flag names: follow the approved contract's parameter names (e.g. `--q` vs
  `--filter`) — confirm at approval; local choice thereafter.

### Documentation

- `apps/notes_cli/README.md` (audience: CLI users): document the optional
  flags and the unchanged default behavior. Same change as the code.

### Task checklist

- [ ] CLI flags implemented; default invocation unchanged (no arguments sent
      by default)
- [ ] Unit tests for flag mapping + default behavior (P2)
- [ ] End-to-end production-path test added and passing (P3)
- [ ] `apps/notes_cli/README.md` updated in the same change
- [ ] CLI suite passes; full three-suite pass recorded for the parent task

### Requirement verification

- P1: unit tests at the CLI boundary (arg parsing → client call), plus the
  end-to-end assertions; the existing unmodified `test_list_command` supports
  default rendering.
- P2: those unit tests (stubbed client is appropriate at this layer; the
  stub proves the CLI's own logic only).
- P3: the end-to-end test is the decisive evidence for R8 — real CLI code,
  real `NotesClient` with its production `from_environment()` configuration,
  real HTTP, real FastAPI app, real SQLite. No stubs on that path. Stub-based
  tests and 020/030's boundary tests are supporting evidence only.
- P4: the README diff reviewed with the code change.

### Additional implementation verification

- Full regression run across `src/tests`, `packages/notes_client/tests`, and
  `apps/notes_cli/tests`; all existing tests pass unmodified.
- Confirm the e2e server runs isolated (temp working directory, ephemeral
  port) and leaves no `notes.db`, socket, or process behind; confirm no
  test-only shortcut was added to product code (`cli.py`, `client.py`, app
  code untouched by test concerns).