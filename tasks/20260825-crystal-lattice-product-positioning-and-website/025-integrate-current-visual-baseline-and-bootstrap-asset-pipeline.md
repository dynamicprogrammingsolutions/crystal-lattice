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
   `mobile/crystal-lattice-control-rn/README.md:306-367`,
   `mobile/crystal-lattice-control-rn/e2e/notificationBanner.e2e.test.ts:1-220`,
   `mobile/crystal-lattice-control-rn/e2e/websiteVisualCapture.e2e.test.ts:1-60`,
   and
   `mobile/crystal-lattice-control-rn/src/testing/MobileWebsiteVisualHarness.tsx:1-279`,
   plus
   `mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN/AppDelegate.swift:1-95`
   — production-screen Detox patterns, native harness selection, the
   implemented Stage C scenario and commands, and the ignored capture
   boundary.

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

### Revised Stage C visual direction

- Homepage proof should show tightly framed product UI without a phone bezel or
  other hardware frame. The homepage is about Crystal Lattice as a whole, not
  specifically the mobile client.
- The mobile page hero component already supports an optional light/dark image,
  but `mobile.yaml` currently provides none.
- `landing_page/public/session-workbench.png` is an obsolete four-phone
  composite. It contains clipped status bars, raw identifiers, and
  crystallography content and is not an acceptable mobile-page source.
- The mobile page may reuse the same reviewed active-session capture as the
  homepage, but only the mobile-page presentation should add a phone frame.
- Chat actions needs a tighter crop than the current retained derivative so
  the action labels remain readable at card size.
- Provider reasoning and usage/cost should preserve the contributed visual
  intent: a full product context plus a magnified focus region. The zoom,
  placement, border, and shadow should be generated programmatically from a
  reviewed source rather than assembled manually.
- A real hosted-model request can initialize a credible coding session, but the
  live request is a candidate-source refresh operation rather than part of
  ordinary screenshot capture, website build, or verification.
- The user's current `~/.crystal/config.json` includes a `codex-openai` agent
  using the OpenAI Responses provider and Codex tools, and
  `~/.crystal/auth/chatgpt-auth.json` is present. A refresh workflow must accept
  these paths as explicit read-only inputs, force ChatGPT auth instead of
  silently falling back to API-key auth, keep generated sessions under ignored
  output, and create repository workspaces only in automatically removed
  temporary directories.
- The originally proposed React Native issue is not a bounded source for this
  workflow. Its reproduction requires a React Native checkout, dependency
  installation, and an Android native bundle, so it was rejected before
  implementation.
- Starlette is used through the application's FastAPI dependency. Starlette
  1.4.0 contains a focused `GZipResponder` compatibility regression in
  `starlette/middleware/gzip.py`: downstream subclasses that used the previous
  constructor shape fail because `thread_minimum_size` became required. The
  retained provenance source is Starlette issue `#3414`.
- A shallow sparse checkout of Starlette 1.4.0 commit
  `3d6d6c20e795d02d22b358758bfa987b436a3ec4`, limited to `starlette/` and
  `tests/`, used approximately 1.4 MB and completed in approximately three
  seconds during the August 27, 2026 planning check. Repository inspection
  requires no installation, server, build, or simulator.

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

Proposed revised Stage C outputs after new approval:

- a pinned public-repository and public-issue input manifest plus a concise
  planning prompt;
- an explicit live refresh command that uses a caller-supplied Crystal Lattice
  config directory and ChatGPT login to produce an ignored candidate session;
- a reviewed, sanitized session fixture derived from the candidate and
  consumed by routine native capture without network or credentials;
- tightly cropped, unframed homepage sources for chat actions, session
  settings, and snapshots;
- reproducible reasoning and usage/cost focus composites with programmatic
  zoom callouts;
- one current framed active-session visual on the mobile page, derived from the
  same reviewed session state rather than the obsolete four-phone composite.

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

### Stage C — Reviewed coding-session source and corrected early visuals

The first one-scenario implementation remains useful infrastructure, but its
checkpoint framing was rejected. Replace the rejected candidate through the
following independently reviewable stages.

#### Stage C1 — Real-session candidate and reviewed fixture

Add a catalog command that parses its own command-specific arguments without
changing the generic runner or CLI. A representative invocation should be:

```bash
yarn visual-assets refresh-session coding-plan \
  --config-dir "$HOME/.crystal" \
  --config "$HOME/.crystal/config.json" \
  --agent codex-openai
```

Require an explicit configuration path or directory. Treat it as read-only,
force the selected request to use ChatGPT auth, and fail rather than falling
back to an API key. Do not copy, print, persist, or report credentials.

Use a checked-in source manifest containing:

- a public repository URL and exact commit SHA;
- a bounded snapshot of one public bug issue;
- a realistic developer prompt containing only the task to perform;
- the selected configured agent, required tools, and expected visible session
  shape.

Use Starlette 1.4.0 at commit
`3d6d6c20e795d02d22b358758bfa987b436a3ec4` with a sparse checkout of
`starlette/` and `tests/`. The provenance manifest may record the source issue
and revision, but the model-facing user prompt must not mention an issue
number, a pinned revision, fixture generation, screenshots, or the website.

The initial model-facing prompt should be:

> After upgrading Starlette, one of our custom `GZipResponder` subclasses
> stopped working. Its constructor still calls
> `super().__init__(app, minimum_size)`, and constructing it now fails with a
> `TypeError` saying that `thread_minimum_size` is missing. Please inspect the
> gzip middleware and existing tests, figure out what changed, and give me a
> focused plan for a backwards-compatible fix and regression coverage. Don't
> change the code yet.

For every refresh, create a new operating-system temporary directory, perform
the shallow sparse checkout there, run the request with that directory as the
workspace, and remove the complete directory when the generation command
finishes or fails. Do not keep a reusable repository cache.

Keep installation, build, server, simulator, and file-modification constraints
outside the user prompt as generation-policy instructions. Reject the
candidate if tool history shows dependency installation, a build or simulator
launch, source modification, or work outside the temporary checkout. Apply
bounded checkout-size and elapsed-time checks before starting the hosted
request.

Run the request through the public `AgentApplication` request path with an
isolated session store rather than through FastAPI or a duplicated send
implementation.

The hosted response is intentionally not treated as byte-deterministic.
Instead, write an ignored candidate session and provenance report, sanitize
provider-native IDs, absolute paths, account data, credentials, raw session
IDs, and volatile timestamps, and require explicit promotion into a reviewed
fixture. Routine capture consumes only the reviewed fixture and therefore
needs no repository network access, hosted model, or personal config.

Automated verification covers manifest pinning, command parsing, forced
ChatGPT auth, isolated output, sanitization, candidate/promotion separation,
and an application-layer integration path with a deterministic fake provider.

Manual checkpoint C1:

- judge whether the user request, tool activity, and final plan look like a
  credible real coding-agent session;
- judge whether the issue excerpt and response are concise enough for visual
  proof;
- judge whether the reviewed fixture is free of private, misleading, or
  distracting content.

#### Stage C2 — Unframed homepage workbench captures

Load the reviewed session fixture in the production-screen mobile harness and
capture light/dark states using semantic readiness checks.

Generate homepage sources without a device bezel:

- chat actions: a tight crop around the modal title and a useful readable set
  of action rows rather than the complete tall screen;
- session settings: a tight crop around the current settings modal and the
  controls needed to support the plugin-schema claim;
- snapshots: a tight crop around the current snapshots modal using sanitized
  short identifiers and the coding-plan session in any visible background.

The crop geometry belongs to each asset's programmatic build so a later
replacement can choose a different framing without changing the runner or CLI.
Do not show the system status bar, broken app header, composer, bottom tabs,
fixture IDs, or hardware frame in homepage derivatives.

Automated verification covers source dimensions, expected crop bounds,
light/dark outputs, no forbidden fixture text, asset budgets, website build,
and responsive browser contracts.

Manual checkpoint C2:

- judge whether each crop is large enough to read at the actual homepage card
  size;
- judge whether the three cards feel like coherent product proof without
  implying that the homepage is specifically about the mobile app.

#### Stage C3 — Reproducible provider focus composites

Add a reusable programmatic focus-callout pipeline. It receives one reviewed
source, creates a cleaned base crop, extracts and scales a second focus crop,
and composites the focus region with a controlled border, radius, placement,
and shadow. This remains ordinary executable JavaScript/ImageMagick behavior,
not a declarative pipeline language.

Use it for:

- reasoning: enlarge the reasoning-effort and verbosity controls over enough
  settings context to show where they live;
- usage/cost: enlarge the current turn's token, duration, cost, or explicitly
  labeled cost-estimation footer over a concise completed coding-plan message.

The callouts must remain readable at the provider-card size and must not hide
or fabricate proof-bearing text.

Automated verification covers deterministic composite dimensions, focus
geometry, light/dark parity, expected source relationship, byte budgets, and
website rendering.

Manual checkpoint C3:

- judge whether the zoom effect clarifies the claimed detail without looking
  like an unrelated pasted panel;
- judge whether the usage and cost labels remain truthful and legible.

#### Stage C4 — Mobile-page active-session hero

Add one current light/dark active-session image to the existing mobile hero.
Use the same reviewed coding-plan session, showing a readable session title,
the bounded issue-planning request, and enough of the assistant result to
communicate continuing real work from a phone.

The underlying native capture remains a clean source. Add a consistent generic
phone frame only in mobile-page presentation, preferably as website/CSS
presentation around the image so the same source can serve framed and
unframed consumers. Do not reuse the obsolete
`landing_page/public/session-workbench.png`.

This is an early release-safe proof of the mobile page's existing claim, not a
decision about the final task-150/task-160 visual set. Additional connection,
session-list, or action-gallery images remain deferred until an approved page
brief requires them.

Automated verification covers both themes, responsive hero layout, active
theme loading, alt text, image dimensions, and mobile/desktop browser
rendering.

Manual checkpoint C4:

- judge whether the framed active-session image makes the mobile-page value
  immediately understandable;
- judge whether the frame, crop, text density, and surrounding hero content
  remain balanced at desktop and phone website widths.

#### Stage C5 — Documentation, handoff, and final verification

Document the delivered session-refresh, reviewed-fixture, unframed crop,
focus-callout, and mobile-frame workflows in the existing consumer and
development visual-asset pages without duplicating architecture explanations.

Update the retained task-025 review/evidence package and task-160 handoff to
identify the provisional assets, their source manifest, freshness triggers,
capture commands, and later replace/retain decision boundary.

Run the complete programmatic asset tests, application-layer refresh
integration test, mobile component/Detox tests, public derivative checks,
website build, and Playwright visual suite. Manual checkpoints remain visual,
content, privacy, and product-communication judgments only.

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
- Recommendation: use the current `codex-openai` configured agent and require
  ChatGPT auth for the live fixture refresh.
- Recommendation: use the Starlette 1.4.0 `GZipResponder` constructor
  compatibility regression as the source task. Keep issue and revision
  provenance in the manifest while presenting only the realistic developer
  request to the model.
- Recommendation: add one framed active-session hero to the current mobile
  page and defer any broader mobile screenshot gallery to task 150/160.
- Decision: homepage derivatives do not include a phone frame; only the mobile
  page may add one.
- Decision: reasoning and usage/cost retain a generated focus-callout effect
  rather than becoming plain crops.
- Decision: preserve the reviewed light and dark captures as optimized pairs
  and use one theme-aware `<img>` element that loads only the active variant,
  then fetches the alternate variant only when the user changes themes.
- Open question: approve the exact Stage A keep/omit set after reviewing the
  corrected page.
- Open question: approve Stage C only after the browser-side workflow passes
  checkpoint B.
- Decision: the user approved the Starlette task, `codex-openai` ChatGPT-auth
  refresh path, and staged C1-C5 expansion.
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
- [x] Pass manual checkpoint B.
- [x] Obtain separate approval before Stage C.
- [x] If approved, implement and verify one native capture scenario.
- [x] Approve the revised Stage C1-C5 expansion.
- [ ] Implement the revised Stage C1 reviewed-session source.
- [ ] Pass manual checkpoint C1.
- [ ] Implement and pass checkpoint C2 for unframed workbench captures.
- [ ] Implement and pass checkpoint C3 for provider focus composites.
- [ ] Implement and pass checkpoint C4 for the mobile-page hero.
- [ ] Complete Stage C5 documentation, handoff, and final verification.
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

### August 26, 2026 — Checkpoint B approved and Stage C started

- The user approved the rewritten command/lifecycle architecture and requested
  continuation to the next human checkpoint.
- Commits `4690d8bc` and `6b811162` preserve the staged asset-workflow layer and
  the final command/lifecycle plus documentation layer separately.
- Stage C automates the existing `session-settings-plugins` proof rather than
  introducing a new public claim or changing the selected website visual set.
- Added a deterministic mobile harness that renders the production chat
  background and production session-settings modal with sanitized coding-agent
  messages and configuration.
- The catalog now treats the light and dark session-settings source masters as
  captured sources backed by one memoized Detox producer. Capture remains
  separate from reviewed-source promotion and public derivative update.
- Stage C will stop at checkpoint C with ignored light/dark source candidates;
  it will not promote them into `visual_assets/sources/` before human review.

### August 26, 2026 — Stage C implementation ready for checkpoint C

- Added `MobileWebsiteVisualHarness`, selected through the same native iOS
  launch-argument routing used by the existing mobile harnesses, with a
  deterministic in-process backend, sanitized coding-session messages, and
  production `SessionChatScreen` plus `SessionSettingsModal`.
- Added stable production modal and settings-scroll identifiers and a
  platform-neutral Detox scenario that captures light and dark settings
  candidates under the mobile ignored `artifacts/website-visual/` directory.
- Added iOS and Android Detox test commands plus build-and-capture commands.
- Wired the existing `session-settings-plugins` catalog asset to one memoized
  Detox producer and the captured-source lifecycle. Existing reviewed source
  masters remain the inputs for normal inspect/check/update.
- Mobile TypeScript verification and the four focused
  `SessionSettingsModal` component tests passed.
- The earlier iOS attempts exposed two unrelated environment/setup issues:
  CoreSimulator instability under memory pressure and an out-of-sync CocoaPods
  sandbox. The retry synchronized Pods, preserved the resulting lock checksum,
  and completed the Release simulator build.
- The first successful app launches still showed the normal application
  because the new harness was registered in JavaScript but omitted from the
  existing native `AppDelegate.swift` harness selector. Adding that bounded
  selector entry made the simulator run `MobileWebsiteVisualHarness`.
- The capture launches with Detox synchronization disabled, enters the
  production screen through an explicit idle harness control, and waits for
  visible `Model` and `Reasoning effort` settings before each screenshot.
- `yarn visual-assets:capture session-settings-plugins` passed the focused
  iOS Detox scenario and produced two distinct PNG candidates:
  `session-settings-light.png` and `session-settings-dark.png`, each
  1206×2622 pixels. The capture report processed 586,538 bytes.
- The light candidate SHA-256 is
  `698331c909d9dd61d079b3ce7f935421c261240e745487e836b7b13c384ccce9`;
  the dark candidate SHA-256 is
  `8c3347e20f0585f14d0994fa48ede78a7230a08823ce157468e62110cca8fd61`.
- The Android E2E APK and test APK build succeeded. Detox reached native
  instrumentation on the configured emulator, but its fixed five-second ANR
  watchdog reported a framework cold-start ANR in Android `ViewRootImpl`;
  successful canonical iOS capture now supplies the Stage C evidence.
- `yarn visual-assets:inspect session-settings-plugins` and the complete
  `yarn visual-assets:check` both pass. The candidates remain ignored, and no
  reviewed source master or public derivative changed.
- Manual checkpoint C is ready. Do not promote the candidates into
  `visual_assets/sources/` or update public derivatives before the user judges
  the native state, sanitization, readability, and claim support.

### August 27, 2026 — Checkpoint C framing rejected and retained sources audited

- Human review confirmed that the deterministic settings state demonstrates
  the intended plugin-provided controls, but rejected the capture framing for
  public use.
- The new candidate has a crowded status/header row, excessive dimmed space
  above the modal, a visible `website-visual-session` fixture identifier, and
  unrelated composer controls below the modal. The current trim/resize pipeline
  would preserve those distractions.
- The user noted that similar framing defects exist in the retained PNG source
  masters and approved the correction principle.
- An audit of all five retained light/dark pairs and their generated WebP
  derivatives confirmed that the defects survive publication:
  - `chat-actions-workbench` has a clipped status bar, a raw UUID session title,
    and a mixed/generic device frame;
  - `session-settings-plugins` has the same status/header and UUID problems,
    although the settings content itself is strong;
  - `session-snapshots-workbench` adds unrelated crystallography conversation
    content plus a raw snapshot/session identifier;
  - `provider-reasoning` uses an artificial two-scale composite with a large
    shadow and repeats the same raw UUID;
  - `provider-usage-cost` uses unrelated long-form content, a raw UUID/session
    footer, and a usage callout whose text becomes too small at card size.
- The dark variants mirror the same framing and content problems; their
  contrast is otherwise acceptable.
- Correcting the settings capture remains a bounded Stage C follow-up.
  Replacing the other four asset families would expand the original
  single-scenario native proof into multiple product scenarios and source
  migrations, so do not begin that broader implementation without an explicit
  staged scope decision.

### August 27, 2026 — Revised Stage C plan drafted

- The user requested a tighter chat-actions crop, deterministic zoom callouts
  for reasoning and usage/cost, unframed homepage proof, and a framed visual
  specifically for the currently image-less mobile page.
- The user also requested a real coding-session source generated from a public
  bug task and repository through the saved ChatGPT login under `~/.crystal`.
- The draft plan separates the non-deterministic, credentialed live refresh
  from deterministic routine capture: pinned inputs produce an ignored
  candidate, human review promotes a sanitized session fixture, and Detox plus
  programmatic image builds replay only the reviewed fixture.
- The originally proposed React Native source was rejected because its
  reproduction requires dependency installation and an Android native bundle.
- The replacement is the Starlette 1.4.0 `GZipResponder` constructor
  compatibility regression. A shallow sparse source-and-test checkout is
  approximately 1.4 MB and needs no installation or server/native execution.
- The source issue and exact Starlette revision remain internal provenance.
  The model receives only a normal developer request describing the failing
  subclass and asking for a focused fix and regression-test plan.
- The generation script creates a fresh operating-system temporary checkout
  for each request and removes it on success or failure. The current
  `codex-openai` configured agent remains the recommended generation target.
- The existing generic CLI and runner do not need new semantics. A
  catalog-defined `refresh-session` command can parse command-specific
  `--config-dir`, `--config`, and `--agent` arguments directly.
- The task execution plan is returned to Draft because the revised C1-C5 work
  is materially broader than the previously approved one-screenshot proof.
  Do not start the expansion until the user approves it.

### August 27, 2026 — Revised Stage C approved

- The user approved the revised plan using the bounded Starlette
  `GZipResponder` compatibility task, the `codex-openai` agent, forced ChatGPT
  authentication from explicitly supplied `~/.crystal` configuration, and
  staged C1-C5 checkpoints.
- Stage C1 is authorized. Stop at its human content/privacy checkpoint before
  promoting a generated session fixture or beginning C2 visual recapture.