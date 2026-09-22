# Implement notes collection pagination

Define the API and database-query work needed for optional pagination on
`GET /notes/`.

Parent Task: tasks/20260919-notes-pagination/000-main.md

## Requirements checklist

- [ ] Add optional `limit` and `offset` query handling only to `GET /notes/`.
- [ ] Return the requested slice in ascending note-ID order.
- [ ] Compute the total from all notes, independent of the requested slice.
- [ ] Expose the total through the header name approved by the parent task.
- [ ] Preserve the current full-list array path when pagination is absent.
- [ ] Use FastAPI-declared validation for invalid values.
- [ ] Leave all item CRUD route signatures and behavior unchanged.

Depends On: None

## Scope and implementation notes

The route owner is `src/app/api/notes.py`; database access belongs in
`src/app/api/crud.py`. Keep count and page selection as explicit
pagination-specific operations. The page query must order by
`notes.c.id.asc()` before applying offset/limit. Do not introduce a response
envelope, because the existing no-pagination contract is a JSON array.

The parent task must resolve the exact header name, numeric constraints, and
behavior when only one query parameter is supplied before this subtask is
implemented.

## Verification

The decisive evidence is a real `TestClient` request against the SQLite-backed
application with notes created through the public API. Confirm that the
returned IDs, total header, and no-parameter response shape match the approved
contract, and that item CRUD routes remain unaffected.
