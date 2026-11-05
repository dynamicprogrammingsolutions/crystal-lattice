# Track The Homepage Publication Sequence

Parent Task:
`tasks/20260930-homepage-getting-started-and-waitlist/000-main.md`

This is the coordination umbrella for the homepage redesign, product overview,
mobile waitlist, and publication. It determines execution order, records
human-review gates, and tracks completion across the implementation subtasks.
It does not own product code, website components, captures, AWS resources, or
requirements already owned by those subtasks.

## Requirements checklist

- [ ] The umbrella keeps one current, human-readable sequence from the
      completed homepage foundation through the publishable product overview,
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

- `tasks/20261024-production-staging-website-channels.md`
  — highest-priority production restoration, staging source channel, staging
  AWS hosting, and dual deployment workflow.
- `tasks/20260930-homepage-getting-started-and-waitlist/010-homepage-structure-prototype.md`
  — completed structural prototype and responsive baseline.
- `tasks/20260930-homepage-getting-started-and-waitlist/015-homepage-content-assets-layout.md`
  — completed content, download-layout, placeholder, and durable-decision
  baseline.
- `tasks/20260930-homepage-getting-started-and-waitlist/018-homepage-visuals-product-improvements.md`
  — product/capture improvements and accepted Plugin, Transparency, and Vibe
  evidence; remaining bookkeeping and ownership handoff must be reconciled.
- `tasks/20260930-homepage-getting-started-and-waitlist/019-publishable-homepage-ui-walkthrough.md`
  — approved brief/copy/visual/image review workflow, selected product
  overview, remaining visual proof, Getting Started/mobile presentation,
  release cut, and final local homepage.
- `tasks/20260930-homepage-getting-started-and-waitlist/020-aws-email-waitlist.md`
  — AWS waitlist, real form, privacy integration, final integrated review,
  production publication, and production verification.

## Current status

| Sequence | Owning task | Status | Next gate |
| --- | --- | --- | --- |
| Foundation structure | `010` | Complete | None |
| Content/layout baseline | `015` | Complete | None |
| Existing visual/product evidence | `018` | Historical evidence retained; older layout/image plan paused | Task `019` consumes selected evidence after channel split |
| Production/staging channels | `tasks/20261024-production-staging-website-channels.md` | Public and verified; awaiting final human public-channel confirmation | Confirm public channels |
| Publishable homepage | `019` | H1 approved; channel blocker cleared | Resume at H2 Complete Opening Copy |
| Compatibility catalogue | website `030` | Focused source refresh accepted; full projection internal; channel blocker cleared | Resume at Canonical Tables checkpoint |
| Waitlist and publication | `020` | Channel dependency satisfied; own decisions and task `019` integration handoff remain | Resolve its own gates, then integrate after later H8 handoff |

## Execution plan

Status: Approved

The sequence now begins with a production/staging release-channel phase,
followed by the publishable-homepage phase, canonical compatibility tables,
and final waitlist/publication integration.

### Priority Phase — Restore production and establish staging

Owning task:
`tasks/20261024-production-staging-website-channels.md`

1. Restore production from exact historical baseline `d3fe28a6`.
2. Add the current six-step Getting Started section without empty media
   placeholders.
3. Preserve all other historical sections until contextual human review.
4. Move the in-progress current homepage into staging ownership.
5. Establish separate production/staging builds and local previews.
6. Establish the public no-index staging AWS/GitHub deployment channel.
7. Deploy and verify both channels only after their explicit gates.

Tasks `019`, compatibility UI work in website `030`, and waitlist website
integration remain paused during this phase.

As of November 4, 2026, this priority phase is implemented and publicly
verified. Tasks `019` and `030` are unblocked at their recorded checkpoints.
Task `020` has cleared only this channel dependency and remains gated by its
own decisions and task `019` handoff.

### Phase A — Reconcile the completed foundation

1. Confirm the completed evidence and current ownership recorded by `010`,
   `015`, and `018`.
2. Keep the accepted Vibe, Plugin, Transparency, popup, icon, and capture
   foundations available to `019`.
3. Record remaining `018` bookkeeping or deferred scope without reopening
   accepted evidence or duplicating new `019` ownership.

No additional visual direction is selected in this phase.

### Phase B — Build the publishable homepage

Candidate A and the earlier walkthrough remain in Git as comparison evidence.
They do not define the next implementation structure.

#### H1 — Brief and terminology

Agent work:

- define the page role, primary visitor, visitor questions, concept ownership,
  terminology, claim boundaries, and information order;
- reconcile parent/specification requirements that conflict with the revised
  direction.

**HUMAN JUDGMENT:** Approve or correct the brief and terminology before
selecting public copy.

#### H2 — Complete opening copy

Agent work:

- prepare complete alternative hero/overview directions rather than isolated
  headline fragments;
- include all headings, paragraphs, figure titles, captions, actions, and
  metadata in scope.

**HUMAN JUDGMENT:** Select or revise one complete direction.

#### H3 — Visual plan

Agent work:

- map the selected copy to intentional desktop and mobile compositions;
- define section rhythm, text measures, figure containment, frames,
  magnification targets, responsive behavior, and accessibility.

**HUMAN JUDGMENT:** Approve the visual system independently from copy.

#### H4 — Image shortlist

Agent work:

- map every retained image to one claim, real source, capture geometry,
  rendered-size target, title, caption, and disposition;
- remove redundant slots rather than filling them;
- specify the compact configured-agent capture and separately framed Desktop/mobile
  continuity sources.

**HUMAN JUDGMENT:** Approve the exact screenshot shortlist and capture
treatments before new implementation/capture work.

#### H5 — Opening candidate in context

Agent work:

- implement the approved opt-in opening candidate;
- recapture/select the approved real-product sources without promotion;
- bind them to the actual page;
- review light/dark desktop, tablet, and phone compositions.

**HUMAN JUDGMENT:** Approve the rendered opening copy, figures, visual rhythm,
and image readability before normal-content integration.

#### H6 — First-user flow

Agent work:

- integrate approved opening content and visual sources;
- complete the six Getting Started steps and Desktop/mobile connection proof;
- group Mobile access;
- explain local discovery, address/port, and bridge in visitor order;
- keep the Desktop path local by default and explain trusted-network exposure
  when LAN discovery is enabled.

**HUMAN JUDGMENT:** Approve the complete overview, Getting Started path,
availability wording, downloads, and connection/security language.

#### H7 — First-release content cut

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

#### H8 — Local homepage ready for waitlist integration

Agent work:

- promote only approved visual sources and bindings;
- complete durable design/asset documentation;
- run content, asset, freshness, accessibility, responsive, light/dark,
  download, availability, security-copy, privacy-scan, and link verification;
- confirm there are no invalid icons, private task data, raw capture
  artifacts, unsupported claims, or review-only UI.

**HUMAN JUDGMENT:** Approve the complete local homepage as publishable apart
from the real waitlist form.

After H8, mark the applicable `019` requirements and checklist complete and
hand the reviewed local site to `020`. Do not publish yet.

### Phase C — Integrate the real waitlist and publish

#### H9 — Waitlist policy and AWS deployment readiness

Agent work:

- inspect SES identity/sandbox and the target AWS environment read-only;
- prepare the dedicated API Gateway/Lambda/DynamoDB/SES/SNS implementation,
  tests, deployment package, privacy changes, and operations documentation.

**HUMAN JUDGMENT:** Approve sender identity, consent/confirmation copy, and
retention/deletion policy.

**HUMAN — MANDATORY:** Complete any required SES identity, DNS, or production
access action that cannot be safely automated.

**HUMAN — MANDATORY:** Explicitly approve AWS deployment.

#### H10 — Integrated website review

Agent work:

- deploy and verify the waitlist service through its public HTTPS path;
- integrate the real accessible form into the approved mobile step;
- verify signup, confirmation, storage, withdrawal, suppression, privacy,
  responsive behavior, and absence of secret or personal-data exposure;
- build and preview the complete integrated website.

**HUMAN JUDGMENT:** Approve the form behavior, consent presentation,
confirmation message, privacy wording, and complete integrated page.

#### H11 — Production publication

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
- **Decision:** execution follows explicit H1–H11 gates, not filename ordering
  alone.
- **Decision:** H1–H8 produce the approved local homepage; H9–H11 add the real
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
- [x] **AGENT:** Commit Candidate A and create the durable brief/copy/visual/
      image review package.
- [x] **HUMAN JUDGMENT — H1:** Approve the brief and terminology.
- [ ] **HUMAN JUDGMENT:** Approve
      `tasks/20261024-production-staging-website-channels.md`.
- [ ] **AGENT:** Build the literal `d3fe28a6` plus current Getting Started
      production candidate and the separate staging variant.
- [ ] **HUMAN JUDGMENT:** Approve local production/staging content and
      separation.
- [ ] **AGENT:** Prepare staging AWS/GitHub/workflow changes.
- [ ] **HUMAN — MANDATORY:** Approve and execute the first dual deployment.
- [ ] **HUMAN JUDGMENT:** Accept both public channels and release paused work.
- [ ] **HUMAN JUDGMENT — H2:** Select or revise one complete copy direction.
- [ ] **HUMAN JUDGMENT — H3:** Approve the visual plan.
- [ ] **HUMAN JUDGMENT — H4:** Approve the image shortlist and treatments.
- [ ] **AGENT:** Implement and capture the H5 opening candidate.
- [ ] **HUMAN JUDGMENT — H5:** Approve the opening in context.
- [ ] **AGENT:** Complete the H6 first-user flow.
- [ ] **HUMAN JUDGMENT — H6:** Approve overview, Getting Started, availability,
      and connection language.
- [ ] **AGENT:** Apply the H7 first-release content cut.
- [ ] **HUMAN JUDGMENT — H7:** Approve retained/deferred advanced content.
- [ ] **AGENT:** Complete H8 homepage verification and source promotion.
- [ ] **HUMAN JUDGMENT — H8:** Approve the local homepage for waitlist
      integration.
- [ ] **AGENT:** Prepare the waitlist service and deployment evidence.
- [ ] **HUMAN JUDGMENT — H9:** Approve policy decisions.
- [ ] **HUMAN — MANDATORY — H9:** Complete required account-owner actions and
      approve AWS deployment.
- [ ] **AGENT:** Deploy, verify, and integrate the waitlist.
- [ ] **HUMAN JUDGMENT — H10:** Approve the complete integrated website.
- [ ] **HUMAN — MANDATORY — H11:** Approve production publication.
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
- Homepage-ready boundary: H8 evidence proves the complete local page through
  production-like browser, accessibility, visual, download, security-copy,
  source-freshness, and private-data checks.
- Waitlist-ready boundary: H10 evidence crosses the real browser → public HTTPS
  endpoint → storage → SES confirmation → withdrawal path.
- Publication boundary: H11 includes explicit human approval, successful
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
- 2026-10-16: H3A was approved and the multi-frame walkthrough is now
  implemented and verified. Desktop uses six named chapters and thirteen
  arrow-navigated frames; mobile and no-JavaScript presentation expose the
  complete sequence through vertical reading. Subtask `019` is paused at H3B
  for in-context human visual review. H4 remains blocked, and no source
  promotion or publication occurred.
- 2026-10-16: H3B accepted the responsive layout and rejected the current
  visual/copy selection. Subtask `019` now owns a focused H3C correction with
  direct interface titles, approximately nine frames, an unsliced Composer,
  contextual Desktop Message/Session actions, larger Session settings, no
  Desktop focused-connection frame, and Message metadata built through the
  maintained `provider-usage-cost` `focusCalloutPipeline`. H4 remains blocked.
- 2026-10-23: Candidate A's static four-story replacement was committed as
  `96e08249`, then rejected as the implementation baseline after contextual
  review of terminology, image magnification, profile readability, figure
  separation, text measures, and device framing. The active sequence was
  revised to H1–H11. Subtask `019` is now paused at the new H1–H4 brief, copy,
  visual-plan, and image-shortlist decisions; all implementation, source
  promotion, waitlist, AWS, and publication steps remain blocked.
- 2026-10-24: Inserted
  `tasks/20261024-production-staging-website-channels.md` as the
  highest-priority phase. Production restores exact baseline `d3fe28a6` plus
  the current Getting Started section with empty visual placeholders removed.
  The current in-progress homepage becomes staging at
  `staging.crystallattice.dev`. Task `019` is paused before H2, website `030`
  is paused before canonical public tables, and waitlist task `020` retains
  its approved plan but pauses all execution.
- 2026-11-04: Production and staging are public and verified with separate
  source roots, artifacts, buckets, distributions, GitHub environments, and
  deployment jobs. Task `019` is unblocked at H2, website `030` is unblocked
  at the Canonical Tables checkpoint, and task `020` has cleared only the
  channel dependency while retaining its own gates.