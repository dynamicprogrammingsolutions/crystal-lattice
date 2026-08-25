# Manual Review: Non-Validated Ideas and Discussion Details

Status: Unvalidated manual-review backlog, August 25, 2026.

## Exclusion Notice

This page is intentionally:

- not linked from the website research index;
- not included in any task `References` or `Start here` section;
- not a source of current product facts;
- not a specification or requirement;
- not an approved content brief;
- not an execution plan;
- not evidence that an idea is valuable, feasible, safe, or intended.

Unless a task explicitly names this file, an agent that discovers it
incidentally must not use it as task context, implementation direction,
research evidence, public copy, or a reason to broaden scope.

This page exists for manual review of ideas and details from the initial
product-website discussion that were not promoted into tasks, specifications,
current documentation, or durable research findings.

## Status Values

- **Research candidate:** potentially useful, but unsupported or insufficiently
  specified.
- **Creative language only:** possible wording, not an approved proposition or
  public claim.
- **Design candidate:** possible product, information-architecture, or UX
  shape requiring separate validation and ownership.
- **Deferred detail:** deliberately omitted from the current durable owner
  until a prerequisite decision exists.
- **Dropped — corrected:** based on a framing or factual assumption explicitly
  corrected during discussion.
- **Dropped — unverified:** stated or implied without enough evidence to retain
  as fact.
- **Dropped — premature commitment:** would select naming, pricing,
  architecture, or behavior before research and approval.

## Manual Review Workflow

For each item considered:

1. Check whether a current specification, research finding, task, or
   implementation document already owns the concept.
2. If already owned, delete the duplicate from this page or mark it as
   superseded by the durable owner.
3. If it is a factual claim, verify it through the owning package or approved
   external research before promotion.
4. If it is a research question, add it to an approved research task only when
   it can change a material decision.
5. If it is a product or UX idea, identify ownership, safety, dependencies,
   acceptance behavior, and whether a separate task is justified.
6. If it is creative language, test comprehension and relevance before adding
   it to the content specification or public copy.
7. If it is rejected, record the reason in the discussion-retention map when
   the rejection is important to future work, then remove it from this page.

Promotion requires moving the accepted idea into its proper durable owner.
Leaving it on this page does not count as retention in a target, task, or
finding.

## Creative Positioning and Copy Candidates

These formulations preserve possible language only. Their underlying product
ideas may already be represented in the positioning baseline or content
specification.

| Candidate wording | Status | Manual-review note |
|---|---|---|
| “One coding-agent workspace. Many model families.” | Creative language only | Test whether “model families” is understandable and whether the statement overemphasizes switching rather than useful work. |
| “One coding-agent workspace for the models and workflows you actually use.” | Creative language only | Possible unified-workspace framing; needs differentiation and comprehension evidence. |
| “Know what your coding agent is doing—and change it.” | Creative language only | Combines transparency and customization; may promise inspectability or modification surfaces not yet delivered uniformly. |
| “Stop setting up a different agent for every model.” | Creative language only | Strong multi-agent convenience framing; needs evidence that duplicated setup is an important problem. |
| “A coding agent that does not hide the harness.” | Creative language only | “Harness” may be insider language and “does not hide” may imply unsupported visibility. |
| “Start with a ready coding agent. Change anything when you need to.” | Creative language only | “Anything” is too broad unless narrowed; useful as a direction for progressive disclosure. |
| “The open coding agent that can change with your workflow.” | Creative language only | Needs evidence that openness and adaptability are differentiating enough to lead. |
| “Ask your coding agent to change the coding agent.” | Creative language only | Memorable natural-language customization concept; depends on a safe user-owned plugin workflow. |
| “Your agent is not trapped in a terminal.” | Creative language only | Historical brainstorm language; remote/mobile access is no longer unique by itself. |
| “Your workflow does not need to be accepted upstream to exist.” | Creative language only | Strong plugin-ownership idea; may require explanation for users unfamiliar with upstream product constraints. |
| “The model gets the harness it expects.” | Creative language only | Model-family compatibility idea; likely too technical for primary consumer copy without explanation. |
| “Agent conversations are work artifacts, not disposable chats.” | Creative language only | Possible session-workbench framing; “artifacts” conflicts with repository terminology guidance and should be rewritten if revisited. |
| “Crystal Lattice is an open coding-agent workspace for people who use more than one model or want more control over how their agent works.” | Creative language only | Provisional explanatory sentence; may narrow the audience too early and needs evidence. |
| “Use Codex-style, Claude Code-compatible, Gemini-, Qwen-, Kimi-, and other configured agents from the same desktop and mobile app.” | Creative language only | Requires a current compatibility matrix and careful trademark/non-affiliation language. |

## Category and Audience Labels

| Idea or detail | Status | Manual-review note |
|---|---|---|
| “Coding-agent workspace” as the primary category | Research candidate | Clearer than “agent infrastructure,” but must be tested against “coding agent” and “agent platform.” |
| “Unified coding agent” as the primary category | Research candidate | May imply one generic behavior rather than model-family-specific profiles. |
| “Transparent coding agent” as the primary category | Research candidate | Transparency may be latent value rather than an initial search or purchase driver. |
| “Agent application platform” as the primary category | Research candidate | May attract builders but make ordinary users think the product is only a framework. |
| “Coding-agent-first platform” as an umbrella | Research candidate | May support broader workflows later without making general-purpose capability the first promise. |
| “Ordinary user” as a public audience label | Deferred detail | Useful internally but potentially patronizing or imprecise in public copy. |
| “Power user” as a public audience label | Deferred detail | Familiar but may exclude curious users who benefit from progressive transparency. |
| “Vibe coder” as a public audience label | Research candidate | Could describe a reachable audience but may date quickly or carry unwanted connotations. |
| Developers, non-developers building with AI, and other AI-assisted knowledge workers as one audience | Research candidate | Their jobs, onboarding, trust, and feature needs may differ materially. |

## Possible Product Naming

| Idea or detail | Status | Manual-review note |
|---|---|---|
| Crystal Lattice as the overall product/platform name | Design candidate | Current usage is broad but the final naming architecture is not specified. |
| Crystal Lattice Control as the mobile and desktop client family | Design candidate | Already used by current clients, but public naming consistency needs later review. |
| “Crystal Lattice Connect” as a managed remote-access name | Dropped — premature commitment | Retain only as a naming test candidate if task 110 or 130 explicitly reintroduces it. |
| Use “managed remote access” instead of “hosted bridge” in consumer copy | Research candidate | Describes an outcome more clearly, but the final service and name are not approved. |

## Candidate Website Routes and Action Labels

These are information-architecture candidates, not an approved page map.

### Possible Routes

- `/download` or `/start`
- `/mobile`
- `/desktop`
- `/cli`
- `/agents`
- `/compatibility`
- `/features`
- `/transparency`
- `/customize`
- `/plugins`
- `/developers`
- `/platform`
- `/sdk`
- `/connect`
- `/remote-access`
- `/open-source`
- `/contribute`
- `/security`
- `/privacy`
- `/compare`
- `/pricing`

Manual-review considerations:

- `/compare` should exist only when comparisons have current attributable
  evidence and a clear user decision.
- `/pricing` should not exist until the managed service and commercial offer
  are sufficiently defined.
- `/agents` and `/compatibility` may be one route or separate user and
  reference views.
- `/platform`, `/developers`, and `/sdk` may fragment one builder path.
- Local, user-operated bridge, and future managed access may fit one
  `/connect` page or require separate focused routes.

### Possible Action Labels

- “Try Crystal Lattice”
- “Start a workspace”
- “Download Crystal Lattice”
- “Use Crystal Lattice”
- “Compare configured agents”
- “Customize your agent”
- “Build with Crystal Lattice”
- “Connect from mobile”
- “Connect remotely”
- “Self-host the bridge”
- “Join the managed-access waitlist”
- “View the source”
- “Contribute”

Status: Creative language only. Final labels depend on distribution,
availability, audience priority, and experiment results.

## Product and UX Ideas

### Inspect Active Agent

Status: Design candidate.

A possible transparency surface could show:

- effective configured agent;
- model and provider;
- authentication/account mode;
- compiled system or developer instructions;
- active tools and model-visible schemas;
- enabled plugins;
- request and reasoning settings;
- provider-native capabilities and state;
- estimated context or request size;
- current-turn and cumulative usage/cost;
- current limitations or unavailable metadata.

Open questions:

- which details are already available through current APIs;
- which information can be exposed safely;
- default versus expanded disclosure;
- provider-specific redaction;
- whether this is a session view, settings view, message detail, or separate
  inspector.

### Natural-Language Customization Examples

Status: Research candidate.

Possible user requests discussed:

- “Add an archive action.”
- “Show cost below every message.”
- “Create a status for sessions waiting for review.”
- “Add a button that exports the current answer.”
- “Change how the model is instructed for this repository.”
- “Add a provider-specific control to settings.”

A potential safe flow:

1. interpret the desired user outcome;
2. identify the appropriate plugin type;
3. create or fork a user-owned local plugin;
4. show the source diff and UI effects;
5. generate or run validation;
6. load the local plugin;
7. reload the application;
8. show success or failure;
9. support rollback.

This exact workflow is not a current product commitment.

### General-Purpose Profile Candidates

Status: Research candidate.

Possible non-coding uses discussed:

- technical research;
- document and report workflows;
- project planning;
- personal knowledge work;
- data processing;
- content generation;
- operations or support workflows;
- simple AI chat.

The ability to send general prompts is not enough. A public general-purpose
claim would need polished defaults, tools, UI, and evidence for a valuable job.

### Existing Upstream Session Import

Status: Research candidate.

Potential behavior:

- import or display sessions created by official coding-agent products;
- continue an imported session through a compatible Crystal Lattice profile;
- attach Crystal Lattice mobile/desktop control to an upstream session.

This is not current behavior and may be technically or contractually
incompatible with some products. The durable research question is already
owned elsewhere; the possible product shapes are preserved here only for
manual review.

## Commercial and Remote-Access Details

| Idea or detail | Status | Manual-review note |
|---|---|---|
| Managed service includes account/device discovery, automatic reconnect, multi-computer routing, push notifications, deep links, and no manual bridge deployment. | Design candidate | Individual capabilities depend on modular bridge, identity, notification, E2EE, and frontend work. |
| Managed service is bundled rather than sold as a relay alone. | Research candidate | Packaging and willingness to pay are unvalidated. |
| A free trial or constrained free allowance reduces adoption risk. | Research candidate | No pricing or unit-economics evidence exists. |
| Hosted service is not placed in the primary homepage proposition before the core coding-agent value is clear. | Research candidate | Likely sensible, but final homepage hierarchy awaits positioning research. |
| A comparison of local network, user-operated bridge, and managed remote access helps users choose. | Design candidate | Could become a focused connection page if current facts and service status support it. |

## Research and Experiment Details Not Yet Adopted

| Idea or detail | Status | Manual-review note |
|---|---|---|
| Test several hero/proposition variants before final information architecture. | Research candidate | The experiment task owns selection and method; no exact variants are approved. |
| Use a waitlist or fake-door test for managed remote access. | Research candidate | Requires privacy, measurement, product, and remote-mutation approval. |
| Compare a simple default view with progressively expanded transparency. | Research candidate | Useful for latent-value testing; exact prototype and metrics are not defined. |
| Observe users switching configured-agent profiles for different tasks. | Research candidate | Could test multi-agent convenience but needs realistic participant workflows. |
| Test whether users prefer compatibility profiles over installing and configuring several official products. | Research candidate | Must distinguish willingness to switch from curiosity about another interface. |
| Test whether explicit compatibility gaps increase trust or discourage adoption. | Research candidate | Could inform the matrix presentation and contributor messaging. |

## Corrected or Rejected Details

These are preserved only to prevent accidental reintroduction.

| Detail | Status | Reason |
|---|---|---|
| “Run agents on your own infrastructure.” | Dropped — corrected | Ordinary use is a process running on the user's computer; “infrastructure” adds inaccurate operational framing. |
| “Self-hosted runtime” as primary consumer language. | Dropped — corrected | Only the bridge may be user-operated/self-hosted. |
| Generic VPN or tunnel tools are direct product alternatives to the bridge. | Dropped — corrected | They are workaround substitutes, not equivalent coding-agent experiences. |
| Crystal Lattice currently opens existing official Claude Code or Codex sessions. | Dropped — corrected | Crystal Lattice owns its compatibility-profile sessions unless import/interoperability is implemented. |
| OpenCode uses one standard tool surface for every model. | Dropped — unverified | Requires direct current investigation. |
| Mobile access alone is a unique differentiator. | Dropped — corrected | First-party coding-agent products now provide mobile continuity; the possible value is the integrated multi-profile/open workspace. |
| A fixed final route map should be implemented before research. | Dropped — premature commitment | The information architecture task follows synthesis and experiments. |
| A final hosted-service name or pricing page should be created now. | Dropped — premature commitment | Product, naming, pricing, trust, and release behavior are not validated. |

## Items Intentionally Not Duplicated Here

The following have durable owners and should not be copied into this backlog:

- visual communication hypotheses and the reproducible asset pipeline;
- evidence-type, pilot, review, privacy, and confidence rules;
- current product and compatibility facts;
- content-system implementation;
- product website content requirements;
- progressive rewrite sequence;
- task handoff and output conventions.
