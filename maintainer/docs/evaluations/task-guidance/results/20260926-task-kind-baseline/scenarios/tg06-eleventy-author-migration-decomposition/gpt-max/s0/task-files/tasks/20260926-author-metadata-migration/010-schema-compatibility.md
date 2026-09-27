# Define the canonical author schema and transition compatibility

Establish the single page-data contract that represents one or more post
authors and temporarily bridges existing scalar `author` front matter to that
contract. This task owns the compatibility boundary consumed by templates and
authoring tools.

Parent Task: tasks/20260926-author-metadata-migration/000-main.md
Depends On: None

## Requirements checklist

- [ ] Record the approved canonical `authors` field name, entry shape, ordering,
  and validation rules.
- [ ] Provide one normalization boundary that exposes canonical authors to
  consumers during the transition.
- [ ] Preserve a legacy singleton author during the migration without
  requiring templates or feeds to read the raw `author` field.
- [ ] Define and test the behavior for canonical input, legacy input,
  conflicting fields, empty values, and malformed entries according to the
  approved policy.
- [ ] Keep the compatibility behavior isolated so the final retirement task can
  remove or retain it as one explicit state change.

## Requirement questions and decisions

- **Question:** Confirm whether canonical entries are ordered strings or
  records, and whether identity/URL fields are in scope.
- **Question:** Confirm precedence or rejection when both `authors` and
  `author` are supplied.
- **Recommendation:** Normalize legacy `author: "Name"` to a one-entry
  collection and make all downstream consumers depend only on the normalized
  value. Do not silently merge conflicting fields without an approved rule.

## Research and supporting facts

- Existing source files expose only scalar `author` values.
- The post layout and feed currently read the legacy key independently, so
  compatibility logic is currently duplicated at the consumer level by
  implication.
- Eleventy configuration is the natural ownership area for a shared
  collection/page-data boundary, but the implementation should use the
  project’s actual data-cascade capabilities rather than scattering template
  conditionals.

## Execution plan
Status: Draft

Define the canonical author interface before changing any consumer. The
normalizer should accept the approved canonical collection and, while the
transition is active, translate a valid legacy scalar into the same internal
shape. It should return enough information for templates and feeds to render
names in source order without knowing which input form supplied them.

Validation and conflict behavior must be explicit. A source item with both
fields, an empty collection, or an invalid entry must follow the approved
policy and produce an actionable diagnostic if rejection is the chosen
behavior. The normalizer must not make the final legacy-rejection decision
itself; that decision belongs to the evidence-gated retirement task.

Add focused coverage for normalization and an integration fixture that sends
the normalized value through at least one real post render. Keep the
compatibility fixture available for the transition tests, but mark it as
intentional so the final source audit can distinguish it from a supported
content dependency.

### Implementation decisions and open questions

- The exact canonical entry shape and conflict policy are blocked on the
  parent requirement questions.
- The normalizer’s public result should be stable enough that templates,
  feed generation, and the authoring helper share one representation.
- Do not remove legacy support in this task; the retirement task owns that
  compatibility-state change.

### Documentation

Contribute the canonical front-matter example and transition semantics to the
maintained development documentation after the shape is approved. Avoid
claiming that legacy input is rejected until the final gate passes.

### Task checklist

- [ ] Resolve and record the schema and validation decisions.
- [ ] Implement the shared normalization boundary during execution.
- [ ] Add canonical, legacy, conflict, and malformed-input evidence.
- [ ] Prove one normalized value reaches a real Eleventy-rendered page.
- [ ] Hand off the stable interface to the rendering and content/authoring
  subtasks.

### Requirement verification

- Verify canonical and legacy fixtures through the actual page-data path and a
  real Eleventy build; do not rely only on a helper-level mock.
- Assert that downstream output receives an ordered canonical collection and
  contains no raw legacy fallback branch in the template/feed consumers.
- Verify invalid or conflicting inputs according to the approved policy and
  preserve the diagnostics needed by the final retirement audit.

### Additional implementation verification

- Use names with punctuation, quotes, and non-ASCII characters.
- Verify author order survives normalization unchanged.
- Verify a single legacy name produces exactly one canonical entry.