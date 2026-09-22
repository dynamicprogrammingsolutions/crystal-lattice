# Expose notes queries through the reusable Python client

Own the `notes-client` public method surface and its mapping to the settled
notes-query HTTP contract, while preserving the current no-argument client
behavior.

Parent Task: tasks/20260920-notes-query/000-main.md

Depends On: tasks/20260920-notes-query/010-api-contract.md

## Requirements checklist

- [ ] The reusable client exposes the approved notes-query options with stable
  Python names, types, defaults, and validation behavior.
- [ ] The client maps supplied query options to the approved API parameters and
  returns the approved response shape.
- [ ] `NotesClient.list_notes()` with no arguments retains its current list
  return behavior and unparameterized request semantics.

## Scope and boundary

This subtask owns `packages/notes_client/notes_client/client.py`, the package
README, and client-focused tests. It consumes the API contract; it does not
redesign wire parameters or CLI behavior.

## Research and supporting facts

- `NotesClient.list_notes()` currently takes no arguments and calls
  `self.transport.get("/notes/").json()`.
- The package has no separate models or query type; the smallest compatible
  surface is an extension of `list_notes()`, subject to the approved contract.
- `packages/notes_client/tests/test_client.py` currently proves only that the
  no-argument call returns a list, while its fixture transport ignores request
  keyword arguments.

## Execution plan

Status: Draft

1. Read the approved API specification from
   `tasks/20260920-notes-query/010-api-contract.md` and map its query
   vocabulary to a stable Python method signature.
2. Preserve the no-argument call path, including its list return shape, and
   ensure optional arguments are omitted or encoded according to the
   specification.
3. Add focused client tests with a request-aware transport double for exact
   parameter mapping, plus a service-backed check if the response shape needs
   cross-boundary coverage.
4. Update `packages/notes_client/README.md` with the supported method usage,
   query semantics, and preserved no-argument behavior.
5. Provide the stable client surface to the CLI subtask; do not let CLI flag
   design alter the package contract.

### Implementation decisions and open questions

- Decision: the client depends on the API contract and cannot independently
  invent parameter names, defaults, response envelopes, or validation rules.
- Decision: retain `list_notes()` as the compatibility entry point and extend
  it only as approved by the contract.
- Open: the exact keyword signature, local-vs-server validation, and response
  typing remain dependent on the unresolved API questions.

### Documentation

- Update `packages/notes_client/README.md` only after the API contract and
  implementation are settled.
- Document the Python signature and show both the no-argument call and a
  bounded/filtering call using the exact approved names.

### Task checklist

- [ ] Confirm the API contract is approved and stable.
- [ ] Define the client method signature and parameter encoding.
- [ ] Implement the client mapping while preserving the no-argument path.
- [ ] Add mapping and compatibility tests.
- [ ] Update package documentation and report evidence to the parent task.

### Requirement verification

- A client test calls the public `NotesClient.list_notes(...)` method with
  each supported option and asserts the transport receives exactly the
  documented HTTP parameters and path.
- A no-argument client test asserts the existing list result and confirms no
  query options are required.
- A service-backed client check uses the real FastAPI application through the
  client transport and confirms the client can consume the approved query
  response, without replacing the API verification owned by subtask 010.

### Additional implementation verification

- Keep compatibility with both `NotesClient.from_environment()` and injected
  transports.
- Ensure omitted optional values do not accidentally become different query
  values such as empty strings or zeroes.
- Run the package test suite with its existing import/setup expectations.