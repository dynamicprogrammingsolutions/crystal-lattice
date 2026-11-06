# 030 — CLI: query flags and production-path proof

Expose the approved notes-query capability on the `notes list` CLI command,
preserve flagless behavior, and prove the production client-to-service path
end to end.

Parent Task: tasks/20261029-notes-query-capability/000-main.md

Depends On: tasks/20261029-notes-query-capability/020-client-query-support.md
(and transitively 010-service-query-endpoint.md; do not start before 020 is
complete)

## Requirements checklist

- [ ] `notes list` accepts optional flags for the approved contract
      (recommended: `--limit N --offset N --sort FIELD --filter TEXT`, with
      `--filter` mapping to the contract's `q` parameter), per the parent's
      approved CLI-flag decision.
- [ ] Flagless `notes list` output is unchanged: `{id}: {title}` per line for
      every note, exactly today's rendering.
- [ ] Flags are passed through to `notes_client` query parameters per the
      published contract.
- [ ] The decisive production-path check passes: an automated end-to-end test
      launches the real service under a real ASGI server, seeds it over HTTP,
      and runs the real CLI entry point as a subprocess with `NOTES_API_URL`
      set, asserting query output (pagination + sort + filter) through the full
      CLI → `notes_client` → HTTP → FastAPI → SQLite chain. Stub-based tests
      do not satisfy this requirement.
- [ ] `apps/notes_cli/README.md` documents the new flags and the flagless
      behavior in the same change.

## Verification

- Component tests with the existing stub-client harness for argument parsing
  and output rendering, including the flagless regression.
- One decisive end-to-end test as named above (real server on an ephemeral
  port; installed `notes` console script preferred, direct
  `notes_cli.cli:main` invocation acceptable; real client only — never a
  stub). Needs uvicorn as a test-only dependency.

## Supporting details

- CLI entry point: `notes = "notes_cli.cli:main"` (`apps/notes_cli/pyproject.toml`);
  `list_command` renders `{id}: {title}` (`apps/notes_cli/cli.py`).
- The client honors `NOTES_API_URL` via `NotesClient.from_environment()`.
- Existing tests: `apps/notes_cli/tests/test_cli.py` with a stub client
  (`apps/notes_cli/tests/conftest.py`).
