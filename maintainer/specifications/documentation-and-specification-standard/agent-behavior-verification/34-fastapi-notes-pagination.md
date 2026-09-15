# Test 34: FastAPI notes-pagination requirement quality

Requirement coverage: `DOCGUIDE-005`–`DOCGUIDE-006`, `DOCVAL-010`,
`DOCVAL-011`

## Source project

- Project: FastAPI CRUD Async, an asynchronous notes REST API.
- Upstream: `https://github.com/testdrivenio/fastapi-crud-async`
- Pinned revision: `4fa7ae952ece61e228135285de1b6a5ff65a1dc8`
- License: MIT

## Project context

The service exposes public create, list, read, update, and delete note routes.
`GET /notes/` currently performs an unbounded database select and returns a
plain JSON array matching `List[NoteDB]`. Item routes already have established
validation and not-found behavior.

## Exact user prompt

> Please inspect this FastAPI notes service. Large note collections make
> `GET /notes/` responses slow and unnecessarily large. Prepare a specification
> and requirements for optional `limit` and `offset` query parameters.
> Existing requests without either parameter must retain their current
> full-list response. When pagination is requested, results must use stable
> ascending note-ID order, `limit` must be between 1 and 100, and `offset` must
> be zero or greater. The response body must remain the existing array of note
> objects, and paginated responses must expose the total note count through
> `X-Total-Count`. Invalid pagination values should use FastAPI's normal
> validation response. Other note endpoints must remain unchanged. Do not
> implement the change or update current user documentation.

## Exact task-file user prompt

> Please inspect this FastAPI notes service. Large note collections make
> `GET /notes/` responses slow and unnecessarily large. Add optional `limit`
> and `offset` query parameters. Existing requests without either parameter
> must retain their current full-list response. When pagination is requested,
> results must use stable ascending note-ID order, `limit` must be between 1
> and 100, and `offset` must be zero or greater. The response body must remain
> the existing array of note objects, and paginated responses must expose the
> total note count through `X-Total-Count`. Invalid pagination values should
> use FastAPI's normal validation response. Other note endpoints must remain
> unchanged. Create one task file with a Draft execution plan for this change.
> Do not implement the change.

## Fixture facts

- `read_all_notes()` currently returns `crud.get_all()` as `List[NoteDB]`.
- `crud.get_all()` currently selects every row without explicit ordering.
- Existing tests assert that `/notes/` returns a plain array.
- Pydantic/FastAPI validation currently produces status 422 for invalid
  request values.
- Create, item-read, update, and delete routes are separate.
- No notes-pagination specification exists.
- `TASKS-v7` is not injected for the initial specification baseline.

## Desired target

The evaluator-only target is
[`targets/34-fastapi-notes-pagination.json`](targets/34-fastapi-notes-pagination.json).
Producing models do not receive it.

## Producer controls

- Start from a fresh fixture with no model-generated seed.
- Inject the requirement-minimal guidance variant.
- Permit changes only under `docs/development/`.
- Do not assert exact requirement wording, count, heading, or file shape.

## Task-file producer controls

- Reuse the same fixture, product outcomes, producers, and efforts.
- Inject the maintained general documentation guidance and effective current
  `TASKS-v7`.
- Request one task file with a Draft plan without separately requesting a
  testing strategy.
- Permit creation of one Markdown task file under `tasks/` only.
- Assess requirement and testing-plan quality from the same output.

## Semantic assessment

Compare generated requirements with the target for optional query behavior,
compatibility, bounds, ordering, body schema, total-count header, validation,
and unaffected endpoints. Identify unnecessary cursor pagination, mandatory
defaults, response envelopes, caching, indexing, versioning, rate limiting, or
deployment scope.

## Human review

The interpreted baseline summarizes material omissions and additions by model
and effort. Complete generated specification and requirement files remain
optional detail.