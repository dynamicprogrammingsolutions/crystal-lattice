# Read-status filter

Add the first discovery capability end to end: filter books by read status —
server selection, API parameter, Books page control, table and empty-state
consistency — plus the first real integration coverage, the pytest isolation
fixture, the verified component test harness, and the book-discovery spec
page.

Parent Task: `tasks/20260920-books-page-discovery/000-main.md`

## Requirements checklist

- [ ] `GET /books` accepts a read-status query parameter and returns only
      matching books. Parameter name, accepted values, envelope, and invalid
      value behavior follow the approved answers to main-file Q1, Q2, and Q4.
- [ ] The filter composes with any discovery parameters that have already
      landed (none at plan time; this slice introduces the parameter-parsing
      structure that `020` and `030` extend).
- [ ] The Books page offers a read-status control that filters the table, and
      the control reflects the active filter. If main-file Q6 is approved, the
      table also shows a read-status column.
- [ ] An empty collection ("No books found.") is distinguishable from "no
      matches for the active filter", and each case shows the right message.
- [ ] CRUD endpoints and behavior are unchanged; component CRUD refreshes
      carry the active read filter (main-file Q7 as approved).
- [ ] `GET /books` without parameters returns the exact current unfiltered
      response — the compatibility regression test lands here.
- [ ] Maintained documentation describes the read filter, the envelope rule,
      and the preserved unfiltered contract as landed.

## Supporting details

- First server change of the effort: `server/app.py` gains query-parameter
  parsing and response shaping; `server/query.py:list_books(books)` grows into
  the selection seam used by later slices.
- `getBooks(params)` already forwards query parameters; no transport change is
  expected beyond passing the new parameter from every refetch path.
- Seed data has one read and one unread book — enough to assert filtering —
  and tests may seed more through the existing POST route once the isolation
  fixture (main decision D5) makes shared `BOOKS` state safe.
- The component test harness is suspected broken (no vitest environment
  config, no jsdom dependency found); verify before relying on it.
- The empty collection state already renders `No books found.`; the
  differentiated no-matches state is introduced here and reused by `020`.

## Execution plan

Status: Draft

Approach: implement read-status selection as a pure function in
`server/query.py`, parse `read` in `server/app.py`, and shape the response per
the approved Q1/Q2 rule (no parameters → today's exact response; any discovery
parameter → discovery envelope). On the client, add a read-status control
(select: All / Read / Unread) to `Books.vue`, render `read` if Q6 is approved,
fetch with the active parameter, and differentiate the two empty states. Pass
`read` from all refetch paths, including CRUD refreshes.

Tasks:

- [ ] Verify the component test harness runs; if not, establish it
      (environment and/or dev dependency) and record what was added.
- [ ] Add the autouse pytest fixture snapshotting/restoring `server.app.BOOKS`
      (main decision D5).
- [ ] Implement read-status selection in `server/query.py` and parameter
      parsing + response shaping in `server/app.py` per approved Q1/Q2.
- [ ] Add the read-status control, filtered fetch, read column (if Q6
      approved), and differentiated empty state to `Books.vue`.
- [ ] Thread `read` through `client/src/api/books.js` call sites, including
      CRUD refetches.
- [ ] Tests: pytest (filtered results; invalid value rule; exact unfiltered
      compatibility regression), component tests (control ↔ table ↔ empty
      state; CRUD refetch carries `read`), integration case for `read` over
      real HTTP (main decision D7 harness born here).
- [ ] Create `docs/development/book-discovery.md` and link it from
      `docs/development/index.md`; document the read filter and contract.

Risks: envelope and invalid-value behavior are blocked until Q1/Q2/Q4 are
answered; the component harness may need environment work first; the
integration harness adds a process-lifecycle dependency to the client test
run — keep its failure mode explicit rather than silently skipping.

### Implementation decisions and open questions

- Parameter name `read` with values `true`/`false` (main decision D2); the
  control is a select rather than toggle buttons — local UI choice, reversible.
- Slice-local decisions defer to the main file's decisions D1–D7; anything
  touching Q1–Q7 behavior waits for the approved answers recorded there.
- No open questions originate in this slice beyond those already tracked in
  the main file.

### Documentation

- Creates `docs/development/book-discovery.md` (audience: developers) and
  links it from `docs/development/index.md`, replacing the "No book-discovery
  specification exists." line. Content covers only behavior this slice makes
  true, plus the envelope/unfiltered contract once Q1/Q2 are approved.

### Task checklist

- [ ] Component harness verified/established; result recorded in
      Implementation Notes.
- [ ] pytest `BOOKS` isolation fixture added and exercised by the new tests.
- [ ] Server selection + parameter parsing + response shaping implemented per
      approved answers.
- [ ] Client control, fetch wiring, read column (if approved), and empty
      states implemented.
- [ ] pytest, component, and integration tests added and passing.
- [ ] Spec page created and linked; unfiltered compatibility regression green.

### Requirement verification

- Filter correctness at the API boundary → pytest: seeded read/unread books;
  `read=true` / `read=false` return only matching rows; composition hook
  exercised as later slices land.
- Unfiltered compatibility → pytest: parameter-less `GET /books` returns the
  exact legacy JSON shape and full list (decisive regression for the preserved
  contract).
- UI consistency → component test: changing the control refetches with `read`
  and renders only matching rows; control reflects the active filter; both
  empty states render their own message at the component boundary.
- Transport agreement → integration case: `getBooks({ read })` against the
  live Flask process returns the filtered envelope — proves client and server
  agree on the parameter over real HTTP.
- CRUD preservation → existing `tests/test_books_api.py` mutation tests pass
  unchanged; component test asserts add/update/remove refetches include the
  active `read` value.
- Documentation currency → the spec page statements match landed behavior in
  the same change (reviewed as part of the slice, not deferred).