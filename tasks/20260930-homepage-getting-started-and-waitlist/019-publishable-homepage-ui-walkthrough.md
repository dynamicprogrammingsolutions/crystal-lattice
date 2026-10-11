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
- [ ] The walkthrough covers, in a coherent teaching order: the overall
      session workspace; agent-profile selection; the session list and
      session-level actions; message details and footers; message-level
      actions; and connections.
- [ ] Each walkthrough stage first explains the ordinary role of the UI area,
      then introduces the relevant Crystal Lattice distinction. It does not
      assume familiarity with coding-agent products, provider terminology,
      plugins, session history operations, or connection architecture.
- [ ] The overview makes clear that Crystal Lattice organizes agent work into
      durable sessions, while the agent-profile stage explains that a profile
      can change the provider route, instructions, tools, features, and UI
      behavior rather than only selecting a model name.
- [ ] Public wording distinguishes Crystal Lattice Codex-, Claude-, Gemini-,
      Qwen-, Kimi-, Grok-, and related profiles from official upstream
      applications, accounts, and sessions.
- [ ] The walkthrough uses one consistent, sanitized product fixture so the
      same connection, agent, session, title, status, user request, assistant
      response, and visual identity persist while the tour moves through UI
      areas. Screenshots remain real product UI; composition may crop,
      highlight, or magnify source regions without inventing controls or
      values.
- [ ] Walkthrough navigation exposes descriptive labels such as Overview,
      Agent, Sessions, Details, Actions, and Connections. It is responsive,
      keyboard accessible, swipe/scroll compatible, reduced-motion aware,
      and understandable without relying on unlabeled dots or autoplay.
- [ ] The former separate **One workspace for every model family** and
      **Sessions become workspaces** compact highlights are incorporated into
      the walkthrough without losing their approved values or durable
      alternatives. The remaining feature sequence is Vibe/Work from anywhere
      as compact end-user highlights, followed by the full-width Plugins and
      Transparency deep dives.
- [ ] The walkthrough explains UI roles without duplicating the later deep
      dives: it identifies what session/message controls and metadata do;
      Plugins later explains how configuration contributes replaceable UI;
      Transparency later demonstrates inspectable instructions and reporting.
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

- **HUMAN JUDGMENT — WALKTHROUGH STORYBOARD:** Review the six-stage teaching
  sequence, stage titles, proposed explanations, distinctive claims, and the
  role of each screenshot before component implementation and new capture
  production.
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
  session list, active conversation, session actions, message actions, and
  response metadata. A Desktop Connections panel exists and has a maintained
  harness but needs a selected website capture state.
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

## Execution plan

Status: Approved

The first public version will teach the product through its UI before asking
the visitor to install it. The walkthrough is a single full-width section
after the hero. A persistent introductory title/body establishes the product
category; labeled stages then move through one coherent product fixture.

The working section direction is:

> **A workspace for agent sessions.**
>
> Crystal Lattice organizes agent work into sessions. Choose how an agent
> works, keep each task in its own session, inspect what happened, and act on
> the whole session or an individual message. Desktop and mobile clients
> expose the same underlying sessions.

This wording is a review baseline, not pre-approved final public copy. The
storyboard checkpoint owns final phrasing.

The walkthrough uses a split presentation on desktop: explanation on one side
and the product image on the other. Phones stack explanation above the image.
The stage controls remain visible and named. The section does not autoplay.
The current feature-image component may be extended when it can preserve its
existing consumers cleanly; a dedicated walkthrough component is acceptable
if the teaching layout and accessibility needs would otherwise distort the
ordinary image strips.

### Walkthrough stages

| Stage | Visitor question | UI proof | Distinction introduced |
| --- | --- | --- | --- |
| **Overview** | What am I looking at? | Clean Desktop view with session list, selected session, conversation, and composer | A task lives in a durable session with workflow state, not only a transcript |
| **Agent** | How is the agent chosen? | Real agent picker with the family-oriented profile list and selected profile details | A profile can change provider route, instructions, tools, features, and controls, not only the model name |
| **Sessions** | How is work organized and controlled? | Real session list with titles/subtitles, statuses, pins, selected row, and Session actions | Session actions affect the whole task; application plugins can contribute or replace these controls |
| **Details** | What can I learn about a response? | User/assistant content with a readable genuine message footer and relevant reasoning/tool state | Metadata such as token/cache/duration/cost remains attached to the response when the provider supplies it |
| **Actions** | What can I do from one message? | Real Message actions popup at a specific assistant message | Modify, fork, summarize, export, delete, or compact from an exact point in history; this scope differs from session actions |
| **Connections** | Where do these sessions come from? | Real Desktop Connections panel with a focused local record and current status | A connection selects where the workspace is running; connections are not sessions |

The Overview stage is self-sufficient: a visitor who does not advance the
walkthrough still understands the product category and primary UI. Later
stages deepen understanding rather than supplying a missing prerequisite.

All walkthrough slides use one deterministic fixture. The Overview is clean.
Subsequent images preserve application context while outlining, dimming, or
magnifying the current area. Configuration-to-control connector lines remain
exclusive to the later Plugins proof. The walkthrough teaches visible roles,
not plugin internals.

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
incorporated into the Agent, Overview, and Sessions stages and retained in the
durable decision record.

### Remaining feature and Getting Started work

**Vibe code—or vibe anything** keeps the accepted System → User → initial
reasoning image. Review its final caption in the new page rhythm.

**Work from anywhere** receives one real Desktop/phone composition over the
same session fixture. It proves continuity rather than connection setup. The
caption states current public/tester/invite availability.

**Plugins** and **Transparency** retain their accepted proof concepts. Rewrite
their image comments to explain what each image proves instead of repeating
generic “plugin-driven and easy to adjust” wording. Keep sample/provider
qualifications and reviewed assets.

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
2. Prepare the six-stage storyboard with exact visitor question, draft copy,
   source UI state, differentiating statement, desktop composition, phone
   composition, and capture/product dependencies.
3. Stop at the storyboard checkpoint for human judgment.
4. Implement the approved information architecture and accessible walkthrough
   behavior with local candidate states.
5. Produce or refresh genuine Desktop/mobile sources through the maintained
   public/native capture boundaries. Put genuine product improvements on
   `develop`, verify them there, and reconcile only confirmed website-used
   changes onto `main`.
6. Compose responsive walkthrough assets and the remaining Work from anywhere,
   Desktop connection, and mobile connection proofs.
7. Bind candidates to the actual page and inspect every slide and section with
   Playwright plus direct `view_image` review.
8. Stop at the walkthrough-in-context checkpoint.
9. Refine remaining feature order, captions, availability, compatibility, and
   proof based on the accepted walkthrough.
10. Revise Getting Started, the Mobile access grouping, local/LAN security
    language, and current release states.
11. Stop at the Getting Started/mobile checkpoint.
12. Apply the lower-page release cut and verify all retained examples and
    links.
13. Stop at the release-cut checkpoint.
14. Complete responsive, accessibility, source-freshness, content, download,
    security-copy, and full-page verification.
15. Stop at the final publish-ready checkpoint.
16. After human acceptance, promote only approved visual sources and update
    maintained public bindings. Do not push or publish.
17. Hand the approved local website to subtask `020` for the real waitlist,
    privacy integration, final integrated review, and explicitly approved
    production publication.

### Implementation decisions and open questions

- **Decision:** the introductory walkthrough teaches the product UI; it does
  not replace Getting Started or begin with commands, ports, project
  directories, server binding, or installation architecture.
- **Decision:** the walkthrough order is Overview → Agent → Sessions →
  Details → Actions → Connections.
- **Decision:** the walkthrough explains ordinary UI role before
  differentiation and introduces plugin/provider terminology only after the
  visible behavior is understandable.
- **Decision:** model-family breadth and durable-session value move into the
  walkthrough instead of remaining separate compact advertisements.
- **Decision:** the same fixture and visual coordinate system carry the
  visitor through the walkthrough.
- **Decision:** labeled stage controls are required; dots may remain only as a
  secondary position indicator.
- **Decision:** Session actions and Message actions retain distinct scopes in
  the explanation.
- **Decision:** message footers explain provider-supplied transparency at the
  response level; the later Transparency section continues to own compiled
  instructions and custom reporting.
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
  stage titles, final public descriptions, and whether any two neighboring
  stages should share one visual without losing the requested UI-area
  explanations.
- **Open human judgment at release-cut checkpoint:** which verified lower-page
  advanced sections remain on the first homepage versus moving to
  documentation or later revisions.

### Documentation

- Append the approved UI-teaching sequence, role-before-difference theory,
  stage alternatives, final copy, visual mappings, release cuts, and rationale
  to
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
- [ ] **AGENT:** Prepare the detailed six-stage storyboard and preserve the
      current baseline.
- [ ] **HUMAN JUDGMENT — CHECKPOINT 1:** Approve the storyboard, exact teaching
      order, proposed claims, and visual responsibilities.
- [ ] **AGENT:** Implement the responsive accessible walkthrough shell and
      revised homepage information architecture.
- [ ] **AGENT:** Capture and compose the approved walkthrough and remaining
      feature sources through real product boundaries.
- [ ] **HUMAN JUDGMENT — CHECKPOINT 2:** Review the complete walkthrough in
      page context at desktop and phone widths.
- [ ] **AGENT:** Finalize remaining feature order, captions, proof, and
      availability distinctions.
- [ ] **AGENT:** Implement and verify the six-step Getting Started and grouped
      Mobile access treatment.
- [ ] **HUMAN JUDGMENT — CHECKPOINT 3:** Review Getting Started, mobile
      availability, connection concepts, and trusted-network language.
- [ ] **AGENT:** Apply the verified lower-page release cut and advanced-user
      routes.
- [ ] **HUMAN JUDGMENT — CHECKPOINT 4:** Approve retained, moved, and deferred
      advanced content.
- [ ] **AGENT:** Complete all release-candidate verification and documentation.
- [ ] **HUMAN JUDGMENT — CHECKPOINT 5:** Approve the complete local
      publish-ready website and candidate source promotion.
- [ ] **AGENT:** Promote approved sources and hand the local website to
      subtask `020`; do not push or publish.

### Requirement verification

- Visitor-understanding boundary: moderated human review starts at the hero
  with no prior product explanation. The reviewer must correctly identify the
  product as an agent-session workspace and explain agent profiles, sessions,
  session actions, message footers/actions, and connections after the
  walkthrough without using Getting Started.
- Walkthrough UI boundary: each stage uses source-fingerprinted production
  components/native captures with one consistent fixture. Inspection maps
  every described control/metadata field to the genuine source; a duplicate
  mock menu or repainted data panel is insufficient.
- Differentiation boundary: copy inspection verifies that each stage explains
  role first, distinction second, distinguishes Crystal Lattice profiles from
  official upstream products, and does not imply uniform provider metadata.
- Navigation/accessibility boundary: browser tests cover descriptive stage
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