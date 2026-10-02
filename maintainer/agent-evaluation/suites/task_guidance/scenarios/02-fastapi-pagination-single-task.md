# TG-02: FastAPI notes pagination as one task

## Project

- Repository: FastAPI CRUD Async
- Revision: `4fa7ae952ece61e228135285de1b6a5ff65a1dc8`
- Kind: public REST API with a large-response performance concern
- Existing semantic target:
  `documentation_standard/targets/34-fastapi-notes-pagination.json`

## Purpose

Verify that one bounded collection-endpoint feature remains one task and that
route, storage, compatibility, and verification planning survive handoff
without turning query mechanics into approved constraints.

## Natural request

> Add optional limit/offset pagination to `GET /notes/` so clients can request
> a bounded ascending-ID slice and receive the total note count in a response
> header. Requests without pagination must keep the current full-list array
> behavior, invalid values should use normal FastAPI validation, and the other
> CRUD routes must not change. Plan the change and create the appropriate task
> structure, but do not implement it.

## Approved outcomes

Use `NOTES-1`–`NOTES-8` from the existing target. Exact SQL, ORM calls, header
helpers, count-query strategy, and omitted-companion behavior beyond the
approved target are not prescribed.

## Canonical plan

1. Inspect the public route, schemas, storage/query boundary, and current route
   tests.
2. Record a question for any omitted-companion behavior not already approved.
3. Add optional validated query parameters while preserving unparameterized
   behavior and the array body.
4. Apply stable ascending ordering and total-count behavior without mandating
   an unapproved query strategy.
5. Verify the production FastAPI HTTP route for normal, boundary, invalid, and
   compatibility behavior.
6. Add focused regression evidence for create, item-read, update, and delete.
7. Update maintained API documentation as plan work when current claims
   require it.

## Expected task shape

- One task file with a Draft plan.
- No storage, route, tests, or documentation subtasks.
- Requirements express public behavior and compatibility, not database-side
  slicing, exact ORM calls, tests, or documentation production.

## Handoff variants

### Retain plan

Preserve route/storage inspection findings, public ambiguities, and HTTP
verification boundaries in the Draft plan.

### Omit plan

Preserve source pointers, current route behavior, existing test coverage and
gaps, public contract constraints, and unresolved questions. Omit proposed
implementation and test steps.

## Continuation target

A fresh agent produces a plan with decisive HTTP evidence, representative
valid/invalid boundaries, honest storage-layer gaps, CRUD regression coverage,
and no invented query implementation.

## Important crossing

The production FastAPI route must interact with the real storage/query behavior
that determines ordering, slicing, and total count.

## Efficiency use

Use this scenario for omit-plan replanning and incomplete-handoff negative
control.

## Human review

- Did the handoff preserve the public contract and ambiguity boundaries?
- Did storage mechanics remain implementation choices?
- Does the later plan avoid mock-only proof of ordering/count behavior?