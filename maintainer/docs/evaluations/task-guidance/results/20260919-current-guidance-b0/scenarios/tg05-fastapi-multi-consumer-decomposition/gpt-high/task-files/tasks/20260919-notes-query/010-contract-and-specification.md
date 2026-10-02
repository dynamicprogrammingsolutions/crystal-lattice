# Define the notes-query contract

Resolve and record the public notes-query contract before API, client, or CLI
implementation begins.

Parent Task: tasks/20260919-notes-query/000-main.md

## Requirements checklist

- [ ] Decide the pagination parameters, defaults, inclusive/exclusive
      semantics, and maximum bound.
- [ ] Decide the public sort keys, direction syntax, default order, and
      deterministic tie-breaker.
- [ ] Decide the text-filter parameter, searched fields, matching semantics,
      and empty-filter behavior.
- [ ] Decide the parameterized response shape and preserve the required
      unparameterized API/client compatibility.
- [ ] Define validation errors and the corresponding client/CLI behavior.
- [ ] Record the approved contract in maintained repository documentation
      before downstream implementation starts.

## Open requirement questions

- Are pagination controls `offset`/`limit`, `page`/`page_size`, or another
  model?
- What are the default and maximum bounds?
- Which fields are sortable and what stable tie-breaker is guaranteed?
- Does text filtering cover title, description, or both, and how is matching
  normalized?
- Does pagination require total/count metadata, or must responses remain
  arrays?
- What client argument names and CLI flags expose the contract?

## Supporting facts

The current API returns a bare JSON array from `GET /notes/`, the client
returns that JSON unchanged, and the CLI iterates it. There is no existing
notes-query specification; `docs/development/index.md` explicitly records
that absence.

## Execution plan

Status: Draft

1. Review the current route, schema, client method, CLI command, and existing
   tests as compatibility inputs.
2. Obtain answers to the open requirement questions and write the agreed
   contract in the owning development documentation.
3. Include examples for an unparameterized request, bounded query, sort,
   filter, empty results, and invalid values.
4. Obtain review/approval of the contract before enabling implementation of
   the dependent subtasks.

### Implementation decisions and open questions

- Decision: this task is a prerequisite for all consumer-facing changes.
- Open: all public semantic choices listed above remain unresolved until
  approved; downstream tasks must not invent them independently.

### Documentation

Create or update the smallest maintained development/API contract page and
link it from the relevant development index if that improves discoverability.
Do not update package READMEs with target behavior until implementation is
verified.

### Task checklist

- [ ] Resolve all public contract questions.
- [ ] Write the approved notes-query specification.
- [ ] Review the compatibility examples against current API/client behavior.
- [ ] Record approval and unblock dependent subtasks.

### Requirement verification

- Contract review confirms every required capability and compatibility rule is
  explicit and consistent across HTTP, Python, and CLI interfaces.
- Specification examples cover the unparameterized path and each new query
  dimension without relying on implementation details.

### Additional implementation verification

- Inspect the existing tests and READMEs after the contract is written to
  ensure no target-only claim has been presented as already supported.