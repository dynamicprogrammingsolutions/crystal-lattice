# Define the author metadata contract and dependency inventory

Establish the structured multi-author schema, transition behavior, and
complete list of legacy producers and consumers before changing content or
templates.

Parent Task: tasks/20260919-author-metadata-migration/000-main.md

## Requirements checklist

- [ ] Specify the supported structured field, ordering, cardinality, and
  author-value shape.
- [ ] Specify HTML/archive and feed output for one and multiple authors.
- [ ] Identify every repository source, test, script, template, and generated
  artifact that produces or consumes author metadata.
- [ ] Define the single compatibility boundary and the evidence required before
  the legacy field can be rejected.

## Open requirement questions and material decisions

- Resolve whether the structured values are names or author records.
- Resolve whether the field is required, and what missing/empty values mean.
- Resolve whether legacy input is accepted only by the normalization boundary or
  remains accepted by the authoring helper during transition.
- Do not add author identity, profile links, or author archive pages unless the
  parent task’s open scope question is approved.

## Supporting facts

The current dependency inventory found `author` in two post files, the post
layout, the feed template, the authoring helper, and the author-output coverage
placeholder. Shared archive/listing templates receive post objects but do not
currently print author data. The sitemap has no author read.

## Execution plan

Status: Draft

Inspect source and test references, document the exact contract, and choose one
normalization location that can map legacy scalar metadata to the new
structured value during the transition. Record output examples for a
single-author post, a multi-author post, and any permitted legacy post. Define
source and generated-output scans that can distinguish intentional migration
documentation from remaining runtime dependencies.

### Implementation decisions and open questions

The task cannot be marked complete until the parent task’s schema and output
questions are resolved. A normalization filter, data transform, or equivalent
boundary is an implementation choice after the contract is approved.

### Documentation

Capture the approved field and output contract in the parent execution plan and
the owning developer guidance during the authoring-tool subtask.

### Task checklist

- [ ] Record the final field name and value shape.
- [ ] Record single- and multi-author rendering and feed examples.
- [ ] Record compatibility inputs and the final rejection behavior.
- [ ] Record the complete producer/consumer inventory and evidence commands.

### Requirement verification

- Contract examples are reviewed against the request and current generated
  surfaces.
- A repository-wide search confirms the inventory includes all current
  `author` reads and writes and identifies any newly discovered dependency.

### Additional implementation verification

- Check YAML quoting/escaping and HTML/feed escaping requirements for author
  names before selecting the migration mechanism.