# Product Website Content

## Purpose

The Crystal Lattice website must help an unfamiliar visitor understand the
product, determine whether it fits their work, choose an appropriate first
action, and distinguish current behavior from incomplete or future
capabilities.

The website is progressively improved as product, market, community, and
early-user evidence develops. A planned later rewrite does not justify leaving
the currently deployed website confusing, inaccurate, or visibly unfinished.

## Current Product Baseline

Until an evidence-backed content decision replaces this baseline, the website
should present Crystal Lattice primarily as a coding-agent product.

Crystal Lattice runs as an ordinary process on the user's computer in the
working directory where the agent should operate. Desktop, mobile, terminal,
and programmatic clients can interact with Crystal Lattice sessions through
the supported application interfaces.

The website must not imply that ordinary use requires operating agent
infrastructure. Technical server, API, and transport terminology belongs in
the appropriate detailed explanation.

Crystal Lattice configured agents may provide compatibility-oriented tools,
instructions, and workflow behavior resembling Codex, Claude Code, Gemini,
Qwen, Kimi, Grok, or other coding-agent products. These are Crystal Lattice
profiles and sessions, not sessions owned by the official upstream
applications.

Broader general-purpose agent behavior is a product and positioning hypothesis
until research and delivered defaults support a clearer claim.

## Visitor Groups

The content must support a progression rather than assume a strict binary
between ordinary and power users.

### Outcome-Focused Users

They need:

- a clear statement of what the product does;
- a short first-success path;
- current download and availability information;
- useful defaults without reading architecture documentation.

### Curious and Controlling Users

They may value:

- model and provider visibility;
- token, duration, cache, and cost information;
- active settings and tools;
- session organization;
- control over prompts, tools, and provider-native features.

The website should make these capabilities understandable without requiring
the visitor to know internal plugin terminology first.

### Plugin Users and Authors

They need to understand:

- what product behavior plugins can change;
- that plugins may contribute application UI as well as model tools;
- how a user-owned plugin can be created, loaded, validated, and replaced;
- where current plugin documentation and source examples live.

### Contributors

They need:

- an honest compatibility and limitation view;
- clear gaps where contributions are welcome;
- links to source, documentation, tests, and contribution guidance.

### Remote-Access Users

They need to understand:

- direct mobile connection on the same local network;
- the bridge as Crystal Lattice-specific remote connectivity when away from
  that network;
- the difference between a user-operated bridge and any future managed
  service;
- the current security and availability state without future guarantees.

## Primary Proposition and Audience Paths

The website should have one primary proposition at a time. It may route to
secondary audiences, but it must not give equal above-the-fold weight to every
technical layer and possible user.

The exact leading proposition remains evidence-dependent. Candidate directions
include:

- one coding-agent workspace across several model-family styles;
- an inspectable and controllable coding agent;
- a coding agent whose behavior and UI can be changed through plugins;
- a coding-agent-first platform that can support broader agent workflows.

Public copy must use only the currently approved direction. Research
hypotheses remain in development research pages.

Audience paths should make the next action clear for visitors who want to:

- use the product;
- compare configured-agent compatibility;
- customize the product;
- build plugins or applications;
- connect from mobile;
- contribute.

## Compatibility and Product Identity

Compatibility content must distinguish:

- official upstream products and accounts;
- Crystal Lattice configured-agent profiles;
- model family;
- provider route;
- authentication or account mode;
- application-wide features;
- default-enabled and optional capabilities.

A compatibility statement must identify an appropriate state:

- supported and default-enabled;
- supported but optional;
- partial;
- experimental;
- planned;
- not implemented;
- not applicable;
- unknown or not recently verified.

Simple checkmarks must not flatten materially different compatibility states.

Compatibility content should identify:

- important supported behavior;
- material gaps;
- current provider/account limitations;
- last verification date where behavior can drift;
- evidence or package source;
- contribution opportunities where appropriate.

The website must not claim complete parity with a proprietary coding-agent
product merely because selected tools or prompts are compatibility-oriented.

## Transparency

The website should explain transparency as more than source availability.

Relevant dimensions may include:

- open-source implementation;
- visible configured agent, model, provider, and auth mode;
- inspectable instructions, settings, and enabled tools where the product
  supports them;
- visible tool calls and operation state;
- input, cached, output, and cumulative token information;
- actual cost or clearly labeled API-equivalent cost estimation;
- explicit compatibility limitations.

The website must not imply that every provider or configured agent exposes the
same metadata.

## Session and Workflow Features

User-facing plugins may provide valuable capabilities such as:

- session search and filtering;
- titles and generated titles;
- pinning;
- archive and restore;
- workflow status;
- ordering;
- summaries;
- attachments and exports;
- notifications and operation progress.

The website should describe the user problem and result before explaining that
the capability comes from a plugin. Feature priority remains research- and
evidence-dependent.

## Customization

The website may explain that users can add or replace product behavior through
plugins. It must distinguish:

- using an existing plugin;
- changing configuration;
- creating a user-owned plugin;
- future or experimental natural-language plugin creation.

Natural-language customization must not be presented as a current simple
workflow until source visibility, validation, reload, failure reporting, and
rollback behavior support the claim.

## Local and Remote Connection

The normal explanation is:

1. Crystal Lattice runs on the user's computer.
2. On the same local network, a mobile client can connect directly.
3. Away from that network, a bridge can relay the Crystal Lattice connection.

The bridge may be user-operated. Any future managed bridge must be presented as
optional managed convenience and must not erase the open user-operated path.

Public content must not claim security, encryption, account, entitlement,
subscription, quota, or availability behavior before the owning product work
has delivered and verified it.

## Current, Partial, and Future Behavior

The website describes current behavior directly.

When a limitation matters to a product decision, express it in public product
language. Do not expose task phases, requirement IDs, checkpoints, approval
state, or internal progress.

Future behavior may appear only in an explicitly appropriate context such as:

- coming-soon distribution state;
- a waitlist;
- a public roadmap or contribution opportunity;
- a clearly identified planned compatibility row.

Future behavior must not be placed beside current behavior in a way that makes
the two indistinguishable.

## Proof

Important claims require concrete proof appropriate to the claim:

- a real product screenshot or recording;
- a verified command or example;
- current compatibility evidence;
- a maintained release or download;
- source and documentation;
- automated or human product verification.

The public website must not render:

- planning placeholders;
- missing-file labels;
- example APIs known to be inaccurate;
- code carrying an internal verification warning;
- speculative screenshots;
- unverified comparison tables.

## Progressive Revision

The website uses progressive releases:

1. a release-safe early-user baseline based on current product truth;
2. a first update based on built-in feature, search, community, and competitor
   evidence;
3. an update based on early-user and remote-access findings;
4. a larger validated release based on synthesis, experiments, page briefs,
   visual proof, and current release state;
5. bounded post-release iteration.

Each deployed version must be independently useful and truthful.

Research does not modify the website automatically. A rewrite or content
decision updates this specification when the intended communication target
changes, then updates current public content.

## Non-Goals

This specification does not:

- select final copy before evidence supports the decision;
- require the homepage to document every plugin or provider;
- turn development terminology into marketing language;
- treat technical possibility as a polished user capability;
- require all research to finish before the website helps early users;
- define technical content formats or rendering;
- redefine product contracts owned by other packages.

## Acceptance Examples

An unfamiliar visitor should be able to answer:

- What is Crystal Lattice?
- Where does it run?
- Is it primarily a coding agent today?
- How do desktop and mobile relate to it?
- What does the bridge do?
- Is a Claude- or Codex-style profile the official upstream application?
- Which models, providers, accounts, and profile features are actually
  supported?
- What can plugins change?
- What can I try now?
- Where can I contribute?

The exact wording and page structure may change while these comprehension
outcomes remain stable.
