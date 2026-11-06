# Server: `GET /books` selection parameters

Add optional selection parameters to `GET /books` — read-status filter,
title/author search, and bounded pagination — while keeping the unfiltered
response and all mutation behavior exactly as today. This is the data-selection
layer of the book-discovery capability and is independently useful to API
consumers.

Parent Task: tasks/20261102-books-page-discovery/000-main.md

Depends On: none. This subtask lands first; the unfiltered default keeps the
current client working until subtask 020 lands.

## Requirements checklist

- [ ] `GET /books` accepts optional `read` (`true`/`false`, case-insensitive),
      `q` (case-insensitive substring match against title or author), `page`
      (positive integer, default 1), and `per_page` (positive integer, default
      10, clamped to a maximum of 100).
- [ ] When any selection parameter is present, the response is
      `{"status": "success", "books": [<page items>], "total": <filtered
      total>, "page": <page>, "per_page": <effective per_page>}`; a page
      beyond the last returns an empty `books` list with the correct `total`
      and status 200.
- [ ] When no selection parameter is present, the response is unchanged:
      `{"status": "success", "books": [all books]}` with no added fields.
- [ ] Malformed values return 400 with an error body: `read` not
      `true`/`false`, or `page`/`per_page` not a positive integer. `per_page`
      above 100 is clamped, not rejected.
- [ ] `POST /books`, `PUT /books/<id>`, and `DELETE /books/<id>` behavior and
      responses are unchanged.
- [ ] Selection logic (filter, search, slice, count) is a pure function in
      `server/query.py`; `app.py` only parses and validates request args and
      shapes responses.
- [ ] API tests cover: the exact legacy unfiltered body, each parameter alone,
      combined parameters, per_page clamping, out-of-range page, each 400
      case, and the existing CRUD cycle still passing.
- [ ] `docs/development/book-discovery.md` exists with the selection contract
      section, and `docs/development/index.md` links it in place of the
      "No book-discovery specification exists." line, in the same change as
      the code.

## Supporting details

- `server/app.py` currently returns `{"status": "success", "books": BOOKS}`
  for all GET requests and ignores query parameters; `BOOKS` is an in-memory
  list of `{"id", "title", "author", "read"}` dicts.
- `server/query.py:list_books(books)` returns a shallow copy and is not called
  by `app.py`. Extending this module keeps selection testable without HTTP.
- `tests/conftest.py` provides the Flask test client via `app.test_client()`;
  `tests/test_books_api.py` covers unfiltered GET and one CRUD cycle.
- The current client calls `GET /books` with no parameters on mount and after
  every mutation, so the legacy default is what keeps it working between this
  subtask and subtask 020.
- Fixture note: `flask` is not installed in the default `python3` (pytest
  9.1.1 is); the executor must use the project environment or install
  dependencies before running the suite.

## Implementation plan

Status: Draft

### Approach

Add a pure selection function to `server/query.py`, roughly
`select_books(books, *, read=None, q=None, page=1, per_page=10) -> tuple[list, int]`
returning the page items and the filtered total. Keep the existing
`list_books` helper untouched. In `app.py`, parse `request.args` for the four
parameters, validate them (400 on malformed `read`/`page`/`per_page`, clamp
`per_page` to 100), and choose the response mode: if any of the four
parameters is present, return the paged body with metadata; otherwise return
today's body unchanged. The "any parameter present" trigger — not "any filter
value set" — is what keeps the compatibility boundary unambiguous.

### Steps

1. Add the selection function in `server/query.py` with filter, case-
   insensitive substring search, slice, and count.
2. Wire `app.py` GET parsing, validation, and both response modes; leave all
   mutation routes untouched.
3. Extend `tests/test_books_api.py` with the coverage listed in the
   requirements, including a test pinning the exact legacy body.
4. Create `docs/development/book-discovery.md` with the API selection
   contract (both response modes, validation, bounds) and update
   `docs/development/index.md` to link it.
5. Run the server suite and confirm all tests, including the pre-existing
   ones, pass.

### Risks and the way back

- A wrong default (e.g. globally applied page size) would silently truncate
  the current client's list; the pinned legacy-body test guards this.
- Response-shape divergence can confuse API consumers; both modes are
  documented in the same change.
- No persisted data exists; rollback is reverting this subtask's commit,
  which also reverts its documentation claims.

### Implementation decisions and open questions

Mirrors the parent plan (pending overall approval): parameter names and
defaults; strict legacy response when no selection parameter is present;
clamp-`per_page`-but-400-malformed; 200-with-empty-list for out-of-range
pages; selection logic pure in `server/query.py`. No subtask-local open
questions.

### Documentation

Owned by this subtask: creation of `docs/development/book-discovery.md` with
the selection contract, and the `docs/development/index.md` link update — both
in the same reviewed change as the code. Audience: developers consuming the
API.

### Task checklist

- [ ] Selection function added in `server/query.py`; `app.py` wired for both
      response modes; mutation routes untouched.
- [ ] API tests added per the requirements checklist; full suite passes.
- [ ] Specification page created and index link updated.

### Requirement verification

pytest through the Flask test client is the decisive evidence: it crosses the
real routing, parsing, validation, and selection path of the app in one run.
The legacy-body test pins unfiltered compatibility; parameterized tests pin
filtering, search, paging, clamping, and the 400 cases; the existing CRUD
test proves mutations are preserved. This deliberately does not cover real
network transport (covered at the next boundary by subtask 020's integration
test), client rendering, or POST body validation (unchanged and untested
today; no new gap introduced).
