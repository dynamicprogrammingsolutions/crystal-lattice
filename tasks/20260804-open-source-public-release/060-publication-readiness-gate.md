# Perform The Public Repository Readiness Gate

Produce a single evidence-backed go/no-go decision before changing repository
visibility.

## Requirements checklist

- [ ] Mandatory subtasks `010` through `050` are complete with evidence.
- [ ] A clean clone passes the agreed minimum build/test/documentation checks.
- [ ] The root presentation, license, support, security, and issue paths are coherent.
- [ ] No unresolved critical legal, security, privacy, cost, or newcomer-understanding blocker remains.
- [ ] Existing GitHub Actions logs/artifacts have been reviewed for public exposure.
- [ ] The owner explicitly approves the candidate commit and publication timing.
- [ ] A rollback and collaborator communication plan exists for any required history rewrite or publication problem.

Parent Task: tasks/20260804-open-source-public-release/000-main.md
Depends On: tasks/20260804-open-source-public-release/010-sensitive-data-and-history-release-gate.md
Depends On: tasks/20260804-open-source-public-release/020-claude-tools-license-and-provenance-restoration.md
Depends On: tasks/20260804-open-source-public-release/030-minimum-public-documentation-and-support.md
Depends On: tasks/20260804-open-source-public-release/040-minimum-ci-and-automation-hardening.md
Depends On: tasks/20260804-open-source-public-release/050-lean-root-cleanup-and-archive.md

## Release gate

The result must be one of:

- `GO`: no unresolved mandatory blocker; proceed to task `070`.
- `NO-GO`: list blocking evidence and return to the owning subtask.

Optional tasks `110` through `140` cannot cause `NO-GO` unless new evidence
shows that a supposedly optional item is actually a legal, security, cost, or
major comprehension risk.

## Current audit findings

### Predecessor and branch state

- Mandatory tasks `010` through `050` are marked complete in the current
  `develop` task tree.
- Current committed branch tips on August 23, 2026:
  - `main`: `7caaa64f31af94fca0d7b2a089c81d49d1c1ed0e`
  - `develop`: `69a4be86`
  - merge base: `a9abe07f1a22dd5cc86fe594e5397f5709bb64c7`
- `main` has two commits not in `develop`; `develop` has twenty commits not in
  `main`.
- Local `develop` is ten commits ahead of `origin/develop`.
- The `develop` worktree has unrelated uncommitted changes in:
  - `mobile/crystal-lattice-control-rn/package-lock.json`
  - `tasks/20260823-frontend-connection-lifecycle/020-shared-connection-lifecycle-controller.md`
- The `main` worktree is clean.
- A publication candidate therefore cannot be represented by either current
  branch tip. It must combine the committed tips in a separate clean worktree
  without including either worktree's uncommitted state.

### Current GitHub state

- `dynamicprogrammingsolutions/crystal-lattice` is private with `main` as the
  default branch.
- Issues are enabled, Discussions and Wiki are disabled, and GitHub detects
  Apache-2.0.
- Repository description, homepage, and topics are unset.
- `main` is not protected. Rulesets currently return the private-plan
  availability error recorded by task `070`.
- GitHub Actions currently:
  - allows all actions;
  - does not require full-SHA pinning;
  - gives the default workflow token write permission;
  - allows Actions to approve pull requests.
- Environment `cli-release` exists without protection rules or a deployment
  branch policy. `production-sites` is not currently present.
- Dependency/security endpoints are disabled, unavailable, or inaccessible in
  the current private configuration and remain task `070` work.

### Workflow and hosted-output state

- Four active workflows exist:
  - `Public CI`: push to `main`/`develop`, pull request, or manual dispatch;
  - `Deploy Static Sites`: push to `main` or manual dispatch;
  - `iOS TestFlight`: manual dispatch only;
  - `Release crystal-lattice-cli`: manual dispatch or CLI release tag.
- Advancing `main` to the publication candidate will therefore intentionally
  start Public CI and static-site deployment, but must not start TestFlight or
  CLI publication.
- At audit time, CLI release run `32662372280` was still active on current
  `main`; task `060` must wait for it and review any resulting release,
  artifact, and log changes before freezing a candidate.
- Public CI run `32662361524` failed on current `main`. The repository security
  validator rejected `contents: write` in the new CLI workflow jobs
  `prepare-release` and `build`.
- This permission/validator mismatch is a current publication blocker. Task
  `060` must not weaken the validator or broaden the allowlist merely to make
  the gate pass; the owning CLI/release automation work must prove and apply
  the least-privilege correction.
- The latest Public CI run on `origin/develop`, `32620462147`, passed repository,
  frontend, and landing/docs jobs but failed Python unit tests. The hosted
  failed-step log was unavailable through the CLI and the failure must be
  reproduced or superseded on the candidate.
- Recent static-site runs have included build failures. The exact candidate
  must pass the static-site build locally before task `070` permits the
  expected deployment-triggering `main` push.
- The current Actions artifact inventory is empty.
- One published release exists, `crystal-lattice-cli-v0.1.0`, with four
  platform archives. The active CLI run may change this inventory.

## Execution plan
Status: Approved

### Phase 1: Clear pre-candidate blockers and freeze inputs

Wait for every active workflow run to finish. Record its conclusion and inspect
new logs, artifacts, draft/published releases, deployments, or external
publication effects.

Resolve or route each failed mandatory check before constructing the final
candidate:

- CLI workflow/security-validator permission mismatch on current `main`;
- Python unit failure on current remote `develop`;
- static-site build failures relevant to the current tree.

Task `060` is a release gate, not the owner of substantive CI, provider,
release, or deployment behavior. If a failure requires code or workflow
changes, declare the candidate temporarily `NO-GO`, return the defect to the
owning task, and restart the gate after its fix is committed.

Fetch and prune remote refs. Record:

- local and remote `main`/`develop` SHAs;
- unique commit lists in both directions;
- tags, open pull-request refs, releases, active runs, artifacts, and
  deployments;
- worktree status for every source branch.

Review the ten currently unpushed `develop` commits and the two current
main-only commits as an explicit candidate inventory. Stop for owner direction
if any commit is experimental, private, unfinished, or not intended for the
initial public repository.

Freeze the selected source SHAs. Any later source-branch movement invalidates
the candidate and requires reconstruction.

### Phase 2: Construct the exact publication candidate

Create a dedicated clean worktree and temporary branch from the latest intended
`origin/main`, for example:

```text
release/open-source-publication-candidate
```

Merge the exact approved committed `develop` tip into that branch with an
ordinary merge commit. Do not:

- copy either worktree's uncommitted files;
- stash/pop unrelated work into the candidate;
- rewrite or squash history;
- resolve an unexpected conflict by guessing;
- push the candidate or update remote `main` during this task.

Expected simple conflicts may be resolved only when both sides' intent is clear.
A conflict affecting release behavior, security policy, generated roadmap
state, public documentation authority, or deployment configuration is a
blocking surprise requiring owner direction.

Record:

- source `main` SHA;
- source `develop` SHA;
- merge/candidate SHA;
- merge conflict list and resolution evidence;
- candidate tree status.

The exact merge commit becomes the only candidate evaluated by the remaining
phases.

### Phase 3: Revalidate predecessor evidence and sensitive-data boundaries

Build a concise evidence matrix for tasks `010` through `050`:

- requirement outcome;
- completion commit(s);
- verification already performed;
- any accepted historical finding;
- whether later commits could invalidate that evidence.

Create an isolated clone of the candidate using `--no-local`, check out the
exact candidate SHA, and provide no repository `.env`, signing identity,
provider credentials, cloud credentials, or local runtime state.

Repeat publication-sensitive checks:

- pinned Gitleaks and TruffleHog history scans over all refs intended to become
  public;
- current-tree scans on the candidate;
- targeted checks for credentials, private keys, runtime sessions, personal
  paths, scanner output, backups, and generated secrets;
- comparison with task `010`'s accepted historical baseline;
- AGI archive hash and location;
- Claude Tools license/provenance consistency;
- no tracked `.crystal` sessions or machine-local Xcode environment files.

No history rewrite is permitted. A newly exposed credential causes `NO-GO`,
credential revocation/rotation, and return to the owning task.

### Phase 4: Run the complete minimum public-CI boundary

Run the exact candidate from the isolated clone using the same boundaries as
the four `Public CI` checks:

1. Repository checks
   - workflow YAML parsing;
   - actionlint;
   - immutable action references;
   - `scripts/check_github_actions_security.py`;
   - JSON/TOML manifest parsing;
   - `git diff --check`.
2. Python unit tests
   - core non-integration suite;
   - application non-integration/non-Docker suite.
3. Frontend package tests
   - frontend SDK;
   - React bindings;
   - shared React Native components.
4. Landing and docs build
   - clean landing dependency install and production build;
   - documentation requirements;
   - documentation preparation;
   - non-strict MkDocs build.

Also verify:

- `test/repo_test_env.py` works with no root `.env`;
- archived diagnostics are not collected as tests;
- active workflow trigger/permission/environment boundaries;
- the iOS TestFlight workflow remains manual-only;
- the CLI workflow remains manual/tag-only;
- the static-site workflow build succeeds before its later expected deployment
  on `main`.

Previously documented provider-package baseline failures do not become
publication blockers unless the candidate changes their behavior or the public
quickstart depends on them. Reproduce and classify any such failure rather than
weakening tests.

Any mandatory candidate check failure is `NO-GO`; fix it in its owning task,
rebuild the merge commit, and rerun all candidate checks.

### Phase 5: Perform the anonymous-developer presentation review

Review the isolated clone as a first-time developer with no maintainer context:

- repository purpose and early-development status;
- installation and first-success commands;
- architecture and package navigation;
- Apache-2.0 license, licensing notes, and notice;
- contribution workflow;
- support route;
- private security-reporting route;
- issue forms and pull-request template;
- production privacy/support/marketing URLs;
- historical archive labeling;
- absence of obsolete root plans and scratch files.

Validate all current local Markdown links and the public website links relevant
to repository, support, privacy, and mobile distribution.

Do not require a logged-out GitHub clone while the repository is still private;
task `080` owns the real anonymous/public clone after visibility changes. This
phase is a clean, credential-free simulation of that experience.

Classify findings:

- legal, security, privacy, unexpected-cost, broken first-use, or major
  comprehension issue: blocker;
- cosmetic, optional governance, expanded metadata, or later information
  architecture improvement: defer to `110` through `150`.

### Phase 6: Review GitHub-hosted exposure and task `070` readiness

Inventory and inspect all workflow runs, logs, artifacts, releases, and
deployments created since task `010`, including completed runs that were active
when this Draft was written.

Download and scan accessible logs and artifacts without recording secret
values. Trace each release asset to its source commit. Report expired or
unavailable output as unavailable rather than clean.

Confirm no workflow is active before the final gate decision.

Record the exact task `070` settings delta:

- Actions default token: write → read;
- Actions PR approval: enabled → disabled;
- allowed actions: all → selected reviewed repositories;
- full-SHA enforcement: disabled → enabled;
- create/protect `production-sites`;
- protect `cli-release`;
- public visibility;
- active `main` ruleset after public visibility enables it;
- dependency/security features;
- repository description, homepage, and topics.

Model expected effects of advancing `main` to the candidate:

- expected: Public CI and static-site workflow;
- forbidden without separate action: TestFlight run, CLI release, release tag,
  or new provider/cloud spend.

The gate may issue `GO` while these settings remain unapplied only because task
`070` owns the immediate visibility transition. It may not issue `GO` if the
settings are unavailable without an accepted safe fallback, the handoff is
ambiguous, or an active workflow/deployment prevents a controlled transition.

### Phase 7: Prepare rollback and collaborator communication

Record a concise task-`070` rollback/incident procedure:

- pause or cancel unexpected workflows;
- restore private visibility if GitHub permits and the owner chooses it;
- disable affected workflows or environments;
- revoke/rotate any newly exposed credential;
- preserve evidence without committing secret values;
- notify known collaborators and early adopters through the agreed private
  channel;
- route public reports through `SECURITY.md` or `SUPPORT.md`;
- rerun task `060` after any corrective commit.

Explicitly state that returning a repository to private does not erase content
already copied while public. Prevention remains the primary control.

No history rewrite is planned or authorized. If future evidence would require
one, stop and request a new owner decision rather than treating rollback as
rewrite permission.

Prepare the short initial collaborator message with:

- exact publication timing;
- approved candidate SHA;
- early-development expectations;
- issue/support/security routes;
- request not to announce broadly until task `080` completes.

Do not send the message or publish an announcement in task `060`.

### Phase 8: Record the decision and obtain owner approval

Write a compact evidence table and one decision:

- `GO`: every mandatory check passes, no active run or unresolved blocker
  remains, and task `070` has an exact executable handoff;
- `NO-GO`: list each blocker, owner, and evidence, and return it to the
  appropriate predecessor or release task.

For a proposed `GO`, present:

- exact candidate SHA;
- source branch SHAs;
- verification commands/results;
- accepted historical findings;
- deferred non-blocking findings;
- expected `main` push workflow effects;
- rollback/communication procedure;
- proposed publication date and time.

Pause for explicit owner approval of both the candidate SHA and publication
timing. The task cannot complete and task `070` cannot begin before that
confirmation.

After approval, freeze merges and direct pushes. Any commit, ref movement,
workflow/configuration change, or newly discovered hosted output invalidates
the `GO` until the affected gate checks are rerun.

### Implementation decisions and open questions

- Recommended candidate composition: latest intended `origin/main` plus every
  reviewed committed change on local `develop`, merged in a dedicated clean
  worktree.
- Publication approval is tied to the exact merge commit, not merely a branch
  name.
- Worktree-local changes are excluded.
- The candidate is not pushed and remote `main` is not changed by task `060`.
- Task `060` reports or routes substantive blockers; it does not relax security
  policy or absorb unrelated repairs.
- The current CLI workflow/security-validator mismatch must be fixed before
  `GO`.
- The current remote `develop` Python failure must be reproduced or superseded
  before `GO`.
- The first public release need not be a tagged software release.
- Optional cleanup remains optional unless evidence reclassifies its risk.
- No history rewrite is authorized.
- Owner approval of the exact SHA and timing is intentionally deferred to the
  final gate step.

### Documentation

- Record branch inputs, evidence, findings, and the final go/no-go decision in
  this task's Implementation Notes and Completion Notes.
- Keep secret values, private correspondence, raw scanner output, and
  credential paths out of committed files.
- Do not create a marketing announcement as part of this gate.
- Do not update the roadmap unless the owner separately gives the explicit
  roadmap-status instruction from the main task.

### Task checklist

- [ ] Wait for active workflows and resolve/route current mandatory failures.
- [ ] Freeze and approve source branch/commit inventory.
- [ ] Construct the clean publication candidate merge commit.
- [ ] Confirm predecessor completion and later-change validity.
- [ ] Repeat sensitive-data and history scans against publication refs.
- [ ] Run all four minimum Public CI boundaries in an isolated clone.
- [ ] Review public-facing repository, support, security, privacy, and issue paths.
- [ ] Review Actions logs/artifacts/releases/deployments since task `010`.
- [ ] Prepare the exact task `070` settings and expected-workflow handoff.
- [ ] Record rollback and collaborator communication procedures.
- [ ] Present candidate SHA, evidence, decision, and timing for owner approval.
- [ ] Declare final `GO` or `NO-GO`.

### Requirement verification

- Predecessor completion: completion notes and commits for `010` through `050`,
  with later invalidation review.
- Clean-clone readiness: isolated candidate checkout passes the four Public CI
  boundaries without local credentials or untracked configuration.
- Public presentation: first-time-developer walkthrough, link validation, and
  website-route checks.
- Critical-risk gate: repeat history/current-tree scans, legal/license review,
  workflow cost/trigger review, and blocker classification.
- Hosted exposure: run/log/artifact/release/deployment inventory and scans.
- Owner approval: explicit confirmation of exact candidate SHA and publication
  date/time.
- Rollback/communication: written controlled-transition procedure suitable for
  task `070`.
- Only a recorded owner-approved `GO` authorizes task `070`.

### Additional implementation verification

- Source worktrees remain unchanged except for this task record.
- No uncommitted source-worktree file enters the candidate.
- Candidate merge parents match the recorded source SHAs.
- Candidate worktree and clean clone are clean at verification time.
- No workflow is active at final decision time.
- GitHub settings and workflow inventory are refreshed immediately before
  owner approval.
- No remote branch, tag, release, visibility, environment, rule, secret, or
  repository setting is changed during task `060`.

## Implementation Notes

### August 23, 2026: execution started and paused before source freeze

The owner approved this plan and instructed execution to stop wherever ongoing
work on `main` prevents a step from completing safely.

Read-only Phase 1 checks established:

- No GitHub Actions run is active or queued.
- CLI release run `32662372280` completed successfully at
  `7caaa64f31af94fca0d7b2a089c81d49d1c1ed0e`.
  - Test, draft-release preparation, and all four platform builds succeeded.
  - Final GitHub Release publication and downloads publication were skipped as
    intended for the draft path.
  - The REST release inventory still exposes only the published
    `crystal-lattice-cli-v0.1.0` release.
  - The Actions artifact inventory remains empty.
- The release log contained normal GitHub redaction markers and credential
  variable-name references. A value-shape scan found no unredacted AWS access
  key, GitHub token, or PEM private-key form. Masked values were not treated as
  evidence that their underlying value was reviewed.
- Public CI run `32662361524` remains failed at current `main` because
  `scripts/check_github_actions_security.py` rejects `contents: write` in CLI
  workflow jobs `prepare-release` and `build`.
- Remote refs remain:
  - `main`: `7caaa64f31af94fca0d7b2a089c81d49d1c1ed0e`
  - `develop`: `237e2e44ea8b13dfaac07bf646f9cd08df07d2e1`
- Local `develop` remains at `69a4be86b7602e050285362ac09f5cdeb4df39da`,
  ten commits ahead of remote `develop`.
- Three older open pull requests target `develop`; none is merged into or
  automatically included in the candidate.
- Concurrent uncommitted work now exists in the `develop` worktree beyond the
  two paths recorded during planning, including roadmap generator,
  specification, test, CSV, and generated Markdown changes. All worktree-local
  changes remain outside the candidate scope.

Execution is paused before fetching/freezing source SHAs or constructing the
candidate because the owner reports that work on `main` is still in progress.
The current clean local `main` worktree and unchanged remote SHA do not override
that explicit coordination state.

Resume condition:

- the owner confirms that the current `main` work is finished;
- all intended `main` commits are committed and, if they are meant to be part
  of the publication candidate, available in the selected source ref;
- no workflow is active or queued.

On resume, refresh all branch, run, release, artifact, deployment, pull-request,
and settings inventories before selecting source SHAs. No candidate branch,
worktree, merge, push, release, visibility change, setting change, or roadmap
update was made during this partial execution.

### August 24, 2026: resumed and stopped on mandatory Public CI blocker

The owner confirmed that work on `main` had finished, so Phase 1 resumed with a
fresh read-only inventory.

Refreshed source state:

- local and remote `main`:
  `9626e546cd23bcac8d8000de233bca1e51b5e5ea`
- local `develop`:
  `eb51b2a3ce969e798ca147b87bbf042358c1b7a5`
- remote `develop`:
  `237e2e44ea8b13dfaac07bf646f9cd08df07d2e1`
- local `develop` is eleven commits ahead of remote `develop`;
- `main` has four commits not in `develop`, and `develop` has twenty-one
  commits not in `main`;
- no workflow run was active or queued.

The completed CLI work also changed the hosted release inventory:

- tag-triggered run `32666529964` completed successfully;
- `crystal-lattice-cli-v0.1.1` is published with the four expected
  `crystal-lattice-python-runtime-v0.1.1` platform archives;
- no retained Actions artifact is present.

Mandatory Public CI remains red on the exact current `main` commit:

- run: `32668516622`
- Python unit tests: passed
- frontend package tests: passed
- landing and docs build: passed
- repository checks: failed

The repository check fails deterministically both in the hosted run and from
the clean `main` worktree:

```text
.github/workflows/release-crystal-lattice-cli.yml:73:
unauthorized write permission 'contents' in job 'prepare-release'
.github/workflows/release-crystal-lattice-cli.yml:98:
unauthorized write permission 'contents' in job 'build'
```

The security validator currently authorizes `contents: write` only for the
final `publish` job. The release workflow grants that authority earlier so the
`prepare-release` job can create a draft release and each matrix `build` job can
upload directly to it. Reconciling this design requires an explicit
least-privilege decision; task `060` must not make the check pass by silently
broadening the allowlist.

Owning work:

- `tasks/20260617-cli-download-domain-release-automation/050-update-release-workflow-to-use-configured-download-target.md`

That subtask is recorded complete, so correcting it requires an authorized
post-completion follow-up or another explicitly selected owning task.

Interim gate result: `NO-GO`.

Execution stopped before:

- freezing publication source SHAs;
- creating a candidate branch or worktree;
- merging `main` and `develop`;
- running candidate scans or clean-clone validation;
- changing any remote ref, release, repository setting, visibility, roadmap, or
  workflow.

Resume condition: the CLI release workflow and Actions security validator have
an explicitly reviewed least-privilege contract, the exact correction is
committed, and Public CI is green on the resulting intended `main` source.

### August 24, 2026: CLI blocker corrected and gate resumed

The owner authorized reopening the completed CLI release workflow task and
continuing this gate.

The correction:

- removed `contents: write` from the release matrix;
- removed the separate privileged draft-release preparation job;
- uses the repository's existing SHA-pinned upload/download artifact actions
  for a one-day tag-build handoff;
- gives only the protected final GitHub Release publisher
  `contents: write`;
- keeps manual dispatch builds free of artifact storage and publication.

Owning task evidence:

- `tasks/20260617-cli-download-domain-release-automation/050-update-release-workflow-to-use-configured-download-target.md`
- correction delivery commit:
  `1ea4e6f030001e67ebd70e7cbff78c27f8aed65e`
- owning-task evidence commit:
  `0da2d938a7545795f9870dea1d6e1f07fa0e3618`

Hosted verification:

- Public CI run `32697863899` passed all four required jobs on the correction
  delivery commit.
- Public CI run `32698271116` passed all four required jobs on the final
  owning-task evidence commit.
- No release workflow, TestFlight workflow, release tag, or download
  publication was triggered by either correction push.

The interim `NO-GO` for this blocker is cleared. The gate may now refresh and
freeze source SHAs, construct the publication candidate, and continue the
remaining checks.

### August 24, 2026: publication candidate merge constructed

Frozen source commits:

- `main`: `0da2d938a7545795f9870dea1d6e1f07fa0e3618`
- `develop`: `a2a17d579eedcaa17e82052e4eba9802e5ad6175`

The isolated candidate worktree is:

```text
/Users/ferenci84/Dev/Mine/ai-agent-platform-publication-candidate
```

Application, bridge, mobile, documentation, workflow, test, and task changes
merged automatically. The merge stopped on conflicts in only:

- `roadmaps/open-source-and-ios-release.csv`
- `roadmaps/open-source-and-ios-release.md`

The owner explicitly selected the `develop` authored CSV as authoritative and
instructed that generated Markdown must not be manually merged.

Resolution evidence:

- the resolved CSV is the exact `develop` version;
- it preserves the newer `main_task` and `completed_at` schema;
- it already contains the completed CLI `050`, `060`, and `070` rows and their
  August 23, 2026 completion dates;
- Markdown was regenerated from the resolved CSV;
- generated Markdown is byte-for-byte identical to the pre-merge `develop`
  generated Markdown;
- no conflict marker remains;
- roadmap check mode passed;
- all `35` roadmap tests passed;
- no Google Sheet read, write, or synchronization was performed.

Roadmap generation currently loads the Sheets registry even for local-only
generation, so a clean worktree without the ignored `roadmaps/.env` cannot run
the named generator command. The merge used the existing ignored environment
file by explicit path without copying it into the candidate or contacting
Google. This is recorded as a non-blocking roadmap-tooling limitation because
the public CI boundary does not invoke roadmap generation and public roadmap
documentation already describes its optional local configuration. It may be
reassessed as post-publication tooling work if early contributors need to edit
the roadmap.

### August 24, 2026: critical npm advisory remediation

The credential-free candidate install reported critical npm advisories and the
gate treated them as blockers until their dependency paths and supported fixes
were understood.

Findings:

- root `shell-quote` `1.8.3` was reachable through
  `react-native` → `react-devtools-core`;
- mobile and desktop also locked `shell-quote` `1.8.3`;
- mobile and desktop React Native CLI `20.0.0` locked
  `fast-xml-parser` `4.5.3`;
- root Vitest `1.6.1` has a critical advisory for its optional UI server.

Remediation:

- updated root `shell-quote` to `1.10.0` within the existing parent range;
- updated the three explicitly pinned mobile and desktop React Native community
  CLI packages from `20.0.0` to the supported same-major `20.2.0`;
- refreshed both app lockfiles to `fast-xml-parser` `5.11.0` and
  `shell-quote` `1.10.0`;
- did not change React Native, React Native macOS, native projects, application
  runtime APIs, or release identifiers.

Verification:

- root, mobile, and desktop `npm audit --omit=dev --package-lock-only` now
  report zero critical advisories;
- root shared package tests passed: `313`, `20`, and `7` tests;
- mobile clean install and React Native configuration passed;
- all `119` mobile Jest tests passed;
- desktop clean install and React Native configuration passed;
- all `105` desktop Jest tests passed.

The remaining full-audit Vitest critical advisory is not a publication blocker:
it applies to the optional Vitest UI server, while repository scripts and
Public CI use non-server `vitest run`. A major Vitest/test-stack upgrade is
deferred to expanded dependency-security work.

Remaining high advisories are transitive React Native, Metro, and related
build/development tooling. They are not loaded by the shipped mobile JavaScript
application as server endpoints, and public pull-request CI has a read-only
token, no repository secrets, and no protected environment. They remain
visible for task `130` dependency-security prioritization rather than being
silently treated as resolved.
