# Homepage Positioning And Visual Decisions

This page preserves the homepage positioning, copy, download presentation, and
proof-visual decisions that are likely to be revisited. It records selected
directions alongside viable alternatives so later redesigns can reuse the
reasoning instead of reconstructing it from task history.

The maintained implementation plan is tracked under
`tasks/20260930-homepage-getting-started-and-waitlist/`. Public website copy
must not present target-only visuals or product improvements as available until
they are implemented and verified.

## Approved First-Release Direction — October 7, 2026

The owner approved a complete first user website with all six reviewed visual
stories, three public compatibility views and a short product-based launch
positioning review. Extensive market research remains a later input.

The existing selections and alternatives below are retained as decision
history. The bounded review may propose changes to the primary audience,
benefit, category, hero or CTA, but no new final wording is selected by this
scope approval. Record the accepted choice and its rationale here when the
review is performed.

Use actual product/release evidence and preserve compatibility limitations.
Coordinate one integrated site/form publication, followed by live website and
waitlist checks. Describe source availability truthfully before repository
visibility changes and verify the public source controls afterward.

## Baseline Before Copy Revision

Commit `89883b92` (`Build homepage structure`) is the durable baseline before
the current copy and platform-download revisions.

Its feature titles were:

1. One workspace for every model family.
2. Replace the parts you disagree with.
3. See what the agent is actually using.
4. Start at your desk. Continue wherever you are.
5. Shape it around your workflow.
6. Sessions become durable workspaces.

Its platform presentation used one generic download-icon macOS control,
generic Desktop icons for unavailable platforms, and generic mobile-device
icons for iOS and Android. That implementation established structure but did
not match the selected logo-led download convention.

## Copy-Orientation Theory

### Statement-oriented titles

Statement-oriented titles name the capability or value directly.

Examples:

- One workspace for every model family.
- Everything is a plugin.
- Transparency by design.
- Work from anywhere.
- Sessions become workspaces.
- You are in control.

They are easy to scan, reduce dependence on body copy, and usually sound more
credible than abstract marketing language. Their risk is repetition: six
declarative headings can feel static.

### Action-oriented titles

Action-oriented titles emphasize what the reader can do.

Examples:

- Replace the parts you disagree with.
- See what the agent is actually using.
- Start at your desk. Continue wherever you are.
- Shape it around your workflow.
- Vibe code—or vibe anything.

They create momentum and make technical capabilities feel relevant. Their risk
is that the underlying value can become unclear when the title is read without
its body.

### Selected principle

Do not force all highlights into one grammatical style. Select the clearest
title for each value, then evaluate the rhythm of the complete grid.

The current mix intentionally combines direct value statements with
action-oriented user outcomes.

## Selected Feature Order And Copy

### 1. One workspace for every model family

Selected title:

> One workspace for every model family.

Selected body:

> Use Codex-, Claude-, Gemini-, Qwen-, Kimi-, and Grok-oriented profiles
> without switching between separate model-specific clients. Each profile
> keeps its model-family instructions, tools, and request behavior inside the
> same workspace.

Why selected:

- “Workspace” covers sessions, apps, tools, and configuration better than
  “app.”
- “Model family” avoids an unsupported claim about every possible model.
- The statement directly communicates the value.

Viable alternatives:

- One app for every model.
- Every model. One workspace.
- Stop switching between model-specific apps.
- Model-native agents, together in one workspace.

Planned proof:

- Add config/API/UI metadata for stable ID, user-facing title, description,
  and order.
- Capture an ordered agent picker.
- Capture Codex selected beside Codex-specific tools such as apply patch,
  shell, and image viewing.
- Capture Claude selected beside Claude-specific tools.

### 2. Replace the parts you disagree with

Selected title:

> Replace the parts you disagree with.

Selected body:

> Providers, tools, model defaults, actions, settings, and UI elements are
> plugin surfaces. Keep the built-in experience where it works and replace
> only the layers your workflow disagrees with.

Why selected:

- It gives the plugin architecture a practical user benefit.
- It communicates selective replacement instead of requiring users to build
  the whole system.
- Its action-oriented voice balances the statement-oriented first title.

Viable alternatives:

- Everything is a plugin.
- Everything is replaceable.
- A plugin for every layer.
- The whole harness is yours to change.
- Your agent. Your rules.

Planned proof:

- Provider-specific settings showing authentication mode and flex processing.
- Separate plugins/features window showing independently selectable features.

### 3. Transparency by design

Selected title:

> Transparency by design.

Selected body:

> Framework and plugin boundaries make instructions, configuration, tools,
> state, and provider metadata visible and user-modifiable. Usage, cache,
> duration, and cost remain visible when the provider supplies them. Open
> source adds full source-level transparency.

Why selected:

- It states the value without implying open source is the mechanism that makes
  runtime behavior inspectable.
- Inspectability comes from explicit framework/plugin boundaries and
  user-modifiable plugins.
- Open source is an additional source-level transparency benefit.

Viable alternatives:

- See what the agent is actually using.
- Full transparency, from prompt to cost.
- See the entire agent stack.
- Nothing important is hidden.
- Inspect every layer.
- You can see what the agent sees.

Planned proof:

- Compiled system/developer instructions and enabled plugin context.
- Completed response metadata showing usage, cache, duration, reasoning tokens,
  and cost when available.

### 4. Work from anywhere

Selected title:

> Work from anywhere.

Selected body:

> Start in the terminal or Desktop app and continue the same session from your
> phone. Connect on the same network or through a self-hosted bridge when you
> are away.

Why selected:

- It states the original value directly.
- The body explains the actual local-network and bridge mechanisms.

Viable alternatives:

- Start at your desk. Continue wherever you are.
- Your workspace, wherever you are.
- One session across every screen.
- Start at your desk. Continue anywhere.
- The same work, on every device.

Planned proof:

- The same reviewed session open in Desktop and mobile.
- Matching session title, latest user/assistant content, and status.

### 5. Vibe code—or vibe anything

Selected title:

> Vibe code—or vibe anything.

Selected body:

> Turn the same agent platform toward software work, research, operations,
> content, evaluations, internal automation, or a workflow built from your own
> tools and plugins.

Why selected:

- It preserves the recognizable “vibe code” idea while intentionally extending
  the platform beyond software development.
- The em dash makes the coined phrase read as a deliberate contrast.
- The body immediately explains the real general-purpose-agent value.

Viable alternatives:

- Vibe code. Then go beyond code.
- From vibe coding to general-purpose agents.
- A general-purpose agent—not just a coding agent.
- Shape it around your workflow.
- More than a coding harness.
- Vibe code—or build any workflow.
- From vibe coding to anything.

Planned proof:

- System message at the top.
- Non-development user prompt below it.
- Initial agent reasoning that implies tool-heavy work.
- Crop before tool calls appear.

### 6. Sessions become workspaces

Selected title:

> Sessions become workspaces.

Selected body:

> Titles, subtitles, status, pinned state, snapshots, attachments, and actions
> turn conversations into durable workspaces. These behaviors are
> plugin-driven: keep them, disable them, replace them, or refine them for your
> workflow.

Why selected:

- It states the durable-session value directly.
- The body distinguishes the plugin-driven implementation from hardcoded
  product behavior.

Viable alternatives:

- Sessions become durable workspaces.
- Durable workspaces, not disposable chats.
- Work that persists.
- Keep the work, not just the transcript.
- Experiment without losing the thread.

Planned proof:

- Session list with `todo`, `in-progress`, and `done`.
- Pinned and unpinned sessions.
- Descriptive titles and subtitles.
- Plugin-provided controls or configuration that own those fields.

## Overlapping Theme: You Are In Control

“You are in control.” remains a viable umbrella value, but it overlaps:

- model choice;
- plugin replacement;
- transparency and modification;
- runtime/connectivity ownership;
- workflow adaptation.

Preserved options:

1. Standalone highlight: strongest wording, highest duplication risk.
2. Hero support line: can tie model choice, replaceability, and transparency
   together, but may compete with the one-size-fits-all positioning.
3. Transparency variation: “You are in control—and nothing is hidden,” but
   this weakens the shorter selected transparency title.
4. Plugin-section outcome: keep “Replace the parts you disagree with” and use
   control as the concluding benefit.

Current recommendation: use control as an outcome in the plugin/body language,
not as a seventh highlight.

## Platform Download Presentation

Reviewed references:

- `https://zcode.z.ai/en/docs/install`
- `https://opencode.ai/download`
- `https://toggl.com/apps/mobile/ios`
- `https://toggl.com/apps/mobile/android`

### Selected Desktop layout: current platform first

```text
Download Crystal Lattice Desktop

[Apple logo] macOS
Universal DMG · Apple silicon + Intel · macOS 14+
[Download for macOS]

All platforms
[Windows logo] Windows — Coming soon
[Linux logo]   Linux — Coming soon
```

Why selected:

- gives the only real download clear priority;
- keeps version/architecture details subordinate;
- makes unavailable platforms discoverable without presenting false actions;
- can activate Windows/Linux later without replacing the section.

Viable alternative: three-column platform matrix.

```text
[Apple logo]        [Windows logo]      [Linux logo]
macOS               Windows             Linux
Universal DMG       Coming soon         Coming soon
[Download]          [disabled]          [disabled]
```

The matrix is symmetrical and easy to extend but gives unavailable platforms
more visual weight.

### Selected mobile availability layout

```text
[Apple logo] iOS             [Android logo] Android
Coming soon                   Coming soon

[email address]
[Join the mobile release waitlist]
```

Until the store listings exist:

- both platform controls are grayed;
- both say **Coming soon**;
- neither is interactive;
- visible text conveys all logo meaning.

Official store badges replace these states only after real listings exist.

## Screenshot-Specific Product Decisions

Some planned proof may require hiding or reordering settings/plugin rows.
Classify each need before implementation:

1. Real product improvement when ordinary users benefit from the behavior.
2. Maintained capture-only UI plugin/fixture when it truthfully demonstrates
   plugin extensibility without changing production defaults.
3. One-off candidate aid only for exploration; never promote it as reviewed
   proof.

The agent picker metadata change is a real product improvement because the
current backend/SDK/Desktop path exposes and renders bare agent IDs.

Selected implementation:

- agent config accepts optional `display.title`, `display.description`, and
  finite `display.order`;
- stable config keys remain agent IDs;
- the existing `/agents` string list and SDK `listAgents()` remain compatible;
- `/agents` adds ordered `agent_descriptors`;
- the SDK adds optional `listAgentDescriptors()` and controller descriptor
  caching;
- Desktop renders descriptor title/description/order and submits the stable ID;
- display metadata is stripped before provider request configuration is built.

Capture-specific ordering/hiding does not add production controls solely for
screenshots. Deterministic fixtures select the relevant rows. Session-workspace
proof reuses the existing `session-status-app`, `session-pinned-app`, and
`session-title-app` contracts, including `todo`, `in_progress`, and `done`
values.

The detailed implementation and verification plan lives in
`tasks/20260930-homepage-getting-started-and-waitlist/018-homepage-visuals-product-improvements.md`.

## Compatibility Claim Provenance

Homepage claims and proof captions use the accepted draft projection in
`landing_page/research/current-product-and-compatibility-baseline/`.
The canonical public-copy input is
`website-compatibility-data.md`, backed by the machine-readable projection,
claim evidence, matrices, completion manifest, and retained generators in the
same package.

Provenance:

- historical planning review commit:
  `c52db305e0a815da5831d462a495df68ec4f2eb7`;
- accepted product source revision:
  `add5f5e71de3bb1676851bb840dfd77620f63ddb`;
- transformation version: `compatibility-baseline-v2`;
- website projection review state: accepted;
- website projection maturity: draft.

The canonical unnumbered package supersedes the earlier
`020-current-product-and-compatibility-baseline` location and contains a more
complete per-plugin feature projection. Do not create or maintain a duplicate
copy at the historical path.

Publication rules:

- Available capabilities may support direct current-product claims.
- Conditional and Optional capabilities retain explicit qualification.
- Planned capabilities are not presented as shipped.
- Model-family tool bundles are Crystal Lattice compatibility
  implementations, not official upstream applications, accounts, or
  sessions.
- Provider metadata and hosted entitlement are not described as uniform.

The accepted package is intentionally pinned to its product source revision.
Running the extractors against the October 4, 2026 repository detects later
Anthropic context-editing and compaction additions. That drift requires a
separate compatibility re-audit; it does not authorize this homepage task to
regenerate or silently reclassify the accepted projection. The maintained
website-projection generator continues to verify the accepted output.

## October 4 Revised Candidate Set

Historical candidate: superseded by the October 5 review below. It did not
receive final visual approval or source promotion. The subsequent uncommitted
in-page trial is also recorded below.

The revised set is implemented on `develop` through these task-owned commits:

- `ebb053ac`: read-only agent defaults API/SDK contract and real two-pane
  Desktop selector;
- `2bfaf03c`: pin/status default corrections with saved-preference
  preservation;
- `4fab5568`: dedicated light/dark user-bubble foreground;
- `7d46556b`: deterministic standard-blue Desktop capture theme;
- `29604c23`: real action fixtures, revised product states, native capture,
  and review-gallery generation.

The review gallery is generated under ignored output at:

```text
landing_page/artifacts/homepage-visual-review/index.html
```

It deliberately does not promote sources, generate public derivatives, change
content bindings, or publish the site.

Candidate-specific facts:

- Codex and Claude use the real consolidated Desktop selector and safe
  effective-default plugin projection.
- Provider/application relationship boards use production captures inside
  explicitly illustrative JSON/connector framing. Red connectors also carry
  numbered text labels.
- The application relationship board currently uses a production
  plugin-contributed action row as its middle proof. Review must decide
  whether this communicates the relationship adequately or whether a
  separate real application-plugin registry row remains necessary.
- Compiled instructions come from the real
  `show_compiled_system_message` feature action.
- Cost report content comes from the real `show_cost_report` application
  action after seeding generic synthetic records through the production
  SQLite store. Values are illustrative, not provider invoices or company
  spending.
- Continuity is presented as one annotated Desktop/phone board using matching
  session content.
- The non-development state identifies the configured `zai` profile as
  GLM-5.3 Flash through Z.ai, includes attached-source work, expands reasoning,
  and stops before tool calls.
- The workspace state uses the production status, pin, and title/subtitle
  contracts, a fresh preference namespace, header-only default pin placement,
  and the default-pinned status rich list.
- Published-source promotion still requires a reproducible macOS producer.
  The current candidate used the latest production JavaScript bundle inside a
  known-good released native shell because a newly generated local Hermes
  runtime crashed before evaluating JavaScript.

## October 5 In-Page Review And Proposed Revision

Status: the initial revision was approved in
`tasks/20260930-homepage-getting-started-and-waitlist/018-homepage-visuals-product-improvements.md`.
The user authorized the layout checkpoint first, with review before later
steps. Its subsequent frame/scroll/alignment follow-up is Draft, as recorded
below. This record is developer design history, not website copy.

### Candidate before this revision

The October 4 uncommitted `develop` trial bound the captures to the real
homepage with these choices:

- `FeatureShowcase` changed to alternating full-width text/image rows when
  media was available.
- The agent picker used Codex/Claude tabs and a phone-only full-size control.
- Plugin proof used individual JSON cards and cropped UI rows, joined by
  runtime SVG lines. Long plugin paths were truncated.
- Transparency showed two mobile captures in a swipeable pair.
- Continuity used a Desktop/phone HTML composition and the label
  "Same session" plus "title · status · agent · latest prompt · answer".
- A standalone "GLM-5.3 Flash through Z.ai" heading appeared above the
  general-purpose workflow.
- Workspace proof used a mobile session list and a small status callout
  labeled "Default-pinned status action".
- Costs carried "illustrative fixture data" wording.
- The old "Treat sessions as workspaces, not disposable chats" gallery
  remained below the new workspace highlight.

The selected six feature titles/bodies were retained. Disposable screenshots
of this trial are under
`landing_page/artifacts/homepage-live-review/` and
`landing_page/artifacts/visual-assets/playwright/captures/` in the develop
worktree. Those files are not a durable substitute for this written record.
The user subsequently allowed a cleanup/snapshot commit at the layout
checkpoint if useful. The selected approach leaves this checkpoint uncommitted
for review.

### User decisions and rationale

- Restore two independent highlight columns on desktop, each with title,
  description, then images. The user selected this familiar structure;
  fitting media into it does not authorize a layout redesign.
- Show both picker images without a switcher. Codex/Claude tabs can imply
  those are the only supported harnesses; the captures should retain the
  broader configured-agent list.
- Compose each plugin relationship into one ImageMagick output. The code
  belongs on the left, the contextual real UI on the right, with connectors
  between actual declarations and contributed controls. Names must be
  readable, not ellipsized after a common path prefix.
- Demonstrate several contributions together, including one export package
  contributing two actions. A series of isolated one-line diagrams misses
  that architectural value.
- Remove goals and implementation vocabulary from public captions. Visible
  repeated session content should demonstrate continuity; a label listing
  the fields to check does not demonstrate it.
- Clear sample data and capture-specific filtering are acceptable when they
  improve comprehension without inventing capabilities. Hide irrelevant
  picker groups only for the capture, and keep production behavior intact.
- Include real Cost and ChatGPT usage reports with readable sample values.
  Use "Sample data" for examples; preserve "estimated" where meaningful and
  do not imply ChatGPT estimated usage is an account invoice.
- Merge the duplicate workspace pitch. Use Desktop session/message action
  popups with readable options, including pin/archive/status and
  fork/delete-from-here/native-compaction controls.
- Rename the long compaction action and fix real popup sizing. Retain action
  IDs, provider gating, confirmation, and saved preferences.

The attached reference screenshots guide composition and label readability.
They are not approved public source images: their personal session content
and usage totals must be replaced by isolated sample data.

### Approved placements and wording

Historical approval for the first layout passes. The later integration
request below supersedes the two additional gallery placements.

- Keep the primary six-highlight grid and existing order. Stack the two
  compact picker captures and the two workspace captures within their
  respective columns; all are ordinary images. This was the first layout
  checkpoint's approved choice; the subsequent review requests horizontal
  image scrolling instead, as recorded below.
- Use the primary three-plugin Session actions composition in the plugin
  highlight. Place the two additional Message actions and Session list
  relationship images in the existing screenshot-gallery style after
  `everything-replaceable`, replacing the duplicate workspace pitch.
- Keep a compact instructions/cost proof in the transparency highlight and
  use an existing-style three-entry gallery after `native-provider-features`
  for **Inspect the instructions**, **See where costs go**, and **Track
  ChatGPT usage**, each with a short visitor-facing description.
- Preserve the snapshots source and a snapshot-guidance link in the merged
  workspace explanation. Move the `session-workbench` fragment to the
  workspace highlight so existing links retain their subject.
- Selected: **OpenAI compaction up to here**. It identifies the actual
  provider-specific capability. Retain **Native compaction up to here** as
  the shorter viable alternative for a future reconsideration.

These specific placements are approved, not permission to add or move arbitrary
sections. If a half-column image remains illegible after reasonable source,
crop, and composition tuning, stop and propose a specific existing-format
alternative using actual website screenshots.

### Staged execution and popup clarification

The user requested review at every important checkpoint before authorizing
the next work and commits. The first checkpoint restores the website layout;
it does not implement product popup changes or produce new source captures.
Use descriptive placeholders for those pending images and retain suitable
existing candidates only as interim layout evidence.

The subsequent product checkpoint must allow one line break (two lines) in
action names on Desktop and mobile, including other popups sharing the same
menu design. Widening the Desktop popup alone is insufficient. Row height,
icon/pin placement, native popup height, and scrolling must accommodate
wrapped names. Preserve actions and eligibility while changing the visible
message action/confirmation label to the selected OpenAI wording.

The implemented layout checkpoint uses ordinary stacked picker images and
descriptive placeholders for the pending composites, reports, and Desktop
menus. The current research screenshot remains an interim source. This
allows review of the approved section structure before the later asset work,
without treating the rejected relationship or continuity images as final.
The existing gallery format supplies both supporting sections. The workspace
fragment moved with its subject, and a snapshot-guide link retains the
recovery story after removing the duplicate gallery.

Automated desktop/phone geometry, content order, active-theme loading, and
overflow checks pass. The 320 px check exposed header overflow, addressed
with tighter spacing only below 360 px while preserving every control.
Playwright captures exist for five widths in both themes. Pixel-level visual
review and user approval remain pending; no commit or final source promotion
has been made for this checkpoint.

### Retained alternatives and limits

- Two picker images side by side are viable only if tools and other model
  families remain readable at the real display width. Stacking was used for
  the first checkpoint and is now superseded by the requested horizontal
  image strip. The Codex/Claude selector tabs remain rejected for this
  marketing context.
- The full-width alternating layout may suit a different page, but is rejected
  for these six highlights and must not return as an automatic media rule.
- Live HTML/SVG relationship diagrams can be useful for an interactive
  tutorial. They are rejected for this static website evidence; connectors
  must be baked into the image.
- Tight menu-row crops are useful as magnified callouts inside a composition,
  but must not replace the complete contextual screenshot on the right.
- The open status list alone obscures the title/subtitle/pin evidence.
  Prefer the real Desktop row popup and enough visible list context.
- A mobile cost table demonstrates the component but wraps names and values
  poorly. Prefer a real Desktop report window and shorter sample names before
  proposing any product-wide report redesign.

Technical provenance stays with the asset sources: exact package/action
mappings, source hashes, generated records, capture settings, and reasons for
sample or presentation changes. Final selection and human visual acceptance
must be recorded here before task closure.

### Image-frame and alignment follow-up

The next user review requested and then approved a small follow-up to layout
checkpoint 1, owned by task 018.

Selected direction from the feedback:

- Reuse the image-frame treatment from **Provider-specific behavior can
  become real UI.**, including its background and aspect ratio.
- Multiple images should scroll horizontally, following the existing mobile
  gallery interaction. This changes the earlier simultaneous/stacked-image
  decision, not the six-highlight layout or the rejection of model-family
  selector tabs.
- Align images across each desktop row where practical and avoid the
  disproportionate tall phone image in **Vibe code—or vibe anything.**
- Defer magnification until the later source/composition work.

The maintained reference before the first restoration used a **3:4** image
frame with a border and rounded corners. The restoration let all image
sources use their natural ratios, unintentionally losing that reference
frame. The follow-up restores a shared 3:4 frame for the proof
images/placeholders, with the reference's light/dark background treatment.
The outer editorial highlights stay unframed.

Fixed aspect ratios equalize image heights but cannot align their starting
positions when adjacent descriptions differ in length. The plan therefore
aligns the copy-area height per desktop pair, releasing that spacing on
single-column mobile. Text is not truncated or forced into a fixed number
of lines. Multiple images use native horizontal scrolling with snap positions
and keyboard access rather than a new model-family selector or carousel
dependency.

Use the current source images fitted inside the frame for this review.
Containing a full phone screen alone will not make its small text readable;
the existing focus/magnification pipeline and improved source framing remain
part of task 018's later asset work. No new carousel library, asset
production, or product-popup change belongs to this layout follow-up.

The implemented follow-up shares one `ProofImage` component across the
highlights, provider examples, and supporting galleries. It contains the
complete image within the fixed frame and uses native horizontal scroll-snap
strips for multiple highlight images. Shared grid rows align the paired
copy areas and media without imposing that spacing on single-column layouts.
Both themes and all five review widths pass browser geometry/overflow checks;
keyboard, pointer, and Chromium-emulated mobile touch scrolling also pass.
User visual acceptance remains pending. The current research image still
needs the later source/callout work for readable detail.

### Integrating the supporting evidence — two layout proposals

Status: Solution B selected and implemented in task 018; visual review pending.
The user accepted the
planned gallery visuals but asked that they belong to the feature highlights.
They requested two proposals, allowing a compact grid or a mixture of compact
and full-width highlights. Those proposals were recorded before the later
selection and implementation below.

Both proposals move the evidence into these owners:

- **Replace the parts you disagree with:** Session actions, Message actions,
  and Session list config-to-UI compositions.
- **Transparency by design:** compiled instructions, Cost report with useful
  usage metadata, and ChatGPT usage report.

The headings **See what goes into each session** and **Your plugins shape the
controls**, and their standalone section entries, are removed when their
content moves. They were an agent-proposed layout choice, explicitly included
in the earlier approved plan, rather than independent user requirements.
Their descriptions remain usable as image labels above the owning frame.

**Solution A: six compact highlights.** Preserve the current order:

| Row | Left | Right |
| --- | --- | --- |
| 1 | One workspace for every model family | Replace the parts you disagree with |
| 2 | Transparency by design | Work from anywhere |
| 3 | Vibe code—or vibe anything | Sessions become workspaces |

Each feature uses one 3:4 image frame, horizontally navigable when it contains
multiple images. This is the smallest restructuring and preserves the
established reading order. Its limitation is the available width for detailed
code/menu/report evidence.

**Solution B: four compact and two expanded highlights.** First show model
families beside work-from-anywhere, then vibe-anything beside session
workspaces. Follow the grid with full-width **Replace the parts you disagree
with** and **Transparency by design**, then Getting Started.

The expanded sections use their existing feature titles and appear once,
without duplicate compact cards. Reuse existing full-width section patterns.
Propose one large 16:9 desktop image area per expanded feature, with its
three images navigable, returning to 3:4 on phones. This changes both order
and desktop proportions and requires explicit selection of Solution B.
It gives the denser evidence more room but lengthens the feature group and
adds a responsive image shape. Mobile legibility still needs reviewed assets.

A two-item grid followed by four expanded features remains a viable variant,
but is not the proposed mixed default: research/workspace images would also
gain a large footprint, pushing Getting Started farther down.

Shared refinements requested before the pause apply to either solution:

- match the **whole** provider-example card: outer themed surface, padding,
  border, rounded corners, and inset image area; retain prominent titles;
- keep native image scrolling, add left/right chevrons and bottom dots inside
  multi-image frames, and synchronize the active dot with scrolling;
- allow dots to select images; disable chevrons at the first/last boundary;
  keep keyboard/reduced-motion support, independent groups, and no autoplay;
- remove snapshot links, scroll hints, and captions beneath images; place any
  useful short label above the frame and keep switching height stable;
- preserve paired-row alignment and ordinary single-column mobile spacing;
- use existing captures and descriptive placeholders for the next layout
  review; defer magnification, product improvements, and new source capture.

The initial recommendation was A for minimal restructuring. The user chose B:
the first four features are end-user-oriented, while the two expanded features
serve readers who want deeper inspection. Both arrangements remain viable;
do not treat the selected order or extra desktop space as permanent.

The implementation keeps all six feature definitions in one YAML list. List
order controls reading order; per-item `layout: full-width` selects the wide
desktop span and image frame. Returning to A needs only reordering that list
and removing the two full-width settings. An isolated build verified A at
desktop and phone widths with no component/source difference other than
`home.yaml`; the live review remains B.

The first B implementation wrapped whole features in outer cards and put
both controls inside the image frame. The user corrected that interpretation
in the following review, recorded below. The two added gallery sections are gone;
their planned visuals are preserved inside the plugin/transparency features.
Current images and placeholders still need the later asset-review work.

The user clarified the worktree boundary: website implementation, tests,
task records, and design documentation belong on main. Specific product
improvements stay on develop for testing before the agreed merge. The prior
split website edits were reconciled onto main and their unchanged pending
copies removed from develop after backup/hash verification. No product or
unrelated research commits were pulled into this layout checkpoint.

### Image-card ownership and control placement

The user clarified that the frame belongs to each **image**, with an optional
image-specific title and description at the top of the card. Feature titles
and descriptions remain outside it. This supersedes the whole-feature card
interpretation and restores the value-led, unframed feature copy.

Implemented on main:

- per-image `label` and optional `description` appear above the screenshot,
  inside its own card;
- image cards match the provider-example surface, border, padding, and
  rounding; the existing provider section is not double-framed;
- clickable pagination dots sit below the card;
- chevrons overlay the sides at the screenshot's vertical center, rather than
  the center of the combined caption/image block;
- aligned caption/canvas rows preserve stable image placement across slides
  and neighboring desktop features;
- no snapshot link, scroll hint, or other prose follows the image card.

The selected B arrangement and content-only layout controls are unchanged.
New captions remain reviewable copy, and screenshot sources/magnification
remain for the later asset work. Browser verification passes; final human
visual acceptance is still required.

### First configuration-to-action image — contextual candidate

The reviewed layout remains the baseline in commit `82906d10`; its plugin
highlight starts with a described Session actions placeholder. Preserve that
authored placeholder and the image title/description while reviewing this
candidate through the explicit local preview.

The selected concept connects three actual declarations to three actual rows:
`session-title-app` → Edit title, `generate-title-app` → Generate title,
and `summarize-range-app` → Summarize range. The screenshot uses the production
Desktop conversation and native popup, with data from the real local
backend/SDK path. The JSON comes from that same configuration.

Use a wide desktop image and a portrait image for phones or compact feature
placement, each in light/dark. Desktop keeps configuration left/UI right,
with the owning window visible and a larger real-menu crop. The user accepted
that Desktop composition on October 6, 2026.

The initial phone version also kept code left/UI right. Preserve its source
definition and candidate as an alternative for a wider compact frame;
it is superseded for phones by the review below. Desktop connections are
baked into image pixels; browser markup does not draw the diagram.

Retained alternatives and rationale:

- A single wide image is simpler to maintain, but shrinking it into the
  portrait phone frame leaves small text and unused space.
- A portrait image also suits option A's compact desktop feature. The shared
  renderer selects that source when the content changes the feature layout.
- Tight row crops alone lose application context. Retain them as magnified
  details within the complete relationship image.
- A stacked configuration/UI arrangement gives names more width on a phone.
  It was initially unselected while code left/UI right applied to both
  shapes. The October 6 review selected stacking for the phone image.

The first automated page pass found the capture harness name in the native
window title, mid-word wrapping of plugin identifiers, and a phone carousel
arrow intruding on configuration text. The candidate producer uses the
product title, keeps plugin names together, and positions the compact code
block clear of the side-control band. Connector starts use declaration-row
edges and terminate within the corresponding real controls.

Those candidate refinements led to the accepted first visual. On October 6,
2026, the user accepted Desktop and then approved the revised stacked phone
version described below. Automated geometry/schema/text evidence remains
separate from that human judgment. Further images receive their own review.

### Phone review — stacked declarations and marked popup rows

The user accepted Desktop and requested full-width configuration above an
enlarged popup on phones. Matching colored marker bands replace the phone
connections, which were too constrained by the narrow columns.

The selected phone treatment keeps one valid JSON block at the top, with
translucent, slightly uneven bands behind the declarations. Below it, the
same blue, teal, and purple bands mark their actual native action rows.
The light popup uses multiply blending and the dark popup uses screen
blending so its original text remains legible.

The excerpt retains the real popup header, close button, side edges, and
bottom corners. A visible crop break indicates the unrelated intervening
entries omitted from the magnified view. It uses original screenshot pixels;
no replacement menu or invented action text is drawn. Source segments,
omission bounds, and highlight geometry remain in the asset manifest.

The prior side-by-side phone files and page captures are retained under
`artifacts/plugin-session-actions-review/before-mobile-stacking/`.
That approach keeps spatial connectors and the surrounding conversation
visible, but gives each column less reading space. The selected stack favors
readable declarations and recognizable popup controls. The user approved this
revised phone version on October 6, 2026. It is the selected baseline for
subsequent relationship visuals; final source promotion/publication follows
its separate boundary.

Retain the previous portrait recipe here as a reproducible alternative
independent of disposable capture files. It uses the same source contract and
native images:

```json
{
  "width": 1200,
  "height": 1600,
  "code": {
    "x": 24, "y": 24, "width": 600, "height": 1280,
    "fontSize": 47, "lineHeight": 66, "entryGap": 20,
    "paddingHorizontal": 12, "suffixScale": 0.6
  },
  "context": { "x": 560, "y": 36, "width": 612 },
  "focus": {
    "x": 658, "y": 620, "width": 510,
    "labelOnly": true, "labelInset": 28, "labelWidth": 144
  }
}
```

Desktop's two reviewed derivatives are unchanged and checked against their
stored hashes. The website still uses the same frame, shared renderer, and
content-only layout controls. This revision changes only the portrait
composition and its annotation method.

### Next proof batch — draft after first-image acceptance

The October 6, 2026 request expands the next work from a single Message actions
image to both remaining plugin images and all three transparency images.
The first image's genuine Generate title icon also needs correction:
`sparkles` is not in the Feather set used by either frontend; `zap` is the
proposed supported replacement. The old accepted composition stays the visual
baseline, with real recapture for the changed icon.

Proposed visual coverage:

| Image | Evidence and selected draft treatment |
| --- | --- |
| Actions for each message | Actual Fork/summarize/PDF/Markdown rows. One export declaration branches to two controls on Desktop; those rows share its marker color on phones. |
| A session list that fits your work | Actual pin/archive/status controls, three descriptive sessions with real status and pinned state, and an open native row menu. Phone keeps an enlarged genuine row/control crop below the code so header/action-bar ownership remains understandable. |
| Inspect the instructions | Actual compiled-system action and native text window, with a short readable template-derived result and conversation context. |
| See where costs go | Real cost action over isolated sample SQLite records; readable totals, a project/day breakdown, and related provider metadata. |
| Track ChatGPT usage | Real usage action over an isolated sample journal; estimated totals, remaining limits, resets, and a short history. |

Native report windows and the production display router remain the UI source.
The financial examples carry **Sample data**, and estimates retain their
qualifiers. Desktop uses context plus magnified report detail; phones give the
real window heading and selected readable excerpts more width. Cropped or
separated details must remain visibly excerpts, with all original payloads
and geometry retained. No invented report text, account login, paid model
request, or pasted-over numbers are needed.

Retained alternatives and rationale:

- One image per review was useful while the first composition's phone layout
  was unsettled. With that treatment accepted, the user prefers one combined
  plugin/transparency review to reduce interruption.
- A single wide report reused on phones needs fewer derivatives but makes
  full tables and long text too small in a portrait frame. The proposal keeps
  separate portrait compositions through the existing responsive renderer.
- Popup-only list crops are compact but lose the star/action-bar ownership
  being demonstrated. Preserve the genuine list row and enough menu context.
- A generic fallback for every invalid icon or an icon-library migration is
  broader than the requested defect. Correct the plugin-owned declarations
  used by both frontends first.

These are planned choices, not completed assets. The combined batch requires
plan approval, then one contextual review of the finished local homepage.

### October 7 batch implementation — contextual review pending

The user approved the combined batch on October 7, 2026. All six candidates
now appear in the actual local homepage under the existing two expanded
highlights. This implements the approved direction; it does not record human
acceptance of the new images.

| Image | Implemented treatment and rationale |
| --- | --- |
| Session actions | Genuine `zap` icon from the fixed plugin; recaptured source with the accepted desktop connections and phone marker stack. Preserve the pre-icon files/hashes for comparison. |
| Actions for each message | Three real declarations map to Fork, summarize, and both exports. Desktop branches from the export declaration; phone export rows share purple. Real popup chrome remains, with visible breaks for omitted entries. |
| A session list that fits your work | Actual pin star, archive, and status controls in the production list, with real titles/subtitles and three distinct states. Desktop connects to controls; phone keeps list/menu context above an enlarged marked row. |
| Inspect the instructions | Genuine native report and a complete narrow-window instruction excerpt on phones. The feature resolves `WORKSHOP_GOAL` from its configured template, rather than displaying substituted website text. |
| See where costs go | Native project/provider report on desktop plus real input/cache/completion detail; phone emphasizes recorded totals and daily total columns. Cropped columns and separated excerpts have visible breaks. |
| Track ChatGPT usage | Native report over a synthetic journal; phone crops retain estimated tokens/cost, both current limits/reset times, and both history lines. No reconstructed numbers or labels. |

Retained implementation alternatives:

- A 360px native report was captured for every report. It is useful for the
  compiled instructions but wraps cost numbers/provider names and truncates
  the visible usage history. Keep those original sources; the selected cost/
  usage portraits magnify real wider-window crops instead.
- Shrinking the entire cost table into a phone frame retains every column but
  makes the numbers hard to read. The selected phone crop prioritizes totals
  and daily totals; the desktop source retains project/provider columns.
  A later alternative could use another real scrolled table excerpt if that
  comparison becomes the stronger story.
- Repainting shortened reports or replacing native popups with website HTML
  would simplify spacing but lose the proof's source. Crop/zoom annotations
  preserve the actual UI and expose the omitted parts.
- The list overview supplies context; the enlarged real row supplies the
  color correspondence. Removing the overview would give controls more space
  but make the pin/header/action-bar ownership less clear.
- The first image's layout remains the approved baseline. An icon-only product
  correction changes actual source pixels/hashes, so the earlier files are
  retained rather than claiming byte equality.

Sample semantics are explicit: the cost total of $3.16 combines $1.90 of
recorded OpenAI costs and $1.26 of estimated OpenRouter costs. The cost caption
adds **Sample data. Totals combine recorded and estimated costs.** The
ChatGPT sample shows three requests, 30,600 input tokens, $1.82 estimated
cost, and limits/history from the same timestamped synthetic journal. Its
caption retains **estimated** and **Sample data**.

Capture uses supported `auth_mode: auto` with an unmistakably fake API key
because explicit ChatGPT mode requires a saved login when creating a real
provider session. The existing read-only usage action supports auto mode;
all credential/journal paths are isolated and no credentials file or inference
request is used. This is a capture-fixture adjustment, not a product-auth
change or evidence that the sample represents a real account.

The native producer exercises public HTTP, the production SDK and list/chat
components, the display router, and real menus/windows. Composition manifests
retain exact payloads, source hashes, geometry, and crops. The homepage flag
`CRYSTAL_PROOF_BATCH_PREVIEW=1` applies only these six local candidates.
Wide/portrait and light/dark files use the existing renderer. Reviewed public
masters, normal homepage YAML, and publication remain separate.

The final review should compare the two sections together on desktop and phone:
whole action names, recognizable popup/window identity, correct colored
relationships, list context versus detail, and meaningful report crops. Browser
screenshots, OCR, and geometry are supporting evidence; human visual acceptance
remains open. Other feature assets follow after this combined review.

Verification retained with the candidates includes the successful native
HTTP/SDK/window run, 11 focused page cases across the five widths/both themes,
9 existing feature/theme regressions, and 60 section screenshots. Asset/source,
generated-fixture/consumer, content, and both app type checks also pass.
Screenshots live under `landing_page/artifacts/proof-batch-review/page/`;
the local review is the actual homepage, not a separate review package.

One raw-source finding is preserved for later investigation: the unobscured
sample footer shows both cost-label variants despite its seeded API-key
metadata. The selected enlargement uses genuine input/cache/completion fields;
financial values are evidenced by the actual report. Do not treat this capture
as verification of ordinary footer condition handling or silently change the
product while revisiting the composition.

### October 7 review correction — simpler plugin coverage

The user selected only **Session actions** and **Actions for each message**
for the plugin highlight; those two images provide enough coverage there.
Remove **A session list that fits your work** from that carousel, retaining its
native inputs and recipe as an unselected alternative. The separate workspace
highlight still owns its previously planned session-list proof.

The user also removed the entire **Serious users eventually disagree with the
harness.** section (`everything-replaceable`). Its prior direction used the
**Everything is replaceable** eyebrow, explained providers/extensions/features/
tools/application actions/UI as plugin surfaces, and included six illustrative
code cards. The retained upper plugin highlight now provides the Plugins
navigation destination. This removal follows the user's explicit request;
the code-card presentation remains historical rather than current guidance.

The user flagged a visible problem in the Transparency compositions and asked
for direct image inspection. Earlier source, native-window, browser, geometry,
and OCR checks did not constitute visual verification. The report images remain
unaccepted, and their exact visual defect is pending inspection rather than
inferred from those automated checks. In this environment `view_image` requires
a full filepath supplied by the user; capture screenshots alone do not satisfy
that tool condition. Do not label image review complete until it is performed.

### October 7 direct visual inspection and report correction

The user supplied the full paths of the three desktop/light page screenshots.
`view_image` inspection confirmed the defect: the context screenshot already
contained its report window, and the composition placed another copy beside it.
The compiled image magnified a mostly empty pane, the cost screenshot had a
clipped viewport and detached metadata strip, and the usage image gave an empty
date form prominent space. Automated source/size/OCR checks had passed without
detecting that poor composition.

Selected correction:

- Use the genuine unobscured conversation capture as context.
- Show one enlarged native report excerpt. Retain window identity, its Close
  control, real text, and an explicit crop break; remove blank window canvas
  and the unused usage form from the excerpt.
- Connect the cost token/cache/completion enlargement to an outlined source
  row so it reads as a magnification rather than an unrelated strip.
- Keep section/card/frame layout and the existing phone derivatives. This is
  a Desktop composition correction, not a product-window or report-data change.
- Frame page review screenshots below the sticky header so the feature title
  remains visible.

The regenerated three desktop/light screenshots were inspected again with
`view_image`: duplication and oversized blank panes are gone, report text is
larger, and the metadata's origin is visible. The cost image remains a genuine
scroll-viewport excerpt; a complete seven-day table would require another
native scroll capture. That continuation option remains viable, without
silently painting rows or altering the production 420px body cap.

The prior recipes, report derivatives, manifests, and page screenshots are
preserved under
`landing_page/artifacts/proof-batch-review/before-report-correction/`.
Retain the original two-report treatment as a rejected direction, not a future
default. Prefer unobscured context plus a single useful report. A smaller
context image, report-only image, or an additional real scrolled detail remain
alternatives if the image needs further refinement.

User-provided paths can be reused to inspect regenerated screenshots during
this task; no repeated permission is needed. Direct image inspection is part
of review, separate from browser/source checks and final human acceptance.
Only the supplied desktop/light paths were visually inspected in this pass.

### October 8 illustrative reporting and visible System message

The user chose one focused image combining daily costs and ChatGPT usage,
keeping the compiled-instructions image separate. The earlier two financial
slides and their genuine scroll captures remain alternatives, not the selected
delivery. The new display may be supplied by a capture-only fixture plugin;
its data and two-decimal formatting do not change permanent production plugins.

Selected sample:

| Day | claude | zai |
| --- | ---: | ---: |
| Oct 6 | $28.40 | $3.20 |
| Oct 7 | $43.25 | $7.45 |
| Oct 8 | $36.10 | $5.60 |

ChatGPT uses an illustrative seven-day capacity equivalent of approximately
$550. Three days since reset move from 0% to 40%: +40 percentage points and
$220.00 estimated usage. That equivalence is a user-stipulated screenshot
assumption, not an OpenAI price or billing claim. All such captions keep sample
wording and the assumption explicit.

The compiled action reads the beginning of the public Codex default, checked
October 8 and pinned to model-catalog revision
`d63a9b8344cfe58bc78bbe319b560378fc8756ef`. Its provenance and excerpt are
maintained under `visual_assets/runtime/proof-batch/`. The real feature still
performs the compilation. This does not update product model defaults.

The Vibe story retains a first System message, an attachment-based User request,
and initial Assistant reasoning without tool calls. The prior source already
contained System, but viewport/copy length hid it. Shorter illustrative copy,
full-history capture, and normal navigation make the intended context visible.
OpenAI-only controls are omitted from this Z.ai capture fixture.

All homepage screenshot comments now identify the pictured plugin surfaces and
their adaptability. Agent, instruction, action, status, and report wording is
specific; it does not claim that every hard-coded client-shell element is a
replaceable plugin.

The tool now allows direct local `view_image` inspection without user-supplied
paths. Use that routinely after generation; the October 7 path limitation is
obsolete. Preserve failed and prior versions, and distinguish build/source/
native/visual evidence. The Mac was subsequently unlocked and the selected
Desktop capture passed through HTTP, the production SDK, and the native UI.
The selected iOS capture also passed both themes with all three role frames
contained in the transcript viewport.

The current candidates are bound to the actual homepage preview. Direct
`view_image` inspection covers both transparency images and Vibe at 1440px
and 390px in both themes, plus the combined report at 320px. The combined
report keeps all three daily rows, both named buckets, the three-day interval,
$220.00, and 0% → 40% / +40 percentage points visible together. The Codex
portrait preserves the complete selected paragraphs; its text is deliberately
dense at phone size and still needs human judgment of legibility. Light-theme
Vibe reasoning retains the application's subdued production color.

Image inspection caught surplus blank native window area below the wide Codex
text. Trimmed that native crop to 390 points and the combined report to 500,
preserving window chrome and the visible crop marker. Portraits use genuine
narrow windows, with complete text/data rather than repainted labels or
duplicated panels. These are local composition choices within the approved
frames, not a change to the section layout.

Verification passed: the combined Desktop public/native producer, selected
iOS native capture, 15 actual-page responsive cases, 25 asset-pipeline tests,
8 content tests, 2 report/provenance tests, 4 mobile harness consumer tests,
source/derivative checks, and normal/candidate builds. LAN delivery matches
all 18 active candidate derivatives. The initial preview build retained
placeholders because its freshness check derived paths from a bundled module;
passing the package root from the actual page loader fixed that consumer.

The pre-October-8 content/captures and the former separate financial recipes
remain alternatives for later comparison. Human contextual acceptance,
another commit, source promotion, and publication remain pending. Review at
`http://192.168.8.10:4182/#feature-transparency` and
`http://192.168.8.10:4182/#feature-vibe-anything`.

## Responsive Multi-Frame Walkthrough Decision — October 16, 2026

The earlier H3 walkthrough used one composite image per chapter and hid the
other chapters behind the same interaction on Desktop and mobile. It remains
recoverable in commit `b2a06b40`. Human review rejected that model because
mobile visitors had to operate a carousel to discover primary explanatory
content, chapter copy was split around the image, and the Session settings
composition tried to teach the Agent picker, provider settings, and Plugins
window at once.

The selected replacement keeps one semantic order with two responsive
presentations:

- mobile and no-JavaScript rendering expose every chapter and frame through
  ordinary vertical scrolling;
- Desktop progressively enhances the same content into named chapter tabs and
  one focused image at a time;
- image-edge arrows move through all frames, chapter labels jump directly, and
  dots plus an `n of m` label show progress inside the active chapter;
- there is no autoplay or swipe-only content;
- the screenshot alone owns the visible frame, with an image title above and
  visitor-facing caption below.

The teaching order is Compose, Messages, Session actions, Session settings,
Workspace, and Connections. Their frame counts are 2 / 2 / 2 / 3 / 2 / 2.
Connections is now part of the conceptual introduction because the separation
between client and runtime materially distinguishes the product. Getting
Started still owns local discovery, address/port, bridge setup, availability,
and trusted-network instructions.

One frame teaches one relationship. Session settings therefore uses separate
Agent, provider-settings, and plugin-feature images. The first Compose frame
shows the familiar conversation and message field, while its second frame
shows active request controls. Message metadata and Message actions are
separate. Session action stars receive their own focused frame. Workspace task
status and runtime request state remain explicitly distinct.

The captions address a first-time visitor. They say what relationship to
notice and why it matters; they do not discuss fixtures, candidates, crops,
review status, or what an image proves. The current Plugins frame describes
visible plugin features only; tools remain visible in the Agent-profile frame
rather than being claimed in a screenshot that does not show them.

The genuine Desktop Connections panel did not have a retained website source.
The first Connections frame therefore uses the genuine Desktop Sessions header
that names `Local workspace` as the focused connection. This is a truthful
first-release explanation of which runtime supplies the list and can later be
replaced with a dedicated Connections capture without changing the component
or chapter model.

The thirteen-frame component, copy, crops, and responsive rhythm remain at the
H3B human in-page checkpoint. No source promotion or public binding is implied
by this implementation.

## H3B Walkthrough Content Review — October 16, 2026

Human review accepted the Desktop staged layout and mobile vertical reading
model. It rejected the current content as final. The next revision keeps the
component behavior and changes only titles, copy, frame selection, source
captures, and image processing.

The accepted copy direction is direct interface naming rather than
action-oriented marketing language:

- Composer;
- Messages;
- Message actions;
- Message metadata;
- Session actions;
- Session settings;
- Agent profile;
- Provider settings;
- Plugins;
- Workspace or Session list;
- Connections or Connection methods.

The current first Compose frame and its caption do not communicate one clear
idea. Replace them with one genuine unsliced chat screen: conversation above,
composer at the bottom, and readable model, reasoning-effort, and web-search
controls. Explain that the selected provider and plugins contribute those
controls and can add others. Introduce the shared star/pinning convention here.
Remove Composer actions from the introductory sequence while retaining the
candidate and verified lifecycle semantics for later advanced use.

Messages should use a contextual Desktop Message actions image first, with the
selected response and real popover visible together. Message metadata follows
as a second image attached to a visible response.

The message-footer image must reuse the maintained processing boundary behind
the lower-page **Usage and cost transparency** item. That item is catalog asset
`provider-usage-cost`, which uses `capturedImageLifecycle` and
`focusCalloutPipeline` over a genuine response plus magnified genuine footer.
The walkthrough may share the existing asset only if fixture, meaning, and
responsive placement fit. Otherwise add a separate catalog asset through the
same lifecycle and pipeline. The rejected ad hoc stack of detached footer
excerpts is retained only as comparison material.

Session actions should use one contextual image; a second crop of the same menu
is redundant once the star convention is understood. Session settings keeps
three images but must enlarge important text. Plugins remains conceptually
accepted. The Desktop focused-connection frame is removed.

The recommended next comparison uses approximately nine frames:

1. Composer;
2. Message actions;
3. Message metadata;
4. Session actions;
5. Agent profile;
6. Provider settings;
7. Plugins;
8. Session list;
9. Mobile connection methods.

The separate Workspace-status image is a recommended cut because one coherent
session list can show title, subtitle, pin, durable status, and current request
state together. Its removal and the exact section heading remain subject to
the next in-context human checkpoint.

## Revision Procedure

When a section does not work in context:

1. Start with the alternatives preserved here.
2. State whether the problem is value clarity, title rhythm, body accuracy,
   proof composition, or responsive layout.
3. Compare at least the selected version and one viable alternative in the
   real page.
4. Record the new decision and rationale here.
5. Preserve the replaced version when it remains credible enough to test
   later.