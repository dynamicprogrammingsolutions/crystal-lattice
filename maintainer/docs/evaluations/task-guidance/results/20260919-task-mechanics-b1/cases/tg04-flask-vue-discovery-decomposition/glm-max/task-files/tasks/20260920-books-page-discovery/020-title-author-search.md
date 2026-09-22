# Title/author search

Add search end to end: a query parameter matching case-insensitive substrings
in title or author (per main-file Q5), a search control on the Books page, and
composition with the read filter — plus its own tests, integration case, and
spec update.

Parent Task: `tasks/20260920-books-page-discovery/000-main.md`

## Requirements checklist

- [ ] `GET /books` accepts a search query parameter matching case-insensitive
      substrings in title OR author, ANDed with any landed read filter;
      envelope and invalid/empty value behavior follow the approved answers to
      main-file Q1, Q2, Q4, and Q5.
- [ ] The search composes with the read filter and any other landed discovery
      parameters.
- [ ] The Books page offers a search control that filters the table, and the
      control reflects the active search (including restored values).
- [ ] The no-matches empty state (introduced by `010`, or introduced here if
      `010` has not executed) covers search-only and combined no-match cases.
- [ ] CRUD endpoints and behavior are unchanged; CRUD refreshes carry the
      active search alongside any landed filter.
- [ ] `GET /books` without parameters still returns the exact unfiltered
      response.
- [ ] Maintained documentation describes search semantics and composition as
      landed.

## Supporting details

- Extends the parameter-parsing structure from `010` and the selection
  function in `server/query.py`; no new architectural pieces.
- If this slice executes before `010`, it must introduce the differentiated
  no-matches empty state itself so every permitted order stays safe.
- Empty query text must behave as "no search active" (per approved Q4/Q5
  rules) so clearing the box restores the unfiltered-by-search view.
- Debounced live search (~250ms, main decision D6) keeps typing practical;
  tests use fake timers to stay deterministic.

## Execution plan

Status: Draft

Approach: extend `server/query.py` selection with the substring matcher over
title and author; parse `q` in `server/app.py` and include it in the discovery
envelope path. In `Books.vue`, add a text input bound to discovery state,
debounce it, fetch with `q` plus any landed parameters, and keep the control
value in sync with the active state. Keep `040`'s future URL mapping in mind
but do not build it here.

Tasks:

- [ ] Implement substring selection in `server/query.py` and `q` parsing in
      `server/app.py` per approved Q4/Q5.
- [ ] Add the debounced search control to `Books.vue`; fetch with the active
      parameter set; reuse/introduce the no-matches empty state.
- [ ] Thread `q` through `client/src/api/books.js` call sites, including CRUD
      refetches.
- [ ] Tests: pytest (title match, author match, case insensitivity, empty `q`,
      composition with `read`), component tests (typing refetches with `q`,
      control reflects state, no-matches state), integration case for `q` over
      real HTTP.
- [ ] Rerun the unfiltered compatibility regression.
- [ ] Update `docs/development/book-discovery.md` with search semantics and
      composition rules.

Risks: debounce timing in component tests (mitigate with fake timers); search
semantics are blocked until Q5 is approved; composition with `read` depends on
`010` having landed or must absorb the shared empty-state work itself.

### Implementation decisions and open questions

- Debounced live search (~250ms) rather than search-on-enter: matches
  discovery-style filtering; URL writing rules (push/replace) remain main
  decision D6 for `040`.
- Single input searches both fields (title OR author) per Q5's proposal; two
  separate inputs would be a scope change requiring user approval.
- No new open questions originate here beyond main-file Q1–Q7.

### Documentation

- Updates `docs/development/book-discovery.md`: search parameter, matching
  semantics, composition with the read filter, and the empty-query rule.
  Claims added only for behavior this change makes true.

### Task checklist

- [ ] Server selection and `q` parsing implemented per approved answers.
- [ ] Search control, debounced fetch, and empty states implemented.
- [ ] CRUD refetch paths carry `q` (and landed `read`).
- [ ] pytest, component, and integration tests added and passing.
- [ ] Unfiltered compatibility regression rerun and green.
- [ ] Spec page updated.

### Requirement verification

- Search correctness at the API boundary → pytest: substring matches in title
  and author, case-insensitive, empty `q` inert, ANDed with `read` when both
  parameters are present.
- Composition → pytest with both landed parameters active in one request.
- UI consistency → component test: debounced typing refetches with `q`; the
  control reflects the active search; no-matches state renders for search-only
  and combined no-match cases.
- Transport agreement → integration case: `getBooks({ q })` and
  `getBooks({ q, read })` against the live Flask process return the expected
  envelopes.
- CRUD preservation → existing mutation tests pass unchanged; component test
  asserts refetches include the active `q` (and `read` when set).
- Documentation currency → spec statements match landed behavior in the same
  change.