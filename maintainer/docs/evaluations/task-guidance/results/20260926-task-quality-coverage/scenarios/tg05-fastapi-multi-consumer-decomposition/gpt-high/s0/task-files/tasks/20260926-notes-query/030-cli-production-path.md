# Expose notes queries in the CLI and prove the production path

Add the approved notes-query controls to `notes list`, preserve its existing
no-option behavior, and verify the actual CLI -> reusable client -> running
service path.

Parent Task: tasks/20260926-notes-query/000-main.md
Depends On: tasks/20260926-notes-query/010-api-contract-and-service.md,
tasks/20260926-notes-query/020-python-client.md

## Requirements checklist

- [ ] `notes list` exposes CLI options corresponding to the approved query
      capability.
- [ ] The no-option `notes list` command retains its current output purpose
      and uses the reusable client's unparameterized behavior.
- [ ] CLI values are forwarded through `NotesClient.list_notes()` rather than
      reimplementing service querying.
- [ ] Invalid CLI values produce the approved user-facing nonzero failure.
- [ ] CLI documentation contains the supported options and examples.
- [ ] A decisive integration check runs the production CLI entry point with
      `NotesClient.from_environment()` against a running notes service, with no
      injected fake client, and proves that query options affect the
      service-backed output.

## Open requirement questions

- Confirm the final CLI option names, defaults, help text, and invalid-input
  behavior after the API contract is approved.
- Confirm whether CLI output remains one `id: title` line per note when the API
  response includes pagination metadata; this follows the approved response
  shape.

## Supporting facts

- The CLI implementation is `apps/notes_cli/cli.py`.
- It currently has only a required `list` subcommand and calls
  `list_command(selected)` after choosing an injected client or
  `NotesClient.from_environment()`.
- Existing CLI tests inject a fake client and assert only that output is
  nonempty; they do not prove the production client or service path.
- The CLI package has a separate README and console-script entry point
  (`notes = "notes_cli.cli:main"`).

## Execution plan

Status: Draft

After the API and client contracts are settled, add CLI arguments that map
one-to-one to the approved query inputs. Keep `list_command` focused on
formatting and have `main` pass parsed values to the production client
method. Preserve the existing no-option invocation and output format unless
the approved response shape requires an explicitly reviewed change.

Keep unit coverage for parsing and rendering with the injected fixture, but
make the decisive check stronger: start the real notes service on a local
address, invoke the actual `notes` console entry point with environment-based
configuration and query options, and assert output from records selected by
the service. Run a no-option invocation in the same path to prove the
compatibility behavior. The check must not pass by supplying the CLI's
optional `client` argument.

### Implementation decisions and open questions

- The CLI delegates all retrieval semantics to `NotesClient`; it must not
  duplicate filtering, sorting, or pagination.
- The end-to-end check must use the production environment/client selection
  path and a real HTTP request to the service.
- Exact option names, response-driven output handling, and invalid-input
  policy remain open until the API contract and client method are approved.

### Documentation

- Update `apps/notes_cli/README.md` with the final command syntax, options,
  examples, defaults, output behavior, and invalid-input behavior.
- Keep the existing basic `notes list` example to document compatibility.

### Task checklist

- [ ] Consume the settled API and client contracts.
- [ ] Add CLI parsing and forwarding for approved query options.
- [ ] Extend unit coverage for parsing, formatting, and no-option behavior.
- [ ] Add/run the real entry-point-to-running-service integration check.
- [ ] Update the CLI README.
- [ ] Record the exact command and service setup used as decisive evidence.

### Requirement verification

- CLI mapping: unit coverage must assert parsed values reach the client method
  and that no-option invocation retains existing output behavior.
- Production path: invoke the actual `notes` console script or equivalent
  installed entry point with `NOTES_API_URL` targeting a running service;
  seed known records through the service boundary, request a combined query,
  and assert the selected stable order and page in stdout.
- Compatibility: the same real path must run `notes list` without query
  options and verify the existing line-oriented output.
- Invalid input: invoke the public command with each approved invalid class
  and assert the documented nonzero/error behavior.

### Additional implementation verification

- Ensure CLI options are not silently ignored when their values are falsey or
  zero-like but valid under the approved contract.
- Ensure the integration command uses the package/runtime configuration that a
  user would use, rather than a test-only client injection or direct route
  call.