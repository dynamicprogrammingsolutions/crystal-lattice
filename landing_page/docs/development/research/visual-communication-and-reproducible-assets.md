# Visual Communication and Reproducible Assets

Status: Supporting product-website knowledge, August 25, 2026.

This page preserves visual communication hypotheses and asset-production
principles identified during initial website planning. It is not a current
product claim, an approved storyboard, or documentation of an implemented
capture system.

The approved content architecture determines which visuals are required.
`tasks/20260825-crystal-lattice-product-positioning-and-website/160-visual-proof-and-reproducible-assets.md`
owns implementation.

## Visual Communication Principles

- A visual must prove or clarify a material product relationship.
- Product proof is more valuable than decorative application framing.
- A screenshot or recording must represent current verified behavior.
- Architecture diagrams distinguish what runs on the user's computer from
  clients and optional remote connectivity.
- Visuals should explain one relationship at a time rather than compress the
  full architecture into one diagram.
- The page brief and claim/proof matrix decide whether a concept belongs on the
  homepage, a focused product page, compatibility content, documentation, or
  nowhere in public communication.

## Candidate Visual Proof

These are hypotheses for later content briefs and visual review.

### Cross-Interface Outcome

A short real sequence may demonstrate:

1. work begins in Crystal Lattice on the computer;
2. the coding agent continues in the same Crystal Lattice session;
3. a notification appears on the phone;
4. the user opens the relevant session;
5. the user inspects, continues, or approves the next action.

The value is continuity across interfaces, not a collage of unrelated
screenshots.

### One Workspace Across Configured Agents

A visual may show several configured-agent profiles using the same:

- session list and organization;
- desktop and mobile clients;
- connection setup;
- notifications;
- attachments;
- application actions.

The visual must not imply that Crystal Lattice sessions are sessions created by
the official upstream coding-agent applications.

### Plugin Propagation

A diagram or recording may show one plugin contributing several related
effects:

```text
one plugin
  ├─ changes request, provider, or tool behavior
  ├─ adds a setting
  ├─ adds an action
  ├─ reports a notification or operation state
  └─ appears through supported mobile and desktop UI contracts
```

This communicates the user consequence of UI-aware plugins without requiring
the visitor to learn plugin protocol names first.

### Local Process and Connectivity

A small trust-oriented diagram may show:

```text
Crystal Lattice running on the user's computer
  ├─ working directory and sessions
  ├─ model/provider credentials
  └─ configured agents and plugins
       ↕
  terminal / desktop / mobile / application clients
       ↕ optional when away from the local network
  user-operated or future managed Crystal Lattice bridge
```

Security, encryption, identity, and managed-service labels must match current
owning-package behavior.

### Configured-Agent Composition

A layered visual may explain why configured-agent profiles differ:

```text
model and provider
system/developer instructions
model-facing tool schemas and result behavior
provider-native capabilities and state
application settings, actions, notifications, and UI
```

This is preferable to presenting only a long model-name table when the intended
message concerns behavior and compatibility.

### Session Workbench

Real product states may prove:

- search and filtering;
- archive and restore;
- pinning and status;
- title generation;
- notifications and long-running operation progress;
- attachments and exports;
- snapshots or other delivered history controls.

Feature selection should follow the findings from
`tasks/20260825-crystal-lattice-product-positioning-and-website/050-built-in-feature-opportunity-mining.md`
and approved content briefs.

### Transparency

A focused proof may show:

- configured agent, model, provider, and authentication mode;
- tool calls or operation state;
- input, cached, output, and cumulative token information;
- actual cost or clearly labeled API-equivalent estimation;
- duration and reasoning controls;
- active instructions, tools, or settings only where currently inspectable.

The proof must not imply uniform metadata across providers.

### Compatibility and Contribution

A visual compatibility surface may distinguish:

- configured-agent compatibility;
- provider and account support;
- application-wide features;
- default, optional, partial, experimental, planned, unavailable, and
  not-applicable states;
- last verification and evidence;
- contribution opportunities.

## Reproducible Asset Pipeline

Production screenshots, diagrams, and recordings should be reproducible
outputs of maintained scenarios rather than one-time manually assembled
images.

### Asset Catalog and Capture Record

Before capture, maintain catalog and capture records for:

- stable visual ID;
- page brief and claim being supported;
- owning product surface;
- required application, connection, configured-agent, and session state;
- fixture or demo-data version;
- capture platform, viewport, theme, and locale;
- automation or human-capture boundary;
- expected sensitive-data review;
- alt text or transcript;
- production filename and route;
- freshness trigger and last verified revision.

### Deterministic Demo State

Use sanitized, versioned:

- configuration;
- configured agents;
- plugins;
- repositories and files;
- sessions and messages;
- notifications and operation states;
- attachments;
- connection identities and labels.

Do not depend on a developer's personal configuration, live credentials,
private repositories, private sessions, or unpredictable hosted-model output
when deterministic fixture behavior can prove the same UI relationship.

### Stable Automation Boundaries

Use the narrowest reliable mechanism:

- browser automation for the static website and browser-rendered proof;
- Detox for mobile UI and screenshot scenarios that require native React
  Native behavior;
- XCUITest when iOS system integration or behavior cannot be proved reliably
  through Detox;
- macOS production-root/native UI tests for desktop windows, popovers, and
  platform behavior;
- focused fixture or component rendering for deterministic low-level states;
- explicit human capture only when automation cannot represent the required
  current product boundary.

Production entities and controls used by automation need stable identifiers.
Capture automation must exercise production UI rather than harness-only copies.

### Diagram Sources

Keep diagrams in a maintainable text or vector source format. Generated raster
or optimized variants are outputs, not competing authored sources.

Diagram updates should be reviewable as changes to:

- nodes and labels;
- ownership;
- data or control flow;
- current versus optional boundaries;
- accessibility text.

### Draft and Production Separation

- Unreviewed captures, recordings, frames, generated variants, reports, and
  review contact sheets belong under `landing_page/artifacts/visual-assets/`
  or the owning package's ignored `artifacts/` directory.
- Approved, sanitized source masters used for reproducible website derivatives
  belong under `landing_page/visual_assets/sources/`.
- Retained capture-state records and reviews belong under
  `landing_page/research/160-visual-proof-and-reproducible-assets/`.
- Only approved, sanitized, optimized derivatives belong under
  `landing_page/public/`.
- Generated website output remains ignored and is never edited directly.

### Review

Before promotion to `public/`, verify:

- the represented behavior is current;
- the claim and page brief still require the visual;
- no credentials, personal data, private content, or misleading staged state
  appears;
- mobile and desktop layouts are readable at their actual presentation size;
- light/dark, contrast, crop, scale, animation, and device framing are
  appropriate;
- alt text or transcript communicates the important relationship;
- third-party names, logos, and content are used appropriately;
- the production route resolves the optimized file.

### Freshness

Refresh or retire an asset when:

- the represented product behavior changes;
- the UI changes materially;
- the compatibility or release state changes;
- a referenced configured agent, provider, account, or bridge state changes;
- the page claim or architecture changes;
- the catalog or capture record's verification period expires.

An old but visually attractive screenshot must not remain when it no longer
proves the current claim.

## Scope Boundary

This page preserves the desired complete visual and asset-production model.
The current early executable catalog, source lifecycle, derivative generation,
and browser verification are documented in
[Visual content and screenshot generation](../visual-content-and-screenshot-generation.md).
This page does not claim that the final native fixtures, capture scenarios, or
complete freshness automation have been delivered.
