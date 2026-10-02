# Specify the public notes-query contract

Write the single maintained specification page that pins the notes-query
public contract — route, parameters, semantics, bounds, errors, and
compatibility guarantees across the API, client, and CLI — so consumers can
rely on it before implementations ship.

Parent Task: tasks/20260925-notes-query-capability/000-main.md
Depends On: none

## Requirements checklist

- [ ] `docs/development/notes-query.md` exists and pins: the collection
  route; every optional parameter (`limit`, `offset`, `sort`, `order`,
  `text`) with semantics, bounds, defaults, and error behavior; the
  deterministic ordering rule (explicit sort with id tiebreak, else id
  ascending when any parameter is present); the response shape; the
  compatibility guarantee for unparameterized requests; the client method
  signature; and the CLI flags.
- [ ] The spec visibly marks the capability `Not implemented` while only
  the contract exists, so it is not read as current user guidance.
- [ ] `docs/development/index.md` links the spec and no longer says "No
  notes-query specification exists."
- [ ] Spec content matches the approved decision set in the parent plan;
  no contract element is invented beyond it.
- [ ] No production code or behavior changes in this subtask.

## Supporting facts

- `docs/development/index.md` currently reads "No notes-query
  specification exists." (docs/development/index.md:3).
- The contract decisions and their rationale live in the parent task's
  `### Implementation decisions and open questions`; this subtask turns the
  approved set into the maintained specification.
- Documentation guidance (`docs/development/documentation.md`) was read
  during planning: smallest structure, documentation placed with the
  audience it serves, target-only text marked. One page in
  `docs/development/` is sufficient; no new directories.

## Execution plan

Status: Draft

Draft the spec page from the approved parent decision set: one section per
surface (HTTP, client, CLI) plus shared semantics (pagination bounds,
ordering rule, matching rule, error behavior, compatibility guarantees).
Update `docs/development/index.md` to link it. Carry a visible `Not
implemented` status marker; subtask 020 removes that marker when the API
ships. Nothing else changes.

### Implementation decisions and open questions

None local. All contract decisions are made in the parent task and must be
approved before this subtask executes. If approval changes a parameter name
or bound, update the parent decision set first, then this spec.

### Documentation

Only the two files above. Audience: developers consuming the public
contract across the three surfaces. No restructuring.

### Task checklist

- [ ] Draft `docs/development/notes-query.md` from the approved decisions
- [ ] Add the visible `Not implemented` status marker
- [ ] Update `docs/development/index.md` (link spec, drop stale line)

### Requirement verification

- Inspection: each contract element — route, five parameters, bounds and
  422 behavior, ordering rule, text matching, response shape, client
  signature, CLI flags, unparameterized guarantee — has a matching spec
  statement, cross-checked against the approved decision set.
- A search for "No notes-query specification exists" under
  `docs/development` returns nothing, and the index links the new page.

### Additional implementation verification

None planned; the artifact is documentation-only and verified by the
inspection above.