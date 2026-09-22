# Expose notes-query controls through the CLI production path

Add user-facing query controls to `notes list`, retain its current no-option
output behavior, and prove the full CLI → reusable client → HTTP service path.

Parent Task: tasks/20260919-notes-query/000-main.md
Depends On: tasks/20260919-notes-query/020-reusable-client.md

## Requirements checklist

- [ ] Expose the approved query controls through `notes list` with stable,
      documented option names and validation.
- [ ] Preserve `notes list` with no options, including its existing output
      format and use of the reusable client.
- [ ] Forward user-selected options through `NotesClient` to the service
      without a CLI-only implementation of filtering, sorting, or pagination.
- [ ] Prove the production client-to-service path with an integration test
      that invokes the CLI against a running FastAPI service.
- [ ] Update CLI documentation with examples, bounds, and compatibility
      behavior.

## Open requirement questions and material design decisions

The CLI cannot finalize its option spellings, defaults, or validation until
the service and client contract is approved. The remaining implementation
choice is how to host the FastAPI application for the decisive integration
test; either an in-process HTTP adapter or a short-lived local server is
acceptable only if the test still uses real HTTP and the production client
class.

## Supporting facts

`apps/notes_cli/cli.py` currently has one `list` subcommand and prints each
returned note as `id: title`. Its tests inject a fake client, which is useful
for output-focused unit coverage but cannot prove HTTP integration. The CLI
package declares no direct service dependency and imports the reusable client
package.

## Execution plan

Status: Draft

Once the client method surface is finalized, add argparse options that map
one-to-one to the approved query controls and pass them to
`NotesClient.list_notes()`. Keep rendering unchanged for the existing
no-option command. Add unit tests for parsing and rendering with a lightweight
fake, then add a separate integration test that starts or otherwise hosts the
real FastAPI application over HTTP, configures the production
`NotesClient`, invokes `main()` with query options, and asserts the filtered,
bounded output. The integration test must not replace the client with an
object whose `list_notes()` implementation returns fixture data.

### Implementation decisions and open questions

- CLI flag names, defaults, and validation messages depend on the approved
  cross-boundary contract. Do not add CLI aliases speculatively.
- The CLI should remain a presentation layer: query semantics and data
  selection belong to the service, and HTTP construction belongs to
  `NotesClient`.
- The service-hosting fixture remains an implementation choice, provided the
  test crosses a real HTTP boundary and uses the production client class.

### Documentation

Update `apps/notes_cli/README.md` with the finalized `notes list` options and
examples. State that the command uses `notes_client` and that no-option
invocation retains the existing output. Ensure examples agree with both the
service and client documentation.

### Task checklist

- [ ] Copy the approved client/service option contract into the CLI parser
      design.
- [ ] Add query flags and pass only selected values to the production client.
- [ ] Preserve and test no-option output and client delegation.
- [ ] Add focused parser/rendering tests for valid and invalid options.
- [ ] Add an end-to-end CLI integration test through a running FastAPI service
      and real `NotesClient`.
- [ ] Update CLI documentation.
- [ ] Run the parent task's final cross-boundary verification and record any
      environment limitations.

### Requirement verification

- [ ] CLI capability: command-level tests demonstrate each approved option is
      parsed and forwarded, while invalid values fail before an HTTP request.
- [ ] Compatibility: `notes list` without options still prints the existing
      `id: title` lines from the client's returned list.
- [ ] Production path: the decisive integration test invokes the actual CLI
      entry flow, production `NotesClient`, real HTTP transport, and FastAPI
      route, then verifies the service-selected result.