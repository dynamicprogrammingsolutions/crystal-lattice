# Define the Books API discovery contract

Plan the Flask-side filtering, search, and bounded-pagination behavior that the Books page will consume while retaining the current unfiltered and CRUD API contracts.

Parent Task: tasks/20260919-books-discovery/000-main.md
Depends On: None

## Requirements checklist

- [ ] The GET books contract can select read status and search title or author using optional query inputs.
- [ ] Explicit discovery requests return a bounded page and enough metadata for the client to render reliable page controls.
- [ ] A GET with no discovery parameters remains a full-list response with the current `status` and `books` fields.
- [ ] Existing POST, PUT, and DELETE endpoints and their current mutation behavior remain intact.
- [ ] API evidence covers selection, pagination boundaries, unfiltered compatibility, and mutation regressions.

## Research and supporting facts

- `server/app.py` owns the `/books` GET/POST route and currently returns the complete module-level `BOOKS` list for GET.
- `server/app.py` owns the `/books/<book_id>` PUT/DELETE route; the request does not authorize changing that public endpoint.
- `server/query.py` has a pass-through `list_books` helper, which is the natural home for pure filtering/pagination transformations if that ownership remains appropriate.
- `tests/test_books_api.py` currently asserts only status codes, so response shape and selection semantics need focused coverage.

## Execution plan

Status: Draft

First settle the shared query and response contract from the parent task. Then keep data selection in a pure, testable helper: preserve collection order, apply the approved read-status predicate, match the approved title/author search semantics, and calculate a bounded slice plus page metadata. The Flask route should parse request arguments, distinguish an absent discovery query from an explicit paged/discovery request, and serialize the result without mutating the source collection.

The no-query path must continue to expose the complete collection through the existing `status` and `books` fields so existing consumers remain compatible. Additive metadata or a paginated shape must not silently change that legacy path. Mutation routes should remain unchanged except for any tests needed to prove they continue to work after the GET logic is extended.

Add API tests for each approved read-status value, title-only and author-only matches, combined filtering, empty results, first/middle/last page boundaries, invalid input handling, and the no-query full-list contract. Keep the tests at the Flask test-client boundary and add helper-level tests only for calculations that are not meaningfully covered by route assertions.

### Implementation decisions and open questions

- Decision: keep the server route at `/books` and make discovery inputs optional.
- Decision: do not paginate or filter the no-query compatibility path unless the approved contract explicitly changes that constraint.
- Open: parameter names, page size, response metadata, matching semantics, and invalid/out-of-range behavior are inherited from the parent task and must be resolved before implementation.
- Recommendation: preserve source order and use a deterministic one-based page model so the client can reason about page bounds without a sort contract.

### Documentation

- Document the final query parameters and response metadata in the feature/development documentation after the API behavior is implemented and tested.
- Do not update current guidance while this task remains a Draft plan.

### Task checklist

- [ ] Resolve and record the public query/response contract.
- [ ] Define the pure selection and pagination behavior, including invalid and out-of-range inputs.
- [ ] Define route-level compatibility behavior for a no-query GET.
- [ ] Plan focused Flask tests for positive, empty, boundary, and regression cases.
- [ ] Mark this subtask ready for execution only after the parent contract is approved.

### Requirement verification

- Optional read-status and title/author selection: Flask test-client requests with each approved query combination and exact returned IDs.
- Bounded pages and metadata: first/last/out-of-range route requests asserting returned slice and page metadata.
- No-query compatibility: a request without discovery parameters asserting the complete fixture collection and existing response keys.
- CRUD preservation: existing POST/PUT/DELETE tests plus a GET-after-mutation assertion where needed to prove the selection extension did not change mutation behavior.