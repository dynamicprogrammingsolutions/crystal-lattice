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
3. `tasks/20260825-crystal-lattice-product-positioning-and-website/025-integrate-current-visual-baseline-and-bootstrap-asset-pipeline.md:1-241`
   plus its executable asset catalog, reviewed source masters, asset review,
   source lifecycle, validation/optimization workflow, accepted public
   baseline, and completion evidence. Reuse rather than reconstruct its
   technical foundation.
4. `landing_page/AGENTS.md:41-104` — claim, source, research/privacy, visual, and
   verification boundaries.
5. `landing_page/docs/development/specifications/product-website-content/content-spec.md:238-274`
   — proof and progressive-revision target.
6. `landing_page/docs/development/research/visual-communication-and-reproducible-assets.md:1-268`
   — retained visual hypotheses, reproducible asset-pipeline requirements,
   automation boundaries, review, and freshness rules.
7. `landing_page/docs/development/content-system.md:79-97` and
   `landing_page/docs/development/content-system.md:138-161` — current public
   asset and build/verification behavior.
8. `landing_page/docs/visual-asset-framework.md:1-579` — supported framework
   usage for assets, pipelines, commands, lifecycle callbacks, custom rules,
   and prepared publication.
9. `landing_page/docs/visual-assets.md:1-772` — concrete image, native-capture,
   reviewed-session, runtime-fixture, derivative, and website-presentation
   processing workflows.
10. `landing_page/docs/development/visual-content-and-screenshot-generation.md:1-690`
   — framework construction, dispatch, contexts, selection, prepared mutation,
   shared services, testing, and extension invariants.
11. `mobile/crystal-lattice-control-rn/AGENTS.md:1-253`,
   `mobile/crystal-lattice-control-rn/docs/development/index.md:1-3`,
   `desktop/crystal-lattice-control-desktop-rn/docs/development/index.md:1-5`,
   and
   `desktop/crystal-lattice-control-desktop-rn/docs/development/native-ui-testing.md:1-23`
   — package-specific mobile rules and desktop development/native-test routes.
   Follow the focused Detox, XCUITest, connection, or desktop convention page
   selected by the approved visual brief and executable asset catalog.

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

## Task-025 provisional baseline handoff

Task 025 completed an accepted early release-safe baseline on August 30, 2026.
The exact retained evidence is:

```text
landing_page/research/025-current-visual-baseline-and-asset-pipeline/
├── accessibility-and-alt-text-review.md
├── asset-review.csv
├── completion-manifest.json
└── performance-baseline.json
```

The completion manifest is the compact machine-readable handoff for current
source paths, public dimensions, byte sizes, hashes, capture commands,
freshness triggers, verification counts, and source revisions.

### Supporting fixtures

| Fixture | Tracked source | Refresh and promotion |
|---|---|---|
| Reviewed coding plan | `landing_page/visual_assets/session_sources/starlette-gzip-responder/manifest.json` plus its tracked config and prompts | `cd landing_page && yarn visual-assets refresh-session coding-plan --config-dir "$HOME/.crystal" --agent codex-openai --python "$HOME/.crystal/dev-cli-venv/bin/python"`; review the ignored candidate and provenance; then `yarn visual-assets promote-session coding-plan` |
| Canonical mobile workbench UI | `landing_page/visual_assets/runtime/mobile-workbench/config.json` plus the reviewed coding-plan fixture | `cd landing_page && yarn visual-assets refresh-runtime-ui mobile-workbench --python "$HOME/.crystal/dev-cli-venv/bin/python"`; review the ignored candidate; then `yarn visual-assets promote-runtime-ui mobile-workbench` |

Live model access is used only to refresh the reviewed coding-session
candidate. Routine Detox capture, catalog checking, website building, and
browser verification use tracked reviewed fixtures.

### Provisional proof assets

| Asset | Current proof | Reviewed sources and build | Freshness triggers |
|---|---|---|---|
| `provider-reasoning` | Reasoning-effort and verbosity controls | `landing_page/visual_assets/sources/provider-reasoning-{light,dark}.png`; programmatic contextual screenshot plus square-corner focus callout | Provider settings UI, reasoning/verbosity schema, or mobile settings presentation |
| `provider-usage-cost` | Input, cache, completion, reasoning-token, duration, and estimated-cost visibility | `landing_page/visual_assets/sources/provider-usage-cost-{light,dark}.png`; programmatic contextual screenshot plus square-corner focus callout | Message-footer presentation or provider usage/cost schema |
| `chat-actions-workbench` | Ordered real plugin-provided session and message actions | `landing_page/visual_assets/sources/chat-actions-workbench-{light,dark}.png`; unframed native crop | Session action menu, application action contract, ordering, or mobile presentation |
| `session-snapshots-workbench` | Automatic pre-compaction and pre-deletion snapshots plus Select, Restore, and Delete | `landing_page/visual_assets/sources/session-snapshots-workbench-{light,dark}.png`; unframed native crop | Snapshot actions, descriptions, dialog, or contract |
| `session-settings-plugins` | Plugin-provided model and provider settings | `landing_page/visual_assets/sources/session-settings-plugins-{light,dark}.png`; unframed native crop | Session settings UI, plugin UI schema, or provider options |
| `mobile-active-session` | Consecutive user/assistant coding follow-up with reasoning, usage, cost, agent, UUID session, total, and composer | `landing_page/visual_assets/sources/mobile-active-session-{light,dark}.png`; unframed native crop; generic phone frame exists only in mobile-page CSS | Mobile chat/header/composer/navigation, reviewed coding session, or mobile-page hero layout |

All six image assets use one package-owned Detox producer:

```bash
cd landing_page
yarn visual-assets capture \
  provider-reasoning \
  provider-usage-cost \
  chat-actions-workbench \
  session-snapshots-workbench \
  session-settings-plugins \
  mobile-active-session
```

Candidate capture, reviewed-source promotion, public derivative update, and
verification remain separate:

```bash
yarn visual-assets promote-source <asset-id>
yarn visual-assets update <asset-id>
yarn visual-assets check <asset-id>
yarn visual-assets:check
```

### Retain, replace, or remove boundary

- These six assets are approved current proof for the early release website.
- They remain provisional for this task. Do not carry them into the final
  visual set merely because they already exist.
- After task 150 supplies approved page briefs and its claim/proof matrix,
  record an explicit retain, replace, or remove decision for every task-025
  asset.
- Retained assets must be recaptured when their configured freshness triggers
  are relevant to the approved page claim.
- A replaced asset should reuse the catalog, fixture, capture, promotion,
  validation, and browser-review foundation where suitable; it does not need
  to preserve the current crop, callout, or page placement.
- The omitted diagrams, web-search proof, caching proof, session list, and
  attachment proof remain candidate gaps rather than implicit requirements.
  Add them only when an approved brief requires the corresponding proof.

## Expected outputs

Retained visual package:

```text
landing_page/research/160-visual-proof-and-reproducible-assets/
├── capture-state-manifest.json
├── asset-review.csv
├── accessibility-and-alt-text-review.md
└── completion-manifest.json
```

Implementation outputs:

- reuse or extension of the task-025 executable asset catalog, reviewed source
  lifecycle, validation, optimization, and browser-capture workflow;
- capture scripts, fixtures, demo plugins, and tests in their owning packages;
- approved optimized files under `landing_page/public/`;
- updates to `landing_page/docs/visual-asset-framework.md` for supported
  framework usage;
- updates to `landing_page/docs/visual-assets.md` for concrete processing
  pipelines and operational workflows;
- `landing_page/docs/development/visual-content-and-screenshot-generation.md`
  for current implementation and architecture;
- updates to `landing_page/docs/development/content-system.md` for implemented
  asset/content behavior;
- exact asset handoff to
  `tasks/20260825-crystal-lattice-product-positioning-and-website/170-validated-website-release-and-product-integration.md`.

Disposable output:

- `landing_page/artifacts/visual-assets/` for landing-side candidates, reports,
  previews, and browser captures, plus owning-package ignored output for native
  drafts, recordings, frames, and source captures.

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
