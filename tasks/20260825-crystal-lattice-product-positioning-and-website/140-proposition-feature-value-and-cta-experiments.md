# Test Propositions, Feature Value, and Calls to Action

Run bounded experiments that test the decision-critical positioning,
audience, feature, compatibility, customization, remote-access, and action-path
hypotheses selected by the synthesis.

## Requirements checklist

- [ ] Each experiment states the decision, audience, hypothesis, alternative,
      method, success interpretation, limitations, and stop condition.
- [ ] Experiments test comprehension and action rather than visual preference
      alone.
- [ ] Feature demonstrations distinguish spontaneous need from value revealed
      after exposure.
- [ ] Results preserve invalidated, weakened, contradictory, and inconclusive
      outcomes.
- [ ] No experiment charges for, promises, or exposes an unavailable product or
      unsafe service.

Parent Task: `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md`
Depends On: `tasks/20260825-crystal-lattice-product-positioning-and-website/130-positioning-and-product-architecture-synthesis.md`

## Candidate experiment areas

- coding-agent versus platform category language;
- one workspace across configured-agent styles;
- transparency and active-agent inspection;
- session/workflow feature value;
- natural-language customization;
- compatibility catalog usefulness;
- mobile and managed remote-access interest;
- first action and CTA;
- ordinary versus advanced disclosure.

## References

### Start here

1. `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md:8-186`
   — shared requirements, open decisions, evidence distinctions, handoff rules,
   output rules, privacy, and remote-action boundaries.
2. `tasks/20260825-crystal-lattice-product-positioning-and-website/130-positioning-and-product-architecture-synthesis.md:1-124`
   plus its accepted synthesis package and experiment handoff. Stop if
   incomplete.
3. `landing_page/docs/development/research/research-method.md:79-102`,
   `landing_page/docs/development/research/research-method.md:146-188`, and
   `landing_page/docs/development/research/research-method.md:190-217` —
   observation/experiment evidence, pilot, review, confidence, privacy, and
   content-promotion rules.
4. `landing_page/docs/development/specifications/product-website-content/content-spec.md:92-218`
   and `landing_page/docs/development/specifications/product-website-content/content-spec.md:258-305`
   — candidate proposition, audience, compatibility, transparency,
   progressive-revision, non-goal, and acceptance boundaries.
5. Current website content and proof delivered by
   `tasks/20260825-crystal-lattice-product-positioning-and-website/120-early-user-and-remote-access-informed-website-update.md:1-102`
   — source material for variants, not a default control that must win.
6. `landing_page/src/content/markdown/privacy.md:71-87` — current website
   logging/analytics and support-correspondence statements that constrain
   measurement choices.

## Known facts and supporting details

- An experiment exists to resolve a material decision, not to measure visual
  preference without consequence.
- Moderated comprehension can proceed before traffic analytics, while
  behavioral or waitlist tests require an approved measurement/privacy path.
- Spontaneous need and value revealed after a demonstration must be recorded
  separately.
- Variants, interpretation rules, and stop conditions must be frozen before
  results are reviewed.
- Interest, clicks, waitlist signup, product activation, and payment are
  different evidence.

## Expected outputs

Human-readable finding:

- `landing_page/docs/development/research/findings/proposition-feature-value-and-cta-experiments.md`

Retained experiment package:

```text
landing_page/research/140-proposition-feature-value-and-cta-experiments/
├── experiment-catalog.json
├── frozen-variants/
├── observation-evidence.jsonl
├── result-summaries.csv
├── decision-ledger.md
├── limitations.md
└── completion-manifest.json
```

Create `frozen-variants/` only when approved variants exist.

Required updates:

- `landing_page/docs/development/research/evidence-index.md`;
- `landing_page/docs/development/research/positioning-and-product-baseline.md`
  for approved durable decisions;
- an architecture/content-decision handoff to
  `tasks/20260825-crystal-lattice-product-positioning-and-website/150-website-information-architecture-and-content-briefs.md`.

## Scope boundaries

- Do not implement the final website or change the content specification until
  decisions are approved.
- Do not enable analytics, create public waitlists, spend money, recruit
  participants, or mutate remote services without the corresponding approval.
- Do not charge for or promise unavailable behavior.
- Do not redefine success after results are known.
- Store draft variants, browser captures, and raw experiment output under
  `landing_page/artifacts/research/140-proposition-feature-value-and-cta-experiments/`.

## Execution plan

Status: Draft

Choose the smallest set of experiments capable of changing a material content
or product decision. Begin with moderated comprehension and low-fidelity
variants, then use traffic, waitlist, or behavioral tests only when approved
measurement and privacy controls exist.

Freeze variants and expected interpretations before observing results. Do not
retrofit success criteria to the outcome. Produce explicit proceed, revise,
defer, reject, or unresolved recommendations.

### Implementation decisions and open questions

- Decision: do not attempt to test every feature or message.
- Recommendation: prefer high decision value and current product proof.
- Open questions: available participant/traffic sources, approved measurement,
  experiment duration, and minimum evidence needed for each decision.

### Documentation

- Store experiment definitions, inputs, observations, and analyses under
  package research ownership.
- Update durable findings and content recommendations.
- Update the content specification only after approved decisions.

### Task checklist

- [ ] Select and approve experiment set.
- [ ] Define frozen variants and interpretations.
- [ ] Verify privacy and measurement readiness.
- [ ] Run comprehension and demonstration tests.
- [ ] Run approved behavioral or waitlist tests where justified.
- [ ] Analyze results and limitations.
- [ ] Record decisions, rejected hypotheses, and unresolved questions.
- [ ] Hand approved outcomes to website architecture.

### Requirement verification

- Experiment records preserve inputs, dates, audience, method, and results.
- Conclusions do not exceed the tested population or method.
- Negative and inconclusive results remain visible.
- No unavailable capability is represented as delivered.
