# Establish Production And Staging Website Channels

Restore a deployable production homepage from the exact website revision
immediately before the Desktop-download homepage restructuring, add the current
Getting Started section without its empty visual placeholders, and establish a
separate public no-index staging site for continued homepage and compatibility
work. Build and deploy both variants independently on every relevant push.

## Requirements checklist

- [x] Production uses commit `d3fe28a62ccdf82451e8273dc30245ca9075f0dd`
      as its exact homepage baseline. This is the parent immediately before
      `89883b925dee2ef071526ef37eef1ae062e863f6` added the new feature showcase
      and the six-step Getting Started structure containing **Download Crystal
      Lattice Desktop**.
- [x] The production homepage preserves the `d3fe28a6` sections, order, copy,
      links, and image-backed content except for changes explicitly required
      to add the current Getting Started section or separately approved during
      contextual review.
- [x] Production adds the current six-step Getting Started section with current
      installer commands, maintained Desktop release metadata/download, current
      platform availability, mobile availability, and connection methods.
- [x] Production Getting Started omits `media` and other empty visual
      placeholder fields. It renders no **Planned visual** panel, missing-image
      box, review-status label, or staging-only placeholder.
- [x] Adding Getting Started does not silently remove or rewrite the historical
      hero installer, **Computer to phone**, bridge, compatibility, provider,
      plugin, SDK, workbench, or other `d3fe28a6` sections. Any duplicate or
      contradictory path is shown in the first local production candidate and
      changed only after explicit human review.
- [x] The in-progress current homepage and later task `019`/`030` work live in
      a separate staging content location and do not overwrite the maintained
      production homepage source.
- [x] Production and staging share maintained components, layouts, styles,
      common pages, and release metadata where practical, but have explicit
      variant-owned homepage content and build outputs.
- [x] The default manual/CI landing build is the production variant. Staging
      requires an explicit variant selection.
- [x] Production and staging build to separate directories and can be previewed
      simultaneously without copying or renaming one variant over the other.
- [x] Staging is public at `staging.crystallattice.dev`, has a visible staging
      identity, and includes HTML `noindex, nofollow`, a disallowing
      `robots.txt`, and a CloudFront `X-Robots-Tag` response header.
- [x] Staging does not run production analytics or pollute production website
      metrics.
- [x] No staging-only candidate image, fixture, review marker, or draft content
      is included in the production build.
- [x] Both variants reject broken image references. Staging may render explicit
      work-in-progress placeholders, but it may not render missing image files.
- [x] Production retains ordinary indexable robot behavior and contains no
      staging marker or staging response header.
- [x] A separate private S3 bucket, CloudFront distribution, Origin Access
      Control, ACM certificate, Route 53 records, response-header policy, and
      scoped deployment role serve the staging site.
- [x] Staging infrastructure is isolated from the production static-site stack
      so staging creation, update, invalidation, or teardown cannot delete or
      replace production resources.
- [x] The existing Ireland EC2 server is not used for static staging hosting
      unless read-only AWS/DNS discovery proves an approved existing ownership
      constraint that requires a new decision.
- [x] Every relevant push to `main` independently builds and attempts to deploy
      both landing variants. A staging build/deploy failure is reported but
      does not cause staging output to be deployed to production or invalidate
      the production distribution.
- [x] Production and staging deployment jobs use separate artifact paths,
      buckets, distributions, GitHub environments, and least-privilege OIDC
      roles.
- [x] Production deployment continues to deploy the documentation site through
      its current production path; this task does not create a staging docs
      site.
- [x] Local and public verification covers content selection, placeholders,
      image integrity, download links, robots behavior, analytics exclusion,
      responsive layout, accessibility, CloudFront headers, DNS/TLS, cache
      invalidation, and artifact separation.
- [x] AWS, Route 53, ACM, IAM, GitHub-environment, workflow publication, and
      production deployment changes require their explicit human checkpoints.
- [x] Tasks `018`, `019`, `030`, and waitlist task `020` record their
      historical/paused ownership behind this task and identify exact
      resumption or handoff points.

## Scope and ownership

This task owns:

- production/staging landing-page source separation;
- the restored production homepage variant;
- the staging homepage variant boundary;
- variant build, preview, content, robots, and analytics behavior;
- separate staging AWS static hosting;
- separate staging GitHub deployment identity;
- dual landing build/deployment workflow;
- local and public verification for both website channels.

This task does not own:

- redesigning the new homepage;
- producing missing task `019` screenshots;
- implementing the compatibility tables from task `030`;
- implementing the waitlist backend or form;
- changing current download artifacts or release metadata;
- changing provider, plugin, Desktop, mobile, CLI, bridge, or agent behavior;
- using the Ireland server as a replacement deployment platform;
- repository visibility or unrelated documentation-site restructuring.

## Approved historical boundary

Git history identifies:

- production baseline:
  `d3fe28a62ccdf82451e8273dc30245ca9075f0dd`
  (**Prepare homepage download flow**, September 30, 2026);
- restructuring commit:
  `89883b925dee2ef071526ef37eef1ae062e863f6`
  (**Build homepage structure**, October 1, 2026).

Commit `89883b92` simultaneously:

- added the new feature showcase;
- added the `gettingStarted` section and renderer;
- added the **Download Crystal Lattice Desktop** step;
- moved installation out of the hero;
- removed the prior **Computer to phone** action guide;
- changed hero/final actions to `#getting-started`.

Production is not the complete `89883b92` result. It is the exact
`d3fe28a6` homepage plus the current Getting Started section, with empty media
placeholders omitted.

## Requirement question

The exact baseline-plus-addition candidate must be rendered before resolving
duplication:

- `d3fe28a6` has an installation chooser in the hero;
- current Getting Started has installation again as step 1;
- `d3fe28a6` has a **Computer to phone** action guide;
- current Getting Started includes workspace startup and mobile connection.

Recommendation: first produce the literal baseline-plus-Getting-Started
candidate. At the local production-content checkpoint, decide whether to keep
the duplication temporarily or approve the smallest removal/link adjustment.
Do not infer permission to remove historical sections from the request to add
Getting Started.

## Paused work and resumption boundaries

### Visual/product evidence task `018`

Retain completed Plugin, Transparency, Vibe, popup, icon, capture-pipeline, and
product evidence. Do not resume its older homepage-layout/image-batch plan.
Task `019` owns future homepage selection and visual integration after this
production/staging task. Any remaining `018` checklist state is historical
bookkeeping unless task `019` explicitly consumes it.

### Homepage task `019`

Paused after H1 Brief and Terminology approval.

Retained decisions:

- category direction: application for configurable AI coding agents;
- use **configured agent**, not profile;
- material differentiators: harness composition, provider-native fidelity,
  and application-level plugin effects;
- accepted recognizable wording for Codex-oriented, Claude-compatible,
  Gemini-oriented, and other harnesses.

Resume after:

- production and staging source/build separation is complete;
- both local variants pass their human checkpoint;
- the staging deployment path is available or has an explicitly approved
  deferred remote step.

Resume at H2: rewrite/select the complete opening copy, then H3 visual plan
and H4 image shortlist.

### Compatibility task `030`

Paused after:

- focused post-baseline source refresh;
- accepted current-source changes for Anthropic context management, Codex
  unified exec, Claude background compaction, and three additional plugins;
- generation of a complete internal evidence projection.

The complete projection is not the public website design.

Approved future public shape:

- one focused **Harnesses** table;
- one focused **Providers** table;
- one focused **Plugins and application features** table;
- selected canonical rows only;
- check/cross/conditional visual states with accessible text;
- baseline API behavior collapsed rather than repeated as individual
  reasoning/tool/caching/cost columns;
- full evidence retained internally.

Resume after this task at the public canonicalization checkpoint, before any
compatibility route/component implementation.

### Waitlist task `020`

The backend/form plan remains independently approved, but all implementation,
website integration, and publication work is paused while this highest-priority
task is active.

Resume website integration only after:

- production/staging channels are established;
- task `019` supplies the later accepted staging homepage;
- the target publication channel and production content update are reviewed.

This task must preserve the future ability for waitlist publication to deploy
production and staging deliberately without mixing their endpoint/configuration
variables.

## Proposed repository structure

```text
landing_page/
├── sites/
│   ├── production/
│   │   ├── content/pages/home.yaml
│   │   ├── public/robots.txt
│   │   └── site.json
│   └── staging/
│       ├── content/pages/home.yaml
│       ├── public/robots.txt
│       └── site.json
├── src/
│   ├── components/
│   ├── layouts/
│   ├── section-system/
│   └── content/
│       ├── pages/
│       └── releases/
├── public/
├── dist/
│   ├── production/
│   └── staging/
└── ...
```

The variant loader first checks `sites/<variant>/content/pages/`, then falls
back to shared `src/content/pages/`. Only the homepage initially requires two
sources.

Shared `public/` contains only assets approved for both channels. Staging-only
candidate assets use the staging-owned public/candidate lifecycle and cannot
be resolved by a production build.

## Staging indexing and presentation

Every staging page must include:

```html
<meta name="robots" content="noindex, nofollow, noarchive, nosnippet">
<meta name="googlebot" content="noindex, nofollow, noarchive, nosnippet">
```

Staging `robots.txt`:

```text
User-agent: *
Disallow: /
```

CloudFront adds:

```text
X-Robots-Tag: noindex, nofollow, noarchive, nosnippet
```

Staging remains public and is not a confidentiality boundary. It must contain
no private data, credentials, personal fixtures, account diagnostics, or
unreleased secrets.

## AWS and CI direction

Use a separate static staging stack:

```text
staging.crystallattice.dev
  -> Route 53 A/AAAA
  -> staging-only CloudFront distribution
  -> staging-only Origin Access Control
  -> staging-only private S3 bucket
```

CloudFront certificates remain in `us-east-1`.

Use a separate GitHub environment such as `staging-sites` and a separate OIDC
role scoped to the staging bucket/distribution. Keep `production-sites` and
its current role scoped to production landing/docs resources.

The deployment workflow builds artifacts before AWS mutation and uses
independent jobs:

```text
build production -> deploy production + docs
build staging    -> deploy staging
```

Both run for every relevant push. Failure is isolated: no job may substitute
the other variant's artifact.

## Human decisions and actions required

- **HUMAN JUDGMENT — PRODUCTION CONTENT:** Review the literal
  `d3fe28a6`-plus-Getting-Started candidate and decide any duplicate
  installation/computer-to-phone cleanup.
- **HUMAN JUDGMENT — LOCAL CHANNELS:** Approve production and staging side by
  side, including content ownership, visible staging identity, robots policy,
  asset isolation, and responsive behavior.
- **HUMAN JUDGMENT — AWS CHANGE SUMMARY:** Approve the exact staging
  CloudFormation, Route 53, ACM, IAM/OIDC, GitHub environment, and workflow
  changes.
- **HUMAN — MANDATORY:** Explicitly authorize AWS and GitHub remote mutations.
- **HUMAN — MANDATORY:** Explicitly authorize the first dual production and
  staging publication.
- **HUMAN JUDGMENT — PUBLIC CHANNELS:** Review both public sites and confirm
  production content, staging no-index behavior, and artifact separation.

## Expected outputs

Repository implementation:

- variant-owned production and staging homepage content;
- variant loader/configuration;
- production/staging build and preview scripts;
- variant-specific robots and analytics behavior;
- production/staging content and browser tests;
- separate staging CloudFormation and OIDC deployment package;
- dual-build/deploy workflow.

Documentation:

- landing package build/preview/deployment guide;
- static-site deployment guide and staging operations;
- content-system variant ownership;
- production restoration decision and historical source boundary;
- paused-task/resumption records.

Verification:

- production and staging local builds;
- simultaneous local previews;
- content and broken-asset checks;
- responsive/accessibility browser checks;
- CloudFormation validation;
- workflow syntax/configuration checks;
- AWS/DNS/TLS/headers/invalidation smoke only after authorization.

## Scope boundaries

- Do not edit generated `dist/` as source.
- Do not load production from `git show` at build time; copy the approved
  historical content into a maintained production source.
- Do not silently modify the historical baseline to improve positioning.
- Do not let staging assets enter shared production public output.
- Do not use `noindex` as a privacy or authentication mechanism.
- Do not connect to the Ireland server or run AWS/GitHub remote commands
  without current explicit authority.
- Do not deploy or change DNS/IAM merely because local implementation passes.
- Do not resume task `019` or compatibility UI implementation before the
  recorded resumption checkpoint.

## Execution plan

Status: Approved

Implement the release-channel split before further homepage or compatibility
UI work.

First preserve the exact historical source and produce a literal local
production candidate:

1. add explicit production/staging variant configuration and paths;
2. copy the `d3fe28a6` homepage into the maintained production source;
3. copy the current in-progress homepage into staging ownership;
4. add the current Getting Started section to production;
5. omit only Getting Started media/placeholder and review-only fields;
6. build both variants with the current shared renderer;
7. inspect the literal production result before resolving duplicate installer
   or mobile-connection content.

Stop at the Production Content checkpoint.

After content approval, complete local channel isolation:

1. make production the default build;
2. add explicit staging build/preview commands;
3. separate output directories;
4. isolate staging-only public assets;
5. add visible staging identity;
6. add staging meta robots, robots.txt, and analytics exclusion;
7. add production/staging content, asset, responsive, accessibility, and
   variant-separation checks;
8. preview both sites simultaneously.

Stop at the Local Channels checkpoint.

After local approval, prepare but do not execute remote changes:

1. read-only inspect the staging DNS/resource state after explicit remote
   inspection authority;
2. add a separate staging static-site CloudFormation template/scripts;
3. add a staging-only OIDC role and GitHub environment contract;
4. split the workflow into production/docs and staging build/deploy paths;
5. validate templates, workflow variables, paths, and least privilege;
6. present the exact AWS/GitHub change summary.

Stop for explicit remote-mutation authorization.

After authorization:

1. provision or reconcile the staging stack;
2. configure the staging GitHub environment and role;
3. run the first dual deployment;
4. verify production content/downloads/robots;
5. verify staging content, visible identity, no-index metadata/header,
   robots.txt, analytics exclusion, DNS/TLS, and asset separation;
6. record outputs, rollback information, and paused-task resumption status.

### Implementation decisions and open questions

- Decision: the production historical baseline is exactly `d3fe28a6`.
- Decision: production adds the current six-step Getting Started section and
  removes only its empty visual placeholders before the first review.
- Decision: the prior production sections are preserved in the first
  candidate; duplicate installer/mobile guidance is a human review decision.
- Decision: staging owns the in-progress new homepage.
- Decision: shared code with separate content roots is preferred over two
  complete Astro copies.
- Decision: production is the default build variant.
- Decision: staging is public but no-index/no-follow and visibly identified.
- Decision: staging uses separate AWS and GitHub deployment identities.
- Decision: the Ireland server is not the default static hosting path.
- Decision: task `019`, compatibility UI work in `030`, and website
  publication integration in `020` are paused as recorded above.
- Open: after viewing the literal production candidate, decide whether the
  historical hero installer and **Computer to phone** guide remain beside
  Getting Started or receive a narrowly approved removal/link adjustment.
- Open: decide whether S3 versioning/rollback improvements are added to the
  existing production stack now or deferred after the staging channel is
  operational.

### Documentation

- Document variant selection, source ownership, builds, previews, outputs,
  robots behavior, analytics behavior, and staging asset rules.
- Document the exact historical production source and approved deviations.
- Document staging stack deployment, GitHub environment variables, smoke
  checks, and rollback.
- Update the paused owning task files when checkpoints complete.

### Task checklist

- [x] Identify the exact pre-Desktop-download historical baseline.
- [x] Record task `018` historical ownership and paused task `019`, `030`, and
      `020` state and resumption intent in this plan and the owning files.
- [x] Obtain approval of this execution plan.
- [x] Add production/staging variant source and build boundaries.
- [x] Build the literal historical-plus-Getting-Started production candidate.
- [x] Obtain Production Content approval.
- [x] Complete local production/staging isolation and tests.
- [x] Obtain Local Channels approval.
- [x] Prepare staging AWS/IAM/GitHub/workflow changes.
- [x] Obtain AWS Change Summary approval.
- [x] Obtain explicit remote-mutation authorization.
- [x] Provision/configure staging and run the first dual deployment.
- [x] Verify both public channels and rollback data.
- [ ] Obtain Public Channels approval.
- [x] Record task `019`, `030`, and `020` resumption status.

### Requirement verification

- Historical baseline: compare maintained production source semantically and,
  where practical, byte-for-byte with
  `d3fe28a62ccdf82451e8273dc30245ca9075f0dd`, with an explicit allowlist for
  the added Getting Started section and later human-approved duplicate
  cleanup.
- Getting Started: production content/build tests verify six ordered steps,
  current installer commands, maintained Desktop release metadata, platform
  availability, connection methods, and absence of media/placeholder fields.
- Variant separation: build both variants from a clean checkout and assert
  different homepage source hashes, output directories, site URLs, robots
  behavior, analytics behavior, and staging marker state.
- Production safety: generated production HTML contains no staging path,
  staging marker, staging candidate asset, planned-visual panel, missing image,
  review label, or `noindex` directive.
- Staging safety: generated staging HTML and HTTP responses contain visible
  staging identity plus meta and `X-Robots-Tag` no-index/no-follow policy;
  `robots.txt` disallows crawling and production analytics are absent.
- Asset integrity: crawl both static outputs and public routes for missing
  local resources; verify staging-only assets are absent from the production
  artifact.
- Deployment isolation: CloudFormation/IAM inspection proves different
  buckets, distributions, certificates/aliases, OACs, environment identities,
  and invalidation targets.
- Public production: browser/link checks verify historical content plus
  approved Getting Started, current CLI/Desktop downloads, responsive layout,
  accessibility, and ordinary indexing behavior.
- Public staging: browser/header checks verify the current in-progress site,
  no-index/no-follow controls, no production analytics, valid TLS, and no
  broken assets.
- Paused work: task-file inspection identifies `018` historical ownership and
  the exact pause/resumption checkpoints for `019`, `030`, and `020`.

### Additional implementation verification

- Run landing content tests and builds separately for production and staging.
- Run representative desktop, tablet, 390-pixel, and 320-pixel browser checks
  in light and dark themes for both variants.
- Validate CloudFormation templates before any deploy and inspect change sets
  before applying them.
- Verify GitHub workflow artifact names, environment scoping, OIDC subjects,
  bucket permissions, distribution IDs, and no cross-channel fallback.
- After deployment, verify Route 53 A/AAAA, ACM status, CloudFront headers,
  cache invalidation, S3 privacy, and public content hashes.

## Implementation Notes

- 2026-10-24: The user approved the complete execution plan and requested a
  clean commit of all current changes in the main worktree before
  implementation. Execution starts with the variant source/build boundary and
  the literal `d3fe28a6` production homepage plus the current Getting Started
  section, omitting only its empty media/placeholder and review-only fields.
  Stop at the Production Content human checkpoint before resolving duplicated
  installer or **Computer to phone** guidance.
- 2026-10-24: Committed the complete pre-implementation planning and evidence
  state as `3470baf0` (`Plan website release channels`).
- 2026-10-24: Added explicit production/staging sources and builds. Production
  defaults to the exact `d3fe28a6` homepage, validated byte-for-byte, with a
  separate current six-step Getting Started section inserted after the hero.
  The addition contains current installer/Desktop/mobile content but no
  `reviewStatus`, `media`, proof placeholder, or planned-visual fields. The
  former current homepage now lives under staging ownership.
- 2026-10-24: Production and staging build successfully to
  `dist/production/` and `dist/staging/`. Production emits ordinary
  `robots.txt`; staging has a visible banner, no-index/no-follow metadata,
  no production analytics, and disallowing `robots.txt`. Shared navigation
  preserves historical production anchors and current staging anchors.
- 2026-10-24: Verification passed 11 content tests, 5 focused production
  Playwright tests, and the 28 active staging browser tests; 68 opt-in preview
  tests were correctly skipped. Both variants passed broken-image and
  overflow checks. Direct image inspection covered production desktop/light,
  phone/light, and phone/dark.
- 2026-10-24: The literal production candidate intentionally displays both the
  historical hero installation chooser and Getting Started installation step,
  and both the historical **Computer to phone** guide and new workspace/mobile
  steps. No duplicate cleanup has been made. Local previews are running at
  `http://192.168.8.10:4180/` (production) and
  `http://192.168.8.10:4181/` (staging). Stop at the Production Content human
  checkpoint.
- 2026-10-24: The implementation is intentionally not ready to push. The
  existing GitHub deployment workflow still synchronizes `landing_page/dist/`
  as one site, while the new builds write `dist/production/` and
  `dist/staging/`. Workflow/AWS changes belong after Production Content and
  Local Channels approval; pushing this intermediate state could deploy the
  wrong object layout.
- 2026-10-24: The user approved production with one narrow deviation from the
  historical baseline: remove the redundant CLI installation chooser from the
  hero and point its first action to Getting Started. The historical source
  remains byte-for-byte intact; `sites/production/content/home-adjustments.yaml`
  records and applies the approved override. The user approved proceeding
  through workflow implementation and deployment, which also approves the
  completed local-channel checkpoint and authorizes AWS/GitHub remote
  mutations and the first dual publication.
- 2026-11-04: Created and inspected the staging hosting change set before
  execution. It contained eleven additions and no updates, replacements, or
  deletions: retained private S3 bucket, bucket policy, OAC, ACM certificate,
  CloudFront distribution, directory-routing function, two cache policies,
  no-index/security response policy, and Route 53 A/AAAA records. Stack
  `crystal-lattice-static-site-staging` completed successfully.
- 2026-11-04: Created and inspected the staging IAM change set before
  execution. It contained one `AWS::IAM::Role` addition and no update,
  replacement, or deletion. The role trusts only the `staging-sites` GitHub
  environment and can write only the staging bucket and invalidate only
  distribution `E3M0P86O9DHUDP`.
- 2026-11-04: Created GitHub environment `staging-sites`, restricted its
  custom deployment branch policy to `main`, and configured environment-scoped
  AWS region, staging bucket/distribution, site/docs URLs, and OIDC role
  secret. Production remains under `production-sites`.
- 2026-11-04: Saved the pre-deployment production bucket locally under ignored
  artifacts at
  `landing_page/artifacts/site-variants/deployment-backups/20261104-232856/production`
  with a SHA-256 manifest. S3 versioning was not enabled.
- 2026-11-04: Published the production artifact to
  `crystal-lattice-prod-site-874087778966` and staging to
  `crystal-lattice-staging-site-874087778966`, then completed invalidations
  `I6XB5DQ7T6PXOW4FXPWTKTLWWK` and
  `I43ZDFUFQJSGOZIN4V68QGJ7HH`.
- 2026-11-04: Public browser verification passed. Production has one
  installation chooser, no hero installer, a hero action targeting
  `#getting-started`, the six-step Getting Started section, the retained
  historical **Computer to phone** section, production analytics, ordinary
  robots behavior, no staging banner/draft assets, and no broken images.
  Staging has its visible banner, meta robots and Googlebot no-index policy,
  CloudFront `X-Robots-Tag`, disallowing robots.txt, no analytics, staging
  draft assets, and no broken images. Both DNS A/AAAA aliases and TLS
  certificates are valid; the Desktop DMG returned HTTP 200.
- 2026-11-04: Task `019` and compatibility task `030` are unblocked at their
  recorded H2 and Canonical Tables checkpoints. Waitlist task `020` has cleared
  this channel dependency but remains gated by its own decisions and task
  `019` integration handoff.