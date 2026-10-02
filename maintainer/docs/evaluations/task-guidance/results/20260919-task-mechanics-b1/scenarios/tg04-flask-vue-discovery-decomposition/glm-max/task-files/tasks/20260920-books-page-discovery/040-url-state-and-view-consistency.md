# URL state sharing and view consistency

Make the full discovery state shareable and restorable through the `/books`
URL: serialize the combined filter/search/page state into query parameters,
restore it on load (including invalid and out-of-range values), keep browser
back/forward consistent, and prove the table, active controls, empty state,
and CRUD refreshes stay consistent across every state.

Parent Task: `tasks/20260920-books-page-discovery/000-main.md`

Depends On: `tasks/20260920-books-page-discovery/010-read-status-filter.md`, `tasks/20260920-books-page-discovery/020-title-author-search.md`, `tasks/20260920-books-page-discovery/030-bounded-pagination.md`

## Requirements checklist

- [ ] The full discovery state (read filter, search text, page) serializes
      into `/books` query parameters and restores from them on load; the
      default state produces no discovery parameters in the URL (main decision
      D2).
- [ ] Browser back/forward keeps the table, active controls, empty state, and
      pager consistent with the restored view (main decision D6 governs
      push/replace).
- [ ] Invalid or out-of-range URL state restores to the approved defined
      state (main-file Q4).
- [ ] Active controls reflect restored and navigated state — no drift between
      the URL and what the controls show.
- [ ] CRUD refreshes after restore keep the restored view (current query,
      clamped page per approved Q7).
- [ ] A shared URL's discovery state round-trips through the real client API
      and Flask server (integration).
- [ ] Documentation is finalized: the spec covers URL sharing/restoration, and
      the root README reflects the completed discovery capability.

## Supporting details

- This slice owns the cross-cutting consistency requirement: it is the single
  decisive check for "table, active controls, empty state, browser navigation,
  and CRUD refreshes stay consistent with the selected view" across the
  combined state.
- URL sync is built once here over the final combined state shape rather than
  as three partial serializations (main decision D1); the parameters and
  defaults it maps were defined by the earlier slices.
- Component tests must mount `Books.vue` with a real router using
  `createMemoryHistory()` (main decision D4) so restore and navigation run
  through real router behavior; memory history faithfully represents our sync
  logic — the router library owns the browser history internals.
- `Books.vue` is not router-aware today; this slice introduces the
  route-query ↔ discovery-state mapping and the push/replace discipline.

## Execution plan

Status: Draft

Approach: in `Books.vue`, map discovery state ↔ `route.query` in one place:
restore state from the route before the first fetch, `push` on discrete
control changes (filter, page) and debounced-`replace` for search typing
(main decision D6), and react to route changes (back/forward) by re-fetching
with the restored state. Omit default values from the URL. Handle
invalid/out-of-range restores per approved Q4 before fetching.

Tasks:

- [ ] Implement the route-query ↔ discovery-state mapping and restore-on-load
      in `Books.vue` (including invalid/out-of-range handling per approved Q4).
- [ ] Wire push/replace URL writing per main decision D6.
- [ ] React to route navigation (back/forward) by restoring state and
      refetching.
- [ ] Keep CRUD refetches consistent with the restored view (clamped page).
- [ ] Component tests with memory-history router: serialize/restore, back/
      forward, invalid-state restore, controls-in-sync, CRUD-after-restore,
      and the decisive combined scenario (fresh → filtered → searched → paged
      → shared-link restore → back/forward → mutate, asserting table,
      controls, empty state, and pager at each step).
- [ ] Integration case: the exact parameter sets the URL mapping produces
      round-trip through `getBooks` against the live Flask process.
- [ ] Finalize `docs/development/book-discovery.md` (URL state section) and
      refresh the root `README.md`.

Risks: router-sync bugs classically appear as feedback loops (state → URL →
state); the mapping must be idempotent and tested for loops. Restore-before-
fetch ordering matters for the first paint; the combined scenario asserts it.
Invalid-state behavior is blocked until Q4 is approved.

### Implementation decisions and open questions

- One mapping function owns state ↔ query serialization in the component;
  `040` does not re-implement per-param logic from earlier slices.
- Restore resolves invalid/out-of-range values before fetching so the first
  request already carries the corrected state (per approved Q4).
- No new open questions originate here beyond main-file Q1–Q7.

### Documentation

- Finalizes `docs/development/book-discovery.md` with the URL state contract
  (parameters, defaults omitted, restore rules) and refreshes the root
  `README.md` so its Books page description covers the completed capability
  set — claims added only for behavior this change makes true.

### Task checklist

- [ ] Route-query mapping, restore, and navigation reactivity implemented.
- [ ] Push/replace writing and default-omission implemented.
- [ ] Invalid/out-of-range restore behavior implemented per approved Q4.
- [ ] Component tests including the decisive combined scenario added and
      passing.
- [ ] Integration round-trip case added and passing.
- [ ] Spec page finalized; README refreshed.

### Requirement verification

- URL serialize/restore → component tests with memory-history router through
  the real router: mounting on `/books?read=false&q=dune&page=2` restores
  controls, table, and pager; default state yields a clean URL.
- Browser navigation → component tests driving `router.push`/`router.back()`:
  each navigation restores a consistent view (decisive evidence for the
  navigation requirement; real browser E2E stays out of scope as recorded in
  the main file).
- Invalid/out-of-range restore → component tests asserting the approved Q4
  outcomes.
- Controls-in-sync → component tests asserting control values match the URL
  after restore and after navigation, in both directions.
- CRUD-after-restore → component test: mutate following a restored view and
  assert the refetch reuses the restored query with clamping per Q7.
- Shared-state round-trip → integration case: parameter sets produced by the
  URL mapping against the live Flask process return the expected envelopes —
  proves the mapping and the server agree over real HTTP.
- Combined view consistency → the decisive all-states scenario test listed in
  the tasks, crossing the real component + real router with the api module
  mocked at the transport boundary.
- Documentation currency → spec and README statements match landed behavior in
  the same change.