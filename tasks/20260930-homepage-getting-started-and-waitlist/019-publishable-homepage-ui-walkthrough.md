# Prepare A Publishable Homepage With A UI Walkthrough

Parent Task:
`tasks/20260930-homepage-getting-started-and-waitlist/000-main.md`

Depends On:
`tasks/20260930-homepage-getting-started-and-waitlist/015-homepage-content-assets-layout.md`

Turn the reviewed homepage direction and accepted proof assets into a
publishable first version. Immediately after the hero, teach an unfamiliar
visitor what Crystal Lattice is by walking through the real product UI. Keep
installation and connection instructions in Getting Started, preserve the
remaining value-led feature sections, complete the essential missing visuals,
and remove placeholders, internal planning language, and unverified public
examples before the waitlist integration task begins.

## Requirements checklist

- [ ] Immediately after the hero, a full-width, screenshot-led walkthrough
      lets an unfamiliar visitor understand Crystal Lattice before asking them
      to install or configure it. The introduction explains the product
      through visible UI concepts rather than startup commands or runtime
      architecture.
- [ ] The walkthrough follows the approved bottom-up teaching order:
      Composer; Messages; Session actions; Session settings; and Workspace.
      It starts from the AI-chat interaction visitors already understand and
      expands from the next request to one message, the whole session, and
      finally many sessions.
- [ ] Each walkthrough chapter first explains the ordinary role of the UI area,
      then introduces the relevant Crystal Lattice distinction. It does not
      assume familiarity with coding-agent architecture, provider terminology,
      plugins, session history operations, or connection architecture beyond
      ordinary AI chat.
- [ ] The Composer stage uses a contextual conversation view and explains
      provider/request controls around the composer, including model,
      reasoning effort, web search, append/resend, immediate cancellation, and
      soft cancellation. Exact cancellation and resend semantics are verified
      through product tests before becoming public claims.
- [ ] The Messages stage distinguishes response metadata from actions at one
      point in history. It introduces genuine message footers and actions such
      as modify, fork, delete, and export; optional plugin examples such as
      **Send to Kindle** may demonstrate extensibility. OpenAI compaction may
      remain visible without forcing its model-specific explanation into the
      introduction.
- [ ] The Session actions stage explains controls that affect the whole task
      and clearly distinguishes them from message-scoped actions. The
      introductory proof focuses on a useful subset such as switch agent,
      settings, plugins, snapshots, title, status, and range operations rather
      than presenting the full power-user catalog without hierarchy.
- [ ] The Session settings stage explains that each session carries its own
      agent setup. It covers agent/profile selection, provider-specific
      options, per-session plugin enable/disable, and tools contributed by
      enabled plugins. It explains that a Crystal Lattice profile can change
      provider route, instructions, tools, features, and UI behavior rather
      than only selecting a model name.
- [ ] The Workspace stage explains the standard session list, search/filter,
      titles/subtitles, pinning, status, open/preview behavior, recent/update
      state, and visible request status across open sessions. The
      application-owned local Watchlist may be evaluated as an optional second
      proof after the standard list is understood and must not be described as
      a server pin or plugin-provided view.
- [ ] Public wording distinguishes Crystal Lattice Codex-, Claude-, Gemini-,
      Qwen-, Kimi-, Grok-, and related profiles from official upstream
      applications, accounts, and sessions.
- [ ] The walkthrough uses one consistent, sanitized product fixture so the
      same connection, agent, session, title, status, user request, assistant
      response, and visual identity persist while the tour moves through UI
      areas. Screenshots remain real product UI; composition may crop,
      highlight, or magnify source regions without inventing controls or
      values.
- [ ] Walkthrough navigation exposes descriptive labels such as Compose,
      Messages, Session actions, Session settings, and Workspace. It is
      responsive, keyboard accessible, swipe/scroll compatible,
      reduced-motion aware, and understandable without relying on unlabeled
      dots or autoplay.
- [ ] The walkthrough uses a candidate-first process: create and explain more
      genuine UI candidates than the final homepage will necessarily retain,
      bind them to the actual local page for responsive visual review, and
      select or defer them only at explicit human checkpoints.
- [ ] The former separate **One workspace for every model family** and
      **Sessions become workspaces** compact highlights are incorporated into
      the walkthrough without losing their approved values or durable
      alternatives. The remaining feature sequence is Vibe/Work from anywhere
      as compact end-user highlights, followed by the full-width Plugins and
      Transparency deep dives.
- [ ] The walkthrough explains UI roles without duplicating the later deep
      dives: it identifies what composer/message/session/workspace controls
      and metadata do; Plugins later explains how configuration contributes
      replaceable UI; Transparency later demonstrates the authored system
      message with placeholders, its compiled result, and configurable
      reporting.
- [ ] Public copy accurately distinguishes the application-owned shell and
      extension surfaces from plugin contributions. It may use the VS Code
      extension-model analogy, but it does not claim that every visible UI
      element is itself a plugin.
- [ ] **Work from anywhere** uses one truthful Desktop/phone composition with
      matching session identity, status, agent, latest prompt, and answer.
      Mobile availability is identified as public, tester-only, invite-only,
      or coming soon according to maintained release state.
- [ ] Getting Started retains the six approved steps in order: install CLI,
      start workspace, download Desktop, connect Desktop, get the mobile app,
      and connect from mobile. Steps 5–6 form a visibly related **Mobile
      access** group without making future or tester-only availability look
      like unrestricted public distribution.
- [ ] The mobile connection step presents the concepts in visitor order:
      local discovery on a trusted network, address and port as a fallback,
      and bridge access away from the local network. It explains the choice
      through the real connection UI rather than three equally prominent
      command fragments.
- [ ] The basic Desktop startup path remains local by default. Any Bonjour/LAN
      command plainly states that it makes the runtime reachable to other
      devices on the network and should be used on a trusted network.
- [ ] The Desktop connection step uses a compact real connection-editor proof
      with port `9000` and an understandable connected outcome. It does not
      retain a large planning placeholder.
- [ ] Screenshot titles and comments serve visitors: they explain what the
      pictured area proves, avoid repetitive templated phrases, retain
      provider/sample/availability qualifications, and contain no fixture,
      checkpoint, provenance, or task language.
- [ ] Public screenshots contain no invalid or fallback `?` icons, private or
      mixed-language task data, unnecessary raw identifiers, debug-focused
      timestamps, or other capture artifacts that make the proof look
      unfinished. Any genuine product change required to produce the accepted
      UI is approved and implemented on `develop` before reconciliation.
- [ ] The publish candidate contains no **Planned visual** panels, review
      status labels, disabled fake waitlist form, internal implementation
      notes, knowingly unverified SDK examples, or public instructions saying
      that later website work still needs to verify the claim.
- [ ] The lower homepage is reduced or revised so that advanced model,
      provider, bridge, plugin-authoring, and SDK material has a clear
      visitor role. Content that duplicates the primary flow, belongs in
      documentation, or is not yet verified is removed from the publish
      candidate rather than padding the first release.
- [ ] Current downloads, platform availability, invite/tester state, bridge
      availability, compatibility limitations, security implications, and
      open-source claims remain truthful and derive from maintained product
      or release evidence.
- [ ] The complete first version is visually reviewed on the actual page in
      light and dark themes at desktop, tablet, and phone widths. Important
      relationships remain legible at page size, and the visitor can reach a
      clear first action without reading the advanced material.
- [ ] The task updates the durable homepage decision record with the teaching
      sequence, copy theory, selected layout, visual mappings, release cuts,
      viable alternatives, and reasons for the final choices.
- [ ] No source promotion, waitlist deployment, production website push, or
      publication occurs before its explicit human checkpoint. The separate
      waitlist task integrates the real form and owns final production
      publication.

## Human decisions and actions required

- **HUMAN JUDGMENT — CANDIDATE STORYBOARD:** Review the five bottom-up
  chapters, candidate screenshots, chapter titles, proposed explanations,
  distinctive claims, and proposed destination of each candidate before
  component implementation and new capture production.
- **HUMAN JUDGMENT — CANDIDATE SELECTION:** Review the expanded candidate set
  on the actual responsive page and decide what remains in the introductory
  walkthrough, what moves to Plugins/Transparency/another deep dive, and what
  is deferred to documentation or a later page.
- **HUMAN JUDGMENT — UI WALKTHROUGH IN CONTEXT:** Review the implemented
  walkthrough on the actual responsive page, including navigation,
  legibility, copy, highlighted regions, and its transition into the
  remaining features.
- **HUMAN JUDGMENT — GETTING STARTED AND MOBILE:** Review the complete
  six-step workflow, tester/public availability language, mobile-access
  grouping, connection-method order, and trusted-network warning.
- **HUMAN JUDGMENT — RELEASE CUT:** Review which lower advanced sections are
  retained on the homepage and which are moved to documentation or deferred.
- **HUMAN JUDGMENT — FINAL PUBLISH-READY SITE:** Approve the complete local
  page, all proof assets, final copy, ordering, responsive behavior, and
  release-state presentation before source promotion and handoff to the
  waitlist task.
- **HUMAN — MANDATORY:** Final AWS deployment and production website
  publication remain governed by
  `tasks/20260930-homepage-getting-started-and-waitlist/020-aws-email-waitlist.md`.
- No account, credential, purchase, or production operation is expected during
  this task. If macOS/iOS native capture is blocked by an OS permission or
  locked device, report the exact human action required rather than
  substituting fabricated UI.

## Supporting facts and current boundary

- The accepted Option B layout currently renders four compact end-user
  highlights followed by full-width Plugins and Transparency sections.
- The current local preview has strong, reviewed Vibe, Plugin, and
  Transparency candidates. The current plugin highlight contains Session
  actions and Message actions; Transparency contains compiled Codex
  instructions and one illustrative costs/ChatGPT report.
- The current first four features still contain three release-blocking visual
  placeholders: Work from anywhere and two Sessions become workspaces images.
  Getting Started still contains Desktop-connection and mobile-connection
  placeholders.
- Playwright review measured the primary feature sequence at about 3,896 CSS
  pixels on a 1440-pixel desktop and 4,964 CSS pixels on a 390-pixel phone.
  Getting Started begins after roughly six and a half phone viewports.
  Unfinished or repetitive content therefore has a material cost on the
  mobile visitor path.
- The current full homepage is about 13,264 CSS pixels tall at 1440 pixels and
  18,405 CSS pixels at 390 pixels. The lower advanced material adds substantial
  length after the primary flow.
- The current lower page includes a detailed bridge deployment guide, a
  model-family matrix, provider-specific UI proof, a plugin-authoring prompt,
  and a Python SDK example. Some public copy still admits that product polish
  or API verification is pending, which cannot remain in a release candidate.
- The actual Desktop captures already demonstrate the required UI areas:
  active composer controls, session list, active conversation, session
  actions, message actions, response metadata, open-session tabs, and a
  application-owned local Watchlist. Session settings and the final selected
  connection/mobile states still need reviewed website capture states.
- The supplied Composer actions image is a strong opening candidate, but its
  public source should show an active request so immediate and soft
  cancellation are available and should retain enough conversation context to
  look like the complete product rather than an isolated menu.
- The supplied Message actions image demonstrates both normal history
  controls and workflow-specific plugin actions. The full Session actions menu
  is too broad for an unstructured introductory image and currently exposes a
  fallback `?` icon for **Collapse compacted messages**; a public candidate
  needs a genuine correction and a focused composition.
- The supplied session-list and Watchlist views are useful candidate sources,
  but final public fixtures need concise sanitized English titles and must
  avoid making raw UUIDs, debug timestamps, or unrelated internal work the
  visual focus.
- The current landing-page asset system supports responsive light/dark
  candidates, source fingerprints, native geometry, explicit preview
  overlays, and direct visual inspection. Candidate artifacts stay outside
  `public/` until human approval.
- Subtask `018` remains the implementation/evidence record for the accepted
  popup, icon, plugin, Transparency, Vibe, and capture-pipeline work. This
  task owns the newly approved publishable information architecture, UI tour,
  remaining proof, release copy, and final local acceptance.
- Subtask `020` owns the AWS email service, real form, consent/privacy
  behavior, production deployment, and final integrated publication.

## H1 candidate storyboard

### Verified behavior and ownership constraints

- **Cancellation:** hard cancel signals both provider work and cooperative
  foreground-tool cancellation. Soft cancel interrupts provider work but does
  not signal the active foreground tool; that tool may finish and persist its
  result before the loop stops, and later tool phases do not begin. Public copy
  should say "signals" rather than promise that an uncooperative process stops
  instantly.
- **Resend:** Resend is available only while no request is active. It sends a
  new request from the current session history without appending another user
  message. Do not publish "resend at any time."
- **Composer ownership:** Append, Append as, Resend, Cancel, and Soft cancel
  are application-owned Composer actions. Model, reasoning effort, web search,
  and similar compact controls are ordinary session config elements placed at
  the composer by the selected provider/extension/feature UI schema.
- **Message ownership:** Modify, Toggle markdown, and Copy message are
  application-owned message actions. Fork/Delete come from
  `session-actions-app`; Summarize/compaction/export actions come from their
  owning plugins. Message footers are plugin/provider UI-schema elements that
  read values from that message's metadata.
- **Session ownership:** Reload, Message limit, Switch agent, Settings,
  Plugins, and Snapshots are application-owned Session actions. Plugin actions
  are merged into the same extension surface and may be pinned beside the
  built-ins.
- **Agent and settings boundary:** Switch Agent opens a separate agent picker.
  Session settings is a separate per-session override window. Session plugins
  is another separate window that enables/disables providers, extensions,
  features, and tools for that session and can reset to agent defaults.
- **Agent-profile proof:** the production picker uses ordered descriptors with
  title/description and a safe provider/extension/feature/tool preview. It
  does not expose private plugin configuration values.
- **System-message proof:** the authored system message can remain a template
  with placeholders in stored session/config state. **Show compiled system
  message** is a non-mutating action that resolves the effective
  developer/system message without sending a model request.
- **Workspace state:** the standard Sessions panel supports application-
  plugin-provided title/subtitle/meta, session-list actions and filters.
  Request status is a lightweight current-runtime estimate with Idle, Not
  started, In progress, Completed, and Interrupted states; it is not durable
  request history.
- **Watchlist boundary:** Watchlist membership/order and local notes are
  application-owned per-device state. They are distinct from server-side
  pinned state and must not be described as a plugin-provided view.
- **Connections:** Desktop stores named connection records with focused/open/
  closed/error state. Mobile currently exposes Manual Address, Automatic
  Discovery, Bridge Service, and Cloud Agent Link. The homepage's simplified
  local discovery → address/port → bridge explanation is a visitor grouping,
  not a verbatim reproduction of every current method label.
- **Known visual defect:** OpenAI native compaction declares icon `rows-3` for
  **Collapse compacted messages**; Feather does not provide that icon, which
  explains the visible `?`. Correct it on `develop` before any public image
  containing that row.
- **Known presentation issue:** current Sessions/Home views deliberately show
  raw session IDs and technical metadata. If the selected public composition
  cannot truthfully avoid making those details visually dominant, changing or
  hiding them is a material product decision for a later checkpoint.

### Persistent introduction

Working title:

> **Familiar chat. More control at every level.**

Working body:

> Crystal Lattice starts with the AI chat interface you already know. Composer
> controls steer the next request, message actions operate from a point in
> history, session controls configure the whole task, and workspace views
> organize many sessions. The application provides stable extension surfaces,
> while plugins can contribute actions, settings, reports, and specialized
> controls.

Recommendation: retain this direction for candidate production. It establishes
the familiar category first and introduces the VS Code-like shell/extension
relationship without saying every visible element is a plugin.

### Chapter 1 — Compose

Working title:

> **Steer the next request.**

Working explanation:

> Start with the familiar composer. The selected profile can expose its model,
> reasoning, and web-search controls beside it. Append or resend when
> appropriate; cancel signals the provider and active tool to stop, while soft
> cancel lets a running tool finish and save its result before the loop stops.

Candidate **C01 — Active Composer actions**

- **Source:** production `ChatPane`, real Composer actions surface, and real
  provider/extension config controls.
- **Desktop composition:** retain the active conversation and session header;
  focus the bottom composer, pinned model/reasoning/search controls, and the
  genuine Composer actions popup. Capture an active request so both
  cancellation choices are enabled.
- **Phone composition:** retain one message above the composer, then place a
  readable popup excerpt below/over the composer while preserving its popup
  identity.
- **What it proves:** Crystal Lattice begins with a familiar chat surface;
  request lifecycle controls are immediately available; provider-specific
  controls can be placed at the composer.
- **Qualification:** built-in lifecycle actions and plugin/provider config
  controls share the surface but have different owners.
- **Prerequisites:** deterministic active-request fixture; selected model name
  must be maintained/sanitized and not imply official upstream-app identity.
- **Proposed destination:** default introductory walkthrough image.

### Chapter 2 — Messages

Working title:

> **Act from any message.**

Working explanation:

> Each response remains a point you can inspect and act from. Message footers
> keep provider-supplied usage or timing metadata with the response. Built-in
> actions cover editing, Markdown, and copying; plugins can add forking,
> deletion, summarization, compaction, sharing, or a workflow-specific action
> such as Send to Kindle.

Candidate **C02 — Message footer**

- **Source:** production message bubble plus genuine `message_footer`
  UI-schema elements.
- **Desktop composition:** show one useful assistant response with the footer
  readable in context; magnify only the real footer when necessary.
- **Phone composition:** show a shorter response and the complete footer below
  it, avoiding a floating strip detached from its message.
- **What it proves:** metadata is associated with the exact response and is
  selected by active provider/plugins.
- **Qualification:** metadata varies by provider and configuration; estimates
  are not invoices.
- **Proposed destination:** Messages chapter candidate; also useful as a
  Transparency supporting candidate.

Candidate **C03 — Message actions**

- **Source:** production Message actions menu combining built-in and genuine
  plugin rows.
- **Desktop composition:** preserve the selected assistant message and popup
  pointer; focus Modify, Copy, Fork here, Delete/Delete from here, one export,
  and Send to Kindle. OpenAI compaction may remain visible but is not called
  out in introductory copy.
- **Phone composition:** stack a recognizable message excerpt above the real
  popup and use only crop/magnification/omission markers already supported by
  the composition pipeline.
- **What it proves:** action scope begins at one message; the same surface can
  accept ordinary history controls and optional workflow actions.
- **Qualification:** Send to Kindle/export/compaction rows appear only when
  their plugins and required configuration are available.
- **Proposed destination:** primary or second Messages chapter image; the
  config-to-row version remains in Plugins.

### Chapter 3 — Session actions

Working title:

> **Control the whole session.**

Working explanation:

> Session actions affect the task as a whole. Switch the agent, open settings
> or plugins, inspect snapshots, edit the title or status, and pin the controls
> you use most. Additional plugins can contribute reports, history operations,
> exports, and other task-level actions.

Candidate **C04 — Focused Session actions**

- **Source:** production Session actions popup and header toolbar.
- **Desktop composition:** retain the session title/header and popup identity,
  but focus a coherent introductory subset: Switch agent, Settings, Plugins,
  Snapshots, title, status, and one range action. Preserve genuine omitted-row
  markers rather than fabricating a shorter menu.
- **Phone composition:** use the same focused subset in the mobile action
  surface with one-line wrap support.
- **What it proves:** session scope is distinct from message scope; built-ins
  and plugin actions share a pinnable surface.
- **Prerequisites:** fix the unsupported `rows-3` icon before using any image
  in which that row is visible; validate every selected row's owner.
- **Proposed destination:** introductory Session actions chapter. The full
  power-user menu belongs in documentation or a later deep dive.

### Chapter 4 — Session configuration

Working title:

> **Configure this session.**

Working explanation:

> An agent profile supplies the starting provider, instructions, tools, and
> features. Switch Agent changes that baseline. Session settings override
> provider-specific choices for this task, while Session plugins can enable,
> disable, or reset the providers, extensions, features, and tools used here.

Candidate **C05 — Agent picker**

- **Source:** production two-pane `AgentPickerWindow`.
- **Desktop composition:** use the approved smaller window; retain the ordered
  Crystal Lattice profile list and selected title/description, with the
  selected profile's safe tool/plugin preview readable on the right.
- **Phone composition:** use a deliberate compact composition rather than
  shrinking the entire landscape window; list above and selected details below
  is acceptable when sourced from the real UI.
- **What it proves:** profiles are named/ordered Crystal Lattice
  configurations and differ in more than model family.
- **Qualification:** label profiles as Codex-oriented, Claude-oriented, and so
  on; do not imply official upstream application sessions/accounts.
- **Proposed destination:** Session configuration chapter candidate.

Candidate **C06 — Provider-specific Session settings**

- **Source:** production `SessionSettingsWindow` backed by session config
  overrides.
- **Desktop composition:** show a focused set such as auth mode, model or
  processing tier/flex, reasoning, and another provider-specific option, with
  reset/default behavior visible where useful.
- **Phone composition:** use the production modal and keep only enough rows to
  explain per-session overrides without presenting the entire schema.
- **What it proves:** the active provider/plugins define ordinary settings,
  and selected values can be overridden for one session.
- **Qualification:** available settings depend on the profile/provider.
- **Prerequisites:** deterministic fixture with truthful enabled/disabled and
  default/overridden state.
- **Proposed destination:** Session configuration chapter candidate; detailed
  provider matrices remain documentation.

Candidate **C07 — Session plugins and tools**

- **Source:** production `SessionPluginsWindow`/modal and genuine
  `SessionPluginEntry` categories.
- **Desktop composition:** prioritize Providers, Extensions, Features, and
  Tools; show clear enabled/disabled state and one session override while
  retaining Reset to defaults.
- **Phone composition:** show the same categories in the production modal with
  the highlighted tools visible without artificial duplicate rows.
- **What it proves:** a session can override the enabled plugin set and reset
  to the agent baseline.
- **Qualification:** the application owns the window; plugin entries and their
  state come from the backend. Toggling providers/tools may materially change
  session behavior.
- **Proposed destination:** Session configuration chapter candidate and
  possible Plugins deep-dive support.

### Chapter 5 — Workspace

Working title:

> **Keep many sessions moving.**

Working explanation:

> Search and filter sessions, preview or open them, and see the title, status,
> pin, and current request state that help you return to the right task.
> Desktop and mobile also keep a local Watchlist and recent-session view across
> saved connections.

Candidate **C10 — Standard session list and filters**

- **Source:** production `SessionsPanel`, application-plugin-provided
  presentation fields/actions/filters, and real request-status indicator.
- **Desktop composition:** show concise sanitized titles/subtitles, mixed
  To do/In progress/Done values, pinned/unpinned state, search, one active
  filter, and Open/Preview controls. Keep one selected row tied to the active
  conversation.
- **Phone composition:** show two or three rows with the same information
  hierarchy and a visible filter affordance.
- **What it proves:** sessions are organized work items rather than anonymous
  transcripts; filters and controls are extensible surfaces.
- **Qualification:** title/status/pin may be supplied by their application
  plugins; request status is a transient runtime estimate.
- **Prerequisites:** resolve whether raw IDs/technical timestamps can be
  de-emphasized truthfully through product presentation or composition.
- **Proposed destination:** primary Workspace chapter image.

Candidate **C11 — Open-session request status**

- **Source:** production session-tab strip and shared
  `SessionRequestStatusIndicator`.
- **Composition:** use the tab strip as an inset attached to C10 or C12, not a
  standalone hero image. Show at least one In progress and one Completed state
  and keep titles legible enough to connect status to work.
- **What it proves:** current work remains visible while moving between open
  sessions.
- **Qualification:** status is lightweight/transient and may be unavailable
  for an offline or unsupported connection.
- **Proposed destination:** supporting inset in Workspace.

Candidate **C12 — Local Watchlist and Recent Sessions**

- **Source:** production Home view and per-device Watchlist/Recent state.
- **Desktop composition:** use four concise sanitized Watchlist cards followed
  by enough Recent Sessions context to show the relationship. Request status,
  local note, connection, and relative time may appear where legible.
- **Phone composition:** use the production two-column Watchlist and a short
  recent timeline.
- **What it proves:** users can maintain a local attention list and recent
  history across saved connections.
- **Qualification:** Watchlist membership/order and notes are local to the
  device; Watchlist is not server pinning and is not currently plugin-owned.
- **Prerequisites:** sanitize titles/content and decide whether public proof
  needs a product option to de-emphasize session IDs.
- **Proposed destination:** optional second Workspace image or later
  multi-session deep dive, selected at H2.

### Deep-dive and setup candidates

Candidate **C08 — Authored System message with placeholders**

- **Source:** real stored/configured System message rendered as the first
  System-role message.
- **Composition:** show a concise understandable template with visible
  placeholders and enough conversation context to establish that it is part
  of the session.
- **What it proves:** authored instructions remain visible and editable in
  their template form.
- **Proposed destination:** Transparency, not the introductory walkthrough.

Candidate **C09 — Compiled System message**

- **Source:** real non-mutating **Show compiled system message** action/display
  using the beginning of the maintained Codex default selected for website
  proof.
- **Composition:** pair with C08 when possible; preserve real action/display
  chrome.
- **What it proves:** visitors can inspect the effective instructions after
  placeholders/defaults are resolved without making a model request.
- **Proposed destination:** Transparency.

Candidate **C13 — Connections and mobile connection methods**

- **Source:** production Desktop Connections panel and production mobile
  connection-method UI.
- **Composition:** Desktop proof focuses saved/focused/open state; mobile proof
  groups local discovery, address/port, and bridge for visitor explanation
  while retaining truthful current labels where shown.
- **What it proves:** clients select where a Crystal Lattice workspace is
  running.
- **Qualification:** public/tester/invite bridge and mobile availability must
  come from maintained release state.
- **Proposed destination:** Getting Started steps 4 and 6, not the top
  walkthrough.

Candidate **C14 — Matching Desktop/mobile session**

- **Source:** production Desktop and mobile consumers over one deterministic
  fixture.
- **Composition:** same title, subtitle, status, agent, latest prompt, and
  answer on both devices.
- **What it proves:** continuity of one runtime session across clients.
- **Qualification:** clearly state current mobile distribution status.
- **Proposed destination:** **Work from anywhere**.

### H1 recommendation for candidate production

Approve production of all fourteen candidates, but use these as the initial
placement hypotheses:

| Chapter/section | Primary candidate | Alternatives to compare at H2 |
| --- | --- | --- |
| Compose | C01 | None unless the popup is too dense |
| Messages | C03 with C02 visible in context | Separate C02/C03 slides |
| Session actions | C04 | Move the full menu to documentation |
| Session configuration | C05 | Add C06 and/or C07 as second/third images |
| Workspace | C10 with C11 inset | C12 as second image or later deep dive |
| Transparency | C08 + C09 | Keep existing usage/cost report as another image |
| Getting Started | C13 | Separate Desktop/mobile connection images |
| Work from anywhere | C14 | None |

H1 does not choose the final image count. H2 makes that decision after the
candidates appear in the actual responsive page.

### Product/capture prerequisites for H2

1. Add a deterministic active-request capture state for C01.
2. Correct the unsupported `rows-3` icon on `develop` if C04 can expose it.
3. Add sanitized unified session fixtures used by conversation, tabs, list,
   Watchlist, connection, and cross-device candidates.
4. Decide during candidate production whether raw session IDs need an approved
   product presentation change; do not fabricate their removal.
5. Add deterministic provider-specific Session settings and per-session plugin
   states for C06/C07.
6. Add the authored-placeholder source paired with the maintained compiled
   Codex proof for C08/C09.
7. Add deterministic mixed request states for C10–C12.
8. Keep candidate artifacts outside `public/` until H2 selection.

## Execution plan

Status: Approved

The first public version will teach the product through its UI before asking
the visitor to install it. The walkthrough is a single full-width section
after the hero. It starts from the AI chat interaction visitors already know
and expands bottom-up through the control scopes around it.

The working section direction is:

> **Familiar chat. More control at every level.**
>
> Crystal Lattice starts with the AI chat interface you already know. Composer
> controls steer the next request, message actions operate from a point in
> history, session controls configure the whole task, and workspace views
> organize many sessions. The application provides stable extension surfaces,
> while plugins can contribute actions, settings, reports, and specialized
> views.

This wording is a review baseline, not pre-approved final public copy. The
storyboard checkpoint owns final phrasing.

The walkthrough uses a split presentation on desktop: explanation on one side
and the product image on the other. Phones stack explanation above the image.
The chapter controls remain visible and named. The section does not autoplay.
The current feature-image component may be extended when it can preserve its
existing consumers cleanly; a dedicated walkthrough component is acceptable
if the teaching layout and accessibility needs would otherwise distort the
ordinary image strips.

### Bottom-up walkthrough chapters

| Chapter | Visitor question | Candidate proof | Distinction introduced |
| --- | --- | --- | --- |
| **Compose** | How do I steer the next request? | Active conversation with the composer, provider controls, and Composer actions | Immediate/soft cancellation, resend/append, model, reasoning, and search controls live around a familiar composer; the extension surface can receive provider/plugin contributions |
| **Messages** | What can I inspect or do from one response? | Genuine message footer plus Message actions at one assistant message | Metadata stays attached to the response; actions such as fork/delete/export operate from an exact point and optional plugins can add workflows such as Send to Kindle |
| **Session actions** | What affects the whole task? | Session header with a focused genuine subset of Session actions | Session actions have whole-task scope and remain distinct from message actions; plugins may contribute or replace entries |
| **Session settings** | How is this session's agent configured? | Agent/provider settings and per-session Plugins/Tools views | A profile is more than a model selector, and each session can carry its own provider options, plugins, and tools |
| **Workspace** | How do I organize and monitor many tasks? | Standard session list/filter/status view, open-session status inset, and optional local Watchlist candidate | Sessions have titles, states, pins, filters, and visible request progress; Desktop and mobile also maintain a local per-device Watchlist and recent-session workspace |

The Compose chapter is the default and must be self-sufficient enough that a
visitor who does not advance still recognizes a complete AI-agent product.
Its image retains conversation context around the magnified composer controls.
The later chapters deepen the hierarchy rather than supplying a missing
category explanation.

All candidates use one deterministic fixture. Screens retain application
context while outlining, dimming, or magnifying the current area. Avoid three
consecutive full-height popups: alternate contextual conversation, focused
menu callouts, settings windows, and workspace views. Configuration-to-control
connector lines remain exclusive to the later Plugins proof.

Connections are not a primary introductory chapter in this bottom-up version.
The tour may briefly state that the focused connection determines which
workspace's sessions are shown. Getting Started owns the full explanation of
local discovery, address/port, and bridge access.

### Candidate pool and selection

Produce enough truthful candidate sources to compare the teaching sequence
before reducing the public page:

1. active conversation with Composer actions;
2. message footer with provider-supplied metadata;
3. Message actions with fork/delete/export and one optional workflow action;
4. focused Session actions;
5. agent picker with ordered profiles and safe plugin/tool preview;
6. Session settings with provider-specific options;
7. Session plugins with per-session Plugins and Tools;
8. authored System message with placeholders;
9. compiled System message;
10. standard session list with search/filter/status;
11. open-session tabs with live request indicators;
12. local Watchlist and Recent Sessions;
13. Connections panel or mobile connection method view;
14. matching Desktop/mobile session.

Candidate production does not pre-approve all fourteen for the homepage. Bind
the viable candidates temporarily to the actual local page, inspect them at
desktop and phone widths, then classify each as:

- introductory walkthrough;
- Plugins/Transparency/another feature deep dive;
- Getting Started;
- documentation or later-page material;
- rejected after contextual review.

### Resulting homepage sequence

1. Concise hero and primary action.
2. Full-width UI walkthrough.
3. Compact row: **Vibe code—or vibe anything** and **Work from anywhere**.
4. Full-width **Replace the parts you disagree with**.
5. Full-width **Transparency by design**.
6. Six-step Getting Started.
7. Only verified, non-duplicative advanced material selected at the release
   cut checkpoint.
8. Final CTA.

The former model-family and durable-session compact items are not simply
deleted. Their value, copy alternatives, captures, and proof requirements are
incorporated into Session settings and Workspace, with related candidates
retained in the durable decision record.

### Remaining feature and Getting Started work

**Vibe code—or vibe anything** keeps the accepted System → User → initial
reasoning image. Review its final caption in the new page rhythm.

**Work from anywhere** receives one real Desktop/phone composition over the
same session fixture. It proves continuity rather than connection setup. The
caption states current public/tester/invite availability.

**Plugins** and **Transparency** retain their accepted proof concepts. Plugins
may deepen the Composer/Message/Session extension surfaces by showing how
configuration contributes actual controls. Transparency owns the deeper
System-message story: authored placeholders in the visible System role
message, the real **Show compiled system message** result, provider-supplied
message metadata, and the reviewed illustrative usage/cost report. Rewrite
comments to explain what each image proves instead of repeating generic
“plugin-driven and easy to adjust” wording. Keep sample/provider
qualifications and reviewed assets.

The standard session list is the primary Workspace proof. Evaluate the local
per-device Watchlist as an optional second Workspace image or later
multi-session deep dive only after the standard navigation model is
understandable. It does not replace or modify the separate server-side pinned
state. An open-session tab strip is an inset for request/status visibility
rather than a standalone section.

Getting Started retains all six steps. The first four are the currently usable
CLI/Desktop path. Steps 5–6 form a clear Mobile access group:

1. install CLI;
2. start the workspace locally;
3. download Desktop;
4. connect Desktop with port `9000`;
5. get the mobile app through the current public or tester channel;
6. connect by local discovery, address and port, or bridge.

The local Desktop command does not need LAN exposure. Mobile setup introduces
Bonjour separately and explains trusted-network reachability. The mobile
connection UI presents Local discovery first, Address and port second, and
Bridge third. Bridge deployment details move to documentation or an advanced
link unless the release-cut checkpoint finds a concise verified homepage role.

The Desktop connection proof is a compact real connection-editor/result state,
not another large feature frame. The mobile proof uses the actual connection
method or Connections UI and current availability state.

### Release-content audit

Inspect every section after Getting Started. Retain content only when it has a
clear audience, verified public claims/examples, and a role not already
fulfilled by the walkthrough or feature proof. At minimum:

- remove internal “needs polish,” “final webpage should verify,” task, and
  review-state wording;
- do not publish the knowingly unverified Python SDK example;
- move detailed AWS bridge deployment to documentation unless a concise
  homepage version is specifically accepted;
- avoid repeating the profile list through both a chip strip and a large
  matrix without a distinct compatibility-evaluation purpose;
- preserve useful provider-native proof only when it adds information beyond
  the main Transparency section;
- provide clear advanced-user routes to profiles/compatibility, plugins,
  remote access, SDK docs, and GitHub.

### Ordered execution

1. Preserve the current page, assets, screenshots, tests, and approved decision
   state as the comparison baseline.
2. Verify public behavior claims for Composer cancellation/resend, message
   footers, action scope, provider options, session plugins, request status,
   and connection state. Record any product defect, invalid icon, debug-first
   presentation, or capture limitation before designing around it.
3. Prepare the five-chapter storyboard and fourteen-item candidate pool with
   exact visitor question, draft copy, source UI state, differentiating
   statement, proposed destination, desktop composition, phone composition,
   and capture/product dependencies.
4. Stop at the candidate-storyboard checkpoint for human judgment.
5. Produce or refresh genuine Desktop/mobile sources through the maintained
   public/native capture boundaries. Put genuine product improvements on
   `develop`, verify them there, and reconcile only confirmed website-used
   changes onto `main`.
6. Compose the candidate walkthrough, deep-dive, Workspace/Watchlist,
   Work-from-anywhere, Desktop-connection, and mobile-connection assets.
7. Bind the viable candidates temporarily to the actual local homepage and
   inspect every candidate in context with Playwright plus direct
   `view_image` review.
8. Stop at the candidate-selection checkpoint. Record which candidates belong
   in the introduction, deep dives, Getting Started, documentation, or later
   revisions.
9. Implement the selected responsive accessible walkthrough and revised
   homepage information architecture. Apply final visitor copy and
   compositions only for the accepted candidates.
10. Stop at the walkthrough-in-context checkpoint.
11. Refine remaining feature order, captions, availability, compatibility,
    and proof based on the accepted walkthrough.
12. Revise Getting Started, the Mobile access grouping, local/LAN security
    language, and current release states.
13. Stop at the Getting Started/mobile checkpoint.
14. Apply the lower-page release cut and verify all retained examples and
    links.
15. Stop at the release-cut checkpoint.
16. Complete responsive, accessibility, source-freshness, content, download,
    security-copy, and full-page verification.
17. Stop at the final publish-ready checkpoint.
18. After human acceptance, promote only approved visual sources and update
    maintained public bindings. Do not push or publish.
19. Hand the approved local website to subtask `020` for the real waitlist,
    privacy integration, final integrated review, and explicitly approved
    production publication.

### Implementation decisions and open questions

- **Decision:** the introductory walkthrough teaches the product UI; it does
  not replace Getting Started or begin with commands, ports, project
  directories, server binding, or installation architecture.
- **Decision:** the walkthrough uses a bottom-up scope hierarchy: Compose →
  Messages → Session actions → Session settings → Workspace.
- **Decision:** the first visual begins with a complete familiar conversation
  and composer context, not an isolated menu or runtime/startup explanation.
- **Decision:** Connections is briefly named as the source of the focused
  workspace but receives its full local-discovery/address/bridge explanation
  in Getting Started.
- **Decision:** the walkthrough explains ordinary UI role before
  differentiation and introduces plugin/provider terminology only after the
  visible behavior is understandable.
- **Decision:** model-family breadth and durable-session value move into the
  walkthrough instead of remaining separate compact advertisements.
- **Decision:** the same fixture and visual coordinate system carry the
  visitor through the walkthrough.
- **Decision:** labeled chapter controls are required; dots may remain only as a
  secondary position indicator.
- **Decision:** Session actions and Message actions retain distinct scopes in
  the explanation.
- **Decision:** the introductory Session actions proof presents a focused
  genuine subset; the exhaustive menu and model-specific history operations
  belong in a deep dive or documentation.
- **Decision:** Session settings is a first-class introductory chapter and
  covers agent/profile, provider options, per-session plugins, and tools.
- **Decision:** message footers explain provider-supplied transparency at the
  response level; the later Transparency section continues to own compiled
  instructions, authored placeholders, and custom reporting.
- **Decision:** the standard session list is introduced before the optional
  local per-device Watchlist; Watchlist membership is distinct from
  server-side pinned state, and request status may use the open-session tab
  strip as a supporting inset.
- **Decision:** build and review a larger candidate pool on the actual page
  before selecting the final introduction. Candidate production does not
  imply public inclusion.
- **Decision:** use the VS Code analogy only to explain the relationship
  between an application-owned shell/extension surfaces and plugin
  contributions; do not claim every visible element is a plugin.
- **Decision:** mobile remains in the six-step workflow, with tester/invite/
  coming-soon state explicit and its connection methods grouped separately.
- **Decision:** local discovery precedes address/port and bridge in the mobile
  explanation.
- **Decision:** the basic Desktop path stays local; LAN reachability is
  introduced intentionally with a trusted-network qualification.
- **Decision:** the first publishable version may be concise and may defer
  advanced material, but it may not contain visible placeholders, internal
  planning language, or knowingly unverified examples.
- **Open human judgment at storyboard checkpoint:** exact section title,
  chapter titles, final public descriptions, and the proposed destination of
  every candidate.
- **Open human judgment at candidate-selection checkpoint:** which candidates
  remain in the top walkthrough, move to Plugins/Transparency/another deep
  dive, move to Getting Started, or are deferred to documentation/later work.
- **Open human judgment at release-cut checkpoint:** which verified lower-page
  advanced sections remain on the first homepage versus moving to
  documentation or later revisions.

### Documentation

- Append the approved bottom-up UI-teaching sequence,
  role-before-difference theory, chapter/candidate alternatives, final copy,
  candidate classifications, visual mappings, release cuts, and rationale to
  `landing_page/docs/development/homepage-positioning-and-visual-decisions.md`.
- Update `landing_page/docs/development/content-system.md` for the walkthrough
  content contract, labeled navigation, responsive behavior, candidate
  preview, and current/future availability fields.
- Update `landing_page/docs/visual-assets.md` and the owning Desktop/mobile
  capture guides for each new source, fixture, crop, composition, manifest,
  and freshness trigger.
- Preserve the current separate feature concepts and alternate screenshot
  variants as durable comparison material rather than deleting the rationale.
- Record the final release cut and every removed/deferred section's destination
  or reason.
- Keep public copy free of task/checkpoint/provenance language.

### Task checklist

- [x] **HUMAN JUDGMENT:** Approve the UI-led walkthrough direction and the
      overall publishable-page plan.
- [x] **HUMAN JUDGMENT:** Approve the bottom-up Compose → Messages → Session
      actions → Session settings → Workspace direction and candidate-first
      selection process.
- [x] **AGENT:** Preserve the current baseline and verify the exact public
      behavior/ownership claims represented by the candidates.
- [x] **AGENT:** Prepare the detailed five-chapter storyboard and expanded
      candidate pool.
- [x] **HUMAN JUDGMENT — CHECKPOINT 1:** Approve the storyboard, exact teaching
      order, proposed claims, candidate responsibilities, and proposed
      destinations.
- [x] **AGENT:** Capture and compose the viable candidates through real product
      boundaries and bind them temporarily to the actual local homepage.
- [x] **HUMAN JUDGMENT — CHECKPOINT 2:** Select the candidates for the
      introduction, deep dives, Getting Started, documentation, and later
      work after responsive in-page review.
- [x] **AGENT:** Implement the selected responsive accessible walkthrough and
      revised homepage information architecture.
- [ ] **HUMAN JUDGMENT — CHECKPOINT 3:** Review the complete selected
      walkthrough in page context at desktop and phone widths.
- [ ] **AGENT:** Finalize remaining feature order, captions, proof, and
      availability distinctions.
- [ ] **AGENT:** Implement and verify the six-step Getting Started and grouped
      Mobile access treatment.
- [ ] **HUMAN JUDGMENT — CHECKPOINT 4:** Review Getting Started, mobile
      availability, connection concepts, and trusted-network language.
- [ ] **AGENT:** Apply the verified lower-page release cut and advanced-user
      routes.
- [ ] **HUMAN JUDGMENT — CHECKPOINT 5:** Approve retained, moved, and deferred
      advanced content.
- [ ] **AGENT:** Complete all release-candidate verification and documentation.
- [ ] **HUMAN JUDGMENT — CHECKPOINT 6:** Approve the complete local
      publish-ready website and candidate source promotion.
- [ ] **AGENT:** Promote approved sources and hand the local website to
      subtask `020`; do not push or publish.

### Requirement verification

- Visitor-understanding boundary: moderated human review starts at the hero
  with no prior product explanation. The reviewer must correctly identify the
  product as an extensible agent-session workspace and explain composer
  controls, message footers/actions, session actions/settings, agent profiles,
  and workspace/session organization after the walkthrough without using
  Getting Started.
- Walkthrough UI boundary: each selected chapter uses source-fingerprinted production
  components/native captures with one consistent fixture. Inspection maps
  every described control/metadata field to the genuine source; a duplicate
  mock menu or repainted data panel is insufficient.
- Candidate-selection boundary: the actual responsive homepage temporarily
  renders every viable candidate. Human review records its final destination
  and confirms that rejected/deferred candidates are removed from the public
  sequence rather than remaining as hidden or unfinished content.
- Differentiation boundary: copy inspection verifies that each chapter explains
  role first, distinction second, distinguishes Crystal Lattice profiles from
  official upstream products, distinguishes shell/extension surfaces from
  plugin contributions, and does not imply uniform provider metadata.
- Navigation/accessibility boundary: browser tests cover descriptive chapter
  controls, arrow keys, pointer, swipe/scroll, focus, current-state
  announcement, reduced motion, resize persistence, theme switching, and
  no-autoplay behavior.
- Responsive visual boundary: actual page screenshots at 1440, 1024, 768,
  390, and 320 CSS pixels in light/dark themes are opened with `view_image`.
  Text, highlighted regions, popup ownership, and UI identity must remain
  understandable at displayed size.
- Feature boundary: content/browser tests prove the old model-family/session
  compact duplicates are absent, their approved values appear in the
  walkthrough, and Vibe, Work from anywhere, Plugins, and Transparency remain
  in the accepted order with current proof.
- Continuity boundary: Desktop and mobile sources show the same session
  identity, agent, status, prompt, and answer through production consumers.
- Getting Started boundary: real public commands/download metadata and actual
  connection UI prove all six ordered steps. The Desktop path uses local
  binding; Bonjour/LAN wording identifies network reachability and trusted
  network use; mobile methods appear in discovery/address/bridge order.
- Release-safety boundary: built HTML, content-source scans, and visual review
  find no placeholders, review labels, internal progress text, fake form,
  unverified API example, stale availability state, broken link, or hidden
  unsupported platform claim.
- Release-cut boundary: every retained lower section has verified claims,
  examples, and audience purpose; removed material has a documented
  destination or deferral rationale.
- Handoff boundary: approved visual sources and public bindings are ready
  locally, while Git state and deployment evidence confirm no production push
  or publication occurred in this task.

### Additional implementation verification

- Run content, asset-catalog, source-freshness, accessibility, normal-build,
  explicit-preview, and responsive Playwright checks appropriate to every
  changed boundary.
- Verify active release/download links from maintained metadata and confirm
  coming-soon/tester/invite states cannot be activated as public store links.
- Verify no private credentials, personal sessions, account journals, real
  costs, email data, or operator-specific connection details enter captures,
  manifests, browser bundles, or public files.
- Preserve unrelated worktree changes and stage only this task's files in each
  approved commit.

## Implementation Notes

- 2026-10-11: Execution began at H1 only. No capture production, walkthrough
  component implementation, public asset promotion, product mutation, push,
  or publication occurred.
- 2026-10-11: Source inspection verified the bottom-up control boundaries:
  application-owned Composer actions coexist with plugin/provider rich config;
  built-in Message/Session actions coexist with genuine plugin actions;
  Session settings, Switch Agent, and Session plugins are separate production
  surfaces.
- 2026-10-11: Soft-cancel behavior is verified by source and five focused core
  tests: provider work is interrupted, an active foreground tool is allowed to
  finish and persist its result, later tool phases do not begin, and hard
  cancel can escalate the tool interruption.
- 2026-10-11: Resend is disabled while a request is active and re-runs the
  current session without appending another user message. Public copy must not
  say "resend at any time."
- 2026-10-11: Corrected the planning assumption that Watchlist is
  plugin-provided. Current Desktop/mobile Watchlist membership/order and local
  notes are per-device application state and remain distinct from server-side
  pinned state.
- 2026-10-11: Identified the fallback `?` source:
  `openai_responses_native_compaction_extension.py` declares unsupported
  Feather icon `rows-3` for **Collapse compacted messages**.
- 2026-10-11: Added the complete fourteen-candidate H1 storyboard, exact
  working copy, source/composition boundaries, qualifications, proposed
  destinations, and H2 prerequisites.
- 2026-10-11: Focused verification passed: 5 core soft-cancel tests; 16
  frontend SDK chat/session-plugin/status tests; 34 system-message feature
  tests; 14 Desktop rich-session/settings/sessions tests; 21 mobile
  rich-session/settings/list-action tests; 10 shared action/status tests; and
  the focused session-actions UI-element test.
- 2026-10-11: The full session-actions plugin suite is not a passing
  verification boundary: 10 tests passed and 2 unrelated copy/delete-session
  tests failed. The message-export suite did not collect because optional
  `xhtml2pdf` is not installed. H1 relies on inspected genuine UI definitions
  for those rows and does not misreport either suite as passing.
- 2026-10-11: The `develop` worktree contains unrelated active work. H1 kept it
  read-only and found no uncommitted differences in the audited Composer,
  Session settings/plugins, native compaction, or mobile chat source files.
- 2026-10-13: The user approved H1 and authorized H2. The candidate process
  remained opt-in through `CRYSTAL_WALKTHROUGH_CANDIDATE_PREVIEW=1`; normal
  content tests and the normal production build continue to render the
  existing public page without the candidate walkthrough or review assets.
- 2026-10-13: Product/capture prerequisites were implemented but remain
  uncommitted on `develop` alongside pre-existing unrelated work. The OpenAI
  compaction action now uses valid stateful Feather icons
  (`minimize-2`/`maximize-2`), and the maintained mobile website harness adds
  genuine production states for an active composer, authored System template,
  request-status session list, local Watchlist/Home view, and connection
  methods. No `develop` changes have been reconciled to `main` or committed.
- 2026-10-13: The final selective Detox capture completed successfully in
  light and dark themes. Focused verification passed: mobile TypeScript;
  6 mobile harness tests; 28 OpenAI native-compaction tests; the generated
  runtime-UI fixture test; 25 landing visual-asset tests; 8 normal homepage
  content/download tests; normal Astro build; and repository diff checks.
- 2026-10-13: The actual homepage now has an opt-in H2 review binding for all
  fourteen candidates. C01–C07 and C10–C12 appear in the five walkthrough
  chapters; C08–C09 remain in Transparency; C13 appears in the mobile
  connection step; and C14 appears in Work from anywhere. Candidate files
  remain ignored review artifacts outside `public/`, and a missing source
  deliberately fails the preview build.
- 2026-10-13: Candidate-page Playwright verification passed 15 tests. It
  covers 1440, 1024, 768, 390, and 320 CSS pixels in light/dark themes, no
  horizontal overflow, ten walkthrough cards, removal of the two superseded
  compact highlights in preview mode, independent image-strip navigation,
  and focused in-page screenshots of every multi-image candidate at 1440 and
  390 pixels.
- 2026-10-13: Visual review found that C03 is the strongest current
  message-action explanation, especially in its purpose-built phone
  composition. C09 and the plugin-driven costs/ChatGPT report remain strong
  Transparency candidates. C06 and C07 accurately show provider and plugin
  ownership but are small at phone page size, so their introductory role
  remains a human selection rather than an implementation assumption.
- 2026-10-13: C01 and C04 preserve genuine popup identity but leave excessive
  empty canvas on desktop and make row text small on phone; C04 also remains
  broader than the planned focused introductory subset. C02 proves genuine
  response metadata, but its text is too small in the current phone frame.
  C05 is clear on desktop and effectively unreadable on phone without a
  responsive crop or alternate composition.
- 2026-10-13: Workspace candidates expose unresolved publication issues.
  C10 has an iOS safe-area collision between the clock and workspace title.
  C11 places durable plugin status beside transient request status in a way
  that can look contradictory without stronger labeling. C12 repeats the
  safe-area collision and is information-dense; the local Watchlist remains
  optional supporting proof rather than a default recommendation.
- 2026-10-13: C13 is a clean production connection-method capture, but the
  actual UI orders Manual Address before Automatic Discovery while the
  approved visitor explanation starts with discovery. The current Getting
  Started layout also retains command-heavy mobile connection text and needs
  H4 restructuring. C14 truthfully shows one session across Desktop/mobile,
  but the current composition has too much empty canvas and is too small on
  phone.
- 2026-10-13: H2 agent work is complete. Execution is paused at Human
  Checkpoint 2 so candidate destinations and the required responsive
  compositions can be selected before the final walkthrough component is
  implemented.
- 2026-10-13: The user approved the H2 content and order and accepted the
  selected direction subject to image-specific responsive treatment. Candidate
  IDs such as C01/C05, candidate/review labels, provenance language, and review
  statuses are internal-only and must be absent from final public copy and
  accessibility text.
- 2026-10-13: Mobile readability is a per-asset acceptance condition, not a
  single global scaling rule. Each selected proof must use the smallest
  truthful intervention that keeps its important text readable at rendered
  phone width: a tighter crop, a smaller Desktop capture window, a shorter
  phone/device viewport, a responsive alternate composition, a focused inset,
  or a genuine magnifier treatment like the accepted usage/cost proof.
- 2026-10-13: H3 will implement the five-chapter selected walkthrough and
  prepare the responsive proof variants. The current expanded stacked
  candidate page is not the final component. H3 stops at Checkpoint 3 for
  desktop/phone review before features and Getting Started are finalized in
  H4.
- 2026-10-13: Getting Started media ownership is now explicit. Step 1 uses the
  maintained interactive CLI installation chooser; Step 2 uses the workspace
  startup command; Step 3 uses real platform/download controls and the
  maintained macOS release link; Step 4 still requires a compact real Desktop
  connection-editor proof with port `9000` and a recognizable connected
  outcome; Step 5 uses Apple/Android availability controls and later receives
  the real waitlist form from subtask `020`; Step 6 uses the genuine mobile
  connection-method UI with responsive treatment and discovery → address/port
  fallback → bridge visitor explanation. No step may retain a planned-visual
  placeholder in the publish candidate.
- 2026-10-13: H3 adds a dedicated `productWalkthrough` section rather than
  retaining the expanded H2 feature-card stack. It presents one active chapter
  at a time in the approved Compose → Messages → Session actions → Session
  settings → Workspace order, with visible chapter names, keyboard
  Arrow/Home/End navigation, labeled previous/next controls, visual swipe,
  no autoplay, reduced-motion-safe behavior, and sequential no-JavaScript
  fallback.
- 2026-10-13: Desktop uses a stable two-column copy/image stage. Mobile shows
  the chapter title and ordinary role first, then the responsive image, then
  the Crystal Lattice distinction. The horizontally scrollable named chapter
  controls do not trap vertical scrolling. Direct section navigation reserves
  space for the sticky site header.
- 2026-10-13: The final capture fixture is coherent. Compose, Messages,
  Session actions, and provider/plugin settings use the same Starlette/Codex
  session. The Workspace list begins with the same titled task and uses a
  descriptive `starlette-compatibility` slug rather than a raw UUID. Durable
  task status and transient request state are aligned and labeled separately.
- 2026-10-13: The maintained mobile capture harness now includes the terminal
  Starlette Message actions state and aligned Workspace state. TypeScript and
  7 focused harness tests pass; selective native light/dark Detox captures for
  Message actions and Workspace pass through the production UI.
- 2026-10-13: `walkthrough-final-composition.mjs` creates independently
  composed light/dark wide (1800 × 1013) and compact (1000 × 1250) assets.
  Compose, Messages, and Session actions use genuine popup/context
  magnification; Session settings combines the agent-profile source with
  focused provider/plugin controls; Workspace crops out the simulator
  safe-area collision and enlarges readable rows. Public compositions contain
  no candidate IDs, review language, or raw session UUIDs.
- 2026-10-13: Final in-page inspection opened every chapter at 1440, 1024,
  768, 390, and 320 CSS pixels in light and dark themes. The compact
  compositions keep the relevant controls readable at rendered phone size;
  the first visual appears before the distinction paragraph on phone. The H3
  page is about 12,988 pixels tall at 1440 and 17,895 pixels at 390, compared
  with the expanded H2 review page's roughly 17,622 and 21,285 pixels.
- 2026-10-13: Verification passed: 12 final-walkthrough Playwright tests,
  15 retained H2-candidate Playwright tests, 8 normal homepage content tests,
  25 landing visual-asset tests, normal and explicit-preview Astro builds,
  mobile TypeScript, 7 mobile harness tests, 28 native-compaction tests, the
  generated runtime-UI fixture test, selective native captures, and diff
  checks.
- 2026-10-13: H3 remains opt-in through
  `CRYSTAL_WALKTHROUGH_FINAL_PREVIEW=1`; its review assets remain ignored and
  outside `public/`. Normal homepage content/build output is unchanged. No
  source promotion, commit, push, deployment, or publication occurred.
- 2026-10-13: H3 agent work is complete and execution is paused at Human
  Checkpoint 3. H4 must not begin until the user approves the walkthrough's
  clarity, legibility, navigation, responsive behavior, and transition into
  the remaining feature sections.
