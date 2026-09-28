# Python client: query parameters on list_notes

Expose the approved query contract on the reusable client so Python consumers
can paginate, sort, and filter the notes collection, while the no-argument
`list_notes()` call keeps its current request and return behavior.

Parent Task: tasks/20260926-notes-query-capability/000-main.md
Depends On: tasks/20260926-notes-query-capability/010-api-collection-query.md
(the contract is implemented and locked before the client relies on it)

## Requirements checklist

- [ ] `NotesClient.list_notes()` accepts optional keyword-only `limit`,
      `offset`, `sort`, and `q`, and forwards provided values as query
      parameters on `GET /notes/` exactly as the approved contract defines
      them — no client-side transformation, defaulting, or validation.
- [ ] The no-argument call issues the same request as today (no query
      parameters) and returns the parsed JSON list — unchanged return type.
- [ ] Component tests prove parameter serialization via a captured request
      and prove the unchanged unparameterized request.
- [ ] `packages/notes_client/README.md` documents the parameters in the same
      change.

## Execution plan

Status: Draft

Approach:
- Extend `list_notes` in
  `packages/notes_client/notes_client/client.py` to
  `list_notes(self, *, limit=None, offset=None, sort=None, q=None)`; build a
  params mapping from the set values and pass it to
  `self.transport.get("/notes/", params=...)` only when non-empty, so the
  unparameterized call stays byte-identical to today's request.
- No validation in the client: the service is the contract boundary; the
  client passes values through (parent decision D5).

Tests (component level, `packages/notes_client/tests/`):
- Fake transport capturing path and query parameters:
  - each parameter appears in the captured query string with the expected
    encoding;
  - unset parameters are omitted;
  - the no-argument call sends no query string (regression) and returns the
    parsed JSON list.
- The existing client test passes unmodified. The full client-to-service
  path is not proven here: it is owned by the named decisive check in 030.

### Implementation decisions and open questions

- D5 (extend `list_notes`; no new method) is approved at the parent level.
  Local choices resolved here: keyword-only parameters to keep the no-arg
  call unambiguous, omission (not empty strings) for unset values.
- Open questions: none.

### Documentation

- `packages/notes_client/README.md`: document the optional parameters and
  note that the no-argument call is unchanged (Python integrator audience).

### Task checklist

- [ ] Add keyword-only query parameters to `list_notes()`
- [ ] Add component tests for serialization and the unparameterized regression
- [ ] Update `packages/notes_client/README.md`
- [ ] Run the client suite

### Requirement verification

- Parent R3 → captured-request component tests prove the forwarded parameters
  and the unchanged no-arg request/return; the production path is proven
  once, end to end, by the decisive check in 030.
- Parent R7 (client part) → README diff in the same change.