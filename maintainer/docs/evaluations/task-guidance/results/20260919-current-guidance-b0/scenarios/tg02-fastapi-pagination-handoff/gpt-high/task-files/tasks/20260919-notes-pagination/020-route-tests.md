# Add public regression coverage for notes pagination

Specify integration coverage for the pagination contract and the preserved
CRUD surface.

Parent Task: tasks/20260919-notes-pagination/000-main.md

## Requirements checklist

- [ ] Verify an unparameterized `GET /notes/` still returns the complete JSON
      array.
- [ ] Verify bounded pages use ascending IDs and honor the approved
      limit/offset semantics.
- [ ] Verify the total-count response header reports the unfiltered count.
- [ ] Verify malformed and out-of-range values receive normal FastAPI 422
      validation responses.
- [ ] Verify create, single-note read, update, and delete routes still work.

Depends On: tasks/20260919-notes-pagination/010-api-pagination.md

## Scope and implementation notes

Extend `src/tests/test_notes.py` through the public `TestClient` boundary.
Seed enough notes via `POST /notes/` to distinguish ordering, offset, limit,
and total count. Keep assertions tied to the approved public header and
parameter rules; do not encode unresolved behavior or test-only database
shortcuts.

## Verification

Run the focused notes test module and ensure collection and exit are clean.
The tests should demonstrate both the legacy no-query path and the new
paginated path, including framework validation rather than a custom error
response.
