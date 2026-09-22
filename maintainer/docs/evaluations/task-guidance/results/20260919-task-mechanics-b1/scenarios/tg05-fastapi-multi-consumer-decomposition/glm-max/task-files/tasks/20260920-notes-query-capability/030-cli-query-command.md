# CLI: notes list query flags and production-path evidence

Add the notes-query capability to the `notes` CLI as optional flags on
`notes list`, preserving the current no-flag behavior and output format, and
prove the capability over the production client-to-service path — a real CLI
invocation using the production default `NotesClient.from_environment()`
against a real running service.

Parent Task: tasks/20260920-notes-query-capability/000-main.md

Depends On: tasks/20260920-notes-query-capability/010-service-query-api.md
(the service contract), tasks/20260920-notes-query-capability/020-client-query-support.md
(the production client surface this CLI must call).

## Requirements checklist

- [ ] `notes list` accepts optional flags mirroring the frozen contract:
      `--limit`, `--offset`, `--sort`, `--order`, `--q`.
- [ ] Running `notes list` with no flags behaves exactly as today: same
      command, no query parameters sent, `f"{id}: {title}"` output per note.
- [ ] Flag values are forwarded to the real client unchanged; the CLI adds no
      client-side validation or defaults beyond argparse type conversion
      matching the contract (`--limit`/`--offset` integers, `--sort` choice,
      `--order` choice, `--q` free text).
- [ ] `apps/notes_cli/README.md` documents the flags for CLI users.
- [ ] Decisive evidence crosses the production path: real service running,
      CLI invoked as users invoke it (installed console script or `main()` with
      no injected client), default `NotesClient.from_environment()` client,
      real HTTP — asserting rendered output reflects pagination, sorting, and
      filtering. No fake client or transport anywhere on this path.
- [ ] Package version bumped to `0.2.0` (parent decision 9).

## Supporting details

Facts from inspection:

- `apps/notes_cli/cli.py:5` — `list_command(client)` iterates
  `client.list_notes()` and prints `f"{note['id']}: {note['title']}"`.
- `apps/notes_cli/cli.py:15` — `main(argv=None, client=None)` defaults to
  `NotesClient.from_environment()`; the `client` parameter exists for
  injection. The production path is the default branch.
- Console script `notes` is declared in `apps/notes_cli/pyproject.toml`
  (`notes = "notes_cli.cli:main"`); version `0.1.0`.
- `apps/notes_cli/tests/test_cli.py` injects a fake client — fine for output
  formatting unit evidence, but nothing today proves the CLI↔client↔service
  chain. The production-path test in this subtask closes that gap and is the
  real consumer that validates the client integration harness from `020`.
- Contract reference: `docs/notes-query.md` (from `010`); client parameters
  per `020`.
- Output rendering (`f"{id}: {title}"`) is a local rendering concern — unit
  tests with an injected client remain the cheapest valid evidence for it.

## Execution plan

Status: Draft

Extend the existing `list` subparser with the five optional flags, mapping
directly onto `list_notes()` keyword arguments (unchanged flag names →
parameter names). Keep `list_command` and its output format unchanged; the
flags only change what is requested, not how results render. Add parser→client
mapping unit tests (stubbed client, injected — acceptable at this internal
interface) and the production-path test: start the real service on an
ephemeral port, seed data via its public POST route, set `NOTES_API_URL`, and
invoke the CLI as production does; assert stdout lines match the expected
paginated/sorted/filtered notes and that a no-flag invocation matches the
current behavior. Update the CLI README and bump the version.

### Implementation decisions and open questions

- Flags on the existing `notes list` command rather than a new `notes query`
  subcommand (resolved per parent decision 1/6 — one capability, one command;
  a second subcommand would fork the concept for CLI users).
- `--q` naming mirrors the HTTP/client parameter exactly (parent decision 6);
  a friendlier alias like `--filter` would create a second name for one
  contract parameter.
- Production-path invocation style (resolved locally, reversible): run the
  installed console script as a subprocess with `NOTES_API_URL` set — the
  strongest available production representation. If console-script
  installation is unavailable in the test environment, the accepted fallback
  is calling `main([...])` with no `client` argument in-process, which still
  uses the production default client and real HTTP; anything injecting a fake
  would not satisfy the requirement and must not be substituted.
- No open questions requiring user input beyond the approved parent decisions.

### Documentation

- `apps/notes_cli/README.md`: document the new flags with brief examples;
  keep `notes list` no-flag behavior described as-is. Audience: CLI users.

### Task checklist

- [ ] Add `--limit`, `--offset`, `--sort`, `--order`, `--q` to the `list`
      subparser and forward them to `list_notes()`.
- [ ] Keep `list_command` output format unchanged.
- [ ] Update `apps/notes_cli/README.md`; bump `notes-cli` to `0.2.0`.
- [ ] Unit tests: flag→parameter mapping for each flag and combined; no flags
      → bare `list_notes()` call (preservation at the CLI→client interface);
      rendering of paginated/sorted results (injected client).
- [ ] Production-path test: real service (uvicorn, ephemeral port) + seeded
      data + `NOTES_API_URL` + CLI invoked without an injected client;
      assert stdout for pagination, sorting, filtering, and the unparameterized
      run.
- [ ] Run the CLI test suite; existing `test_list_command` stays green.

### Requirement verification

- Production path (parent R6 — decisive): the subprocess/console-script run
  crosses CLI → `NotesClient.from_environment()` → real `httpx` → real
  service → rendered stdout. Asserting ordered, filtered, page-limited output
  proves the whole chain, which no lower-level or fake-based test can.
- Flag mapping and preservation (parent R5): unit tests with a stub at the
  CLI→client interface prove each flag forwards under its contract name and
  that a bare `notes list` issues the same call as today; existing test stays
  green.
- Documentation (parent R7): README diff reviewed in the same change as the
  flags that make it true.