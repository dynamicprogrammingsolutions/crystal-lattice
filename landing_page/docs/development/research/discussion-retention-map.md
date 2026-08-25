# Initial Planning Discussion Retention Map

Status: Retention audit, August 25, 2026.

This page maps the important ideas from the initial product-website planning
discussion to their durable repository owners. It identifies ideas that are
only partially retained and ideas intentionally not retained.

The discussion transcript is not a source of current product truth. Product
facts remain owned by implementation packages and accepted verification.

## Status Key

- **Retained:** the durable idea, decision, or question has a clear repository
  owner.
- **Partially retained:** the durable principle or research question is stored,
  but a volatile fact, exact implementation, final choice, or complete dataset
  remains future work.
- **Not retained:** the item is intentionally absent as a durable claim or
  target. The reason and revisit owner are explicit.

## Task Reference Key

- [Main task](../../../../tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md)
- [Task 010 — documentation and content-specification foundation](../../../../tasks/20260825-crystal-lattice-product-positioning-and-website/010-website-documentation-and-content-specification-foundation.md)
- [Task 020 — current product and compatibility baseline](../../../../tasks/20260825-crystal-lattice-product-positioning-and-website/020-current-product-and-compatibility-baseline.md)
- [Task 025 — current visual baseline and asset-pipeline foundation](../../../../tasks/20260825-crystal-lattice-product-positioning-and-website/025-integrate-current-visual-baseline-and-bootstrap-asset-pipeline.md)
- [Task 030 — release-safe early-user website](../../../../tasks/20260825-crystal-lattice-product-positioning-and-website/030-release-safe-early-user-website.md)
- [Task 040 — research foundation](../../../../tasks/20260825-crystal-lattice-product-positioning-and-website/040-research-foundation.md)
- [Task 050 — built-in feature opportunity mining](../../../../tasks/20260825-crystal-lattice-product-positioning-and-website/050-built-in-feature-opportunity-mining.md)
- [Task 060 — search demand and terminology](../../../../tasks/20260825-crystal-lattice-product-positioning-and-website/060-search-demand-and-terminology.md)
- [Task 070 — community problems and workarounds](../../../../tasks/20260825-crystal-lattice-product-positioning-and-website/070-community-problems-and-workarounds.md)
- [Task 080 — competitor, category, and multi-agent research](../../../../tasks/20260825-crystal-lattice-product-positioning-and-website/080-competitor-category-and-multi-agent-research.md)
- [Task 090 — first evidence-informed website update](../../../../tasks/20260825-crystal-lattice-product-positioning-and-website/090-first-evidence-informed-website-update.md)
- [Task 100 — early-user observation and interviews](../../../../tasks/20260825-crystal-lattice-product-positioning-and-website/100-early-user-observation-and-interviews.md)
- [Task 110 — remote access and bridge viability](../../../../tasks/20260825-crystal-lattice-product-positioning-and-website/110-remote-access-and-bridge-viability.md)
- [Task 120 — early-user and remote-access website update](../../../../tasks/20260825-crystal-lattice-product-positioning-and-website/120-early-user-and-remote-access-informed-website-update.md)
- [Task 130 — positioning and product-architecture synthesis](../../../../tasks/20260825-crystal-lattice-product-positioning-and-website/130-positioning-and-product-architecture-synthesis.md)
- [Task 140 — proposition, feature-value, and CTA experiments](../../../../tasks/20260825-crystal-lattice-product-positioning-and-website/140-proposition-feature-value-and-cta-experiments.md)
- [Task 150 — website information architecture and content briefs](../../../../tasks/20260825-crystal-lattice-product-positioning-and-website/150-website-information-architecture-and-content-briefs.md)
- [Task 160 — visual proof and reproducible assets](../../../../tasks/20260825-crystal-lattice-product-positioning-and-website/160-visual-proof-and-reproducible-assets.md)
- [Task 170 — validated website release](../../../../tasks/20260825-crystal-lattice-product-positioning-and-website/170-validated-website-release-and-product-integration.md)
- [Task 180 — production measurement and iteration](../../../../tasks/20260825-crystal-lattice-product-positioning-and-website/180-production-measurement-and-iteration.md)
- [Task 190 — managed remote-access paid launch website](../../../../tasks/20260825-crystal-lattice-product-positioning-and-website/190-managed-remote-access-paid-launch-website.md)

## Product Category, Audience, and Value

| Discussion point | Status | Durable owner | Notes |
|---|---|---|---|
| Treat the work as a new evidence-informed website program rather than reopening the old landing-page task as the canonical plan. | Retained | `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md`; [evidence index](evidence-index.md) | The old task and brainstorm remain historical inputs. |
| Present the runtime as a process running on the user's ordinary computer, not as infrastructure the user operates. | Retained | [positioning baseline](positioning-and-product-baseline.md); [content specification](../specifications/product-website-content/content-spec.md) | This is an approved terminology correction. |
| Treat Crystal Lattice as coding-agent-first while researching whether general-purpose agent use should become prominent. | Retained | [positioning baseline](positioning-and-product-baseline.md); [content specification](../specifications/product-website-content/content-spec.md); task 130 | The broader category remains a hypothesis. |
| Research one workspace across Codex-, Claude Code-, Gemini-, Qwen-, Kimi-, Grok-, and related configured-agent styles. | Retained | [positioning baseline](positioning-and-product-baseline.md); tasks 020, 080, 130, and 140 | Public wording must remain compatibility-accurate. |
| Treat ordinary and power users as a progression supported by progressive disclosure. | Retained | [positioning baseline](positioning-and-product-baseline.md); [content specification](../specifications/product-website-content/content-spec.md); tasks 100 and 140 | Outcome-focused, curious, controlling, plugin, and builder behavior is preserved. |
| Investigate transparency as source, configuration, prompt/tool, execution, usage, cost, and compatibility visibility. | Retained | [positioning baseline](positioning-and-product-baseline.md); [content specification](../specifications/product-website-content/content-spec.md); tasks 050, 130, and 140 | Uniform provider metadata is explicitly not assumed. |
| Investigate natural-language customization as “ask the agent to change the agent.” | Retained | [positioning baseline](positioning-and-product-baseline.md); [content specification](../specifications/product-website-content/content-spec.md); tasks 050 and 140 | Source visibility, validation, reload, failure reporting, and rollback are retained as required safety hypotheses before promotion. |
| Route users, compatibility evaluators, customizers, builders, mobile users, and contributors to different next actions. | Retained | [content specification](../specifications/product-website-content/content-spec.md); task 150 | The exact hierarchy remains research-dependent. |

## Product Facts, Compatibility, and Feature Opportunities

| Discussion point | Status | Durable owner | Notes |
|---|---|---|---|
| A Crystal Lattice compatibility profile is not the official upstream application and does not automatically continue its sessions. | Retained | [positioning baseline](positioning-and-product-baseline.md); [content specification](../specifications/product-website-content/content-spec.md); task 020 | Existing-session import/interoperability is an explicit research question. |
| Separate configured-agent compatibility, provider/account support, and application-wide features. | Retained | [content specification](../specifications/product-website-content/content-spec.md); content requirements; task 020 | Status must distinguish default, optional, partial, experimental, planned, unavailable, and unknown. |
| Make compatibility gaps and last verification visible and use them as contributor paths. | Retained | [content specification](../specifications/product-website-content/content-spec.md); tasks 020 and 150 | The actual matrix remains an expected task-020 output. |
| Research small built-in features such as archive, search, filters, status, pinning, titles, summaries, attachments, exports, notifications, configuration reload, MCP, usage, cost, and timing. | Retained | [positioning baseline](positioning-and-product-baseline.md); [evidence index](evidence-index.md); task 050 | Adaptive handoffs are created only after the inventory shows coherent clusters. |
| Look for scripts, proxies, viewers, dashboards, paid products, and complicated workarounds that reveal feature gaps. | Retained | [research method](research-method.md); tasks 050, 070, and 080 | Workarounds and direct competitors remain separate classifications. |
| Do not assume that a unified competitor uses one standard prompt/tool surface for every model. | Retained | task 080 | Direct verification is required. |
| Preserve open source as both source transparency and an optional user-operated path. | Retained | [content specification](../specifications/product-website-content/content-spec.md); tasks 110 and 150 | Open source alone is not assumed to be the primary proposition. |

## Mobile, Bridge, and Commercial Service

| Discussion point | Status | Durable owner | Notes |
|---|---|---|---|
| Direct local-network mobile connection and bridge-based remote connection are different paths. | Retained | [positioning baseline](positioning-and-product-baseline.md); [content specification](../specifications/product-website-content/content-spec.md); task 110 | The normal public explanation is explicit. |
| The bridge is Crystal Lattice-specific remote connectivity, not the runtime itself. | Retained | [positioning baseline](positioning-and-product-baseline.md); task 110 | The runtime is not marketed as self-hosted infrastructure. |
| First-party mobile access makes phone control important but insufficient as a standalone differentiator. | Retained | [positioning baseline](positioning-and-product-baseline.md); tasks 080 and 110 | Current competitor details must be refreshed. |
| A future paid service should preserve local and user-operated bridge paths and sell managed convenience/integration. | Retained | [content specification](../specifications/product-website-content/content-spec.md); tasks 110 and 190 | Identity, E2EE, notification, entitlement, purchase, quota, and reliability claims remain owned by their product tasks. |
| Generic networking tools should not be presented as direct coding-agent competitors. | Retained | task 110 | They may be studied only as workaround substitutes affecting willingness to pay. |

## Website Content and Progressive Delivery

| Discussion point | Status | Durable owner | Notes |
|---|---|---|---|
| The current site leads with mechanisms and jargon, mixes several audiences, and contains placeholders or unverified examples. | Retained | [positioning baseline](positioning-and-product-baseline.md); task 030 | Exact deployed strings are re-audited rather than copied into durable findings. |
| “Claim → proof → try it” is useful, but the homepage should not become full executable documentation. | Retained | [content specification](../specifications/product-website-content/content-spec.md); task 150 | Detailed workflows belong on focused pages or docs. |
| Publish a useful release-safe website before completing research. | Retained | [content specification](../specifications/product-website-content/content-spec.md); tasks 030, 090, 120, and 170 | Every deployed version must be independently useful and truthful. |
| Community and competitor research should precede the first evidence-informed rewrite. | Retained | main task; tasks 070, 080, and 090 | Early-user recruiting still does not block that rewrite. |
| Update the content specification before implementation when a content decision changes the target. | Retained | main task; content specification; every rewrite task | Research does not update public copy automatically. |
| Keep the content system separate from the copywriting-focused content specification. | Retained | [content-system documentation](../content-system.md); content specification; task 010 | A content-system specification is deferred until actual complexity justifies it. |
| Keep website knowledge and research under `landing_page/`, tasks under root `tasks/`, and disposable output under ignored package artifacts. | Retained | `landing_page/AGENTS.md`; research index; main task | Audience and source-of-truth boundaries are explicit. |
| Maintain a claim/evidence matrix and keep unverified code or visual proof out of production. | Retained | [content specification](../specifications/product-website-content/content-spec.md); content requirements; tasks 150, 160, and 170 | Product packages remain authoritative for the behavior being summarized. |
| Let search and user language inform SEO and content terminology instead of selecting keywords from internal vocabulary. | Retained | [research method](research-method.md); tasks 060 and 150 | Final SEO intent awaits retained search evidence. |
| Keep measurement privacy-compatible and update public privacy statements with the implementation. | Retained | content requirements; task 180 | The current no-third-party-analytics statement remains authoritative until changed with code/configuration. |
| Integrate mobile, desktop, CLI, source, documentation, and hosted-service availability from their owning release sources. | Retained | main task; tasks 030 and 170 | Distribution facts are consumed rather than duplicated as independent website truth. |

## Visual Communication and Assets

| Discussion point | Status | Durable owner | Notes |
|---|---|---|---|
| Use a real cross-interface outcome sequence instead of unrelated device screenshots. | Retained | [visual communication and reproducible assets](visual-communication-and-reproducible-assets.md); task 160 | Final storyboard remains content-brief-dependent. |
| Explain one workspace across configured agents. | Retained | [visual communication and reproducible assets](visual-communication-and-reproducible-assets.md); task 160 | Must not imply official upstream session ownership. |
| Show how one plugin can change agent behavior and contribute settings, actions, notifications, or UI. | Retained | [visual communication and reproducible assets](visual-communication-and-reproducible-assets.md); task 160 | This is a visual hypothesis, not a guaranteed homepage section. |
| Explain local process, clients, and optional bridge connectivity separately. | Retained | [visual communication and reproducible assets](visual-communication-and-reproducible-assets.md); task 160 | Security labels remain current-product-dependent. |
| Use a configured-agent composition visual rather than relying only on a model-name table. | Retained | [visual communication and reproducible assets](visual-communication-and-reproducible-assets.md); task 160 | It may show model/provider, instructions, tools, native behavior, and application UI. |
| Demonstrate session organization and transparency through real workbench states. | Retained | [visual communication and reproducible assets](visual-communication-and-reproducible-assets.md); task 160 | Feature selection follows research and page briefs. |
| Reproducible asset pipeline. | Retained | [Reproducible Asset Pipeline](visual-communication-and-reproducible-assets.md#reproducible-asset-pipeline); tasks 025 and 160 | Task 025 establishes the early browser-side foundation; task 160 extends it for the final approved visual set. |

## Research Method and Task Handoffs

| Discussion point | Status | Durable owner | Notes |
|---|---|---|---|
| Keep product facts, search, community, competitor, issue, interview, and experiment evidence separate. | Retained | [research method](research-method.md); main task | No source answers every decision. |
| Use bounded pilots, manual stratified review, expansion approval, stopped branches, and contradiction preservation. | Retained | [research method](research-method.md); task 040 | Fixed record counts are intentionally avoided. |
| Create adaptive feature-research handoffs only after coherent clusters appear. | Retained | [research method](research-method.md); task 050 | Task creation and execution require approval. |
| Make each task a cold handoff whose background survives replacement of its execution plan. | Retained | main task and every subtask | Ordered bounded references, known facts, expected outputs, and scope boundaries precede every execution plan. |
| Insert progressive rewrite tasks between research groups. | Retained | main task and task hierarchy | Research and website delivery are intentionally interleaved. |

## Partially Retained

| Discussion point | Status | Retained portion | Missing portion and reason |
|---|---|---|---|
| Current competitor and market observations. | Partially retained | Initial source routes in [evidence index](evidence-index.md); category questions in tasks 080 and 110. | Exact claims and comparisons were not promoted into durable findings because they are time-sensitive and were not collected through the approved normalized research method. |
| Current built-in capability inventory. | Partially retained | Initial package routes and examples in [evidence index](evidence-index.md); dimensions in task 020. | Complete rows, support status, last verification, and evidence await task 020. |
| Feature-to-user-pain and workaround conclusions. | Partially retained | Hypothesis and method in [positioning baseline](positioning-and-product-baseline.md), [research method](research-method.md), and task 050. | Actual findings await retained task-050 evidence. |
| Specific page map and route names. | Partially retained | Audience paths and content responsibilities are in the content specification and task 150. | Final routes are intentionally deferred until synthesis and experiments. |
| Product naming architecture. | Partially retained | Product/service relationship and naming decisions are assigned to tasks 110 and 130. | Final labels for the platform, Control clients, and managed service are not approved. |
| Early-user sample and interview design. | Partially retained | Participant patterns, evidence distinctions, privacy, and outputs are in task 100. | Recruitment channels, sample size, compensation, and recording remain approval-dependent. |
| Website measurement. | Partially retained | Measurement requirement, evidence boundaries, candidate approaches, and privacy dependency are in task 180. | No tool, event set, consent model, or retention period is approved. |
| Roadmap integration. | Retained | The release roadmap contains the staged website/research sequence and paid-launch gate. | Roadmap maturity differs for internal testing, external review, broad mobile release, all-platform release, and paid managed remote access. |
| Internationalization and localized acquisition. | Partially retained | Task 060 permits market/language expansion based on pilot yield and release relevance. | No locale set or localization requirement is approved because demand and release priorities are unknown. |
| Social proof, testimonials, and community acquisition. | Partially retained | Proof and early-user research are retained in tasks 100, 150, and 160. | No testimonial, public user quote, community channel, or consented proof has been collected. |

## Explicitly Not Retained

| Discussion point | Status | Reason dropped or deferred | Revisit owner |
|---|---|---|---|
| Exact proposed hero sentences, slogans, and creative copy variants from the discussion. | Not retained | They are unvalidated creative hypotheses and would become accidental canonical copy if stored in the target specification. The underlying proposition concepts are retained. | Tasks 130, 140, and 150 |
| A fixed final homepage/page architecture proposed before research. | Not retained | Final information architecture must follow accepted positioning and experiments. | Task 150 |
| Exact candidate managed-service name such as “Crystal Lattice Connect.” | Not retained | Naming is unvalidated and could create an unintended product commitment. | Tasks 110 and 130 |
| Fixed research sample sizes, source counts, or paid-source budgets suggested during discussion. | Not retained | Task 040 intentionally uses pilot yield and decision value to set expansion and budget. | Task 040 |
| Generic VPN or tunnel products as direct bridge competitors. | Not retained as a direct-competitor claim | The user corrected this framing. They remain possible workaround substitutes only. | Task 110 |
| “Users can access their existing official Claude Code or Codex sessions through Crystal Lattice.” | Not retained | This would be inaccurate without explicit import or interoperability. Crystal Lattice currently owns its compatibility-profile sessions. | Tasks 020 and 080; future product task if validated |
| “OpenCode uses one standard tool surface for all models.” | Not retained as fact | The statement was not directly verified and task 080 explicitly requires verification. | Task 080 |
| Runtime described as self-hosted agent infrastructure. | Not retained | The user corrected the product model: Crystal Lattice is an ordinary process on the computer. Only the bridge may be user-operated/self-hosted. | Content specification and task 110 |
| Complete raw web pages, discussion threads, API responses, browser state, and full interview transcripts. | Not retained in Git | Copyright, privacy, security, context-size, and source-of-truth boundaries require minimized normalized evidence and ignored/private raw storage. | Research method and each research task |
| Full content-system specification and mandatory technical-spec page. | Not retained | Current YAML/Markdown/Astro behavior is simple enough for one development page. A specification is created only if delivered complexity justifies it. | Future separately approved content-system work |
| Landing package registration in the generated documentation-site catalog. | Not retained | Publication of website development/research pages needs a separate audience and navigation decision. Package README routing is currently sufficient. | Future documentation/publication task |
| Final hosted-bridge pricing, tiers, free allowance, or payment claims. | Not retained until approved current behavior exists | No approved willingness-to-pay evidence or production commercial service exists yet. Task 190 publishes only the later approved current values. | Tasks 110 and 190 plus owning bridge-commercial work |
| Final visual storyboard or production screenshots. | Not retained as current output | Visual concepts and the reproducible pipeline are retained, but approved briefs and current product states must precede production assets. | Tasks 150 and 160 |
| Current volatile competitor details as permanent facts. | Not retained | They can change quickly and must be refreshed with dates and direct sources during task 080. | Task 080 |

## Review Rule

When a future task materially changes or rejects an item above:

1. update the owning durable finding, specification, or current documentation;
2. update this map only when the retention status or owner changes;
3. preserve rejected or contradictory research in the owning finding rather
   than erasing it;
4. do not copy task progress into public website content.
