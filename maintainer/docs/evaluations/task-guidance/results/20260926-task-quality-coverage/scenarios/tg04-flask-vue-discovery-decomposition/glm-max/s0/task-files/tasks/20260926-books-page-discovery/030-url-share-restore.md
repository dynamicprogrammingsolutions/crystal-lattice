# URL state sharing and restore (deep links, browser navigation)

Bind the 020 view state to the `/books` URL: encode the current discovery
state in query params, restore it from shared or deep links while normalizing
invalid values, keep browser back/forward and CRUD/clamp transitions
consistent with the URL, and complete the discovery documentation.

Parent Task: tasks/20260926-books-page-discovery/000-main.md

Depends On: tasks/20260926-books-page-discovery/010-server-discovery-api.md,
tasks/20260926-books-page-discovery/020-client-discovery-view.md

## Requirements checklist

- [ ] U1 — The current view (read filter, search text, page) is encoded in
      `/books` query params per parent D5; non-default state yields a
      shareable URL; the default view keeps the URL clean.
- [ ] U2 — Opening `/books` with query params restores the view: controls,
      table, and fetch reflect the encoded state; invalid values normalize to
      defaults without errors (parents D4/D5).
- [ ] U3 — Browser back/forward keeps the table, active controls, and loaded
      data consistent with the URL state (R5).
- [ ] U4 — CRUD refreshes and page clamping keep the URL in sync with the
      view actually rendered (R7 extended to the URL).
- [ ] U5 — Evidence: component tests with the real router (restore,
      normalization, back/forward, sync) plus an integration deep-link case
      through the real server for the full production restore path.

## Execution plan

Status: Draft

Design: the route query is the single source of truth for the 020 view object.
A watcher maps `route.query` → view (normalizing invalid values), and applied
view changes map back to router navigation: `push` on applied filter/search/
page changes (parent D6, so back/forward walks result states) and `replace`
when normalizing on load, so no spurious history entries appear. Restores
drive `refresh()` through the same path as control changes, so table,
controls, and empty state stay consistent by construction (R6). Back/forward
is exercised through the real history-mode router.

Steps:

1. Implement query → view parsing and normalization (absent/invalid `read`,
   `q`, `page` → defaults; `replace`-clean the URL when normalization
   occurred).
2. Implement view → URL sync (`push` on applied changes per D6; the default
   view keeps a clean URL).
3. Route restores and back/forward drive `refresh()` through the 020 path;
   CRUD and clamp transitions propagate to the URL.
4. Component tests with the real router (extend
   `client/tests/Books.spec.js`): deep-link restore (read/q/page applied with
   consistent controls and rows), invalid-param normalization (URL cleaned,
   defaults applied), back/forward stepping between applied states, and URL
   sync after CRUD and clamp.
5. Integration: extend `client/tests/books.integration.js` with a deep-link
   case — encoded URL → real router → real fetch → filtered rows from the
   real server — completing the full production path for R4.
6. Docs: URL-state section in `docs/development/index.md`; README sentence
   for shareable/restorable state.

### Implementation decisions and open questions

- Parent decisions D5 (encoding) and D6 (push/replace policy) govern;
  child-local, reversible choices: the exact normalization rules (invalid
  read token, non-numeric or negative page → default).
- If jsdom cannot exercise real history back/forward, do not silently
  substitute a memory router (it is not the production path): record the gap
  and name the manual check — exact steps — needed to evidence U3 through the
  real components, per the parent plan's named-check rule for R5.

### Documentation

- Add the URL-state section to `docs/development/index.md` and the README
  shareable-state sentence, in the same change as the behavior, per the
  parent plan's `### Documentation` section.

### Task checklist

- [ ] Query → view parsing and normalization implemented.
- [ ] View → URL sync (push/replace policy) implemented.
- [ ] Restores, back/forward, and CRUD/clamp consistency wired through
      `refresh()`.
- [ ] Component tests per U5 added; suite passes.
- [ ] Integration deep-link case added; suite passes.
- [ ] Docs and README updated.

### Requirement verification

- U1 → decisive: component test asserting the URL after applying non-default
  state (encoded per D5) and a clean URL for the default view.
- U2 → decisive: component test mounting at a deep-linked URL asserting
  controls, emitted fetch params, and rows; plus a normalization case for
  invalid values.
- U3 → decisive: component test with the real history-mode router stepping
  back/forward and asserting view plus refetch; if that proves impossible in
  jsdom, the manually named check above.
- U4 → decisive: component test asserting the query string after CRUD refresh
  and after an out-of-range clamp.
- U5 integration → decisive for the R4 full path: shared URL → real router →
  real transport → real server → rendered filtered rows.

### Additional implementation verification

- Run the full client suite (component + integration) once to confirm all
  URL-state and view suites collect and exit cleanly together, with the
  harness still runnable via `npm test`.