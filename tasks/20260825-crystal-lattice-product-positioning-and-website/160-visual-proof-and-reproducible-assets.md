# Produce Visual Proof and Reproducible Website Assets

Create the real screenshots, diagrams, and short interaction sequences required
by approved content briefs, with deterministic product states and a
maintainable refresh workflow.

## Requirements checklist

- [ ] Every production visual has an approved communication purpose and maps to
      a current product claim.
- [ ] Screenshots and recordings use sanitized, deterministic product,
      session, configuration, and connection states.
- [ ] Mobile and desktop captures use reliable automation where practical and
      identify any required human/native verification.
- [ ] Architecture, compatibility, plugin, transparency, session, and
      connectivity diagrams are accurate, accessible, and maintainable.
- [ ] Draft output remains ignored; only approved optimized production files
      enter `landing_page/public/`.

Parent Task: `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md`

Depends On:

- `tasks/20260825-crystal-lattice-product-positioning-and-website/025-integrate-current-visual-baseline-and-bootstrap-asset-pipeline.md`
- `tasks/20260825-crystal-lattice-product-positioning-and-website/150-website-information-architecture-and-content-briefs.md`

## Candidate proof

- one configured-agent workspace across several profiles;
- session search/archive/status organization;
- usage, token, cost, and duration transparency;
- active-agent inspection;
- plugin-provided action or UI propagation;
- local and bridge mobile connection;
- natural-language customization concept only if delivered;
- compatibility and contribution view.

## References

### Start here

1. `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md:8-186`
   — shared proof, storage, privacy, handoff, and scope rules.
2. `tasks/20260825-crystal-lattice-product-positioning-and-website/150-website-information-architecture-and-content-briefs.md:1-115`
   plus its approved page briefs, claim/proof matrix, visual requirements, and
   completion manifest. Stop if incomplete.
3. `tasks/20260825-crystal-lattice-product-positioning-and-website/025-integrate-current-visual-baseline-and-bootstrap-asset-pipeline.md:1-219`
   plus its visual manifest, asset review, validation/optimization workflow,
   accepted public baseline, and completion evidence. Reuse rather than
   reconstruct its technical foundation.
4. `landing_page/AGENTS.md:41-98` — claim, source, research/privacy, visual, and
   verification boundaries.
5. `landing_page/docs/development/specifications/product-website-content/content-spec.md:238-274`
   — proof and progressive-revision target.
6. `landing_page/docs/development/research/visual-communication-and-reproducible-assets.md:1-265`
   — retained visual hypotheses, reproducible asset-pipeline requirements,
   automation boundaries, review, and freshness rules.
7. `landing_page/docs/development/content-system.md:79-95` and
   `landing_page/docs/development/content-system.md:134-156` — current public
   asset and build/verification behavior.
8. `mobile/crystal-lattice-control-rn/AGENTS.md:1-253`,
   `mobile/crystal-lattice-control-rn/docs/development/index.md:1-3`,
   `desktop/crystal-lattice-control-desktop-rn/docs/development/index.md:1-5`,
   and
   `desktop/crystal-lattice-control-desktop-rn/docs/development/native-ui-testing.md:1-23`
   — package-specific mobile rules and desktop development/native-test routes.
   Follow the focused Detox, XCUITest, connection, or desktop convention page
   selected by the approved visual manifest.

## Known facts and supporting details

- A production visual must prove an approved current claim, not merely fill
  space.
- Draft captures and generated intermediates are disposable; only reviewed
  production files move to `landing_page/public/`.
- Current mobile and desktop UI states may differ, and native/manual
  verification remains necessary where automation cannot prove presentation.
- Sanitized deterministic sessions, files, settings, notifications, and
  connections are required.
- Task 025 establishes only an early baseline and reusable technical
  foundation. Its accepted images are not automatically the final visual set;
  task-150 briefs determine what this task must retain, replace, or add.
- Screenshot-generation mechanics are documented as current implementation
  only after they exist.

## Expected outputs

Retained visual package:

```text
landing_page/research/160-visual-proof-and-reproducible-assets/
├── visual-manifest.yaml
├── capture-state-manifest.json
├── asset-review.csv
├── accessibility-and-alt-text-review.md
└── completion-manifest.json
```

Implementation outputs:

- reuse, extension, or explicit migration of the task-025 manifest,
  validation, optimization, and browser-capture workflow;
- capture scripts, fixtures, demo plugins, and tests in their owning packages;
- approved optimized files under `landing_page/public/`;
- `landing_page/docs/development/visual-content-and-screenshot-generation.md`
  when a reusable current workflow is delivered;
- updates to `landing_page/docs/development/content-system.md` for implemented
  asset/content behavior;
- exact asset handoff to
  `tasks/20260825-crystal-lattice-product-positioning-and-website/170-validated-website-release-and-product-integration.md`.

Disposable output:

- `landing_page/artifacts/research/160-visual-proof-and-reproducible-assets/`
  for drafts, raw captures, recordings, frames, and generated previews.

## Scope boundaries

- Do not capture private user data, credentials, real private sessions, or
  unapproved third-party content.
- Do not stage future product behavior as if delivered.
- Do not modify unrelated product UI merely to make a screenshot attractive;
  route required product work to its owner.
- Do not implement final page copy or information architecture.
- Do not create a content-system specification unless actual delivered
  complexity justifies a separately approved scope.

## Execution plan

Status: Draft

Create the final visual manifest from approved briefs by extending or
explicitly migrating the task-025 foundation. Build or reuse deterministic
demo plugins, sessions, files, notifications, and connection states. Use
Detox/mobile automation, macOS production-root testing, browser capture, or
focused manual capture according to the boundary being proven.

Keep drafts and generated intermediates under ignored package artifacts.
Review content, privacy, cropping, readability, alt text, light/dark behavior,
device framing, compression, and freshness before promoting files to
`public/`.

### Implementation decisions and open questions

- Decision: no production visual is created merely to fill layout space.
- Decision: task-025 assets remain provisional until an approved task-150
  claim/proof brief selects them.
- Recommendation: automate high-churn UI captures and source diagrams in a
  maintainable text/vector format.
- Open questions: exact visual set, video/GIF policy, device frames, visual
  refresh cadence, and whether the content system needs a later formal asset
  contract.

### Documentation

- Add current screenshot/visual generation documentation only after the
  workflow exists.
- Update content-system documentation for implemented asset types.
- Keep target proof requirements in the content specification/page briefs.

### Task checklist

- [ ] Create and approve the visual manifest.
- [ ] Review and reuse or migrate the task-025 asset-pipeline foundation.
- [ ] Prepare sanitized deterministic demo states.
- [ ] Implement or reuse capture automation.
- [ ] Capture mobile, desktop, browser, and diagrams.
- [ ] Complete visual and privacy review.
- [ ] Add alt text and responsive presentation guidance.
- [ ] Optimize and promote approved assets.
- [ ] Verify assets through real website pages.

### Requirement verification

- Each production visual corresponds to current verified product behavior.
- No credentials, personal data, private sessions, or misleading staged state
  is present.
- Captures are reproducible or have a documented human boundary.
- Public assets render accessibly and responsively.
