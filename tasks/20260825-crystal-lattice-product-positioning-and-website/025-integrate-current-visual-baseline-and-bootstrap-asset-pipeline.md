# Integrate the Current Visual Baseline and Bootstrap the Asset Pipeline

Integrate the existing landing-page screenshot contribution as a truthful,
readable, performant early visual baseline and establish the smallest reusable
asset workflow that later visual-production work can extend.

## Requirements checklist

### Functional requirements

- [ ] The relevant screenshot contribution is integrated on current
      `develop` while preserving the original author's authorship and current
      website content.
- [x] Every visual retained in public content accurately supports its
      associated current product claim and remains readable on desktop and
      mobile.
- [x] Public images use bounded, optimized delivery that avoids unnecessary
      eager or duplicate theme-variant downloads.
- [x] Retained visuals have useful alternative text and render correctly in
      supported themes and responsive layouts.
- [x] A minimal reproducible programmatic asset catalog, source lifecycle,
      validation, and browser-review workflow exists for the accepted early
      visual baseline.
- [x] The workbench visual runtime is derived from a canonical Git-tracked
      application configuration through public `AgentApplication` UI-schema
      APIs, and the production action menu shows real plugin-provided actions
      in their declared order.
- [x] Message deletion and OpenAI native compaction create default-on
      pre-mutation session snapshots, and native compaction is available as an
      inclusive message-level “up to here” action.

### Non-functional requirements

- [x] Public visuals contain no fabricated product UI, credentials, private
      data, misleading platform framing, contradictory connection behavior, or
      planning placeholders.
- [x] Unreviewed capture candidates and review output remain ignored; reviewed,
      sanitized source masters remain outside `landing_page/public/`, and only
      optimized derivatives enter `landing_page/public/`.
- [x] Work proceeds through the approved Stage A and Stage B manual
      checkpoints; native capture work does not start without separate Stage C
      approval.
- [x] Automatic snapshots are not silently pruned or limited in this task;
      their full-session storage cost and manual deletion behavior are
      documented.

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
7. `landing_page/docs/visual-assets.md:1-875` — supported asset-author workflow
   for assets, programmatic builds, direct commands, lifecycle callbacks,
   captured sources, catalog commands, and verification.
8. `landing_page/docs/development/visual-content-and-screenshot-generation.md:1-681`
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
- The generation source owns a Git-tracked minimal configuration derived from
  the repository default config. `~/.crystal` supplies only the saved ChatGPT
  credential file; personal application configuration is not an input.
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
- an explicit live refresh command that uses the tracked minimal generation
  config plus a caller-supplied ChatGPT credential directory to produce an
  ignored candidate session;
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
- The approved Stage C2 follow-up authorizes bounded changes to shared
  frontend action ordering, `session-actions-app`, the OpenAI Responses native
  compaction plugins, application snapshot documentation, and their focused
  tests. If safe pre-mutation snapshots require a materially broader session
  transaction or persistence redesign, stop and ask before expanding scope.

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
  --agent codex-openai \
  --python "$HOME/.crystal/dev-cli-venv/bin/python"
```

Load the Git-tracked configuration named by the source manifest. Require an
explicit credential directory, force the selected request to use ChatGPT auth,
and fail rather than falling back to an API key. Do not load personal
application configuration or copy, print, persist, or report credentials.

Use a checked-in source manifest containing:

- a public repository URL and exact commit SHA;
- a bounded snapshot of one public bug issue;
- a realistic developer prompt containing only the task to perform;
- the tracked minimal application configuration, selected agent, required
  tools, and expected visible session shape.

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

Generate homepage sources without device/system chrome while preserving the
application context that makes each surface visibly a modal:

- chat actions: show the modal title and a useful readable set of action rows
  over the active coding-plan session;
- session settings: show the current settings modal and the controls needed to
  support the plugin-schema claim over the active session;
- snapshots: show the current snapshots modal using sanitized short
  identifiers over the active coding-plan session.

The crop geometry belongs to each asset's programmatic build so a later
replacement can choose a different framing without changing the runner or CLI.
Remove the system status bar, Dynamic Island, and hardware frame. Preserve the
correctly positioned application header, session content, session ID, bottom
action controls, composer, Append, and Send so the captured surface reads as a
modal inside the application.

Automated verification covers source dimensions, expected crop bounds,
light/dark outputs, no forbidden fixture text, asset budgets, website build,
and responsive browser contracts.

Manual checkpoint C2:

- judge whether each crop is large enough to read at the actual homepage card
  size;
- judge whether the three cards feel like coherent product proof without
  implying that the homepage is specifically about the mobile app;
- judge whether each modal remains visually grounded in a recognizable active
  session without device chrome.

#### Stage C2 follow-up — Canonical runtime UI and operation-backed snapshots

Replace the handwritten action/settings state in the native visual harness
with a canonical Git-tracked runtime configuration and UI fixture generated
through public `AgentApplication` APIs. Keep this as a first-class asset-source
lifecycle rather than starting a live HTTP server during Detox capture.

Add
`landing_page/visual_assets/runtime/mobile-workbench/config.json`, derived from
the repository default configuration but limited to one `codex-openai` agent
using `gpt-5.6-luna` with medium reasoning and the plugins that support the
current workbench proof. Include the OpenAI Responses provider UI needed by the
settings screenshot plus these application plugins:

- `session-actions-app`;
- `session-title-app`;
- `generate-title-app`;
- `summarize-range-app`;
- the OpenAI Responses native-compaction application plugin.

Omit unrelated authentication-menu, application-reload, MCP, cloud-agent,
session-list-only metadata, export, attachment, demonstration, alternate
provider, and native-history-rebuild plugins from this screenshot-specific
configuration. This does not change the production default configuration.

Generate an ignored candidate and explicitly promoted tracked
`mobile/crystal-lattice-control-rn/src/testing/fixtures/websiteRuntimeUi.json`
containing the sanitized session application UI schema, provider/session UI
schema, effective base settings, relevant overrides, contributing plugin and
action identifiers, action labels/icons/conditions/orders, and source config
and session-fixture hashes. The visual-asset check regenerates the local
contract and fails when the promoted fixture is stale. Detox consumes only the
promoted fixture and therefore does not need Python, plugin loading, a server,
credentials, or HTTP readiness during capture.

Use the generated fixture through the harness backend and open the production
`SessionActionsBar` from the real session header. Remove the custom
`ActionsMenuContent` screenshot path. Add a separate non-visual integration
test that starts the public HTTP application boundary with the canonical
configuration and verifies that the production frontend backend adapter
receives the expected session action and settings contracts.

Make these permanent product improvements:

- remove the legacy frontend-native `Delete range` action; message deletion is
  owned by `session-actions-app`, which remains enabled in the default config;
- preserve numeric action `order` from UI schema through frontend action
  definitions and stable-sort combined frontend-native and plugin actions,
  retaining declaration order for missing/equal values;
- assign explicit frontend-native action orders: Reload 0, Message limit 20,
  Agent switch 25, Settings 90, Plugins 91, Snapshots 92, and Debug events 100;
- apply the same ordering contract to shared mobile and desktop consumers;
- show the OpenAI compacted-transcript collapse/expand action only when the
  session contains compacted history.

Add a message-level OpenAI Responses application action labeled
`Compact native history up to here`. Map the selected visible message index to
a dedicated `message_index` input, normalize it to the existing exclusive
`end_index = message_index + 1`, and delegate to the current background
compaction path. Preserve the existing progress notification, cancellation,
retry, conflict detection, and commit behavior. The selected message is part
of the compacted prefix.

Create automatic pre-mutation snapshots with Option A behavior: enabled by
default and without automatic retention, pruning, or count limits.

- `session-actions-app` creates a snapshot after validating and normalizing a
  non-empty message deletion and immediately before persisting the mutation.
  Copy, fork, whole-session deletion, and no-op deletion do not create these
  snapshots.
- The OpenAI native-compaction background process creates a snapshot only
  after provider work succeeds, inside the existing commit lock, immediately
  before the reconciled compacted session is saved. Cancellation, provider
  failure, application shutdown/reload interruption, and commit conflict do
  not retain an automatic compaction snapshot.
- If a mutation save fails after a provisional snapshot is created, delete
  that snapshot before propagating the failure.
- Keep the implementation local to the two plugins and existing
  `AgentApplication` snapshot methods unless a third consumer or a concrete
  correctness problem justifies a shared commit helper.

Use precise, pre-state reasons such as:

- `Before deleting message [14]`;
- `Before deleting messages [18, 22, 25]`;
- `Before deleting messages [357:]`;
- `Before compacting conversation [:277]`.

Store structured metadata including `origin: automatic`, plugin ID, action ID,
normalized range or indices, and the compaction operation ID when applicable.
The current frontend displays the human-readable `reason`; metadata is retained
for future filtering, retention, and richer history UI.

Regenerate the snapshot visual with deterministic ranges that match the
reviewed coding-plan session. Show at least one automatic deletion snapshot,
one automatic compaction snapshot, and optionally one manual snapshot so the
visual communicates recoverable operation history rather than only manual
bookmarks.

Automated verification covers:

- removal of the legacy frontend delete action;
- stable ordering across frontend-native, application-plugin, and provider
  actions, including equal/missing order behavior;
- configuration-generated UI fixture provenance and stale-fixture detection;
- the real production action menu consuming generated plugin actions;
- inclusive compaction through the selected message;
- snapshot creation and restoration before successful message deletion;
- snapshot creation and restoration before successful native compaction;
- no retained automatic snapshot for no-op deletion, cancellation, provider
  failure, application interruption, or commit conflict;
- provisional snapshot cleanup when mutation persistence fails;
- application/plugin unit tests, public HTTP plus production frontend-adapter
  integration, mobile component/Detox coverage, asset checks, website build,
  and Playwright responsive/theme contracts.

Manual checkpoint C2 follow-up:

- judge whether the real action menu makes plugin-provided capabilities
  immediately visible without looking technically cluttered;
- judge whether the automatic snapshot reasons are understandable, precise,
  and visually more useful than the former manual-only fixture;
- judge whether the recaptured action, settings, and snapshot cards remain
  readable and truthful at desktop and phone website sizes.

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
- Decision: remove the legacy frontend-native delete-range action and let
  `session-actions-app` own message deletion.
- Decision: frontend-native and plugin-provided actions honor the existing
  numeric UI-schema `order` contract through a stable combined sort.
- Decision: add `Compact native history up to here` as an inclusive
  message-level action backed by the existing asynchronous native-compaction
  operation.
- Decision: automatic snapshots before message deletion and successful native
  compaction are enabled by default. This task adds no automatic retention,
  pruning, or count limit; users remove snapshots manually.
- Decision: the visual pipeline generates and promotes a reviewed
  `websiteRuntimeUi.json` from the canonical config and reviewed session.
  Detox does not start a live server; a separate automated HTTP/frontend
  adapter integration test covers that boundary.
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
- Add `application/python/docs/session-snapshots.md` as the canonical
  user-facing snapshot guide. Document manual and automatic snapshots,
  pre-mutation semantics, readonly selection and restore behavior, operations
  that currently create automatic snapshots, manual deletion, full-session
  storage cost, and the explicit absence of automatic pruning or limits.
  Route it from `application/python/docs/index.md` and the concise package
  README without duplicating the full explanation.
- Update `plugins/session-actions-app/README.md` with the plugin-owned
  automatic snapshot behavior for successful message deletion and examples of
  normalized reasons. Link to the canonical application snapshot guide for
  storage, restore, and retention behavior.
- Update `plugins/openai_responses/README.md` with the message-level
  compaction action, background lifecycle, successful-commit snapshot
  behavior, failure/cancellation exclusions, and example reasons. Link to the
  canonical application snapshot guide.
- Update `plugins/docs/ui-elements.md` with the supported numeric action-order
  contract, stable tie behavior, and a concrete application/message-action
  example.
- Update `plugins/docs/application-plugins.md` with a concise, reusable
  pre-mutation snapshot pattern using public `AgentApplication` methods,
  including lock placement and failure cleanup. Present this as an
  application-plugin capability rather than claiming that all actions are
  automatically snapshotted.
- Update the existing landing-page visual-asset consumer and development pages
  with the canonical runtime config, generated UI candidate/promotion
  lifecycle, provenance checks, and the reason Detox intentionally consumes a
  reviewed fixture while HTTP integration is verified separately.

### Task checklist

- [x] Confirm task-020 product/compatibility facts needed by retained visuals.
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
- [x] Implement the revised Stage C1 reviewed-session source.
- [x] Pass manual checkpoint C1.
- [x] Implement C2 unframed workbench captures.
- [x] Pass manual checkpoint C2.
- [x] Implement the approved C2 follow-up product action cleanup and ordering.
- [x] Add the native-compaction “up to here” message action.
- [x] Add default-on, unpruned automatic snapshots for successful message
      deletion and native compaction.
- [x] Add the canonical mobile-workbench config and generated/promoted runtime
      UI fixture lifecycle.
- [x] Update automatic snapshot, plugin action, and visual-runtime
      documentation.
- [x] Pass the C2 follow-up automated verification.
- [x] Pass the C2 follow-up manual visual checkpoint.
- [x] Implement and automatically verify C3 provider focus composites.
- [x] Pass manual checkpoint C3.
- [x] Implement and automatically verify C4 mobile-page hero.
- [x] Pass manual checkpoint C4.
- [x] Complete Stage C5 documentation, handoff, and final verification.
- [x] Record completion evidence and the task-160 handoff.

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
- The promoted runtime UI fixture is reproducibly generated from the canonical
  config and reviewed session through public application APIs, while a
  separate integration test verifies the live HTTP/frontend-adapter boundary.
- Restoring an automatic deletion or compaction snapshot recovers the exact
  pre-mutation session, and unsuccessful operations do not leave an automatic
  snapshot.

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

### August 27, 2026 — Stage C1 local workflow complete; hosted refresh blocked

- Commit `1a402724` preserves the prior native-capture implementation and the
  approved revised C1-C5 plan before Stage C1 execution.
- Added the `coding-plan` direct-command asset plus catalog-level
  `refresh-session` and `promote-session` workflows without changing the
  generic CLI or runner.
- Added the Starlette 1.4.0 source manifest and realistic model-facing prompt.
  The refresh helper creates an operating-system temporary sparse checkout,
  verifies revision/size/time budgets, uses the shared
  `TerminalApplication`/`AgentApplication` request path, sanitizes private and
  volatile data, validates tool activity, and removes the checkout on success
  or failure.
- Candidate output remains ignored and reviewed-fixture promotion remains a
  separate prepared mutation. No candidate or reviewed fixture currently
  exists.
- Added automated coverage for command parsing, sanitizer behavior,
  forbidden installation/source-write detection, the shared application
  request path with the deterministic echo provider, catalog compatibility,
  and complete existing public-asset checking.
- Verification passes:
  - three Python session-fixture tests;
  - fourteen Node visual-asset tests;
  - all eleven catalog check results and the existing 503,904-byte public
    derivative baseline;
  - `git diff --check`.
- The first hosted refresh stopped before ChatGPT. Copying the full personal
  config while redirecting `plugin_cache_dir` to a temporary directory caused
  `AgentApplication` plugin discovery to bootstrap every configured path
  plugin. That attempted dependency installation and then failed importing the
  OpenAI Responses bundle because the active development Python has
  `aiohttp 3.9.3`, which lacks the API expected by the cached/current plugin.
- The temporary plugin cache and Starlette checkout were removed. No candidate
  was produced. `pip check` passes afterward; the active environment remains
  on FastAPI 0.115.0, Starlette 0.38.6, and aiohttp 3.9.3.
- Continuing now requires a runtime-boundary decision not present in the
  approved plan. Recommendation: accept the already-installed Crystal Lattice
  bundled Python runtime and the existing `~/.crystal/cache/plugins` as
  explicit read-only refresh inputs, verify the cache is unchanged before and
  after generation, and continue to use the current worktree's application
  code plus isolated temporary workspace/session state. Do not retry until the
  user approves this additional runtime/cache input boundary.

### August 27, 2026 — Stage C1 ready for human checkpoint

- The user directed the refresh workflow to use the Python interpreter behind
  `crystal-lattice-cli-dev`:
  `~/.crystal/dev-cli-venv/bin/python`.
- Loading the complete personal plugin catalog remained unsuitable because
  source-plugin fingerprints can differ from cached revisions. The final
  implementation derives a minimal temporary config from the selected
  `codex-openai` agent:
  - OpenAI Responses provider and required provider extensions;
  - request-options feature;
  - the core-packaged read-only `FileReaderTool`;
  - no application plugins, MCP, shell execution, source-write tools, path
    plugin installation, or personal plugin-cache mutation.
- The model-facing session contains only the realistic Starlette developer
  request. Operational safety is enforced by the read-only tool set,
  temporary checkout, candidate validation, and source/promotion boundary
  rather than visible fixture instructions.
- The final hosted refresh completed in 66.9 seconds. Its temporary sparse
  checkout used 1,251,521 bytes and was removed after generation.
- The ignored candidate is
  `landing_page/artifacts/visual-assets/session-fixtures/coding-plan/candidate.json`.
  It is 85,959 bytes with SHA-256
  `49b1c50a12775d907d0c85bb84a958c42958b5c3607a9abc808fafc80cf2d092`.
- The candidate has 11 visible messages and 10 retained repository-inspection
  activities. Failed read attempts, checkout-log output, personal paths,
  usernames, email addresses, credentials, provider tokens, issue number, and
  fixture-generation language are absent. Long successful tool output is
  bounded for the reviewed fixture.
- The final assistant answer identifies the required keyword-only
  `thread_minimum_size` regression, proposes restoring the shared/default
  threshold without broader behavior changes, and specifies direct subclass
  constructor regression coverage.
- No reviewed fixture exists and `promote-session` has not been run.
- Automated verification passes:
  - three Python session-fixture tests;
  - fourteen Node visual-asset tests;
  - eleven complete catalog checks for the existing public derivative
    baseline;
  - `git diff --check`.
- Manual checkpoint C1 is ready for judgment of session credibility,
  concision, technical quality, and privacy. Promotion and C2 remain blocked
  until the user approves this candidate.

### August 27, 2026 — Stage C1 configuration made inspectable

- The user required the exact generation configuration to be minimal,
  Git-tracked, and directly inspectable instead of being derived from
  `~/.crystal/config.json` at runtime.
- Added
  `landing_page/visual_assets/session_sources/starlette-gzip-responder/config.json`
  using the repository default config as its baseline:
  - one `openai` provider with ChatGPT auth;
  - one `codex-openai` agent using `gpt-5.6-luna` with medium reasoning;
  - OpenAI Responses provider, auth, tools, reasoning, usage, verbosity,
    caching, and request-option support;
  - the core-packaged read-only `FileReaderTool`;
  - no additional agents, application plugins, MCP, shell, source-write tools,
    API keys, or personal paths.
- The manifest now names the tracked config. The refresh command no longer
  accepts a personal config path; `--config-dir` is used only to resolve the
  saved ChatGPT credential file.
- Provenance records the tracked config SHA-256 and the final candidate's
  config hash matches the file byte-for-byte.
- The user subsequently selected `gpt-5.6-luna` with medium reasoning for the
  tracked generation config. Regeneration evidence for that committed config
  supersedes the earlier `gpt-5.4-mini` candidate values above.
- No reviewed fixture exists and promotion remains blocked pending checkpoint
  C1 approval.

### August 27, 2026 — Stage C1 approved and promoted

- The user approved C1 with one requested configuration change:
  `gpt-5.6-luna` with medium reasoning.
- Commit `a6bd52fa` records the complete reproducible session-fixture workflow
  and the tracked configuration before the final hosted refresh.
- The refresh from that committed config completed in 43.3 seconds. The
  candidate contained five visible messages, four successful repository
  inspections, no failed tool results, and passed the privacy/internal-context
  scan.
- Final generation evidence:
  - config SHA-256:
    `bfad8038590c3403a15c6fc4ec3208fc92ad56a45c32195fbf162cc67e34f782`;
  - candidate SHA-256:
    `92f28a784f40a69e185462fea6acaef4962e685791c0f7e78ddeb8fb2755ead4`;
  - candidate size: 60,136 bytes;
  - sparse checkout size: 1,251,521 bytes.
- `promote-session coding-plan` copied the exact reviewed candidate to
  `mobile/crystal-lattice-control-rn/src/testing/fixtures/websiteCodingPlanSession.json`.
- Stage C2 is authorized.

### August 27, 2026 — Stage C2 ready for visual checkpoint

- The production native visual harness now loads the reviewed coding-plan
  fixture and captures three selectable workbench states in light and dark:
  session actions, snapshots, and session settings.
- Actions use the shared production `ActionsMenuContent` inside the production
  modal frame. Snapshots and settings use their production modal components.
  The reviewed session screen remains mounted underneath an opaque
  theme-colored capture backdrop, preventing transcript bleed through modal
  surfaces.
- One Detox invocation captures all six source PNGs on the iPhone 17 Pro
  simulator. The completed native run passed in both themes for all three
  states.
- The three assets now use captured-source lifecycles. Their reviewed source
  PNGs are the current native captures, without fixture IDs in the visible
  modal content.
- Added a reusable programmatic ImageMagick crop operation. Crop geometry stays
  in each asset definition:
  - actions: `1080x940+63+880`;
  - snapshots: `1080x1090+63+790`;
  - settings: `1080x1540+63+555`.
- Final WebP candidates and exact evidence:
  - actions light: 1000x851, 15,586 bytes,
    `3ee015d5691634fd6683445d74b224af450311e5737a5925b844f877a6d5494e`;
  - actions dark: 1000x851, 15,650 bytes,
    `98bd1b644b7a7c4d50c078ddc609807dfcc2bd899838a04186cd22b894da7098`;
  - snapshots light: 1000x1006, 29,164 bytes,
    `0b1c585f85b17d9d39f47ebd8d2a9a4a948c887955e7b9677efafbccbb1d3ce5`;
  - snapshots dark: 1000x1006, 30,760 bytes,
    `7b82ceb363137929a9bcf30fb76a6f35a192a36d8ffa10aa74c393c5e2089f92`;
  - settings light: 1000x1414, 46,040 bytes,
    `c3c6ae968d187110db307dc402515d4ad8bc90b47f78ccdab72c000e9bc9b92b`;
  - settings dark: 1000x1414, 49,116 bytes,
    `6a63da05ae6df37e57a2790f879411317aeba1a6257f26a974512248e5597282`.
- The homepage content dimensions and actions alt text now match the generated
  files. Public working-tree derivatives are updated but uncommitted.
- The screenshot gallery uses the themed raised surface instead of a hardcoded
  white image background, so letterbox space is correct in dark mode.
- The active-theme browser test now scrolls every lazy image into view instead
  of relying on the former page geometry. Its exact five-image totals are
  228,372 light bytes and 218,230 dark bytes.
- Automated verification passes:
  - mobile TypeScript typecheck;
  - iOS Detox build and six-state native capture;
  - fourteen visual-asset unit tests, including crop command composition;
  - complete eleven-result asset catalog check;
  - Astro production build;
  - all eleven Playwright desktop/phone and light/dark visual contracts;
  - `git diff --check`.
- Manual checkpoint C2 is ready. Judge readability at actual card size,
  coherence across the three cards, and whether the modal-only presentation
  communicates product capability without making the homepage feel
  mobile-specific.

### August 27, 2026 — Stage C2 application context restored

- The user clarified that C2 must omit only device/system chrome. The
  application header, session content, session ID, bottom actions, composer,
  Append, and Send must remain visible so each surface reads as an in-product
  modal.
- The harness now mirrors the application's safe-area structure, fixing the
  previously overlapped header. Detox waits for the modal fade before capture,
  and the temporary opaque capture backdrop was removed.
- All six sources were recaptured successfully. The final deterministic crop
  is `1206x2442+0+180`, beginning below the iOS status area and extending
  through the complete bottom controls. Edge trimming is disabled so light and
  dark variants retain identical geometry.
- The workbench gallery uses a tall `40/81` media aspect so the restored
  context remains readable at desktop and phone card widths. No simulated
  device border is added.
- Workbench WebPs use quality 76 and all six are 1000x2025:
  - actions light: 48,144 bytes,
    `7181d57fc191a9db9a4a2c3bc0d6b050fd43cffe536a9fbddcb247093b4bc97e`;
  - actions dark: 46,334 bytes,
    `c7fe783d25feec0fe7c0c3e676294d30073dfb49018f5aeb91c33962dd47a357`;
  - snapshots light: 49,008 bytes,
    `3d70bd7e9aee3c7aa040105990a0c2c97ce67e824210972a127891bc4981dcd1`;
  - snapshots dark: 48,974 bytes,
    `4de8fd37dbf462a7bf211806210898f62ed75feb19361be475dc60e489725b7a`;
  - settings light: 51,566 bytes,
    `7f5b368e90e9ed8b0e0afe67bab8e09261312754898d119911ba69ce26e382c5`;
  - settings dark: 54,866 bytes,
    `eeefe3afe32f9ac1a9fd426f2f588a7482bc088af38c84c3532f32b890b6cccf`.
- The five-image homepage totals are 286,300 bytes in light mode and 272,878
  bytes in dark mode, within the existing 300,000-byte per-theme budgets.
- Verification remains green after the correction:
  - mobile TypeScript typecheck;
  - iOS Detox build and six-state capture;
  - fourteen visual-asset unit tests;
  - complete eleven-result catalog check;
  - Astro production build;
  - all eleven Playwright desktop/phone light/dark contracts;
  - `git diff --check`.
- C2 remains uncommitted and awaits the revised visual checkpoint.

### August 28, 2026 — Stage C2 product follow-up approved

- The user approved the canonical runtime-UI fixture design, permanent action
  ordering correction, removal of the legacy frontend delete-range action,
  conditional compacted-transcript toggle, and message-level native
  compaction action.
- The user selected automatic snapshot Option A: message deletion and
  successful native compaction create snapshots by default, with no automatic
  pruning, retention limit, or count limit in this task.
- The approved follow-up remains planned and unimplemented. It must complete
  its automated contract/integration coverage and stop at the dedicated
  mobile visual checkpoint before C3 continues.

### August 28, 2026 — Stage C2 product follow-up ready for visual checkpoint

- Permanent product action improvements are implemented:
  - the legacy frontend-native `Delete range` action and modal were removed;
  - shared action definitions preserve optional numeric `order`;
  - the shared menu model stable-sorts frontend-native and plugin actions;
  - mobile and desktop propagate plugin order and use explicit native action
    orders;
  - the OpenAI compacted-transcript toggle is conditional on compacted session
    metadata.
- OpenAI native compaction now exposes `Compact native history up to here` as
  an application-owned message action. It maps the selected message index to
  the existing exclusive compaction boundary and keeps the background
  operation, progress, cancellation, retry, conflict, and commit behavior.
- Successful message deletion and successful native compaction now create
  default-on automatic pre-mutation snapshots. No-op deletion, cancellation,
  provider failure, application interruption, commit conflict, and failed
  persistence do not retain an automatic snapshot. This implementation adds
  no automatic pruning or count limit.
- Snapshot restore now preserves the live session-notification container.
  This prevents restoring a compaction snapshot from resurrecting an obsolete
  in-progress banner while still restoring messages and provider-native
  history.
- Added the canonical tracked runtime configuration at
  `landing_page/visual_assets/runtime/mobile-workbench/config.json`. It
  defines one `codex-openai` screenshot agent using `gpt-5.6-luna` with medium
  reasoning, the selected provider/application plugins, six focused real
  setting keys, and deterministic snapshot presentation data.
- Added `refresh-runtime-ui` and `promote-runtime-ui` asset commands. The
  generated and promoted
  `mobile/crystal-lattice-control-rn/src/testing/fixtures/websiteRuntimeUi.json`
  is 17,153 bytes with SHA-256
  `c3c83621d2e40c6d14816fe771a2642a3ff3efdb3cf31336e375492e3b286fcf`.
  `check mobile-workbench` regenerates and compares the fixture byte-for-byte.
- The native harness now consumes the promoted runtime fixture. The action
  capture opens the production `SessionActionsBar` from the real header;
  settings and snapshots consume generated real schema and deterministic
  operation-history data. Detox synchronization remains disabled because the
  active production screen owns intentional polling timers; readiness uses
  explicit semantic identifiers and visible content.
- Added a non-visual real-server integration that starts FastAPI from the
  canonical config and verifies the promoted action/settings contract through
  `FetchTransport` and `RestAgentBackend`.
- Updated the canonical application snapshot guide, plugin package READMEs,
  shared application-plugin and UI-element authoring docs, frontend SDK
  integration guide, and landing visual-asset consumer/development docs.
- Final reviewed public derivatives are all 1000x2025:
  - actions light: 38,372 bytes,
    `bef7d5cefa6680c6b386f20c22b0c65feef538ec66986c1ff43cbb036ff6644a`;
  - actions dark: 37,896 bytes,
    `9d476332506e8ec1c42849dbb216c1d394b8d9146599948caa6fb7966ef6aa21`;
  - snapshots light: 49,092 bytes,
    `31808b2f74ca0d60dd90955c0327b8d3d4bd57b3216d0fa6813679d244866c7a`;
  - snapshots dark: 50,496 bytes,
    `865b735fc75522a600503dd8bf607f0ab86feade82d69d50ca0469559fe43478`;
  - settings light: 48,866 bytes,
    `a831addcc2865c72b495d4c18f0f14a0f75a1821f1dd4ba2536d2bdc903c3e47`;
  - settings dark: 47,930 bytes,
    `86d7add2912ded1f843a9ce73f3ffb659225acf1b6272d6ab7d0922f02d35d3d`.
- Automated verification completed:
  - shared React Native action components: 9 tests;
  - frontend SDK: 313 unit tests;
  - canonical FastAPI/`RestAgentBackend` integration: 1 test;
  - mobile: TypeScript plus 119 Jest tests;
  - iOS Detox build and six-state native capture;
  - OpenAI native compaction: 38 focused tests;
  - core snapshot restore: 3 tests;
  - session-actions automatic snapshots: 3 focused tests;
  - visual asset JavaScript: 16 tests;
  - visual asset Python: 4 tests;
  - complete catalog: 12 results within budgets;
  - Astro build and all 11 responsive/theme Playwright contracts;
  - Python Black and Ruff;
  - documentation preparation and MkDocs build;
  - `git diff --check`.
- The complete pre-existing `session-actions-app` test file still has two
  unrelated compatibility failures: one assertion expects the older raw event
  list instead of the current event-store envelope, and whole-session deletion
  with a persisted unknown agent ID reaches the application lifecycle before
  deletion. The new automatic-snapshot tests pass and neither existing failure
  is changed by this follow-up.
- The C2 follow-up is uncommitted and stopped at the required mobile/browser
  visual checkpoint.

### August 28, 2026 — Stage C2 and product follow-up approved

- The user accepted the final desktop and phone, light and dark workbench
  versions.
- Manual checkpoint C2 and the dedicated C2 product-follow-up checkpoint are
  complete.
- Stage C3 remains unstarted. The next delivery step is to commit the accepted
  C2 implementation, documentation, task evidence, reviewed source masters,
  and public derivatives before implementing the separately reviewable
  provider focus composites.

### August 29, 2026 — Stage C3 ready for visual checkpoint

- Committed the accepted C2 state before starting C3:
  - `57a7653f Add ordered actions and automatic session snapshots`;
  - `49ae63be Generate canonical website workbench visuals`.
- The imported provider masters were already manually composited zoom images,
  so they could not serve as clean deterministic inputs. Replaced them through
  the package-owned Detox producer:
  - reasoning uses the production session-settings modal generated from the
    canonical runtime UI fixture;
  - usage/cost uses the production chat screen and message footer for the real
    reviewed Starlette coding-plan turn.
- The runtime UI fixture now retains:
  - the real provider message-footer schema;
  - a deterministic excerpt of the final reviewed assistant response;
  - the original turn usage metadata, including input `3,851`, estimated
    cached `200`, completion `1,558`, reasoning `1,100`, estimated cost
    `$0.013019`, and estimated turn `$0.013999`.
- Corrected the OpenAI Responses usage UI contract so API-backed turns keep
  `cost`/`turn` labels while ChatGPT-backed turns explicitly display
  `estimated cost`/`estimated turn`. This makes the visual and product
  behavior honest about API-price estimation.
- Added `focusCalloutPipeline(...)` as ordinary programmatic
  JavaScript/ImageMagick behavior. It:
  - uses one reviewed source for both base and focus crops;
  - fixes the crop origin to northwest;
  - exposes explicit per-asset `canvas`, `original`, and `callout` sections;
  - controls the original crop, dimensions, placement, border, and dimming
    independently from the final canvas;
  - extracts and scales the proof-bearing focus region;
  - controls the square callout dimensions, placement, border, and shadow per
    asset;
  - applies sRGB normalization, metadata stripping, and WebP encoding.
- After the first C3 review, revised both compositions so:
  - callouts have square corners;
  - the original screenshot is narrower than the final image;
  - the callout is wider than the original screenshot;
  - the canvas leaves visible space around the callout shadow;
  - each callout is placed above the corresponding original-sized source
    region using asset-specific vertical geometry.
- Replaced the old phone-silhouette/manual composites with current unframed
  light/dark provider cards:
  - reasoning light: 1000x1315, 32,054 bytes,
    `d8067aa8efca1115bb05d6cd53b66486222d0f548ae716fb812d048c0138648d`;
  - reasoning dark: 1000x1315, 31,050 bytes,
    `31511d829f1dc26151458a0089d1c3f076a8294b90e53d77fff54f288f6bc8ac`;
  - usage light: 940x1334, 53,148 bytes,
    `4e40df8d85f8425a1c922488dc3d154189af0653b9781d783632920129e91022`;
  - usage dark: 940x1334, 62,984 bytes,
    `90980155399d4850839deb7eb46bcafba9a11260d14afdc447a940b59b2bc5e5`.
- Updated authored alt text and exact active-theme byte contracts. The complete
  catalog now validates 12 results totaling 544,396 bytes.
- Automated verification completed:
  - 17 visual-asset JavaScript tests;
  - runtime-fixture Python test;
  - 31 OpenAI Responses usage-extension tests;
  - mobile TypeScript and all 119 Jest tests;
  - final eight-state iOS Detox build/capture;
  - real FastAPI/`FetchTransport`/`RestAgentBackend` integration;
  - complete visual catalog check;
  - Astro build and all 11 responsive/theme Playwright contracts;
  - Black, Ruff, and `git diff --check`.
- Stage C3 remains uncommitted and is stopped at the required manual visual
  checkpoint. Stage C4 has not started.

### August 29, 2026 — Stage C3 approved

- The user approved the revised provider focus composites with square
  callouts, reduced contextual screenshots, wider focus panels, explicit
  shadow clearance, and asset-specific vertical placement.
- Manual checkpoint C3 is complete.
- Stage C4 remains unstarted until the accepted C3 implementation, tests,
  documentation, source masters, public derivatives, and task evidence are
  committed.

### August 29, 2026 — Stage C4 ready for visual checkpoint

- Committed the accepted C3 provider focus composites as:
  - `a37f2d3d Add deterministic provider focus visuals`.
- Added the canonical `mobile-active-session` asset with light/dark sources
  captured by the existing production-screen Detox producer.
- Extended the generated runtime UI fixture with a deterministic mobile-hero
  transcript derived from the reviewed Starlette coding-plan session:
  - the complete realistic user request is preserved;
  - the assistant presentation is an exact bounded excerpt beginning with
    `Focused backwards-compatible fix` and showing the concrete
    `thread_minimum_size: int = 128 * 1024` recommendation;
  - duplicated reasoning metadata is omitted only from this presentation
    fixture so the beginning of the user request and concrete result fit in one
    initial viewport.
- The native source uses the real production `SessionChatScreen` and
  `MessageBubble` components. It retains the readable
  `website-coding-plan` session ID, message actions, status area, composer,
  Append, and Send controls.
- Added stable production message-bubble test identifiers and extended the
  native visual test to ten light/dark states. The normal catalog `capture`
  command now completes successfully.
- Added a direct-section YAML media binding so a catalog asset can own a
  section-level image such as the mobile hero without inventing a single-item
  gallery. Added focused automated coverage for that binding.
- Added the active-session image to the mobile page through its authored YAML.
  The reviewed source remains an unframed native capture; the mobile page adds
  a generic frame entirely through CSS, including clipping, border, radius,
  and shadow.
- Published optimized derivatives:
  - light: 1000x2025, 71,336 bytes,
    `ee0f25d7196cfe67764b249eaade1066920bfe95c0f1db28c2bab28bd8626d9a`;
  - dark: 1000x2025, 66,266 bytes,
    `e07eb780380100e888292ca83f8abccb7d29df820aee6e5dcd83d5189f92d260`.
- Selected WebP quality independently by theme after reviewing comparison
  images at the actual 280-pixel website width. The complete active-theme
  assets remain below the existing 300 KB budget:
  - light: 292,868 bytes;
  - dark: 296,622 bytes.
- Automated verification completed:
  - 18 visual-asset JavaScript tests;
  - deterministic runtime-fixture Python test;
  - mobile TypeScript and all 119 Jest tests;
  - successful ten-state iOS Detox build/capture through the catalog;
  - real FastAPI/`FetchTransport`/`RestAgentBackend` integration;
  - complete 14-result visual catalog totaling 689,926 bytes;
  - Astro build and all 12 responsive/theme Playwright contracts;
  - CSS phone-frame, eager image, active-theme, dimensions, alt-text, and
    broken-image checks;
  - Black, Ruff, and `git diff --check`.
- The initial Stage C4 candidate is committed as a separate baseline before
  the approved footer, identity, and status-row follow-up. Manual checkpoint
  C4 remains open. Stage C5 has not started.

### August 29, 2026 — Stage C4 footer and identity follow-up

- Committed the initial deterministic mobile hero separately as:
  - `a3066ac6 Add deterministic mobile session hero`.
- Added backward-compatible OpenAI Responses display controls:
  - formally declared the existing `show_usage` master switch;
  - added `usage_message_footer_fields` as an optional supported-field filter;
  - added `show_usage_status_total` for the cumulative status-bar total;
  - added `show_reasoning_context_footer` to hide only the reasoning-context
    footer while preserving reasoning behavior and metadata.
- Existing configurations retain the complete usage footer and status total.
  The compact mobile-hero profile selects `turn_cost`, `turn_input`, and
  `turn_output`; keeps `Total`; and hides reasoning context, estimated cached
  tokens, and auth mode.
- The compact usage values are cumulative for the complete tool-using user
  turn:
  - turn input: 4,051;
  - turn output: 1,688;
  - estimated turn: $0.013999.
- Kept the accepted provider-usage proof unchanged by generating separate full
  and compact UI-schema projections from the same real plugin configuration.
  The provider proof retains all 17 footer definitions; the mobile hero
  contains only the auth-conditioned turn-cost definitions, turn input, turn
  output, and the `Total` status element.
- Replaced the human-readable fixture session ID with the stable manifest-owned
  UUID `dc4efaec-9451-5981-a721-175a079860fb`.
- Added manifest-owned `agent_id: codex-openai` to the reviewed session summary
  so the status row follows the same metadata path as real application
  sessions.
- The mobile chat header now renders the existing session presentation title,
  with the established presentation fallback behavior, while session details
  and the status row retain the full UUID.
- The final native proof therefore shows:
  - header: `Plan a Starlette compatibility fix`;
  - compact assistant footer: estimated turn, turn input, and turn output;
  - status row: Agent, UUID Session, and Total.
- Updated OpenAI Responses user documentation for the new keys and stable
  footer-field identifiers.
- Published revised derivatives:
  - light: 1000x2025, 77,472 bytes,
    `70ec95efaf1f06fd6972a414b2b9e39cf07d2fcb9f588d1d22cc4cc142885a2b`;
  - dark: 1000x2025, 67,562 bytes,
    `ddf538e6d0ec69aaba184ce8f080020a8d79dabd60663275be0515dc758f9ac3`.
- Theme budgets remain below the existing 300 KB limit:
  - light: 299,004 bytes;
  - dark: 297,918 bytes.
- Automated verification completed:
  - 120 focused OpenAI usage/reasoning plugin tests;
  - Black and Ruff for changed Python plugin and fixture code;
  - four deterministic session/runtime fixture tests;
  - 18 visual-asset JavaScript tests;
  - mobile TypeScript and all 119 Jest tests;
  - 314 frontend SDK tests;
  - real FastAPI/`FetchTransport`/`RestAgentBackend` integration;
  - successful ten-state iOS Detox build/capture with title assertion;
  - complete 14-result visual catalog totaling 698,671 bytes;
  - Astro build and all 12 responsive/theme Playwright tests;
  - `git diff --check`.
- The revised Stage C4 candidate remains uncommitted and is stopped at the
  required manual visual checkpoint. Stage C5 has not started.

### August 29, 2026 — Stage C4 consecutive follow-up exchange

- The user approved replacing the non-consecutive `[0]` user / `[4]`
  assistant hero projection with a real consecutive follow-up exchange after
  the repository investigation.
- The reviewed session source will add a tracked, realistic engineering
  follow-up asking whether the compatibility fix should duplicate the existing
  default or share a module-level constant.
- Session refresh will send that follow-up through the same live session after
  the initial tool-using investigation completes.
- The reviewed fixture will retain the complete investigation and follow-up
  transcript. Candidate validation will require:
  - repository-inspection tool activity in the initial turn;
  - a later consecutive user/assistant follow-up pair;
  - no follow-up tool call;
  - reasoning metadata on the follow-up response.
- The provider usage/cost proof will remain sourced from the first completed
  investigation response so accepted Stage C3 content does not change.
- The mobile hero will use the last user and last completed assistant messages,
  preserve the follow-up reasoning display, and keep the compact usage and
  Agent/UUID/Total status configuration.
- This follow-up remains part of the uncommitted revised Stage C4 change. A new
  manual visual checkpoint is required before Stage C4 can be marked complete
  or Stage C5 begins.

### August 29, 2026 — Stage C4 consecutive exchange implemented

- Added tracked `follow-up-prompt.md` and extended the reviewed-session refresh
  workflow to send a real second request through `TerminalApplication`.
- The follow-up refresh extends the first five manually approved investigation
  messages instead of regenerating them:
  - the runtime is seeded from the reviewed fixture;
  - `seed_message_count: 5` prevents repeated refreshes from accumulating
    additional follow-up turns;
  - the candidate builder verifies the semantic runtime prefix and restores
    the exact reviewed message objects before appending the new pair.
- OpenAI provider reconstruction intentionally collapses the empty assistant
  tool-call carrier from the runtime-visible prefix. Validation therefore
  compares the semantic `user → tool → tool → assistant` prefix while the
  promoted fixture preserves the original five-message sequence including the
  carrier.
- The promoted reviewed fixture contains seven messages:
  - `[0]` through `[4]` are byte-for-byte identical to the accepted
    investigation fixture;
  - `[5]` is the real engineering follow-up;
  - `[6]` is one no-tool assistant response with reasoning metadata.
- The full reviewed `[6]` response remains in the fixture. The mobile hero uses
  the standard `metadata.display` contract to show an exact bounded excerpt:
  the recommendation and backwards-compatibility rationale. This keeps both
  consecutive message headers visible while preserving the complete source
  response for other consumers.
- The accepted Stage C3 provider usage proof remains sourced from `[4]` with
  its existing text and `$0.013019` response cost.
- The final hero displays:
  - `[5] User` with the follow-up question;
  - `[6] Assistant`;
  - `Reasoning: Deciding on shared default constant`;
  - the direct-default recommendation and compatibility rationale;
  - estimated turn `$0.003598`, turn input `2,236`, turn output `257`;
  - Agent `codex-openai`;
  - UUID Session `dc4efaec-9451-5981-a721-175a079860fb`;
  - cumulative Total `$0.018577`.
- Final derivatives:
  - light: 1000x2025, 78,018 bytes,
    `55a4f00c51b57fc355059923a26eab75f96330850b62b70c2f0c48b6be3a4c84`;
  - dark: 1000x2025, 68,378 bytes,
    `ce0aa2813b683d32068dc03a2b64b146be23ab52269d3cbc929700c357b05ff8`.
- Theme budgets remain below the existing 300 KB limit:
  - light: 299,550 bytes;
  - dark: 298,734 bytes.
- Final automated verification:
  - six session-fixture tests, including reviewed-prefix preservation and
    follow-up shape/reasoning validation;
  - one deterministic runtime-fixture test;
  - 18 visual-asset JavaScript tests;
  - 120 OpenAI usage/reasoning plugin tests;
  - mobile TypeScript and all 119 Jest tests;
  - 314 frontend SDK tests;
  - real FastAPI/`FetchTransport`/`RestAgentBackend` integration;
  - successful ten-state iOS Detox build/capture;
  - complete 14-result visual catalog totaling 707,738 bytes;
  - Astro build and all 12 responsive/theme Playwright tests;
  - Black, Ruff, and `git diff --check`.
- The implementation remains unstaged and is stopped at the revised manual C4
  checkpoint. Stage C5 has not started.

### August 30, 2026 — Stage C4 approved

- The user approved the consecutive follow-up mobile hero in both light and
  dark themes at desktop and phone website widths.
- Manual checkpoint C4 is complete.
- The accepted implementation, source masters, public derivatives, runtime and
  reviewed-session fixtures, plugin display controls, tests, and task evidence
  are ready to be committed together before Stage C5 begins.

### August 30, 2026 — Stage C5 complete

- Committed the accepted Stage C4 implementation as:
  - `a6c5fc28 Complete mobile session hero follow-up`.
- Updated the standalone visual-asset consumer guide with:
  - all current catalog commands;
  - exact reviewed-session refresh and promotion commands;
  - canonical runtime UI refresh;
  - focus-callout authoring;
  - shared Detox capture;
  - unframed source and CSS mobile-frame boundaries;
  - freshness-trigger and later retain/replace guidance.
- Updated the development architecture page with the reviewed-session producer,
  semantic seed-prefix validation, runtime UI projections, focus composition,
  unframed native capture, CSS framing, and Python fixture-test boundaries.
- Completed the retained task-025 evidence package:
  - refreshed accessibility and alt-text review for all six proof assets;
  - current performance and active-theme budgets;
  - per-asset source revisions, manifests, decisions, and freshness guidance;
  - machine-readable `completion-manifest.json` containing fixture commands,
    source/public paths, hashes, budgets, verification, and the task-160
    decision boundary.
- Updated task 160 with the exact provisional assets, source manifest,
  supporting fixtures, capture and promotion commands, freshness triggers, and
  the requirement to explicitly retain, replace, or remove every task-025
  asset after task 150 supplies approved page briefs.
- Task 020 remains an unapproved Draft and was not marked complete. The facts
  required by the retained visuals were verified directly against the owning
  application, plugin, frontend, and production-screen boundaries.
- Final code-state verification completed before the Stage C4 commit:
  - 120 OpenAI provider display tests;
  - mobile TypeScript and all 119 Jest tests;
  - 314 frontend SDK tests;
  - real FastAPI/frontend adapter integration;
  - successful ten-state Detox build/capture;
  - complete catalog, Astro build, Playwright, Black, Ruff, and diff checks.
- Post-documentation verification:
  - 18 visual-asset JavaScript tests;
  - seven Python session/runtime fixture tests;
  - 14-result catalog check totaling 707,738 bytes;
  - Astro build;
  - all 12 responsive/theme Playwright tests;
  - JSON, CSV, and `git diff --check`.
- The implementation is complete on
  `review/CL-291-landing-page-screenshots`. The first functional requirement
  and parent-task checkbox remain open because this review branch has not been
  merged into `develop`; merging is outside the current branch-local
  implementation step.