# 040 — Discovery state share/restore and browser navigation

Complete R4 at the whole-view level: the combined discovery state (read status, search, page) is shareable and restorable through the URL, control changes produce consistent history entries, and browser back/forward and CRUD refreshes always show a view consistent with the URL state. This subtask also closes the combined facets of R5.

Parent Task: tasks/20260925-books-discovery/000-main.md
Depends On: tasks/20260925-books-discovery/010-read-status-filter.md
Depends On: tasks/20260925-books-discovery/020-title-author-search.md
Depends On: tasks/20260925-books-discovery/030-pagination.md

## Requirements checklist

- [ ] A URL carrying any combination of `read`, `q`, and `page` restores the exact view — table rows, active controls, empty state, and pager — on fresh load, refresh, or paste-in.
- [ ] Control changes produce the approved history entries (push for read-status and page changes; debounced replace for search typing), and back/forward always lands on a view consistent with the stored URL state.
- [ ] CRUD under a combined state keeps the view consistent (refresh with current params, clamped where results shrank).
- [ ] Combined-state consistency of table, active controls, empty state, navigation, and CRUD refresh verified end to end.

## Supporting details

- 010–030 encode and restore their individual params; this subtask owns the combined contract and the navigation-semantics check.
- History semantics are decided in the parent plan (material decision pending approval).
- The live harness from 010 is reused; jsdom + vue-router history support automated back/forward via `router.go`.
- No manual browser check is defined in this fixture; the automated live path traverses router, axios transport, Flask routing, and query selection together.

## Execution plan

Status: Draft

1. Audit combined-state write paths in `Books.vue` for consistency with the approved history semantics; adjust any param written with the wrong semantics.
2. Decisive live-path test: set filter + search + page through real controls → URL contains all three; `router.back()` / `forward()` restore prior views; a fresh mount of the combined URL restores rows, controls, and pager; deleting a book under the combined state keeps the view consistent (clamped if needed).
3. Sweep empty-state and control consistency across combined states (filter+search with zero matches; page reset transitions).
4. Docs: README gains the user-facing share/restore note (URL format and what a shared link restores).

### Implementation decisions and open questions

- Material (pending approval, parent plan): history semantics; the combined URL format is simply the union of the per-feature params (no additional state or tokens).
- No unresolved requirement-level questions.

### Documentation

- README share/restore usage note; same change as the behavior.

### Task checklist

- [ ] Combined URL contract verified and (if needed) corrected in the shared query-state sync
- [ ] Decisive live-path test (combined restore, back/forward, CRUD under combined state)
- [ ] README share/restore note

### Requirement verification

- Decisive (R4 + combined facets of R5): live-path test — combined-state fresh-load restore, back/forward traversal, and CRUD refresh under combined state, through real router + axios + Flask.
- Supporting: re-run of 010–030 decisive tests to confirm no regression.

### Additional implementation verification

- Re-run the full pytest and vitest suites as the final parent-level gate.