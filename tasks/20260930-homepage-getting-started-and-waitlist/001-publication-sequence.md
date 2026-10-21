# Track The Homepage Publication Sequence

Parent Task:
`tasks/20260930-homepage-getting-started-and-waitlist/000-main.md`

This is the coordination umbrella for the homepage redesign, UI walkthrough,
mobile waitlist, and publication. It determines execution order, records
human-review gates, and tracks completion across the implementation subtasks.
It does not own product code, website components, captures, AWS resources, or
requirements already owned by those subtasks.

## Requirements checklist

- [ ] The umbrella keeps one current, human-readable sequence from the
      completed homepage foundation through the publishable UI walkthrough,
      real waitlist integration, production approval, publication, and
      post-publication verification.
- [ ] Every implementation outcome remains owned by its dedicated task. This
      file summarizes order and evidence without silently adding, replacing,
      or weakening child requirements.
- [ ] Material human-judgment checkpoints are explicit and stop execution
      until the user approves the reviewed result.
- [ ] Mandatory account-owner, AWS, privacy, and production-publication
      actions remain visibly distinct from agent work.
- [ ] A phase is marked complete only when the owning task records evidence
      and any required human review is confirmed.
- [ ] Later work does not begin merely because its filename follows an earlier
      task; the explicit sequence and dependency gates below control execution.
- [ ] The tracker is updated as checkpoints complete so another agent can
      resume without reconstructing the order from conversation history.
- [ ] Final completion requires a verified production homepage, working
      download paths, working waitlist confirmation/withdrawal, removal of
      controlled test records, and updated child/parent completion evidence.

## Tracked implementation tasks

- `tasks/20260930-homepage-getting-started-and-waitlist/010-homepage-structure-prototype.md`
  — completed structural prototype and responsive baseline.
- `tasks/20260930-homepage-getting-started-and-waitlist/015-homepage-content-assets-layout.md`
  — completed content, download-layout, placeholder, and durable-decision
  baseline.
- `tasks/20260930-homepage-getting-started-and-waitlist/018-homepage-visuals-product-improvements.md`
  — product/capture improvements and accepted Plugin, Transparency, and Vibe
  evidence; remaining bookkeeping and ownership handoff must be reconciled.
- `tasks/20260930-homepage-getting-started-and-waitlist/019-publishable-homepage-ui-walkthrough.md`
  — approved bottom-up walkthrough, candidate selection, remaining features,
  Getting Started/mobile presentation, release cut, and final local homepage.
- `tasks/20260930-homepage-getting-started-and-waitlist/020-aws-email-waitlist.md`
  — AWS waitlist, real form, privacy integration, final integrated review,
  production publication, and production verification.

## Current status

| Sequence | Owning task | Status | Next gate |
| --- | --- | --- | --- |
| Foundation structure | `010` | Complete | None |
| Content/layout baseline | `015` | Complete | None |
| Existing visual/product evidence | `018` | In progress; ownership reconciled | Retain historical evidence and deferred bookkeeping |
| Publishable homepage | `019` | H3 responsive multi-frame storyboard prepared | Human checkpoint H3A: approve frames, captions, and responsive reading model |
| Waitlist and publication | `020` | Draft; blocked by `019` | Begins only after H6 homepage approval and handoff |

## Execution plan

Status: Approved

The sequence is intentionally divided into a publishable-homepage phase and a
final waitlist/publication phase. Candidate production is broader than final
homepage selection: viable real-product images are placed on the actual local
page, reviewed responsively, and then selected, moved, or deferred at a human
gate.

### Phase A — Reconcile the completed foundation

1. Confirm the completed evidence and current ownership recorded by `010`,
   `015`, and `018`.
2. Keep the accepted Vibe, Plugin, Transparency, popup, icon, and capture
   foundations available to `019`.
3. Record remaining `018` bookkeeping or deferred scope without reopening
   accepted evidence or duplicating new `019` ownership.

No additional visual direction is selected in this phase.

### Phase B — Build the publishable homepage

#### H1 — Candidate storyboard

Agent work:

- verify public claims for composer cancellation/resend, message metadata,
  action scope, session settings/plugins, request status, and connections;
- prepare the bottom-up Compose → Messages → Session actions → Session
  settings → Workspace storyboard;
- describe the fourteen candidate sources, their copy, composition,
  dependencies, and proposed destinations.

**HUMAN JUDGMENT:** Approve the teaching order, claims, screenshot
responsibilities, and candidate destinations before new capture production.

#### H2 — Candidate selection on the real page

Agent work:

- implement approved product/capture prerequisites on `develop`;
- verify them and reconcile only website-used changes to `main`;
- create viable responsive candidates through real product boundaries;
- bind them temporarily to the actual homepage;
- inspect desktop/phone and light/dark states with Playwright and
  `view_image`.

**HUMAN JUDGMENT:** Select what belongs in the introductory walkthrough,
Plugins/Transparency/another feature, Getting Started, documentation, later
work, or the rejected set.

#### H3 — Selected walkthrough in context

Agent work:

- prepare and review the responsive multi-frame storyboard before replacing
  the preserved one-image implementation;
- implement a progressively enhanced Desktop stage with labeled chapters,
  focused frames, image-edge arrows, and no autoplay;
- render all chapters and frames in ordinary vertical document order on
  mobile, without requiring tabs, dots, arrows, or swipe to discover content;
- use visitor-facing image titles and captions that explain what relationship
  to inspect;
- preserve clear scope from request to message, session, settings, workspace,
  and the final client/runtime connection boundary;
- verify that Compose explains a complete product and that the separate
  Agent, provider-settings, and Plugins/Tools frames remain legible.

**HUMAN JUDGMENT — H3A:** Approve the chapter/frame storyboard, draft
visitor-facing captions, Desktop interaction, and mobile vertical reading
order before component implementation.

**HUMAN JUDGMENT — H3B:** Approve the implemented walkthrough's clarity,
visual rhythm, legibility, responsiveness, and transition into the remaining
feature sections.

#### H4 — Features, Getting Started, and Mobile access

Agent work:

- finalize Vibe, Work from anywhere, Plugins, and Transparency;
- complete the truthful Desktop/mobile continuity proof;
- complete the six Getting Started steps;
- group the mobile app and mobile connection steps;
- explain local discovery, address/port, and bridge in visitor order;
- keep the Desktop path local by default and explain trusted-network exposure
  when LAN discovery is enabled.

**HUMAN JUDGMENT:** Approve feature proof, captions, release availability,
downloads, connection concepts, and network-security language.

#### H5 — First-release content cut

Agent work:

- remove placeholders, fake forms, internal planning language, and unverified
  examples;
- retain only advanced homepage material with a verified claim, clear
  audience, and distinct purpose;
- move detailed bridge, SDK, provider, compatibility, plugin-authoring, or
  action-reference material to documentation when it does not serve the first
  homepage;
- maintain clear advanced-user routes.

**HUMAN JUDGMENT:** Approve every retained, moved, deferred, and rejected
advanced section.

#### H6 — Local homepage ready for waitlist integration

Agent work:

- promote only approved visual sources and bindings;
- complete durable design/asset documentation;
- run content, asset, freshness, accessibility, responsive, light/dark,
  download, availability, security-copy, privacy-scan, and link verification;
- confirm there are no invalid icons, private task data, raw capture
  artifacts, unsupported claims, or review-only UI.

**HUMAN JUDGMENT:** Approve the complete local homepage as publishable apart
from the real waitlist form.

After H6, mark the applicable `019` requirements and checklist complete and
hand the reviewed local site to `020`. Do not publish yet.

### Phase C — Integrate the real waitlist and publish

#### H7 — Waitlist policy and AWS deployment readiness

Agent work:

- inspect SES identity/sandbox and the target AWS environment read-only;
- prepare the dedicated API Gateway/Lambda/DynamoDB/SES/SNS implementation,
  tests, deployment package, privacy changes, and operations documentation.

**HUMAN JUDGMENT:** Approve sender identity, consent/confirmation copy, and
retention/deletion policy.

**HUMAN — MANDATORY:** Complete any required SES identity, DNS, or production
access action that cannot be safely automated.

**HUMAN — MANDATORY:** Explicitly approve AWS deployment.

#### H8 — Integrated website review

Agent work:

- deploy and verify the waitlist service through its public HTTPS path;
- integrate the real accessible form into the approved mobile step;
- verify signup, confirmation, storage, withdrawal, suppression, privacy,
  responsive behavior, and absence of secret or personal-data exposure;
- build and preview the complete integrated website.

**HUMAN JUDGMENT:** Approve the form behavior, consent presentation,
confirmation message, privacy wording, and complete integrated page.

#### H9 — Production publication

**HUMAN — MANDATORY:** Explicitly approve production website publication.

Agent work after approval:

- publish through the protected website workflow;
- monitor the deployment;
- verify the anonymous production page, downloads, form, confirmation,
  storage, withdrawal, and mobile/platform availability;
- remove controlled test records;
- update `020`, this tracker, and the parent task with completion evidence.

### Implementation decisions and open questions

- **Decision:** `001` is a coordination tracker, not another implementation
  owner.
- **Decision:** child requirements and evidence remain authoritative when this
  summary and a child file differ; reconcile the tracker immediately rather
  than changing child scope silently.
- **Decision:** execution follows explicit H1–H9 gates, not filename ordering
  alone.
- **Decision:** H1–H6 produce the approved local homepage; H7–H9 add the real
  waitlist and produce/verify the public website.
- **Decision:** candidate production is deliberately broader than public
  selection.
- **Decision:** product changes needed by website proof are implemented and
  verified on `develop`, then reconciled to `main` only after they are
  confirmed and used.
- **Decision:** no AWS deployment or production publication is implied by
  approval of the homepage plan.
- **Open human decisions remain in `020`:** sender identity,
  consent/confirmation copy, retention/deletion policy, AWS deployment, and
  production publication.

### Documentation

- Keep this sequence synchronized with child status, checkpoint acceptance,
  commit/deployment evidence, and current blockers.
- Put durable copy/visual rationale in the landing package's development
  documentation, not solely in this tracker.
- Put AWS architecture, deployment, privacy, and operator details in the
  waitlist package/public privacy documentation owned by `020`.
- Do not copy secrets, account identifiers, email addresses, raw tokens, or
  internal deployment diagnostics into this file.

### Task checklist

- [x] Complete structural prototype `010`.
- [x] Complete content/assets/layout baseline `015`.
- [x] Reconcile completed/deferred `018` ownership with `019`.
- [x] **AGENT:** Prepare H1 candidate storyboard.
- [x] **HUMAN JUDGMENT — H1:** Approve candidate storyboard.
- [x] **AGENT:** Produce and bind the H2 candidate set on the actual page.
- [x] **HUMAN JUDGMENT — H2:** Select candidate destinations.
- [x] **AGENT:** Implement the selected walkthrough.
- [ ] **HUMAN JUDGMENT — H3:** Approve the walkthrough in context.
- [ ] **AGENT:** Complete features, Getting Started, and Mobile access.
- [ ] **HUMAN JUDGMENT — H4:** Approve features and setup flow.
- [ ] **AGENT:** Apply the first-release content cut.
- [ ] **HUMAN JUDGMENT — H5:** Approve retained/deferred advanced content.
- [ ] **AGENT:** Complete homepage verification and source promotion.
- [ ] **HUMAN JUDGMENT — H6:** Approve the local homepage for waitlist
      integration.
- [ ] **AGENT:** Prepare the waitlist service and deployment evidence.
- [ ] **HUMAN JUDGMENT — H7:** Approve policy decisions.
- [ ] **HUMAN — MANDATORY — H7:** Complete required account-owner actions and
      approve AWS deployment.
- [ ] **AGENT:** Deploy, verify, and integrate the waitlist.
- [ ] **HUMAN JUDGMENT — H8:** Approve the complete integrated website.
- [ ] **HUMAN — MANDATORY — H9:** Approve production publication.
- [ ] **AGENT:** Publish, monitor, verify production, and remove test records.
- [ ] **AGENT:** Complete `019`, `020`, this tracker, and the parent task with
      evidence.

### Requirement verification

- Ordering requirement: task inspection shows each implementation step and
  human gate mapped to its owning child and no later phase marked complete
  before its prerequisites.
- Human-gate requirement: checkpoint completion records the reviewed artifact
  or deployed boundary and explicit user acceptance.
- Child-ownership requirement: implementation evidence appears in `018`,
  `019`, or `020`; this file contains status and links rather than duplicate
  hidden requirements.
- Homepage-ready boundary: H6 evidence proves the complete local page through
  production-like browser, accessibility, visual, download, security-copy,
  source-freshness, and private-data checks.
- Waitlist-ready boundary: H8 evidence crosses the real browser → public HTTPS
  endpoint → storage → SES confirmation → withdrawal path.
- Publication boundary: H9 includes explicit human approval, successful
  protected deployment, anonymous production checks, authenticated state
  verification, and controlled-test cleanup.
- Completion boundary: all parent requirements map to completed child
  evidence, and unresolved/deferred work is explicitly recorded rather than
  implied complete.

### Additional implementation verification

- Review this tracker at every human checkpoint and before each deployment.
- Ensure commit status, worktree ownership, and branch reconciliation are
  explicit before source promotion.
- Treat skipped, blocked, or gated checks as not run unless their prerequisite
  was deliberately enabled and the result was verified.

## Implementation Notes

- 2026-10-11: H1 source verification and the fourteen-candidate storyboard are
  complete in subtask `019`. Execution is paused at the required H1 human
  checkpoint before product/capture changes or candidate binding.
- 2026-10-11: `018` remains the historical evidence owner for accepted Vibe,
  Plugin, Transparency, popup, icon, and capture-pipeline work. `019` owns all
  new candidate production, selection, page restructuring, remaining feature
  proof, and local publish-ready acceptance.
- 2026-10-13: The user approved the H1 storyboard. H2 then produced the
  fourteen-candidate pool through real product/capture boundaries, bound the
  candidates to an opt-in version of the actual homepage, and verified normal
  public builds remain unchanged.
- 2026-10-13: H2 agent work is complete and paused at the required human
  candidate-selection checkpoint. Responsive light/dark Playwright review
  covers 1440, 1024, 768, 390, and 320 CSS pixels; every carousel candidate
  also has focused 1440- and 390-pixel captures for visual judgment.
- 2026-10-13: The user approved the H2 content and teaching order, with the
  explicit condition that every selected image receive an individual
  phone-legibility treatment and that Getting Started retain all required
  code, download, and image evidence. H3 may begin, but must stop at its human
  walkthrough-in-context checkpoint before H4.
- 2026-10-13: H3 is agent-complete. The selected five-chapter walkthrough,
  responsive wide/compact compositions, interaction/accessibility behavior,
  normal-build isolation, and responsive light/dark browser matrix are
  implemented and verified. Execution is paused at the required H3 human
  walkthrough-in-context checkpoint.
- 2026-10-16: H3 human review found the first compact compositions unreadable
  on an iPhone 12 Mini and rejected their overlapping magnifier treatment.
  The first implementation is preserved in main commit `747b20fc`; H3 is
  undergoing a focused responsive-composition revision and remains at the
  same human checkpoint. H4 and every later publication step remain blocked.
- 2026-10-16: The H3 responsive revision is agent-complete and verified at the
  same checkpoint. It replaces the fixed 4:5 compact media with
  chapter-specific natural heights and non-overlapping source/detail
  compositions. Human acceptance is still required before H3 can be checked
  off or H4 can begin.
- 2026-10-16: A second H3 mobile refinement was approved after the readable
  images proved taller than a phone viewport. Pre-adjustment state is
  preserved in main commit `b2f16e0b` and develop commit `06ba19fa`. The new
  H3 acceptance target is a full-width, whole-image viewport fit with
  image-edge chapter arrows; H4 remains blocked pending review.
- 2026-10-16: The second H3 mobile refinement is agent-complete and verified
  through short-phone light/dark browser coverage. It remains uncommitted and
  paused at the same H3 human checkpoint; no later publication step has
  started.
- 2026-10-16: The second H3 refinement was preserved on `main` as
  `b2a06b40`. Human review then approved replacing its one-image-per-chapter
  interaction with a six-chapter, thirteen-frame model: Desktop uses labeled
  chapters and image-edge frame arrows; mobile exposes the complete sequence
  through ordinary vertical scrolling. Subtask `019` is paused at H3A for
  review of the recorded frame order and draft visitor-facing captions before
  component implementation. H4 remains blocked.