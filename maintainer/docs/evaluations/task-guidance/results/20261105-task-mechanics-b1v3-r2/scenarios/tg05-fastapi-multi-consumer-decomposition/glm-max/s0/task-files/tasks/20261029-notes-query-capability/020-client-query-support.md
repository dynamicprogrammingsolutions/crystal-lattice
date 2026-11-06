# 020 — Client: query support in notes_client

Expose the approved notes-query capability in the reusable `notes_client`
package while preserving current zero-argument `NotesClient.list_notes()`
behavior exactly.

Parent Task: tasks/20261029-notes-query-capability/000-main.md

Depends On: tasks/20261029-notes-query-capability/010-service-query-endpoint.md
(the published contract; do not start before 010 is complete)

## Requirements checklist

- [ ] `NotesClient.list_notes()` accepts optional keyword-only parameters
      matching the approved contract (recommended: `limit`, `offset`, `sort`,
      `q`, all defaulting to `None`), per the parent's approved client-surface
      decision.
- [ ] A zero-argument call sends the unparameterized request exactly as today:
      `GET /notes/` with no query string, returning the decoded JSON list;
      existing call sites remain source-compatible.
- [ ] Provided parameters are serialized to the URL query string exactly per
      the published contract.
- [ ] `packages/notes_client/README.md` documents the new parameters and the
      zero-argument guarantee in the same change.

## Verification

- Component tests with the existing stub-transport harness: the zero-argument
  call issues a request to `/notes/` with no query parameters; each provided
  keyword produces the contract's query string; the decoded payload is passed
  through unchanged.
- Full client-to-service behavior is decisively proven once by 030's
  end-to-end production-path check using this real package; this subtask must
  not build a duplicate live-server harness.

## Supporting details

- `NotesClient` sends requests through an injected transport;
  `list_notes()` is a single `transport.get("/notes/").json()`
  (`packages/notes_client/notes_client/client.py:21`).
- Existing tests: `packages/notes_client/tests/test_client.py` with a stub
  transport returning `[]` (`packages/notes_client/tests/conftest.py`).
