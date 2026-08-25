# Observe and Interview Early Users

Use the first evidence-informed website and current product to study
comprehension, activation, perceived value, switching behavior, transparency,
customization, and ordinary-to-power-user progression.

## Requirements checklist

- [ ] Participants represent relevant coding-agent usage patterns rather than
      one convenience sample only.
- [ ] Observation covers website understanding, installation or connection,
      first useful result, and reactions to selected product capabilities.
- [ ] Interviews investigate explicit needs, latent value, objections,
      switching behavior, duplicated setup, session continuity, transparency,
      and customization.
- [ ] Findings preserve participant privacy, selection bias, contradictory
      evidence, and uncertainty.
- [ ] The result produces decision-useful content, onboarding, product, and
      experiment recommendations without treating qualitative evidence as
      prevalence.

Parent Task: `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md`
Depends On: `tasks/20260825-crystal-lattice-product-positioning-and-website/090-first-evidence-informed-website-update.md`

## Candidate participant patterns

- users committed to one major coding agent;
- users switching among several coding agents or models;
- developers and vibe coders;
- users concerned about cost or context;
- mobile/remote users;
- self-hosting-oriented users;
- plugin or extension authors.

## References

### Start here

1. `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md:8-186`
   — shared requirements, questions, evidence distinctions, handoff rules,
   storage rules, and privacy boundaries.
2. `tasks/20260825-crystal-lattice-product-positioning-and-website/090-first-evidence-informed-website-update.md:1-114`
   plus its completion notes and deployed website — the actual content and
   first-use path participants will encounter. Stop if incomplete.
3. `landing_page/docs/development/research/research-method.md:79-102`,
   `landing_page/docs/development/research/research-method.md:161-200`, and
   `landing_page/docs/development/research/research-method.md:202-228` —
   interview interpretation, review, confidence, privacy, promotion, and
   progressive-revision rules.
4. `landing_page/docs/development/research/positioning-and-product-baseline.md:68-170`
   — hypotheses and open questions requiring observation or interview
   evidence.
5. Accepted findings and completion manifests from
   `tasks/20260825-crystal-lattice-product-positioning-and-website/050-built-in-feature-opportunity-mining.md:1-128`
   through
   `tasks/20260825-crystal-lattice-product-positioning-and-website/080-competitor-category-and-multi-agent-research.md:1-119`
   — prior external evidence used to select participants and prompts without
   leading them to desired answers.
6. `landing_page/research/README.md:32-84` — minimized retained evidence and
   private/raw exclusions.

## Known facts and supporting details

- Early-user recruiting intentionally follows a useful evidence-informed
  website rather than blocking it.
- Observation of actual comprehension and first use is different from an
  interview response.
- Spontaneous value statements must be distinguishable from reactions after a
  feature or positioning demonstration.
- Participant selection will be biased and cannot establish prevalence.
- Recording, compensation, contact, consent, and retention may require
  decisions or authority not granted by this task file alone.

## Expected outputs

Human-readable finding:

- `landing_page/docs/development/research/findings/early-user-observation-and-interviews.md`

Retained research package:

```text
landing_page/research/100-early-user-observation-and-interviews/
├── research-protocol.md
├── participant-sample.csv
├── observation-evidence.jsonl
├── interview-evidence.jsonl
├── coding-and-review.csv
├── comprehension-and-activation-map.csv
├── recommendation-handoff.md
└── completion-manifest.json
```

`participant-sample.csv` contains participant categories and research-relevant
attributes only, not names or contact details.

Required updates:

- `landing_page/docs/development/research/evidence-index.md`;
- `landing_page/docs/development/research/positioning-and-product-baseline.md`
  only for durable cross-task changes;
- a content handoff to
  `tasks/20260825-crystal-lattice-product-positioning-and-website/120-early-user-and-remote-access-informed-website-update.md`;
- a synthesis handoff to
  `tasks/20260825-crystal-lattice-product-positioning-and-website/130-positioning-and-product-architecture-synthesis.md`.

## Scope boundaries

- Do not recruit, contact, compensate, or record participants before the
  relevant protocol and authority are approved.
- Do not commit names, contact data, recordings, full transcripts, private
  sessions, credentials, or unnecessary personal details.
- Do not change public content or the content specification.
- Do not interpret qualitative themes as population prevalence.
- Store private/disposable material under
  `landing_page/artifacts/research/100-early-user-observation-and-interviews/`
  or an approved non-repository location.

## Execution plan

Status: Draft

Define research questions and a privacy-conscious interview/observation
protocol. Recruit through approved early-adopter channels after the updated
website is usable. Observe the actual first-use path before presenting product
explanations or positioning alternatives.

Use short capability demonstrations to test latent value, including session
organization, usage/cost visibility, active-agent transparency, switching
configured agents, mobile continuity, and natural-language customization
concepts. Synthesize findings without preserving unnecessary personal data.

### Implementation decisions and open questions

- Decision: recruiting does not block earlier website rewrites.
- Recommendation: separate spontaneous value statements from reactions after
  a feature demonstration.
- Open questions: recruitment channels, participant count, compensation,
  recording consent, and whether remote moderated testing is sufficient.

### Documentation

- Add anonymized early-user findings and limitations.
- Store consented minimized observation records and review notes under package
  research ownership.
- Keep recordings and full transcripts private/disposable unless separately
  approved.

### Task checklist

- [ ] Define protocol, participant groups, consent, and privacy handling.
- [ ] Recruit approved participants.
- [ ] Observe website and first-use comprehension.
- [ ] Conduct interviews and capability demonstrations.
- [ ] Normalize and anonymize observations.
- [ ] Review themes and contradictions.
- [ ] Produce content, product, and experiment recommendations.
- [ ] Hand findings to the next progressive rewrite and synthesis.

### Requirement verification

- Participants and methods are documented without unnecessary identifiers.
- Findings distinguish spontaneous, prompted, observed, and inferred evidence.
- Important contradictions and failed comprehension remain visible.
- Recommendations link representative evidence and limitations.
