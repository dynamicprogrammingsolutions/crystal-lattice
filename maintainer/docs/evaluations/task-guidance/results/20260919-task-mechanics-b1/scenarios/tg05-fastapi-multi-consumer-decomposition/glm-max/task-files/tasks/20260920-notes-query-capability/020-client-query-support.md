# Client: notes query support in notes-client

Extend the reusable `notes-client` package so `NotesClient.list_notes()` can
express the frozen notes-query contract (bounded pagination, stable sorting,
optional text filtering) while the current unparameterized call keeps issuing
the identical request as today.

Parent Task: tasks/20260920-notes-query-capability/000-main.md

Depends On: tasks/20260920-notes-query-capability/010-service-query-api.md
(the HTTP contract must be implemented and its specification published before
this package's public surface grows against it).

## Requirements checklist

- [ ] `NotesClient.list_notes()` accepts optional keyword parameters mirroring
      the frozen contract: `limit`, `offset`, `sort`, `order`, `q`.
- [ ] Calling `list_notes()` with no arguments issues the exact request issued
      today — `GET /notes/` with no query string — so existing client users are
      unaffected.
- [ ] Parameter names and validation-free pass-through semantics match the
      contract; the client forwards values and lets the service enforce bounds
      (client-side duplication of server validation is not required and not
      added).
- [ ] `packages/notes_client/README.md` documents the new optional parameters
      for client users, with the unparameterized call shown as default
      behavior.
- [ ] Evidence: component tests for the request actually issued (no params
      when called bare; contract-matching params otherwise), plus one
      integration test of the real client over real HTTP against a real
      running service exercising the query path.

## Supporting details

Facts from inspection:

- `packages/notes_client/notes_client/client.py:20` — `list_notes()` currently
  calls `self.transport.get("/notes/").json()` with no other arguments.
- `from_environment()` (`client.py:9`) builds an `httpx.Client` from
  `NOTES_API_URL` (default `http://127.0.0.1:8000`); the transport attribute is
  the only injection point.
- `packages/notes_client/tests/test_client.py` uses a fake transport whose
  `get(self, path, **kwargs)` accepts arbitrary keyword arguments — sufficient
  to assert forwarded `params` without real HTTP, but it does not prove real
  HTTP behavior; that is why one integration test is required.
- Package version is `0.1.0`; per parent decision 9 it is bumped to `0.2.0` in
  this change.
- Contract reference: parent plan decisions 1–8; the authoritative text is
  `docs/notes-query.md` created by subtask `010`.
- The service-boot harness needed for the integration test (real app from
  `src/`, uvicorn on an ephemeral port) is maintained test infrastructure; it
  is justified here because the package's entire purpose is real HTTP, and it
  is exercised for real by the CLI production-path test in subtask `030`.

## Execution plan

Status: Draft

Change `list_notes` to a keyword-only signature
`list_notes(self, *, limit=None, offset=None, sort=None, order=None, q=None)`.
When every parameter is `None`, call `self.transport.get("/notes/")` exactly as
today (no `params` argument at all) — the preservation guarantee is this
branch, not a reconstructed equivalent. When any parameter is set, build
`params` from the non-`None` values only (so omitted parameters stay truly
absent from the query string) and pass it to `transport.get`. Bump the package
version, update the README, and add the component and integration tests.

### Implementation decisions and open questions

- Keyword-only parameters with `None` defaults (resolved locally, reversible):
  prevents positional-argument drift if the contract later grows, and makes
  "absent" unambiguous.
- No client-side validation or default injection (resolved locally): the
  service owns bounds and defaults; duplicating them in the client invites
  drift from the frozen contract. Server `422`s propagate to callers as httpx
  responses, matching today's error behavior (unspecified, unchanged).
- No open questions requiring user input beyond the approved parent decisions.

### Documentation

- `packages/notes_client/README.md`: document the optional parameters and
  their contract meaning, pointing to `docs/notes-query.md` as the
  authoritative HTTP contract. Audience: users of the reusable client package.

### Task checklist

- [ ] Add the keyword-only parameters and the bare-call fast path to
      `NotesClient.list_notes()`.
- [ ] Bump `notes-client` version to `0.2.0` (parent decision 9).
- [ ] Update `packages/notes_client/README.md`.
- [ ] Component tests (fake transport capturing `get` kwargs): bare call → no
      params kwarg; each parameter forwards with its contract name; `None`
      values omitted from `params`.
- [ ] Integration test: boot the real service (uvicorn, ephemeral port), seed
      via the service's public POST route, point
      `NotesClient.from_environment()` at it via `NOTES_API_URL`, and verify a
      paginated/sorted/filtered query and a bare query against the expected
      results — through real `httpx`, not a fake.
- [ ] Run the client test suite; existing `test_list_notes` stays green.

### Requirement verification

- Capability mirroring (parent R1/R4): integration test through real HTTP
  shows the client's query call returns the page the contract defines
  (bounds/sort/filter applied by the real service) — this crosses the
  package's real transport boundary, which a fake cannot prove.
- Preservation (parent R2, client side): component test asserts the bare call
  reaches the transport as `get("/notes/")` with no `params` kwarg, matching
  today's code path; existing test stays green.
- Documentation (parent R7): README diff reviewed in the same change as the
  code that makes it true.