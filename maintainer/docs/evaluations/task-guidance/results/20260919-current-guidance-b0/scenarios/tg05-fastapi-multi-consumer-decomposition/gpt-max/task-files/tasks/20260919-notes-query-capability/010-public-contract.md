# Define the notes-query public contract

Parent Task: `tasks/20260919-notes-query-capability/000-main.md`

Define and record the single query contract that the service, reusable client,
and CLI will share. This is a planning and contract-gating subtask; consumer
implementation must wait until its public decisions are reviewed.

## Requirements checklist

- [ ] The contract defines bounded pagination, stable sorting, and optional
  text filtering for the notes collection.
- [ ] The contract specifies parameter names, defaults, bounds, allowed sort
  values, tie-breaking, filter matching, response shape, and invalid-input
  behavior.
- [ ] The contract explicitly preserves the current no-argument API and client
  behavior.
- [ ] The client method surface and CLI controls are mapped to the same
  semantics without introducing a second query dialect.
- [ ] The contract is available to reviewers before API, client, or CLI
  consumers are implemented.

## Unresolved requirement questions

- Choose the pagination model and its maximum bounded values.
- Decide whether parameterized results are always lists or whether an envelope
  with pagination metadata is required.
- Choose allowed sort fields, direction syntax, default order, and the
  deterministic tie-breaker.
- Define the filter's searchable fields, matching/case rules, and empty-value
  behavior.
- Define validation status/details and the corresponding client and CLI
  handling.
- Define CLI option names and whether its output includes metadata.

## Research and supporting facts

- The current API route, client method, and CLI command have no query
  parameters.
- The current API and client both expose a raw list, so changing parameterized
  response shape could create a separate compatibility decision.
- No notes-query specification exists in `docs/development/index.md`.

## Execution plan

Status: Draft

Collect the open decisions, write the contract at the smallest useful
maintained documentation boundary, and use it as the acceptance reference for
the three implementation subtasks. Do not add implementation code or claim
target behavior as current guidance during this subtask.

### Implementation decisions and open questions

- The contract must be approved before consumer work starts because parameter
  names, response shape, and error semantics are public compatibility
  decisions.
- Recommended baseline for review: bounded `limit`/`offset`, explicit sort
  field and direction with an `id` tie-breaker, and a single text query over
  title and description. This remains a recommendation until approved.
- The contract should distinguish omitted parameters from explicitly supplied
  defaults so the no-argument compatibility path remains precise.

### Documentation

- Draft the focused contract in `docs/development/notes-query.md` only after
  the unresolved requirement questions have answers.
- Include HTTP examples, client argument mapping, CLI flag mapping, validation
  behavior, stable-order guarantees, filtering semantics, and the
  no-argument compatibility rule.
- Link it from `docs/development/index.md` only once it describes implemented
  behavior or the project explicitly accepts a target specification boundary.

### Task checklist

- [ ] Gather answers to every unresolved contract question.
- [ ] Record the approved contract and compatibility examples.
- [ ] Review the contract with the API, client, and CLI implementation owners.
- [ ] Mark the contract as the dependency gate for the remaining subtasks.

### Requirement verification

- [ ] Contract review confirms all three required query capabilities and every
  public compatibility/error condition is specified.
- [ ] A reviewer can derive the API request, client call, and CLI invocation
  from the same contract without guessing or adding consumer-specific rules.
- [ ] The contract explicitly shows that no-argument API and client calls keep
  their existing list behavior.

### Additional implementation verification

- [ ] Check that the proposed bounds and sort/filter vocabulary match fields
  actually present in `src/app/db.py` and do not promise unsupported data.