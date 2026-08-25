# Mine Built-In Features for Product Opportunities

Inspect the existing plugin and application feature set in adaptive, manageable
groups to discover user pains, workarounds, competitor gaps, proof
opportunities, and deeper research branches.

## Requirements checklist

- [ ] User-visible built-in and optional capabilities are mapped to concrete
      user jobs and current product surfaces.
- [ ] Each reviewed capability records readiness, limitations, affected
      configured agents/providers/clients, and default versus optional state.
- [ ] Search language, community language, competitor support, workaround
      products, explicit value, latent value, and risk are assessed where
      evidence permits.
- [ ] Adaptive follow-up handoffs are proposed only for coherent,
      decision-useful clusters discovered during the inventory.
- [ ] Findings identify which capabilities merit homepage proof, focused
      pages, compatibility content, documentation, experiments, or no
      marketing emphasis.

Parent Task: `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md`
Depends On:

- `tasks/20260825-crystal-lattice-product-positioning-and-website/040-research-foundation.md`
- `tasks/20260825-crystal-lattice-product-positioning-and-website/020-current-product-and-compatibility-baseline.md`

## Starting clusters

Potential routing groups include session organization, transparency and cost,
configured-agent compatibility, context/compaction, mobile/notifications,
customization, provider/auth/media settings, MCP/integrations, and advanced
operations. These are seeds, not fixed subtasks.

## References

### Start here

1. `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md:8-186`
   — shared requirements, current product decisions, handoff rules, output
   conventions, and research boundaries.
2. `tasks/20260825-crystal-lattice-product-positioning-and-website/020-current-product-and-compatibility-baseline.md:1-125`
   plus its completed outputs — authoritative factual catalog and evidence
   dimensions. Stop if incomplete.
3. `tasks/20260825-crystal-lattice-product-positioning-and-website/040-research-foundation.md:1-117`
   plus its completed outputs — approved source, schema, review, budget, pilot,
   and adaptive-handoff contracts. Stop if incomplete.
4. `landing_page/docs/development/research/research-method.md:104-173` —
   retained record shape, feature-opportunity fields, pilot, expansion, and
   review rules.
5. `landing_page/docs/development/research/positioning-and-product-baseline.md:107-149`
   — shared feature, compatibility, mobile, and bridge hypotheses.
6. `landing_page/docs/development/research/evidence-index.md:18-63` — initial
   configuration, plugin, configured-agent, and application-feature source
   map.
7. `application/python/agent_terminal_app/default_config/config.json:514-568`
   and `application/python/agent_terminal_app/default_config/config.json:710-870`
   — globally loaded plugins, application settings, and configured-agent
   plugin composition.
8. `plugins/docs/index.md:1-32` — plugin documentation router. Follow a
   package's README, AGENTS, docs, manifests, source, and tests only when its
   inventory row or verification requires them.

## Known facts and supporting details

- The factual inventory from
  `tasks/20260825-crystal-lattice-product-positioning-and-website/020-current-product-and-compatibility-baseline.md`
  is an input; this task adds user-job, pain, workaround, competitor, proof,
  and research-priority interpretation.
- Default configuration and plugin manifests are the first inventory route;
  reading every plugin implementation before clustering is unnecessary.
- Explicit searched pain and latent value revealed by demonstration must be
  kept separate.
- Application-wide features, configured-agent compatibility, provider/account
  behavior, and frontend support are different dimensions.
- Follow-up handoffs are proposed only after the inventory identifies coherent
  non-overlapping clusters.

## Expected outputs

Human-readable finding:

- `landing_page/docs/development/research/findings/built-in-feature-opportunity-map.md`

Retained research package:

```text
landing_page/research/050-built-in-feature-opportunity-mining/
├── input-manifest.json
├── plugin-inventory.jsonl
├── feature-opportunity-matrix.csv
├── external-evidence.jsonl
├── search-and-community-seed-catalog.csv
├── proof-and-placement-map.csv
├── manual-review.csv
├── adaptive-handoff-proposals.md
└── completion-manifest.json
```

Required updates:

- `landing_page/docs/development/research/evidence-index.md`;
- `landing_page/docs/development/research/positioning-and-product-baseline.md`
  only for durable corrected facts or materially changed shared hypotheses;
- outputs from
  `tasks/20260825-crystal-lattice-product-positioning-and-website/020-current-product-and-compatibility-baseline.md`
  only when a factual catalog error is discovered;
- concrete terminology/hypothesis handoffs to
  `tasks/20260825-crystal-lattice-product-positioning-and-website/060-search-demand-and-terminology.md`,
  `tasks/20260825-crystal-lattice-product-positioning-and-website/070-community-problems-and-workarounds.md`,
  `tasks/20260825-crystal-lattice-product-positioning-and-website/080-competitor-category-and-multi-agent-research.md`,
  and
  `tasks/20260825-crystal-lattice-product-positioning-and-website/090-first-evidence-informed-website-update.md`.

## Scope boundaries

- Do not modify `landing_page/src/content/` or the product-content
  specification.
- Do not update a roadmap.
- Do not create follow-up task files or execute parallel handoffs without user
  approval.
- Do not start broad external collection before the bounded pilot and its
  checkpoint are approved.
- Do not treat plugin, issue, discussion, product, or search counts as value by
  themselves.
- Store disposable output under
  `landing_page/artifacts/research/050-built-in-feature-opportunity-mining/`.

## Execution plan

Status: Draft

Create a complete package/plugin inventory, then review it in bounded thematic
batches. For each feature, record product behavior and evidence before
searching for related pain, workarounds, or competitors.

Use parallel handoffs only after the initial inventory defines non-overlapping
clusters and source boundaries. Synthesize the results into a feature-to-job
map, research seed catalog, proof map, and recommended follow-up branches.

### Implementation decisions and open questions

- Decision: do not pre-create one task per plugin or feature.
- Recommendation: separate explicit searched pain from latent value revealed
  only through demonstrations.
- Open question: decide which clusters justify independent tasks after the
  initial inventory and pilot.

### Documentation

- Add a substantive built-in-feature opportunity finding page.
- Store normalized inventories and evidence under `landing_page/research/`.
- Update the evidence index and compatibility baseline where factual gaps are
  discovered.

### Task checklist

- [ ] Build the complete feature/plugin inventory.
- [ ] Define bounded thematic batches.
- [ ] Review current behavior, readiness, and limitations.
- [ ] Pilot external pain/workaround discovery.
- [ ] Propose and execute approved adaptive handoffs.
- [ ] Synthesize feature, proof, and research-priority maps.
- [ ] Record counterevidence and low-value branches.
- [ ] Hand concrete terminology and hypotheses to
      `tasks/20260825-crystal-lattice-product-positioning-and-website/060-search-demand-and-terminology.md`,
      `tasks/20260825-crystal-lattice-product-positioning-and-website/070-community-problems-and-workarounds.md`,
      `tasks/20260825-crystal-lattice-product-positioning-and-website/080-competitor-category-and-multi-agent-research.md`,
      and
      `tasks/20260825-crystal-lattice-product-positioning-and-website/090-first-evidence-informed-website-update.md`.

### Requirement verification

- Every conclusion maps to current product evidence and, where applicable,
  external evidence.
- Default, optional, partial, and unavailable behavior is distinguishable.
- Dynamic handoffs do not overlap or hide unreviewed scope.
- Marketing recommendations identify proof and claim limitations.
