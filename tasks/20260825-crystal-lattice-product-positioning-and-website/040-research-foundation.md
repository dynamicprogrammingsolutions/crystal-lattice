# Establish the Product Website Research Foundation

Define the decisions, source boundaries, evidence model, budget controls,
review method, privacy rules, and adaptive handoff process for the positioning
research program.

## Requirements checklist

- [ ] Research decisions, starting hypotheses, contradictory possibilities,
      and confidence language are explicit.
- [ ] Candidate sources are assessed by question, coverage, access, cost,
      permitted use, privacy, and bias.
- [ ] Retained records preserve provenance and separate source facts from
      inference.
- [ ] Pilot, review, expansion, stop, paid-source approval, and correction
      rules are reproducible.
- [ ] The foundation permits new feature, source, audience, and positioning
      branches without turning the program into a fixed pipeline.

Parent Task: `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md`
Depends On:

- `tasks/20260825-crystal-lattice-product-positioning-and-website/010-website-documentation-and-content-specification-foundation.md`
- `tasks/20260825-crystal-lattice-product-positioning-and-website/020-current-product-and-compatibility-baseline.md`

## Research decisions to support

- primary product category and audience;
- multi-agent/model-family convenience;
- transparency and control value;
- session/workflow feature value;
- natural-language customization value;
- coding-agent versus general-purpose scope;
- mobile continuity and bridge viability;
- website language, proof, paths, and calls to action.

## References

### Start here

1. `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md:8-186`
   — shared requirements, questions, approved structure, handoff rules,
   retained-output rules, and research boundaries.
2. `tasks/20260825-crystal-lattice-product-positioning-and-website/020-current-product-and-compatibility-baseline.md:1-125`
   plus its completed outputs — product facts and compatibility dimensions
   that seed research without establishing market value. Stop if incomplete.
3. `landing_page/docs/development/research/research-method.md:1-228` — durable
   evidence types, common record shape, feature review, pilot, manual review,
   confidence, privacy, and content-promotion method.
4. `landing_page/docs/development/research/positioning-and-product-baseline.md:68-181`
   — current hypotheses, recommendations, questions, and progressive rewrite
   direction.
5. `landing_page/docs/development/research/evidence-index.md:1-106` — current
   product, historical, release, and initial external source routes.
6. `landing_page/research/README.md:1-84` — retained evidence, excluded raw
   material, review, and lineage constraints.

### Additional references

- Source-specific official terms, pricing, API, robots, and access
  documentation discovered during source assessment.
- Repository privacy and documentation policy when a proposed source or output
  creates a new audience or retention question.

## Known facts and supporting details

- Product/repository evidence, search demand, community evidence, competitor
  claims, issues, interviews, and experiments answer different questions.
- The program needs a bounded pilot-and-expand model rather than one fixed
  end-to-end pipeline.
- Paid sources, account registration, restricted credentials, user contact,
  and material source expansion require explicit approval.
- Research must support progressive rewrites and cannot become a gate for the
  already-planned early-user baseline.
- Later research tasks need exact schemas, output paths, review rules, and
  handoff conventions rather than recreating them independently.

## Expected outputs

Human-readable foundation:

- `landing_page/docs/development/research/findings/research-foundation.md`

Retained research package:

```text
landing_page/research/040-research-foundation/
├── decision-brief.md
├── hypothesis-ledger.csv
├── source-assessment.md
├── evidence-schema.json
├── review-and-expansion-policy.md
├── access-and-budget-decisions.md
├── handoff-conventions.md
└── completion-manifest.json
```

Required updates:

- `landing_page/docs/development/research/research-method.md` only for approved
  durable method refinements;
- `landing_page/docs/development/research/evidence-index.md` for approved
  source routes;
- downstream task supporting details when the approved foundation determines
  an exact source, schema, budget, or handoff contract they must consume.

## Scope boundaries

- Do not begin broad source collection.
- Do not spend money, register accounts, retrieve restricted credentials, or
  contact research participants.
- Do not change public website content or the content specification.
- Do not create adaptive follow-up task files; define the proposal and approval
  mechanism only.
- Store disposable access tests under
  `landing_page/artifacts/research/040-research-foundation/`.

## Execution plan

Status: Draft

Start from the package research method, then produce a concrete source
assessment, hypothesis ledger, shared record schema, source-specific
extensions, budget proposal, and review thresholds. Pilot only enough source
access to validate feasibility before requesting paid or restricted access.

Define how adaptive feature-mining handoffs are proposed and approved. Preserve
raw disposable output under ignored package artifacts and normalized retained
evidence under the package research directory.

### Implementation decisions and open questions

- Recommendation: select sources per question rather than requiring one API to
  cover the program.
- Recommendation: use human decisions for whole-category expansion or
  positioning conclusions.
- Open questions: acceptable paid-source budget, approved accounts, and
  privacy-compatible interview and measurement tools.

### Documentation

- Update `research-method.md` only when the approved concrete process refines
  its durable method.
- Add source assessments and machine-readable manifests under package research
  ownership.
- Keep credentials and raw source content outside tracked files.

### Task checklist

- [ ] Define the decision brief and hypothesis ledger.
- [ ] Assess candidate sources and access constraints.
- [ ] Define shared and source-specific record shapes.
- [ ] Define pilot, review, correction, expansion, and stop rules.
- [ ] Propose budgets and approval gates.
- [ ] Define evidence storage and privacy controls.
- [ ] Define adaptive handoff criteria.
- [ ] Obtain approval before paid or restricted collection.

### Requirement verification

- A later researcher can identify what decision each source supports.
- Retained evidence can be traced to source, date, query/route, and review.
- Paid and restricted source use cannot begin without explicit approval.
- Privacy, copyright, and disposable-output boundaries are testable.
