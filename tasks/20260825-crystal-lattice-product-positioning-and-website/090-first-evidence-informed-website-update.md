# Publish the First Evidence-Informed Website Update

Revise the early-user website using accepted built-in feature, search,
community, and competitor findings without waiting for early-user interviews
or the final positioning program.

## Requirements checklist

- [ ] The leading message and feature order reflect accepted early research
      rather than only the original brainstorm.
- [ ] Community-described problems and current competitor expectations inform
      terminology, proof, and audience paths.
- [ ] The update includes an honest compatibility/transparency preview where
      the current baseline supports it.
- [ ] The website remains a coherent current product experience rather than a
      research report or exhaustive plugin catalog.
- [ ] Build, accessibility, responsive, visual, command, link, and production
      verification pass.

Parent Task: `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md`
Depends On:

- `tasks/20260825-crystal-lattice-product-positioning-and-website/030-release-safe-early-user-website.md`
- `tasks/20260825-crystal-lattice-product-positioning-and-website/050-built-in-feature-opportunity-mining.md`
- `tasks/20260825-crystal-lattice-product-positioning-and-website/060-search-demand-and-terminology.md`
- `tasks/20260825-crystal-lattice-product-positioning-and-website/070-community-problems-and-workarounds.md`
- `tasks/20260825-crystal-lattice-product-positioning-and-website/080-competitor-category-and-multi-agent-research.md`

## Scope

This update may adjust the homepage, feature hierarchy, compatibility preview,
transparency explanation, multi-agent convenience, and audience routes. It
does not need to finalize hosted bridge positioning, user segmentation, or the
long-term page architecture.

## References

### Start here

1. `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md:8-186`
   — shared requirements, approved content/research decisions, handoff rules,
   output rules, and public boundaries.
2. `tasks/20260825-crystal-lattice-product-positioning-and-website/030-release-safe-early-user-website.md:1-128`
   plus its completion notes and deployed/current outputs — starting public
   website baseline. Stop if incomplete.
3. `tasks/20260825-crystal-lattice-product-positioning-and-website/050-built-in-feature-opportunity-mining.md:1-128`,
   `tasks/20260825-crystal-lattice-product-positioning-and-website/060-search-demand-and-terminology.md:1-115`,
   `tasks/20260825-crystal-lattice-product-positioning-and-website/070-community-problems-and-workarounds.md:1-111`,
   and
   `tasks/20260825-crystal-lattice-product-positioning-and-website/080-competitor-category-and-multi-agent-research.md:1-119`
   plus their accepted findings and completion manifests — required evidence
   inputs. Stop if any dependency is incomplete.
4. `landing_page/docs/development/specifications/product-website-content/content-spec.md:92-274`
   — proposition, audience paths, compatibility, transparency, features,
   customization, connection, current/future, proof, and revision target.
5. `landing_page/docs/development/specifications/product-website-content/requirements.md:6-22`
   — live requirement state to update.
6. `landing_page/docs/development/content-system.md:7-148` — current authoring,
   rendering, asset, and verification behavior.
7. `landing_page/src/content/pages/home.yaml:1-441` and the current content
   files changed by
   `tasks/20260825-crystal-lattice-product-positioning-and-website/030-release-safe-early-user-website.md:1-128`
   — implementation starting point.

## Known facts and supporting details

- This is the first rewrite that may change emphasis using external evidence.
- Built-in feature, search, community, and competitor findings are all
  required; early-user interviews and managed-bridge viability are not.
- Research findings can conflict and must be reconciled into one coherent
  current page rather than pasted into separate sections.
- The website remains current product content, not a research report.
- Any changed intended communication target must be recorded in the content
  specification before implementation.

## Expected outputs

Content decision:

- `landing_page/docs/development/research/findings/first-evidence-informed-content-decision.md`

Required target/state updates:

- `landing_page/docs/development/specifications/product-website-content/content-spec.md`;
- `landing_page/docs/development/specifications/product-website-content/requirements.md`.

Current implementation outputs:

- updated `landing_page/src/content/pages/home.yaml`;
- only the additional current page, Markdown, navigation, footer, section, or
  component files justified by the approved content decision;
- focused tests or content validation for introduced behavior.

Verification outputs:

- successful build and relevant browser checks;
- desktop/mobile visual and accessibility observations;
- command/link/release-fact validation;
- production evidence only when deployment is separately authorized.

## Scope boundaries

- Do not wait for
  `tasks/20260825-crystal-lattice-product-positioning-and-website/100-early-user-observation-and-interviews.md`
  or
  `tasks/20260825-crystal-lattice-product-positioning-and-website/110-remote-access-and-bridge-viability.md`.
- Do not claim a final positioning architecture or managed-service offer.
- Do not publish research confidence, task, experiment, or evidence-tracking
  language.
- Do not add a feature merely because it exists; include only evidence-backed
  content serving the selected current message.
- Store draft previews and captures under
  `landing_page/artifacts/research/090-first-evidence-informed-website-update/`.

## Execution plan

Status: Draft

Review the accepted findings and explicit content recommendations. Choose the
smallest coherent website changes with enough evidence to improve the current
experience. Update the content specification first when the target changes,
then implement through the existing content system.

Use real current proof and omit findings that cannot yet be translated into a
supported public claim. Validate locally and visually, prepare production
deployment, and obtain the required confirmation before remote mutation.

### Implementation decisions and open questions

- Decision: community and competitor research are required inputs.
- Decision: early-user interviews and bridge viability are not blockers.
- Open question: select the leading early evidence direction from the accepted
  research rather than predetermining it in this task.

### Documentation

- Update accepted research findings and the evidence index.
- Update content specification and requirements for changed target outcomes.
- Keep current implementation documentation aligned if section/page mechanics
  change.

### Task checklist

- [ ] Review accepted source findings and contradictions.
- [ ] Select the bounded content changes.
- [ ] Update target content and requirements.
- [ ] Implement public copy and proof changes.
- [ ] Run automated and visual validation.
- [ ] Obtain deployment approval.
- [ ] Deploy and verify when authorized.
- [ ] Prepare the deployed site for early-user recruiting.

### Requirement verification

- Content decisions trace to accepted findings without exposing research
  mechanics publicly.
- The page remains understandable to an unfamiliar early user.
- Compatibility and comparison wording stays within verified boundaries.
- Production behavior and links match the approved current content.
