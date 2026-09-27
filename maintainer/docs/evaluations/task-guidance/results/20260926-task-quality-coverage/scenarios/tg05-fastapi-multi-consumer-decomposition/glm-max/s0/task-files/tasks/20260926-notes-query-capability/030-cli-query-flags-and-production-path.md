# CLI: query flags and the production client-to-service path

Expose the query capability on `notes list` and prove — through the real
production path — that the CLI, the client, and the running service work
together: a real server, the real `NotesClient`, the real `main()`.

Parent Task: tasks/20260926-notes-query-capability/000-main.md
Depends On: tasks/20260926-notes-query-capability/010-api-collection-query.md
and tasks/20260926-notes-query-capability/020-client-query-parameters.md

## Requirements checklist

- [ ] `notes list` supports `--limit`, `--offset`, `--sort`, and `--filter`
      (parent decision D6), forwarding provided values to the client's
      parameters.
- [ ] The no-flag `notes list` invocation and its `{id}: {title}` output
      format are unchanged.
- [ ] A CLI unit test proves the flags map to client arguments and the output
      format is unchanged.
- [ ] The named decisive end-to-end check runs the production path: a real
      uvicorn server serving the real app, notes seeded through the public
      POST route, the real `NotesClient` via `NOTES_API_URL`, and a real
      `main([...])` invocation with no injected test double — asserting a
      parameterized query's stdout and the unparameterized full listing
      through the same path.
- [ ] `apps/notes_cli/README.md` documents the flags and the
      `notes-client` dependency (parent decision D9) in the same change.

## Execution plan

Status: Draft

Approach:
- `apps/notes_cli/cli.py`: add options to the `list` subparser
  (`--limit` int, `--offset` int, `--sort` str, `--filter` str, all defaulting
  to unset) and pass only provided values to `client.list_notes(...)`; keep
  the print loop and line format unchanged.
- Named decisive check (new test in `apps/notes_cli/tests/`):
  - start `uvicorn.Server` serving `app.main.app` on an ephemeral
    `127.0.0.1` port in a daemon thread and wait for startup (`uvicorn` is
    added as a test dependency of the CLI app — parent decision D7);
  - seed notes through the public HTTP POST route so the check uses only
    public behavior;
  - set `NOTES_API_URL` to the server address, build
    `NotesClient.from_environment()`, and call
    `main(["list", "--sort", "title", "--limit", "2", "--filter", ...])` with
    no injected client; assert the exact stdout lines (order, filtering,
    pagination);
  - run the unparameterized `main(["list"])` against the same server and
    assert the full seeded listing — compatibility verified through the
    production path as well.
  - This test traverses the real CLI parser → real client → real httpx →
    real TCP → real FastAPI app → SQLite. The per-side tests (020's
    captured-transport test, 010's route tests) remain supporting evidence
    only and do not substitute for this check.
- CLI unit test (existing pattern with a fake client): flags forwarded as the
  expected client keyword arguments; unchanged formatting.

Environment: execution must first establish a test environment — no
virtualenv or declared test dependencies exist yet, and the end-to-end test
needs `app` (from `src/`), `notes_client`, and `notes_cli` importable
alongside `uvicorn` and `pytest`. Run from an isolated working directory:
the service writes `./notes.db` relative to the working directory.

### Implementation decisions and open questions

- D6 (flag names), D7 (real uvicorn server), and D9 (dependency recording)
  are approved at the parent level. Local choices resolved here: ephemeral
  port with a daemon-thread server; seeding via the public POST route;
  the decisive check uses the `from_environment()` construction path.
- Open questions: none.

### Documentation

- `apps/notes_cli/README.md`: document the new flags and the dependency on
  `notes-client` (D9); end-user audience.

### Task checklist

- [ ] Add query flags to the `list` subparser
- [ ] Add CLI unit test for flag forwarding and output regression
- [ ] Add the named production-path end-to-end check (real server, real client, real CLI)
- [ ] Update `apps/notes_cli/README.md`
- [ ] Run the CLI suite and record the decisive check's run

### Requirement verification

- Parent R4 → CLI unit test (flags → client arguments; unchanged line format)
  plus the end-to-end check.
- Parent R6 → the named decisive check described above; count it successful
  only when the intended tests collect and exit cleanly with the real server
  running.
- Parent R2/R3 production-path cross-check → the unparameterized
  `main(["list"])` assertion through the same real server and client path.
- Parent R7 (CLI part) → README diff in the same change.