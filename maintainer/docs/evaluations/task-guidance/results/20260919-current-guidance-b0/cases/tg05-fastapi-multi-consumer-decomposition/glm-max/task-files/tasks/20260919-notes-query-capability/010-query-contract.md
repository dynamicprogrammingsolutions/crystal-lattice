# Stabilize the public notes-query HTTP contract

Specify the notes-query capability's public HTTP contract — parameters,
pagination bounds, sorting, optional text filtering, response shape, error
behavior, and unparameterized compatibility — in maintained documentation, and
obtain approval so the client and CLI build against a stable contract.

This subtask changes no service behavior and no user-facing README claims. It
is the gate for `020`, `030`, and `040`.

Parent Task: `tasks/20260919-notes-query-capability/000-main.md`

Depends On: none (first subtask).

## Requirements checklist

- [ ] C1: A maintained specification describes the notes-query HTTP contract:
      the operation and route, pagination parameters with explicit bounds,
      sort parameters with deterministic (tie-broken) ordering, the optional
      text filter and its matching semantics, the response shape, and the
      validation/error behavior for invalid parameters.
- [ ] C2: The specification explicitly states the compatibility rule:
      unparameterized requests keep current behavior exactly (full collection
      returned as a bare JSON array, no sorting, no filtering, no page cap).
- [ ] C3: The specification is approved — the contract is "stable" — and the
      approval is recorded in this task file before `020`, `030`, or `040`
      begins.
- [ ] C4: `docs/development/index.md` no longer states that no notes-query
      specification exists and points to the specification.

## Supporting facts

- Current behavior being pinned (verified): `GET /notes/` (prefix configured in
  `src/app/main.py:15`) returns `crud.get_all()` — every note, DB order, no
  parameters; response is a bare JSON array.
- FastAPI's default validation behavior returns 422 for failed query-parameter
  constraints; the contract should state this explicitly rather than leave it
  implicit.
- Documentation rules (`docs/development/documentation.md`): specifications may
  describe an intended target; user documentation must only describe current
  supported behavior. Therefore the root README, client README, and CLI README
  are NOT touched here — their claims become true only with the implementing
  changes in 020/030/040. The specification page is the intended-target
  artifact.
- Smallest structure applies: a single specification page; no placeholder
  sections or directory scaffolding beyond what the content needs.
- `docs/development/index.md` currently reads "No notes-query specification
  exists." and must be updated with the spec (C4).

## Execution plan

Status: Draft

1. Decide the contract values below (open questions section), presenting them
   for approval together with this plan.
2. Write the specification as one page under `docs/` (placement by audience
   and ownership; likely a sibling of `docs/development/` serving API
   consumers, but the exact location is decided when writing, following
   `docs/development/documentation.md`).
3. Update `docs/development/index.md` (C4).
4. Record approval in this task file (turn the checklist item C3 true with a
   dated note) — this is the stability gate for 020/030/040.

Recommended contract content (to be confirmed or amended at approval):

- Operation: the existing `GET /notes/` collection operation gains optional
  query parameters; no new route. Rationale: defaults preserve current
  behavior exactly and avoid stabilizing a second route.
- Pagination: `limit` (1..max, recommendation max 100) and `offset`
  (>= 0). Parameters absent ⇒ not applied at all (unparameterized requests
  are unbounded, preserving R5). Out-of-bounds values ⇒ 422 (explicit
  rejection preferred over silent capping; the contract must pick one).
- Sorting: `sort` restricted to a whitelist (recommendation: `id`, `title`),
  optional descending form (recommendation a `-` prefix), deterministic
  tie-break on `id` ascending so pages never shuffle equal keys; `sort`
  absent ⇒ current DB order (unchanged).
- Filtering: single optional `q` parameter, case-insensitive substring match
  (recommendation: over `title` only, as the smallest useful filter; extending
  to description is a contract choice to make now, not later); `q` absent ⇒
  no filtering.
- Response shape: unchanged bare JSON array in every case (no envelope), so
  the shape never depends on which parameters were supplied.
- Error behavior: FastAPI 422 for invalid/unknown/out-of-bounds values,
  documented explicitly.

### Implementation decisions and open questions

All items below are material (user-visible HTTP contract) and need approval
before this plan is marked `Approved`; none is resolved yet:

- Parameter surface: extend `GET /notes/` with optional parameters vs a new
  query route. Recommendation: extend the existing operation.
- Pagination bounds and enforcement: 422 vs silent cap for oversized `limit`;
  the numeric maximum. Recommendation: 422, max 100.
- Sort field whitelist, direction syntax, and tie-break rule. Recommendation:
  `id` and `title`, `-` prefix for descending, `id` ascending tie-break.
- Filter target (`title` only vs title + description) and matching
  (case-insensitive substring recommended), parameter name (`q`
  recommended).
- Response shape: bare array (recommended) vs envelope when paginating.
  Recommendation: bare array always; keeps R5 trivially true.

### Documentation

- One specification page under `docs/` describing the contract above,
  including a short "current behavior preserved" section (C2) and worked
  request examples.
- `docs/development/index.md` updated (C4).
- Audience: HTTP API consumers, plus maintainers of the client and CLI who
  implement against the contract. No user README changes in this subtask.

### Task checklist

- [ ] Contract decisions approved (recorded above with date)
- [ ] Specification page written and reviewed
- [ ] `docs/development/index.md` updated
- [ ] Approval recorded (C3) — gate for 020/030/040

### Requirement verification

- C1, C2: the specification change itself is the evidence — the requirement is
  the existence of a stable documented contract at the public HTTP boundary;
  a reviewed diff of the spec page is decisive.
- C3: the dated approval note in this task file plus the `Depends On` edges
  that 020/030/040 declare; no automated test (docs-only change).
- C4: the `docs/development/index.md` diff.
- Downstream behavioral evidence of the contract arrives with 020's API tests;
  it is intentionally not produced here because nothing is implemented yet.

### Additional implementation verification

- None beyond documentation review; no code, tests, or dependency changes are
  in scope for this subtask.