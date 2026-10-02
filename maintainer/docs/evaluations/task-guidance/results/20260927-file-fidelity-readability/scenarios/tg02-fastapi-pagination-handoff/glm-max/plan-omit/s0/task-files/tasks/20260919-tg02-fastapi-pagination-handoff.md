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
`src/tests/test_notes.py`. Current collection responses are plain arrays.
Exact ORM/SQL construction is not prescribed. Behavior when only one
pagination parameter is supplied remains a requirement question.