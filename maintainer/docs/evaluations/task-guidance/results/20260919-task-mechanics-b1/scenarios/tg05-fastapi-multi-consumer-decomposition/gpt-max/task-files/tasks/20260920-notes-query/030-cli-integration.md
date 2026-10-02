# CLI notes-query integration

Expose the approved notes-query controls through `notes list`, preserve its
current no-option output, and prove the production CLI-to-client-to-service
path. This task depends on both the API contract and reusable client and is a
Draft planning handoff.

## Requirements checklist

- [ ] `notes list` exposes the approved query controls with clear help text
  and forwards them through the production `NotesClient`.
- [ ] An unparameterized `notes list` invocation preserves the current
  `id: title` output behavior.
- [ ] A decisive integration test invokes the CLI with a real
  `NotesClient` connected to the FastAPI service and verifies that
  pagination, stable sorting, and text filtering affect service-derived
  output as specified.

Parent Task: `tasks/20260920-notes-query/000-main.md`

Depends On:

- `tasks/20260920-notes-query/010-public-api-contract.md`
- `tasks/20260920-notes-query/020-reusable-client.md`

## Scope and workstreams

- Own CLI argument parsing, option-to-client mapping, output behavior,
  integration evidence, and application documentation.
- Keep the existing injectable client seam for fast rendering tests, but do
  not treat it as proof of the production path.
- Do not add CLI-only query semantics or bypass the reusable client.

## Unresolved requirement questions

The API and client tasks must resolve these before this task starts:

- Final option names, value formats, defaults, and validation messages.
- Whether the CLI displays metadata if the approved response is not a bare
  list, and how empty result sets are rendered.
- Whether all service query controls are exposed or a documented subset is
  approved.

## Research and supporting facts

- `apps/notes_cli/cli.py` currently defines only a `list` subcommand and
  calls `client.list_notes()` without arguments.
- `list_command` prints each returned note as `"{id}: {title}"`.
- The current CLI test injects a minimal fake client, proving rendering only;
  it does not exercise argument parsing, HTTP, the reusable package, or the
  FastAPI service.
- The CLI README currently promises only that `notes list` prints every note
  through `notes_client`.

## Execution plan

Status: Draft

1. Wait for the API contract and client surface to be approved and verified.
2. Add the approved `notes list` options and pass values directly through
   the production client API. Preserve existing no-option parsing and
   rendering.
3. Keep unit coverage for parsing, help, rendering, and user-facing
   validation. Add a separate integration test that supplies a real
   `NotesClient` with a real HTTP transport to the FastAPI service, invokes
   the CLI entry point with query options, and asserts service-derived
   output.
4. Update the CLI README with supported options and examples after the
   production-path test passes.

Execution waits for completion and approval of both declared dependencies.

### Implementation decisions and open questions

- CLI flags must mirror the approved public contract closely enough that
  users can transfer API examples to the command without undocumented
  translation.
- The decisive test must not inject a fake object whose `list_notes()` is
  preprogrammed with filtered data. It must cross the real client and
  FastAPI collection route; a test service process or faithful HTTP
  application transport may provide the environment.
- Output formatting should remain the existing one-line note format unless
  the approved response contract makes additional metadata user-visible.

### Documentation

- Update `apps/notes_cli/README.md` with the final command syntax, bounds,
  sorting/filter examples, and no-option compatibility behavior.
- Keep help text and README examples synchronized with the approved client
  and API contract.

### Task checklist

- [ ] Confirm both API/contract and client dependencies are complete.
- [ ] Implement approved CLI options and client forwarding.
- [ ] Add parsing/help/rendering regression tests.
- [ ] Add and run the real CLI-to-client-to-service integration test.
- [ ] Update CLI documentation and report the production-path evidence.

### Requirement verification

- **CLI controls:** parser and forwarding tests assert each approved option
  reaches the client in the expected form and invalid input is reported.
- **Unparameterized compatibility:** the existing rendering test plus a
  no-option invocation assert the `id: title` output remains unchanged.
- **Production path:** the decisive integration test invokes the CLI entry
  point with the actual `NotesClient` and FastAPI service, seeds notes with
  distinguishable sort/filter values, and asserts the returned output proves
  the service performed the query.