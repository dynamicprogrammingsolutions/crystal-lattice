# Prepare A Publishable First-User Homepage

Replace the unfinished homepage prototype with an owner-reviewed product
explanation, consistent real-product visuals, a truthful six-step first-use
path, and a deliberate lower-page release cut.

Parent Task:
`tasks/20260930-homepage-getting-started-and-waitlist/000-main.md`

Depends On:
`tasks/20260930-homepage-getting-started-and-waitlist/015-homepage-content-assets-layout.md`

Paused By:
`tasks/20261024-production-staging-website-channels.md`

## Requirements checklist

- [ ] The homepage role, primary visitor, visitor questions, terminology,
      concept ownership, claim boundaries, and information order are approved
      before the next implementation candidate is built.
- [x] Primary homepage copy uses **application for configurable AI coding
      agents** as the category direction and does not define Crystal Lattice
      as a generic **AI agent platform**. It distinguishes the configured
      agent, its harness, provider route, plugins, session, and application.
- [ ] The hero identifies a recognizable product category, one primary
      benefit, that Crystal Lattice runs on the visitor's computer, and a
      truthful first action.
- [ ] Before Getting Started, one coherent product-at-a-glance figure
      establishes the complete application through a real Desktop state that
      includes sessions, selected conversation, composer, and relevant setup
      identity.
- [ ] The opening explanation focuses on three material differences:
      configured agents can select materially different harnesses;
      provider-native history/behavior can remain distinct from normalized
      display history; and plugins can affect application/session behavior in
      addition to model-facing tools.
- [ ] Desktop and mobile are explained as clients for the same Crystal Lattice
      sessions on the computer. A matched cross-device figure uses separately
      framed genuine captures rather than one blended product canvas.
- [ ] Every retained visual has one visitor-facing purpose, one primary claim,
      a real sanitized source, a direct interface-oriented title, useful alt
      text, and a concise caption. Redundant slots are removed rather than
      filled.
- [ ] Screenshot title, bounded figure surface, image, and caption form one
      clear visual unit with separation from surrounding prose.
- [ ] Related screenshots have consistent apparent UI magnification at actual
      rendered size. Important proof-bearing labels are readable inline.
- [ ] A dedicated compact real Agent-picker capture removes unused window
      space before capture and shows configured-agent identity plus the
      materially different harness/tool behavior being explained without
      repainting or fabricating product text.
- [ ] Desktop and mobile receive restrained presentation frames where client
      identity or continuity matters. Focus crops and callouts remain
      unframed when another frame would reduce readability or add noise.
- [ ] The normal homepage renders no planned-visual panel, missing-proof
      placeholder, review-status label, disabled fake form, intentionally
      blank image surface, or knowingly unverified example.
- [ ] The approved product values remain represented through selected copy,
      proof, or focused routes without requiring six equal feature cards or a
      fixed number of homepage visuals.
- [ ] Getting Started retains exactly six ordered steps: install CLI, start a
      workspace, download Desktop, connect Desktop, get the mobile app or join
      its release waitlist, and connect from mobile.
- [ ] The default Desktop startup path binds locally. Same-network mobile
      access and bridge access away from the local network are introduced
      separately with current security and availability qualifications.
- [ ] The Desktop connection step includes a compact genuine connection editor
      and recognizable connected result using port `9000`.
- [ ] The mobile connection step presents automatic local discovery first,
      manual address and port as fallback, and bridge access away from the
      local network third.
- [ ] Current downloads, public/tester/invite availability, compatibility
      limitations, bridge state, security implications, and source
      availability derive from maintained product or release evidence.
- [ ] Material after Getting Started has a distinct visitor and purpose.
      Detailed bridge deployment, compatibility reference, plugin authoring,
      SDK examples, and repeated proof move to focused documentation or routes
      when they interrupt the first-user path.
- [ ] The complete candidate is responsive, keyboard accessible, semantically
      ordered, reduced-motion aware, and understandable without hidden primary
      content, autoplay, carousel operation, or required swipe interaction.
- [ ] The complete page is visually reviewed in light and dark themes at
      desktop, tablet, and phone widths. Text measures, figure containment,
      image presence, UI magnification, framing, and page length are all
      reviewed in context.
- [ ] Maintained landing-package documentation records the selected brief,
      exact public copy, visual plan, image-purpose map, capture ownership,
      responsive behavior, lower-page release cut, and reasons for material
      decisions.
- [ ] No source push, visual-source promotion, waitlist deployment, AWS
      mutation, or production website publication occurs before its explicit
      human checkpoint. Subtask `020` continues to own the real waitlist and
      final integrated publication.

## Scope and ownership

This task owns the final local homepage apart from the functional waitlist:

- first-user homepage brief and terminology;
- hero and pre-Getting Started public copy;
- product overview information architecture and visual system;
- remaining homepage proof assets and screenshot consistency;
- six-step Getting Started presentation;
- first-release lower-page content cut;
- local publish-readiness verification and documentation.

Subtask `020` owns the real waitlist service and form, privacy integration,
and its later integrated production verification.
`tasks/20261024-production-staging-website-channels.md` now owns the
production/staging source split, restoration of the interim production
homepage, staging infrastructure, and dual deployment workflow.

Current public behavior and product interfaces remain authoritative. If an
accepted screenshot would require a genuine product behavior change, stop and
obtain approval for that product change rather than fabricating the state.

## Current findings

- Candidate A was committed as `96e08249` after responsive and native-capture
  verification. It improved the former thirteen-frame walkthrough but is not
  the selected direction.
- Human review found that Candidate A:
  - used **AI agent** as an unapproved and misleading category;
  - gave Composer and Workspace materially different apparent magnification;
  - allowed the Workspace figure to appear absent or visually subordinate;
  - made the profile picker unreadable despite large unused window space;
  - lacked sufficient separation between prose and figures;
  - used inconsistent text widths;
  - presented Desktop/mobile without suitable frames;
  - treated four stories as a layout answer before establishing a copy and
    visual system.
- Review of the Dynamic Programming Solutions website and Crystal Lattice case
  study identified a better working method:
  - page role and visitor questions before copy;
  - concept ownership and terminology boundaries;
  - complete visitor-facing copy separate from presentation notes;
  - desktop/mobile visual plan before implementation;
  - claim-to-image plan and candidate contact sheets;
  - focused thumbnails selected for inline readability;
  - separate copy, visual, and screenshot approvals;
  - implementation only after those approvals.
- The current product-content specification's fixed six-visual requirement was
  inconsistent with the approved direction. It now requires every retained
  visual to have a distinct purpose and permits redundant slots to be removed.

## Durable review package

The reviewable target is maintained under:

`landing_page/docs/development/homepage-first-user-release/`

It contains:

- `README.md`;
- `brief.md`;
- `copy-draft.md`;
- `visual-plan.md`;
- `image-plan.md`.

Candidate A remains available through its explicit preview and commit for
comparison. Current normal homepage content remains unchanged until a new
direction passes the required approvals.

## Open questions

### Brief and terminology

- Resolved: use **application for configurable AI coding agents** as category
  orientation.
- Resolved: use **configured agent**, not **profile**, for the named `agents`
  configuration used by a session.
- Resolved: use **harness** for materially different tool implementations,
  provider integration, context behavior, and controls around the configured
  agent.
- Resolved: the primary differentiators are harness composition,
  provider-native fidelity, and plugins that can affect the application.
- Resolved: included agents may be introduced as Codex-oriented,
  Claude-compatible, Gemini-oriented, and other evidence-backed harnesses,
  with an explicit non-upstream identity statement and a route to the focused
  compatibility catalogue owned by website task `030`.

### Copy

- Select opening direction A, B, or C, or request a complete revised
  alternative.
- Approve or revise the shared overview headings and captions.
- Rewrite the prior A/B/C alternatives around the approved harness,
  provider-native, and application-plugin differentiation.

### Visual plan

- Approve one large Desktop product-at-a-glance figure followed by three
  consistent proof rows and one cross-device figure.
- Approve the proposed text measures and non-alternating proof-row structure.
- Approve restrained macOS and phone frames for product overview/continuity.
- Decide whether inline enlargement is useful for secondary details or
  unnecessary on the homepage.

### Image plan

- Confirm that the large Desktop figure replaces separate Composer and
  Workspace stories.
- Confirm the configured-agent/harness comparison proof.
- Confirm whether provider-native fidelity uses the maintained relationship
  diagram, focused real UI, or both.
- Confirm the plugin-configuration-to-application-effect proof.
- Confirm the compact Agent-picker capture requirements.

### Later checkpoints

- Approve exact Getting Started copy and connection images.
- Decide whether the Vibe/non-coding story remains after Getting Started,
  moves to a focused route, or is removed from the first release.
- Decide the final compatibility, provider, plugin, bridge, SDK, and
  contribution routes retained below Getting Started.

## Human decisions and actions required

- **HUMAN JUDGMENT — BRIEF AND TERMINOLOGY:** Approve the page role, primary
  visitor, questions, concept ownership, terminology, and information order.
- **HUMAN JUDGMENT — COMPLETE COPY:** Select or revise one complete opening
  direction and approve the shared overview copy.
- **HUMAN JUDGMENT — VISUAL PLAN:** Approve the desktop/mobile composition,
  section rhythm, text measures, figure system, framing, and responsive rules.
- **HUMAN JUDGMENT — IMAGE SHORTLIST:** Approve every opening image's claim,
  source/capture direction, inline treatment, and disposition.
- **HUMAN JUDGMENT — FIRST-USER FLOW:** Approve the implemented overview,
  six-step Getting Started path, Mobile access grouping, availability wording,
  and responsive reading length.
- **HUMAN JUDGMENT — RELEASE CUT:** Approve every retained, moved, deferred,
  and rejected lower-page section.
- **HUMAN JUDGMENT — FINAL LOCAL SITE:** Approve the complete local homepage,
  proof assets, copy, responsive behavior, and release-state presentation
  before handoff to subtask `020`.
- **HUMAN — MANDATORY:** Final AWS deployment and website publication remain
  governed by subtask `020`.

## Execution plan

Status: Approved

Treat `96e08249` as a committed comparison boundary. Do not continue polishing
Candidate A's component structure while the underlying copy and visual system
are under review.

First establish the durable homepage target:

1. define the page role, primary visitor, visitor questions, concept
   ownership, terminology, claim boundaries, and information order;
2. prepare several complete opening-copy alternatives rather than isolated
   headline fragments;
3. map the proposed copy to explicit desktop and mobile compositions;
4. map every retained visual to one claim, real source, capture geometry,
   rendered-size target, title, caption, and disposition;
5. reconcile the package-owned product-content specification and parent task
   so they no longer force a rejected six-visual layout.

Stop for the brief, copy, visual-plan, and image-shortlist decisions. Although
the review documents may be prepared together, implementation begins only
after each applicable decision is explicit.

After approval:

1. create the new opt-in candidate using the selected copy and visual plan;
2. recapture the complete Desktop overview and compact Agent picker;
3. produce the approved configured-agent/harness proof;
4. select or produce the provider-native fidelity and application-plugin
   proofs;
5. render actual-page candidates in light/dark themes and at all review widths;
6. stop for contextual approval before source promotion.

Then integrate accepted sources through the visual-asset catalog and normal
homepage content. Revise Getting Started, complete its connection images, and
stop for the First-User Flow checkpoint.

After that checkpoint, remove or route lower-page material according to its
audience and evidence. Finish with local production builds, content scans,
catalog/freshness checks, responsive browser tests, direct image inspection,
accessibility checks, release/download verification, and privacy/sanitization
review.

Promote only final human-approved visual sources. Hand the accepted local site
to subtask `020` without pushing, deploying, or publishing.

### Implementation decisions and open questions

- Decision: revise this task in place; Git retains rejected Candidate A and
  prior walkthrough history.
- Decision: copy and visual direction are approved before another implementation
  candidate.
- Decision: primary copy uses **application for configurable AI coding
  agents** as category orientation and avoids the broader **AI agent
  platform** definition.
- Decision: the homepage uses no fixed number of visual stories.
- Decision: one large Desktop image establishes the complete application.
- Decision: configured-agent harness composition, provider-native fidelity,
  and application-level plugin effects are the material differentiators.
- Decision: model selection, ordinary instructions, generic permissions,
  session persistence, history, usage/cost display, Desktop/mobile access, and
  source availability are orientation or supporting facts rather than primary
  value claims.
- Decision: proof rows use one consistent layout rather than automatic
  left/right alternation.
- Decision: real window geometry is corrected before capture when unused space
  or UI scale makes a screenshot unreadable.
- Decision: Desktop/mobile continuity uses separately framed clients.
- Decision: current normal homepage content remains unchanged during planning.
- Open human judgment: exact ordinary-language category.
- Open human judgment: selected complete opening-copy direction.
- Open human judgment: visual-plan details and inline enlargement.
- Open human judgment: final focused proof set.
- Open human judgment: Getting Started copy and lower-page release cut.

### Documentation

- Maintain the first-user review package under
  `landing_page/docs/development/homepage-first-user-release/`.
- Update the package development index to route to the review package.
- Update the product-content specification and requirements when approved
  communication outcomes change.
- Update `content-system.md`, `visual-assets.md`, and the package README only
  after the selected implementation changes their current workflows.
- Reconcile the large historical homepage decision record after final
  selection without turning it into a second editable copy of the new brief.
- Keep target-only public copy visibly marked not implemented until normal
  homepage integration and verification.

### Task checklist

- [x] Commit Candidate A and its capture/preview work before changing
      direction (`96e08249`).
- [x] Review the related Dynamic Programming Solutions homepage and real
      Crystal Lattice case-study workflow, copy, presentation notes, image
      planning, and selected screenshots.
- [x] Create the durable homepage brief, copy, visual, and image review
      package.
- [x] Reconcile the fixed six-visual requirement in the parent task and
      product-content specification.
- [x] Complete the Brief and Terminology human checkpoint.
- [ ] Complete the Complete Copy human checkpoint.
- [ ] Complete the Visual Plan human checkpoint.
- [ ] Complete the Image Shortlist human checkpoint.
- [ ] Implement the selected opt-in homepage candidate.
- [ ] Capture/select the approved overview, configured-agent/harness,
      provider-native, and application-plugin proof without promotion.
- [ ] Complete the contextual opening-page human checkpoint.
- [ ] Integrate approved normal content, responsive assets, and catalog
      bindings.
- [ ] Revise and verify the six-step Getting Started and Mobile access group.
- [ ] Complete the First-User Flow human checkpoint.
- [ ] Apply the lower-page release cut and update advanced-user routes.
- [ ] Complete the Release Cut human checkpoint.
- [ ] Run final content, visual, accessibility, release, link, privacy, and
      responsive verification.
- [ ] Update maintained implementation documentation.
- [ ] Complete the Final Local Site human checkpoint.
- [ ] Promote approved sources and hand the local site to subtask `020`
      without pushing or publishing.

### Requirement verification

- Brief requirement: human review approves the page role, visitor questions,
  primary audience, terminology, concept ownership, claim boundaries, and
  information order recorded in the durable brief.
- Copy requirement: human review selects one complete opening direction and
  approves every public heading, paragraph, figure title, caption, action, and
  metadata item in scope before implementation.
- Product-understanding requirement: moderated review begins at the hero with
  no prior explanation. Before Getting Started, the reviewer can identify what
  Crystal Lattice is, where it runs, what a session/workspace contains, what
  can be seen or configured, and how Desktop/mobile relate.
- Visual-plan requirement: human review approves both desktop and mobile
  compositions, stable text measures, figure containment, frame use,
  magnification targets, and responsive behavior before implementation.
- Image-purpose requirement: the maintained image plan assigns one claim,
  source, capture geometry, inline treatment, caption, and disposition to
  every retained image.
- Genuine-proof requirement: catalog/source inspection maps every
  proof-bearing control and value to a reviewed real-product source. Repainted
  values, duplicate mock menus, and invented UI are insufficient.
- Placeholder requirement: a normal production build and source scan find no
  placeholder panels, review labels, fake form, internal implementation copy,
  intentionally blank image canvas, or unverified API warning.
- Screenshot-consistency requirement: direct inspection at rendered page size
  confirms comparable apparent UI scale, readable primary labels, consistent
  figure treatment, sanitized content, and intentional frames.
- Getting Started requirement: built HTML and browser tests verify all six
  ordered steps, maintained installation/download data, local-default Desktop
  startup, port `9000` connection proof, grouped Mobile access, and discovery
  → address/port → bridge explanation.
- Truthfulness requirement: content inspection traces release, platform,
  compatibility, bridge, source, and security claims to maintained
  product/release sources.
- Release-cut requirement: human review records a destination or rejection
  reason for every removed advanced section and confirms that every retained
  section has a distinct audience and verified purpose.
- Accessibility/responsive requirement: keyboard, semantics, visible focus,
  reduced motion, theme switching, no-JavaScript reading, horizontal
  containment, and viewport checks pass at 1440, 1024, 768, 390, and 320
  pixels.
- Handoff requirement: Git and deployment inspection confirm that only
  approved local sources/bindings are ready for subtask `020`; no push, source
  promotion, AWS mutation, or publication occurred.

### Additional implementation verification

- Run focused landing content tests, the production Astro build,
  visual-asset tests/checks, and affected Playwright suites.
- Open full-page and focused screenshots in light/dark themes at every review
  width.
- Verify active release/download links and confirm unavailable platforms
  remain non-interactive and accurately labeled.
- Scan public files and browser bundles for private identifiers, credentials,
  personal session data, operator-specific addresses, internal task language,
  and stale preview paths.
- Use pixel/content checks or another reliable browser assertion to detect a
  missing, transparent, or visually blank product-at-a-glance image.

## Implementation Notes

- 2026-10-23: Candidate A was committed as `96e08249`
  (`Prepare homepage overview candidate`) before the approved direction
  changed.
- 2026-10-23: Human review accepted the structural improvement but rejected
  Candidate A as the implementation baseline because of terminology,
  inconsistent magnification, missing/subordinate Workspace presentation,
  unreadable profile proof, weak figure separation, inconsistent text widths,
  and unframed client imagery.
- 2026-10-23: Reviewed
  `tasks/20260818-website-and-offer-page-rollout/061-real-case-study-copy-visuals-and-private-implementation.md`
  and its Crystal Lattice case-study package in the Dynamic Programming
  Solutions website. Adopted its separation of discovery/brief, public copy,
  presentation notes, image-generation plan, candidate batches, approval
  gates, focused thumbnails, and responsive in-context review.
- 2026-10-23: Created the durable first-user homepage package with a page
  brief, three complete opening-copy alternatives, a desktop/mobile visual
  plan, and a seven-image opening/Getting Started shortlist.
- 2026-10-23: Corrected the parent task and product-content specification so
  the final homepage no longer has to preserve six visual stories. Added a
  terminology requirement preventing the broader **AI agent platform**
  definition from replacing an accurate coding-agent category.
- 2026-10-23: Current public YAML and Candidate A code remain unchanged.
  Execution is paused for the Brief and Terminology, Complete Copy, Visual
  Plan, and Image Shortlist human decisions before another implementation
  candidate is built.
- 2026-10-24: The user approved **application for configurable AI coding
  agents** as the category direction, **configured agent** instead of
  **profile**, and the harness/provider-native/application-plugin
  differentiator hierarchy. The brief records the accepted hybrid wording for
  Codex-oriented, Claude-compatible, Gemini-oriented, and other
  evidence-backed harnesses. H1 is complete; exact copy, visual plan, and
  image shortlist remain open.
- 2026-10-24: This task is paused before H2 behind
  `tasks/20261024-production-staging-website-channels.md`. Resume only after
  the production/staging source and local-build split passes its human
  checkpoint and the staging deployment path is available or explicitly
  deferred. Resume at H2 Complete Opening Copy; H1 decisions and the durable
  review package remain authoritative.
