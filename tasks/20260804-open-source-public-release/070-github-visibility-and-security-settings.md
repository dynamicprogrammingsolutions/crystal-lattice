# Change GitHub Visibility And Apply Immediate Security Settings

Perform the manual GitHub administration required to make the approved
repository commit public without leaving `main`, Actions, security intake, or
deployment credentials unnecessarily exposed.

## Requirements checklist

- [ ] The approved publication candidate is the repository state made public.
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

1. Confirm task `060` is `GO` and record the approved commit SHA.
2. Pause merges and direct pushes.
3. Confirm no production deployment workflow is currently running.
4. Confirm required repository secrets are stored only in GitHub settings, not
   in files.
5. Open repository **Settings → Actions → General**.
6. Set default workflow permissions to **Read repository contents and packages**.
7. Disable **Allow GitHub Actions to create and approve pull requests**.
8. Require approval for first-time outside contributors before their workflows
   run.
9. Confirm fork workflows receive neither repository secrets nor write tokens.
10. Change the allowed-actions policy to selected actions:
    - allow GitHub-owned actions;
    - allow `aws-actions/configure-aws-credentials`;
    - allow `ruby/setup-ruby`;
    - add a future action repository only when a reviewed, SHA-pinned workflow
      actually needs it.
11. Require actions to be pinned to a full-length commit SHA.
12. Create or update environment `production-sites`.
13. Restrict `production-sites` to `main` and add a required reviewer if
    supported.
14. Confirm environment `cli-release` is restricted to tags matching
    `crystal-lattice-cli-v*`; add a required reviewer if supported.
15. Create or update environment `testflight`.
16. Restrict `testflight` to `main` and add a required reviewer if supported.
17. Move or scope static-site deployment secrets to `production-sites`, CLI
    publication secrets to `cli-release`, and iOS signing/upload secrets to
    `testflight` where supported.
18. Confirm pull-request jobs cannot access any protected environment or
    publication secret.

### Publish and validate the approved candidate while still private

1. Confirm the approved task `060` candidate SHA has not changed.
2. Advance `main` to that exact candidate commit while the repository is still
   private.
3. Expect exactly:
   - `Public CI`;
   - `Deploy Static Sites`.
4. Do not manually dispatch TestFlight or CLI release and do not create a
   release tag.
5. Require all four Public CI jobs to pass on the candidate SHA.
6. Require the static-site build, artifact handoff, protected deployment, and
   both AWS deployments to pass.
7. If GitHub still reports stale artifact-storage quota, any protected
   environment is unavailable, or either expected workflow fails, stop with the
   repository private and return to task `060` or the owning deployment task.
8. Verify all of these live routes return successfully:
   - `https://crystallattice.dev/`
   - `https://crystallattice.dev/privacy`
   - `https://crystallattice.dev/support`
   - `https://crystallattice.dev/mobile`
   - `https://docs.crystallattice.dev/`
9. Verify the live Claude Tools documentation contains the candidate's
   public-behavior/Apache provenance and no longer contains the superseded
   statement that normalized fixtures are subject to Anthropic's terms.
10. Refresh the workflow, artifact, deployment, release, and repository-setting
    inventories. Continue only when no workflow is active or queued.

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
- Push and deploy the approved candidate while the repository remains private;
  visibility changes only after candidate CI and live legal/support surfaces
  pass.
- Stop before visibility if artifact quota prevents the static-site handoff.
- The current TestFlight workflow is manual-only and its release job uses the
  protected `testflight` environment.

### Documentation

- Record the final settings and any unavailable organization-plan features.
- Do not record secret names with values.

### Task checklist

- [ ] Apply pre-visibility Actions settings.
- [ ] Protect production, CLI release, and TestFlight environments.
- [ ] Advance private `main` to the approved candidate and validate expected workflows.
- [ ] Verify live landing, support, privacy, mobile, and corrected docs content.
- [ ] Change visibility to public.
- [ ] Protect `main`.
- [ ] Enable immediate security features.
- [ ] Recheck deploy/release environment protection after visibility changes.
- [ ] Set repository presentation metadata.
- [ ] Verify through logged-out and API checks.

### Requirement verification

- GitHub settings/API inspection confirms public visibility and protections.
- Private pre-visibility workflow runs prove the approved candidate and current
  static-site deployment path before public exposure.
- A test pull request cannot deploy, publish, or read protected secrets.
- Private vulnerability reporting and public Issues are accessible.
