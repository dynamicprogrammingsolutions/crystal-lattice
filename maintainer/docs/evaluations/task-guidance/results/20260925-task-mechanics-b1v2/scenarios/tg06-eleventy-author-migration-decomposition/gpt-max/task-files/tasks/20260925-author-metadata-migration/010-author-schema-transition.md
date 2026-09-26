# Establish the structured author schema and transition boundary

Define the approved structured author contract and provide the single
compatibility boundary that lets existing scalar-author content continue to
build while consumers migrate. This subtask owns the material data-contract
and compatibility decision; it does not own the individual templates or the
bulk content migration.

## Requirements checklist

- [ ] Define an approved structured representation that can carry one or more
      named authors and document its required fields and cardinality.
- [ ] Normalize the structured representation to one stable shape for all
      downstream consumers.
- [ ] During the transition, normalize the legacy scalar form to the
      single-author equivalent without losing the existing name or changing
      unrelated post data.
- [ ] Define the evidence-gated retirement behavior for the legacy form;
      consumers must not independently fall back to the scalar field.
- [ ] Provide contract-level evidence for both one-author and multi-author
      inputs and for the transition behavior.

Parent Task: tasks/20260925-author-metadata-migration/000-main.md

Depends On: None

## Unresolved requirement questions

- Confirm the field name, record/string shape, and any author identity fields
  before treating the normalized shape as a public contract.
- Confirm whether the final state must reject legacy input or may retain
  read compatibility indefinitely after migration.

## Supporting facts and research

- The current scalar field is named `author` in both existing post files.
- The layout receives `author` as a variable, while the feed reads
  `post.data.author`; there is no existing shared normalization layer.
- The authoring helper and output consumers therefore need one agreed
  boundary rather than separate compatibility logic.

## Execution plan

Status: Draft

Introduce the author contract at the earliest shared data boundary available
in the Eleventy site. Consumers should receive only the normalized
multi-author collection. While the migration is in progress, the boundary
may recognize the legacy scalar and convert it to a one-author collection.
The legacy branch must be visibly transitional so the final source/output
evidence can authorize its removal or rejection.

1. Resolve the schema and final-retirement questions with the parent task.
2. Identify the appropriate Eleventy data/configuration integration point and
   define the normalized value and its handling for one and many authors.
3. Add focused contract evidence for structured input, legacy input during the
   transition, missing/invalid required author data if the approved contract
   specifies validation, and the final retirement behavior.
4. Record the exact source/output scans and production-build evidence that
   the parent must see before removing the legacy branch.
5. Hand the stable contract to the content/authoring and generated-output
   subtasks; do not add consumer-specific scalar fallbacks.

### Implementation decisions and open questions

- The normalization location is an implementation choice within this
  subtask; the public schema and retirement outcome remain unresolved.
- Error behavior for malformed or legacy input after retirement must follow
  the approved contract rather than being invented during planning.

### Documentation

- Supply the final contract wording to the parent for the maintained
  developer documentation. Avoid documenting a draft field shape as current
  guidance.

### Task checklist

- [ ] Resolve and record the structured schema.
- [ ] Resolve and record the final legacy-retirement outcome.
- [ ] Implement the shared transition boundary after parent approval.
- [ ] Add contract evidence for structured and transition inputs.
- [ ] Provide the parent with the evidence required for the final gate.

### Requirement verification

- The decisive check for this subtask is its contract test at the shared data
  boundary, covering both a single structured author and multiple structured
  authors, plus the legacy scalar while compatibility is enabled.
- The parent production-build check remains the decisive proof that this
  boundary is actually used by the public templates and feed.

### Additional implementation verification

- Search for direct scalar-author reads after consumer migration and ensure
  only the intentionally retained transition boundary/test references remain.