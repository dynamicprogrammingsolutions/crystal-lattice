# Produce Homepage Proof Visuals And Supporting Product Improvements

Parent Task:
`tasks/20260930-homepage-getting-started-and-waitlist/000-main.md`

Depends On:
`tasks/20260930-homepage-getting-started-and-waitlist/015-homepage-content-assets-layout.md`

After the selected homepage copy and download layout are approved in context,
make the real product improvements and reviewed capture fixtures needed to
produce truthful proof for all six highlights. Keep screenshot-specific
ordering or hiding separate from durable product behavior until its ownership
is explicitly decided.

## Requirements checklist

- [ ] The six feature themes remain between the hero and Getting Started,
      each ordered title, description, then images. Two-column portions stack
      on phones. The user chooses between an all-six grid and a mixed layout
      before implementation; no layout is changed implicitly to fit assets.
- [x] Option B presents four end-user-oriented compact features followed by
      two full-width features for deeper inspection. Order and compact/full
      placement are content-configurable so option A or another arrangement
      needs no component rewrite or duplicated feature copy.
- [ ] The planned content from "See what goes into each session" and "Your
      plugins shape the controls" belongs to the transparency and replaceable
      parts highlights respectively. Remove those two standalone sections
      without dropping their planned visual evidence.
- [x] Highlight image areas and placeholders reuse the frame, background, and
      treatment of "Provider-specific behavior can become real UI", with
      3:4 compact/phone frames and 16:9 expanded desktop frames in option B.
      Multiple images use horizontal scrolling on desktop and mobile instead
      of vertical stacking. Image frames in each desktop row align where
      practical despite different description lengths; mobile releases the
      paired-row spacing.
- [x] Each image owns the provider-example card treatment, including optional
      image-specific title/description above its inset screenshot canvas.
      Feature-level titles/descriptions remain outside the card. Multi-image
      groups have chevrons overlaid at the screenshot's left/right center and
      position dots below the card, synchronized with scrolling. No snapshot
      link, scroll hint, or caption is appended beneath the card.
- [x] Configured agents support a user-facing title, description, and explicit
      order in addition to the stable agent ID, and that metadata reaches the
      public backend/SDK/Desktop picker without breaking existing string-ID
      consumers.
- [x] The agent picker presents ordered title/description rows while retaining
      stable IDs for submission, session metadata, APIs, and compatibility.
- [ ] Desktop agent selection is a real consolidated two-pane window: the
      ordered agent list remains on the left and the selected agent's effective
      default provider/extensions/features/tools appear on the right before a
      session is created or switched.
- [ ] A read-only public backend/SDK contract supplies effective agent-profile
      plugin entries without creating a temporary session, exposing secrets,
      or changing stable agent/session IDs.
- [ ] Highlight 1 has two images accessible through a horizontal image strip,
      without Codex/Claude selector tabs:
      Codex with apply patch, shell, and image viewing; and Claude with
      read/write/edit/glob/grep/bash-style tools. The compact real picker keeps
      the broader model-family list visible; irrelevant plugin categories
      may be hidden for capture.
- [ ] Highlight 2 uses ImageMagick-composed relationship images, not live
      HTML/SVG connections on the website. Desktop has one readable
      multi-plugin JSON block on the left and real application UI with visible
      background on the right; lines connect declarations to their controls.
      Mobile stacks the full-width JSON block above a magnified, recognizable
      native popup excerpt and pairs declarations/actions with matching
      translucent row highlights, without connector lines.
      The primary Session actions image shows
      at least three plugins and three actions; additional requested examples
      include Fork/share message actions and pin/archive/status list controls.
      Plugin names and action labels must remain visible at page size.
- [ ] Highlight 3 uses the real **Show compiled system message** session action
      and the real **Show cost report** action contract. It combines compiled
      instructions, provider usage metadata, and deterministic synthetic cost
      records using the established magnification/callout treatment without
      implying uniform provider metadata or real company spending. Add the
      real ChatGPT usage report, use readable sample amounts and short bucket
      names, and keep usage estimates distinct from billed costs.
- [ ] Highlight 4 is one reviewed composite image—not two independent images—
      with a recognizable Desktop frame and a phone frame. Both clients show
      the same title, subtitle/status/agent, latest prompt, and answer so
      continuity is immediately visible.
- [ ] The light-theme user-message foreground is corrected as a product fix:
      dark text is used on the light blue user bubble while dark-theme contrast
      remains light-on-dark across both maintained Markdown renderers, raw
      message text, and applicable attachment/message affordances.
- [ ] Highlight 5 uses the selected GLM-5.3 through Z.ai capture state and
      shows the system message, a non-development user request, and expanded
      initial reasoning together. The request naturally requires file/web/tool
      work; the screenshot stops before tool calls and neither the prompt nor
      reasoning uses the phrase **tool-heavy**. The capture's model/provider
      choice is not an external website heading.
- [ ] The session-pinned plugin keeps the star in the header but changes its
      action-bar `default_pinned` value to `false`; the session-status plugin
      changes its rich status action defaults to pinned. Existing stored user
      preferences remain authoritative and are not force-migrated.
- [ ] Highlight 6 shows the corrected production defaults with exact
      session-status, session-pinned, and session-title plugin contracts:
      `todo`, `in_progress`, and `done`; pinned and unpinned sessions;
      descriptive titles/subtitles; one visible pin star per row; and the
      archive and status actions present in the action bar. A Desktop list
      screenshot includes the action popup open without obscuring the list
      evidence. A second Desktop screenshot shows message actions and
      highlights Fork here, Delete from here, and the renamed compaction row.
- [x] The old "Treat sessions as workspaces, not disposable chats" section
      is removed or merged into the workspace highlight; it does not repeat
      the same feature pitch as a separate section.
- [x] The message action currently labeled "Compact native history up to here"
      is renamed "OpenAI compaction up to here". Action popups and other
      popups sharing their menu design allow one line break (two lines) on
      both Desktop and mobile so complete action names remain visible.
      Desktop popup sizing accommodates these rows. Action IDs, dispatch, scope, provider eligibility,
      confirmations, and saved action preferences remain compatible.
- [ ] Website copy and captions serve visitors. Remove capture objectives,
      technical fixture/provenance labels, the external GLM/Z.ai capture
      heading, and "default-pinned" terminology. Sample financial/usage values
      may use the plain label "Sample data"; internal provenance stays in
      developer records.
- [ ] Published Desktop captures use a deterministic standard blue accent
      similar to mobile, not the operator's personal macOS accent color.
- [x] Website claims and captions are reconciled with the accepted draft
      compatibility baseline now maintained under
      `landing_page/research/current-product-and-compatibility-baseline/`,
      preserving Available, Conditional, Optional, and Planned distinctions
      and the non-upstream compatibility disclaimer.
- [x] Every screenshot-specific hide/reorder behavior is explicitly classified
      as a real product improvement, a maintained capture fixture/plugin, or a
      one-off candidate aid before implementation.
- [x] Capture-only behavior does not silently alter production defaults or
      misrepresent unavailable product capability.
- [ ] Light/dark proof variants, alt text, dimensions, compression, content
      bindings, and freshness triggers are maintained through the visual asset
      framework.
- [ ] Final proof assets, claims, and layout receive human approval on the
      actual responsive website before final source promotion or publication.
      Previously implemented product prerequisites may be reconciled onto main
      for website use at the explicitly approved checkpoint. Other product
      integrations retain their review gate; waitlist work follows its
      separately approved scope.

## Current approval boundary and questions

The reviewed Solution B website layout is committed on main as `82906d10`
(`Refine homepage feature visuals`). Four compact features serve end users;
two expanded features support deeper inspection. Order and width remain
content-configurable. Frames belong to individual images, with optional
image-specific headings above the screenshot, dots below the card, and
chevrons over the screenshot sides.

The user authorized the next product checkpoint on develop: two-line names
in shared Desktop/mobile popups, measured Desktop action-popup sizing, and
the message label/confirmation title **OpenAI compaction up to here**.
Implementation and verification are complete for this checkpoint, including
macOS and iOS native checks. On October 6 the user authorized its commit and
requested a plan for the next step. The popup checkpoint is committed on
develop as `9e053402` (`Improve action menu readability`).

The user subsequently approved correcting the next plan to reconcile the
three pending capture files and their required earlier changes onto main
first, then proceed with the Session actions image. Checkpoint 3 is
**Approved**, with another human review stop before the remaining images.
Reconciliation is authorized; a new implementation commit or publication is
not part of this instruction.

Checkpoint 3 is implemented, verified, and accepted by the user on Desktop
and phone. The first Session actions image is the approved baseline on the
actual local homepage; remaining image slots retain their previous state.
Review at `http://192.168.8.227:4182/#feature-plugins`.
No new commit, push, source promotion, or publication has occurred.
The three migrated capture edits are cleared from develop; unrelated work
there and the unrelated parent/waitlist edits on main remain separate.

Latest review: the user accepts the Desktop composition and requests the
mobile revision described above. This revision is authorized on main.
Retain the accepted Desktop image bytes. Keep real popup chrome in the phone
excerpt, use matching physical-marker-style colors on its real rows and the
code declarations, and stop for review after updating the actual page.
No new commit or publication is authorized.

The user approved the stacked phone revision and asked for a next-step
proposal. The current Desktop images remain byte-identical to their accepted
versions. Record that human acceptance without claiming a `view_image`
inspection, which was not performed. Checkpoint 4 below is **Draft**;
new-image execution awaits approval of the next plan. The user subsequently
authorized a scoped commit of the accepted checkpoint; the requested broader
image batch and invalid-icon correction will be planned after that commit.

The bounded reconciliation includes the agent-default preview (`ebb053ac`),
pin/status defaults (`2bfaf03c`), user-message contrast (`4fab5568`), capture
theme (`7d46556b`), the Desktop/mobile portions of visual candidates
(`29604c23`), and the popup checkpoint (`9e053402`). The defaults/contrast
changes are prerequisites of the maintained capture fixtures and theme.
Exclude the obsolete standalone review-package changes in `29604c23`.
Then transfer the pending Desktop harness, compact agent-picker spacing,
and mobile capture-save edits, verify their contents and behavior, and remove
only those transferred pending edits from develop. Preserve unrelated changes
and commits. The reconciliation is left reviewable on main without creating
a new commit; preserve patch backups and a source-commit manifest.

Approved decisions:

1. Keep all six feature themes and their planned evidence before Getting
   Started. Integrate additional visuals into their owning highlights.
   The former standalone-gallery placements are superseded by this request;
   choose the grid/full-width distribution from the two proposals below.
2. Use **OpenAI compaction up to here** for the message action and its
   confirmation title. Retain the existing OpenAI-only eligibility.
3. Support two-line action labels across the shared Desktop/mobile popup
   design, including other menus using that design.

Review checkpoints: (1) website layout; (2) product popup/label fixes;
(3) first three-plugin composition on the page; (4) remaining sources and
page integration; (5) final asset acceptance. Stop at each important point so
the user can review and authorize the next work and commits. The existing
main-merge and publication boundaries still apply.

The latest layout feedback explicitly supersedes the earlier stacked,
simultaneously visible picker-image decision. Ordinary horizontal image
scrolling is requested; the model-family selector tabs remain rejected.
Magnification/callout work is deferred to this task's later asset-production
steps and is not part of the layout follow-up.

Selected material choice: Solution B, with four compact features followed by
the plugin and transparency features at full width. A remains a retained
content-only alternative. Do not add user-facing audience labels or rewrite
the approved copy merely to reflect the end-user/deep-reader distinction.

Worktree rule clarified by the user: all website implementation, task records,
and design documentation belong in
`/Users/ferenci84/Dev/Mine/ai-agent-platform-main` on `main`. Specific product
changes belong on `develop` for the user's testing, then merge to main at the
agreed confirmation boundary. Reconcile this task's earlier pending website
changes onto main without carrying unrelated work or unconfirmed product
changes. Future website work must not be split between these worktrees.

Implementation must stop and ask before changing an approved section layout,
moving/removing additional sections, broadening product behavior, changing a
public contract, or using a different screenshot concept to make a difficult
capture easier. Local crop, spacing, sample-value, and line-coordinate tuning
within the approved design does not require repeated approval.

## Current repository and inspection findings

- Website implementation, tests, task, and durable decision record are now
  maintained in the `main` worktree:
  `/Users/ferenci84/Dev/Mine/ai-agent-platform-main`.
  Product work remains on `develop` in
  `/Users/ferenci84/Dev/Mine/ai-agent-platform` until confirmed and used by
  the website. This task's pending website edits were backed up, reconciled
  onto main, and removed from develop after hash checks. Product capture
  harness changes remain on develop. Unrelated work is also present; do not
  reset, stage, or rewrite it.
- Before the first restoration, `FeatureShowcase.astro` switched content to one
  full-width row per highlight when media exists. `FeatureVisual.astro`
  introduces tabs, live SVG connectors, and technical captions. These are
  rejected design choices, removed in the first restoration rather than
  accepted as new baselines.
- `ScreenshotGallery.astro` already supports titled/described image entries,
  two/three-column galleries, theme images, and a narrow-screen scroll
  presentation. `ActionGuide.astro` owns the established bridge section.
  Reuse these presentation patterns; do not invent another section system.
- Verified primary relationship mappings:
  `session-title-app` → Edit title; `generate-title-app` → Generate title;
  `summarize-range-app` → Summarize range.
- Verified message mappings:
  `session-actions-app` → Fork here / Delete from here;
  `message-export-actions` → Share as PDF / Share as Markdown;
  `summarize-range-app` → Summarize messages up to here.
  The export package registers separate PDF and Markdown plugin classes, so
  one package declaration can truthfully branch to both contributed actions.
  No plugin consolidation is needed.
- Verified list mappings:
  `session-pinned-app` → header star; `session-archive-app` → Archive/restore
  session; `session-status-app` → Set status. Archive already declares
  `default_pinned: true`; status does too on current `develop`. Keep the
  existing saved-preference behavior.
- Main still has the previous fixed-width, one-line popup implementation.
  Develop commit `9e053402` supplies the verified measured width, actual
  content height, and two-line names. Its integration is a proposed
  prerequisite for the next capture on main, not a screenshot-only substitute.
- `openai_responses_native_compaction_app.py` owns the compaction row and
  confirmation label. The operation remains gated by the
  `ext:openai_responses_native_compaction` capability.
- `chatgpt-auth-app` already renders `show_usage_report` from its usage
  journal. It reports estimates, limit percentages/reset times, and percent
  history; it is not an account invoice. Its supported report path can use
  an isolated sample journal without accessing a personal account.
- The Desktop capture currently exports its main content view. Native
  `NSPopover` windows are separate surfaces: the revised producer must capture
  them together with their owning window, at their real on-screen positions.
  Existing XCUITest popover tests and application screenshots are relevant
  production capture boundaries.
- Earlier work reported a clean macOS producer/Hermes startup problem and a
  stale `mobile-workbench` runtime fixture. Treat both as unresolved inputs
  to verify, not as permission to bypass real UI or weaken catalog checks.
- The attached October 5 reference images establish readable popup rows,
  native popup context, and report composition. Do not reuse their private
  session text, paths, usage totals, or account details as website data.
- October 6 inspection: the Desktop producer currently handles agent-picker
  and continuity scenes, and exports only `window.contentView`; it does not
  capture a separately owned native Session actions popover. Its shell helper
  also clears the whole output directory and uses `pkill` before launching.
  The new selected-scene producer must preserve other candidates and touch
  only processes it starts. The successful October 5 XCUITest popup capture
  provides a maintained native route to extend.
- `ProofImage` already selects the approved frame ratios, but `ThemedImage`
  currently selects only light/dark sources. Distinct wide/portrait
  compositions need an optional responsive source binding; existing images
  must continue working with their current fields.

## Prior approved decisions

### Agent metadata contract

Historical starting point: `/agents` and `frontend-sdk.listAgents()` exposed
string IDs, and the Desktop picker rendered those strings. Title, description,
and order required a public compatibility design.

Recommendation:

- preserve `listAgents(): string[]` temporarily for compatibility;
- add an agent-descriptor endpoint/method returning
  `{id, title, description, order}`;
- let new clients prefer descriptors and fall back to string IDs;
- keep IDs authoritative for session creation/switching and persistence.

This contract was approved and implemented before the October 2 visual review.

### Screenshot-specific row selection and ordering

Options:

1. **Real product improvement**
   - Add user-facing hide/order controls for settings or plugin rows.
   - Best when ordinary users need the capability.
   - Highest API, persistence, UX, and testing cost.
2. **Maintained capture-only UI plugin/fixture**
   - A deterministic plugin contributes or orders only the rows required by the
     reviewed screenshot fixture.
   - Truthful when the screenshot demonstrates real plugin extensibility.
   - Must remain clearly test-owned and not change production defaults.
3. **One-off candidate aid**
   - Temporary local-only code or data used to explore composition.
   - Cannot be promoted as reviewed proof unless replaced by a reproducible
     maintained source.

The approved rule remains: prefer real product improvements when ordinary
users benefit; otherwise use a maintained capture-only plugin/fixture. Do not
promote one-off candidate aids.

## Proposed visual set — October 5 revision

### 1. One workspace for every model family

Two independent compact Desktop captures below the title and description,
accessible through a horizontally scrolling image strip on desktop and mobile.
Use the same fixed frame for each slide, without model-family selector tabs.
The agent list retains the
other configured families. A maintained capture option shows only Tools in
the right pane and removes unnecessary empty space. Production new-session
and switch-agent windows retain all effective plugin groups.

### 2. Replace the parts you disagree with

Primary image: one JSON block on the left listing session title, generated
title, and range-summary packages; full contextual Desktop Session actions
capture on the right; three baked red connections to Edit title, Generate
title, and Summarize range.

Two additional images reuse the same composition:

- Message actions: session actions → Fork here; export package → both sharing
  rows; range-summary package → Summarize messages up to here. This provides
  three package declarations and at least four matched action rows, including
  the one-declaration-to-two-actions example.
- Session list: pin, archive, and status packages → the top-right star and the
  archive/status controls. Keep the list and open action popup in context.

Generate these as complete image files with ImageMagick. Playwright may
rasterize syntax-highlighted JSON as an intermediate input. Use valid loader
syntax, soft wrapping at path boundaries, and legible package names; do not
truncate strings or fabricate shorter unsupported package identifiers.

All three images belong to this highlight, in one horizontally navigable
image area. Remove the separate `plugin-action-examples` section after
transferring its descriptions and pending visuals.
Retain provider authentication/flex/reasoning proof in the existing
`native-provider-features` section.

### 3. Transparency by design

Use three images in this highlight's horizontally navigable image area,
replacing the compact combined placeholder and the separate
`transparency-details` gallery. Keep the meaningful per-image labels and short
descriptions above the frame when useful:

- **Inspect the instructions** — See the system message assembled for a
  session.
- **See where costs go** — Compare recorded costs by project and provider.
- **Track ChatGPT usage** — See estimated usage and remaining limits for
  connected ChatGPT sessions.

These are proposed supporting captions, not replacements for the six chosen
highlight titles/bodies. Prefer real Desktop report windows to narrow mobile
tables. Seed short bucket/project names and meaningful sample activity across
several dates; generate totals through the real report actions. Use "Sample
data" where needed. Retain "estimated" and provider-specific qualifiers.

### 4. Work from anywhere

One composed Desktop/phone image with matching title, state, prompt, and
answer. Source both clients from one shared session fixture: current separately
authored Desktop/mobile excerpts are not sufficient evidence of an exact
match. Remove the "Same session · title · status · agent…" instruction label.
The repeated visible content and device frames convey continuity.

### 5. Vibe code—or vibe anything

One real non-development conversation showing the system message at the top,
the user request below, and initial expanded reasoning before tool calls.
Shorten the sample text and adjust capture framing so all three are visible.
The GLM/Z.ai choice remains fixture provenance and ordinary app identity;
remove the external technical model/provider heading from the website.

### 6. Sessions become workspaces

Two Desktop images in the same horizontal image-strip treatment below the
existing highlight title/description:

1. The session list with descriptive titles/subtitles and pinned/unpinned
   sessions, visible archive/status action-bar controls, and the actual row
   action popup open. Show the readable options from the reference, while
   preserving list evidence around the popup.
2. A conversation with the real Message actions popup open. Subtle baked
   emphasis identifies Fork here, Delete from here, and the approved renamed
   compaction action. Show complete labels, not an isolated fabricated menu.

Use ordinary labels such as **Organize your sessions** and **Control the
conversation** above the frame only if useful. Keep the existing explanation that behavior is
plugin-driven and can be disabled, replaced, or refined.

Remove the duplicate "Treat sessions as workspaces, not disposable chats"
pitch after its useful controls are represented here and provider settings
remain covered in their existing section. Preserve the existing snapshots
image/source and the existing mention of snapshots in the workspace copy;
do not silently discard the recovery capability or create another workspace
pitch. Proposed anchor handling: move `session-workbench` to this highlight
so existing links still reach the same subject.

## October 2, 2026 visual review outcome

The first candidate set is retained as design history but is not approved for
promotion or homepage binding.

Review findings:

1. The agent/tool content was useful, but the side-by-side window did not exist
   in the product. Replace it with a real consolidated Desktop window.
2. Replace standalone settings/plugins screenshots with annotated
   configuration-to-plugin-to-UI relationship proof, including a session
   actions example.
3. Replace the direct system-message bubble with the real session action and
   add real Cost report action proof plus magnification.
4. Replace independent Desktop/mobile images with one framed composite whose
   shared session is unmistakable.
5. Correct user-bubble contrast, use GLM-5.3 through Z.ai, expand reasoning,
   and revise the prompt/reasoning language.
6. Correct pin/status default-pinned behavior and recapture the real plugin
   state.

The operator's pink macOS accent is personal configuration and is not part of
the product identity. Published Desktop captures use deterministic blue.

Compatibility source reviewed during planning and reconciled after the branch
merge:

- historical review branch: `develop`;
- historical review commit:
  `c52db305e0a815da5831d462a495df68ec4f2eb7`;
- canonical package:
  `landing_page/research/current-product-and-compatibility-baseline/`;
- canonical website projection:
  `landing_page/research/current-product-and-compatibility-baseline/website-compatibility-data.md`;
- accepted product source revision:
  `add5f5e71de3bb1676851bb840dfd77620f63ddb`;
- transformation version: `compatibility-baseline-v2`;
- review state: accepted;
- maturity: draft.

The canonical package supersedes the historical numbered location and is more
complete than the earlier projection, so the historical file is not copied
into a duplicate directory. The accepted website projection verifies against
its maintained generator. Current extraction also detects later Anthropic
context-editing and compaction additions; under the package's source-revision
policy, that drift requires a separate re-audit and does not silently alter
the accepted classifications used by this website task.

## Execution plan

Status: Draft

This draft applies only to checkpoint 4, **the Message actions relationship
image**, below. Prerequisite reconciliation, layout, popup, and the first
Session actions visual are already accepted; this does not reopen them.
Final source promotion, other product integrations, and publication retain
their separate gates.

### Design

#### Common content ownership

Both solutions contain the same six feature themes before Getting Started.
Their existing titles and core descriptions remain the starting copy.
Incorporate all requested evidence into the owning feature:

| Feature | Images in its own image area |
| --- | --- |
| One workspace for every model family | Codex picker; Claude picker |
| Replace the parts you disagree with | Session actions relationship; Message actions relationship; Session list relationship |
| Transparency by design | Compiled instructions; Cost report with relevant usage metadata; ChatGPT usage report |
| Work from anywhere | One matching Desktop/phone composition |
| Vibe code—or vibe anything | System message, non-development request, initial reasoning |
| Sessions become workspaces | Desktop list with popup; Desktop message-action popup |

Remove `transparency-details` / "See what goes into each session" and
`plugin-action-examples` / "Your plugins shape the controls" after moving
their data. The feature group contains each theme once. Do not retain a
compact duplicate overview for a feature that becomes full-width in Solution B.
Keep the existing provider deep dive and other previously maintained sections
below Getting Started; no unrelated page restructuring is proposed.

#### Shared refinements for either solution

- Use the **provider-example card treatment for each image**, with its optional
  image-specific title and description above the inset screenshot canvas.
  Keep the feature title/description unframed outside that image card. Match
  the reference surface, border, rounding, and padding; preserve prominent
  feature titles and direct hero attachment without a new heading/divider.
- Preserve accepted native horizontal scrolling and snapping. Add previous/
  next chevron buttons and clickable bottom dots to multi-image frames.
  Put chevrons at the screenshot's side centers as overlays and put the dots
  below the image card. One image needs no controls. New asset compositions
  must keep proof-bearing controls clear of the small side overlays.
- Buttons move one image; the first/last direction is disabled at the
  corresponding boundary. Dots select an image and identify the current one.
  Reflect swipes, trackpad/keyboard scrolling, and resizing in the controls.
  Keep accessible button names and current-position state, reduced-motion
  behavior, stable frame height, and independent state for each feature.
  No model-family tabs, autoplay, wraparound, or new carousel dependency.
- Remove the snapshot-guide link, scroll hint, and captions below the image.
  Keep snapshots mentioned in the existing feature description and retain the
  source image for reuse. Image labels/descriptions belong at the top of their
  own card, with stable space across image changes. Only dots follow the card.
- Keep 3:4 frames for compact two-column items and phone layouts, aligned
  across desktop pairs through their shared copy-row height. No text
  truncation or retained pairing whitespace on phones.
- Current images and described placeholders suffice for this layout pass.
  Fit complete source images without distortion. New captures, baked plugin
  connectors, and magnified callouts remain in the later asset checkpoints.

#### Solution A — all six highlights in one two-column grid

Keep the existing sequence and three rows:

| Desktop row | Left | Right |
| --- | --- | --- |
| 1 | One workspace for every model family | Replace the parts you disagree with |
| 2 | Transparency by design | Work from anywhere |
| 3 | Vibe code—or vibe anything | Sessions become workspaces |

All feature image areas use the shared 3:4 frame. The plugin and transparency
items each have three images in their own horizontally navigable area.
On phones, preserve the same reading order in one column.

Approach: extend the existing showcase/media components with the common card
and navigation treatment, migrate the two gallery data sets into their
owners, and delete their standalone section entries. Do not implement a
second layout mode unless Solution B is chosen instead.

Tradeoff: the smallest page/layout change and a compact, consistent overview.
Configuration/menu compositions and detailed reports have less desktop
display space, so later capture/callout work is important. If the real proof
cannot become readable at that size, stop with page screenshots before
proposing a different layout.

#### Solution B — four compact highlights plus two full-width highlights

Proposed feature-group sequence, all before Getting Started:

1. Two-column row: **One workspace for every model family** /
   **Work from anywhere**.
2. Two-column row: **Vibe code—or vibe anything** /
   **Sessions become workspaces**.
3. Full-width **Replace the parts you disagree with**, with its three images.
4. Full-width **Transparency by design**, with its three images.
5. Getting Started, followed by the unchanged existing deep dives.

This explicitly changes the feature order: a short capability overview comes
first, then the two detailed architectural/inspection features. Keep the
original feature titles; do not use the two added gallery headings.

Reuse existing full-width section shells and title/description/image
presentation. Each expanded feature has one large image area with the same
chevrons/dots and native scrolling, not three narrow simultaneous thumbnails.
Propose a **16:9 desktop image canvas** for these two full-width areas, bounded
by the existing page width, returning to **3:4 on phones**. The outer card and
inset treatment match Solution A. This ratio change is part of Solution B's
approval, not an implementation choice to make silently.

Approach: retain one feature list and renderer. The order of that list controls
reading order; an optional per-item `layout: full-width` spans the page and
selects the wide desktop frame. Omitted/compact values use the normal column.
This renders the two detailed features once as full-width rows while keeping
all six before Getting Started. A requires only reordering the list and
clearing the two full-width values. Reuse common media/control components.
Later asset compositions
must work at desktop and mobile sizes; wide desktop presentation alone does
not solve phone readability.

Tradeoff: more desktop room for code-to-control relationships and report
text, at the cost of a longer feature area, a changed order, and an additional
responsive image shape. Getting Started moves farther down the page.

The user also allowed a two-item compact grid. Retain that as an alternative:
model families and work-from-anywhere first, followed by four full-width
features. It is not the proposed default for Solution B because it gives
the simpler research/workspace visuals a large page footprint too.

#### Product changes versus capture-only changes

**Product fixes on develop:**

- Rename the message compaction row and its confirmation title using the
  selected approved wording. Keep `compact_native_history_through_message`,
  `compact_native_history`, parameters, provider capability gating, history
  semantics, snapshot behavior, and confirmation intact. Because the label is
  plugin-owned, consumers including mobile will receive the same label.
- Make macOS action-popup sizing accommodate actual labels and reserve space
  for both the leading icon and trailing pin control. Use a measured/content
  width bounded by the visible screen; retain scrolling for tall menus and
  full text at the bound. Apply it to production Session actions, Message
  actions, and list-row menus through their maintained native path.
- Allow one line break (up to two lines) in action names in the shared menu
  content on both Desktop and mobile, including other popup consumers of the
  same design. Account for taller rows in native size/scroll calculations.
  Inspect ordinary, rich/custom, and disabled rows plus pin affordances.
  If a real label cannot fit within two lines at the available width, bring
  that concrete case to review instead of inventing a truncation rule.
- Keep native anchoring, dismissal, keyboard action access, and saved pin
  preferences. A wider popup is not a new menu implementation.

**Maintained capture-only changes:**

- compact picker window with only Tools visible on the right; the full
  configured-agent list stays visible on the left;
- deterministic row selection/order and sample titles, subtitles, report
  buckets, amounts, dates, prompts, and reasoning;
- standard blue theme across main windows and separately mounted native
  popovers; ordinary windows retain the user's system theme/accent;
- isolated action preferences, making the actual pin/archive/status state
  visible without resetting the operator's saved settings.

No new global archive/status/pin defaults, account connection, provider call,
email/PDF sharing, destructive history action, or new plugin API is required
to make these captures. Existing plugin contracts supply the actions.

#### Real UI source generation and composition

The owning application renders real windows, menus, and reports. The landing
asset pipeline owns syntax presentation, image framing, focus callouts,
connector drawing, resize, compression, and website binding.

Use maintained sanitized config and report inputs to:

1. load the actual production plugins in an isolated application;
2. obtain their real action/UI schema and map package declarations to action
   IDs; never infer the mapping solely from similar display labels;
3. seed isolated cost records and a ChatGPT usage journal, then invoke the real
   read-only report actions;
4. render deterministic data through production Desktop/mobile components;
5. capture the app window and its real `NSPopover` with the background
   visible, using the native capture/XCUITest path;
6. optionally render the valid JSON snippet with Playwright, then use
   ImageMagick to assemble the left-code/right-UI composition and draw all
   connectors onto the final pixels;
7. produce light/dark optimized candidates, use them on the actual local
   homepage, and inspect the webpage with Playwright screenshots and
   `view_image`.

Each composition definition records source paths/hashes, crops, geometry,
package/action mapping, and exact source/target row positions. Lines must end
on the corresponding config declaration and real control, avoid label text,
and branch for the export package's two actions. Theme variants preserve those
relationships. Useful alt text describes the relationship without relying
only on line color.

Keep the complete app screenshot as context on the right; a focus callout may
enlarge its actual popup region without replacing the background with a
fabricated menu. For narrow displays, the same code-left/UI-right relationship
remains in the composed image. Stop for an approved placement adjustment if
it cannot be legible there.

Candidate files stay under ignored artifacts and are staged only into an
explicit local preview of the real website. Clean up the previous pass's
task-owned untracked `public/homepage-draft` files when replacing them with
this preview path; do not promote unapproved files merely to preview them.
There is no standalone review gallery/package. Final approved sources and
derivatives return through the existing visual asset catalog lifecycle.

#### Report data and continuity

Use short sample buckets such as `OpenAI` and `OpenRouter` and generic projects,
with multiple nonzero days and totals that reconcile through the existing
report calculation. Keep journal values, percentages, reset times, tokens,
and cost classifications internally consistent. Do not paint new numbers
over an unrelated report or expose personal journals/accounts.

The ChatGPT report retains its estimated-usage and limit semantics. A plain
"Sample data" caption is sufficient for invented values; it must not imply
that estimated usage cost is an additional subscription charge.

Desktop/mobile continuity uses one shared fixture for the full session
identity and displayed prompt/answer. The website should make the match
observable through its content, not assert it with a capture-goal label.

#### Compatibility and prior verification

Preserve the already-implemented descriptors/API/SDK, plugin-default, theme,
and stable-ID work. The accepted compatibility baseline remains pinned;
this pass does not reclassify provider support. Existing passing test evidence
is retained in Implementation Notes, but does not establish approval of any
new image or layout.

Reproduce the native build problem with the current source before choosing a
fix. A routine in-scope producer repair may proceed after plan approval; a
native/runtime upgrade, architectural workaround, or change of product surface
requires another decision. Similarly, diagnose the stale visual fixture from
its maintained generator before refreshing it; do not update hashes to hide
an unexplained mismatch.

### Next checkpoint: first Session actions relationship image

**Outcome:** replace only the first placeholder under **Replace the parts you
disagree with** with one reproducible relationship image, in light/dark and
wide/portrait variants. Keep the other two plugin placeholders and every
other feature as they are. The image-card label remains **Session actions**,
with its existing description; alt text describes the three relationships.

The accepted Desktop image has one valid JSON excerpt on the left and the
real conversation/popup on the right, with baked connections. The revised
mobile image has full-width code above a magnified native popup excerpt:
matching translucent marker bands identify the three corresponding rows,
without lines. Preserve the real header, close control, and edges. If an
enlarged excerpt omits unrelated menu rows, mark the crop break visibly and
record its source segments; do not redraw a fabricated menu.

| Visible plugin package | Real contributed action |
| --- | --- |
| `session-title-app` | Edit title |
| `generate-title-app` | Generate title |
| `summarize-range-app` | Summarize range |

**Responsibilities and data flow.** A small maintained capture configuration
loads these three actual plugins into an isolated local backend. Use the
existing deterministic provider pattern from the SDK backend integration
harness (`plugins.deterministic_stream_provider.DeterministicStreamProvider`)
and seed a short, sanitized conversation through the public session/message
API. No provider inference, account credentials, personal history, title
generation, or summarization operation is needed.

The native scene uses production `ChatPane` and the production
`RestAgentBackend`/`FetchTransport` against that backend. Open the real Session
actions trigger and locate rows by stable action identity. The same loaded
config supplies the visible JSON excerpt and the package/action mapping;
labels must not be invented or hand-maintained in a separate fake menu.
This provides one decisive config → backend HTTP → production SDK → native
menu check. Record the schemas and screenshot geometry from that run.

The Desktop package owns its capture-only scene and native-window capture.
The landing catalog owns optional Playwright rendering of the code block,
ImageMagick composition, responsive derivatives, provenance, and page binding.
All new checkpoint work belongs on main after the approved reconciliation.
A further ordinary product fix belongs on develop; stop
before broadening that scope or silently importing another product commit.

**Implementation sequence after approval:**

1. **AGENT:** preserve the three pending capture-file diffs and their hashes
   before changing either worktree. Reconcile the six named source changes
   above into main without the superseded review package or unrelated
   develop changes. Transfer the pending Desktop harness and compact-picker
   edits together, plus the mobile screenshot-saving edit. Verify that all
   three main files match the preserved develop versions, then run focused
   agent-preview, theme, plugin-default, popup, capture-consumer, HTTP/SDK,
   and type checks. Only after that evidence, remove the exact transferred
   pending hunks from develop. Record provenance and leave the reconciled
   main changes uncommitted for the next review. Extend the reconciled
   Desktop harness for the new scene instead of creating another divergent
   copy of it.
2. **AGENT:** add the isolated three-plugin capture config and backend setup.
   Verify exact package, plugin ID, action ID, order, and display-label
   mappings through the public HTTP API and production SDK. Derive the
   rendered JSON from the loaded configuration. The broader stale
   `mobile-workbench` fixture is not an input to this focused scene; leave its
   unrelated refresh to the later checkpoint and report its known stale state.
3. **AGENT:** extend the proven XCUITest/native capture route with a selected
   Session actions scene built from current source. Capture the owning
   window and popup together in their actual positions, including window
   chrome and conversation background. Retain the separate window/popover
   bounds so the crop cannot cut off a popup extending past its owner.
   Use the deterministic blue capture palette in both native roots and
   isolated preferences. Any menu ordering/hiding is capture-only and
   recorded. Open the menu without executing its actions.
   The focused producer captures this one scene in both required themes into
   its own artifact directory, preserves other output files, and cleans up
   only its own process. Native UI automation runs sequentially.
   If the fresh build fails, stop with its actual diagnostic before choosing
   a runtime upgrade, reused binary, or alternative product surface.
4. **AGENT:** make one composition definition with a 16:9 wide derivative
   and a 3:4 portrait derivative, each in both themes. Desktop retains code
   left/UI right. The user-reviewed mobile revision stacks full-width code
   above a recognizable popup excerpt and pairs rows by matching translucent
   marker colors. Use visual soft-wrapping for long JSON
   strings, with complete plugin names. A magnified crop of the actual menu
   may emphasize its three rows while the surrounding window remains visible.
   Desktop lines end on corresponding declarations and real rows; mobile
   draws no lines. Marker bands preserve readable text and cover only the
   mapped rows. Store crops, popup-source segments, correspondence/annotation
   geometry, source revision,
   hashes, mappings, and output dimensions in the maintained asset recipe.
5. **AGENT:** add optional responsive source selection to the existing image
   renderer. The expanded desktop frame uses the wide derivative; phones and
   compact feature placement use the portrait derivative. Existing theme
   selection, lazy loading, alt text, and current image fields remain valid.
   This keeps option A a content-only rearrangement. Preserve the accepted
   frame/card, title/body order, chevrons, dots, and neighboring placeholders.
6. **AGENT:** bind the candidates only in an explicit local preview of the
   real homepage on main. Keep masters and intermediate files under ignored
   `landing_page/artifacts/`; do not promote reviewed sources/public assets
   to obtain a preview. Add the scoped producer/recipe checks, run the
   affected content/build/browser checks, and verify active-theme/source
   loading, actual dimensions, full labels, connector endpoints, and absence
   of overflow. Take Playwright screenshots at 1440, 1024, 768, 390, and 320
   CSS pixels in both themes, including a compact-placement smoke check.
7. **HUMAN JUDGMENT — STOP:** review the actual page/LAN preview and its
   desktop/phone screenshots before any other proof image, source promotion,
   or next implementation commit. If labels or relationships remain
   unreadable after bounded crop/zoom/spacing work, present that evidence and
   ask before changing the established frame or the newly selected mobile
   stack/highlight concept.

**Image-inspection tooling:** Playwright screenshots and geometry checks are
agent work. The current `view_image` tool additionally requires full file
paths supplied by the user. Use these stable review paths, request them at
the review handoff if they have not been supplied, and do not call OCR or
geometry checks a visual inspection:

- `/Users/ferenci84/Dev/Mine/ai-agent-platform-main/landing_page/artifacts/plugin-session-actions-review/desktop.png`
- `/Users/ferenci84/Dev/Mine/ai-agent-platform-main/landing_page/artifacts/plugin-session-actions-review/mobile.png`

Other widths/themes remain alongside these two primary screenshots. No
standalone review gallery/package is proposed. Human-only work is plan/
integration approval, any OS permission that actually blocks native capture,
providing the image paths needed by the tool, and final contextual visual
judgment. No account login, hosted-provider spending, deployment, or new
public API is part of this checkpoint.

### Next checkpoint: Message actions relationship image

**Outcome:** replace only **Actions for each message**, the second image slot
under **Replace the parts you disagree with**. Keep the approved Session
actions image, its image-card copy, the overall layout, and all other slots
unchanged. Use the existing caption:
**Fork, summarize, or share a message using the plugins you choose.**

Three actual package declarations contribute four highlighted controls:

| Package declaration | Native Message actions row | Stable element ID |
| --- | --- | --- |
| `session-actions-app` | Fork here | `fork_session_at_message` |
| `summarize-range-app` | Summarize messages up to here | `summarize_before_message` |
| `message-export-actions` | Share as PDF | `message_share_as_pdf` |
| `message-export-actions` | Share as Markdown | `message_share_as_markdown` |

**Design:** reuse the accepted wide Desktop configuration-left/UI-right
composition, with one export declaration branching to both export rows.
Reuse the accepted portrait code-above-popup treatment. Both export rows
share the declaration's marker color; the other two packages have their own
colors. Retain genuine popup chrome and visibly mark any cropped-out entries.
Keep full action names, including the longer summarization label.

**Capture boundary:** load the actual packages in an isolated local backend,
seed the existing short workshop conversation through the public API, and
connect the production SDK and unchanged production chat/capture host.
Open the real Message actions trigger inside the specific assistant
transcript row, not the first identically named trigger in the window.
Verify the public schema's plugin IDs, action IDs, message-index parameter
bindings, and the four real native rows. Open the menu only; do not fork,
summarize, delete, export files, or deliver messages.

The export package descriptor also registers Send to Kindle. Loading it is
not permission to invoke it. Unrelated rows can remain in the actual source
capture or be omitted through the same visibly marked excerpt treatment.
Do not replace the package with a lookalike plugin for convenience.

**Steps after approval:**

1. **AGENT:** preserve the approved four Session actions derivatives and their
   hashes. Keep its existing capture inputs intact. Add a focused Message
   actions config and capture test, reusing the existing production chat host.
   No product change is planned; capture-test selection and isolated data
   belong on main.
2. **AGENT:** verify the three-package/four-row contract through public HTTP
   and the production SDK, then capture the selected assistant message's
   native popup with its owning conversation in light/dark. Record the
   exact target message index and native geometry.
3. **AGENT:** extend only the necessary recipe/helper support for one
   declaration mapping to multiple rows. Produce separate wide/portrait
   derivatives from those real sources. On Desktop, two same-color branches
   reach PDF/Markdown; on phones, two same-color marker bands identify those
   rows. Keep the approved first image unchanged.
4. **AGENT:** put the candidate into the second slot of the actual main
   homepage preview. Verify both themes at 1440, 1024, 768, 390, and 320px,
   the longer action name, popup identity, correspondence, carousel clearance,
   stable framing, and the first approved image's unchanged bytes. Use the
   least expensive scoped native, HTTP/SDK, asset, and browser evidence.
5. **HUMAN JUDGMENT — STOP:** review this second composition in context before
   further image production, another implementation commit, or promotion.
   If four readable rows do not fit the approved phone frame after bounded
   crop/spacing tuning, show the real page evidence and ask before changing
   the frame or truncating names.

Main owns capture/composition, website, task, and decision-record changes.
A discovered ordinary product fix belongs on develop and follows its review
boundary. Keep existing first-image production source files unchanged where
possible so adding capture-test coverage does not invalidate its provenance.
Do not change schema IDs, popup behavior, or saved preferences for this image.

### Ordered execution

1. **HUMAN JUDGMENT — COMPLETE:** B and the shared refinements are approved.
   Add content-configurable ordering/width and reconcile website work to
   main as requested. Product changes remain on develop pending confirmation.
2. **AGENT:** Preserve the October 4 candidate and reasons it was rejected in
   the durable decision record. Record current relevant diffs/capture sources
   without committing or disturbing parallel work.
3. **AGENT:** Implement only the chosen layout and shared refinements.
   Move the gallery visuals into the appropriate features, remove the two
   added section entries, and preserve all six feature themes. Add button/dot
   navigation synchronized with native scrolling and remove everything below
   the image. Use existing candidate images and descriptive placeholders;
   do not begin new capture or magnification work.
   Verify the selected desktop/mobile order and ratios, aligned compact
   cards, buttons/dots after every input method, keyboard focus, independent
   image state, client-side navigation cleanup, and absence of image/footer
   overflow. Capture both themes at the existing five review widths.
   **STOP — HUMAN REVIEW:** Review the actual page, then authorize the next
   product checkpoint and any commit.
4. **AGENT:** Implement and verify the real popup-sizing and compaction-label
   fixes plus shared Desktop/mobile two-line labels on `develop`. Preserve
   action behavior and native popup ownership.
   **STOP — HUMAN REVIEW:** Demonstrate menus before starting new captures.
5. **AGENT:** Make the native producer reproducible and capture a first
   three-plugin Session actions composition. Put it in the actual compact or
   full-width position selected by A or B and examine desktop/phone sizes immediately.
   If readable composition cannot fit, pause here with the actual screenshots.
   **STOP — HUMAN REVIEW:** Obtain review before producing the remaining set.
6. **AGENT:** Generate the remaining relationship/menu/report/picker/continuity
   sources using real schemas and isolated sample data. Produce complete
   ImageMagick composites and light/dark derivatives.
7. **AGENT:** Bind candidates to the local homepage and existing gallery
   formats. Run browser checks and inspect screenshots with `view_image` at
   1440, 1024, 768, 390, and 320 CSS pixels, including both themes and scrolled
   viewport captures. Fix bounded legibility and spacing issues.
8. **AGENT:** Run the relevant product regression, native, HTTP/SDK, content,
   visual-pipeline, and website checks; document the actual boundaries and
   any blocked check. Resolve explained fixture drift through its generator.
9. **HUMAN JUDGMENT:** Review the actual site on LAN and approve the layout,
   captions, sample data, mappings, and final sources. Images must pass both
   visual review and source-truth checks.
10. **AGENT, after that confirmation:** Promote reviewed sources through the
    maintained catalog and prepare the confirmed product changes for main.
    No commit/push/publication without a new explicit instruction. Respect
    the existing separate publication and waitlist boundaries.

### Implementation decisions and open questions

- **Checkpoint 4 recommendation — Draft:** Message actions is the next focused
  image, using the now accepted Desktop and phone treatments. The export
  package's two actual classes prove one package can contribute multiple
  controls. No new material product decision is presently required.
- **Checkpoint recommendation:** save the accepted work in a scoped commit
  before extending the pipeline, if the user authorizes that commit.
  Visual approval alone is not a commit instruction; no commit or source
  promotion was performed when recording this next-step plan.
- **October 6 approved correction:** reconcile the three pending capture
  files together with the six named, already implemented source changes
  before extending the main harness. The previous popup-only integration
  proposal left related capture work split across branches and is superseded.
  Preserve the pending diffs, verify their main copies and focused consumers,
  and only then clear those exact pending develop edits. Do not bring the
  rejected standalone review package or unrelated develop work into main.
- **October 6 approved design:** use four derivative files (wide/portrait ×
  light/dark) for the same image, selected by the existing frame placement.
  One reduced wide image would leave small text and unused space in the
  phone's portrait frame. Add only optional image-source fields, with no
  section-layout change or separate mobile interaction.
- **October 6 approved producer:** extend the successful XCUITest native
  capture route, using a fresh source build and the real backend/SDK/native
  controls. A content-view bitmap alone omits the native popover. Do not
  resolve the earlier Release producer issue by silently reusing an old app.
- Explicit user decisions: all six feature themes; title/description/images;
  horizontally accessible agent images; complete ImageMagick relationship images with
  readable names and three or more mapped controls; visitor-focused copy;
  editable sample data; ChatGPT report; merged workspace pitch; real popup
  readability fix; stop before an unapproved material change.
- **Superseded:** the two additional lower-page galleries. The user requests
  their planned visuals inside their owning highlights instead.
- **Selected:** B's four compact/two full-width structure, changed feature
  order, and 16:9 desktop frame variant. The top four are end-user-oriented;
  the expanded pair is for deeper inspection. A and future rearrangements
  remain content-only choices using the same renderer.
- **Shared user refinements:** individual image cards with optional image
  title/description above the screenshot; unframed feature copy; side-centered
  chevron overlays; dots below the image card; no other below-card text/links;
  and retained native scrolling.
  Plan approval selects the bounded navigation behavior described above.
- **Approved:** "OpenAI compaction up to here" rather than "Native
  compaction up to here". The former names the provider-specific capability;
  the latter is shorter. This is a label change, not a compaction redesign.
- **Approved clarification:** names may wrap once to two lines in all popups
  sharing the action-menu design, on Desktop and mobile.
- **Latest user direction:** match the provider-section image frame,
  background, and aspect ratio; use horizontal scrolling for multiple images
  on desktop/mobile; align paired images; defer magnification.
  The 3:4 shared-frame implementation and per-row copy alignment are approved.
- Recommendation: keep existing highlight title/body copy; keep only useful
  image labels/descriptions above the frame and plain sample-data wording.
  Remove the snapshot link and scroll hint rather than relocating extra prose.
  Final copy remains subject to review in context.
- Capture permission is bounded: simplify sample content, hide/reorder
  irrelevant rows, and adjust windows, while retaining production controls.
  Do not silently turn fixture preferences into product defaults.
- No human account/login/spending action is expected. If native OS automation
  permission or a material producer change is required, explain the exact
  blocker and ask then; do not replace the native menu with a mock.

### Documentation

- For checkpoint 4, add its real package/action/message-index mappings,
  source geometry, one-to-many correspondence support, and verified command
  to the existing capture/processing guides. Append the new candidate and
  later human decision to the existing durable design record; preserve the
  first accepted visual and its alternatives.
- For checkpoint 3, update the existing Desktop capture guide with its
  selected-scene command, local backend lifetime, isolation, theme, window/
  popup capture, and safe cleanup. Update the landing visual-processing and
  content-system guides only for the new recipe and optional responsive
  source fields. Preserve the current placeholder/copy and record candidate
  geometry, readability tradeoffs, and the later human choice in the existing
  durable visual-decision document; do not mark the image accepted early.
- Keep the pre-revision candidate, copy variants, changed decisions, rationale,
  evidence gaps, and final selections in
  `landing_page/docs/development/homepage-positioning-and-visual-decisions.md`.
  Preserve viable alternatives and identify rejected layout directions so a
  later agent does not accidentally restore them.
- Update landing content-system and visual-processing docs for the selected
  feature layout, full card treatment, synchronized image navigation, baked ImageMagick composition,
  local candidate preview, and final catalog lifecycle. Supersede the
  standalone review-gallery instructions.
- Update Desktop popup/capture documentation and affected plugin user docs
  for the chosen compaction wording. Document tools-only picker presentation
  as capture-only.
- Maintain source provenance, row/package/action mappings, sample-data
  generation, theme geometry, alt text, dimensions, byte budgets, and
  freshness triggers with the visual catalog. These are developer records,
  not website captions.
- Preserve the accepted compatibility baseline provenance and existing SDK/API
  documentation; no new contract is planned.

### Task checklist

- [x] **PRIOR WORK:** Agent metadata/API/SDK/picker, bubble contrast, pin/status
      defaults, deterministic theme, action fixtures, and compatibility
      reconciliation implemented; evidence retained below.
- [x] **HUMAN JUDGMENT:** October 5 review rejects the full-width highlight
      layout, agent switcher, live HTML connectors, and internal captions.
- [x] **HUMAN JUDGMENT:** Approve this revised plan and its named decisions,
      with Desktop/mobile two-line popup labels and staged review checkpoints.
- [x] **AGENT:** Restore the standard layout and apply only approved placement
      and duplicate-section changes.
- [x] **HUMAN JUDGMENT:** Approve the frame/scroll/alignment layout follow-up.
- [x] **AGENT:** Apply the shared frame and ratio, horizontally scrolling
      image sets, and paired-row alignment; verify in the actual page.
- [x] **HUMAN JUDGMENT:** Choose A or B and approve the combined refinement
      plan before execution resumes.
- [x] **AGENT:** Reconcile this task's pending website changes onto main,
      verify the transfer, and remove only the migrated pending edits from
      develop. Leave product and unrelated work untouched.
- [x] **AGENT:** Integrate the gallery evidence into the selected feature
      layout, apply the full card treatment and chevrons/dots, remove
      below-image content, and verify the actual page.
- [x] **HUMAN JUDGMENT:** Review the layout checkpoint and authorize the next
      product step and any commit.
- [x] **AGENT:** Implement and verify popup sizing and the selected label.
- [x] **HUMAN JUDGMENT:** Authorize the product popup checkpoint commit.
- [x] **AGENT:** Commit the popup changes on develop and prepare the next plan.
- [x] **HUMAN JUDGMENT:** Approve the focused Session actions image plan,
      including prior capture reconciliation, product prerequisites,
      integration timing, and responsive sources.
- [x] **AGENT:** Back up and reconcile the prior capture work and required
      source changes onto main, verify it, and clear only migrated develop
      edits before starting new capture implementation.
- [x] **AGENT:** Resolve reproducible native capture and validate the primary
      three-plugin composition on the actual page.
- [x] **HUMAN JUDGMENT:** Review that first composition on desktop/mobile
      before further images, promotion, or another implementation commit.
- [x] **HUMAN JUDGMENT:** Accept the current Desktop composition.
- [x] **HUMAN JUDGMENT:** Review the revised stacked phone composition.
- [ ] **HUMAN JUDGMENT:** Approve the focused Message actions image plan.
- [ ] **AGENT:** Capture, compose, bind, and verify the Message actions image
      while preserving the approved first image.
- [ ] **HUMAN JUDGMENT:** Accept the Message actions candidate in context.
- [ ] **AGENT:** Generate and compose remaining production visual sources.
- [ ] **AGENT:** Bind local candidates, inspect responsive Playwright images
      with `view_image`, and complete focused verification.
- [ ] **HUMAN JUDGMENT:** Approve the final in-context visuals and copy.
- [ ] **AGENT:** Promote approved sources, update the durable record, and
      report the remaining merge/publication boundaries.

### Requirement verification

- Checkpoint 4 ownership is this task. The decisive check loads the three
  actual packages in the backend, seeds the conversation through public
  endpoints, opens the chosen assistant message's production menu through
  `RestAgentBackend`, and checks/captures all four real rows and their public
  message-index bindings. The composition's recorded geometry connects one
  export declaration to both export controls. Page checks verify current
  source selection, popup identity, complete names, marked crop omissions,
  same-color phone correspondence, and unchanged approved first-image bytes.
  A mocked schema or replacement frontend menu is insufficient.
- Checkpoint 3 ownership is this task. Its decisive source check starts the
  isolated backend with the three real plugins, seeds a session through the
  public API, connects production `RestAgentBackend` to production `ChatPane`,
  opens the native Session actions menu, and verifies/captures the three
  actual rows. The composition recipe then ties the recorded declarations
  and row bounds to its baked endpoints. A mocked schema plus an unrelated
  screenshot does not satisfy this check. Native geometry and both themed
  composites feed actual homepage captures at the five review widths.
  Human judgment of readability and source promotion remains unchecked.
- Layout and audience: production-built local homepage proves the selected
  A/B arrangement, all six themes exactly once before Getting Started,
  title/description/images order, two accessible
  picker captures in the horizontal strip without model-family tabs, merged
  duplicate workspace copy, and no
  internal caption phrases. Playwright checks breakpoints, image completeness,
  both themes, keyboard access, and absence of page overflow. Inspect real
  viewport and element screenshots with `view_image`; a passing layout metric
  alone is not visual acceptance.
- Layout follow-up: browser measurements verify the common 3:4 frame,
  matching frame tops/bottoms within each desktop row, and relaxed copy
  spacing on phones. Scroll each multi-image group independently with
  pointer/touch and keyboard, verify both images are reachable, and confirm
  that scrolling does not resize the frame or overflow the page. Final
  pixel-level acceptance remains a human review of the actual website.
- Combined refinement: verify every requested plugin/report image slot under
  its owning feature and absence of the two standalone gallery sections.
  Check image-card appearance against the reference, unframed feature copy,
  image captions above their screenshots, chevron/dot selection,
  synchronized active state after swipe/wheel/keyboard input and resizing,
  independent groups, first/last boundaries, reduced motion, and navigation
  away/back without duplicate listeners. Chevrons must align with the actual
  screenshot center despite caption-height differences, and dots must be
  below the card. No visible prose, caption, or link may follow the card.
  Test only the selected layout:
  A uses 3:4 throughout; B adds 16:9 at desktop for its two expanded features
  and returns those frames to 3:4 on phones.
- Content-only layout flexibility: verify B in the main preview, then render
  an isolated copy of the same site with only the content reordered and the
  full-width flags removed. Confirm six compact items, the original A order,
  and 3:4 frames without changing any component code.
- Plugin relationships: load the displayed config with actual plugins, read
  their public UI schemas through HTTP and the production SDK adapter, and
  check exact action/package mappings including the two export rows. Native
  captures verify production rendering; ImageMagick provenance and reviewed
  page screenshots verify every baked endpoint and name. A hard-coded frontend
  fixture alone does not prove that config contributes those actions.
- Reports: isolated records/journal → real report actions → production
  Desktop action display. Verify sums and estimation semantics from returned
  data, then inspect readable tables/limits and plain sample-data captions.
  Do not use hosted requests or personal credentials for this evidence.
- Popup fix and label: plugin schema regression verifies new visible label,
  unchanged action IDs, confirm dialog, and existing provider gating; a public
  HTTP/SDK consumer verifies the same schema. Native menu tests prove the
  full selected label and pin affordance are visible, anchored, and usable.
  Test production list/message menus and the other shared-design consumers on
  Desktop and mobile, including two-line labels and correct scroll extent.
  Do not use a duplicate screenshot-only menu.
- Workspace and continuity: native captures show pin/archive/status and menu
  options while titles/subtitles remain readable; the message popup shows all
  three highlighted operations. Shared Desktop/mobile fixture assertions
  require matching identity and displayed prompt/answer before composition.
- General-purpose proof: the actual captured viewport contains system message,
  request, and reasoning; no visible tool calls or external technical heading.
- Preserved product behavior: reuse prior tests for stable IDs, effective
  plugins, light/dark user text, and saved pin preferences; rerun relevant
  consumers when capture or shared menu changes touch them.
- Final asset acceptance: catalog/source freshness, exact bindings, alt text,
  light/dark sizes, compression, active-theme loading, and human in-page
  approval. Record blocked native/catalog checks explicitly; no skipped gate
  or unexplained hash refresh counts as passed.

### Additional implementation verification

- Verify screenshot/report input directories are isolated from live runtime,
  accounts, costs, journals, and saved preferences.
- Verify tools-only picker filtering and screenshot row selection are not
  enabled for ordinary product windows.
- Verify separate popup roots receive the capture theme without changing the
  user's system accent or normal app theme.
- Native screenshot collection must include the intended app/popover and
  exclude unrelated windows; never use the user's reference account totals.
- The website test server must use an isolated port, with reuse disabled:
  the previous pass accidentally exercised an unrelated preview on port 4321.
- Do not weaken a failing network/image-loading assertion merely because
  visual checks pass. Determine whether the issue is response-event
  collection, cache, loading behavior, or a real regression before changing
  its evidence boundary.

## Implementation Notes

Append new entries at the end of this section, keeping older entries first.

- 2026-10-02: The user approved the descriptor compatibility recommendation,
  capture-specific configuration/plugin approach, and this execution plan.
- 2026-10-02: Existing session-status, session-pinned, and title/subtitle
  application plugin contracts are authoritative for Highlight 6. Capture
  fixtures must use them directly or mirror them exactly.
- 2026-10-02: Added optional `agents.<id>.display` configuration with title,
  description, and finite order. The application exposes ordered descriptors
  in `GET /agents` while preserving the legacy sorted string list. Display
  metadata is removed before provider request configuration is built.
- 2026-10-02: Added SDK `AgentDescriptor`,
  `listAgentDescriptors()`, descriptor-aware controller caching, and
  `ensureDescriptorsLoaded()`. Desktop renders ordered title/description rows,
  shows the stable ID as secondary metadata, and still submits only the ID.
- 2026-10-02: Product verification passed: 76 focused core/application tests,
  all 352 frontend SDK tests, Desktop TypeScript checking, and focused picker
  and Sessions-panel component tests.
- 2026-10-02: Added a maintained Desktop website-visual harness using the
  production agent picker and production session-plugins window. The
  harness-owned AppKit content-view export avoids screen-recording permission.
  It generated Codex and Claude light/dark candidates successfully.
- 2026-10-02: Added deterministic mobile capture kinds for provider
  authentication/flex settings, feature plugins, compiled instructions,
  non-development reasoning, and plugin-driven session workspaces. The session
  workspace fixture uses the existing session-status, session-pinned, and
  session-title plugin IDs, values, and UI contracts.
- 2026-10-02: The expanded iOS Detox capture is running in the background
  after its first foreground build exceeded ten minutes. Candidate review and
  promotion remain pending.
- 2026-10-02: The complete 20-state iOS Detox website-visual loop passed in
  one run after replacing brittle readiness text with stable production
  identifiers. It generated light/dark candidates for provider settings,
  feature plugins, compiled instructions, usage/cost, mobile continuity,
  general-purpose reasoning, and plugin-driven workspaces.
- 2026-10-02: Added a Desktop same-session continuity state using the same
  session ID, title, latest prompt/answer, and agent as the mobile fixture. The
  incremental macOS producer generated its light/dark candidates together with
  the Codex and Claude picker/tool candidates.
- 2026-10-02: Added paired-proof support to the homepage media contract without
  changing the approved editorial/card structure. No candidate is bound yet.
- 2026-10-02: A LAN review gallery groups all ten light and ten dark candidates
  by the six feature highlights. Human approval is now the gate before source
  promotion, WebP generation, homepage binding, and final responsive review.
- 2026-10-02: Human review did not approve the first candidate set. The task
  returned from Approved to Draft because the revision adds a real
  consolidated Desktop selector, a public read-only agent-profile plugin
  contract, a shared theme token, plugin default changes, real action-display
  fixtures, and materially different compositions.
- 2026-10-02: The consolidated selector is feasible. Existing
  `list_plugins_for_agent()` and per-agent plugin runtime state provide the
  backend source, but no public agent-profile plugin endpoint currently exists.
  The session-plugin endpoint cannot cover new-session selection because no
  session exists yet.
- 2026-10-02: Confirmed the light-theme color defect: the classic Markdown
  renderer uses `textOnPrimary` for user messages even though
  `bubbleUserBg` is a translucent 12% blue. Raw text already uses normal dark
  text, and the selectable Markdown renderer currently ignores the user
  variant. A dedicated user-bubble foreground token is the coherent fix.
- 2026-10-02: Confirmed real action contracts:
  `show_compiled_system_message` returns a modal text action display, and
  `show_cost_report` returns a modal Markdown report with totals, daily
  project/bucket tables, and top sessions/projects.
- 2026-10-02: Confirmed current plugin defaults are the reverse of the reviewed
  target: pin is `default_pinned: true`; status list and session actions are
  `default_pinned: false`. Stored frontend preferences already override plugin
  defaults and must not be migrated.
- 2026-10-02: Reviewed the accepted draft compatibility data from `develop`
  commit `c52db305e0a815da5831d462a495df68ec4f2eb7`. It is absent on current
  `main`, so the revised plan imports/reconciles it before publishing claims.
  Available, Conditional, Optional, and Planned states remain distinct, and
  model-family bundles remain Crystal Lattice compatibility implementations,
  not official upstream applications.
- 2026-10-02: This was a planning-only pass. No product, plugin, capture, or
  website source was modified beyond this task-plan revision.
- 2026-10-02: The user approved the revised plan, including the additive
  agent-profile plugin endpoint, all plugin groups in the consolidated picker,
  the shared `bubbleUserText` contract, status default-pinned on both list and
  session-view surfaces, compatibility-baseline reconciliation, and execution
  of the revised product/capture work. Planned asset promotion remains gated by
  a later human visual confirmation.
- 2026-10-04: Reconciled the historical numbered compatibility reference with
  the canonical accepted package at
  `landing_page/research/current-product-and-compatibility-baseline/`. The
  accepted website projection is pinned to source revision
  `add5f5e71de3bb1676851bb840dfd77620f63ddb`, uses transformation
  `compatibility-baseline-v2`, and passes its maintained website-data
  generator check. Current extraction detects later Anthropic
  context-editing/compaction additions; the package explicitly requires a
  separate re-audit for post-source drift, so this task does not regenerate
  or silently reclassify accepted claims.
- 2026-10-04: Implemented the approved product changes on `develop` without
  merging them to `main`, per the user's branch boundary:
  - `ebb053ac` adds the safe read-only agent-profile plugin endpoint, SDK
    method/cache, real two-pane Desktop selector, compatibility fallback,
    documentation, and backend-to-SDK integration coverage;
  - `2bfaf03c` makes pin header-only by default, makes status default-pinned
    on list and session surfaces, and proves stored preferences remain
    authoritative;
  - `4fab5568` adds the shared `bubbleUserText` contract and applies it to
    light/dark mobile Markdown engines, raw user text, and Desktop user
    message rendering;
  - `7d46556b` isolates deterministic standard-blue capture theming from the
    ordinary macOS system/accent theme;
  - `29604c23` adds real generated compiled-system/cost action fixtures,
    revised GLM-5.3/Z.ai and workspace states, stable native selectors,
    dedicated-simulator selection, and the review-gallery generator.
- 2026-10-04: Product verification on `develop` passed:
  - core: 635 passed, 1 expected xfail;
  - application: 575 passed, 1 skipped;
  - frontend SDK: 373 unit tests plus 23 real-backend integration tests;
  - shared RN components: 76 tests;
  - Desktop: TypeScript plus 45 suites / 204 tests;
  - mobile: TypeScript plus 56 suites / 290 tests;
  - plugin-default, HTTP, rich-UI, fixture, and landing visual-framework
    focused suites.
- 2026-10-04: The compiled-system fixture executes
  `show_compiled_system_message` through the actual feature action. The cost
  fixture seeds generic records through the actual SQLite cost store and
  executes `show_cost_report` through the actual application action. Captures
  render the generated payloads through the production action-display
  component. Cost values are explicitly illustrative and contain no private
  paths, credentials, or company spending.
- 2026-10-04: Native iOS capture passed for the required light/dark actions,
  provider-settings, feature-plugins, continuity, compiled, cost, GLM/Z.ai,
  and workspace states. Desktop light/dark sources were captured from the
  current production JavaScript bundle in the known-good released native
  shell after a newly generated Hermes runtime crashed before JavaScript
  evaluation. Before source promotion, the default clean macOS producer must
  be made independently reproducible or the reviewed native-shell input must
  become an explicit maintained producer option.
- 2026-10-04: Generated the ignored review gallery at
  `landing_page/artifacts/homepage-visual-review/index.html`. It includes both
  themes, relationship boards with red and numbered connectors, real action
  displays, a framed Desktop/mobile continuity concept, GLM-5.3/Z.ai
  reasoning, and plugin-driven workspaces. No source promotion, public WebP,
  homepage binding, or website publication occurred.
- 2026-10-04: One review item remains explicit in Highlight 2: the application
  relationship candidate uses a production plugin-contributed action row as
  its middle proof. Human review must decide whether that is sufficient or a
  separate production application-plugin registry row is still required.
- 2026-10-05: The user approved the revised plan and OpenAI action wording,
  added Desktop/mobile two-line wrapping for all shared-design popups, and
  authorized only the layout checkpoint before the next review. Existing
  candidate images may show the current capture state; descriptive
  placeholders reserve new composition/report/menu sources for later steps.
  Chose to keep this checkpoint uncommitted so the requested visual review
  precedes a clean layout commit.
- 2026-10-05 layout checkpoint: restored two desktop highlight columns and
  title/description/media order, removed the switcher and live connector
  renderer, and kept both picker images visible. Replaced pending composition
  sources with descriptive placeholders. The existing research image is
  retained as an interim source; the required system-message recapture is
  still outstanding.
  Added the approved three-entry transparency gallery and two-entry plugin
  action gallery using the existing component. Moved `session-workbench`
  to the workspace highlight and added its snapshot-guidance link.
  Retained the old reviewed image sources while removing their obsolete
  page bindings. Narrowed header spacing below 360 px after the 320 px
  browser check exposed overflow; all header controls remain.
  Verification: build passed; 8 content checks, 19 pipeline tests, and 23
  Playwright tests passed. The responsive checks cover 1440/1024/768/390/320 px
  in both themes, image loading, stacked picker images, two-column geometry,
  content order, absence of overflow, and existing download/keyboard paths.
  A focused catalog check passed for both theme variants of provider reasoning,
  provider usage/cost, old chat actions, snapshots, and settings/plugins.
  The complete catalog check still fails on the stale `mobile-workbench`
  runtime fixture; no source refresh/promotion was attempted in this step.
  Playwright PNGs are under
  `landing_page/artifacts/homepage-layout-step1/` and the existing
  `landing_page/artifacts/visual-assets/playwright/captures/`.
  These were generated and layout metrics checked, but not opened with
  `view_image`: its tool instruction restricts use to image paths supplied
  in full by the user. Human visual review remains pending.
  The real website preview is served at `http://192.168.8.227:4175/`.
  Code is uncommitted on `develop`; task/decision records are uncommitted in
  the main worktree. No product popup changes, merge, push, or publication.
- Next checkpoint proposal, pending the user's layout review and instruction:
  first map every consumer of the shared popup row design (ordinary actions,
  rich/custom rows, list/session/message menus, and matching dropdown menus).
  Implement two-line labels for those Desktop/mobile consumers with enough
  row height and stable icon/pin alignment. Update macOS width/height and
  scrolling calculations without replacing native popovers. Rename the
  message action and confirmation title to "OpenAI compaction up to here",
  preserving IDs, provider gating, dispatch, confirmations, and preferences.
  Verify actual shared consumers and the public plugin schema, then show
  production macOS and mobile menu examples at narrow widths. Stop for review
  and commit authorization before capture/composition work. No product change
  from this proposal has been started.
- 2026-10-05: The user approved the shared image-frame, horizontal-scroll, and
  paired-row alignment follow-up. Implement only that pass and stop again for
  review; popup fixes, new captures, and magnification stay in later steps.
  The user requested chronological implementation notes appended at the end;
  moved the earlier October 5 entries after the October 2–4 history.
- 2026-10-05 frame/scroll/alignment checkpoint: implemented a shared
  `ProofImage` frame for highlights, provider examples, and supporting
  galleries. The frame is 3:4 with a border, rounded corners, and the provider
  sources' light/dark canvas backgrounds. Whole images use `object-fit:
  contain`; placeholders use the identical frame. Removed natural-aspect
  gallery sizing and the special narrow, tall phone-image presentation.
  Multiple highlight images now use independent native horizontal scroll-snap
  strips with a focusable region, scrollbar, and short scroll hint, without
  selector tabs or carousel JavaScript. Shared grid rows align copy areas and
  image edges across desktop pairs; single-column items have independent rows.
  Build and all 8 content checks passed. The 24-test Playwright suite passed,
  followed by a new focused Chromium mobile touch-swipe test (1 passed).
  Coverage includes frame ratio/appearance across all proof sections;
  image top/bottom alignment within 1 CSS pixel at 1440/1024/768 px; no
  inherited desktop copy spacing at 390/320 px; light/dark image loading;
  keyboard/pointer scrolling of each image strip without moving the other;
  and a native browser touch gesture in a mobile-emulated Chromium context.
  The touch check is not a physical iOS/Safari device test.
  Updated website captures, including the second picker image, are under
  `landing_page/artifacts/homepage-layout-frames/`; the normal section
  captures are under `landing_page/artifacts/visual-assets/playwright/captures/`.
  Human visual approval remains pending, including actual screenshot
  readability. Magnification, recapture, popup fixes, commits, and merges
  were not started. The local site remains on port 4175 for the review stop.
- 2026-10-05: The user selected B, separating four end-user highlights from
  two expanded deep-inspection highlights, and requested content-only layout
  flexibility. They clarified that all website/task/documentation work belongs
  in the main worktree; only specific product changes stay on develop for
  their testing before the agreed merge. Backed up the task-owned pending
  website files and candidate images under main's ignored
  `landing_page/artifacts/worktree-reconciliation/` before reconciling them.
  No unrelated research or product commits are included in this transfer.
- 2026-10-05 option B checkpoint: implemented the selected four compact
  end-user features and two expanded inspection features in the main worktree.
  The same `FeatureShowcase`/`FeatureMedia`/`ProofImage` path renders all six;
  YAML order and optional per-item `layout: full-width` control arrangement.
  The full provider-example card treatment, chevrons, active/clickable dots,
  first/last boundaries, reduced-motion behavior, and resize/navigation cleanup
  are implemented. Native scrolling remains available. Controls stay inside
  reserved image-frame space, and no link, caption, or scroll hint follows
  the frame. Plugin/report visual sets now belong to their owning highlights;
  no separate gallery headings remain.
  Main verification: build, 8 content checks, 27 Playwright checks, 19 visual
  framework tests, and a focused 10-variant retained-image catalog check pass.
  Browser coverage includes both themes at 1440/1024/768/390/320 px, compact
  row alignment, wide/phone ratios, complete placeholder text, controls,
  keyboard/pointer/touch state synchronization, resize, and actual client-side
  navigation away/back.
  Independently built option A in an isolated temporary site with identical
  component/source files except `src/content/pages/home.yaml`. Its desktop
  and phone layout, image ratios, order, and navigation pass. Main remains B.
  A's dependency symlink caused Astro compile-cache resolution failures;
  cloning the already-installed dependencies resolved them. Port 4324 was
  owned by an unrelated Python server, so the verifier now selects a free
  port and verifies the response before testing. No unrelated service was
  stopped or configuration changed.
  Reconciliation removed only 11 unchanged-since-backup tracked website edits,
  the two task-created component files, and backed-up generated draft images
  from develop. `git status --short -- landing_page` there is now clean.
  Active code, tests, documentation, and review assets for this checkpoint
  are in main; product work and unrelated commits remain on develop.
  The LAN preview on port 4175 now runs from main. Layout screenshots and
  the content-only A verification record are under
  `landing_page/artifacts/homepage-option-b/`.
  Stop for human visual review. Final proof/capture approval, magnification,
  popup product fixes, product merges, commits, pushes, and publication remain
  outside this completed layout checkpoint.
- 2026-10-05 image-card correction: the user clarified that image frames must
  not wrap the entire feature section. Restored unframed feature-level copy
  and moved the reference card treatment to each carousel image. Added
  optional per-image descriptions alongside existing labels, rendered above
  the screenshot within its card. The standard provider examples retain
  their existing card without adding a second outer wrapper.
  Pagination dots now sit below the image card. Chevron buttons overlay
  the left/right sides at the actual screenshot center, measured independently
  of the image-heading height. Removed the old reserved bottom control band.
  Shared grid rows keep image headings and screenshot canvases aligned across
  compact desktop pairs and prevent height changes between slides.
  Main build and 8 content checks passed. All 27 Playwright checks passed
  across the focused 5-check feature suite and remaining 22 checks. Evidence
  includes optional title/description placement, image-card reference styling,
  unframed features, canvas ratios/alignment at all five widths in both
  themes, pagination below the card, chevron center within 1 CSS pixel, and
  native pointer/keyboard/touch/navigation behavior. Updated captures are
  under `landing_page/artifacts/homepage-image-cards/`.
  Option B's order, content-configurable widths, product worktree boundary,
  and later asset/magnification work are unchanged. No commit or product
  change was made; stop for visual review of this correction.
- 2026-10-05: The user approved committing the reviewed website checkpoint
  and continuing to the product popup/label step. Commit only this task's
  website implementation, review assets, tests, documentation, and task 018
  on main; exclude the concurrently edited parent/waitlist task files.
  The six `public/homepage-draft` images remain explicitly draft inputs for
  this reproducible local-review checkpoint; this commit does not approve
  final capture promotion or production publication. Next, implement
  Desktop/mobile two-line menu labels, Desktop popup sizing, and the selected
  OpenAI compaction message label on develop, then stop for review.
- 2026-10-05 popup checkpoint in progress: committed the reviewed website
  checkpoint on main as `82906d10` (`Refine homepage feature visuals`), excluding
  unrelated parent/waitlist edits. Product changes are being implemented on
  develop. The shared ordinary, application-action, rich-list, and config-option
  rows now allow two-line names. Desktop native popup width uses measured
  labels with space for icons/state/pins, and height follows rendered content
  within the screen limit. Native menu ownership/anchoring stays intact.
  The OpenAI message-action label and confirmation title are renamed while
  preserving stable IDs and dispatch. Product/native verification is in
  progress; no product commit, merge, new website capture, or publication.
- 2026-10-05 popup checkpoint complete; stop for human review:
  - Implemented the plugin-owned **OpenAI compaction up to here** message label
    and confirmation title on develop. Stable action IDs, inclusive message
    scope, eligibility, confirmations, and dispatch are preserved.
  - Shared ordinary action rows, custom application-action rows, rich-list
    options, and config dropdown options allow two-line names. Row height
    grows with text while icon/pin targets retain their space. Compact
    toolbar controls and neutral state-value labels keep their prior layout.
    Mobile modal height is bounded so long menus scroll.
  - Desktop uses system-font text measurement with padding/icon/state/pin
    space, bounded to 480 points and the available host/screen width. React
    reports actual header/content height; the native owner limits height to
    80% of the visible screen. Menu IDs guard against late resize events
    affecting a different menu. Native anchoring and dismissal remain.
    Overflow triggers now expose their button accessibility role; production
    message-menu triggers and text labels have stable test identifiers.
  - Verification passed: 18 compaction plugin tests; a new real
    FastAPI → `FetchTransport` → `RestAgentBackend` schema test; 76 shared
    package unit tests; 27 mobile component tests; 4 Desktop consumer tests;
    Desktop and mobile TypeScript checks; and `git diff --check`.
  - Final native verification passed with successful command exits:
    macOS `testMessageActionNamesWrapAndKeepPinsIndependent` and
    `testRichSessionUiModelAndPlacedActions` in
    `/tmp/clc-popup-labels-macos-sequential.xcresult`; the selected iOS
    `richSessionUi.e2e.test.ts` case with `--testNamePattern
    "wraps the compaction name"` on simulator
    `BC14B6EF-D3A1-4E5A-A791-CDEEFF8394F1`, logged in
    `/tmp/clc-popup-labels-ios-review.log`.
    Both menu checks cover wrapping, independent pins, dismissal, bounded
    height, and reaching/pinning the last item in an oversized list.
    The two unselected iOS cases and Android native UI tests were not run.
  - Shared test data lives in `test/fixture/action-menu-labels.json`. The
    actual compaction label is checked through HTTP; a synthetic longer
    action exercises wrapping. The final label fits completely in two lines
    on both platforms. Native geometry and screenshot OCR verify this;
    final visual acceptance belongs to the user. No `view_image` inspection
    was performed because that tool requires a full image path supplied by
    the user.
  - Review screenshots in the develop worktree:
    `desktop/crystal-lattice-control-desktop-rn/artifacts/action-popup-review/macos-message-actions.png`
    and
    `mobile/crystal-lattice-control-rn/artifacts/detox/action-popup-review/ios-message-actions.png`.
    These are native test evidence, not website asset promotion. Desktop
    uses the complete popover crop so a popup extending outside its host
    window is not cut off.
  - Test-harness fixes cover subpixel geometry tolerance, asynchronous pin
    updates, and UIKit's brief dismissal hit-test interception. One parallel
    native run lost a transient dropdown; final native runs were sequential.
    Keep macOS UI automation and simulator UI automation sequential to avoid
    focus interference. Debug warning banners are dismissed through their
    normal close control before the menu screenshot.
  - Updated maintained shared-menu, Desktop action/native-test, plugin-user,
    and SDK integration documentation on develop. The plugin README also
    has unrelated pending originator work; a later scoped commit must stage
    only this checkpoint's wording change from that file.
  - The existing website runtime UI fixture remains stale and still needs
    its planned refresh before new asset capture. The new isolated schema
    test does not claim that the older canonical website-fixture integration
    test passes. Debug native verification does not by itself close the
    separate reproducible release-capture producer work.
  - **HUMAN JUDGMENT:** Review the menus and authorize the product commit and
    next checkpoint. Trying the changes in the normal develop Desktop app
    requires its native rebuild/relaunch; the backend needs to load the
    updated plugin for the renamed action. Next, prepare the first composite
    connecting three visible plugin entries to Edit title, Generate title,
    and Summarize range, place it into the existing website highlight on main,
    and review desktop/mobile page captures. No product commit/merge, new
    website image work, push, or publication was performed in this checkpoint.
- 2026-10-06: The user authorized committing the popup checkpoint and asked
  for the next-step plan. Committed its 30 product/test/documentation files
  on develop as `9e053402` (`Improve action menu readability`). Excluded the
  three older pending picker/website-capture edits and unrelated task work.
  Rechecked the current develop baseline after intervening commits: 18 plugin
  tests, 1 real HTTP/SDK test, 27 mobile component tests, 4 Desktop consumer
  tests, both app type checks, and the staged whitespace check passed. The
  mobile suite emitted a non-failing React `act` warning. Prior successful
  native evidence remains recorded above; native suites were not repeated
  for this unchanged popup implementation.
  Updated this task on main with the bounded **Draft** checkpoint-3 plan:
  one real three-plugin Session actions composition, fresh native capture,
  four theme/shape derivatives, and review inside the existing homepage.
  Proposed only the explicit popup-commit integration timing exception;
  left the requirement merge gate unchanged pending approval. The exact
  popup patch passes a read-only apply check against main. No product merge,
  capture implementation, source generation/promotion, push, or publication
  was performed during this planning turn.
- 2026-10-06 reconciliation and checkpoint 3 started: the user approved
  correcting the plan and proceeding. Updated the plan to reconcile the
  existing three capture edits and their product/capture prerequisites onto
  main first. The scoped source list is `ebb053ac`, `2bfaf03c`, `4fab5568`,
  `7d46556b`, Desktop/mobile changes from `29604c23`, and `9e053402`.
  The old standalone review-package changes and unrelated develop commits
  are excluded. Changes remain uncommitted for the next human checkpoint.
  Execution will preserve pending patches, verify the reconciled copies and
  consumers, then remove only the migrated pending edits from develop.
- 2026-10-06 reconciliation verified: applied the scoped six-commit source
  changes to main without creating commits, excluding all four obsolete
  landing-review-package changes from `29604c23`. Saved the three pending
  files, their patch, hashes, and source commits under
  `landing_page/artifacts/plugin-session-actions-reconciliation/`. All three
  transferred files matched byte-for-byte. Main checks passed: 8 Desktop
  picker/theme/menu-consumer tests, 19 mobile menu/capture-consumer tests,
  1 action-fixture test, 28 plugin tests, 2 agent-profile core/HTTP tests,
  2 selected SDK HTTP integration tests, both app type checks, and whitespace.
  The SDK harness first selected main's incomplete `.venv`; rerunning with
  `/Users/ferenci84/.pyenv/versions/3.11.12/bin/python` passed. The 22 other SDK
  cases were deliberately not selected. There was no existing dedicated
  Desktop website-harness component suite; native capture remains the next
  decisive check. After rechecking both worktree hashes, reversed only the
  preserved pending patch on develop. Its remaining dirty files are unrelated
  task work. All reconciled changes remain reviewable and uncommitted on main.
- 2026-10-06 checkpoint 3 implemented; stop for review:
  - Added a focused real-backend/native capture using the three actual plugin
    packages, the public session/message/action APIs, production
    `RestAgentBackend`/`FetchTransport`, `ChatPane`, and its native menu.
    The sample uses the existing deterministic provider and makes no hosted
    inference request. Native checks verify actual IDs, labels, and row
    positions in both themes.
  - The capture builds current main source with the dedicated
    `.website-capture` bundle identity. Ordinary builds retain their release
    identity. Debug website capture uses its bundled JavaScript, its visible
    title is **Crystal Lattice Desktop**, and the owning window and popover
    share the fixed blue capture theme. The existing user Release instance
    remained running.
  - Window/popover pixels and geometry are exported as named XCTest
    attachments, retaining their actual relative positions without including
    unrelated desktop windows. Direct writes from the sandboxed runner were
    denied during the first attempt; attachment export resolved that without
    requesting system permission. A text-label selector was also corrected
    to production transcript IDs/native user-message values. Teardown runs
    after failures and closes only the capture instance started by the test.
  - Final native evidence: `npm run capture:session-actions:macos` with
    `PYTHON=/Users/ferenci84/.pyenv/versions/3.11.12/bin/python` passed its
    backend/SDK/native integration check and both selected XCTest cases.
    The final command exit is `0` in
    `desktop/crystal-lattice-control-desktop-rn/artifacts/website-session-actions/capture.exit`.
    `contract.json`, both source PNG pairs, geometry, and `.xcresult` bundles
    are in that directory. This verifies the source checkout, not a rebuilt
    public release artifact.
  - Added the `homepage-session-actions` catalog candidate and maintained
    composition recipe. ImageMagick combines real native pixels and bakes
    three links from the loaded config's declarations to their actual rows.
    Its four derivatives are 2400 × 1350 wide and 1200 × 1600 compact, in
    light/dark. Current sizes are approximately 93/94 KB wide and 59/58 KB
    compact; all meet the 240 KB per-derivative budget. The manifest records
    source/config/recipe hashes, crops, row/name bounds, and endpoints.
  - Phone refinements preserve whole plugin names, keep the configuration
    clear of carousel arrows, and tighten the real menu crop without
    clipping its names. Connector curves stay between their endpoint columns
    and avoid the source text. OCR recognizes all three action names in
    desktop, 390px, and 320px page captures; it is supporting text evidence,
    not a substitute for visual review.
  - Optional compact image fields use the existing shared renderer: compact
    features choose portrait sources at every size, while expanded features
    switch below 760px. Both picture-source and image URLs follow the active
    theme. Alt text explicitly names each package/action relationship.
  - The explicit `CRYSTAL_SESSION_ACTIONS_PREVIEW=1` build overlays only this
    candidate onto the existing first plugin-image slot and copies derivatives
    into `artifacts/plugin-session-actions-site/`. Authored homepage YAML,
    reviewed source masters, and `public/` remain unchanged. Aggregate catalog
    inspection/checking records this unreviewed candidate as not run unless
    explicitly selected; its selected inspect/check commands passed.
  - Website evidence: 8 content tests, 21 visual-pipeline tests, 11 focused
    preview Playwright checks, 9 existing feature/theme Playwright checks
    against the preview, and 8 normal-site visual scenarios passed.
    The focused checks cover all five planned widths in both themes, source
    switching on resize, full plugin-name bounds outside carousel controls,
    active theme, navigation, neighboring placeholders, ratios, and overflow.
    Desktop and native-harness TypeScript checks and whitespace checks passed.
  - An isolated actual-site option-A build verified portrait sources and 3:4
    frames at 1440 and 390 pixels. Production component code was unchanged;
    content reordered the six items and removed their full-width flags.
    The temporary build enabled Vite symlink preservation to resolve the
    shared dependency directory; its first attempt exposed that temporary
    build-path issue. The temporary source/build and server were removed.
    The live main preview remains option B.
  - Updated the Desktop capture guide, landing processing/content-system
    guides, and durable visual-decision record, retaining the prior placeholder
    baseline and the unselected single-wide/stacked alternatives.
    The focused producer always captures both required themes of this one
    scene in one backend lifetime; it does not add an arbitrary scene/output
    selector. This is a bounded implementation choice, not a new requirement.
  - Review page: `http://192.168.8.227:4182/#feature-plugins`, verified HTTP 200
    locally and through the LAN address. The preview PID/log are under
    `landing_page/artifacts/plugin-session-actions-review/`. Primary browser
    screenshots are `desktop.png` and `mobile.png` there; all five widths,
    both themes, OCR output, and option-A checks are also retained.
  - **HUMAN JUDGMENT — STOP:** review the first composition, especially narrow
    phone readability, and authorize any next commit/work. The `view_image`
    tool still requires the user to supply full screenshot paths; no
    `view_image` inspection or final visual acceptance is claimed.
    Remaining images, canonical mobile-workbench fixture refresh, source
    promotion, release/publication work, and further product integration
    remain outside this completed implementation checkpoint.
- 2026-10-06 mobile composition revision approved: the user accepts Desktop
  and selects full-width code above an enlarged, identifiable popup for
  mobile. Matching physical-marker-style highlights replace mobile connector
  lines; code background highlighting is included as the suggested aid.
  Preserve the previous side-by-side candidate and rationale, retain accepted
  Desktop bytes, use actual captured popup chrome/rows, and mark any omitted
  middle region as a crop. This changes the image composition only, on main;
  no product changes, native recapture, commit, or publication are needed.
- 2026-10-06 stacked phone revision implemented; stop for review:
  - The 1200 × 1600 portrait now has full-width code above a magnified native
    popup excerpt. The same blue/teal/purple translucent, uneven marker bands
    pair each declaration with its actual action row; no mobile connections
    are drawn. The code remains valid JSON derived from the loaded config.
  - Preserved the real captured popup header, close control, and rounded
    edges. A visible crop interruption marks the unrelated middle entries
    omitted from the enlargement. Native row coordinates drive the crops and
    highlights; their source segments and omission bounds are recorded.
    Masked the outside shadow area after OCR exposed background conversation
    fragments, without replacing popup text or controls.
  - Both reviewed Desktop derivatives remain byte-identical. The recipe
    guards their SHA-256 values against accidental regeneration changes.
    Saved the prior side-by-side definition, candidates, manifest, and page
    captures under
    `landing_page/artifacts/plugin-session-actions-review/before-mobile-stacking/`.
    The durable decision record preserves that alternative and explains the
    selected stack/highlight treatment.
  - Verification passed: selected candidate inspect/check, 22 visual-pipeline
    tests, and 11 responsive Playwright checks at the five widths in both
    themes. New checks prove portrait stacking, absence of connectors,
    retained popup chrome/crop provenance, and declaration/action bounds clear
    of carousel controls. All derivatives stay within the existing budget.
    The normal source captures and product code were reused unchanged.
  - The existing LAN preview serves the update at
    `http://192.168.8.227:4182/#feature-plugins` (HTTP 200).
    Refreshed phone screenshots are `mobile.png`, `390-light.png`,
    `320-light.png`, and their dark counterparts under
    `landing_page/artifacts/plugin-session-actions-review/`.
    OCR output there is supporting text evidence only. `view_image` was not
    used because its full-path input requirement remains unmet.
  - **HUMAN JUDGMENT — STOP:** review the revised phone image. No new commit,
    source promotion, other image production, or publication was performed.
- 2026-10-06 first visual accepted; next checkpoint planned: the user approves
  the revised version and requests a proposal. Marked the combined Desktop/
  phone review complete and recorded the selected treatment in the durable
  decision document. Proposed only the second plugin-highlight image,
  **Actions for each message**, as a Draft next checkpoint: three actual
  package declarations → Fork here, Summarize messages up to here, Share as
  PDF, and Share as Markdown. The export declaration maps to both exports.
  Native source inspection confirms the real schema IDs and package
  descriptor entries. Keep the accepted first image frozen and reuse its
  Desktop/phone design. A scoped checkpoint commit is recommended separately.
  No new source capture, code implementation, test run, commit, promotion,
  push, or publication occurred during this planning turn.
- 2026-10-06 accepted checkpoint commit authorized: the user explicitly
  authorizes committing the accepted state before expanding the next plan.
  The commit includes the previously reconciled product/capture prerequisites,
  first Session actions producer/composition/responsive preview, and its
  approval/decision records. The unrelated parent and waitlist task edits
  remain outside this commit. Rechecked all 22 visual-asset tests and the four
  current candidate derivatives successfully. No push or publication is
  authorized. The requested icon correction and larger image batch are
  subsequent work, not part of this accepted implementation snapshot.
