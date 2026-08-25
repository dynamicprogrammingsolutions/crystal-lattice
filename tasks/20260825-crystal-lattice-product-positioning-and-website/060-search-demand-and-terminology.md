# Research Search Demand and Terminology

Investigate how potential users search for coding-agent workspaces,
multi-agent convenience, transparency, session management, customization,
mobile continuity, and broader agent use.

## Requirements checklist

- [ ] Search evidence retains market, language, query, date, source, and metric
      provenance.
- [ ] Queries are organized by user problem, product category, audience,
      intent, and candidate website path.
- [ ] Internal terms are compared with the language searchers and result pages
      actually use.
- [ ] Search demand, result composition, commercial signals, and low/no-demand
      findings remain distinct.
- [ ] Findings produce concrete terminology and SEO/content recommendations
      without treating volume as product fit.

Parent Task: `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md`
Depends On: `tasks/20260825-crystal-lattice-product-positioning-and-website/040-research-foundation.md`

## Starting query families

- coding agents on mobile or away from the computer;
- one interface for Claude Code, Codex, Gemini, Qwen, or other agents;
- coding-agent session search, archive, filter, status, and history;
- token, context, usage, and cost visibility;
- inspect system prompt, tools, or request payload;
- coding-agent plugins and customization;
- self-hosted/open coding agents;
- existing-session import or continuity;
- coding-agent versus general-purpose agent workflows.

## References

### Start here

1. `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md:8-186`
   — shared requirements, questions, content/research decisions, handoff rules,
   output conventions, and boundaries.
2. `tasks/20260825-crystal-lattice-product-positioning-and-website/040-research-foundation.md:1-117`
   plus its completed outputs — approved sources, markets/languages, schemas,
   budget, review rules, and collection gates. Stop if incomplete.
3. `tasks/20260825-crystal-lattice-product-positioning-and-website/050-built-in-feature-opportunity-mining.md:1-128`
   plus its completed seed catalog and handoff — feature-derived user problems
   and terminology. If
   `tasks/20260825-crystal-lattice-product-positioning-and-website/050-built-in-feature-opportunity-mining.md:1-128`
   is incomplete, use only the foundation-approved initial query scope and
   record the missing input.
4. `landing_page/docs/development/research/research-method.md:34-43` and
   `landing_page/docs/development/research/research-method.md:146-188` —
   search-evidence interpretation, pilot, review, and confidence rules.
5. `landing_page/docs/development/research/positioning-and-product-baseline.md:68-170`
   — current category, multi-agent, transparency, customization, mobile, and
   general-purpose hypotheses.
6. `landing_page/docs/development/research/evidence-index.md:77-106` — method
   origin and external source seeds; refresh every current source used.

## Known facts and supporting details

- Search demand can reveal language and relative demand but cannot establish
  product fit, adoption, conversion, or willingness to pay.
- Product-name navigation, informational troubleshooting, jobs, communities,
  utilities, and direct product intent must remain distinguishable.
- Internal terms such as harness, provider-native, or application plugin may
  have little search demand even when the underlying user problem is valuable.
- Feature mining supplies seeds, not a closed taxonomy.
- Market/language expansion should follow pilot yield and product release
  relevance rather than equal coverage of every country.

## Expected outputs

Human-readable finding:

- `landing_page/docs/development/research/findings/search-demand-and-terminology.md`

Retained research package:

```text
landing_page/research/060-search-demand-and-terminology/
├── source-assessment.md
├── query-catalog.csv
├── collection-manifest.json
├── normalized-search-evidence.jsonl
├── serp-observation-evidence.jsonl
├── manual-review.csv
├── terminology-and-intent-map.csv
├── stopped-branch-audit.csv
└── completion-manifest.json
```

`serp-observation-evidence.jsonl` is created only when result-page evidence is
actually collected; the completion manifest records a not-used or blocked
source instead of creating an empty placeholder.

Required updates:

- `landing_page/docs/development/research/evidence-index.md`;
- `landing_page/docs/development/research/positioning-and-product-baseline.md`
  only for materially changed shared hypotheses or terminology;
- a concrete content handoff for
  `tasks/20260825-crystal-lattice-product-positioning-and-website/090-first-evidence-informed-website-update.md`.

## Scope boundaries

- Do not change current public copy or the content specification.
- Do not upload campaign keywords, run advertising, or infer lead quality.
- Do not use paid or restricted sources beyond the approved decisions in
  `tasks/20260825-crystal-lattice-product-positioning-and-website/040-research-foundation.md`.
- Do not claim that a zero or missing volume means a user problem does not
  exist.
- Store raw responses, caches, and temporary analysis under
  `landing_page/artifacts/research/060-search-demand-and-terminology/`.

## Execution plan

Status: Draft

Run a bounded broad terminology and demand pilot before localized or paid
expansion. Preserve exact queries and inspect result composition so vendor,
documentation, job, community, utility, and direct-product interpretations are
not collapsed.

Use findings from feature mining as seeds while allowing the data to introduce
new language and product branches. Require approval before paid API use or
larger localized collection.

### Implementation decisions and open questions

- Recommendation: prioritize English-language global/category discovery first,
  then select markets based on observed relevance and product release goals.
- Recommendation: keep navigational searches for major product names separate
  from problem and category demand.
- Open question: which paid keyword/SERP source and budget, if any, is
  justified after the pilot.

### Documentation

- Add search-demand and terminology findings.
- Store query catalogs, normalized metrics, SERP records, reviews, and
  manifests under package research ownership.
- Update content recommendations, not current public copy.

### Task checklist

- [ ] Define initial queries and markets.
- [ ] Assess search and keyword sources.
- [ ] Run and review the bounded pilot.
- [ ] Refine or stop noisy query families.
- [ ] Obtain approval for any paid expansion.
- [ ] Collect approved expanded evidence.
- [ ] Review result composition and terminology.
- [ ] Produce concrete recommendations and counterevidence.

### Requirement verification

- Every reported query and metric retains source and date provenance.
- Result composition is manually reviewable.
- Search volume is not described as adoption, conversion, or willingness to
  pay.
- Findings identify both productive and weakened terminology.
