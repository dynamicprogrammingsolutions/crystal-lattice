# Positioning and Product Baseline

Status: Initial supporting baseline, August 25, 2026.

This page records durable knowledge needed to continue product-website
research without reconstructing earlier conversations. It is supporting
research, not current public copy or a normative content target.

## Verified Product Facts

- **Fact:** Crystal Lattice runs as an ordinary process on the user's computer
  in the working directory where the agent should operate.
- **Fact:** The product includes terminal/HTTP, mobile, and macOS desktop
  clients or surfaces at different release-readiness levels.
- **Fact:** A mobile client can connect directly on the same local network.
- **Fact:** The bridge relays Crystal Lattice application traffic when the
  mobile client and computer are not on the same local network.
- **Fact:** The bridge can be operated by the user. A public production hosted
  bridge is not currently delivered.
- **Fact:** The default configuration is coding-agent-oriented.
- **Fact:** Current configured agents include Codex-, Claude-, Gemini-, Qwen-,
  Kimi-, Grok-, and related model-family profiles through different provider
  and plugin combinations.
- **Fact:** A compatibility-oriented configured agent is not the official
  upstream coding-agent application and does not automatically share its
  sessions or account support.
- **Fact:** Application plugins currently contribute session organization,
  filters, actions, UI fields, notifications, settings, and other application
  behavior.
- **Fact:** Provider and extension plugins may surface reasoning, usage, token,
  cache, duration, cost, attachment, and provider-specific information.
- **Fact:** The repository and many components are open source, with
  component-specific license boundaries documented separately.

## Current Website Observations

- **Observation:** The current homepage leads with model-native harness
  terminology before establishing a simple product category and ordinary user
  outcome.
- **Observation:** The current page mixes first use, bridge deployment,
  provider/model compatibility, plugin authoring, session features, and SDK
  automation in one long path.
- **Observation:** Planning placeholders and explicitly unverified code are
  represented by public content sources and should not remain in a
  release-facing website.
- **Observation:** The existing mobile page explains local and bridge
  connection more plainly than the homepage but reflects pre-store-release
  availability.
- **Observation:** The previous landing-page task explicitly treated its
  result as an intermediate content direction.

## Terminology Corrections

- **Decision:** Ordinary product copy should say that Crystal Lattice runs on
  the user's computer, not on the user's infrastructure.
- **Decision:** The runtime process is not described as self-hosted in primary
  consumer language. The bridge may accurately be called user-operated or
  self-hosted.
- **Decision:** The bridge is Crystal Lattice-specific remote connectivity,
  not a generic infrastructure product.
- **Decision:** Technical terms such as server, HTTP API, provider-native, and
  application plugin are introduced only after their user-relevant meaning is
  clear.
- **Decision:** Public content must distinguish Crystal Lattice configured
  agents from official Codex, Claude Code, Gemini, Qwen, Kimi, Grok, and other
  products.

## Current Positioning Baseline

- **Recommendation:** Present Crystal Lattice primarily as a coding-agent
  product until research and delivered defaults support a broader category.
- **Hypothesis:** A strong ordinary-user proposition may be one coding-agent
  workspace across several model-family styles, providers, and plugin-provided
  features.
- **Hypothesis:** Multi-agent convenience may reduce duplicated setup for
  sessions, mobile connectivity, MCP, prompts, tools, credentials, and
  organization.
- **Hypothesis:** Transparency may be valuable as a leading or supporting
  proposition: users can understand which agent, provider, settings, tools,
  usage, and costs affect behavior.
- **Hypothesis:** Transparency may be latent rather than directly searched.
  Demonstrations may reveal value that users did not request beforehand.
- **Hypothesis:** Natural-language creation of a user-owned plugin could let an
  ordinary user ask Crystal Lattice to add or change a product capability.
- **Hypothesis:** The strongest natural-language customization outcome is not
  code generation alone, but source-visible change, validation, reload,
  failure reporting, and rollback inside the product.
- **Hypothesis:** Coding-agent-first positioning may support a broader future
  statement that prompts, tools, workflows, and UI can be replaced for
  non-coding work.

## Ordinary-to-Power-User Progression

- **Recommendation:** Treat ordinary and power users as a progression rather
  than unrelated markets.
- **Hypothesis:** Outcome-focused users need useful defaults and a short
  first-success path.
- **Hypothesis:** Curious users gain value from understandable duration,
  token, cost, tool, and status details.
- **Hypothesis:** Controlling users may change model, provider, reasoning,
  prompts, tools, or session behavior.
- **Hypothesis:** Plugin users may install or request a new capability without
  becoming framework authors.
- **Hypothesis:** Progressive disclosure can help users become more capable
  without forcing architecture and configuration into the initial workflow.

## Built-In Feature Opportunity

- **Observation:** Current plugins already address session archive, search,
  filtering, status, pinning, ordering, titles, message counts, summaries,
  attachments, exports, notifications, authentication, configuration reload,
  MCP runtime control, usage, cost, and timing.
- **Hypothesis:** Some of these features correspond to user pain currently
  solved by scripts, proxies, separate viewers, dashboards, or paid products.
- **Recommendation:** Research each feature by user job, competitor support,
  workaround, search language, community evidence, readiness, limitation, and
  best visual proof.
- **Recommendation:** Use adaptive parallel research handoffs after the
  inventory reveals coherent feature clusters rather than defining every
  branch in advance.

## Compatibility Transparency

- **Recommendation:** Maintain separate views for configured-agent
  compatibility, provider/account support, and application-wide features.
- **Recommendation:** Distinguish supported/default, supported/optional,
  partial, experimental, planned, not implemented, not applicable, and unknown
  states.
- **Recommendation:** Distinguish code present in the repository from a plugin
  being packaged, loaded, default-enabled, frontend-supported, automatically
  tested, and real-provider verified.
- **Hypothesis:** An explicit compatibility and limitation catalog can build
  trust and provide focused contribution paths.

## Mobile and Bridge

- **Observation:** First-party coding-agent products increasingly provide
  mobile continuity, making mobile access important but insufficient as a
  standalone differentiator.
- **Hypothesis:** Crystal Lattice can differentiate through one open mobile and
  desktop workspace across several configured-agent styles and providers.
- **Question:** Do users need to continue sessions created by official
  upstream applications, or will they adopt future sessions created inside
  Crystal Lattice?
- **Recommendation:** Treat upstream-session import or interoperability as an
  explicit research question.
- **Recommendation:** Present a future managed bridge as optional managed
  convenience while preserving direct local-network and user-operated bridge
  paths.

## Open Questions

- Which user group should receive primary homepage emphasis?
- Is the clearest category coding agent, coding-agent workspace, unified coding
  agent, transparent coding agent, or agent platform?
- How many target users actively switch among coding-agent products or model
  families?
- Which duplicated setup work causes meaningful frustration?
- Which built-in session and transparency features affect adoption or
  retention?
- Do users value compatibility with an upstream style without official session
  import?
- Which missing compatibility features are release blockers versus honest
  contribution opportunities?
- Can natural-language customization be made safe and understandable for
  non-authors?
- Which non-coding workflows justify a polished general-purpose profile?
- What remote-access outcome would justify paying for a managed bridge?
- Which privacy-compatible measurement method is acceptable for website
  experiments and production iteration?

## Current Recommendation

Use progressive website releases:

1. make the current site useful and truthful for early users;
2. update it after built-in feature, search, community, and competitor
   evidence;
3. update it after early-user and remote-access research;
4. perform a larger validated rewrite after synthesis and experiments;
5. continue bounded post-release learning.
