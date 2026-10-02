# 030 — Bounded pagination

Deliver server-side pagination with a bounded page size: `/books` accepts `page` (with a fixed `per_page`), returns additive paging metadata, and the Books page gains a pager. The page is encoded in the URL, resets when filter or search changes, and clamps when results shrink, so the pager, table, controls, and empty state stay consistent through CRUD and navigation.

Parent Task: tasks/20260925-books-discovery/000-main.md
Depends On: tasks/20260925-books-discovery/010-read-status-filter.md
Depends On: tasks/20260925-books-discovery/020-title-author-search.md (page reset on control changes and paging over filtered/searched results)

## Requirements checklist

- [ ] `GET /books` supports `page` with a fixed bounded `per_page` and returns `total`, `page`, `per_page` metadata alongside `books`; the returned slice is correct for any filter/search combination.
- [ ] The Books page shows Prev/Next controls and the current range ("Page X of Y"); navigation moves through bounded pages and updates the URL.
- [ ] Changing read status or search resets the page to 1; a page beyond the last (deep link or after deletes) clamps to the nearest valid page.
- [ ] Opening a URL with `?page=…` restores the paged view; CRUD refreshes preserve the page while still valid (clamped when results shrink).
- [ ] Unfiltered requests keep returning the full list with the existing envelope fields (additive metadata only).

## Supporting details

- The server envelope today is `{status, books}`; paging metadata is additive and must not change the `books` contract.
- Seed data is two books; tests seed additional books through the real POST endpoint (e.g., 12 total) rather than altering production seeds.
- History semantics for page changes come from the approved parent decision (push).

## Execution plan

Status: Draft

1. Server: `server/query.py` slices after filtering and searching; clamp `page` to `[1, last_page]` and `per_page` to bounds; `server/app.py` adds `total`/`page`/`per_page` to the response. pytest covers slicing, totals, bounds, combination with `read`+`q`, and unchanged unfiltered behavior.
2. Client: pager derived from the response metadata; page changes write `?page=…` via `router.push`; a watch on `read`/`q` resets the page; fetch params become `{read, q, page}`; CRUD refresh passes the current params (the server clamps when results shrink).
3. The pager is hidden while a filtered/searched result set is empty (the empty state takes over); visible and consistent otherwise.
4. Tests: component spec for pager states; decisive live-path test — page through seeded results; delete the last item of the last page → clamped consistent view; change filter → page resets; fresh load of `?page=2` restores.
5. Docs: README Books API section documents the paging params and envelope; Books-page notes document the pager.

### Implementation decisions and open questions

- Material (pending approval, parent plan): default `per_page` 5 with max 50; clamping instead of 400; no page-size control.
- Local: pager control set (Prev/Next + indicator; no numbered jump list). Reversible.

### Documentation

- README paging contract and pager usage notes; same change as the behavior.

### Task checklist

- [ ] Server paging envelope + clamping + compatibility tests
- [ ] Client pager, URL write/read, reset-on-change, clamp-through-CRUD
- [ ] Decisive live-path test (navigation, reset, clamp, restore)
- [ ] README updated

### Requirement verification

- Decisive (R3): live-path test — Prev/Next through the real path changes rows and URL; a filter change resets to page 1; deleting the last item on the last page clamps the view consistently; a fresh mount with `?read=…&q=…&page=2` restores the paged view.
- Supporting: pytest envelope/bounds/combination tests; component spec.

### Additional implementation verification

- Re-run the existing pytest suite unmodified: the additive envelope change must not alter `{status, books}` semantics for unfiltered calls (R6).