# Research Community Problems and Workarounds

Investigate how coding-agent users describe session, transparency,
multi-agent, customization, mobile, cost, context, and workflow problems, and
which scripts, proxies, viewers, dashboards, plugins, or paid products they use
to compensate.

## Requirements checklist

- [ ] Relevant discussions retain source, date, discovery route, bounded
      excerpts, and access provenance.
- [ ] Evidence is classified by user role, problem, context, workaround,
      desired outcome, urgency, switching signal, and direction.
- [ ] Technical symptoms, feature requests, seller promotion, tutorials,
      explicit user value, and willingness-to-pay evidence remain separate.
- [ ] Supporting and contradictory evidence for current positioning
      hypotheses is preserved.
- [ ] Findings produce reusable user language and decision-useful feature or
      content recommendations without treating discussion counts as market
      size.

Parent Task: `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md`
Depends On: `tasks/20260825-crystal-lattice-product-positioning-and-website/040-research-foundation.md`

## Scope

Potential sources include public Reddit, Hacker News, Stack Exchange, GitHub
Discussions/issues, app reviews, product forums, and other permitted public
communities. Source access and persistence rules are reassessed before
collection.

## References

### Start here

1. `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md:8-186`
   — shared requirements, evidence distinctions, decisions, handoff rules,
   output rules, and research boundaries.
2. `tasks/20260825-crystal-lattice-product-positioning-and-website/040-research-foundation.md:1-117`
   plus its completed outputs — approved source-access, evidence schema,
   review, privacy, budget, and expansion rules. Stop if incomplete.
3. `tasks/20260825-crystal-lattice-product-positioning-and-website/050-built-in-feature-opportunity-mining.md:1-128`
   plus its completed search/community seed catalog — product-derived problem
   families and workaround hypotheses. If incomplete, use only the
   foundation-approved initial scope and record the missing input.
4. `landing_page/docs/development/research/research-method.md:45-77`,
   `landing_page/docs/development/research/research-method.md:104-124`, and
   `landing_page/docs/development/research/research-method.md:161-200` —
   community/issue interpretation, retained record shape, review, confidence,
   privacy, and copyright rules.
5. `landing_page/docs/development/research/positioning-and-product-baseline.md:68-170`
   — hypotheses and open questions that community evidence may support or
   contradict.
6. `landing_page/research/README.md:42-94` — retained evidence, exclusions,
   review, and lineage.

## Known facts and supporting details

- Community records expose language, workarounds, objections, and context; raw
  counts do not represent market size.
- Technical symptoms, feature requests, explicit switching intent, explicit
  commercial signals, tutorials, seller promotion, and source noise require
  separate classifications.
- Search snippets are discovery aids; retained evidence should use the source
  page when accessible.
- Usernames, profiles, inferred personal attributes, private/deleted content,
  and outreach lists are unnecessary.
- Workaround products discovered here feed competitor research but are not
  automatically direct competitors.

## Expected outputs

Human-readable finding:

- `landing_page/docs/development/research/findings/community-problems-and-workarounds.md`

Retained research package:

```text
landing_page/research/070-community-problems-and-workarounds/
├── source-access-assessment.md
├── query-manifest.json
├── normalized-community-evidence.jsonl
├── manual-review.csv
├── problem-language-map.csv
├── workaround-product-map.csv
├── exclusion-and-counterevidence.csv
└── completion-manifest.json
```

Required updates:

- `landing_page/docs/development/research/evidence-index.md`;
- `landing_page/docs/development/research/positioning-and-product-baseline.md`
  only for durable cross-task changes;
- source and terminology handoffs to
  `tasks/20260825-crystal-lattice-product-positioning-and-website/080-competitor-category-and-multi-agent-research.md`
  and
  `tasks/20260825-crystal-lattice-product-positioning-and-website/090-first-evidence-informed-website-update.md`.

## Scope boundaries

- Do not contact users, infer identities, or build prospect lists.
- Do not bypass login walls, CAPTCHAs, private APIs, robots restrictions, or
  other access controls.
- Do not commit full pages, discussion threads, browser state, or unnecessary
  personal data.
- Do not change public content, the content specification, or roadmaps.
- Store raw browser/API output under
  `landing_page/artifacts/research/070-community-problems-and-workarounds/`.

## Execution plan

Status: Draft

Start with bounded source/query pilots across major problem families. Prefer
source pages over search snippets, minimize personal data, and preserve
workarounds and counterevidence. Expand only productive branches.

Manually review a stratified sample and correct systematic classification
errors before synthesis. Identify terms and representative cases for the first
evidence-informed rewrite and later user research.

### Implementation decisions and open questions

- Decision: community counts are not market-size evidence.
- Recommendation: preserve products and scripts used as workarounds for later
  competitor research without treating every workaround as a direct
  competitor.
- Open question: which authenticated or restricted communities, if any, are
  necessary after public-source pilots.

### Documentation

- Add community problem and workaround findings.
- Retain normalized minimized evidence and review records under package
  research ownership.
- Keep raw pages, browser state, and full threads under ignored artifacts or
  do not retain them.

### Task checklist

- [ ] Assess sources and terms.
- [ ] Define problem/query families.
- [ ] Run bounded pilots.
- [ ] Expand productive branches.
- [ ] Normalize and deduplicate retained evidence.
- [ ] Classify problems, workarounds, outcomes, and direction.
- [ ] Complete stratified manual review.
- [ ] Produce user-language, feature, counterevidence, and content handoffs.

### Requirement verification

- Retained evidence is attributable and minimized.
- Manual review covers major sources, families, directions, and engagement.
- Seller, tutorial, technical-only, and user-value evidence is distinguishable.
- Blocked or inaccessible routes are recorded rather than bypassed.
