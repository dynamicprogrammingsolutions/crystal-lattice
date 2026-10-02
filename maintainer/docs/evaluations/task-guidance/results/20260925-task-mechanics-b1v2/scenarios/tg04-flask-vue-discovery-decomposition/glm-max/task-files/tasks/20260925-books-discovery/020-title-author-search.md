# 020 — Title/author search

Deliver title/author search end to end: `/books` accepts `q`, matching case-insensitive substrings in title or author, combined (AND) with the read-status filter; the Books page gains a search control whose value is shared and restored through the URL, with table, active controls, empty state, and CRUD refreshes staying consistent.

Parent Task: tasks/20260925-books-discovery/000-main.md
Depends On: tasks/20260925-books-discovery/010-read-status-filter.md (search combines with the read filter and reuses the live harness and query-state sync)

## Requirements checklist

- [ ] `GET /books?q=…` returns books whose title or author contains the term (case-insensitive); combined with `read`, both conditions apply.
- [ ] The Books page offers a search input; the table, empty state, and active search reflect the entered term; the read filter and search can be active together.
- [ ] The URL encodes `q`; opening a URL with `?q=…` (alone or with `read`) restores the view; typing updates the URL per the approved history semantics.
- [ ] CRUD refreshes preserve both active controls and the filtered view.

## Supporting details

- Same fetch/refresh seams as 010; the derived state becomes `{read, q}` from `route.query`.
- Matching is a single-term substring, case-insensitive, against either field; no ranking or tokenization.
- The live harness from 010 is reused; no new transport setup.

## Execution plan

Status: Draft

1. Server: `server/query.py` applies `q` after the read filter; pytest covers title match, author match, case-insensitivity, combination, and unfiltered compatibility.
2. Client: search input bound to `route.query.q` (debounced `router.replace` per approved semantics); fetch includes `{read, q}`; the empty state reuses the filtered-no-match message.
3. Tests: component spec for input and active-control consistency; decisive live-path test — type a term, assert the filtered table and URL; combine with `?read=…`; fresh load restores both.
4. Docs: README Books API section gains `q` in the same change.

### Implementation decisions and open questions

- Material (pending approval, parent plan): `q` as case-insensitive substring over title OR author; single term.
- Local: debounce interval (≈250 ms); whitespace-only terms treated as absent. Reversible.

### Documentation

- README Books API section: `q` semantics and combination with `read`.

### Task checklist

- [ ] Server `q` selection + combination semantics + pytest tests
- [ ] Client search control with debounced URL write-back and combined fetch
- [ ] Decisive live-path test (search alone, combined with filter, restore)
- [ ] README updated

### Requirement verification

- Decisive (R2; URL facets of R4): live-path test through real router + axios + Flask — search filters rows through the full path; combined filter+search matches AND semantics; a fresh mount with `?read=false&q=…` restores the table and both controls.
- Supporting: pytest route tests and `server/query.py` unit tests; component spec.

### Additional implementation verification

- Confirm a search matching nothing returns `total: 0` (once 030 adds the envelope) without breaking the empty-state path that exists after 010.