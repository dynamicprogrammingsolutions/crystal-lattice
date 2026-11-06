# Preserve the Selected Book Filter During CRUD Refresh

Fix the full-stack refresh regression without changing existing contracts.

## Requirements checklist

- [ ] `REFRESH-1`: All/Read/Unread selection remains active after add, update,
  and delete refreshes.
- [ ] `REFRESH-2`: Mutation refreshes use the selected filter through the
  production client transport and Flask route.
- [ ] `REFRESH-3`: The visible active choice, results, and empty state match
  the refreshed filtered response.
- [ ] `REFRESH-4`: Existing CRUD success, response shape, and unfiltered
  behavior remain compatible.

## Supporting details

Normal filter selection already works. The regression is in mutation methods
inside `client/src/components/Books.vue`, which call `getBooks()` without the
selected filter. Filter encoding is owned by `client/src/api/books.js`; the
Flask route already accepts it.

## Execution plan

Status: Draft

Trace the shared filtered-fetch path, route every mutation refresh through that
path while preserving current filter state, and verify representative CRUD
refreshes through the production client transport and Flask response.

### Implementation decisions and open questions

No requirement question is open. Choose the smallest local state/fetch reuse
that preserves the existing public behavior.

### Documentation

No user documentation change is expected for this regression fix.

### Task checklist

- [ ] Confirm all mutation refresh call paths.
- [ ] Reuse one filter-aware collection refresh path.
- [ ] Verify visible active state, results, and empty state.
- [ ] Add focused CRUD and production-crossing regressions.

### Requirement verification

- `REFRESH-1`–`REFRESH-3`: representative add/update/delete refreshes preserve
  the selected filter through the real client/HTTP path and render the result.
- `REFRESH-4`: existing CRUD and unfiltered regressions remain green.