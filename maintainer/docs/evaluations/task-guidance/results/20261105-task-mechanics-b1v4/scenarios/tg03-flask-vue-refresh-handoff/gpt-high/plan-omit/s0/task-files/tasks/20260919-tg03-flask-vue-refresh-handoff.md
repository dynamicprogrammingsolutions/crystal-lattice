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

Normal filter selection already works. Mutation methods in
`client/src/components/Books.vue` call `getBooks()` without the selected
filter. Filter encoding lives in `client/src/api/books.js`; the Flask route
already accepts it. The fix must retain the production client-to-server
crossing and preserve existing contracts.