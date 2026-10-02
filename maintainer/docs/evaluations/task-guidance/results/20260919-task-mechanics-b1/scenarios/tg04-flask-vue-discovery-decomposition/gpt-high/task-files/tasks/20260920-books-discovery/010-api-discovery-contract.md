# Server discovery query and compatibility contract

Define and verify the Flask list endpoint’s filtering, search, bounded pagination, and response metadata so the Books page can consume a stable contract without breaking unfiltered callers.

Parent Task: tasks/20260920-books-discovery/000-main.md

## Requirements checklist

- [ ] `GET /books` supports the approved read-status filter.
- [ ] `GET /books` supports the approved title-or-author search behavior.
- [ ] `GET /books` supports bounded page selection and returns enough pagination metadata for the client to render and navigate pages.
- [ ] Combining discovery parameters selects the correct books deterministically.
- [ ] `GET /books` with no discovery parameters preserves the current status and `books` response fields for existing callers.
- [ ] Existing POST, PUT, and DELETE behavior remains usable by the client.

## Requirement questions and material decisions

- The parent’s unresolved questions about parameter names, matching semantics, default/max page size, and malformed/out-of-range values apply here.
- The response shape must decide whether pagination metadata is additive for all responses or only present for parameterized requests. This is a compatibility decision and is not resolved in this draft.
- The query implementation must decide whether filtering/searching occurs before pagination and must document the ordering; the expected user behavior strongly recommends selection before pagination, but this remains part of the approved contract.

## Supporting facts

- `server/query.py` is the natural owner for reusable list selection, but it currently has no public contract or tests.
- `server/app.py` directly exposes the in-memory `BOOKS` list and currently serializes all books for GET.
- The existing fixture data includes both read and unread books, but API tests do not currently assert contents or ordering.

## Execution plan

Status: Draft

After the public choices are approved, define a small query/result contract in the server query boundary. Parse and validate request parameters in the Flask boundary, apply search and read filtering before pagination, preserve a stable ordering, and return metadata sufficient to determine current page, page size, total results, and available pages. Preserve the exact legacy fields and mutation routes for an unparameterized request as required by the approved compatibility decision.

Extend the Python API tests with representative individual and combined queries, page-bound cases, empty results, the unfiltered response contract, and mutation regressions. Keep tests on the real Flask test client and the production query path.

### Implementation decisions and open questions

- Decision: server query logic belongs in `server/query.py`; HTTP parameter parsing and response assembly remain in `server/app.py`.
- Decision: do not add a second endpoint or alter mutation routes as part of discovery.
- Open: public parameter spellings/values, response metadata placement, and invalid-input behavior need approval from the parent task.

### Documentation

- Document the approved API parameters, matching/order rules, pagination metadata, and unfiltered compatibility in the maintained development documentation selected by the parent task.
- Do not update current guidance with unresolved target behavior while the task is Draft.

### Task checklist

- [ ] Resolve and record the server-facing public contract.
- [ ] Implement reusable selection and pagination behavior.
- [ ] Preserve and test unfiltered GET compatibility.
- [ ] Add direct Flask API regression coverage.
- [ ] Publish the verified API contract in maintained documentation.
- [ ] Hand the stable contract to the client child.

### Requirement verification

- Read-status filtering and title/author search: Flask client requests with known fixture data and assertions on returned IDs/content.
- Combined filtering/search/pagination and deterministic ordering: Flask client requests that assert both item IDs and metadata.
- Bounds and empty pages: boundary requests at first, last, beyond-last, and zero-result cases according to the approved invalid-input policy.
- Unfiltered compatibility: an unparameterized `GET /books` assertion for status and `books`, plus existing mutation tests.
