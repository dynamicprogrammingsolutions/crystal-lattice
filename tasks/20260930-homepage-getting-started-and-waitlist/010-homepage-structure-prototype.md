# Build The Homepage Structural Prototype

Parent Task:
`tasks/20260930-homepage-getting-started-and-waitlist/000-main.md`

Implement only the new homepage structure so it can be reviewed in its real
responsive context. Use explicit placeholders for new proof assets and render
draft copy for evaluation, while keeping copy approval, asset production,
highlight ordering, and the final visual layout outside this approved scope.

## Requirements checklist

- [ ] The local homepage has the intended primary section order: concise hero,
      six-card highlights shell, then six-step Getting Started.
- [ ] The existing CLI installation chooser is moved from the hero into
      Getting Started step 1 without duplicating its maintained commands.
- [ ] The hero links to `#getting-started` and retains the existing GitHub and
      verified macOS header-download behavior unless the prototype review
      recommends a later change.
- [ ] The highlights shell renders six typed cards and supports draft title,
      description, status, and media fields.
- [ ] New or not-yet-approved proof assets render as clearly identifiable
      placeholders; no fabricated screenshot or conceptual image is presented
      as production evidence.
- [ ] The six selected themes remain explicitly unapproved copy used only to
      review structure in context.
- [ ] The Getting Started shell renders exactly six semantic ordered steps:
      install CLI, start workspace, download Desktop, connect Desktop, get the
      mobile app, and connect from mobile.
- [ ] The structural Desktop step reads maintained release metadata and
      presents truthful macOS availability plus Windows/Linux Desktop
      coming-soon states.
- [ ] The structural mobile step presents truthful store-coming-soon states
      and a non-functional waitlist slot that cannot submit or collect email.
- [ ] Duplicate top-level computer-to-phone content is removed from the
      prototype, and affected navigation/CTA anchors resolve to the new
      Getting Started section.
- [ ] One reviewable baseline is responsive, keyboard navigable,
      semantically ordered, light/dark compatible, and free from horizontal
      overflow, while its final visual composition remains unsettled.
- [ ] The prototype is built, tested, and shared through a local/LAN preview;
      it may be committed locally under the user's explicit authorization but
      is not pushed or published without a later explicit instruction.

## Approval boundary

Approval of this subtask authorizes implementation of structure only:

- content schemas and section registration;
- section order and anchor changes;
- a concise hero shell;
- six highlight-card shells;
- six getting-started-step shells;
- reuse of maintained installation and release data;
- placeholder treatment for new proof;
- responsive and accessible baseline behavior;
- focused structural tests and a local review preview.

It does **not** approve:

- any draft headline or description as final public copy;
- the sixth highlight;
- production of new captures or illustrations;
- reuse of an existing image as final proof for a revised claim;
- final highlight ordering;
- final card proportions, spacing, typography, composition, or animation;
- the final treatment of retained deep-dive sections;
- a functional waitlist form;
- a push, AWS change, or production deployment.

## Draft content used only for contextual review

The prototype may render the five current draft feature cards in this proposed
order:

1. One workspace for every model family.
2. Replace the parts you disagree with.
3. See what the agent is actually using.
4. Shape it around your workflow.
5. Start at your desk. Continue wherever you are.
6. Sessions become durable workspaces.

All six cards must carry source-level review metadata. The local preview may
show a discreet `Draft` or `Proof needed` treatment where it helps reviewers
avoid mistaking the candidate for publication-ready content. Such labels are
not intended for production.

## Structural design

### Hero shell

- Make the current installation content optional.
- Keep badge, title, short description, primary action, and secondary GitHub
  action.
- Point the primary action to `#getting-started`.
- Do not finalize hero height, whitespace, title line breaks, or action
  treatment during this subtask.

### Highlights shell

- Extend the existing feature-showcase model or introduce the smallest
  equivalent typed structure needed for six cards.
- Establish a review baseline of three columns on wide screens, two on
  intermediate screens, and one on phones.
- Support per-card title, description, media, alt text, and review status.
- Use placeholder panels for all new proof requirements.
- Existing reviewed images may be temporarily displayed only when clearly
  identified as candidate proof; their final claim binding belongs to subtask
  `015`.
- Do not optimize final image crops, compositions, or byte budgets yet.

### Getting Started shell

Render a semantic ordered sequence with these structural content types:

1. Embedded installation chooser.
2. Shell-command panel.
3. Release-backed platform download panel.
4. Connection instructions with code/address or media slot.
5. Store availability plus disabled waitlist slot.
6. Mobile connection instructions plus media slot.

The component contract should remain bounded to these known needs rather than
becoming a general page-builder system.

### Remaining page

- Move the provider strip away from the required primary sequence.
- Remove the old duplicate computer-to-phone action guide.
- Leave selected technical deep dives below Getting Started in their current
  form unless a minimal anchor/content adjustment is required.
- Update the final CTA to target Getting Started.
- Defer deep-dive pruning, reordering, and final spacing to subtask `015`.

## Execution plan

Status: Approved

First, define the narrow content types and registration needed to render the
hero, six highlight shells, and six heterogeneous getting-started steps. Make
the hero installation chooser optional and move the existing authored
installation content into step 1 without changing its commands.

Next, reorder the homepage content into the approved structural sequence and
populate the highlight and getting-started shells with explicitly draft text,
review statuses, maintained release data, real existing commands, and
placeholders for new proof. The waitlist position is a disabled explanatory
slot, not an input or fake submission.

Then, implement one restrained responsive baseline. The goal is to make
hierarchy, density, reading order, and component behavior observable—not to
lock final aesthetics. Avoid time-intensive polishing, new animations,
capture production, or layout variants before human review.

Finally, add focused structural tests, run the production-configured site
build and browser suite on an isolated port, and provide desktop/phone
light/dark screenshots plus a LAN-accessible interactive preview. The review
handoff explicitly lists all still-draft copy, placeholder assets, and
unsettled visual decisions.

### Implementation decisions and open questions

- Decision: structural implementation is independently approvable.
- Decision: copy, assets, ordering, and final layout remain Draft after this
  subtask.
- Decision: placeholders are required for new proof assets.
- Decision: use all six selected themes only as contextual draft content.
- Decision: place durable session workspaces last in the first prototype;
  final ordering remains deferred.
- Decision: inspectability is a result of explicit framework/plugin design and
  user-modifiable plugins. Open source adds full source-level transparency.
- Decision: implement one simple responsive baseline rather than multiple
  design variants.
- Decision: do not add a working form or collect email.
- Open question deferred to human review: final feature ordering and visual
  composition.

### Documentation

- Update landing development documentation only where the new structural
  section contracts or draft/placeholder states require maintainer guidance.
- Do not publish draft labels, approval notes, fixture instructions, or
  placeholder explanations as public product documentation.
- Record the prototype review URL/screenshots and unresolved decisions in this
  task's implementation notes after execution begins.

### Task checklist

- [ ] **AGENT:** Define the structural content types and section registration.
- [ ] **AGENT:** Make the hero installation chooser optional and move it to
      Getting Started step 1.
- [ ] **AGENT:** Add six highlight shells with draft/proof status support.
- [ ] **AGENT:** Add all six getting-started structural step types.
- [ ] **AGENT:** Integrate maintained Desktop release metadata and platform
      states.
- [ ] **AGENT:** Add the disabled waitlist integration slot.
- [ ] **AGENT:** Reorder sections and update affected anchors/CTAs.
- [ ] **AGENT:** Add focused content, semantic, keyboard, responsive, and
      placeholder tests.
- [ ] **AGENT:** Run the production-configured build and browser verification.
- [ ] **AGENT:** Provide LAN review links and desktop/phone light/dark
      screenshots.
- [ ] **HUMAN JUDGMENT:** Review structure in context without approving copy,
      proof assets, ordering, or final layout.
- [ ] **AGENT:** Record the review outcome and hand off to subtask `015`.

### Requirement verification

- Section-order evidence: built HTML and browser assertions show Hero,
  Highlights, and Getting Started in that exact primary order.
- Highlight-shell evidence: six typed cards render with draft status and
  placeholder behavior at desktop, tablet, and phone widths.
- Getting-started evidence: one browser test traverses all six semantic steps
  and verifies the real chooser, command, release data, platform states,
  connection content, disabled waitlist slot, and mobile connection shell.
- Availability evidence: maintained macOS release metadata and live link
  checks pass; Windows/Linux Desktop and mobile stores remain non-interactive
  and truthful.
- Accessibility evidence: heading order, ordered-list semantics, keyboard
  focus, link names, disabled controls, placeholder alt treatment, and status
  announcements pass.
- Approval-boundary evidence: repository inspection proves no new production
  proof asset, form endpoint, email input, AWS configuration, or production
  deployment was introduced.
- Human review evidence: LAN preview and screenshots are supplied with an
  explicit list of draft and unsettled elements.

### Additional implementation verification

- Run content/analytics tests, TypeScript/Astro build, and the full
  production-configured Playwright suite on an isolated port.
- Verify no horizontal overflow at representative wide, tablet, and phone
  widths.
- Verify light/dark theme behavior without treating placeholder styling as
  final.
- Verify the existing header Desktop download tests and release checksum
  contract still pass.
- Verify the existing user-owned long-running local preview process is not
  stopped or altered.
- Verify no push, AWS mutation, or production deployment occurs.

## Implementation Notes

- 2026-09-30: The user approved execution of this structural subtask only.
  Copy, proof assets, final ordering, final visual layout, and tasks `015` and
  `020` remain Draft.
- 2026-09-30: The sixth draft theme is durable session workspaces.
- 2026-09-30: Transparency copy must explain that explicit framework/plugin
  design and user-modifiable plugins provide inspectability. Open source is an
  additional source-level transparency value, not the primary mechanism.
- 2026-09-30: The user explicitly authorized a commit before structural
  implementation.