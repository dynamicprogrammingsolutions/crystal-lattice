# Redesign The Homepage And Add A Mobile Release Waitlist

Restructure the Crystal Lattice homepage around a concise hero, six
proof-backed product highlights, and a six-step getting-started journey. After
the redesigned website is complete and reviewed locally, add a small AWS-backed
email waitlist with SES confirmation and integrate its real form into the
mobile-download step.

## Requirements checklist

- [ ] The homepage primary sequence is: concise hero, six visual product
      highlights, then a six-step getting-started section.
- [ ] The six highlights include the five approved themes—one workspace for
      model-family-oriented agents, replaceable plugin surfaces, transparent
      and open-source operation, work from anywhere, and adaptability beyond
      development—plus durable session workspaces.
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

- `tasks/20260930-homepage-getting-started-and-waitlist/010-homepage-structure-prototype.md`
  owns only the structural prototype: page order, component shells,
  placeholders, draft-content hooks, a responsive baseline, and a local
  review build.
- `tasks/20260930-homepage-getting-started-and-waitlist/015-homepage-content-assets-layout.md`
  owns approved public copy, the logo-led download layout, exact planned-visual
  descriptions, and the durable design-decision record.
- `tasks/20260930-homepage-getting-started-and-waitlist/018-homepage-visuals-product-improvements.md`
  owns the real product improvements, screenshot-only presentation decisions,
  reviewed fixtures, and final proof asset production.
- `tasks/20260930-homepage-getting-started-and-waitlist/020-aws-email-waitlist.md`
  owns the deployed waitlist service and then adds the actual working form to
  the reviewed website.
- Production publication is completed through subtask `020` after the service
  and final integrated website have both passed human review.

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
- Local unpushed landing-page changes already add the verified macOS header
  download icon and its maintained release metadata. The redesign must retain
  or deliberately supersede those changes without losing the direct download
  contract.
- A push touching `landing_page/**` automatically invokes the protected
  production static-site workflow, so local review must precede the publishing
  push.

## Subtasks

- [x] `tasks/20260930-homepage-getting-started-and-waitlist/010-homepage-structure-prototype.md`
- [x] `tasks/20260930-homepage-getting-started-and-waitlist/015-homepage-content-assets-layout.md`
- [ ] `tasks/20260930-homepage-getting-started-and-waitlist/018-homepage-visuals-product-improvements.md`
- [ ] `tasks/20260930-homepage-getting-started-and-waitlist/020-aws-email-waitlist.md`

## Execution plan

Status: Draft

The work is deliberately ordered structure first, content/assets/layout
second, and service integration last.

Subtask `010` establishes only the page information architecture, component
contracts, placeholder states, responsive baseline, and integration boundary.
It renders draft copy solely for contextual review and does not approve that
copy, new assets, highlight ordering, or the overall visual layout.

Subtask `015` starts from that working structure and applies the selected copy,
platform-logo download layout, and detailed placeholder descriptions. It also
creates the durable decision record while preserving the selected alternatives.

Subtask `018` then makes any approved backend/SDK/Desktop improvements needed
for truthful proof, resolves whether screenshot-specific ordering/hiding uses
real product controls or capture-only plugins, and produces reviewed visual
assets.

Subtask `020` then deploys the minimal AWS service, verifies confirmation and
withdrawal behavior, and adds the actual form to the reviewed mobile-download
step. This keeps the public form contract driven by a real backend rather than
a placeholder endpoint. The final integrated site is reviewed again before
one protected production publication.

The three-subtask structure also keeps personal-data handling separate from
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

- Decision: implement the website redesign before the waitlist service.
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
- Open human decisions owned by subtask `020`: public sender address,
  consent wording, and retention/deletion period.

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
- [ ] **AGENT:** Complete visual/product-improvement subtask `018` after its
      material product and capture-only decisions are approved.
- [ ] **HUMAN JUDGMENT:** Approve the finalized homepage copy, proof assets,
      ordering, and visual layout.
- [ ] **AGENT:** Complete and verify the AWS service plus integrated form in
      subtask `020`.
- [ ] **HUMAN — MANDATORY:** Complete any SES identity or production-access
      action that requires the AWS account owner.
- [ ] **HUMAN JUDGMENT:** Approve consent copy, sender identity, retention,
      and final integrated website presentation.
- [ ] **HUMAN — MANDATORY:** Approve AWS and production website publication.
- [ ] **AGENT:** Deploy through the approved paths and verify the production
      page, signup, confirmation, withdrawal, and downloads.
- [ ] **AGENT:** Record completion evidence and remaining follow-up without
      rewriting the completed desktop-release history.

### Requirement verification

- Homepage structure and highlight requirements: production-built HTML plus
  content-contract and responsive browser tests must show the exact ordered
  hero, six highlights, and getting-started section with all approved themes.
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