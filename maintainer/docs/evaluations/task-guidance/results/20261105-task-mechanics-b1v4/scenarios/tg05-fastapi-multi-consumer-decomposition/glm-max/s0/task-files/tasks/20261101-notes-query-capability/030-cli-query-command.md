# CLI: query flags and the production-path proof

Expose the query capability to CLI users as flags on the `list` command and
prove the production client-to-service path end to end: a real CLI invocation
through the production `NotesClient` against a real running service, with no
test doubles in that path.

Parent Task: tasks/20261101-notes-query-capability/000-main.md

## Requirements checklist

- [ ] CLI users can query notes with pagination, sorting, and filtering flags on `notes list`, passed through to the production client; output rendering is unchanged.
- [ ] The decisive end-to-end check traverses the real production path — CLI invocation → production `NotesClient.from_environment()` → running service over HTTP — and asserts that stdout reflects the requested paging, sorting, and filtering. Fake-client unit tests remain supporting evidence only.
- [ ] Existing `notes list` output behavior is preserved for the unparameterized case, covered by both the unit regression and the end-to-end check.
- [ ] `apps/notes_cli/README.md` documents the new flags in the same change.

Depends On: `tasks/20261101-notes-query-capability/010-api-query-contract.md`
and `tasks/20261101-notes-query-capability/020-client-query-support.md`
(the CLI consumes the client method against the stable contract).

## Supporting details

**Proposed CLI surface (binding once the parent plan is approved).** The
`list` subcommand gains `--limit` (int ≥ 1), `--offset` (int ≥ 0), `--sort`
(choices: `id`, `title`, `description` and their `-`-prefixed descending
forms), and `--query` (free text, mapped to the client's `q`). argparse
validates ranges and choices locally so normal CLI use never triggers a 422;
values pass through to `client.list_notes(...)`.

**Current code facts.**

- `apps/notes_cli/cli.py` — `main(argv=None, client=None)` builds an
  argparse parser with a required `list` subcommand; `list_command(client)`
  prints `{id}: {title}` per note from `client.list_notes()`. A `client`
  argument already allows injection, but the decisive check uses the
  production client, not an injected double.
- `apps/notes_cli/pyproject.toml` — console script
  `notes = "notes_cli.cli:main"`; declares **no dependencies** despite
  importing `notes_client` (parent plan decision 10: add the dependency and
  report it).
- **Pre-existing defects to fix incidentally and report:** the console script
  targets a `notes_cli` package directory that does not exist
  (`apps/notes_cli/` contains `cli.py` directly), and
  `apps/notes_cli/tests/test_cli.py` calls `list_command` without importing
  it, so the current CLI test cannot pass as shipped. 030 makes the real CLI
  code importable in tests and repairs the missing import; that repair is
  reported, not silent.
- The CLI module has no `__main__` block, so the automated decisive check
  invokes `main(argv)` in-process with the production client; the installed
  `notes` console script remains the manual equivalent.
- Existing CLI tests use a fake client (`tests/conftest.py`); kept as
  rendering-regression evidence only.

**Harness facts.**

- Real-service runs need `uvicorn` (introduced per parent plan decision 11)
  and a subprocess launched from a temporary working directory (the service
  DB path is CWD-relative), with readiness polling and an ephemeral port.
- Seed notes over real HTTP (`POST /notes/`) before invoking the CLI.
- Keep this end-to-end harness local to `apps/notes_cli/tests/`; no shared
  test code with the client package.

## Implementation plan

Status: Draft

**Design.** Extend the `list` subparser with `--limit`, `--offset`, `--sort`,
and `--query`, with argparse-level validation (type/range/choices) matching
the approved contract so user errors surface locally with a clean message and
nonzero exit. Pass validated values through to the production client method;
leave `list_command` rendering as is.

**Order logic.** Last subtask: consumes the client method (020) against the
stable contract (010). Its milestone — the production path proven end to end —
completes the feature.

**Verification.** Decisive evidence, named exactly: start the real app with a
`uvicorn` subprocess from a temporary CWD on an ephemeral port; poll
readiness; seed at least five notes over HTTP including duplicate-title rows
and filterable text; set `NOTES_API_URL` to the test server; invoke
`main(["list", "--limit", "2", "--offset", "2", "--sort", "title",
"--query", "<term>"])` (and variants) with the production
`NotesClient.from_environment()`; assert stdout lines match the expected
page of the filtered, title-sorted set, and that the unparameterized
`main(["list"])` output equals today's `{id}: {title}` rendering of every
note. No test doubles appear in this path. Supporting evidence: the repaired
fake-client unit test for rendering. Deliberately not covered: hosted
deployment, concurrency, and the console-script packaging itself (the missing
`notes_cli` package directory is fixed only as far as tests require; if full
console-script installability is wanted, that is a follow-up).

**Risks.** The e2e harness is the most complex test in the feature (process
lifecycle, ports, readiness) — bound all waits with timeouts and clean up the
subprocess; scope creep via the pre-existing packaging defects — fix the
minimum needed for the decisive check and report the rest; regression risk on
unparameterized output — covered by the e2e case plus the unit test.

### Implementation decisions and open questions

Governed by parent plan decisions 4–8 and 10–11. Local reversible choices
(exact flag names if `--query` feels wrong, validation messages) resolve at
execution; flag names are user-visible, so any deviation is reported.

### Documentation

`apps/notes_cli/README.md` documents the new flags with examples in this same
change (audience: CLI users).

### Task checklist

- [ ] Add `--limit`, `--offset`, `--sort`, `--query` to the `list` subcommand with argparse validation; pass through to the production client.
- [ ] Add the end-to-end production-path test exactly as named under Verification.
- [ ] Fix the missing `list_command` import in `test_cli.py` and make the CLI module importable; report both repairs.
- [ ] Add the undeclared `notes-client` dependency to `apps/notes_cli/pyproject.toml`; report it.
- [ ] Update `apps/notes_cli/README.md`.
- [ ] Existing CLI suite stays green.

### Requirement verification

- CLI exposes the capability and proves the production client-to-service path
  → the named end-to-end check; it is the only check that traverses CLI,
  client, and service together, which is why it cannot be waived or replaced
  by the per-side tests. Not covered: hosted deployment, concurrency.
- Unparameterized CLI output preserved → the `main(["list"])` e2e case plus
  the fake-client rendering unit test. Not covered: API or client internals
  (010/020 evidence).
- Documentation → the changed `apps/notes_cli/README.md` page, reviewed in the
  same change as the code.
