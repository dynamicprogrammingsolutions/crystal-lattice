# Define Website Information Architecture and Content Briefs

Translate approved positioning and experiment results into the target page
hierarchy, audience routes, content responsibilities, claim/proof briefs,
compatibility placement, SEO intent, and release integration without
implementing the final website.

## Requirements checklist

- [ ] The homepage has one primary proposition and routes secondary audiences
      without becoming an exhaustive product manual.
- [ ] Page and shared-content responsibilities prevent duplicated,
      contradictory explanations.
- [ ] Every planned material claim is classified as current, conditional,
      evidence-needed, or prohibited and names appropriate proof.
- [ ] Compatibility, transparency, plugin/customization, mobile, desktop,
      remote-access, open-source, contributor, support, privacy, and docs
      content has an explicit home.
- [ ] Page briefs define purpose, audience, questions, proof, CTA, dependencies,
      and exclusions without writing final copy prematurely.

Parent Task: `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md`
Depends On: `tasks/20260825-crystal-lattice-product-positioning-and-website/140-proposition-feature-value-and-cta-experiments.md`

## Scope

Candidate routes remain hypotheses until this task decides them. The work must
coordinate with existing mobile, desktop, CLI, docs, privacy, support,
open-source, and bridge owners rather than duplicating their contracts.

## References

### Start here

1. `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md:8-186`
   — shared product requirements, decisions, handoff rules, output rules, and
   package/release boundaries.
2. `tasks/20260825-crystal-lattice-product-positioning-and-website/130-positioning-and-product-architecture-synthesis.md:1-124`
   plus its accepted proposition, audience, product-relationship, claim, and
   alternative outputs.
3. `tasks/20260825-crystal-lattice-product-positioning-and-website/140-proposition-feature-value-and-cta-experiments.md:1-113`
   plus its approved decision ledger and completion manifest. Stop if
   incomplete.
4. `landing_page/docs/development/specifications/product-website-content/content-spec.md:1-305`
   — current target to revise with approved architecture and content
   responsibilities.
5. `landing_page/docs/development/specifications/product-website-content/requirements.md:6-22`
   — live requirements and evidence state.
6. `landing_page/docs/development/content-system.md:7-161` — current
   implementation capability; briefs must not become YAML/component plans.
7. Release and package owners listed in
   `landing_page/docs/development/research/evidence-index.md:18-75` — current
   facts and detailed user guidance that page briefs may summarize or link.

## Known facts and supporting details

- The homepage needs one primary proposition and cannot serve as the complete
  documentation for every audience.
- Shared questions need one content owner to avoid divergent explanations.
- Compatibility and limitations are a first-class trust surface but do not
  redefine package behavior.
- Page briefs define communication outcomes and proof, not Astro section types.
- The architecture should remain useful if a secondary product hypothesis or
  managed-service state changes.

## Expected outputs

Package development content:

```text
landing_page/docs/development/content-briefs/
├── index.md
├── website-information-architecture.md
├── claim-and-proof-matrix.md
├── page-brief-manifest.md
└── pages/
    └── <approved-page-briefs>.md
```

Create `pages/` only when the approved page set is known and each brief is
substantive.

Retained decision package:

```text
landing_page/research/150-website-information-architecture-and-content-briefs/
├── input-decision-manifest.json
├── navigation-and-cta-map.csv
├── shared-content-ownership.csv
├── seo-intent-map.csv
├── implementation-handoff.md
└── completion-manifest.json
```

Required updates:

- `landing_page/docs/development/specifications/product-website-content/content-spec.md`;
- `landing_page/docs/development/specifications/product-website-content/requirements.md`;
- `landing_page/docs/development/index.md` and `landing_page/docs/index.md`
  when the new brief set needs discoverability;
- explicit visual requirements for
  `tasks/20260825-crystal-lattice-product-positioning-and-website/160-visual-proof-and-reproducible-assets.md`;
- exact implementation inputs for
  `tasks/20260825-crystal-lattice-product-positioning-and-website/170-validated-website-release-and-product-integration.md`.

## Scope boundaries

- Do not write final page copy or implement website routes/components.
- Do not encode YAML or Astro implementation choices in content briefs.
- Do not duplicate current provider, plugin, release, bridge, privacy, or app
  contracts.
- Do not create empty briefs for speculative routes.
- Store disposable wireframes and generated comparisons under
  `landing_page/artifacts/research/150-website-information-architecture-and-content-briefs/`.

## Execution plan

Status: Draft

Update the content specification with approved content architecture and visitor
outcomes. Define a page map, shared-content model, navigation, CTA hierarchy,
claim/evidence matrix, visual proof requirements, SEO intent, release
dependencies, and page briefs.

Preserve implementation flexibility: briefs should define communication
outcomes and content responsibilities rather than YAML section types or Astro
component choices.

### Implementation decisions and open questions

- Recommendation: route detailed executable guidance to focused pages or docs
  rather than placing every workflow on the homepage.
- Recommendation: make compatibility and limitations a first-class trust
  surface.
- Open questions: final route names, product naming, managed-service route,
  comparison content, and documentation-site publication relationships.

### Documentation

- Update `content-spec.md` and requirements with approved architecture.
- Add page briefs under package development ownership only when each brief has
  substantive content.
- Keep rendering and section implementation in content-system documentation.

### Task checklist

- [ ] Update target audience and proposition decisions.
- [ ] Define page hierarchy and shared content.
- [ ] Define navigation and CTA paths.
- [ ] Build claim/evidence and proof matrix.
- [ ] Define compatibility and contributor content.
- [ ] Define SEO intent and exclusions.
- [ ] Write substantive page briefs.
- [ ] Obtain human approval before final implementation.

### Requirement verification

- Every major visitor question has one clear owning page.
- Material claims have current evidence or are excluded/conditional.
- Page briefs are implementable without relying on conversation context.
- The architecture remains useful if a secondary product hypothesis changes.
