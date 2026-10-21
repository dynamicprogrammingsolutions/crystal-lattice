# Redesign The Homepage And Add A Mobile Release Waitlist

Restructure the Crystal Lattice homepage around a concise hero, a
screenshot-led UI walkthrough, the approved proof-backed product values, and
a six-step getting-started journey. After the redesigned website is complete
and reviewed locally, add a small AWS-backed email waitlist with SES
confirmation and integrate its real form into the mobile-download step.

## Requirements checklist

- [ ] The homepage primary sequence is: concise hero, an introductory
      screenshot-led UI walkthrough, the remaining visual product highlights,
      then a six-step getting-started section.
- [ ] The walkthrough and highlights together preserve the six approved
      themes—one workspace for model-family-oriented agents, replaceable
      plugin surfaces, transparent and open-source operation, work from
      anywhere, adaptability beyond development, and durable session
      workspaces—without forcing every theme to remain a separate card.
- [ ] Public copy clearly distinguishes Crystal Lattice configured-agent
      profiles and model-family-oriented defaults from official upstream
      applications such as Claude Code, Codex, Gemini, Kimi, or other products.
- [ ] Getting Started presents, in order: CLI installation, workspace startup,
      Desktop download, Desktop connection, mobile download/waitlist, and
      mobile connection.
- [ ] Current platform states remain truthful: the CLI is available for its
      maintained platforms, Desktop is downloadable for macOS while Windows
      and Linux Desktop are marked coming soon, and App Store/Google Play
      distribution is marked coming soon without hiding current source or
      internal-test availability.
- [ ] A simple public form collects only the email and necessary consent
      metadata, stores it safely in AWS, sends a confirmation through Amazon
      SES, supports withdrawal, and does not expose email data or AWS
      credentials to the browser or repository.
- [ ] The redesigned page, waitlist form, confirmation flow, and public
      downloads are responsive, keyboard accessible, semantically structured,
      privacy-conscious, and verified through their real production paths.
- [ ] Before the task closes, a durable package-owned design record preserves
      the intermediary homepage copy and visual alternatives, the theory and
      tradeoffs behind them, the final selections, and the reasons viable
      alternatives were not selected, so later revisions do not require
      reconstructing the design discussion.
- [ ] Production website and AWS publication occur only after explicit human
      review and approval.
- [ ] The existing desktop-release task remains the evidence source for the
      macOS artifact; this task does not rewrite its completed release history.

## Workstreams and ownership

- `tasks/20260930-homepage-getting-started-and-waitlist/001-publication-sequence.md`
  is the coordination umbrella. It tracks the approved order, H1–H9 human
  gates, current completion, and handoff across the implementation subtasks
  without owning their product requirements.
- `tasks/20260930-homepage-getting-started-and-waitlist/010-homepage-structure-prototype.md`
  owns only the structural prototype: page order, component shells,
  placeholders, draft-content hooks, a responsive baseline, and a local
  review build.
- `tasks/20260930-homepage-getting-started-and-waitlist/015-homepage-content-assets-layout.md`
  owns approved public copy, the logo-led download layout, exact planned-visual
  descriptions, and the durable design-decision record.
- `tasks/20260930-homepage-getting-started-and-waitlist/018-homepage-visuals-product-improvements.md`
  owns the implemented product improvements, capture infrastructure, reviewed
  fixtures, and accepted Plugin/Transparency/Vibe evidence produced before
  the publishable-page restructuring.
- `tasks/20260930-homepage-getting-started-and-waitlist/019-publishable-homepage-ui-walkthrough.md`
  owns the UI-led product introduction, revised publishable information
  architecture, remaining proof assets, Getting Started/mobile presentation,
  release-content cut, and final local website acceptance.
- `tasks/20260930-homepage-getting-started-and-waitlist/020-aws-email-waitlist.md`
  owns the deployed waitlist service and then adds the actual working form to
  the reviewed website.
- Production publication is completed through subtask `020` after the service
  and final integrated website have both passed human review.
- `tasks/20260825-crystal-lattice-product-positioning-and-website/030-release-safe-early-user-website.md`
  owns the complete website's bounded positioning review, compatibility
  presentation, integrated content acceptance and live website checks.
  Its accepted candidate is consumed by `020`'s publishing step; both record
  evidence from the same artifact and publishing push.

## Approved shared website checkpoint — October 7, 2026

The group 1 outcome includes the published complete user website with all
six reviewed visual stories, three public compatibility views and rethought
owner-approved launch positioning. The existing product evidence supports
that bounded review; broad market research remains later.

Service/form work in 020 stays independent of final copy/proof readiness.
Before the single integrated publishing push, website 030 supplies its accepted
content candidate and 020 supplies its verified service/form and approved
privacy policy. After the push, 030 verifies live pages/assets/tables and 020
verifies the production signup/receipt/withdrawal flow. These are stage
checkpoints, not mutual whole-task completion dependencies.

Website 030's published-site acceptance gates open-source visibility in
`tasks/20260804-open-source-public-release/070-github-visibility-and-security-settings.md`.
Its anonymous-user validation follows in
`tasks/20260804-open-source-public-release/080-post-publication-validation-and-early-adopter-intake.md`.
No actual AWS/site/source publication is authorized by this tracking approval.

## Supporting facts

- The current hero embeds the full CLI installation chooser. The redesign
  moves that maintained chooser to Getting Started step 1 and leaves the hero
  focused on positioning and one primary action.
- Crystal Lattice Desktop `0.9.0 (4)` is publicly available for macOS 14+ as a
  universal `arm64`/`x86_64` DMG. Windows and Linux Desktop packages do not
  currently exist.
- The CLI already has maintained macOS/Linux and native Windows installation
  paths.
- The mobile app exists, has successful internal TestFlight history, and can
  be run from source, but public App Store and Google Play distribution are
  not currently available.
- The landing package has no current waitlist API, database, mailing-list
  provider, consent flow, or email-subscription storage.
- The landing package already maintains reviewed light/dark product captures
  and a visual-asset lifecycle. Several approved images can be reused, but the
  revised themes require new proof for the configured-agent, cross-device, and
  non-development-workflow stories.
- The production homepage has the verified macOS header download icon and
  maintained release metadata, confirmed on October 7, 2026. The redesign
  retains that direct-download contract; technical publication does not
  establish unrecorded human review.
- A push touching `landing_page/**` automatically invokes the protected
  production static-site workflow, so local review must precede the publishing
  push.
- On October 5, 2026, the user authorized planning subtask `020` alongside
  ongoing `015`/`018` work and confirmed that nothing remaining in those tasks
  blocks it. Service and form implementation may proceed independently after
  `020` plan approval. Final publication still reviews the integrated website.
- On October 6, 2026, the user selected reuse of
  `support@dynamicprogrammingsolutions.com` for SES receipts in `us-west-2`.
  SES production sending is enabled in the inspected region. Subtask `020`
  owns sender-authentication preflight and a waitlist-specific configuration
  set without changing shared sending defaults. Public task text contains
  only non-sensitive configuration and authenticated discovery instructions.

## Subtasks

- [ ] `tasks/20260930-homepage-getting-started-and-waitlist/001-publication-sequence.md`
- [x] `tasks/20260930-homepage-getting-started-and-waitlist/010-homepage-structure-prototype.md`
- [ ] `tasks/20260930-homepage-getting-started-and-waitlist/015-homepage-content-assets-layout.md`
- [ ] `tasks/20260930-homepage-getting-started-and-waitlist/018-homepage-visuals-product-improvements.md`
- [ ] `tasks/20260930-homepage-getting-started-and-waitlist/019-publishable-homepage-ui-walkthrough.md`
- [ ] `tasks/20260930-homepage-getting-started-and-waitlist/020-aws-email-waitlist.md`

## Execution plan

Status: Draft

Tracking reconciliation on October 7: 010 is done; 015's original copy
delivery is complete but its remaining Getting Started requirement is in
review; 018 is in progress; 020 remains pending with a Draft plan. The original
015 Completion Notes remain intact and its follow-up is recorded separately.

The structure and integration slot already exist. Under the October 5, 2026
instruction, service/form work in `020` can proceed alongside remaining
content/visual work in `015`/`018`; their completion is not a prerequisite for
that implementation. Final integrated-site publication remains gated by human
review.

Subtask `010` establishes only the page information architecture, component
contracts, placeholder states, responsive baseline, and integration boundary.
It renders draft copy solely for contextual review and does not approve that
copy, new assets, highlight ordering, or the overall visual layout.

Subtask `015` starts from that working structure and applies the selected copy,
platform-logo download layout, and detailed placeholder descriptions. It also
creates the durable decision record while preserving the selected alternatives.

Subtask `018` makes the approved backend/SDK/Desktop improvements needed for
truthful proof and records the accepted capture work completed before the
publishable restructuring.

Subtask `019` then uses those product/capture foundations to teach the product
through its real UI, finish the remaining proof, revise Getting Started, and
produce the reviewed local publish candidate.

Subtask `020` independently deploys the minimal AWS service, verifies
confirmation and withdrawal behavior, and adds the actual form to the mobile-download
step. This keeps the public form contract driven by a real backend rather than
a placeholder endpoint. The final integrated site is reviewed again before
one protected production publication. Include website 030's accepted launch
positioning, all six 018 visual stories and all three compatibility views in
that candidate. After the same push, run both 030's live website checks and
020's production form checks.

The staged subtask structure also keeps personal-data handling separate from
general website content. Website components must not gain direct AWS
credentials, administrative reads, or mailing-list export behavior. The
backend owns validation, idempotency, storage, confirmation, suppression, and
withdrawal. Operator access remains an authenticated AWS command-line
workflow, not a public administration page.

The decisive end-to-end boundary is:

```text
production homepage form
  -> public HTTPS waitlist endpoint
  -> validation and conditional write
  -> encrypted DynamoDB record
  -> SES confirmation
  -> confirmed public success state
```

The production verification must also exercise unsubscribe/withdrawal and
prove that no email value appears in public responses, browser bundles,
repository files, or application logs.

### Implementation decisions and open questions

- Decision: under the October 5 instruction, implement the waitlist service
  alongside remaining 015/018 work; review the final integrated site together.
- Decision: website 030 owns complete content acceptance; 020 retains the
  single publishing push. Use stage checkpoints rather than circular
  whole-task completion dependencies.
- Decision: make structural implementation independently approvable while
  copy, assets, ordering, and final layout remain Draft.
- Decision: the waitlist subtask adds the actual form; the website subtask
  does not publish a fake endpoint or collect data.
- Decision: merge open-source value into the transparency highlight instead
  of dedicating a separate highlight to open source.
- Decision: use durable session workspaces as the sixth highlight.
- Decision: inspectability comes from explicit framework/plugin boundaries and
  user-modifiable plugins; open source adds source-level transparency rather
  than causing runtime inspection.
- Decision: use a dedicated AWS serverless service rather than coupling
  marketing email data to the bridge, cloud-agent orchestrator, or desktop
  download infrastructure.
- Decision: keep the initial waitlist deliberately small—email, consent
  evidence, confirmation, withdrawal, bounce/complaint state, and operator
  export/delete only.
- Decision: do not add a public admin UI, bulk campaign sender, tracking
  pixels, custom email analytics, segmentation, names, company fields, or
  free-form profile data.
- Sender/SES region selected: `support@dynamicprogrammingsolutions.com`,
  `us-west-2`. Remaining human decisions owned by subtask `020`: waitlist
  data location, consent wording, and retention/deletion period.

### Documentation

- Update landing-package documentation for the new homepage section model,
  maintained proof bindings, waitlist build configuration, and local preview
  workflow.
- Create a durable homepage positioning and visual-decision record under the
  landing package's development documentation before closing the parent task.
  It must include the committed pre-revision prototype, intermediary variants,
  selection criteria, final decisions, and viable alternatives worth testing
  later.
- Update the privacy policy with the approved waitlist purpose, data fields,
  AWS/SES processing, retention, withdrawal, and contact route.
- Add package-local waitlist deployment and operations documentation under
  `deploy/aws-waitlist/`.
- Keep task phases, approval labels, AWS account details, secrets, tokens, raw
  email addresses, and internal deployment diagnostics out of public copy.

### Task checklist

- [x] **HUMAN JUDGMENT:** Select the sixth highlight: durable session
      workspaces.
- [x] **AGENT:** Complete and locally verify structural subtask `010`.
- [x] **HUMAN JUDGMENT:** Review the structure in context without treating
      draft copy, placeholders, ordering, or layout as approved.
- [ ] **AGENT:** Complete content/assets/layout subtask `015` after its
      decisions are approved.
- [ ] **AGENT:** Reconcile the completed visual/product evidence in subtask
      `018` and finish any explicitly retained implementation bookkeeping.
- [ ] **AGENT:** Complete publishable UI-walkthrough subtask `019` through its
      staged human-review checkpoints.
- [ ] **HUMAN JUDGMENT:** Approve the finalized homepage copy, proof assets,
      ordering, and visual layout.
- [ ] **AGENT:** Complete and verify the AWS service plus integrated form in
      subtask `020`.
- [ ] **AGENT + HUMAN if needed:** Complete effective SES sender verification
      and DKIM preflight; production access is already enabled and is rechecked.
- [ ] **HUMAN JUDGMENT:** Approve waitlist data location, consent copy,
      retention, and final integrated website presentation.
- [ ] **HUMAN — MANDATORY:** Approve AWS and production website publication.
- [ ] **AGENT:** Deploy through the approved paths and verify the production
      page, signup, confirmation, withdrawal, and downloads.
- [ ] **AGENT:** Record completion evidence and remaining follow-up without
      rewriting the completed desktop-release history.

### Requirement verification

- Homepage structure and product-value requirements: production-built HTML
  plus content-contract and responsive browser tests must show the exact
  ordered hero, UI walkthrough, remaining highlights, and Getting Started,
  with all six approved themes represented in their selected locations.
- Availability requirement: maintained content tests and live-link checks
  must prove current CLI/macOS links and non-interactive coming-soon states
  without implying unavailable Desktop or store releases exist.
- Waitlist requirement: one deployed public-path integration test must submit
  a unique test address, inspect the resulting DynamoDB record through
  authenticated AWS access, and verify the SES confirmation path without
  bypassing the public API.
- Privacy/security requirement: inspection must prove least-privilege IAM,
  encrypted storage, bounded CORS, request-size and rate controls, no email
  body logging, hashed opaque withdrawal tokens, and no public list/read API.
- Withdrawal requirement: a real confirmation email's unsubscribe path must
  change the stored state and prevent future active-list export.
- Accessibility requirement: desktop and mobile browser checks must cover
  semantic heading/ordered-step structure, form labels, errors, keyboard
  operation, focus, status announcements, and disabled coming-soon controls.
- Production publication requirement: the protected workflow must complete,
  and anonymous production checks must verify the new page, downloads, form,
  confirmation state, and absence of broken or placeholder actions.
- Durable decision-record requirement: documentation inspection must show the
  pre-revision prototype, intermediary alternatives, copy-orientation theory,
  visual/download research, final decisions and rationale, and
  rejected-but-viable options, with links from the completed task.

### Additional implementation verification

- Verify visual-asset bindings, light/dark source selection, alt text,
  dimensions, byte budgets, and reviewed-source provenance.
- Verify duplicate signup and resend behavior remains idempotent.
- Verify malformed, oversized, bot-honeypot, and throttled requests do not
  create records or trigger SES.
- Verify bounce and complaint events suppress affected records.
- Verify operator export excludes unsubscribed, bounced, and complained
  records and does not write unencrypted output into the repository.
- Verify no existing long-running local preview process is stopped merely to
  run browser tests; use an isolated configurable port.