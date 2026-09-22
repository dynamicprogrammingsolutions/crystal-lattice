# Extend the Books list API for discovery

Define and implement the server-owned selection contract that lets clients
filter by read status, search title or author, and request bounded pages while
preserving the existing unfiltered API and CRUD routes.

Parent Task: tasks/20260920-books-discovery/000-main.md

## Requirements checklist

- [ ] `GET /books` supports the approved read-status filter vocabulary.
- [ ] `GET /books` supports the approved title-or-author search semantics.
- [ ] `GET /books` returns a bounded page and enough approved metadata for a
  client to render page state and enforce valid navigation.
- [ ] Missing discovery parameters retain the existing unfiltered response
  contract and include the complete collection.
- [ ] Existing `POST /books`, `PUT /books/<book_id>`, and
  `DELETE /books/<book_id>` behavior remains compatible.

## Scope and ownership

This child owns server-side query parsing, normalization, filtering,
pagination, response metadata, and the Flask-boundary regression evidence.
It does not own Vue controls, URL synchronization, or client mutation
refreshes.

## Depends On

None.

## Unresolved requirement questions and decisions

- Public parameter names and values, page size, metadata shape, search
  normalization, and invalid/out-of-range page behavior are inherited from the
  parent plan and must be settled before implementation.
- The API must not make an unapproved change to mutation payloads, mutation
  status codes, or the existing unfiltered `status`/`books` response fields.

Recommended contract for approval: a shared status/search/page vocabulary,
case-insensitive substring search across title and author, a documented
default page size, explicit total/page/last-page or equivalent metadata, and
normalization of invalid page requests to a valid bounded result.

## Research and supporting facts

- `server/app.py` currently imports Flask request handling but does not read
  query parameters for `GET /books`.
- `server/query.py` is an isolated, currently trivial list-selection helper,
  making it the natural owner for pure filtering/pagination calculations.
- The existing Flask tests only assert status codes, so response-shape,
  ordering, compatibility, and boundary regressions need focused coverage.

## Execution plan

Status: Draft

1. Confirm the public query and response contract with the parent task.
2. Extend the query helper with deterministic status filtering, title/author
   search, and bounded pagination without mutating the source collection.
3. Wire the approved query into `GET /books`, retaining the existing
   unparameterized response fields and adding only approved metadata.
4. Add Flask-client tests for no parameters, each status value, title and
   author search, combined criteria, empty results, first/middle/last pages,
   invalid or out-of-range pages, and CRUD compatibility.
5. Document the settled API contract in the maintained developer guidance
   selected by the parent plan.

### Implementation decisions and open questions

Do not choose public names or metadata solely for implementation convenience.
The parent task's unresolved questions are API compatibility decisions. Once
approved, record the exact vocabulary here before marking this child
approved.

### Documentation

Document the final `GET /books` query parameters, matching semantics,
pagination metadata, default behavior, and unfiltered compatibility in the
maintained developer documentation. Keep the documentation beside the
developer-facing API guidance rather than duplicating it in test descriptions.

### Task checklist

- [ ] Resolve the inherited API contract questions.
- [ ] Mark this child `Approved` after the parent plan is approved.
- [ ] Implement query selection and pagination.
- [ ] Wire the Flask route without regressing mutation routes.
- [ ] Add and run focused API regression tests.
- [ ] Update the maintained API guidance.
- [ ] Append completion notes with the exact contract and test evidence.

### Requirement verification

- The decisive check for the filter/search/pagination requirements is the
  Flask test client calling the real `GET /books` route with approved query
  combinations and asserting both items and metadata.
- The decisive compatibility check is the same route with no query string,
  asserting the existing response fields and complete collection, plus the
  existing POST/PUT/DELETE tests.

### Additional implementation verification

- Verify results preserve the existing collection order unless an approved
  ordering decision says otherwise.
- Verify filtering and pagination operate on a copy or derived sequence so
  reads cannot mutate global `BOOKS`.
- Verify empty pages and empty filtered results have stable metadata that the
  client can use without guessing.