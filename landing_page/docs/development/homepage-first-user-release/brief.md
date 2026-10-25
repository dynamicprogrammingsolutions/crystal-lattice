# Homepage First-User Release Brief

Status: **Draft for owner review — not implemented.**

Updated: 2026-10-23

## Page role

The homepage should answer:

> What is Crystal Lattice, why might it be useful for my coding work, and what
> is the shortest truthful path to try it?

The page orients, demonstrates, and routes. It does not reproduce the complete
compatibility catalogue, plugin-authoring guide, bridge-deployment guide,
Python SDK reference, or product history.

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
2. Where does it run and who owns the working files and sessions?
3. What does the complete application workspace look like?
4. What remains visible while a session is running?
5. What can be configured without changing the whole application?
6. How can provider- or feature-specific behavior appear in the interface?
7. Do Desktop and mobile open the same Crystal Lattice sessions?
8. What is the shortest current path to install and connect?
9. Where should I go for compatibility, customization, mobile, source, or
   contribution detail?

Page length is not a target. Every retained section must answer one of these
questions, prove an important claim, or provide a necessary next route.

## Terminology

### Primary-language decisions

- Do not use **AI agent** as the product category or hero terminology.
- Do not say **your AI agents**, **agent platform**, or **agent runtime** in
  the opening explanation.
- Explain the product in terms of a coding workspace, sessions, conversations,
  models, tools, profiles, provider controls, Desktop, and mobile.
- Say that Crystal Lattice runs on the visitor's computer. Do not describe
  ordinary use as operating infrastructure or a self-hosted runtime.
- Use **workspace** for the application-level relationship among sessions,
  selected conversation, configuration, and clients.
- Use **session** for persistent work that contains a conversation and its
  working state.

### Terms introduced after the ordinary product explanation

- **Profile** describes a reusable setup that can select instructions, tools,
  model/provider defaults, and related controls.
- The current interface label **Agent** may appear when naming the real
  `Agent` picker. Public prose should introduce it as the profile picker rather
  than assume that “agent” is already the visitor's product category.
- **Provider** is introduced when provider-specific controls or metadata are
  shown.
- **Plugin** is introduced after its user consequence is clear: a plugin can
  add or replace behavior, tools, settings, actions, reports, or interface
  controls.
- **Coding agent** may be used in compatibility or category detail after the
  product has been explained. It is not required in the hero.

### Terms excluded from the opening path

- AI agent;
- harness;
- model-native;
- provider-native;
- runtime session;
- application plugin;
- feature plugin;
- self-hosted infrastructure.

These terms may appear on focused technical pages where they are necessary and
defined.

## Concept ownership

| Concept | Homepage treatment | Authoritative detail |
| --- | --- | --- |
| Product category and primary benefit | Hero and opening copy | This brief and selected homepage copy |
| Complete application shape | One large Desktop workspace figure | Product UI and maintained screenshot source |
| Persistent sessions | Product-at-a-glance explanation | Product documentation |
| Visible model/provider/request information | One focused proof | Provider and product documentation |
| Profiles and configuration | One compact real profile-picker proof | Configuration documentation |
| Replaceable or extensible behavior | One provider/plugin UI proof and a concise explanation | Plugin documentation |
| Desktop/mobile continuity | One matched, separately framed pair | Mobile and Desktop documentation |
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

- a plain-language category;
- one concrete benefit;
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
- profile or model identity;
- current request/session state where useful.

The figure establishes the application before smaller proof images are
introduced. Short labels below the figure may identify sessions, profile,
provider controls, and clients without painting annotations into the image.

### 3. Visible, configurable, and extensible

These qualities remain distinct:

- **Visible:** important model, provider, request, usage, cost, tool, or state
  information can remain inspectable when available.
- **Configurable:** a profile and provider settings can change the setup
  without forcing the visitor through several unrelated configuration files.
- **Extensible:** plugins can add or replace coherent behavior and UI without
  requiring the complete application to be replaced.

Use three consistent proof rows or figures. Do not turn the concepts into
three slogan cards with decorative icons.

### 4. Desktop and mobile continuity

Owns:

- one matching Crystal Lattice session;
- separately framed Desktop and mobile clients;
- the fact that the phone is another client for the sessions on the computer.

Connection methods remain in Getting Started.

### 5. Getting Started

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

### 6. Secondary routes and final action

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
- imply broad non-coding product fit from one demonstration;
- describe planned or test-only behavior as generally available;
- retain a visual slot whose claim is duplicated or no longer belongs on the
  homepage.

## Copy acceptance criteria

- The hero works for a visitor who has never heard “AI agent,” “harness,” or
  “provider-native.”
- The product category and primary benefit are understandable before any
  profile, provider, plugin, or connection terminology appears.
- The opening copy says that Crystal Lattice runs on the visitor's computer.
- Every heading communicates a product relationship when read without its
  paragraph.
- “Workspace,” “session,” “profile,” “provider,” and “plugin” each have one
  stable meaning.
- Public copy distinguishes Crystal Lattice profiles from official upstream
  applications.
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
