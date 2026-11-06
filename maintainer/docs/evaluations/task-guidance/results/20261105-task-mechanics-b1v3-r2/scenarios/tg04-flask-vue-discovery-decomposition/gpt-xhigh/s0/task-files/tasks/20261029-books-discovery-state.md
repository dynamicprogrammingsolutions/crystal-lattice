# Books Discovery State

Make the Books page usable for larger collections with read-status filtering,
title/author search, bounded pagination, and URL-restorable discovery state,
while keeping the existing CRUD flow and unfiltered API behavior compatible.

## Requirements checklist

- [ ] Let users filter books by read status, search by title or author, and move
  only among valid result pages.
- [ ] Encode the current discovery state in the URL and restore it on reload and
  browser back/forward navigation.
- [ ] Keep the table, active controls, empty state, and results refreshed after
  CRUD operations consistent with that discovery state.
- [ ] Preserve existing CRUD behavior and the unfiltered `GET /books` API
  contract.

## Open questions

- **API and URL contract:** Should filtering and pagination be performed by the
  Flask API or in the client, and what query keys and filtered-response shape
  should be used? Recommendation: server-side selection with optional query
  parameters; keep the no-parameter response unchanged and include page metadata
  only for discovery requests.
- **Search and status semantics:** Should status choices be All, Read, and
  Unread, and should search be a case-insensitive partial match against either
  title or author? Recommendation: yes to both.
- **Page behavior:** What page size and numbering convention should be used, and
  should changing search/status reset to the first page? Recommendation: a
  fixed page size of 20, one-based page numbers, and reset to page one when
  search or status changes.
- **Invalid or stale pages:** How should invalid URL pages and pages made
  out-of-range by CRUD changes be handled? Recommendation: normalize to the
  nearest valid page and update the URL.

## Research and supporting facts

- `client/src/components/Books.vue` currently loads all books on mount and
  reloads all books after add, update, and delete. It has only a table and the
  “No books found.” empty state.
- `client/src/api/books.js` already lets `getBooks` pass optional query
  parameters.
- `server/app.py` currently returns `{"status": "success", "books": BOOKS}` for
  `GET /books`; its POST, PUT, and DELETE routes implement the current CRUD
  behavior.
- `server/query.py` currently returns a copy of the full list and is not used
  by the route.
- Existing client coverage is a mocked empty-state component test;
  `client/tests/books.integration.js` is a placeholder. API tests cover basic
  list and mutation status codes but not response compatibility or discovery.
- The router is Vue Router history mode. There is no existing client README or
  full browser-backed integration harness; the root `README.md` is the current
  user-facing project overview.

## Execution plan

Status: Draft

Treat a single discovery view as the unit of delivery: the URL carries the
selected search, status, and page; the Books page renders that state and asks
the API for the matching page; and every successful mutation refreshes the
same view. The recommended API design adds optional server-side filtering and
pagination while leaving the current no-parameter response unchanged. Keep
existing mutation endpoints and payloads intact. Finalize the open API and
behavior choices before implementing them.

The decisive cross-boundary check is
`client/tests/books.integration.js`: run the actual Books component with the
configured Vue Router and Axios transport against a real Flask HTTP service,
without mocking the books API. Verify filter/search/page selection, URL
reload and back/forward restoration, and a CRUD mutation that refreshes the
selected results. Make the test self-contained by managing its Flask service.
Run it with `cd client && npm test -- tests/books.integration.js`. Focused API
tests supplement this check but do not replace it.

### Implementation decisions and open questions

The four questions above remain unresolved and need approval before execution.
The recommendations are a proposed direction, not approved API or user-visible
behavior. Keep the single end-to-end task: the client state, route, transport,
and API selection are one connected user capability in this fixture.

### Documentation

Update the existing root `README.md` for Books page users with the confirmed
filter, search, pagination, and URL-restoration behavior. Do not create a
separate discovery specification or documentation structure for this feature.

### Task checklist

- [ ] Resolve the discovery API and URL contract and behavior questions.
- [ ] Add optional API filtering and bounded pagination without changing
  unfiltered `GET /books` behavior or CRUD endpoints.
- [ ] Synchronize Books controls, data, URL navigation, and CRUD refreshes.
- [ ] Add focused API and client tests plus the decisive real-service
  integration check.
- [ ] Update the root README with verified user guidance.

### Requirement verification

- Requirements 1–3: the named `client/tests/books.integration.js` check must
  exercise the real Books component, configured router, Axios transport, and
  Flask API together, including browser history and post-mutation refresh.
- Requirement 4: assert the exact existing no-parameter `GET /books` response
  shape in `tests/test_books_api.py`, and verify existing CRUD operations
  remain successful; the real-service integration check also confirms the
  client still uses that compatible path.