# Add Optional Notes Pagination

Add a bounded collection query while preserving existing API compatibility.

## Requirements checklist

- [ ] `NOTES-1`: `GET /notes/` accepts optional validated limit and offset
  controls.
- [ ] `NOTES-2`: Unparameterized requests preserve the full-list array
  behavior.
- [ ] `NOTES-3`: Requested slices use stable ascending note-ID order.
- [ ] `NOTES-4`: Paginated responses retain the note array and expose total
  count in a response header.
- [ ] `NOTES-5`: Invalid values use normal FastAPI validation.
- [ ] `NOTES-6`: Create, item-read, update, and delete behavior remains
  compatible.

## Supporting details

The public route is in `src/app/api/notes.py`; storage behavior is in
`src/app/api/crud.py`; current route coverage is in
`src/tests/test_notes.py`. Exact ORM/SQL construction is not prescribed.
Behavior when only one pagination parameter is supplied remains a requirement
question.

## Execution plan

Status: Draft

Inspect route and storage behavior, resolve omitted-companion semantics, add
the approved query contract without changing the array response, and verify
ordering, slicing, total count, validation, unparameterized compatibility, and
the unaffected CRUD routes through public HTTP behavior.

### Implementation decisions and open questions

- Requirement question: approve behavior when only limit or only offset is
  present.
- Resolve query construction locally after the public behavior is approved.

### Documentation

Update maintained API documentation for the approved query and header behavior.

### Task checklist

- [ ] Inspect the public route, storage boundary, and existing coverage.
- [ ] Resolve the omitted-companion public behavior.
- [ ] Implement the validated compatible pagination contract.
- [ ] Add decisive route/storage and CRUD regression evidence.
- [ ] Update affected API documentation.

### Requirement verification

- `NOTES-1`–`NOTES-5`: public HTTP tests with representative normal, boundary,
  and invalid requests backed by real ordering/count behavior.
- `NOTES-2` and `NOTES-6`: focused compatibility regressions.