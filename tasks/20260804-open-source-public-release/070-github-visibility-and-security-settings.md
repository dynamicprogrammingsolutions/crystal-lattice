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
8. Require approval for workflows from outside collaborators.
9. Review allowed Actions policy and approved immutable action references.

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
7. Add the stable checks from task `040` as required checks.
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

1. Create or update environment `production-sites`.
2. Restrict it to `main` and approved release references.
3. Add a required reviewer if supported.
4. Create or update environment `cli-release`.
5. Restrict it to release tags and add approval.
6. Reserve `testflight` for the later iOS workflow.
7. Confirm pull-request jobs cannot access these environments or secrets.

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

### Documentation

- Record the final settings and any unavailable organization-plan features.
- Do not record secret names with values.

### Task checklist

- [ ] Apply pre-visibility Actions settings.
- [ ] Change visibility to public.
- [ ] Protect `main`.
- [ ] Enable immediate security features.
- [ ] Protect deploy/release environments.
- [ ] Set repository presentation metadata.
- [ ] Verify through logged-out and API checks.

### Requirement verification

- GitHub settings/API inspection confirms public visibility and protections.
- A test pull request cannot deploy, publish, or read protected secrets.
- Private vulnerability reporting and public Issues are accessible.
