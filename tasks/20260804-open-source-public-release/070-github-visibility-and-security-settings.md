# Change GitHub Visibility And Apply Immediate Security Settings

Integrate the reviewed readiness work into the actively developed repository,
apply the immediate GitHub security settings, make the current remote
repository public, and verify the transition without stopping normal branch
development.

## Requirements checklist

- [ ] The tested readiness-baseline changes are integrated into the actual
  current `main`, and every remote ref added or changed since the baseline has
  passed the required delta review.
- [ ] All branches, tags, pull-request refs, and reachable history present on
  GitHub at the visibility change are treated as publication scope; future
  pushed refs are public by default.
- [ ] `main` is protected by a ruleset or branch protection requiring pull requests and required checks.
- [ ] Force pushes and deletion of `main` are blocked.
- [ ] Default Actions token permissions are read-only and Actions cannot approve pull requests.
- [ ] Production deployment/release environments require appropriate approval and branch restrictions.
- [ ] Fork-based pull requests and other untrusted workflows cannot access
  repository secrets, protected environments, write tokens, signing
  credentials, or deployment authority.
- [ ] Dependency graph, Dependabot alerts, secret scanning, push protection, and private vulnerability reporting are enabled where available.
- [ ] Repository description, homepage, topics, license detection, Issues, and support/security links are correct.
- [ ] No unexpected workflow runs or infrastructure deployments occur during the transition.

Parent Task: tasks/20260804-open-source-public-release/000-main.md
Depends On: tasks/20260804-open-source-public-release/060-publication-readiness-gate.md

## Responsibility split

### Agent-executable work

- Integrate or adapt the remaining readiness-baseline changes on current
  `main`.
- Inventory and scan remote branches, tags, pull-request refs, workflow output,
  releases, and deployments.
- Run local audits, tests, builds, link checks, and live-route verification.
- Configure Actions permissions, allowed actions, SHA enforcement,
  environments, repository metadata, and supported security features through
  the GitHub API after approval.
- Push approved refs, monitor expected workflows, stop on unexpected activity,
  and perform post-change API and logged-out verification.

### Owner-required work

- Explicitly approve execution of this Draft plan and the publication timing.
- Complete or explicitly authorize the final repository visibility change.
- Complete any GitHub owner re-authentication, confirmation prompt, or required
  environment approval.
- Retain the original secret values for the later environment-secret migration;
  GitHub does not expose stored values for automated copying.

## Procedure

### Prepare security settings while still private

1. Confirm task `060` is `GO` and record its tested readiness-baseline SHA and
   remote-ref inventory.
2. Confirm active development continues throughout the process and use
   baseline-plus-delta checks instead of stopping branch activity.
3. Inventory current GitHub branches, tags, pull-request refs, releases, and
   their tip SHAs, and compare them with task `060`.
4. Scan every new or changed remote ref and its newly reachable commits with
   the task `060` secret/privacy checks.
5. Re-run affected legal, documentation, dependency, workflow, build, or test
   checks when the delta touches those boundaries.
6. Confirm no production deployment or release workflow is currently running.
7. Confirm required repository secrets are stored only in GitHub settings, not
   in files.
8. Set default workflow permissions to **Read repository contents and
   packages**.
9. Disable **Allow GitHub Actions to create and approve pull requests**.
10. Require approval for first-time outside contributors before their workflows
   run.
11. Confirm fork workflows receive neither repository secrets nor write tokens.
12. Change the allowed-actions policy to selected actions:
    - allow GitHub-owned actions;
    - allow `aws-actions/configure-aws-credentials`;
    - allow `ruby/setup-ruby`;
    - add a future action repository only when a reviewed, SHA-pinned workflow
      actually needs it.
13. Require actions to be pinned to a full-length commit SHA.
14. Create or update environment `production-sites`.
15. Restrict `production-sites` to `main` and add a required reviewer if
    supported.
16. Confirm environment `cli-release` is restricted to tags matching
    `crystal-lattice-cli-v*`; add a required reviewer if supported.
17. Create or update environment `testflight`.
18. Restrict `testflight` to `main` and add a required reviewer if supported.
19. Attach only the static-site, CLI publication, and TestFlight publication
    jobs to their corresponding environments.
20. Keep existing secret values at repository scope for the initial
    publication under the owner's accepted trusted-write-collaborator model.
21. Confirm:
    - no workflow uses `pull_request_target`;
    - Public CI does not reference repository secrets;
    - secret-bearing workflows do not run for pull requests;
    - TestFlight remains manual-only;
    - CLI publication remains manual/tag-only;
    - deployment and publication jobs retain their branch/tag environment
      restrictions.
22. Record environment-scoping of the existing secret values as mandatory
    post-publication hardening in task `130`.

### Integrate and validate current `main` while still private

1. Work in `/Users/ferenci84/Dev/Mine/ai-agent-platform-main` on `main`.
2. Treat the old publication-candidate branch as evidence and a source for
   selected changes, not as a branch to merge wholesale into current `main`.
3. Adapt the remaining applicable baseline changes to current code:
   - repeat and apply supported dependency-advisory remediation against the
     current lockfiles;
   - attach the TestFlight publication job to `testflight`;
   - adapt the Actions security validator to require the exact intended
     workflow/job/environment mappings;
   - retain current deployment and CLI-release improvements that superseded
     the old baseline.
4. Record the actual current `main` SHA being validated.
5. Refresh the remote-ref inventory. If another branch, tag, or pull-request
   ref changed during setup, scan that delta before continuing.
6. Push only the approved current `main` and other specifically intended refs.
7. Expect exactly:
   - `Public CI`;
   - `Deploy Static Sites`.
8. Do not manually dispatch TestFlight or CLI release and do not create a
   release tag.
9. Require all four Public CI jobs to pass on the actual current `main` SHA.
10. Require the static-site build, protected deployment, and both AWS
    deployments to pass.
11. Stop with the repository private if a protected environment is unavailable,
    an expected workflow fails, or an unexpected workflow, release, TestFlight
    upload, or infrastructure operation starts.
12. Verify all of these live routes return successfully:
    - `https://crystallattice.dev/`
    - `https://crystallattice.dev/privacy`
    - `https://crystallattice.dev/support`
    - `https://crystallattice.dev/mobile`
    - `https://docs.crystallattice.dev/`
13. Verify the live Claude Tools documentation contains the reviewed
    public-behavior/Apache provenance and no longer contains the superseded
    statement that normalized fixtures are subject to Anthropic's terms.
14. Refresh the workflow, deployment, release, repository-setting, and
    remote-ref inventories immediately before visibility changes. Review any
    new delta while development continues.
15. Continue only when no workflow is active or queued and every current
    remote ref is covered by the baseline plus reviewed deltas.

### Change visibility

1. Open repository **Settings → General**.
2. Scroll to **Danger Zone**.
3. Choose **Change repository visibility**.
4. Select **Public**.
5. Confirm `dynamicprogrammingsolutions/crystal-lattice`.
6. Complete the owner confirmation.
7. Do not announce the repository until the remaining steps and task `080`
   succeed.

### Protect the default branch immediately

1. Open **Settings → Rules → Rulesets**.
2. Create an active branch ruleset targeting `main`.
3. Require pull requests before merging.
4. Require at least one approval.
5. Dismiss stale approvals when new commits are pushed.
6. Require resolution of review conversations.
7. Add these stable checks from task `040` as required checks:
   - `Public CI / Repository checks`
   - `Public CI / Python unit tests`
   - `Public CI / Frontend package tests`
   - `Public CI / Landing and docs build`
8. Block force pushes.
9. Block branch deletion.
10. Keep bypass access limited to repository administrators for emergency use.

### Enable security features

1. Open **Settings → Advanced Security** or **Code security and analysis**.
2. Enable dependency graph.
3. Enable Dependabot alerts.
4. Enable Dependabot security updates.
5. Enable secret scanning.
6. Enable push protection.
7. Enable private vulnerability reporting.
8. Review initial alerts before adding new automation.

### Protect deployments

1. Recheck that `production-sites`, `cli-release`, and `testflight` retained
   their branch/tag restrictions and reviewer rules through the visibility
   change.
2. Confirm the static-site, CLI release, and TestFlight publication jobs are
   the only jobs attached to those environments.
3. Confirm fork-based pull-request jobs cannot access repository secrets,
   protected environments, write tokens, or publication authority.
4. Keep environment-scoping of the existing secret values deferred to task
   `130`; do not delete or recreate secret values during this transition.

### Complete repository presentation

1. Set a concise description.
2. Set the homepage to the Crystal Lattice landing page.
3. Add focused repository topics.
4. Confirm Issues are enabled.
5. Leave Discussions disabled for the initial release unless the owner wants a
   second support channel.
6. Confirm GitHub recognizes Apache-2.0.
7. Check the repository from a logged-out browser.

## Execution plan
Status: Approved

Execute this as a mixed automatic/manual transition. The agent performs the
repository integration, delta review, tests, most GitHub settings changes,
workflow monitoring, and verification. The owner approves publication timing
and completes or explicitly authorizes the final visibility operation and any
GitHub confirmation that cannot be automated.

Because rulesets are not currently available for this private repository on its
present plan, minimize the interval between making the repository public and
activating the `main` ruleset.

The current repository settings require mandatory pre-publication correction:

- default workflow permissions are `write`;
- Actions may approve pull requests;
- all third-party actions are allowed;
- full-SHA policy enforcement is disabled.

Environments `production-sites` and `cli-release` already have their intended
`main` branch and CLI release-tag restrictions. Environment `testflight` still
needs to be created and the current TestFlight publication job needs to be
attached to it.

Existing secret values may remain repository-scoped for the initial public
release. This is an explicit risk acceptance based on trusted write
collaborators, manual/restricted publication triggers, no
`pull_request_target`, and secret-free Public CI. It does not prevent a trusted
collaborator or compromised write-enabled account from deliberately using a
repository secret in a new workflow. Moving the values to protected
environments remains required post-publication hardening in task `130`.

### Implementation decisions and open questions

- Keep Issues enabled.
- Keep Discussions disabled initially.
- Do not enable expensive or noisy optional automation until task `130`.
- Use protected environments for production authority.
- Require the four stable `Public CI` checks on `main`.
- Permit only GitHub-owned actions plus the currently required AWS credentials
  and Ruby setup action repositories.
- Require full-SHA action references; version comments remain informational.
- Integrate the readiness-baseline changes with current development while the
  repository remains private; visibility changes only after current-tip CI,
  remote-ref delta review, and live legal/support surfaces pass.
- Keep branches active during publication. Use a baseline-plus-delta model for
  every remote branch, tag, and pull-request ref.
- Local-only branches are outside GitHub publication scope until pushed.
- Keep existing secret values repository-scoped for the initial publication;
  defer their environment migration to task `130`.
- Do not defer Actions token hardening, selected-action enforcement,
  environment branch/tag restrictions, or TestFlight environment attachment.
- The current TestFlight workflow is manual-only and must use the protected
  `testflight` environment before publication.

### Documentation

- Record the final settings and any unavailable organization-plan features.
- Record the accepted temporary repository-secret trust model and the task
  `130` follow-up.
- Do not record secret values.

### Task checklist

- [x] Integrate applicable readiness-baseline changes into current private
  `main`.
- [x] Apply pre-visibility Actions settings.
- [x] Protect production, CLI release, and TestFlight environments.
- [x] Verify fork-PR and protected-workflow isolation without relocating secret
  values.
- [x] Scan all remote-ref changes since task `060`.
- [ ] Validate Public CI, static deployment, and live public-facing content on
  the actual current `main`.
- [ ] Change visibility to public.
- [ ] Protect `main`.
- [ ] Enable immediate security features.
- [ ] Recheck deploy/release environment protection after visibility changes.
- [x] Set repository presentation metadata.
- [ ] Verify through logged-out and API checks.

### Requirement verification

- GitHub settings/API inspection confirms public visibility and protections.
- Private pre-visibility workflow runs prove the actual current `main` and
  static-site deployment path before public exposure.
- Remote-ref inventory and delta scans cover all branches, tags,
  pull-request refs, and newly reachable commits present at publication.
- A fork-based test pull request cannot deploy, publish, receive a write token,
  or read repository secrets.
- Private vulnerability reporting and public Issues are accessible.

## Implementation Notes

### September 7, 2026: private-side preparation completed

Execution started in
`/Users/ferenci84/Dev/Mine/ai-agent-platform-main` on local `main` at
`63e73300c6f504a5361d11797024d2b8e6026655`. At the start, local `main` was 24
commits ahead of `origin/main`, local `develop` pointed to the same commit, the
repository was private, no workflow was active or queued, and no pull request
was open.

The old publication-candidate branch was not merged wholesale. Its still
applicable changes were adapted to current `main`:

- root `shell-quote` resolved to `1.10.0`;
- mobile and desktop React Native community CLI packages moved from `20.0.0`
  to the supported same-major `20.2.0`;
- both application lockfiles resolved `fast-xml-parser` to `5.11.1` and
  `shell-quote` to `1.10.0`;
- the TestFlight publication job now uses environment `testflight`;
- the Actions security validator requires the exact four intended
  workflow/job/environment mappings while retaining the newer static-site
  deployment checks.

Production-only npm audits report zero critical findings for the root, mobile,
and desktop lockfiles. The remaining root full-audit critical finding is the
previously accepted development-only Vitest UI-server advisory; remaining
mobile and desktop findings are non-critical transitive tooling findings
tracked for task `130`.

Private GitHub settings now enforce:

- read-only default workflow token permissions;
- no Actions pull-request approval;
- selected Actions limited to GitHub-owned actions,
  `aws-actions/configure-aws-credentials`, and `ruby/setup-ruby`;
- full-length commit-SHA action references.

Environment state now is:

- `production-sites`: restricted to branch `main`;
- `cli-release`: restricted to tags matching `crystal-lattice-cli-v*`;
- `testflight`: created and restricted to branch `main`.

Required reviewers remain unavailable in the current private-repository plan
and must be reconsidered immediately after visibility changes. Existing secret
values remain repository-scoped under the approved temporary trust model and
their migration is tracked in task `130`.

The fresh publication mirror covered 34 remote branch heads, two tags, all 12
GitHub pull-request heads, and 2,014 commits:

- Gitleaks `8.30.1`: the same three accepted findings—one notification-cache
  false positive and two revoked historical JWT findings;
- TruffleHog `3.96.0`: zero verified credentials and the same two unverified
  revoked historical JWT findings, with the previously documented Lob
  false-positive detector excluded.

No new secret or privacy finding was identified.

Local verification on the updated tree:

- Actions validator, actionlint, workflow YAML parsing, manifest parsing, and
  `git diff --check`: passed;
- core Python 3.11: `504 passed`, `26 deselected`, one expected xfail;
- application Python 3.11 in a clean CI-equivalent virtual environment:
  `371 passed`, one skipped, `92 deselected`;
- frontend SDK: `335 passed`;
- React bindings: `20 passed`;
- shared React Native components: `51 passed`;
- mobile clean install/configuration: passed; `176` tests passed;
- desktop clean install/configuration: passed; `141` tests passed;
- landing production build: passed with all five expected routes;
- documentation preparation and non-strict production build: passed.

The first application run used a contaminated shared Python environment and
failed while loading incompatible cached plugin dependencies. A clean Python
3.11 environment resolved that failure. A second clean run initially omitted
the virtual environment from subprocess `PATH`; rerunning with the same
`setup-python` path behavior used by Public CI passed the full application
suite. No source change was required for either local-environment issue.

Execution remains before the current-`main` commit/push, hosted Public CI and
deployment validation, final remote-ref delta check, visibility confirmation,
and post-public settings.

### September 7, 2026: current `main` pushed and privately validated

Commit `6ad8970a28addb3fef184eb9fd85d05597132779` was pushed to remote
`main`. The push advanced `main` by 25 reviewed commits and intentionally
triggered only:

- Public CI run `34141194786`: passed all four required jobs;
- Deploy Static Sites run `34141194767`: passed the landing/docs builds,
  protected AWS OIDC assumption, and both deployments.

No TestFlight run, CLI release run, release tag, or new release was triggered.
The deployment for `6ad8970a28addb3fef184eb9fd85d05597132779`
finished successfully.

All required live routes returned HTTP `200` after deployment:

- `https://crystallattice.dev/`
- `https://crystallattice.dev/privacy`
- `https://crystallattice.dev/support`
- `https://crystallattice.dev/mobile`
- `https://docs.crystallattice.dev/`

The deployed Claude Tools page states that the package is an independent,
AI-assisted compatibility implementation based on publicly visible Claude Code
interfaces and that its normalized fixtures are Apache-2.0 licensed. The
superseded Anthropic-license statement is absent.

The post-push publication mirror covered 34 remote branch heads, two tags, all
12 GitHub pull-request heads, and 2,015 commits. Both history scans remained
identical to the accepted baseline:

- Gitleaks: three accepted findings, with no new finding;
- TruffleHog: two unverified revoked historical JWT findings and zero verified
  credentials.

The two new workflow log archives contained:

- zero Gitleaks findings;
- zero TruffleHog findings;
- no private-key, AWS access-key, or GitHub-token value shape;
- normal GitHub masking markers only.

No Actions artifact is retained and no workflow is active or queued.

Repository presentation metadata now includes:

- description: `A modular, provider-agnostic AI agent platform with Python,
  terminal, web, mobile, and desktop clients.`;
- homepage: `https://crystallattice.dev`;
- topics: `agent-framework`, `ai-agents`, `fastapi`, `llm`, `python`, and
  `react-native`;
- Issues enabled and Discussions disabled.

The next commit records this evidence only. After its hosted Public CI and
final ref delta scan pass, execution stops for the owner visibility
confirmation.

### September 8, 2026: website truthfulness delta prepared

Before repository visibility changed, the owner requested two public-surface
corrections. Current `main` and `origin/main` were synchronized at
`5351da7ea6cdde808c40ea93aaae31adde4dd99f`, and the preceding analytics work
was committed with a clean worktree.

The prepared delta:

- restores the homepage hero badge to `Open Source`;
- retains the model-native/plugin-driven product description elsewhere;
- removes the unavailable `pipx install crystal-lattice-cli` and
  `pip install crystal-lattice-cli` claims from maintained user guidance;
- documents the bundled download installer as the released user path and
  editable source installs as the developer path;
- makes the hero alternate-install field optional and omits its row when no
  supported alternative exists;
- adds a landing content regression test and runs it in both Public CI and
  static-site deployment.

Local verification passed:

- four analytics tests;
- two new homepage-content tests;
- landing production build with five generated routes;
- two documentation analytics tests;
- documentation preparation and non-strict production build;
- workflow YAML parsing, actionlint, Actions security validation, and
  `git diff --check`;
- an isolated live installer smoke test using release `0.1.4`, followed by a
  successful `crystal-lattice --help`;
- maintained and generated public documentation contain no unsupported
  `pipx`/`pip` CLI installation command;
- generated homepage HTML contains `Open Source`, the supported installer, and
  no alternate-install row.

The refreshed pre-push publication mirror covered 34 branch heads, five tags,
all 12 GitHub pull-request heads, and 2,066 commits:

- Gitleaks: the same three accepted historical findings;
- TruffleHog: zero verified credentials, the two accepted revoked historical
  JWT findings, and one new unverified URI match in the analytics sanitizer
  test.

The new URI match is the intentionally fake
`name:password@example.com` referrer used to prove that analytics removes URL
credentials and private query/fragment data. It is not an active credential
and is retained as useful security-test coverage.

Public CI run `34275747652` on concurrent `develop` work was still active, so
the website delta was not pushed while that run was in progress.
