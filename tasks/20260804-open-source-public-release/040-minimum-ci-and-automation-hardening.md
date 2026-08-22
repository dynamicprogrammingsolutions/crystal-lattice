# Add Minimum Public CI And Harden Automation

Ensure untrusted public contributions are validated without receiving deployment
credentials, broad write permissions, or an easy path to unexpected cloud cost.

## Requirements checklist

- [x] Pull requests run a bounded, credential-free validation workflow covering the primary supported code paths.
- [x] Pull-request workflows use read-only permissions and do not expose repository, AWS, provider, signing, or deployment secrets.
- [x] Existing deployment and release workflows grant write/OIDC permissions only to jobs and steps that require them.
- [x] Third-party Actions use an approved immutable reference strategy.
- [x] CI concurrency and scope controls prevent obviously wasteful duplicate execution.
- [x] Public contributors cannot cause production deployment or package publication by opening or modifying a pull request.

Parent Task: tasks/20260804-open-source-public-release/000-main.md
Depends On: tasks/20260804-open-source-public-release/010-sensitive-data-and-history-release-gate.md

## Known starting state

- No general pull-request CI workflow was found.
- Repository Actions currently default to write permission.
- Actions are allowed to approve pull requests.
- All actions are allowed and SHA pinning is not required.
- Static-site deployment uses AWS OIDC.
- CLI release automation has workflow-level `contents: write` and
  `id-token: write`.

## Current audit findings

- The repository is still private and currently has two active workflows:
  `Deploy Static Sites` and `Release crystal-lattice-cli`.
- Neither active workflow uses `pull_request`, `pull_request_target`,
  `workflow_run`, or another event that executes untrusted pull-request code.
- The static-site workflow runs on pushes to `main` for site-related paths and
  by manual dispatch. Its single build/deploy job receives `id-token: write`
  from workflow scope.
- The CLI release workflow runs by manual dispatch and on
  `crystal-lattice-cli-v*` tags. All test, build, and publication jobs currently
  receive both `contents: write` and `id-token: write`, although only the
  GitHub-release job needs contents write and only the downloads publication
  job needs AWS OIDC.
- The latest observed static-site deployment succeeded in approximately three
  minutes. The latest observed manual CLI test/build run succeeded in
  approximately eleven minutes; its publication jobs were correctly skipped
  because it was not a tag run.
- No GitHub deployment environments currently exist.
- Repository Actions policy currently allows all actions, does not require SHA
  pinning, gives the default `GITHUB_TOKEN` write permission, and allows Actions
  to approve pull requests.
- Current private-fork settings do not send secrets or write tokens, but they
  also do not run fork pull-request workflows. Public-fork approval behavior
  must be configured during task `070`.
- Two repository secrets and repository-level deployment variables are
  configured. The planned PR workflow does not need or reference any of them.
- Every active external action is referenced through a mutable major tag.
- The current major lines resolve to these reviewed patch releases:
  - `actions/checkout` `v4.4.0`
  - `actions/setup-python` `v5.6.0`
  - `actions/setup-node` `v4.4.0`
  - `actions/upload-artifact` `v4.6.2`
  - `actions/download-artifact` `v4.3.0`
  - `aws-actions/configure-aws-credentials` `v4.3.1`
  - `softprops/action-gh-release` `v2.6.2`
- A disabled GitHub Pages workflow remains under `.github/workflows/`. Earlier
  deployment work identifies it as obsolete and superseded by the active AWS
  static-site workflow; it also references obsolete documentation build paths.
- Root npm, landing Yarn, and docs dependency files exist. The shared frontend
  packages expose fast Vitest commands, and the Python packages define
  non-integration defaults.
- Documentation strict mode is not yet a reliable gate because the docs-site
  README records pre-existing warnings. A normal prepared MkDocs build is the
  appropriate initial CI boundary.
- Local `actionlint` and `shellcheck` are available for implementation
  verification.

## Lean pre-publication scope

The initial required CI should prioritize:

- Core Python unit tests.
- Application Python unit tests.
- Fast shared frontend package tests or type checks that are stable.
- Landing/docs build validation when those files change.
- Cheap static validation such as `git diff --check` or manifest parsing.

Broad provider integration, hosted API, Docker/cloud, mobile native UI, and
multi-platform release matrices remain outside pull-request CI unless already
cheap and deterministic.

## Execution plan
Status: Approved

### Phase 1: Add a stable public pull-request workflow

Create `.github/workflows/public-ci.yml` with workflow name `Public CI`.

Triggers:

- every `pull_request`, without path filtering;
- pushes to `main` and `develop`;
- manual dispatch for owner-initiated branch verification.

Do not use `pull_request_target`, `workflow_run`, reusable privileged workflows,
or any event that would combine untrusted code with a trusted token.

Set:

- top-level `permissions: contents: read`;
- fixed `ubuntu-24.04` runners;
- `persist-credentials: false` on checkout;
- explicit job timeouts;
- no repository secrets, variables, environments, OIDC, artifact publication,
  provider credentials, native signing, or deployment commands;
- concurrency keyed by workflow and pull request/ref, with superseded
  pull-request runs cancelled while `main`/`develop` push runs are allowed to
  finish.

Do not add workflow-level path filters. Required workflows that do not start
can leave branch protection waiting for a missing check. The initial four jobs
are bounded enough to run on every pull request, and stable check names are more
important than speculative path optimization.

Use these exact job names so task `070` can require them:

1. `Repository checks`
2. `Python unit tests`
3. `Frontend package tests`
4. `Landing and docs build`

The resulting required-check contexts will be:

- `Public CI / Repository checks`
- `Public CI / Python unit tests`
- `Public CI / Frontend package tests`
- `Public CI / Landing and docs build`

#### Repository checks

Run:

- the pull-request or pushed-commit `git diff --check` boundary;
- JSON and TOML parsing for the root/public package manifests and primary
  application configuration;
- a small repository-owned validation script that rejects:
  - mutable external `uses:` references in active workflows;
  - a privileged PR trigger such as `pull_request_target`;
  - `secrets.`, deployment environments, or `id-token: write` in
    `public-ci.yml`;
  - publication workflows that acquire write/OIDC permission outside their
    explicitly authorized jobs.

Keep the validator standard-library-only so it does not need a third-party
action or package merely to enforce the workflow trust boundary.

#### Python unit tests

Use Python 3.11 and the dependency installation already exercised by the CLI
release workflow:

```bash
python -m pip install \
  -e "core/python[dev]" \
  -e application/python \
  -e "plugins/openai_responses[dev]" \
  -e plugins/tool-compat-shared \
  -e plugins/mcp-shared \
  -e plugins/web-fetch-shared
pytest core/python/tests -q -m "not integration"
pytest application/python/tests -q -m "not integration and not docker"
```

This is one lean Python version, not a compatibility matrix. Broader versions
and plugin/provider suites remain task `130` candidates.

#### Frontend package tests

Use Node.js 22, root `npm ci`, and the three stable shared-package commands:

```bash
npm --workspace @crystal-lattice/frontend-sdk test
npm --workspace @crystal-lattice/frontend-sdk-react test
npm --workspace @crystal-lattice/frontend-rn-components test
```

Do not add mobile/desktop native builds, Detox, macOS UI tests, Android
emulators, bridge/cloud integration, or hosted-provider tests to required
public CI.

#### Landing and docs build

Build from lockfiles and authored documentation sources:

```bash
yarn --cwd landing_page install --frozen-lockfile
yarn --cwd landing_page build
python -m pip install -r docs_site/requirements.txt
python docs_site/scripts/prepare_mkdocs_site.py
(cd docs_site && mkdocs build)
```

Do not use `docs_site/scripts/build_mkdocs_site.py` in PR CI because it refreshes
committed reference snapshots after building. Do not make `--strict` a required
gate until its recorded pre-existing warnings are resolved.

### Phase 2: Narrow static-site deployment authority

Update `.github/workflows/deploy-static-sites.yml` while preserving its
push/manual triggers and successful build/deployment sequence.

- Set workflow-level permissions to `contents: read`.
- Grant `id-token: write` only to the deployment job.
- Associate the deployment job with environment `production-sites`.
- Set a bounded job timeout.
- Keep deployment concurrency serialized with `cancel-in-progress: false`;
  cancelling a job between S3 synchronization and CloudFront invalidation is
  less safe than allowing the active deployment to finish.
- Keep every secret and deployment variable out of the PR workflow.
- Set `persist-credentials: false` on checkout.

Task `070` will create/protect `production-sites`, restrict it to `main`, add
the available reviewer gate, and migrate or scope deployment secrets to that
environment where supported.

### Phase 3: Narrow CLI release authority and cost

Update `.github/workflows/release-crystal-lattice-cli.yml` without changing its
manual-build and release-tag policy.

- Set workflow-level permissions to `contents: read`.
- Keep test and platform-build jobs read-only.
- Grant `contents: write` only to the GitHub-release publication job.
- Grant `id-token: write` only to the downloads publication job; retain
  `contents: read` there.
- Associate both publication jobs with environment `cli-release`.
- Keep the existing condition that publication jobs run only for
  `refs/tags/crystal-lattice-cli-v*`.
- Add workflow concurrency keyed by ref:
  - duplicate manual runs for the same ref may cancel superseded work;
  - tag release runs must not be cancelled in progress.
- Add bounded timeouts to test, build, and publication jobs.
- Set `persist-credentials: false` on checkout steps.

Do not add a new requirement that release tags be ancestors of `main`; that
would change the existing release policy beyond the approved lean hardening
scope.

Task `070` will protect `cli-release`, restrict it to release tags, add the
available reviewer gate, and migrate or scope release secrets to that
environment where supported.

### Phase 4: Pin the active automation supply chain

Replace every external `uses:` reference in active and newly added workflows
with a full 40-character commit SHA. Retain an inline version comment for human
review.

Use the current reviewed patch release in each existing major line rather than
combining hardening with a major-version upgrade:

- `actions/checkout` `v4.4.0`
- `actions/setup-python` `v5.6.0`
- `actions/setup-node` `v4.4.0`
- `actions/upload-artifact` `v4.6.2`
- `actions/download-artifact` `v4.3.0`
- `aws-actions/configure-aws-credentials` `v4.3.1`
- `softprops/action-gh-release` `v2.6.2`

Before editing, resolve each immutable release tag again and verify that its
commit matches the planned SHA. Record the tag in the comment, not as the
executable reference.

Remove `.github/workflows/publish-docs.yml.disabled` instead of pinning it. It
is non-executable, obsolete, references incorrect build paths, and has already
been superseded by AWS deployment.

Major action upgrades and automated action-SHA update tooling remain deferred
to task `130`.

### Phase 5: Document reproducible checks and permission boundaries

Update `CONTRIBUTING.md` with:

- the four required check names;
- the local commands used by each check;
- the explicit exclusion of hosted-provider, Docker/cloud, and native UI tests
  from required PR CI;
- guidance that those broader suites still apply when a change crosses their
  boundary.

Keep permission rationale adjacent to the relevant workflow permissions through
concise YAML comments:

- static deployment needs OIDC only for AWS deployment;
- GitHub release publication needs contents write;
- downloads publication needs OIDC;
- all test/build jobs remain read-only.

Update task `070`'s manual settings handoff with:

- the four exact required-check contexts;
- default workflow permission `read`;
- Actions PR approval disabled;
- approval required for first-time external contributors;
- secrets/write tokens not sent to fork workflows;
- full-SHA pinning required;
- selected actions limited to GitHub-owned actions plus the explicitly used
  AWS credentials and GitHub-release action repositories;
- `production-sites` and `cli-release` environment restrictions.

No GitHub setting is changed during task `040`.

### Phase 6: Verify without deployment credentials

Run task-owned validation with deployment, AWS, provider, and signing
credentials unset:

- `actionlint .github/workflows/*.yml`, with shellcheck integration;
- the repository-owned Actions security validator;
- Python unit commands from `Public CI`;
- shared frontend package tests;
- landing build;
- prepared non-strict MkDocs build;
- `git diff --check`;
- static inspection confirming:
  - no PR workflow references `secrets`, repository variables, environments,
    OIDC, deployment, or publication;
  - deploy/release workflows have no PR-capable trigger;
  - every active external action is pinned to a full SHA;
  - only the authorized jobs have write or OIDC permission;
  - no public CI command invokes hosted-provider, AWS, Docker/cloud, native
    signing, TestFlight, or deployment paths.

Inspect the workflow graph to confirm a fork-style `pull_request` event can only
reach the four read-only validation jobs.

An actual GitHub-hosted fork run cannot be completed while the repository is
private under the current fork settings. After the workflow is committed and
pushed, a same-repository test pull request may be run only with separate owner
authorization. Anonymous/fork execution, required-check behavior, environment
gates, and secret isolation must be reverified in tasks `060`, `070`, and `080`.

### Implementation decisions and open questions

- Keep the initial required-check set to four stable jobs that always start,
  rather than path-filtering required workflows.
- Do not introduce self-hosted runners for untrusted pull requests.
- Hosted-provider tests remain explicitly opt-in.
- Use Python 3.11, Node.js 22, and `ubuntu-24.04` as the initial single-version
  CI baseline.
- Do not require docs strict mode before its known warnings are resolved.
- Preserve the current CLI tag-release policy.
- Pin reviewed releases within the currently used action major lines; defer
  major action upgrades and automated update tooling.
- Remove the obsolete disabled Pages workflow.
- No unresolved material question remains. Approval authorizes the workflow,
  validator, contribution-guide, current-task, and task-`070` handoff changes
  described above, but not GitHub settings changes, pushes, pull requests,
  releases, or deployments.

### Documentation

- Update `CONTRIBUTING.md` with required checks and local reproduction commands.
- Add concise permission-rationale comments to active workflows.
- Record exact manual settings and required-check names in task `070`.
- Do not add a broad CI architecture document for the lean initial workflow.

### Task checklist

- [x] Define stable minimum required checks.
- [x] Add credential-free pull-request CI.
- [x] Narrow deploy/release workflow permissions.
- [x] Pin or constrain third-party actions.
- [x] Add concurrency/cost controls.
- [x] Remove the obsolete disabled Pages workflow.
- [x] Document required checks and the task `070` settings handoff.
- [x] Validate workflows from a branch without secrets.

### Requirement verification

- Static trust-boundary inspection and the later hosted public test show that a
  pull request from a fork can run required validation without secrets.
- Workflow permission inspection shows read-only PR jobs and narrowly scoped
  publication permissions.
- A PR cannot trigger AWS deployment, CLI release, or future TestFlight upload.
- The four documented check contexts are available for `main` branch
  protection.
- Repository settings can enforce full-SHA pinning and the selected-action
  allowlist without blocking an active workflow.

### Additional implementation verification

- Confirm the current dirty worktree changes outside task `040` remain
  untouched and unstaged.
- Confirm no repository secret/variable value is printed or recorded.
- Confirm no AWS, GitHub release, package publication, deployment, or
  infrastructure mutation occurs during validation.
- Confirm generated docs-site and landing-site output remains ignored and is
  not committed.

## Implementation Notes

### Main-worktree integration

- Work was performed in the dedicated `main` worktree as requested.
- `develop` was merged into `main` before implementation.
- The merge produced one conflict in the mobile `.gitignore`; owner-approved
  resolution retained both the Fastlane-generated-file ignores from `main` and
  the local Xcode environment ignore from `develop`.
- Merge commit: `a1793746`.

### Public CI

- Added `.github/workflows/public-ci.yml` with workflow name `Public CI`.
- The workflow runs on pull requests, pushes to `main`/`develop`, and manual
  dispatch.
- It defines the four stable check contexts recorded in the plan.
- Top-level token permission is `contents: read`.
- Checkout credentials are not persisted.
- No job references repository secrets, repository variables, deployment
  environments, OIDC, provider credentials, signing, TestFlight, or
  publication/deployment commands.
- Pull-request runs cancel superseded runs; branch push runs are allowed to
  finish.

### Repository-owned security validation

- Added `scripts/check_github_actions_security.py`.
- The standard-library-only validator checks:
  - full-SHA external action references;
  - unauthorized write/OIDC permissions;
  - unauthorized deployment environments;
  - privileged PR triggers on publication workflows;
  - required public-CI job names and read-only boundary;
  - privileged fragments in public CI.
- Negative checks confirmed that mutable actions, unauthorized contents write,
  and PR-capable deployment triggers are rejected.

### Deployment and release hardening

- Split static-site build and deployment into separate jobs.
- The build job is read-only and uploads a one-day static-site artifact.
- Only the deployment job has AWS OIDC and environment
  `production-sites`.
- CLI test/build jobs inherit read-only permission.
- Only the GitHub Release job has `contents: write`.
- Only the downloads publication job has AWS OIDC.
- CLI publication jobs reference environment `cli-release`.
- Added bounded timeouts and release concurrency without changing tag-release
  semantics.

### Immutable action references

- Pinned every active action to a full 40-character commit SHA with a reviewed
  patch-version comment.
- Preserved existing action major lines; no action major upgrade was mixed into
  the hardening task.
- Removed the obsolete disabled GitHub Pages workflow.

### Documentation and settings handoff

- Updated `CONTRIBUTING.md` with required check names and local reproduction
  commands.
- Updated task `070` with exact required checks, selected-action policy,
  full-SHA requirement, fork settings, and environment restrictions.
- No GitHub repository setting was changed.
- Added post-publication task
  `150-continuous-cli-development-releases.md` with Options A-C and the
  recommendation to begin with per-main-push development prereleases.

### Adjacent dependency-security finding

- Root workspace `npm audit` reported one critical and eleven high findings
  with `--omit=dev`.
- Classification showed that npm auto-installs React Native for wildcard peer
  dependencies in shared workspace packages; the critical `shell-quote`
  advisory arrives through `react-devtools-core`.
- The affected tree is contributor/test tooling, is not bundled into the
  Python CLI, and is not shipped inside the shared package peer dependency.
- Public CI has no secrets, write token, OIDC, signing, or deployment authority,
  limiting the trust consequence independently of the tooling advisory.
- The finding and safe remediation candidates were recorded in task `130`.
  No unreviewed `npm audit fix` or React Native/toolchain upgrade was performed.

## Completion Notes

Completed on August 14, 2026.

### Outcome

- The repository now has bounded public PR validation for Python, shared
  frontend packages, landing/docs, manifests, and workflow security.
- Publication workflows cannot be triggered by pull-request events and expose
  privileged tokens only in their publication jobs.
- Active external action dependencies are immutable.
- Exact check names and owner-only GitHub settings are ready for tasks `060`
  and `070`.

### Requirement evidence

- Credential-free PR CI: `public-ci.yml` has four bounded jobs, read-only
  contents permission, no secret/variable/environment/OIDC references, and no
  deployment or publication commands.
- Least privilege: static build is separate from AWS deployment; CLI
  test/build jobs are read-only; GitHub write and AWS OIDC are isolated to
  their owning jobs.
- Immutable actions: security-validator and static inspection found only the
  reviewed full-SHA action set.
- Cost controls: PR concurrency cancels superseded runs, static deployment
  remains serialized, release manual runs can cancel superseded work, tag runs
  cannot be cancelled, and jobs have explicit timeouts.
- Publication isolation: deploy/release workflows have no PR-capable event;
  public CI has no route to AWS, GitHub Releases, TestFlight, or environments.

### Verification performed

- `actionlint .github/workflows/*.yml`
  - passed
- Workflow YAML parse
  - all three active workflows parsed
- `python3 scripts/check_github_actions_security.py`
  - passed; three active workflows validated
- Validator negative checks
  - mutable action, unauthorized write, and PR-trigger fixtures rejected
- Manifest parse
  - eight JSON and four TOML manifests parsed
- Core Python unit suite
  - `448 passed`, `26 deselected`, `1 xfailed`
- Application Python unit suite
  - `320 passed`, `90 deselected`
- Frontend SDK
  - `302 passed`
- React frontend bindings
  - `20 passed`
- Shared React Native components
  - `7 passed`
- Landing build
  - passed; five static routes generated
- Prepared non-strict MkDocs build
  - passed with recorded pre-existing navigation/docstring/reference warnings
- Immutable-action, trigger, permission, environment, diff, and generated-output
  checks
  - passed

### Deferred hosted/public boundary

The repository remains private and no remote branch or pull request was created.
Actual GitHub-hosted pull-request execution, fork approval behavior, required
check enforcement, environment reviewer gates, and secret isolation must be
verified during tasks `060`, `070`, and `080`.
