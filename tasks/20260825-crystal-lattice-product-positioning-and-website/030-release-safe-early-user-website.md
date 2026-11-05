# Publish The First-User Website And Compatibility Catalogue

Publish the owner-approved first-user homepage together with a transparent
compatibility catalogue derived from the accepted product baseline. Keep the
homepage concise, give configured agents and materially different harnesses a
recognizable introduction, and put detailed agent, harness, provider, and
plugin status on a focused public route.

Parent Task:
`tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md`

Depends On:

- `tasks/20260825-crystal-lattice-product-positioning-and-website/020-current-product-and-compatibility-baseline.md`
- `tasks/20260825-crystal-lattice-product-positioning-and-website/025-integrate-current-visual-baseline-and-bootstrap-asset-pipeline.md`

Accepted Input Boundary:

- `tasks/20260930-homepage-getting-started-and-waitlist/019-publishable-homepage-ui-walkthrough.md`
  owns the homepage brief, copy, visual plan, proof selection, Getting Started,
  release cut, and final local homepage. Compatibility work may prepare its
  independent projection and route after this plan is approved, but final
  navigation, terminology, integrated acceptance, and publication consume the
  homepage accepted at task `019`'s final local checkpoint.

Coordinates With:

- `tasks/20260930-homepage-getting-started-and-waitlist/020-aws-email-waitlist.md`
  — owns the real waitlist, one integrated publishing push, and production
  form verification.

Previously Paused By:

- `tasks/20261024-production-staging-website-channels.md` — establishes the
  production/staging source and deployment channels before compatibility UI
  implementation resumes. The channels are now public and verified; resume at
  the Canonical Tables checkpoint.

## Requirements checklist

- [ ] The published homepage is the owner-approved result of task `019`; this
      task does not restore the former six-card or walkthrough structure.
- [ ] The homepage introduces the existence of included configured agents and
      materially different harnesses with concise recognizable examples, then
      routes detailed compatibility questions to a focused catalogue instead
      of rendering exhaustive tables in the first-user flow.
- [ ] Public wording uses **configured agent** for Crystal Lattice's named
      agent configurations and **harness** for materially different tool,
      provider, context, and control behavior. It does not rename agents as
      profiles.
- [ ] Public wording may describe configured agents as Codex-oriented,
      Claude-compatible, Gemini-oriented, or another evidence-backed family
      qualifier. Each qualifier matches its owning package evidence; no
      universal parity or compatibility claim is inferred from a family name.
- [ ] Every public configured-agent or harness explanation visibly states that
      these are Crystal Lattice implementations, not official upstream
      applications, accounts, or sessions.
- [ ] The public compatibility catalogue contains three concise canonical
      tables: harnesses, providers, and plugins/application features.
- [ ] Configured agents are introduced through homepage/harness examples and
      progressive detail rather than a fourth exhaustive public table.
- [ ] Configured agents, harnesses, providers, and plugins remain separate
      axes. The UI does not flatten them into one sparse cross-product or imply
      that a provider is a harness, a harness is an agent, or every plugin
      applies to every agent.
- [ ] The harness table contains only canonical differentiating capabilities,
      combining related tools into meaningful rows such as command execution,
      editing, media, web, MCP, skills, compaction, and subagents.
- [ ] The provider table collapses ordinary required coding-agent API behavior
      into a **Basic API support** result, separates subscription
      authentication, and lists only meaningful native extras such as native
      search/compaction, flex or priority processing, verbosity, file/image
      input, image generation, and provider routing.
- [ ] The plugin/application-feature table groups product behavior such as
      session organization, actions/history, provider controls, usage/cost,
      attachments/assets, context, MCP, export/sharing, and cloud workspaces;
      it does not publish the complete package inventory as the primary table.
- [ ] Public status presentation preserves material distinctions including
      available, conditional, optional, experimental/in development, planned,
      unavailable/unsupported, not applicable, unknown/not verified, default
      selected, and source-only or internal states where relevant.
- [ ] Canonical tables may use check, cross, and conditional symbols, but each
      cell includes accessible text and does not rely on color alone.
- [ ] Public rows retain enough source/version, limitation, prerequisite, and
      verification information to be trustworthy without exposing internal
      task paths, private diagnostics, or research workflow language.
- [ ] The public projection is generated or validated from the accepted
      compatibility research. It does not manually duplicate authoritative
      provider, agent, harness, or plugin facts in page copy.
- [ ] Before publication, deterministic extraction and focused verification
      identify source drift since the accepted baseline. Changed claims are
      refreshed through their owning evidence boundary; unchanged accepted
      evidence is not broadly re-audited.
- [ ] Unsupported and not-applicable states are not collapsed into generic
      negative checkmarks. Planned and in-development work remains visually
      distinct from delivered behavior.
- [ ] The compatibility catalogue is responsive, keyboard accessible,
      semantically structured, linkable to individual groups/entries, and
      usable without horizontal page overflow or color-only status meaning.
- [ ] The complete integrated website has current downloads, first-use,
      mobile/bridge, support, privacy, documentation, source, and waitlist
      paths derived from their owning release sources.
- [ ] Visible planning placeholders, knowingly unverified APIs, stale
      availability statements, internal task terminology, and unsupported
      official-product parity claims are absent.
- [ ] Local implementation, compatibility review, waitlist deployment,
      production publication, live verification, and repository visibility
      remain separate gates.

## Scope and ownership

This task owns:

- the public compatibility information architecture;
- compatibility terminology and table/list presentation;
- a focused website-facing canonical projection derived from the complete
  retained evidence;
- the focused compatibility route or approved route set;
- current status, limitation, freshness, and evidence presentation;
- integration of task `019`'s accepted homepage with the compatibility route;
- final integrated content acceptance and live website checks after the shared
  publishing push.

This task does not own:

- the homepage copy, visual plan, proof assets, Getting Started, or release cut
  owned by task `019`;
- the compatibility evidence baseline owned by task `020`;
- provider, plugin, configured-agent, mobile, Desktop, CLI, bridge, account,
  security, or release behavior;
- the waitlist backend/form/privacy implementation or publishing push owned by
  the waitlist task;
- repository visibility or anonymous-source validation.

## Accepted research inputs

The completed baseline already provides:

- accepted configured-agent records;
- provider/account routes;
- model-family tool and feature bundles;
- a 66-project plugin catalogue;
- lifecycle, capability, packaging, loading, default, frontend, automated-test,
  hosted-verification, limitation, confidence, and review states;
- stable claim evidence and deterministic validation;
- a draft website projection that downstream work may refine.

Authoritative retained sources:

- `landing_page/research/current-product-and-compatibility-baseline/configured-agent-compatibility.csv`
- `landing_page/research/current-product-and-compatibility-baseline/model-family-feature-matrix.json`
- `landing_page/research/current-product-and-compatibility-baseline/provider-support-matrix.json`
- `landing_page/research/current-product-and-compatibility-baseline/feature-catalog.json`
- `landing_page/research/current-product-and-compatibility-baseline/claim-evidence.jsonl`

The generated version-two projection is retained as complete internal evidence
and drift validation. It is not the approved public information design. This
task owns a later canonical public selection derived from that evidence; it
does not rewrite the accepted source merely to shorten website tables.

## Approved terminology and relationship direction

Homepage direction supplied by task `019`:

> Crystal Lattice includes configured agents with Codex-oriented,
> Claude-compatible, Gemini-oriented, and other harnesses. These are Crystal
> Lattice implementations, not the official upstream applications.

Relationship model:

```text
configured agent
  ├─ provider route and account/auth mode
  ├─ default model or model family
  ├─ harness/tool and provider plugin composition
  └─ selected supporting plugins
```

The catalogue uses this model to explain relationships without implying that
every combination is supported or that a family-oriented harness owns an
official upstream application's sessions.

## Approved public table direction

### 1. Harnesses

Primary question:

> What materially changes between the available harness families?

Canonical rows should combine implementation details. For example, the
Codex-oriented column needs one command row for `exec_command` +
`write_stdin`, not separate rows for each tool. Expected primary rows include:

- editing tools;
- command execution;
- image/media;
- web tools;
- MCP;
- skills;
- compaction;
- subagents.

Features that are uniformly unavailable and do not clarify a meaningful
comparison, such as the current structured planning and request-user-input
gaps, may appear as a concise note rather than separate rows.

### 2. Providers

Primary question:

> Which provider/account route supplies complete ordinary coding-agent API
> support, subscription authentication, and meaningful provider-native extras?

Primary columns:

- provider route;
- Basic API support;
- subscription authentication;
- native extras;
- important condition/limitation.

Basic API support canonicalizes expected behavior such as streaming, tool
calling, reasoning, usage/cost, caching, and normal retry handling. Native
extras contain only differentiating behavior.

### 3. Plugins and application features

Primary question:

> Which additional product behaviors exist, where do they apply, and what is
> their maturity?

Primary rows are product behavior groups, not package rows. Plugin package
names and the complete 69-project inventory remain in progressive developer
detail or internal evidence.

## Open questions

- Exact canonical rows and grouping inside the three approved tables.
- Exact family qualifiers:
  - Codex-oriented versus Codex-compatible;
  - Claude-compatible versus Claude-oriented;
  - Gemini-, Qwen-, Kimi-, Grok-, and other family labels according to package
    evidence.
- Which configured-agent examples and default models appear as progressive
  harness detail rather than on the primary table.
- Which plugin package names appear in expandable detail.
- Public status vocabulary and visual treatment for **in development** versus
  **planned**, where the retained evidence currently uses source presence,
  lifecycle status, capability status, and maintained future tasks.
- How much source path, plugin name, verification date, and evidence detail is
  visible initially versus progressively disclosed.
- Whether source/version freshness appears per row, per group, or in one
  catalogue-level verification note.

## Human decisions and actions required

- **HUMAN JUDGMENT — CANONICAL TABLES:** Approve the selected rows, grouping,
  symbols, wording, and omissions in the three public tables before UI
  implementation.
- **HUMAN JUDGMENT — LOCAL CATALOGUE:** Review the implemented responsive
  catalogue, terminology, limitations, evidence/freshness presentation, and
  homepage route in context.
- **HUMAN JUDGMENT — INTEGRATED SITE:** Approve the exact homepage,
  compatibility catalogue, waitlist/privacy presentation, downloads, and
  navigation before production publication.
- **HUMAN — MANDATORY:** AWS deployment, production publication, and
  repository visibility keep their separate confirmation gates.

## References

### Start here

1. `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md`
   — parent requirements, evidence roles, release sequencing, and public
   boundaries.
2. `tasks/20260825-crystal-lattice-product-positioning-and-website/020-current-product-and-compatibility-baseline.md`
   — completed compatibility evidence, accepted decisions, source revision,
   generators, limitations, and downstream refinement boundary.
3. `tasks/20260930-homepage-getting-started-and-waitlist/019-publishable-homepage-ui-walkthrough.md`
   and
   `landing_page/docs/development/homepage-first-user-release/brief.md`
   — homepage ownership and approved configured-agent/harness terminology.
4. `landing_page/docs/development/research/findings/current-product-and-compatibility-baseline.md`
   — human-readable accepted findings and website projection boundary.
5. `landing_page/research/current-product-and-compatibility-baseline/website-compatibility-data.json`
   and its generator/selection files — accepted draft evidence feeding the
   internal version-two projection and later canonical public selection.
6. `landing_page/docs/development/specifications/product-website-content/content-spec.md`
   and `requirements.md` — intended public communication outcomes and live
   target state.
7. `landing_page/docs/development/content-system.md`,
   `landing_page/AGENTS.md`, and `landing_page/README.md` — current authored
   content, rendering, claim, build, and verification boundaries.

## Expected outputs

Durable content decision:

- `landing_page/docs/development/research/findings/release-safe-early-user-content-decision.md`

Website-facing compatibility source:

- a maintained canonical three-table projection generated from the accepted
  research and focused current-source refresh;
- implementation source under the landing package's content/data ownership,
  with no manual duplication of authoritative rows;
- validation that every public row resolves to accepted evidence or a
  separately refreshed current claim.

Current public implementation:

- focused compatibility route or approved route set;
- navigation and homepage route to the catalogue;
- semantic status legend, grouped rows/cards/tables, limitations, evidence and
  freshness presentation;
- task `019`'s accepted homepage and first-use path;
- affected mobile, support, privacy, terms, footer, or documentation routes
  only when current evidence requires them.

Target/state:

- approved updates to the product-content specification;
- implementation, verification, documentation, and evidence state updates in
  requirements.

Verification:

- focused canonical selection/generator validation;
- content and route tests;
- responsive and keyboard browser tests;
- semantic/accessibility review;
- source/version/limitation checks;
- full landing build and integrated-site review;
- production checks only after the shared authorized publication.

## Scope boundaries

- Do not repeat broad compatibility research or reclassify unchanged accepted
  rows merely to produce different public wording.
- Do not write public compatibility facts directly from task prose when an
  accepted data/evidence source exists.
- Do not place exhaustive compatibility tables in the homepage first-user
  path.
- Do not present official upstream applications, accounts, or sessions as
  included Crystal Lattice products.
- Do not infer complete parity from tool/package names.
- Do not expose internal task paths, research confidence labels, private
  diagnostics, credentials, account identifiers, or raw provider responses.
- Do not expose development fixtures, templates, or support libraries as
  ordinary user-facing product capabilities without explicit grouping.
- Do not publish planned or in-development behavior with the same presentation
  as delivered behavior.
- Do not update the roadmap or deploy remotely without separate authority.

## Execution plan

Status: Approved

Keep the accepted compatibility research and generated version-two projection
as complete internal evidence. Do not expose that full projection directly.

Execution is paused behind
`tasks/20261024-production-staging-website-channels.md`.

After resumption, create a canonical public selection:

1. derive one small harness table from differentiating capabilities only;
2. combine related tool implementations into one understandable row;
3. derive one provider table with Basic API support, subscription auth,
   native extras, and concise conditions;
4. derive one plugin/application-feature table from product behavior groups
   rather than package rows;
5. map current, conditional, planned, and unavailable states to accessible
   check/cross/conditional presentation;
6. retain exact package, provider, model, evidence, limitation, and freshness
   detail outside the primary scan path;
7. validate every public cell against accepted or explicitly refreshed
   evidence.

Stop for the Canonical Tables checkpoint before route/component
implementation.

After canonical-table approval, implement the focused compatibility route
using semantic tables and progressive details. Do not add search, comparison
scoring, or a dense client-side data application merely because the internal
source is large.

Integrate the accepted task `019` homepage through a concise configured-agent
introduction and one compatibility action. Verify both independently, then
review them together with current downloads, documentation, mobile/bridge,
support, privacy, and waitlist presentation.

The waitlist task performs the single authorized production publishing push
after its own AWS/privacy gates and this task's integrated-site acceptance.
After publication, verify public homepage, compatibility routes, status
semantics, evidence/freshness notes, links, downloads, and waitlist behavior.
Repository visibility follows its separate release task.

### Implementation decisions and open questions

- Decision: revise this task in place; the completed compatibility research
  remains the evidence owner.
- Decision: task `019` owns the homepage and supplies an accepted input rather
  than becoming a circular whole-task dependency.
- Decision: the homepage introduces configured agents/harnesses but does not
  render the exhaustive catalogue.
- Decision: public compatibility uses three concise tables: harnesses,
  providers, and plugins/application features.
- Decision: configured-agent examples belong in homepage/harness context and
  progressive details rather than an exhaustive fourth table.
- Decision: configured agents are not renamed profiles.
- Decision: a harness is broader than model choice, instructions, or a shared
  tool permission list.
- Decision: per-family **oriented** or **compatible** wording follows package
  evidence rather than one universal adjective.
- Decision: the accepted research package and version-two projection remain
  complete internal evidence; this task owns a smaller canonical public
  selection.
- Decision: final homepage, compatibility catalogue, waitlist, and publication
  use one integrated artifact and shared publication checkpoint.
- Decision: compatibility UI work is paused behind the production/staging
  channel task.
- Open human questions are listed above and must be resolved before canonical
  table or UI work.

### Documentation

- Record approved compatibility information architecture and public
  terminology in the durable release-safe content decision.
- Update the product-content specification and requirements after the content
  model is approved.
- Update `content-system.md` only for delivered projection/rendering behavior.
- Document the projection generator/source boundary and freshness workflow
  without duplicating the accepted research catalogue.
- Keep provider, harness, agent, and plugin package documentation
  authoritative for behavior.

### Task checklist

- [x] Reconcile this task with the revised task `019` homepage ownership and
      completed compatibility research.
- [x] Draft and review the complete internal
      configured-agent/harness/provider/plugin evidence model.
- [x] Obtain Content Model human approval.
- [x] Define and generate the version-two website projection.
- [x] Run current-source drift detection and refresh changed claims only.
- [x] Obtain focused source-refresh human approval.
- [ ] Define the selected canonical harness/provider/plugin tables.
- [ ] Obtain Canonical Tables human approval.
- [ ] Implement the approved compatibility route or route set.
- [ ] Add the concise homepage compatibility introduction/action after task
      `019` supplies its accepted local homepage.
- [ ] Verify public status, limitation, evidence, and freshness presentation.
- [ ] Run content, build, responsive, keyboard, semantic, accessibility, and
      link checks.
- [ ] Obtain Local Catalogue human approval.
- [ ] Review the complete integrated homepage, catalogue, waitlist/privacy,
      navigation, downloads, docs, support, and mobile/bridge paths.
- [ ] Obtain Integrated Site human approval.
- [ ] Coordinate the authorized publishing push through the waitlist task.
- [ ] Verify public homepage/catalogue/routes and record acceptance before
      repository visibility work.

### Requirement verification

- Homepage ownership: task and source inspection show that task `019` owns
  homepage copy/visuals while this task owns the compatibility catalogue and
  integrated content acceptance.
- Three-table separation: generated public data and rendered HTML expose
  harnesses, providers, and plugins/features as separate concise tables while
  complete configured-agent relationships remain available in internal
  evidence and progressive detail.
- Configured-agent identity: every public agent maps to accepted source
  identity, harness/tool bundle and provider route, retains its limitation and
  qualifier, and states that it is not an official upstream application or
  session.
- Harness accuracy: harness rows identify material tool/provider/context
  behavior backed by package descriptors/evidence and do not treat model,
  prompt, or permission-only differences as separate harness proof.
- Provider accuracy: public provider rows preserve auth/account distinctions,
  current/conditional/planned states, prerequisites, limitations, and
  verification freshness from accepted or refreshed evidence.
- Plugin accuracy: public plugin rows resolve to the accepted catalogue,
  preserve lifecycle/capability/default distinctions, and separate ordinary
  user-facing product behavior from examples, templates, support libraries,
  distribution-specific packages, and fixtures.
- Projection lineage: deterministic validation traces every public cell to
  accepted evidence or a focused refreshed claim and reports source drift
  rather than silently changing classifications.
- Accessibility/responsiveness: browser and semantic checks cover linkable
  headings, keyboard navigation, table/list reading, details disclosure,
  status text independent of color, and no horizontal page overflow at
  desktop, tablet, 390-pixel, and 320-pixel widths.
- Integrated-site boundary: human review accepts the exact homepage,
  compatibility catalogue, waitlist/privacy presentation, navigation,
  downloads, docs, support, and mobile/bridge content before publication.
- Publication boundary: live verification follows explicit authorization and
  checks public routes/data/statuses against the accepted artifact.

### Additional implementation verification

- Run the accepted compatibility generators/checks before and after the new
  projection work.
- Validate JSON/CSV parsing, stable IDs, evidence references, source paths,
  status mappings, route anchors, and generated public data.
- Check that internal task paths, private identifiers, credentials, research
  confidence fields, and raw diagnostics are absent from browser output.
- Use a small current-source comparison to identify changed configured agents,
  plugin descriptors, provider routes, and maintained planned states.
- Treat hosted-provider verification as not run unless explicitly authorized
  and performed; do not upgrade a status from local tests alone.

## Implementation Notes

- 2026-10-24: The user approved the revised execution plan and ordered work to
  proceed through the version-two compatibility projection before task `019`
  resumes. Content Model approval selects one `/compatibility` route with four
  linkable views, harness-family-first configured-agent grouping, exact models
  in progressive technical detail, a user-facing plugin catalogue separated
  from developer/internal projects, explicit public status distinctions, and
  progressive evidence/freshness disclosure. Execution starts with projection
  generation and current-source drift detection and must stop at the Projection
  human checkpoint before route/component implementation.
- 2026-10-24: Generated the task-owned retained projection under
  `landing_page/research/release-safe-early-user-website/` without rewriting
  the completed baseline. The projection has 20 configured agents grouped
  into eight relationship groups, six harness families with 71 capability
  rows, 10 provider/account routes with 191 capability rows, and all 69
  current plugin projects grouped as 33 included, 9 optional, 3
  distribution-specific, and 24 developer/internal projects. Exact model and
  plugin-package defaults are progressive technical details rather than
  primary agent columns.
- 2026-10-24: Focused drift detection found no accepted configured-agent
  provider/model/plugin/shell-mode identity changes, but current display
  metadata exists for all 20 agents. Refreshed the projection for Anthropic
  native compaction/context editing, Codex unified exec, the Claude background
  compaction application plugin, and three additional plugin projects:
  `embedded-workspace-settings`, `interleaved-thinking`, and
  `shell-tool-settings`.
- 2026-10-24: Focused local verification passed 185 tests: Anthropic context
  management 20, Claude compaction 43, Codex unified exec/shell selection 98,
  embedded workspace settings 2, interleaved thinking 9, and shell-tool
  settings 13. The first combined new-plugin command failed during collection
  because `embedded-workspace-settings` was not installed in the shared
  environment; package-source `PYTHONPATH` reruns passed and are the counted
  evidence. No hosted provider request was run.
- 2026-10-24: The deterministic generator and JSON parsing checks pass.
  Validation covers complete current plugin inventory, stable configured-agent
  grouping, progressive model detail, known public statuses, planned
  capability treatment, Anthropic refreshed rows, input hashes, and absence of
  internal task paths, requirement IDs, obsolete **profile** terminology, and
  **AI Agent Platform** from the proposed public projection. Route/component
  implementation remains unstarted; the complete projection is now retained
  as internal evidence pending canonical public table selection.
- 2026-10-24: The user accepted the focused source refreshes but rejected the
  complete version-two projection as direct website content. Retain it as
  internal evidence. The approved future public shape is three small
  canonical tables—Harnesses, Providers, and Plugins/application features—
  with selected meaningful rows, baseline provider behavior collapsed into a
  Basic API result, related tool implementations combined, and accessible
  check/cross/conditional states. Configured agents remain homepage/harness
  examples and progressive detail, not a fourth exhaustive table.
- 2026-10-24: Compatibility canonicalization and route implementation are
  paused behind `tasks/20261024-production-staging-website-channels.md`.
  Resume at the Canonical Tables checkpoint after the production/staging
  channels pass their recorded resumption boundary.
- 2026-11-04: The production/staging blocker is cleared. The full projection
  remains internal evidence, and public implementation may now resume at the
  Canonical Tables checkpoint for the three approved focused tables. This task
  has not otherwise resumed during channel deployment.
