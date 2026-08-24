# Change GitHub Visibility And Apply Immediate Security Settings

Perform the manual GitHub administration required to make the actively
developed repository and its current remote refs public without leaving
`main`, Actions, security intake, or deployment credentials unnecessarily
exposed.

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
- [ ] Dependency graph, Dependabot alerts, secret scanning, push protection, and private vulnerability reporting are enabled where available.
- [ ] Repository description, homepage, topics, license detection, Issues, and support/security links are correct.
- [ ] No unexpected workflow runs or infrastructure deployments occur during the transition.

Parent Task: tasks/20260804-open-source-public-release/000-main.md
Depends On: tasks/20260804-open-source-public-release/060-publication-readiness-gate.md

## Manual procedure

### Before changing visibility

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
6. Confirm no production deployment workflow is currently running.
7. Confirm required repository secrets are stored only in GitHub settings, not
   in files.
8. Open repository **Settings → Actions → General**.
9. Set default workflow permissions to **Read repository contents and packages**.
10. Disable **Allow GitHub Actions to create and approve pull requests**.
11. Require approval for first-time outside contributors before their workflows
   run.
12. Confirm fork workflows receive neither repository secrets nor write tokens.
13. Change the allowed-actions policy to selected actions:
    - allow GitHub-owned actions;
    - allow `aws-actions/configure-aws-credentials`;
    - allow `ruby/setup-ruby`;
    - add a future action repository only when a reviewed, SHA-pinned workflow
      actually needs it.
14. Require actions to be pinned to a full-length commit SHA.
15. Create or update environment `production-sites`.
16. Restrict `production-sites` to `main` and add a required reviewer if
    supported.
17. Confirm environment `cli-release` is restricted to tags matching
    `crystal-lattice-cli-v*`; add a required reviewer if supported.
18. Create or update environment `testflight`.
19. Restrict `testflight` to `main` and add a required reviewer if supported.
20. Move or scope static-site deployment secrets to `production-sites`, CLI
    publication secrets to `cli-release`, and iOS signing/upload secrets to
    `testflight` where supported.
21. Confirm pull-request jobs cannot access any protected environment or
    publication secret.

### Integrate and validate the current repository while still private

1. Integrate the tested readiness-baseline changes into the current `main`
   without discarding newer approved development.
2. Record the actual `main` SHA that will be public at the transition.
3. Refresh the full remote-ref inventory. If another branch, tag, or
   pull-request ref changed during setup, scan that delta before continuing.
4. Expect exactly:
   - `Public CI`;
   - `Deploy Static Sites`.
5. Do not manually dispatch TestFlight or CLI release and do not create a
   release tag.
6. Require all four Public CI jobs to pass on the actual current `main` SHA.
7. Require the static-site build, artifact handoff, protected deployment, and
   both AWS deployments to pass.
8. If GitHub still reports stale artifact-storage quota, any protected
   environment is unavailable, or either expected workflow fails, stop with the
   repository private and return to task `060` or the owning deployment task.
9. Verify all of these live routes return successfully:
   - `https://crystallattice.dev/`
   - `https://crystallattice.dev/privacy`
   - `https://crystallattice.dev/support`
   - `https://crystallattice.dev/mobile`
   - `https://docs.crystallattice.dev/`
10. Verify the live Claude Tools documentation contains the reviewed
   public-behavior/Apache provenance and no longer contains the superseded
   statement that normalized fixtures are subject to Anthropic's terms.
11. Refresh the workflow, artifact, deployment, release, repository-setting,
    and remote-ref inventories immediately before visibility changes. If refs
    changed again, review the new delta while development continues.
12. Continue only when no workflow is active or queued and every current remote
    ref is covered by the baseline plus reviewed deltas.

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
2. Confirm the static-site, CLI release, and TestFlight jobs are the only jobs
   attached to those environments.
3. Confirm pull-request jobs cannot access these environments or secrets.

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
Status: Draft

This task is primarily manual and must be performed by an organization or
repository owner. The agent may prepare commands and verify settings through
read-only GitHub API calls, but changing visibility and organization security
settings requires explicit owner action.

Because rulesets are not currently available for this private repository on its
present plan, minimize the interval between making the repository public and
activating the `main` ruleset.

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
- Stop before visibility if artifact quota prevents the static-site handoff.
- The current TestFlight workflow is manual-only and its release job uses the
  protected `testflight` environment.

### Documentation

- Record the final settings and any unavailable organization-plan features.
- Do not record secret names with values.

### Task checklist

- [ ] Apply pre-visibility Actions settings.
- [ ] Protect production, CLI release, and TestFlight environments.
- [ ] Scan all remote-ref changes since task `060`.
- [ ] Integrate baseline changes into current private `main` and validate expected workflows.
- [ ] Verify live landing, support, privacy, mobile, and corrected docs content.
- [ ] Change visibility to public.
- [ ] Protect `main`.
- [ ] Enable immediate security features.
- [ ] Recheck deploy/release environment protection after visibility changes.
- [ ] Set repository presentation metadata.
- [ ] Verify through logged-out and API checks.

### Requirement verification

- GitHub settings/API inspection confirms public visibility and protections.
- Private pre-visibility workflow runs prove the actual current `main` and
  static-site deployment path before public exposure.
- Remote-ref inventory and delta scans cover all branches, tags,
  pull-request refs, and newly reachable commits present at publication.
- A test pull request cannot deploy, publish, or read protected secrets.
- Private vulnerability reporting and public Issues are accessible.
