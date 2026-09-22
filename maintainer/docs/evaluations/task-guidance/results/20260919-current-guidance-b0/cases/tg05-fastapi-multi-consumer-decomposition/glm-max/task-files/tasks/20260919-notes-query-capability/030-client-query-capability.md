# Add the notes-query capability to the notes_client package

Extend the reusable `NotesClient` public API with the approved contract's
optional pagination, sorting, and filtering parameters, forwarded to the
collection route, while preserving the current unparameterized call exactly,
with unit evidence at the client's HTTP-construction boundary and the package
README updated in the same change.

Parent Task: `tasks/20260919-notes-query-capability/000-main.md`

Depends On: `tasks/20260919-notes-query-capability/010-query-contract.md`
(the client is a consumer of the stable HTTP contract). It deliberately does
not depend on `020`: the client's own behavior is testable against the
contract without the server implementation, and the real client-to-service
composition is proven in `040`.

## Requirements checklist

- [ ] L1: `NotesClient` exposes the query capability per the approved
      contract: optional pagination, sort, and filter parameters are forwarded
      to `GET /notes/` as the contracted query string.
- [ ] L2: Unparameterized `list_notes()` is preserved: the request issued is
      identical to today's (path `/notes/`, no query parameters) and the
      return contract is unchanged — proven by a regression test.
- [ ] L3: `packages/notes_client/README.md` describes the capability as
      current supported behavior, updated in the same reviewed change as the
      code.

## Supporting facts

- `NotesClient` (`packages/notes_client/notes_client/client.py`) takes an
  injected transport and calls `self.transport.get("/notes/").json()`.
  `from_environment()` wraps `httpx.Client` bound to `NOTES_API_URL`.
  httpx natively supports `params=` on `get`, so parameter forwarding needs no
  new dependency and no manual query-string encoding.
- Existing test transport (`packages/notes_client/tests/conftest.py`) returns
  a fixed empty response and records nothing. The plan extends this maintained
  test harness to record `(path, params)` per call so tests can assert exact
  forwarding. Per testing guidance, shared test harnesses are maintained test
  infrastructure verified through a real consumer — the existing and new
  client tests are that consumer.
- The client's important boundary is HTTP request construction; a recording
  transport is the least expensive test that proves it without weakening the
  client code path. Full composition with the real service is intentionally
  deferred to `040`'s end-to-end proof and is recorded below as the gap this
  subtask leaves open.
- Current README states `list_notes()` "currently returns the unparameterized
  collection" — that sentence must change with the behavior (L3), not before.

## Execution plan

Status: Draft

1. Decide the method surface (open questions below) and add the optional
   parameters to `list_notes()` mirroring the approved contract's names and
   semantics. Absent parameters are omitted from the request entirely — no
   defaults are sent — so an unparameterized call produces byte-identical
   requests to today's behavior (L2).
2. Extend the test harness transport to record requests, then add tests:
   - Each parameter forwarded alone, with the exact expected `params`.
   - Combined parameters in one call.
   - Unparameterized regression (L2): `list_notes()` with no arguments issues
     the request exactly as before (no `params` / no query string) and
     returns the parsed JSON body.
3. Update `packages/notes_client/README.md` (L3) in the same change.
4. Run the `packages/notes_client/tests` suite; existing tests pass
   unmodified.

### Implementation decisions and open questions

- Method surface (material, user-visible for Python consumers; needs approval
  with this plan): extend `list_notes()` with optional keyword parameters
  (recommendation — one capability, one method, unparameterized default
  unchanged) vs add a separate `query_notes()` method. If the approved 010
  contract shapes parameter names differently than the client surface, the
  client surface follows the contract's names.
- No other open questions: transport injection and `from_environment()`
  behavior are preserved as-is.

### Documentation

- `packages/notes_client/README.md` (audience: Python consumers of the
  package): document the optional parameters and state that the unparameterized
  call is unchanged. Same change as the code.

### Task checklist

- [ ] Client method extended per the approved contract
- [ ] Recording-transport tests added (parameter forwarding + unparameterized
      regression)
- [ ] `packages/notes_client/README.md` updated in the same change
- [ ] `packages/notes_client/tests` suite passes, existing tests unmodified

### Requirement verification

- L1: recording-transport unit tests proving the exact query-string
  construction per parameter and in combination — the client package's public
  boundary; decisive for the client side of R1/R2–R4 forwarding.
- L2: the regression test proving the no-argument call is request-identical
  to current code (R6). Current existing test (returns a list) is kept as a
  supporting shape check, not as the evidence for L2.
- L3: the README diff reviewed with the code change.
- Known gap deferred by design: the client against the real service is proven
  in `040`'s end-to-end test (R8); this subtask's evidence is
  request-construction only and must not be cited as service-composition
  proof.

### Additional implementation verification

- Full `packages/notes_client/tests` run, existing tests unmodified.
- Confirm `from_environment()` behavior is untouched (no new configuration
  surface unless the approved contract requires one).