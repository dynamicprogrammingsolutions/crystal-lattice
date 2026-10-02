# Deliver the Books discovery state and URL experience

Connect the approved discovery API to the Vue Books page so controls, results, pagination, URL navigation, empty states, and CRUD refreshes remain one consistent view.

Parent Task: `tasks/20260925-books-discovery/000-main.md`

Depends On: `tasks/20260925-books-discovery/010-api-discovery-contract.md`

## Requirements checklist

- [ ] The Books page exposes the approved read-status filter and title/author search controls.
- [ ] The table renders the selected page, while active controls and pagination reflect the same selected state and response metadata.
- [ ] A no-match or empty collection state is clear and corresponds to the active filter/search view.
- [ ] Discovery state is encoded in the approved `/books` URL query format and can initialize the page from a shared URL.
- [ ] Browser back/forward navigation restores both the URL state and the displayed results.
- [ ] Add, update, and delete retain their existing behavior and refresh the currently selected discovery view.
- [ ] Changes to the result set reconcile the current page according to the approved out-of-range policy.

## Unresolved requirement questions

- Use the parent-approved query names, status values, page size, history semantics, and out-of-range behavior; this task must not choose incompatible client-only defaults.
- Confirm whether search requests update on each keystroke or on an explicit submit; this is user-visible and should be agreed before implementation.
- Confirm whether control changes should reset to the first page; this is the recommended behavior for a new filter/search but needs approval if it is part of the URL contract.

## Research and supporting facts

- `client/src/components/Books.vue` currently has only `books` data and repeats an unfiltered `getBooks()` call after each mutation.
- `client/src/api/books.js` already accepts `getBooks(params)`, so this task should preserve that public client helper and make parameter construction explicit and testable.
- `client/src/router.js` uses a `/books` route with web history, but the component currently neither reads nor writes route queries.
- `client/tests/Books.spec.js` mocks the API module and covers only the empty state; `client/tests/books.integration.js` is an unused placeholder.
- The page must preserve its existing CRUD methods while changing the fetch path to use current discovery state.

## Execution plan

Status: Draft

Use one normalized discovery-state model for the route query, API parameters, active-control rendering, pagination controls, and refreshes. On initial mount and every relevant route-query change, parse the approved URL state, request the corresponding page through `getBooks`, and render the response. Control interactions should update the router according to the approved history policy; browser navigation should therefore enter the same watcher/fetch path rather than maintaining a second local state machine.

Keep query-state normalization in small testable functions or methods owned by the page/client boundary. Keep the table dependent on the fetched page rather than locally filtering a full collection, so page counts and empty states come from the server’s selected view. After each add/update/delete, re-fetch with the current route query and apply the approved page reconciliation when the mutation changes the available result set.

Expand `client/tests/Books.spec.js` for controls, active values, table rows, page bounds, no-match rendering, route initialization, and back/forward behavior. Replace the integration placeholder with a production-transport check: mount the real Books component with the real API client and run it against a running Flask app, so the check crosses component, Axios transport, HTTP route, query selection, and response rendering. Keep mocked component tests for focused state/rendering cases, but do not treat them as the decisive cross-boundary evidence.

### Implementation decisions and open questions

- URL state and page state remain one owned feature because a discovery change must drive both navigation and fetching, and CRUD refreshes must preserve both.
- The existing CRUD API helpers and mutation methods remain the compatibility boundary.
- The exact URL/history policy, submit/debounce behavior, page-reset rule, and out-of-range reconciliation are parent-level questions.

### Documentation

- Contribute the verified control names, URL examples, navigation behavior, empty-state meaning, and CRUD refresh behavior to the maintained Books discovery documentation.
- Include a share/restore example only after the real router/API integration check passes.

### Task checklist

- [ ] Consume the approved API contract from `010-api-discovery-contract.md`.
- [ ] Implement normalized discovery state, controls, active state, table/empty rendering, and bounded pagination.
- [ ] Synchronize the state with the Books route and browser history.
- [ ] Preserve CRUD calls and refresh the selected view after each mutation.
- [ ] Add focused component/router tests and the real Flask transport integration check.
- [ ] Record verification and documentation evidence for the parent task.

### Requirement verification

- Controls, active state, table, pagination, and no-match state: focused Vue component tests with API responses representing multiple pages and zero matches.
- URL restoration and browser navigation: router-mounted test starting from a query URL, changing state, then traversing history and asserting requests/rendered rows.
- CRUD refresh consistency: production-transport integration test with a non-default query active while creating, updating, and deleting a record.
- Full connection: exact integration invocation should start Flask with `python -m flask --app server.app run --port 5000` and run the client integration test against that process; record any environment-specific setup needed for the repository’s test runner.