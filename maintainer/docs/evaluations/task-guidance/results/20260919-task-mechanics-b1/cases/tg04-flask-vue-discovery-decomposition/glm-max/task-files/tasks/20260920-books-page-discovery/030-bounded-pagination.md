# Bounded pagination

Add bounded paging end to end: the server serves one page at a time over the
filtered and searched set with envelope metadata, and the Books page offers a
pager that stays consistent with the selected view — plus its own tests,
integration case, and spec update.

Parent Task: `tasks/20260920-books-page-discovery/000-main.md`

## Requirements checklist

- [ ] `GET /books` returns a bounded page (server-side per main-file Q1) of
      the filtered/searched set, with page metadata sufficient to render a
      pager, per the approved Q1/Q2 envelope.
- [ ] Page size is the approved constant (Q3); results outside the requested
      page are not served.
- [ ] Paging composes with the read filter and search — bounds are computed
      over whatever discovery parameters have landed.
- [ ] The Books page offers prev/next paging with a page indicator; controls
      disable at the bounds and reflect the current page.
- [ ] Changing filter or search resets the page per approved Q4; restoring or
      requesting an out-of-range page behaves per approved Q4.
- [ ] CRUD endpoints and behavior are unchanged; CRUD refreshes keep the
      current view, clamping the page into range when the result set shrank
      (approved Q7).
- [ ] `GET /books` without parameters still returns the exact unfiltered
      response.
- [ ] Maintained documentation describes the pagination contract and
      client paging behavior as landed.

## Supporting details

- This is the slice that makes larger collections practical: payloads stay
  bounded because the server never returns more than one page when pagination
  parameters are present.
- pytest seeding becomes cheap here: the isolation fixture from `010`
  (main decision D5) restores `server.app.BOOKS`, so tests can seed dozens of
  books without cleanup.
- The pager must derive its bounds from envelope metadata (`pageCount`),
  never from the row count of the current page alone.
- If this slice executes before `010`/`020`, it lands the discovery envelope
  itself and later slices adopt it — the envelope rule is defined by parameter
  presence, not slice order.

## Execution plan

Status: Draft

Approach: extend `server/query.py` with page slicing over the selected set and
total counting; parse `page` (and the size constant) in `server/app.py` and
emit `page`/`pageCount`/`total` per the approved envelope. In `Books.vue`, add
prev/next controls with a `Page X of Y` indicator, clamp/reset per approved
Q4, and keep CRUD refetches on the current (clamped) page.

Tasks:

- [ ] Implement page slicing + totals in `server/query.py`; `page` parsing and
      envelope metadata in `server/app.py` per approved Q1–Q4.
- [ ] Add the pager to `Books.vue` with bound-aware disabled states and the
      approved reset/clamp rules.
- [ ] Keep CRUD refetches on the current view with approved clamping.
- [ ] Tests: pytest (bounding, metadata, page over filtered/searched set,
      out-of-range behavior), component tests (pager bounds, page changes
      refetch, CRUD keeps clamped page), integration case for `page` over real
      HTTP.
- [ ] Rerun the unfiltered compatibility regression.
- [ ] Update `docs/development/book-discovery.md` with the pagination
      contract.

Risks: pager correctness depends on envelope metadata shape (blocked until
Q1/Q2 approved); reset/clamp semantics blocked until Q4/Q7 approved; seeded
multi-page fixtures must exercise at least three pages to prove bounding on
both ends.

### Implementation decisions and open questions

- Pager UI is prev/next plus an indicator (no page-number selector) — minimal
  and sufficient for "move through bounded pages"; a page-size selector stays
  out of scope per the main file.
- Page size lives as a server constant (Q3), not a client concern, so bounds
  have a single source of truth.
- No new open questions originate here beyond main-file Q1–Q7.

### Documentation

- Updates `docs/development/book-discovery.md`: pagination parameters, page
  size constant, envelope metadata, reset/clamp rules, and the unchanged
  unfiltered contract.

### Task checklist

- [ ] Server slicing, totals, and envelope metadata implemented per approved
      answers.
- [ ] Pager implemented with bounds, reset, and clamp rules.
- [ ] CRUD refetch paths keep the clamped current page.
- [ ] pytest, component, and integration tests added and passing.
- [ ] Unfiltered compatibility regression rerun and green.
- [ ] Spec page updated.

### Requirement verification

- Bounding at the API boundary → pytest: a seeded multi-page collection
  returns exactly the requested slice, correct `page`/`pageCount`/`total`, and
  composes with `read`/`q` when present; out-of-range and sub-1 pages behave
  per approved Q4.
- Unfiltered compatibility → pytest regression: parameter-less `GET /books`
  unchanged.
- Pager consistency at the UI boundary → component test: indicator matches the
  served page, prev/next disable at bounds, page changes refetch with `page`,
  filter/search changes reset per Q4, CRUD refetch keeps the clamped page.
- Transport agreement → integration case: `getBooks({ page })` (and combined
  parameter sets) against the live Flask process returns the expected bounded
  envelope.
- CRUD preservation → existing mutation tests pass unchanged; component test
  asserts refetches carry `page` with approved clamping.
- Documentation currency → spec statements match landed behavior in the same
  change.