# Crystal Lattice Product Positioning and Website

Build an evidence-informed product website that helps early users immediately,
improves progressively as research arrives, and eventually communicates a
validated primary proposition, audience paths, compatibility, transparency,
and release choices.

## Requirements checklist

### Functional requirements

- [ ] Every deployed website version gives an unfamiliar early user an
      accurate explanation of Crystal Lattice and a useful first action.
- [ ] The website progressively incorporates product, feature, search,
      community, competitor, early-user, and remote-access findings without
      waiting for the complete research program.
- [ ] The final validated content selects one primary proposition while
      providing clear paths for users, compatibility evaluators, customizers,
      builders, mobile users, and contributors.
- [ ] Configured-agent, provider/account, application-feature, limitation, and
      contribution information is presented transparently.
- [ ] Mobile, desktop, CLI, open-source, local-network, user-operated bridge,
      and future managed-service states are integrated from their owning
      release sources.

### Non-functional requirements

- [ ] Public claims remain current, attributable, accessible, privacy-aware,
      and free of internal progress language or visible planning placeholders.
- [ ] Durable website knowledge, specifications, findings, and retained
      evidence are owned under `landing_page/`; task tracking remains under
      `tasks/`; disposable output remains ignored.
- [ ] Search volume, discussions, feature requests, competitor claims,
      interviews, experiments, and observed product behavior remain distinct
      evidence types with explicit limitations.
- [ ] The program preserves contradictory evidence and may revise or abandon
      initial positioning hypotheses.

## Requirement questions

- Which proposition and visitor group should receive primary homepage
  emphasis after research and experiments?
- Should general-purpose agent use remain secondary to coding-agent
  positioning or become a major product path?
- Which transparency details should be visible by default versus progressively
  disclosed?
- Does natural-language plugin customization become a product capability worth
  leading with?
- What managed remote-access bundle and price, if any, is justified?
- Which privacy-compatible measurement approach should be adopted?

## Approved structure and decisions

- The content system and product content are separate concerns.
- `landing_page/docs/development/content-system.md` documents current YAML,
  Markdown, Astro, section, and rendering behavior.
- `landing_page/docs/development/specifications/product-website-content/`
  defines copywriting and visitor-understanding targets without a mandatory
  technical-spec page.
- Research knowledge belongs under
  `landing_page/docs/development/research/`; normalized retained evidence
  belongs under `landing_page/research/`; disposable output belongs under
  ignored `landing_page/artifacts/`.
- The website uses several progressive rewrites.
- Community and competitor research complete before the first
  evidence-informed rewrite.
- Early-user recruiting and interviews do not block the release-safe or first
  evidence-informed website.
- Current positioning begins coding-agent-first until evidence and delivered
  defaults justify a different target.
- Crystal Lattice compatibility profiles must not be presented as official
  upstream products or sessions.

## Known facts and supporting details

- The previous landing-page work explicitly described its result as
  intermediate.
- The current default configuration is coding-agent-oriented and contains
  several compatibility-oriented configured agents.
- Current application plugins already provide substantial session,
  organization, action, notification, settings, and transparency behavior.
- First-party coding-agent products now provide mobile continuity, so phone
  access is important but not sufficient differentiation.
- The release roadmap contains a placeholder website dependency for external
  iOS review and a separate desktop landing-page task.

## Shared handoff rules

Every subtask in this directory must remain understandable and executable if
its `## Execution plan` section is removed and rewritten.

Before planning or execution, the assigned agent must:

1. read the subtask's `### Start here` references in order; that list, not the
   main-task catalog below, defines its required external context;
2. read this main task's shared requirements, questions, decisions, facts,
   storage rules, and boundaries;
3. read the parent and every declared dependency;
4. stop and report the blocker when a dependency's required outputs or
   acceptance evidence are incomplete;
5. read `landing_page/AGENTS.md` before changing or creating files under
   `landing_page/`;
6. treat line ranges as context bounds for the current revision and re-locate
   the named section if earlier edits have shifted those lines;
7. keep supporting facts, references, expected outputs, and scope boundaries
   outside the replaceable execution plan.

An agent may inspect additional code, tests, or package documentation when a
listed source directs it there or when verification of a specific claim
requires it. It should not bulk-read the repository merely because a task is
exploratory.

## References

### Start here for main-task orchestration

1. `landing_page/AGENTS.md:1-97` — package-specific content, claim, research,
   privacy, visual, output, and verification boundaries. Follow its reading
   routes when the subtask touches website or research files.
2. `landing_page/docs/development/specifications/product-website-content/content-spec.md:1-305`
   — durable copywriting and visitor-understanding target. Research tasks use
   it as a decision boundary, not as proof that a hypothesis is true.
3. `landing_page/docs/development/specifications/product-website-content/requirements.md:1-22`
   — live implementation, verification, documentation, and evidence state.
4. `landing_page/docs/development/research/positioning-and-product-baseline.md:1-181`
   — shared verified facts, observations, hypotheses, recommendations, and
   questions. Update rather than duplicate it when a cross-task baseline
   changes.
5. `landing_page/docs/development/research/research-method.md:1-228` —
   evidence-role, record, pilot, review, confidence, privacy, promotion, and
   progressive-revision rules.
6. `landing_page/docs/development/research/evidence-index.md:1-106` — current
   local source map and initial external-source routes.
7. `landing_page/research/README.md:1-84` — retained evidence, excluded raw
   material, review, and lineage rules.

### Additional shared references

- `landing_page/docs/development/content-system.md:1-148` — current YAML,
  Markdown, Astro, section, asset, build, and rendering behavior. Required for
  rewrite or implementation tasks; research tasks need it only when a
  recommendation depends on current presentation capability.
- `landing_page/README.md:1-137` — package build, preview, public URL, and
  documentation routes.
- `tasks/20260611-landing-page-positioning-update/000-main.md:1-140` and
  `tasks/20260611-landing-page-positioning-update/resources/6421366435434d79a999bbd9a4a1e812-website-content-brainstorm.md:25-190`
  — historical intermediate content direction and original product brainstorm.
  Use them as prior hypotheses, not current authority.

## Expected outputs

- Human-readable durable findings belong under
  `landing_page/docs/development/research/findings/` using the exact filename
  declared by the owning subtask.
- Retained machine-readable evidence for a subtask belongs under
  `landing_page/research/<subtask-number>-<subtask-slug>/`.
- Disposable raw responses, caches, browser captures, intermediate
  classifications, draft screenshots, and generated previews belong under
  `landing_page/artifacts/research/<subtask-number>-<subtask-slug>/` or another
  task-declared ignored package-artifacts path.
- Current public copy belongs under `landing_page/src/content/`.
- Approved production visual files belong under `landing_page/public/`.
- Current implementation documentation belongs under
  `landing_page/docs/development/`.
- Intended product communication belongs in the product website content
  specification and requirements.
- Every retained research package must identify its input manifest,
  authoritative outputs, transformation/version information, manual-review
  inputs, limitations, and completion status.
- Do not create empty output directories or placeholder documents.

## Scope boundaries

- Research findings do not update public content or the content specification
  automatically.
- A rewrite task may update the content specification first when an approved
  content decision changes the target.
- Research tasks do not update roadmaps, deploy the website, create follow-up
  task files, spend money, register accounts, use restricted credentials, or
  contact external people without explicit authority.
- Public website tasks do not redefine provider, plugin, mobile, desktop, CLI,
  bridge, account, security, or release contracts owned by other packages.
- Production deployment and other remote mutations require the confirmation
  applicable at execution time.
- No task may weaken evidence review, privacy, accessibility, claim accuracy,
  or verification merely to produce an apparent completion.

## Subtasks

- [x] `tasks/20260825-crystal-lattice-product-positioning-and-website/010-website-documentation-and-content-specification-foundation.md`
- [ ] `tasks/20260825-crystal-lattice-product-positioning-and-website/020-current-product-and-compatibility-baseline.md`
- [ ] `tasks/20260825-crystal-lattice-product-positioning-and-website/030-release-safe-early-user-website.md`
- [ ] `tasks/20260825-crystal-lattice-product-positioning-and-website/040-research-foundation.md`
- [ ] `tasks/20260825-crystal-lattice-product-positioning-and-website/050-built-in-feature-opportunity-mining.md`
- [ ] `tasks/20260825-crystal-lattice-product-positioning-and-website/060-search-demand-and-terminology.md`
- [ ] `tasks/20260825-crystal-lattice-product-positioning-and-website/070-community-problems-and-workarounds.md`
- [ ] `tasks/20260825-crystal-lattice-product-positioning-and-website/080-competitor-category-and-multi-agent-research.md`
- [ ] `tasks/20260825-crystal-lattice-product-positioning-and-website/090-first-evidence-informed-website-update.md`
- [ ] `tasks/20260825-crystal-lattice-product-positioning-and-website/100-early-user-observation-and-interviews.md`
- [ ] `tasks/20260825-crystal-lattice-product-positioning-and-website/110-remote-access-and-bridge-viability.md`
- [ ] `tasks/20260825-crystal-lattice-product-positioning-and-website/120-early-user-and-remote-access-informed-website-update.md`
- [ ] `tasks/20260825-crystal-lattice-product-positioning-and-website/130-positioning-and-product-architecture-synthesis.md`
- [ ] `tasks/20260825-crystal-lattice-product-positioning-and-website/140-proposition-feature-value-and-cta-experiments.md`
- [ ] `tasks/20260825-crystal-lattice-product-positioning-and-website/150-website-information-architecture-and-content-briefs.md`
- [ ] `tasks/20260825-crystal-lattice-product-positioning-and-website/160-visual-proof-and-reproducible-assets.md`
- [ ] `tasks/20260825-crystal-lattice-product-positioning-and-website/170-validated-website-release-and-product-integration.md`
- [ ] `tasks/20260825-crystal-lattice-product-positioning-and-website/180-production-measurement-and-iteration.md`
- [ ] `tasks/20260825-crystal-lattice-product-positioning-and-website/190-managed-remote-access-paid-launch-website.md`

## Execution plan

Status: Draft

Keep the current website useful throughout the program. Establish package-local
documentation and target ownership first, audit current product and
compatibility truth, then publish a release-safe early-user rewrite.

After the research foundation is approved, built-in feature mining, search,
community, and competitor research may proceed in parallel. Their accepted
findings feed the first evidence-informed rewrite. That deployed site then
supports early-user recruiting and remote-access research, followed by another
bounded rewrite.

Only after the source research and early-user evidence are available should
the work select a primary positioning architecture, run proposition and CTA
experiments, finalize page briefs, create production visual proof, and deliver
the larger validated release. Production measurement then drives bounded
iteration. The production paid managed remote-access offer receives a separate
website launch gate after public bridge clients, policy/security, measurement,
and owner-confirmed hosted-service readiness are complete.

Each substantive rewrite updates the content specification first when the
intended target changes, updates requirements, implements through the current
content system, verifies locally and visually, and deploys only with the
authority required for the remote mutation.

### Implementation decisions and open questions

- Decision: task plans remain Draft until the user approves execution of the
  relevant subtask.
- Decision: research findings do not modify public content automatically.
- Decision: no research task is required merely to satisfy a target record
  count; pilots expand only when decision value justifies it.
- Decision: the complete research program does not block a useful early-user
  site.
- Open questions are listed near the top of this task and are resolved by the
  appropriate research, synthesis, or experiment subtask.

### Documentation

- Package-local current documentation, research, and specifications live under
  `landing_page/docs/`.
- Retained normalized evidence lives under `landing_page/research/`.
- Current public copy remains under `landing_page/src/content/`.
- Release facts remain owned by their product/release packages and are
  consumed rather than independently redefined.

### Task checklist

- [x] Establish the package-local documentation, content specification,
      research, evidence, and ignored-output boundaries.
- [ ] Audit current product, compatibility, account, provider, and
      application-feature truth.
- [ ] Publish the release-safe early-user website.
- [ ] Complete source research and the first evidence-informed rewrite.
- [ ] Complete early-user and remote-access research and the second rewrite.
- [ ] Select and test the primary positioning and page architecture.
- [ ] Produce visual proof and the validated website release.
- [ ] Establish production measurement and iteration.
- [ ] Publish the managed remote-access paid offer only after its public and
      hosted-service release gates pass.
- [ ] Add the approved task sequence to the requested roadmap in a separate
      user-authorized step.

### Requirement verification

- Early usefulness: production and manual review show that each deployed
  rewrite offers an accurate first action.
- Progressive evidence: research findings, content decisions, specification
  changes, and website releases remain traceable without collapsing their
  roles.
- Compatibility transparency: current matrices and evidence distinguish
  configured agents, providers/accounts, application features, and gaps.
- Final content: comprehension and action-path experiments support the selected
  proposition and architecture.
- Release integration: production routes and downloads match current owning
  release sources.
- Paid offer: public price, trial, purchase, E2EE, privacy, support, and free
  connection choices match approved production behavior.
- Quality: accessibility, responsive, build, link, visual, privacy, and
  measurement checks pass at the relevant boundaries.
