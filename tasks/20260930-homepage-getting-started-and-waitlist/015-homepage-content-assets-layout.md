# Finalize Homepage Copy, Proof Assets, Ordering, And Layout

Parent Task:
`tasks/20260930-homepage-getting-started-and-waitlist/000-main.md`

Depends On:
`tasks/20260930-homepage-getting-started-and-waitlist/010-homepage-structure-prototype.md`

Start from the approved structural prototype and finalize the homepage's public
copy, sixth highlight, proof assets, highlight ordering, responsive visual
composition, and getting-started presentation through contextual and visual
human review. This subtask still leaves the actual waitlist form to subtask
`020`.

## Requirements checklist

- [ ] The structural prototype is reviewed in context before copy, assets,
      ordering, or visual layout are treated as approved.
- [ ] The hero's final public title, short description, and actions are
      approved in the rendered page.
- [ ] The six-card visual highlights section has human-approved copy,
      ordering, proof, and responsive composition.
- [ ] Five highlight themes are implemented as approved: one workspace for
      model-family-oriented agents; replaceable plugin surfaces; transparent,
      open-source and inspectable operation; work from anywhere; and
      adaptability to workflows beyond development.
- [ ] The sixth highlight presents durable session workspaces with approved
      copy and proof.
- [ ] The general-purpose-agent highlight uses **Vibe code—or vibe anything.**
      as its selected working title unless contextual review explicitly
      approves another preserved variation.
- [ ] Getting Started retains exactly six ordered steps—install CLI, start
      workspace, download Desktop, connect Desktop, get the mobile app, and
      connect from mobile—with final copy and visual treatment approved in
      context.
- [ ] Step 1 reuses the maintained CLI installation chooser rather than
      duplicating installer commands.
- [ ] Step 3 uses maintained desktop release metadata for the macOS download
      and marks Windows and Linux Desktop as coming soon without implying the
      CLI is unavailable there.
- [ ] Step 5 accurately marks public App Store and Google Play distribution as
      coming soon. This subtask provides only a waitlist integration slot and
      does not submit email data.
- [ ] Existing verified macOS header-download behavior is retained as a
      persistent shortcut unless explicitly changed by the user.
- [ ] Desktop download presentation includes Apple/macOS, Windows, and Linux
      logos with text labels; macOS is active, while Windows and Linux are
      grayed out and explicitly marked **Coming soon**.
- [ ] Mobile availability presentation includes Apple/iOS and Android logos
      with text labels; both are grayed out and explicitly marked
      **Coming soon** until real store listings exist.
- [ ] Existing useful technical deep dives remain below the new primary flow,
      while the duplicate computer-to-phone guide and superseded CTA/anchors
      are removed or rewritten.
- [ ] The finalized local candidate is responsive, keyboard accessible,
      semantically ordered, theme-correct, and built only from approved public
      copy and reviewed proof assets.
- [ ] No production website push occurs in this subtask.
- [ ] A durable landing-package development document records the committed
      pre-revision prototype, every viable intermediary title/body/visual
      alternative, statement-oriented versus action-oriented copy theory,
      final decisions and rationale, and rejected-but-still-viable variations
      before this subtask or the parent task is closed.

## Current committed prototype before content revisions

Commit `89883b92` (`Build homepage structure`) is the durable Git snapshot of
the current structural and copy baseline before the next content/download
redesign.

The committed feature order and exact titles are:

1. **One workspace for every model family.**
2. **Replace the parts you disagree with.**
3. **See what the agent is actually using.**
4. **Start at your desk. Continue wherever you are.**
5. **Shape it around your workflow.**
6. **Sessions become durable workspaces.**

The committed draft bodies are:

1. > Use Codex-, Claude-, Gemini-, Qwen-, Kimi-, and Grok-oriented profiles
   > from the same workspace. Each profile can provide model-family defaults
   > for instructions, tools, and request behavior while sessions stay in one
   > application.
2. > Providers, toolsets, features, actions, settings, and UI elements are
   > plugin surfaces. Keep the defaults that fit your workflow and replace the
   > rest through configuration.
3. > Crystal Lattice makes effective instructions, enabled plugins, tools, and
   > provider metadata visible because those layers are explicit and
   > user-modifiable. Usage, cache, duration, and cost stay visible when the
   > provider supplies them. Its open-source implementation adds source-level
   > transparency over the whole platform.
4. > Open the same runtime sessions from the terminal, Desktop app, or phone.
   > Use automatic discovery on the same network or a self-hosted bridge when
   > you are away.
5. > Build with custom agents, tools, actions, plugins, and the Python SDK. Use
   > the same platform for software work, research, operations, evaluations,
   > content workflows, and internal automation.
6. > Titles, pinned state, snapshots, attachments, settings, and plugin actions
   > turn a conversation into work you can return to, inspect, and recover.

The committed planned visuals are:

1. Desktop agent picker showing reviewed model-family profiles beside an active
   workspace.
2. Reviewed settings/plugins capture plus an illustrative plugin-layer map.
3. Compiled instructions and enabled plugins paired with provider usage/cost
   metadata.
4. Matching Desktop and mobile views of one reviewed session.
5. A reviewed non-development workflow.
6. Session history, pinned state, snapshots, and recovery controls.

The committed Desktop download treatment is one icon-led active macOS control
plus neutral Windows/Linux coming-soon controls. The committed mobile treatment
is neutral iOS/Android coming-soon controls plus a deferred waitlist position.
These download treatments are now design history, not the selected target.

The committed Desktop connection step uses local host `127.0.0.1` by default
and asks the user to enter only port `9000`.

## Copy-orientation theory to preserve

### Statement-oriented titles

Statement-oriented titles name the value or capability directly. They are
usually easier to scan and make the page's product thesis explicit.

Examples:

- One workspace for every model family.
- Everything is a plugin.
- Transparency by design.
- Work from anywhere.
- Sessions become workspaces.
- You are in control.

Strengths:

- immediately communicates the value;
- works well when readers skim only headings;
- reduces ambiguity and marketing cleverness;
- gives supporting copy room to explain mechanisms.

Risks:

- can feel generic or static;
- may undersell the emotional/user outcome;
- several statement titles in sequence can sound repetitive.

### Action-oriented titles

Action-oriented titles address what the reader can do or change.

Examples:

- Replace the parts you disagree with.
- See what the agent is actually using.
- Start at your desk. Continue wherever you are.
- Shape it around your workflow.
- Vibe code—or vibe anything.

Strengths:

- creates momentum and a stronger voice;
- frames features around user agency;
- can make technical capabilities feel more concrete.

Risks:

- may hide the underlying value when read without the body;
- can become vague or overclaim;
- may make six neighboring sections sound like unrelated slogans.

### Current working principle

Do not force all six titles into one grammatical style. Prefer the title that
states each value most clearly. Preserve a deliberate rhythm by pairing
statement-oriented anchors with action-oriented alternatives or supporting
sentences.

The first two current titles are explicitly preferred:

- **One workspace for every model family.**
- **Replace the parts you disagree with.**

Alternatives for those themes remain comparison material; they do not
supersede the preferred titles without later human approval.

## Draft highlight copy and proof brainstorm

The proposed initial ordering follows the product argument from model breadth,
through replaceability and inspectability, into location and workflow
flexibility:

1. One workspace for every model family.
2. Replace the parts you disagree with.
3. See what the agent is actually using.
4. Start at your desk. Continue wherever you are.
5. Shape it around your workflow.
6. Sessions become durable workspaces.

This ordering and all copy below remain unapproved until reviewed in the
structural prototype.

### 1. One workspace for every model family

Recommended headline:

> One workspace for every model family.

Selection state: current preferred title.

Viable title alternatives to retain:

- One app for every model.
- Every model. One workspace.
- Stop switching between model-specific apps.
- Model-native agents, together in one workspace.

Rationale for the current preference:

- “Workspace” better represents sessions, tools, configuration, Desktop, and
  mobile than “app.”
- “Every model family” is more accurate than implying support for literally
  every model.
- It is statement-oriented and directly communicates the value.

Draft body:

> Use Codex-, Claude-, Gemini-, Qwen-, Kimi-, and Grok-oriented profiles from
> the same workspace. Each profile can provide model-family defaults for
> instructions, tools, and request behavior while sessions stay in one
> application.

Content direction:

- Use Codex-, Claude-, Gemini-, Qwen-, Kimi-, and Grok-oriented configured
  profiles from the same application and session system.
- Emphasize model-family-oriented default toolsets and workflows.
- Do not imply these profiles are the official upstream applications or that
  Crystal Lattice imports their accounts or private sessions.

Proof direction:

- Create a deterministic Desktop agent-picker capture containing reviewed
  configured-agent IDs.
- Include enough surrounding session/status UI to communicate one workspace,
  not merely a list of model names.

### 2. Everything is a plugin and replaceable

Recommended headline:

> Replace the parts you disagree with.

Selection state: current preferred title.

Viable title alternatives to retain:

- Everything is a plugin.
- Everything is replaceable.
- A plugin for every layer.
- The whole harness is yours to change.
- Your agent. Your rules.

Rationale for the current preference:

- It gives the plugin architecture a user-centered reason to matter.
- It communicates selective replacement rather than requiring users to build
  everything themselves.
- Its action-oriented voice creates useful contrast with the statement-oriented
  first title.

Draft body:

> Providers, toolsets, features, actions, settings, and UI elements are plugin
> surfaces. Keep the defaults that fit your workflow and replace the rest
> through configuration.

Content direction:

- Providers, model-family toolsets, features, tools, session actions,
  application actions, settings, and UI schema are plugin surfaces.
- Users can retain useful defaults while replacing selected layers through
  configuration.

Proof direction:

- Reuse the reviewed settings/plugins screenshot.
- Pair it with a small deterministic layer diagram identifying provider,
  tools, features, actions, and UI schema.
- The screenshot proves visible plugin contribution; the diagram explains the
  broader architecture without pretending to be product UI.

### 3. Everything is transparent and open source

Recommended headline:

> See what the agent is actually using.

Selection state: open for further review.

Viable value-led alternatives:

- Transparency by design.
- Full transparency, from prompt to cost.
- See the entire agent stack.
- Nothing important is hidden.
- Inspect every layer.
- You can see what the agent sees.

Draft body:

> Crystal Lattice makes effective instructions, enabled plugins, tools, and
> provider metadata visible because those layers are explicit and
> user-modifiable. Usage, cache, duration, and cost stay visible when the
> provider supplies them. Its open-source implementation adds source-level
> transparency over the whole platform.

Content direction:

- Effective instructions, selected agent, enabled plugins, tools,
  provider-native metadata, usage, cache information, duration, and cost are
  inspectable at the boundaries where the active provider supplies them.
- Explicit framework and plugin boundaries make the execution path
  inspectable and let users modify the plugins involved.
- Crystal Lattice is open source, adding source-level transparency over the
  complete implementation.
- Do not imply every provider supplies uniform metadata.

Proof direction:

- Reuse the reviewed usage-and-cost focus image.
- Add a deterministic **Show compiled system message** capture.
- Compose them as “before the request” and “after the request” proof.
- Include source/repository access in the card action or caption rather than
  creating a separate open-source highlight.

### 4. Work from anywhere

Recommended headline:

> Start at your desk. Continue wherever you are.

Selection state: open; the original value-led title remains a strong option.

Viable alternatives:

- Work from anywhere.
- Your workspace, wherever you are.
- One session across every screen.
- Start at your desk. Continue anywhere.
- The same work, on every device.

Draft body:

> Open the same runtime sessions from the terminal, Desktop app, or phone. Use
> automatic discovery on the same network or a self-hosted bridge when you are
> away.

Content direction:

- The terminal, Desktop app, mobile app, and SDK operate against the same
  runtime/session model.
- Same-network discovery and self-hosted bridge connectivity must remain
  clearly distinguished.

Proof direction:

- Reuse the reviewed mobile active-session image.
- Create a Desktop capture of the same reviewed session.
- Compose the two views side by side with matching session identity to prove
  continuity rather than merely showing two clients.

### 5. Adjustable to workflows beyond development

Recommended headline:

> Vibe code—or vibe anything.

Selection state: selected working title, pending contextual/visual validation.

Draft body:

> Turn the same agent platform toward software work, research, operations,
> content, evaluations, internal automation, or a workflow built from your own
> tools and plugins.

Viable alternatives to retain:

- Vibe code. Then go beyond code.
- From vibe coding to general-purpose agents.
- A general-purpose agent—not just a coding agent.
- Shape it around your workflow.
- More than a coding harness.
- Vibe code—or build any workflow.
- From vibe coding to anything.

Rationale for the selected working title:

- It includes the established “vibe code” idea while intentionally extending
  it beyond software development.
- The em dash makes the English phrase read as a deliberate contrast.
- “Vibe anything” is a coined product phrase rather than an established
  category, so the body must immediately state the real general-purpose value.
- It is memorable, but must be checked in context to ensure it does not make
  the surrounding value-led titles feel less credible.

Content direction:

- Custom tools, actions, agents, plugins, and the Python SDK can support
  coding, research, operations, content workflows, evaluations, and internal
  automation.
- Avoid the unbounded public claim “works for any workflow.”

Proof direction:

- Create one reviewed non-development fixture through the real application
  and plugin path.
- Preferred first concept: a bounded research-brief workflow using sanitized
  public source notes and a plugin-provided follow-up or export action.
- Acceptable alternatives include support triage, structured data enrichment,
  or internal checklist generation.
- Do not use a static mock, private customer data, or an unverified SDK
  example as proof.

### 6. Durable session workspaces

Draft headline:

> Sessions become durable workspaces.

Draft body:

> Titles, pinned state, snapshots, attachments, settings, and plugin actions
> turn a conversation into work you can return to, inspect, and recover.

This option has the strongest existing product proof and overlaps least with
the five approved themes.

Viable alternatives to retain:

- Sessions become workspaces.
- Durable workspaces, not disposable chats.
- Work that persists.
- Keep the work, not just the transcript.
- Experiment without losing the thread.

## Additional overlapping theme: You are in control

“You are in control.” is a viable umbrella value, but currently overlaps with
multiple sections:

- model choice in **One workspace for every model family**;
- modification in **Replace the parts you disagree with**;
- inspectability in the transparency section;
- local/remote choice in **Work from anywhere**;
- workflow adaptation in **Vibe code—or vibe anything**.

Possible uses to preserve for later review:

1. **Standalone highlight**
   - Title: **You are in control.**
   - Body direction: choose the model-family profile, inspect the effective
     harness, replace plugins, and decide where the runtime and sessions live.
   - Risk: duplicates several stronger, more specific values.
2. **Umbrella phrase in the hero**
   - Use as a short supporting statement tying together model choice,
     replaceability, transparency, and local control.
   - Risk: may compete with the current “outgrow one-size-fits-all agents”
     positioning.
3. **Transparency title**
   - Example: **You are in control—and nothing is hidden.**
   - Risk: weakens the explicit transparency value and becomes long.
4. **Plugin-section supporting sentence**
   - Keep **Replace the parts you disagree with** as the title and use “You are
     in control” as the concluding benefit.
   - Current best fit if the phrase is used without creating a seventh theme.

## Download presentation research and viable targets

Reviewed examples:

- `https://zcode.z.ai/en/docs/install`
- `https://opencode.ai/download`
- `https://toggl.com/apps/mobile/ios`
- `https://toggl.com/apps/mobile/android`

The supplied examples establish two useful patterns:

- ZCode emphasizes one current-platform/latest download and follows it with an
  “All platforms” set covering macOS, Windows, and Linux variants.
- OpenCode lists Desktop downloads by explicit operating system,
  architecture, and package format.
- Toggl gives iOS and Android their own platform-specific presentation, device
  imagery, and dedicated download section.

### Required target behavior

- Desktop controls show Apple/macOS, Windows, and Linux logos.
- macOS is active and offers the verified universal DMG.
- Windows and Linux controls are visibly grayed out and say **Coming soon**.
- Mobile controls show Apple/iOS and Android logos.
- Both mobile controls remain visibly grayed out and say **Coming soon** until
  real store listings exist.
- Logo meaning is also conveyed by text; accessibility must not depend on the
  logo alone.

### Viable Desktop layout A: current platform first

```text
Download Crystal Lattice Desktop

[Apple logo] Download for macOS
Universal DMG · Apple silicon + Intel · macOS 14+

All platforms
[Windows logo] Coming soon
[Linux logo]   Coming soon
```

Strengths:

- closest to the ZCode pattern;
- gives the only real download clear priority;
- architecture detail remains secondary.

### Viable Desktop layout B: platform matrix

```text
[Apple logo]        [Windows logo]      [Linux logo]
macOS               Windows             Linux
Universal DMG       Coming soon         Coming soon
[Download]          [disabled]          [disabled]
```

Strengths:

- closest to OpenCode's explicit per-platform organization;
- future Windows/Linux activation is straightforward;
- visually comparable across platforms.

Risk:

- gives unavailable platforms more visual weight.

### Viable Mobile layout

```text
[Apple logo] iOS             [Android logo] Android
Coming soon                   Coming soon

[email address                         ]
[Join the mobile release waitlist      ]
```

When public listings exist, the grayed platform controls can be replaced with
the official App Store and Google Play badges.

## Supporting implementation facts

- The current `HeroSection` requires an installation chooser. It can be made
  optional without creating a second hero component.
- The current feature showcase supports reviewed light/dark images but is
  fixed to two columns. It can be extended to a three-column six-card layout
  while retaining its existing default.
- Existing visual assets directly support usage/cost, settings/plugins,
  actions, snapshots, and mobile-session claims. The revised themes require
  new configured-agent, compiled-instructions, Desktop/mobile continuity, and
  non-development-workflow proof.
- The existing `ActionGuide` cannot cleanly compose an installation chooser,
  command panel, maintained download metadata, unavailable platform states,
  mobile store states, and a future form. A focused `gettingStarted` section
  is warranted.
- The local pending header icon already reads the exact Desktop release URL,
  version/build, architectures, minimum macOS, and checksum from a maintained
  release document.

## Execution plan

Status: Draft

Start from the approved structural prototype and review the five draft cards,
sixth-card options, hero copy, getting-started copy, and retained deep dives in
their real desktop and phone context. Record copy and ordering changes before
producing new assets so proof work follows the approved narrative.

After the copy direction and sixth theme are selected, produce only the proof
assets required by the approved cards. New captures must traverse real product
paths with deterministic reviewed state. Conceptual architecture graphics
must be visibly illustrative and must not imitate screenshots.

Then refine card ordering, image composition, dimensions, spacing, typography,
and responsive behavior through LAN previews and light/dark screenshots. The
three-column/two-column/one-column structure from the prototype is a starting
point, not a locked visual requirement.

Finalize the six getting-started steps in context, including the balance
between download controls, code, explanatory text, and reviewed media. Keep
the waitlist position non-functional but visually ready for subtask `020`.

No push occurs during this subtask. Its completion is a human-approved local
website candidate with reviewed copy, reviewed proof, approved ordering, and
approved visual layout.

### Implementation decisions and open questions

- Decision: inherit the approved component and content structure from subtask
  `010`; structural redesign is not reopened unless contextual review exposes
  a material problem.
- Decision: merge open-source value into transparency.
- Decision: inspectability comes from explicit framework/plugin boundaries and
  user-modifiable plugins; open source adds full source-level transparency.
- Decision: the sixth highlight is durable session workspaces.
- Decision: use **Vibe code—or vibe anything.** as the selected working title
  for the general-purpose-agent value while retaining all viable alternatives.
- Decision: keep **One workspace for every model family.** and **Replace the
  parts you disagree with.** as preferred titles; alternatives remain testable
  options rather than superseding proposals.
- Decision: preserve statement-oriented and action-oriented variants and judge
  each theme by clarity, rhythm, credibility, and contextual appearance rather
  than enforcing one title grammar.
- Decision: platform presentation must include Apple/macOS, Windows, Linux,
  Apple/iOS, and Android logos with text labels.
- Decision: unavailable Windows, Linux, iOS, and Android controls are grayed
  out and explicitly marked **Coming soon**.
- Open design question: use Desktop layout A (current platform first) or
  layout B (platform matrix).
- Open positioning question: whether and where to use **You are in control.**
- Decision: retain the header macOS download icon as a persistent shortcut
  while Getting Started owns explanatory download content.
- Decision: keep accurate source/internal mobile availability subordinate to
  the primary store-coming-soon message.
- Decision: do not render a functional or fake waitlist form in this subtask.

### Documentation

- Update `landing_page/README.md` when the new section model or proof inputs
  change maintainer workflow.
- Update `landing_page/docs/development/content-system.md` with the
  getting-started and extended feature-showcase authoring contracts.
- Update visual-asset documentation or catalog metadata for each new reviewed
  proof asset.
- Keep public content focused on delivered behavior; do not publish planning
  labels, approval state, internal fixture names, or placeholder visuals.
- Before closure, create and link a durable
  `landing_page/docs/development/` record containing:
  - the `89883b92` pre-revision snapshot;
  - all viable copy and visual alternatives;
  - statement-oriented versus action-oriented theory;
  - download-pattern research;
  - final selected copy, visuals, and ordering;
  - reasons each selected option won;
  - rejected-but-viable alternatives worth testing later.

### Task checklist

- [x] **HUMAN JUDGMENT:** Select **Vibe code—or vibe anything.** as the current
      working general-purpose title.
- [ ] **HUMAN JUDGMENT:** Review and revise all six draft card copies in the
      rendered structural prototype.
- [ ] **HUMAN JUDGMENT:** Approve or revise the highlight ordering.
- [ ] **HUMAN JUDGMENT:** Approve the hero and getting-started copy direction.
- [ ] **AGENT:** Produce, review, promote, and bind required new proof assets.
- [ ] **AGENT:** Apply approved copy and proof to the existing structure.
- [ ] **AGENT:** Refine the card and getting-started visual layout through
      responsive local review.
- [ ] **AGENT:** Add the non-functional waitlist integration slot for subtask
      `020` without collecting data.
- [ ] **AGENT:** Add content, accessibility, responsive, link, and visual
      tests.
- [ ] **AGENT:** Create the durable homepage positioning/visual decision
      record and reconcile it with the final implementation before closure.
- [ ] **AGENT:** Build and provide a LAN-accessible preview.
- [ ] **HUMAN JUDGMENT:** Approve the local website redesign and proof.
- [ ] **AGENT:** Hand the approved integration contract to subtask `020`.

### Requirement verification

- Primary-order verification: built HTML and browser tests show Hero,
  Highlights, and Getting Started in the approved order before retained deep
  dives.
- Highlight verification: content tests require six cards, exact approved
  theme IDs, reviewed media, useful alt text, and the user-selected sixth
  theme; visual tests cover both themes and desktop/tablet/phone layouts.
- Configured-agent claim verification: proof and copy are checked against
  current configured agents and model-family tool plugins without claiming
  official upstream application identity.
- Transparency/open-source verification: the card uses current compiled
  instructions, plugin/tool state, provider metadata, and repository/license
  evidence without claiming uniform provider metadata.
- Getting-started verification: semantic ordered-list and focused content
  tests require the exact six steps and their correct download/code/media
  boundaries.
- Availability verification: live CLI/macOS links and maintained metadata
  pass; Windows/Linux Desktop and public mobile stores remain non-interactive
  and explicitly coming soon.
- Accessibility verification: keyboard, focus, heading order, alt text,
  disabled-state semantics, responsive containment, and reduced-motion checks
  pass in the production build.
- Handoff verification: the reviewed build exposes a typed, documented slot
  for the later waitlist form but contains no endpoint, credential, email
  submission, or fake success behavior.
- Decision-record verification: the package-owned development document
  includes commit `89883b92`, every viable retained variation, the
  action-oriented/statement-oriented framework, researched platform-download
  patterns, final selections and rationale, and later-testable alternatives.

### Additional implementation verification

- Run landing content/analytics tests, TypeScript/Astro build, visual-asset
  checks, and the complete production-configured Playwright suite on an
  isolated port.
- Confirm active theme images are the only variants loaded initially and all
  new media respects dimensions and byte budgets.
- Confirm no placeholders, unverified APIs, private data, or upstream-product
  parity claims appear.
- Confirm existing direct desktop download metadata and checksum tests remain
  intact.
- Confirm no website source is pushed or deployed in this subtask.