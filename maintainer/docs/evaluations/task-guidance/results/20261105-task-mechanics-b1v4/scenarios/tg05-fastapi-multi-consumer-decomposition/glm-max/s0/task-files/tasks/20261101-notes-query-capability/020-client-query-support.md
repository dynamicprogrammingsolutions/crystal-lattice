# Client: expose the notes query capability on NotesClient

Expose the approved query capability on `NotesClient` so any Python consumer
can paginate, sort, and filter against the stable HTTP contract, without
changing the existing unparameterized call behavior, and prove the client's
contract conformance against the real running service.

Parent Task: tasks/20261101-notes-query-capability/000-main.md

## Requirements checklist

- [ ] `NotesClient` exposes the query capability with parameters matching the approved contract, mapping them to the stable HTTP contract and omitting any parameter not supplied.
- [ ] Existing `list_notes()` behavior is preserved: a parameter-free request to `/notes/` returning the parsed JSON list — proven by request-shape regression evidence.
- [ ] An integration test proves the real client against the real running service over real HTTP, covering at least one paginated, one sorted, and one filtered round trip. This is the decisive check for this subtask; fake-transport tests stay supporting evidence only.
- [ ] `packages/notes_client/README.md` describes the new surface in the same change.

Depends On: `tasks/20261101-notes-query-capability/010-api-query-contract.md`
(the contract must be stable before this package relies on it).
Depended on by: `tasks/20261101-notes-query-capability/030-cli-query-command.md`.

## Supporting details

**Proposed client surface (binding once the parent plan is approved).**
`list_notes(limit=None, offset=None, sort=None, q=None)`. Unset parameters are
omitted from the query string entirely, so an unparameterized call sends
exactly today's request (`GET /notes/` with no query component) and returns
the parsed JSON list.

**Current code facts.**

- `packages/notes_client/notes_client/client.py` — `NotesClient(transport)`;
  `from_environment()` builds an `httpx.Client` from `NOTES_API_URL` (default
  `http://127.0.0.1:8000`); `list_notes()` returns
  `self.transport.get("/notes/").json()`.
- Package `pyproject.toml`: `notes-client` 0.1.0, depends on `httpx` only.
- Existing tests (`packages/notes_client/tests/`) use a fake transport whose
  `get()` accepts `**kwargs`; they can verify call mapping but not contract
  conformance.
- Error-path behavior: the client does not raise on HTTP error statuses today.
  Parent decision 9 keeps it that way — do not add `raise_for_status` in this
  task; record as a possible follow-up instead.

**Harness facts.**

- No `uvicorn` is declared anywhere in the fixture; serving the real app in
  the integration test requires introducing it (parent plan decision 11:
  recommend root `pyproject.toml` dependencies).
- The service DB path is CWD-relative (`sqlite:///./notes.db`): launch the
  server subprocess from a temporary working directory and wait for readiness
  before testing.
- Seed data through the real HTTP API (`POST /notes/` with plain `httpx`) so
  the fixture itself stays on the production path.
- Keep this integration harness local to `packages/notes_client/tests/`;
  `packages/` and `apps/` are independently maintained and share no test code.
- Recommend bumping `notes-client` to 0.2.0 in this change (additive public
  surface on a 0.x package) — parent plan decision 10.

## Implementation plan

Status: Draft

**Design.** Extend `list_notes()` with the four optional keyword parameters.
Build the request's `params` dict from supplied values only and pass it to the
transport `get`; absent parameters produce the same parameter-free request as
today. Return the parsed JSON list unchanged.

**Order logic.** Starts only after 010 completes (stable contract, real
service to conform to). Its own milestone — client surface implemented and
conformance-proven — gates 030.

**Verification.** Decisive evidence: an integration test that launches the
real app via a `uvicorn` subprocess (temporary CWD, ephemeral port, readiness
wait), seeds notes over HTTP, then drives the real `NotesClient` (via
`from_environment()` with `NOTES_API_URL` pointed at the test server) through
paginated, sorted, and filtered calls, asserting results match the seeded
data under the approved contract semantics. Request-shape regression: extend
the fake-transport unit test to capture the request and assert that
`list_notes()` with no arguments issues a query-string-free `GET /notes/`.
Deliberately not covered: CLI rendering (030), hosted deployment.

**Risks.** Contract drift between package and service — caught by the
conformance test against the real service; harness flakiness from port or
readiness races — use an ephemeral port and poll readiness with a bounded
timeout; `notes.db` leakage — temporary CWD for the server process.

### Implementation decisions and open questions

Governed by parent plan decisions 4–7, 9–11. Local reversible choices (params
dict construction, fixture structure) resolve at execution.

### Documentation

`packages/notes_client/README.md` documents the new parameters and their
semantics in this same change (audience: Python consumers of the package).

### Task checklist

- [ ] Extend `list_notes()` with optional keyword parameters; omit unset values from the query string.
- [ ] Add the real-service integration test (uvicorn subprocess, temp CWD, seeded over HTTP).
- [ ] Extend the fake-transport unit test with the request-shape regression case.
- [ ] Update `packages/notes_client/README.md`; bump package to 0.2.0.
- [ ] Existing client suite stays green.

### Requirement verification

- Client exposes the capability against the stable contract → the real-client
  integration test over real HTTP. Not covered: CLI rendering.
- Unparameterized preservation → the request-shape regression case plus the
  existing suite staying green. Not covered: API response content (010's
  evidence).
- Documentation → the changed `packages/notes_client/README.md` page, reviewed
  in the same change as the code.
