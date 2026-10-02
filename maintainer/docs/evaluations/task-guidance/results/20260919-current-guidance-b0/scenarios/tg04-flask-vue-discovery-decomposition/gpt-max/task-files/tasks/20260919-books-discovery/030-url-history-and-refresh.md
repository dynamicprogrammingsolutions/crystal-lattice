# Synchronize Books discovery with URL history and CRUD refreshes

Plan the router integration that shares and restores Books discovery state, handles browser navigation, and keeps mutation refreshes aligned with the selected view.

Parent Task: tasks/20260919-books-discovery/000-main.md
Depends On: tasks/20260919-books-discovery/020-client-discovery-state.md

## Requirements checklist

- [ ] A `/books` URL can encode the approved discovery state and restore it on direct entry and reload.
- [ ] User changes update the URL without losing the displayed controls or producing router/component synchronization loops.
- [ ] Browser back and forward restore the corresponding discovery state and reload the matching result page.
- [ ] Add, update, and delete refresh the current discovery query and reconcile page/URL changes if the result set changes.
- [ ] Existing `/books` navigation and CRUD endpoints remain usable when the URL has no discovery query.

## Research and supporting facts

- `client/src/router.js` uses `createWebHistory` and declares only the `/books` route; query handling is currently implicit and untested.
- `client/src/components/Books.vue` owns the current mutation methods, so the component and router need a deliberate synchronization boundary rather than independent URL and local state.
- The current API methods reload without parameters after mutations, which would discard any future filter/search/page selection.

## Execution plan

Status: Draft

Define a single parse/serialize mapping between the canonical component state and the `/books` query string. On route entry or a browser history event, parse and normalize the query before loading data. On a user state change, update the route and let the route-selected state drive the request, avoiding a second competing local copy. Normalize equivalent default values consistently so shared links remain stable.

Separate initial/programmatic route synchronization from user-originated navigation to avoid update loops. Test the chosen history policy with a memory history/router harness: direct query entry restores controls and data; a user transition changes the URL; back/forward restores prior selections and causes the correct GET request. Apply the approved search debounce/commit policy so typing does not unexpectedly create excessive history entries.

Route all add/update/delete follow-up loads through the same canonical state and URL-aware loader. If a mutation removes the last item from the current page or changes an item’s membership in the active filter, apply the approved page-normalization policy and update the URL before asserting the final table and empty state. Keep mutation endpoint calls and payloads unchanged.

### Implementation decisions and open questions

- Decision: `/books` query parameters are the shareable source for discovery state; no separate storage mechanism is in scope.
- Decision: browser back/forward must be treated as state changes that reload data, not merely as URL changes.
- Open: exact serialization names/default omission, history granularity for search, and invalid/out-of-range normalization follow the parent task.
- Recommendation: push committed filter/page changes, use a debounced or committed search transition, and replace only canonicalization of an equivalent/default query.

### Documentation

- Document a copyable `/books` query example, restoration behavior, and the mutation-refresh rule after the URL contract is implemented and verified.
- Keep the current development documentation unchanged during planning.

### Task checklist

- [ ] Define the canonical query parser and serializer, including defaults and invalid values.
- [ ] Define the route-entry, user-change, and back/forward event flow.
- [ ] Define history behavior for filter, search, and page transitions.
- [ ] Define mutation refresh and page/URL reconciliation behavior.
- [ ] Plan router-backed tests for direct links, reload-equivalent entry, back/forward, and CRUD refreshes.

### Requirement verification

- Share/restore behavior: router-backed test starting at a fully specified `/books` query and asserting restored controls, request parameters, and rows.
- Browser navigation: memory-history test creating at least two discovery states, navigating back and forward, and asserting both URL and loaded result.
- CRUD consistency: integration test performing each mutation while a non-default discovery query is active and asserting the follow-up query, final URL, page bounds, and table/empty state.
- Legacy navigation: test entering `/books` without a query and confirming the existing default view still loads.