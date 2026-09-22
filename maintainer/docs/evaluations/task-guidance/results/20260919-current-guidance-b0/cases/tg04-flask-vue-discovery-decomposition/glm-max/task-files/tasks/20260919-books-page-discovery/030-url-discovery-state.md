# URL share/restore for Books discovery state

Encode the selected discovery state (filter, search, page) in the `/books`
URL so it can be shared and restored, keep browser back/forward consistent
with the view, and keep the controls in sync with restored state.
Independently useful: any discovery view is shareable by link.

Parent Task: tasks/20260919-books-page-discovery/000-main.md
Depends On: tasks/20260919-books-page-discovery/020-books-page-discovery-controls.md

## Requirements checklist

- [ ] The current discovery state is encoded in the `/books` URL query.
- [ ] Opening a URL that carries discovery state restores the same view; the table, active controls, and empty state match the restored state.
- [ ] Browser back/forward moves between discovery states with the view, controls, and empty state kept consistent.
- [ ] Committed control changes update the URL; defaults keep the URL clean (no discovery params).
- [ ] Invalid or unknown URL values do not break restore (handled per the approved invalid-value rule).
- [ ] The URL share/restore slice of the discovery documentation is updated in the same change.

## Supporting facts

- The router is vue-router 4 with `createWebHistory` and a single `/books`
  route (`client/src/router.js`); the route query is the natural state carrier
  and requires no new dependency.
- Vue Test Utils can mount against a router built with `createMemoryHistory`
  to exercise restore and popstate-style navigation without a browser.
- Existing tests cover neither routing nor URL state.

## Execution plan

Status: Draft

Make the route query the single source of truth for discovery state:
initialize from the route, write committed changes with `push` (live typing
excluded) and normalization/clamping with `replace`, and react to route-query
changes (including back/forward) by updating the view and controls from the
query. Unknown or invalid values normalize to defaults per the approved rule
(main-task D6). Guard against update loops (route watcher vs control writer).

Verification: component tests mounting `Books` with a memory-history router —
restore from an initial query, URL updates on committed changes, back/forward
restores prior states with controls and table consistent, and invalid values
normalize. This crosses the real router boundary for history behavior without
a browser harness; no end-to-end harness is added in this task.

### Implementation decisions and open questions

- Push vs replace and default omission follow main-task D3/D4; invalid-value
  handling follows D6 — all recommendation-level until approved.
- Local choice: normalization happens at the read boundary so restored and
  control-driven state pass through one code path.

### Documentation

Update `docs/development/index.md`: document the URL parameter encoding,
default omission, and back/forward behavior.

### Task checklist

- [ ] Route-query state binding in `Books.vue` (single source of truth)
- [ ] Push/replace handling for committed changes and normalization
- [ ] Component tests: restore, URL update, back/forward consistency, invalid values
- [ ] URL behavior documented

### Requirement verification

- Restore and navigation consistency → memory-history router component tests
  (the real vue-router boundary for history transitions; no browser-level
  end-to-end exists today and none is planned in this task).