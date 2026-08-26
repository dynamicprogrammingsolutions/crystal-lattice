# Integrate the Current Visual Baseline and Bootstrap the Asset Pipeline

Integrate the existing landing-page screenshot contribution as a truthful,
readable, performant early visual baseline and establish the smallest reusable
asset workflow that later visual-production work can extend.

## Requirements checklist

### Functional requirements

- [ ] The relevant screenshot contribution is integrated on current
      `develop` while preserving the original author's authorship and current
      website content.
- [ ] Every visual retained in public content accurately supports its
      associated current product claim and remains readable on desktop and
      mobile.
- [ ] Public images use bounded, optimized delivery that avoids unnecessary
      eager or duplicate theme-variant downloads.
- [ ] Retained visuals have useful alternative text and render correctly in
      supported themes and responsive layouts.
- [ ] A minimal reproducible programmatic asset catalog, source lifecycle,
      validation, and browser-review workflow exists for the accepted early
      visual baseline.

### Non-functional requirements

- [ ] Public visuals contain no fabricated product UI, credentials, private
      data, misleading platform framing, contradictory connection behavior, or
      planning placeholders.
- [ ] Unreviewed capture candidates and review output remain ignored; reviewed,
      sanitized source masters remain outside `landing_page/public/`, and only
      optimized derivatives enter `landing_page/public/`.
- [ ] Work proceeds through the approved Stage A and Stage B manual
      checkpoints; native capture work does not start without separate Stage C
      approval.

Parent Task: `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md`

Depends On:

- `tasks/20260825-crystal-lattice-product-positioning-and-website/020-current-product-and-compatibility-baseline.md`

## References

### Start here

1. `tasks/20260825-crystal-lattice-product-positioning-and-website/000-main.md:8-186`
   — shared product, proof, storage, privacy, task-handoff, and scope
   boundaries.
2. `tasks/20260825-crystal-lattice-product-positioning-and-website/020-current-product-and-compatibility-baseline.md:1-125`
   plus its accepted compatibility and feature outputs. Stop before public
   promotion if incomplete.
3. `tasks/20260825-crystal-lattice-product-positioning-and-website/030-release-safe-early-user-website.md:1-128`
   — downstream baseline website outcomes, current claim boundaries, and
   verification expectations.
4. `tasks/20260825-crystal-lattice-product-positioning-and-website/160-visual-proof-and-reproducible-assets.md:1-136`
   — later final-visual owner, expected reusable outputs, and automation
   boundaries.
5. `landing_page/AGENTS.md:41-104` — claim accuracy, current/public source,
   privacy, visual, and verification rules.
6. `landing_page/docs/development/content-system.md:79-97` and
   `landing_page/docs/development/content-system.md:138-161` — current
   screenshot sections, public-file boundary, and build/preview verification.
7. `landing_page/docs/visual-assets.md:1-659` — supported asset-author workflow
   for assets, programmatic builds, direct commands, lifecycle callbacks,
   captured sources, catalog commands, and verification.
8. `landing_page/docs/development/visual-content-and-screenshot-generation.md:1-568`
   — catalog dispatch, direct-command and lifecycle composition, runtime
   services, prepared mutations, source producers, and verification internals.
9. `landing_page/docs/development/research/visual-communication-and-reproducible-assets.md:151-268`
   — visual manifest, deterministic state, automation, review, promotion, and
   freshness model.
10. `mobile/crystal-lattice-control-rn/AGENTS.md:193-222`,
   `mobile/crystal-lattice-control-rn/README.md:306-350`, and
   `mobile/crystal-lattice-control-rn/e2e/notificationBanner.e2e.test.ts:1-220`
   — existing production-screen Detox and screenshot patterns if Stage C is
   separately approved.

### Contribution and review references

- Source branch: `origin/feat/CL-291/landing-page-for-app`.
- Source commit:
  `2858ae1ad85f40f16c526d01a7128241b8688e05`.
- Review branch: `review/CL-291-landing-page-screenshots`.
- Author-preserving cherry-pick:
  `e88aa46ee8d6bd0969c63c78f8e152f1fd938974`.
- Fresh review worktree:
  `/Users/ferenci84/Dev/Mine/ai-agent-platform-cl291-landing-review`.

## Known facts and supporting details

### Import and verification

- The remote feature branch contains one commit not merged into
  `origin/develop`.
- Cherry-pick preserved author
  `loneranger455-maker <rangerlone547@gmail.com>`; the current user is recorded
  only as committer.
- One `mobile.yaml` conflict was resolved by retaining the current Crystal
  Lattice wording and adding the contributed dark-image source.
- `yarn build` completed all five static routes.
- Eight headed Chrome Playwright scenarios passed across the home/mobile
  routes, desktop/phone widths, and light/dark themes.
- Browser validation found no broken image assets.
- A browser-only layout review confirmed that two provider cards and three
  session-workbench cards per desktop row materially improve readability.

### Performance baseline

- The homepage requests 24 images totaling 29,918,022 bytes.
- Light and dark image variants are both ordinary `<img>` elements and both
  load even though one is hidden.
- Several sources are 2,000–5,000 pixels tall and are displayed as small
  thumbnails.
- The contributed image set adds approximately 29 MB of public files before
  generated-site output.

### Visual review baseline

Keep after focused crop and optimization:

- provider reasoning and verbosity;
- chat actions;
- snapshots;
- session settings and plugins.

Narrow, relabel, or retain only temporarily:

- usage/cost, because the current card also claims attachment behavior not
  visibly demonstrated;
- session attachments, because the screenshot shows adding input media rather
  than preserving generated/session-owned assets;
- session list, because its repeated generic sessions do not yet demonstrate
  a serious coding workspace.

Replace or omit before public promotion:

- web search/citations, because citations are not visibly proved;
- caching/compaction, because unrelated content and large annotations obscure
  the claimed behavior;
- local connection diagram, because a maintainable source diagram would
  communicate the ordinary process and clients more clearly;
- bridge diagram, because its local `ws://192.168.1.66:4000` state contradicts
  the adjacent AWS/CloudFront remote-bridge instructions;
- mobile hero capture, because the crystallography answer weakens
  coding-agent positioning and the platform screenshot/device frame appears
  inconsistent.

### Existing infrastructure

- The mobile package already uses production-screen Detox harnesses,
  launch-argument scenario selection, stable test identifiers, and
  `device.takeScreenshot()`.
- The public backend and frontend SDK can create sessions, append/send
  requests, observe events, and persist/export session state.
- The existing OpenRouter image-generation provider can create or transform
  one source image, but provider modernization or a direct OpenAI image
  provider is separate plugin-owned work.
- A live hosted-model request is useful for seeding authentic content but is
  not deterministic enough to run during every screenshot refresh.
- The older screenshot worktree has an uncommitted
  `landing_page/package-lock.json`; do not discard or remove that worktree
  without resolving its ownership.

## Expected outputs

Current executable catalog and reviewed source masters:

```text
landing_page/visual_assets/
├── config.mjs
└── sources/
```

Retained review package:

```text
landing_page/research/025-current-visual-baseline-and-asset-pipeline/
├── asset-review.csv
├── performance-baseline.json
├── accessibility-and-alt-text-review.md
└── completion-manifest.json
```

Stage A implementation:

- an author-preserving imported commit followed by a separate corrective
  commit or commits;
- corrected responsive card layout and visual content mapping;
- optimized public image files and their authored content references;
- loading, decoding, dimensions, theme behavior, and alt-text improvements;
- removal or omission of misleading public visuals.

Stage B implementation:

- a programmatic asset catalog with catalog-defined commands, direct asset
  commands, composable asset lifecycle callbacks, and opaque asset config;
- explicit reviewed-file and captured-source lifecycles;
- per-asset, per-variant, and complete-catalog commands;
- image path, dimensions, format, byte-budget, and broken-image checks;
- reproducible desktop/mobile and light/dark Playwright captures;
- deterministic capture-to-reviewed-source and reviewed-to-public
  optimization/promotion commands;
- current implementation documentation only for behavior actually delivered.

Optional Stage C implementation after separate approval:

- one focused mobile website-visual scenario in the owning mobile package;
- a production-screen Detox harness or approved real-backend boundary;
- deterministic native capture consumed through the programmatic source
  producer and reviewed-source workflow.

Disposable output:

- `landing_page/artifacts/visual-assets/`
  for raw screenshots, full-page captures, contact sheets, generated variants,
  Playwright output, and optimization diagnostics.

## Scope boundaries

- Do not select the final task-160 visual set or preempt task-150 page briefs.
- Do not update the OpenRouter image provider or add a direct OpenAI image
  provider in this task.
- Do not use image generation to alter product text, controls, citations,
  settings, connection state, notifications, or other proof-bearing UI.
- Do not make the routine capture path depend on a live model, changing GitHub
  issue, unpinned repository revision, personal configuration, or private
  credentials.
- Do not update the roadmap or deploy the website without separate authority.
- Do not remove the older dirty worktree or discard its lockfile change.
- If Stage A or Stage B requires product changes outside the landing package,
  or a solution materially more complicated than the approved bounded
  workflow, stop and ask the user.
- Stage C and any real-provider/GitHub-workspace seeding work require a new
  approved checkpoint before implementation.

## Execution plan

Status: Approved

### Stage A — Merge-ready visual baseline

Keep the author-preserving cherry-pick as the contribution/import commit. Add a
separate corrective change that increases screenshot readability, removes or
relabels misleading proof, optimizes production files, avoids unnecessary
theme-variant loading, and adds specific alternative text.

Run the landing build and headed desktop/mobile, light/dark browser review.
Record the accepted asset classification and performance evidence.

Manual checkpoint A:

- judge whether each retained screenshot clearly and truthfully supports its
  associated current product claim;
- judge whether the corrected desktop/mobile and light/dark presentation is
  readable, visually balanced, and free of confusing or misleading proof.

### Stage B — Minimal asset-pipeline foundation

Create one executable JavaScript catalog for the accepted assets. Pipelines are
replaceable programmatic functions, reusable processing elements are ordinary
functions, and unique processing may remain beside its only asset. Keep
reviewed source masters outside `public/`; retain imported commit/path
information as provenance rather than a runtime dependency.

Add focused website-side checks for asset existence, dimensions, formats, byte
budgets, alternative text, and responsive rendering. Support explicit
per-asset and per-variant inspection, public update, and complete-catalog
verification. Keep capture, reviewed-source promotion, public transformation,
and browser presentation as separate lifecycle operations. Turn the headed
Playwright review into a reusable capture/validation command.

Document only the workflow that is actually implemented.

Manual checkpoint B:

- judge whether the executable catalog and programmatic pipeline extension
  points are understandable, proportionate, and flexible enough for static,
  custom-generated, and Detox-produced assets;
- judge whether the reviewed-source, capture-candidate, promotion, and public
  derivative boundaries are appropriate and maintainable;
- judge whether the current website screenshots remain visually suitable,
  readable, and truthful at their actual presentation sizes;
- judge whether the current implementation documentation is sufficient for a
  contributor to add or refresh an asset without reconstructing design
  decisions;
- decide whether the optional native capture proof in Stage C is valuable
  enough to authorize.

### Stage C — Optional native capture proof

After separate approval, add one production-screen Detox visual scenario and
route its named outputs through the Stage B source-producer, review, and
optimization workflow.

Use a deterministic in-process backend or retained reviewed session fixture.
A real provider may seed a fixture once, but routine captures replay the
sanitized state and wait for semantic UI checkpoints rather than fixed times.

Manual checkpoint C:

- judge whether the native capture presents a credible, current, and visually
  useful product state;
- judge whether its visible content is sanitized and avoids misleading product
  implications;
- judge whether its optimized website presentation remains readable and
  supports the intended claim.

### Implementation decisions and open questions

- Decision: preserve `e88aa46e` as the import commit and place corrections in
  later commits.
- Decision: retain `e88aa46e` and original paths as provenance only; current
  source masters must make ordinary generation independent of Git history.
- Decision: define assets and replaceable pipelines programmatically in one
  executable catalog rather than creating a declarative pipeline language.
- Decision: keep capture, source promotion, derivative update, and verification
  as separate commands so expensive producers do not run during normal checks.
- Decision: use two provider cards and three session-workbench cards per
  desktop row as the Stage A starting point.
- Decision: diagrams carrying product facts use maintainable SVG or equivalent
  source rather than generated raster text.
- Decision: real model output may seed reviewed fixture content, but routine
  capture is deterministic.
- Decision: preserve the reviewed light and dark captures as optimized pairs
  and use one theme-aware `<img>` element that loads only the active variant,
  then fetches the alternate variant only when the user changes themes.
- Open question: approve the exact Stage A keep/omit set after reviewing the
  corrected page.
- Open question: approve Stage C only after the browser-side workflow passes
  checkpoint B.
- Open question: decide later whether OpenRouter Image API modernization or a
  direct GPT Image provider deserves separate plugin work.

### Documentation

- Keep `landing_page/docs/visual-assets.md` as a standalone consumer guide for
  developers adding assets, builds, commands, lifecycle callbacks, captured
  sources, and catalog commands.
- Keep
  `landing_page/docs/development/visual-content-and-screenshot-generation.md`
  as current architecture and maintainer documentation for dispatch, runtime
  services, lifecycle composition, mutation safety, and extension boundaries.
- Keep detailed recipes in the consumer guide and link rather than duplicate
  them in development documentation.
- Update `landing_page/docs/development/content-system.md` only with the
  content/public-file integration summary and routes to the two focused pages.
- Update product-content requirements with implementation and verification
  evidence; do not change the content target unless Stage A exposes a genuine
  target question.

### Task checklist

- [ ] Confirm task-020 product/compatibility facts needed by retained visuals.
- [x] Preserve and verify the author-attributed import commit.
- [x] Complete Stage A layout, content, accessibility, and performance
      corrections.
- [x] Run automated and headed browser verification.
- [x] Pass manual checkpoint A.
- [x] Create the initial programmatic visual-asset catalog and retained asset
      review.
- [x] Add website-side asset validation and optimization.
- [x] Add reusable Playwright capture/visual checks.
- [x] Add standalone visual-asset consumer documentation and update current
      architecture documentation.
- [ ] Pass manual checkpoint B.
- [ ] Obtain separate approval before Stage C.
- [ ] If approved, implement and verify one native capture scenario.
- [ ] Record completion evidence and the task-160 handoff.

### Requirement verification

- Git history shows the original contributor as author of the imported change.
- Every public visual has a current claim, source, alt text, viewport/theme
  review, and accepted retain/replace decision.
- Browser evidence confirms readable desktop/mobile presentation with no
  missing images or visible placeholders.
- Network and file reports confirm the approved asset budgets and loading
  behavior.
- The executable catalog can reproduce and validate selected variants and the
  complete accepted Stage A public set without reading deleted files from Git
  history.
- Any Stage C evidence uses production screens and deterministic sanitized
  state.

### Additional implementation verification

- Run `yarn build` from `landing_page/`.
- Exercise home/mobile routes at representative desktop and phone widths in
  light and dark themes.
- Verify keyboard, semantic structure, contrast, alt text, image dimensions,
  layout stability, lazy loading, and theme switching.
- Confirm raw captures, generated variants, browser traces, and contact sheets
  remain ignored.
- Confirm no provider, mobile, desktop, bridge, or runtime behavior changed
  unless separately approved.

## Implementation Notes

### August 25, 2026 — Stage A started

- The user approved execution on
  `review/CL-291-landing-page-screenshots`.
- Commit `e88aa46e` remains the author-preserving import commit.
- Task 020 is not complete. Stage A may reach a review-ready branch checkpoint,
  but its visuals are not approved for public promotion until the dependency's
  required facts are accepted.
- Stage A will preserve optimized light/dark pairs behind one theme-aware image
  element. This avoids duplicate initial requests while keeping each website
  theme visually coherent.
- The contradictory connection diagrams, unsupported provider proof, and
  misleading mobile hero capture will be omitted rather than replaced with
  speculative visuals.

### August 25, 2026 — Stage A implementation ready for checkpoint A

- The provider proof uses two desktop columns and retains only reasoning
  controls plus usage/cost transparency.
- The session-workbench proof uses three desktop columns and retains only chat
  actions, snapshots, and settings/plugins. Mobile cards use a wider horizontal
  snap layout.
- Current public content omits the contradictory local/bridge diagrams,
  unsupported search/citation and cache/compaction proof, generic session-list
  and attachment captures, and the misleading mobile hero screenshot.
- Five retained light/dark capture pairs were trimmed, resized, stripped, and
  encoded as WebP with matching dimensions and specific alternative text:
  provider reasoning, provider usage/cost, chat actions, session snapshots,
  and session settings/plugins.
- The active light set totals 264,884 bytes and the active dark set totals
  239,020 bytes. The ten files total 503,904 bytes, but only the selected set
  loads initially; the alternate set loads once only if the user changes
  themes. This replaces the reviewed state in which 24 images totaling
  29,918,022 bytes loaded both variants.
- `ThemedImage.astro` renders one actual image element with light/dark source
  metadata. The layout applies the active source after restoring the saved or
  preferred theme and updates that element when `data-theme` changes.
- The unused mobile frame and all rejected contributed raster files were
  removed from current public output. The preexisting unrelated
  `session-workbench.png` remains for the complete Stage B manifest audit.
- `yarn build` passed and generated all five routes.
- Eleven headed Chrome checks passed: home/mobile routes at desktop/phone
  widths in light/dark themes, the focused layout scenario, active-theme
  network loading and toggle behavior, and dark-theme persistence across Astro
  client navigation. No loaded image was missing.
- Initial homepage navigation requests none of the lazy proof images. Forcing
  every proof image to load in light mode requests only the 264,884-byte light
  set; starting in dark mode requests only the 239,020-byte dark set. Toggling
  after loading one theme requests the alternate set once.
- Disposable review captures remain under
  `landing_page/artifacts/review/cl291-screenshots/`.
- The incomplete task-020 dependency still blocks public promotion.

### August 25, 2026 — Checkpoint A approved

- The user approved the Stage A implementation by requesting that it be
  committed and that work continue to the next checkpoint.
- Task 020 remains incomplete, so checkpoint approval does not authorize
  public promotion.
- Stage B is authorized. Stage C remains separately gated.

### August 25, 2026 — Stage B implementation ready for checkpoint B

- Added the retained visual manifest, 12-row asset review, performance
  baseline, and accessibility/alternative-text review under
  `landing_page/research/025-current-visual-baseline-and-asset-pipeline/`.
- Added `scripts/visual-assets.mjs` with `inspect`, `update`, and `check`
  commands. It extracts source images from `e88aa46e`, applies the declared
  ImageMagick transforms, validates content mappings, dimensions, byte
  ceilings, per-theme budgets, and SHA-256 values, and compares generated
  candidates byte-for-byte with `public/`.
- `yarn visual-assets:update` regenerated all ten derivatives without changing
  their Git state. A following `yarn visual-assets:check` passed.
- Added package-owned Playwright configuration and 11 visual contracts covering
  desktop/phone, home/mobile, light/dark, image semantics, column layout,
  lazy active-theme loading, toggling, and Astro client navigation.
- `yarn test:visual` and `yarn test:visual:headed` both passed all 11 tests.
  Thirty-six current full-page/focused captures are available under the ignored
  task artifact directory.
- Added package scripts, Playwright 1.55.0 development dependency, and
  synchronized Yarn/npm lockfiles. Frozen Yarn installation and npm
  package-lock verification passed.
- Added current package documentation for the manifest, ImageMagick commands,
  themed image behavior, browser checks, generated output, and change workflow.
  The package indexes, README, and AGENTS guidance route to it.
- Documentation preparation and MkDocs build passed. Reported navigation,
  absolute-link, and API-reference warnings predate this task.
- The ignored generation report and Playwright captures are the checkpoint-B
  manual review inputs. `completion-manifest.json` remains deferred until the
  task can complete; task 020 still blocks public promotion and Stage C remains
  optional.

### August 26, 2026 — Stage B architecture revised before checkpoint B

- Commit `f52e4edc` preserves the first Stage B implementation before the
  architecture revision.
- The user rejected a declarative pipeline-definition language and approved a
  single executable JavaScript catalog with replaceable programmatic pipelines
  and an explicit source lifecycle.
- Moved the ten accepted PNG source masters to
  `landing_page/visual_assets/sources/`. Their imported revision and original
  paths remain provenance in `visual_assets/config.mjs`; routine generation no
  longer reads deleted files through `git show`.
- Replaced the task-specific YAML manifest and monolithic script with a
  package-owned catalog plus generic API, selection, validation, runner,
  programmatic ImageMagick operations, CLI, and Detox source-producer modules.
- Added `list`, `capture`, `promote-source`, `inspect`, `update`, and `check`
  commands. Inspection and checking default to all assets when no selector is
  supplied; mutating commands require an explicit asset or `--all`.
- Asset and variant selectors allow one derivative to be processed without
  regenerating the complete catalog.
- Capturing writes only ignored candidates. Promotion explicitly updates a
  reviewed source master, and public update remains a separate operation.
  Ordinary inspection, update, and checking never invoke Detox or another
  source producer.
- The Detox producer exposes multiple named outputs from one memoized command,
  allowing one package-owned native scenario to serve several configured
  assets.
- Nine focused Node tests cover programmatic operations, one-off pipeline
  elements, catalog validity, selection, explicit mutation selection,
  capture/promotion separation, one-run/multiple-output Detox behavior, and
  prevention of partial public updates when a later candidate fails.
- The selected dark provider-reasoning variant and all ten current variants
  regenerate and pass byte-for-byte checking from current source masters.
- Each maintained source master has the same Git blob as its recorded imported
  source. Selected-variant and `--all` public updates both leave the approved
  WebP files unchanged.
- Playwright reports and captures now use the reusable
  `landing_page/artifacts/visual-assets/` boundary. The development
  documentation describes the executable catalog and source lifecycle.
- `yarn verify:visual` passed nine programmatic asset tests, all ten derivative
  checks, and all eleven headless browser scenarios. The same eleven scenarios
  passed headed.
- Documentation preparation and MkDocs build passed with only the previously
  reported navigation, absolute-link, and API-reference warnings.
- Checkpoint B remains open. No native capture scenario has been added, and
  Stage C remains separately gated.

### August 26, 2026 — Manual-checkpoint evidence clarified

- The user requires manual checkpoints to contain only outcomes that need
  visual, architectural, product, or editorial judgment.
- Deterministic regeneration, hash, byte, path, Git-diff, test, build, and
  report checks remain automated verification and are no longer repeated as
  manual instructions.

### August 26, 2026 — Catalog commands and asset lifecycle finalized

- The user found the prior `variant.pipeline` execution implicit and the
  identity `defineAsset`/`defineVisualAssets` helpers insufficiently
  inspectable.
- `defineAsset` now validates the common `id`, `metadata`, `config`,
  `commands`, and `lifecycle` contract. Asset-specific config remains opaque
  and is interpreted only by assigned callbacks.
- Assets may define direct commands, lifecycle callbacks, or both. Missing
  operations are explicit rather than implied by a fixed image schema.
- `defineVisualAssets` now validates catalog commands and assets, builds the
  asset index, exposes command names to the CLI, and dispatches complete
  catalog workflows.
- The catalog visibly defines the ordering of `list`, `inspect`, `check`,
  `update`, `capture`, and `promote-source`. Each workflow explicitly chooses
  a direct asset command, composed lifecycle stages, or unsupported behavior.
- The runner now provides only argument selection, runtime/path/process
  services, command-local cache, prepared-effect application, asset
  description, and reports. It no longer interprets image variants, sources,
  builds, expectations, content bindings, or publication.
- The CLI derives supported commands from the catalog. New catalog commands
  can be invoked through `yarn visual-assets <command>` without CLI or runner
  changes.
- Image-specific config and behavior moved to
  `scripts/visual-assets/lifecycle/image.mjs`. The current assets use lifecycle
  composition; tests also cover direct-command-only and mixed assets.
- Twelve focused Node tests pass, including direct/lifecycle coexistence,
  catalog selection, unknown common keys, capture/promotion separation, Detox
  output memoization, explicit per-asset direct-versus-lifecycle resolution,
  and prepare-before-apply mutation safety.
- Added `landing_page/docs/visual-assets.md` as the standalone consumer guide
  for developers adding or extending visual assets.
- Refocused
  `landing_page/docs/development/visual-content-and-screenshot-generation.md`
  on catalog dispatch, runner services, lifecycle composition, prepared
  mutations, ownership, testing, and extension invariants.
- Checkpoint B remains open for human architectural, documentation, and visual
  judgment.