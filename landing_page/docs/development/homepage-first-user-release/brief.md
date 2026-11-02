# Homepage First-User Release Brief

Status: **Differentiator direction approved; exact copy and visual treatment
remain under review — not implemented.**

Updated: 2026-10-24

## Page role

The homepage should answer:

> What is Crystal Lattice, why might it be useful for my coding work, and what
> is the shortest truthful path to try it?

The page orients, demonstrates, and routes. It does not reproduce the complete
compatibility catalogue, plugin-authoring guide, bridge-deployment guide,
Python SDK reference, or product history.

The opening separates necessary product orientation from actual
differentiation. Category, installation, sessions, model selection,
instructions, permissions, ordinary tool enablement, history, usage/cost
display, Desktop/mobile availability, and source availability may need to be
stated, but they do not become leading value claims merely because Crystal
Lattice supports them.

## Primary visitor

The first reading path is for someone who:

- uses models and tools for software work;
- may already use one or more coding-oriented applications;
- does not know Crystal Lattice terminology;
- wants to understand the product before reading installation or architecture
  documentation;
- needs a credible reason to continue to Getting Started.

Compatibility evaluators, customizers, plugin authors, mobile users, and
contributors remain supported through secondary routes. They do not receive
equal above-the-fold weight.

## Visitor questions

The proposed information order answers:

1. What kind of application is Crystal Lattice?
2. What does the complete application look like?
3. How can one configured agent use a materially different harness from
   another?
4. How does Crystal Lattice retain provider-native behavior instead of
   reducing every provider to one generic representation?
5. How can plugins change the application and session workflow, not only add
   model-facing tools?
6. What is the shortest current path to install and connect?
7. Where should I go for compatibility, customization, mobile, source, or
   contribution detail?

Page length is not a target. Every retained section must answer one of these
questions, prove an important claim, or provide a necessary next route.

## Terminology

### Primary-language decisions

- Use **application for configurable AI coding agents** as the current
  category direction. After the first category introduction, prefer
  **coding agent** or **agent** where the meaning is clear.
- Do not use the generic phrase **AI agent platform** as the primary
  definition. It is broader than the current coding-agent-first product and
  makes the developer/runtime architecture sound like the first-user product.
- Say that Crystal Lattice runs on the visitor's computer. Do not describe
  ordinary use as operating infrastructure or a self-hosted runtime.
- Use **configured agent** for the named `agents` configuration selected by a
  session. Do not replace this concept with **profile**.
- Use **harness** for the materially variable behavior around the model. In
  first-user language, define it briefly through the tool implementations,
  provider integration, context behavior, and controls used by the configured
  agent.
- Use **workspace** only for the visible application context. It is not the
  product category or primary differentiator.
- Use **session** as the ordinary unit of work without presenting session
  persistence or organization as a differentiator by itself.

### Relationship among the terms

- The **Crystal Lattice application** owns configuration, sessions, clients,
  and the extension system.
- A **configured agent** selects the provider/model configuration and plugin
  packages used by a session.
- The configured agent's **harness** may include different tool
  implementations and schemas, provider extensions, context behavior, and
  controls. This is more substantial than selecting another model, changing a
  prompt, or allowing a subset of one shared tool catalogue.
- A **plugin** supplies or changes one part of provider behavior, tool
  behavior, feature behavior, session/application behavior, or UI schema.
- A **session** uses a configured agent and may be opened through supported
  clients. The first-user homepage does not need to explain the complete
  configuration resolution model.

### Terms introduced after the category

- **Provider** is introduced when provider-specific controls or metadata are
  shown.
- **Provider-native** is introduced only when explaining that Crystal Lattice
  retains the provider's native request history separately from its normalized
  display history.
- **Plugin** is introduced after its user consequence is clear: plugins can
  compose harness behavior and can also contribute settings, actions,
  notifications, reports, and controls to the application.

### Terms excluded from the opening path

- AI agent platform;
- your AI agents;
- model-native;
- runtime session;
- self-hosted infrastructure.

Detailed plugin-kind names, request-pipeline terminology, native message field
names, and internal configuration resolution belong on focused technical
pages.

## Concept ownership

| Concept | Homepage treatment | Authoritative detail |
| --- | --- | --- |
| Product category | Concise hero orientation, not a differentiation claim | This brief and selected homepage copy |
| Complete application shape | One large Desktop workspace figure | Product UI and maintained screenshot source |
| Different harnesses per configured agent | Primary product claim with focused agent/tool proof | Agent configuration and plugin packages |
| Provider-native history and behavior | Focused explanation and diagram or product proof | Core/provider documentation |
| Plugins that affect the application | Focused cause/effect proof for settings, actions, reports, notifications, or controls | Plugin documentation |
| Included configured agents | Concise recognizable examples plus a route to detailed compatibility | Public compatibility catalogue |
| Sessions and application organization | Visible in the application overview without a separate value claim | Product documentation |
| Desktop/mobile continuity | Availability and connection explanation near Getting Started | Mobile and Desktop documentation |
| Installation and first connection | Six-step Getting Started | Package installation and connection guides |
| Compatibility matrices | Short route only, if retained | Focused compatibility content |
| Detailed bridge deployment | No homepage procedure | Bridge documentation |
| Plugin authoring | Short route only, if retained | Plugin authoring documentation |
| Python SDK examples | No unverified homepage example | SDK documentation and examples |
| Product origin and historical MVP | Not part of the first-use homepage | Case study or project history |
| Non-coding workflows | Secondary proof only after core positioning is clear | Later focused route or evidence-informed revision |

## Proposed information order

### 1. Hero

Owns:

- the category **application for configurable AI coding agents**;
- the primary differentiator that a configured agent can use a materially
  different harness, not merely another model or permission list;
- that the product runs on the visitor's computer;
- one primary route to Getting Started;
- one lower-emphasis route to source or documentation.

The hero should be text-led. It does not need to carry a screenshot when the
next section supplies a stronger full-width product view.

### 2. Product at a glance

Owns one large, framed Desktop image showing:

- the session list;
- the selected conversation;
- the composer;
- configured-agent identity;
- current request/session state where useful.

The figure establishes the application before focused differentiator proof is
introduced. It is orientation, not a claim that sessions, conversations, a
composer, or model selection are unusual.

### 3. Different harnesses per configured agent

Owns the primary product difference:

- each session uses a configured agent;
- configured agents can load materially different tool implementations,
  provider extensions, context behavior, and controls;
- this difference is broader than selecting another model, editing ordinary
  instructions, or allowing a subset of one shared tool inventory.

The accepted first-user wording direction may introduce included agents as:

> Crystal Lattice includes configured agents with Codex-oriented,
> Claude-compatible, Gemini-oriented, and other harnesses. These are Crystal
> Lattice implementations, not the official upstream applications.

Use the exact qualifier supported by each harness family rather than applying
one universal **compatible** claim. The homepage gives only enough recognizable
examples to make the concept concrete and routes detailed agent, harness,
provider, and plugin status to the public compatibility catalogue.

Use focused configured-agent and tool/harness proof. A second image is
justified only when it demonstrates a genuinely different harness composition
rather than another model name.

### 4. Provider-native fidelity

Owns:

- Crystal Lattice retains provider-native request history separately from the
  normalized form used for display and generic application behavior;
- provider-specific continuation state does not have to be reconstructed into
  one generic message/tool format;
- visible provider controls or metadata are supporting examples, not the
  complete claim.

Prefer a concise maintained diagram when ordinary UI cannot communicate the
relationship accurately.

### 5. Plugins can affect the application

Owns:

- plugins may change provider, tool, feature, session, or application
  behavior;
- plugins may contribute settings, message/session actions, notifications,
  reports, and interface controls;
- extensibility is not limited to adding another model-facing tool.

Use a focused cause/effect relationship when possible: one plugin
configuration or capability beside the resulting genuine application control,
action, or report.

### 6. Getting Started

Retains six ordered steps:

1. install the CLI;
2. start a workspace;
3. download Desktop;
4. connect Desktop;
5. get the mobile app or join the release waitlist;
6. connect from mobile.

The default Desktop path stays local. Same-network mobile discovery, manual
address entry, and bridge access away from the local network are explained
separately.

Desktop/mobile availability and continuity belong here unless later review
shows a distinct homepage claim beyond ordinary client access.

### 7. Secondary routes and final action

The first-release cut should prefer a compact route group for:

- compatibility;
- customization and plugins;
- mobile;
- documentation;
- source and contribution.

Detailed bridge deployment, model/provider matrices, plugin-writing prompts,
and SDK examples do not remain inline merely because components already
exist.

## Claim boundaries

The homepage must not:

- imply that Crystal Lattice owns or imports sessions from official Codex,
  Claude Code, Gemini, or other upstream products;
- imply universal provider metadata or feature parity;
- imply public App Store or Google Play availability before maintained release
  evidence confirms it;
- imply that the bridge is required for local use;
- use “open source” as proof that runtime behavior is automatically visible;
- present model selection, configurable instructions, generic permissions,
  session persistence, history, cost display, Desktop/mobile access, or source
  availability as primary differentiators;
- claim that every configured agent has a distinct harness when two agents
  resolve to materially equivalent provider/tool behavior;
- describe a generic allow/deny tool list as proof of different harnesses;
- imply broad non-coding product fit from one demonstration;
- describe planned or test-only behavior as generally available;
- retain a visual slot whose claim is duplicated or no longer belongs on the
  homepage.

## Copy acceptance criteria

- The hero establishes the AI coding-agent category without defining Crystal
  Lattice as a generic AI agent platform.
- The difference between a configured agent and its harness is understandable
  without explaining the full configuration or plugin architecture.
- The opening copy says that Crystal Lattice runs on the visitor's computer.
- Primary value headings communicate materially differentiating information
  rather than ordinary coding-agent capabilities.
- “Configured agent,” “harness,” “plugin,” “workspace,” “session,” and
  “provider-native” each have one stable meaning.
- Public copy distinguishes Crystal Lattice configured agents from official
  upstream applications.
- Different harness claims identify actual differences in tool
  implementations, provider integration, context behavior, or controls rather
  than only model, instruction, or permission changes.
- Provider-native fidelity is not reduced to a generic transparency, token,
  usage, or cost claim.
- Plugin extensibility names application/session effects in addition to model
  tools.
- No section repeats another section's claim merely to use an available
  screenshot.
- Getting Started remains a shorter route than the product explanation that
  precedes it.

## Visual acceptance criteria

- One large image establishes the application before focused proof images.
- Text widths do not change arbitrarily with screenshot aspect ratio.
- Each screenshot title, bounded image surface, and caption read as one
  figure.
- Important interface text is readable at inline page size.
- Apparent UI magnification is consistent across related figures.
- Desktop and mobile receive restrained frames where the client relationship
  matters.
- Focus crops remain unframed when a device/window frame would add noise.
- Desktop, tablet, and mobile have intentional compositions rather than
  relying on automatic column stacking.
- Missing or rejected concepts leave no empty visual slot.
