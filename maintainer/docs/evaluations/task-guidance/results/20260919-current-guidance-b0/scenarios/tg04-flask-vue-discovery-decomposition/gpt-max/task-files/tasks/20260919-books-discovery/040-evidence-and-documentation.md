# Verify and document Books discovery behavior

Plan the cross-boundary evidence and maintained documentation update needed to make the Books discovery feature reviewable and current once implementation is approved.

Parent Task: tasks/20260919-books-discovery/000-main.md
Depends On: tasks/20260919-books-discovery/010-api-discovery-contract.md, tasks/20260919-books-discovery/020-client-discovery-state.md, tasks/20260919-books-discovery/030-url-history-and-refresh.md

## Requirements checklist

- [ ] API tests prove filtering, title/author search, bounded pagination, empty results, and no-query compatibility at the Flask route boundary.
- [ ] Client tests prove active controls, table/page rendering, empty-state consistency, URL restoration, browser navigation, and CRUD refreshes.
- [ ] Regression evidence proves existing add/update/delete operations and unfiltered loading remain available.
- [ ] Maintained development documentation describes the verified supported discovery behavior and URL contract after implementation.

## Research and supporting facts

- Python tests live under `tests/` and use the Flask test client fixture in `tests/conftest.py`.
- JavaScript tests live under `client/tests/` and run with `vitest run`; current component coverage mocks the API and has no router integration harness.
- `client/tests/books.integration.js` explicitly records that production transport integration coverage does not yet exist.
- `docs/development/index.md` is the current development documentation index and currently says no book-discovery specification exists.

## Execution plan

Status: Draft

Keep evidence at the smallest boundary that proves each requirement. Extend the Flask test-client suite for the public API contract and compatibility. Extend component tests for local state and rendering. Add a router-backed integration test with a realistic memory-history setup for URL restoration and browser navigation, and include the real API adapter boundary where query parameter wiring is part of the claim rather than mocking it away.

Organize regression cases around user-visible transitions: default unfiltered load, filter/search change, first/last page movement, no matches, direct shared URL, back/forward, add/update/delete while filtered, and a mutation that invalidates the current page. Assert both state/request facts and visible output so a passing test cannot hide a stale table or URL.

After implementation passes the focused tests, update the smallest maintained documentation location. Replace the current “no book-discovery specification exists” statement with verified guidance or link to a focused page only if the behavior needs a longer contract. Include the final status values, search semantics, pagination parameters/metadata, URL example, browser restoration, and CRUD-refresh behavior. Record any gated test that could not be run rather than implying completion.

### Implementation decisions and open questions

- Decision: verification must cross the Flask route, Vue rendering, and router/history boundaries; isolated mocks alone are not sufficient for the URL/transport claims.
- Decision: documentation is updated only after behavior is implemented and evidence passes.
- Open: test fixtures, query names, and exact user-facing copy must follow the approved parent/API/client decisions.
- Recommendation: keep the no-match and page-boundary cases explicit in both API and UI coverage because they are the most likely places for stale controls or out-of-range URLs.

### Documentation

- Planned target: `docs/development/index.md`, with a new focused feature page only if the final contract exceeds the index’s intended scope.
- Document only verified current behavior; do not turn this Draft plan into user guidance.
- Include a concise example of a shareable `/books` URL and explain how browser navigation and CRUD refreshes preserve discovery state.

### Task checklist

- [ ] Map each approved requirement to an API, component, or router-backed test.
- [ ] Add regression cases for unfiltered GET and existing CRUD behavior.
- [ ] Add focused edge cases for empty results, page bounds, invalid URLs, and mutation membership changes according to the approved policy.
- [ ] Run the applicable Python and Vitest suites and record the actual commands/results.
- [ ] Update the maintained documentation after implementation and verification.

### Requirement verification

- API discovery requirements: Flask test-client suite with real route parsing and response assertions.
- UI consistency requirements: Vue component suite asserting active controls, current-page rows, pagination bounds, and empty state together.
- URL/history requirements: router-backed integration suite using memory history and actual route query transitions.
- CRUD/compatibility requirements: mutation regression suite plus no-query GET coverage, with the selected discovery query retained during refresh.
- Documentation requirement: human review of the updated maintained page against the verified test-backed contract.