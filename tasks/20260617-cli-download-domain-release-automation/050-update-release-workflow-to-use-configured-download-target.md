# Update Release Workflow To Use Configured Download Target

Update the CLI release GitHub Actions workflow so the matrix-built release artifacts publish to the configured download bucket/domain instead of hardcoded S3 values.

## Requirements checklist

- [x] Update `.github/workflows/release-crystal-lattice-cli.yml`.
- [x] Preserve the existing matrix build behavior.
- [x] Preserve tag/version validation.
- [x] Preserve GitHub Release publication.
- [x] Replace hardcoded S3 bucket/prefix/role with GitHub variables/secrets.
- [x] Upload a domain-correct installer during the workflow.
- [x] Write `latest.txt` for the release tag.
- [x] Upload all four expected release assets.
- [x] Invalidate CloudFront when a distribution ID is configured.
- [x] Document workflow variables/secrets in `deploy/aws-cli-downloads/README.md`.
- [x] Test workflow syntax locally.
- [x] Test workflow from the main-branch worktree on the testing domain.

Parent Task: `tasks/20260617-cli-download-domain-release-automation/000-main.md`

Depends On:

- `tasks/20260617-cli-download-domain-release-automation/030-add-domain-aware-installer-upload.md`
- `tasks/20260617-cli-download-domain-release-automation/040-add-github-oidc-role-and-vars-setup.md`

## Current Workflow Behavior

Current release workflow:

- runs tests
- validates tag version
- builds four platform archives via GitHub-hosted matrix runners
- smoke-tests each archive
- uploads artifacts
- publishes a GitHub Release
- publishes S3 downloads using hardcoded:

```text
bucket: crystal-lattice-downloads-874087778966
prefix: crystal-lattice-cli
role: arn:aws:iam::874087778966:role/CrystalLatticeReleaseS3Publisher
region: us-east-1
```

Keep the matrix. Only make the download target configurable.

## Expected Workflow Inputs

Use repository configuration:

```text
vars.AWS_REGION
vars.CLI_DOWNLOADS_BUCKET
vars.CLI_DOWNLOADS_PREFIX
vars.CLI_DOWNLOADS_BASE_URL
vars.CLI_DOWNLOADS_CLOUDFRONT_DISTRIBUTION_ID
secrets.CLI_DOWNLOADS_AWS_ROLE_TO_ASSUME
```

If CloudFront distribution ID is empty, skip invalidation rather than failing.

## Installer Generation In Workflow

The workflow should upload an installer whose default base URL is:

```text
${{ vars.CLI_DOWNLOADS_BASE_URL }}
```

Do not upload the source `scripts/install.sh` unchanged unless it already has the correct default for the configured target.

Prefer using `deploy/aws-cli-downloads/upload-installer.sh` or a shared helper so local and CI installer generation match.

## Documentation Requirements

Add README notes for:

- required GitHub variables
- required GitHub secret
- test profile workflow setup
- production profile workflow setup
- how to run/watch the workflow
- how to verify the publish job used the configured bucket/domain

## Testing Requirements

Local/static checks:

```bash
actionlint .github/workflows/release-crystal-lattice-cli.yml
```

If `actionlint` is unavailable, document that and use a fallback syntax/read-through check.

Main-worktree workflow testing:

- use the requested main-branch worktree
- push workflow changes to a branch or merge path that GitHub can see
- configure GitHub OIDC trust for the test ref
- run workflow manually if applicable:

  ```bash
  gh workflow run release-crystal-lattice-cli.yml \
    --repo dynamicprogrammingsolutions/crystal-lattice \
    --ref <test-ref>
  ```

For release-tag behavior, use a test version/tag only if approved. Record whether the test was:

- dry run/manual dispatch only
- test branch workflow run
- real release tag

Verify on the testing domain:

- `install.sh` has the testing base URL
- `latest.txt` points to expected tag
- all expected archives are present after release publish
- CloudFront invalidation was created

## Execution plan

Status: Approved

Complete this subtask as the first part of one coordinated release campaign
covering subtasks 050, 060, and 070. The campaign should create one new CLI
release, publish it to the testing download domain through the tag-triggered
workflow, validate it, promote the same GitHub Release to production, and then
restore GitHub's default release target to production.

Execution must start from a clean, synchronized `main` worktree. The current
local `main` and `origin/main` histories are divergent, so the release commit
and tag target must be resolved before any version bump or tag operation.

Use a new patch version because `crystal-lattice-cli-v0.1.0` already exists and
contains legacy asset names. The recommended release is `0.1.1`, subject to
human confirmation.

Before creating a release commit:

1. Reconcile the intended `main` history and verify the selected release commit
   is pushed to `origin/main`.
2. Update `application/python/pyproject.toml` to the approved new version and
   update version-specific public documentation where it represents the
   current release rather than an illustrative example.
3. Verify the source installer default, Git Bash support, and release workflow
   changes are present in the release commit.
4. Verify the test and production CloudFormation stacks and OIDC roles still
   exist and record their outputs.
5. Record the current production GitHub variables and confirm the
   `CLI_DOWNLOADS_AWS_ROLE_TO_ASSUME` secret exists.
6. Explicitly create or inspect the `cli-release` GitHub environment. It is
   currently not returned by the repository environments API. Configure it
   without an approval gate for this validation unless the user requests a
   protected release approval.

Validate the exact release commit before tagging:

1. Run `actionlint .github/workflows/release-crystal-lattice-cli.yml`.
2. Run the workflow's local fast test commands.
3. Trigger a `workflow_dispatch` run for the exact release commit on `main`.
4. Require the test job and all four build/archive-smoke jobs to pass.
5. Confirm both publish jobs are skipped because the run is not tag-triggered.

Prepare the testing publish target:

1. Run `configure-github-actions-vars.sh --profile test --dry-run`.
2. Apply `configure-github-actions-vars.sh --profile test`.
3. Read back all non-secret repository variables and confirm they point to:

   ```text
   https://download.crystallattice.dev.dynamicprogrammingsolutions.com/crystal-lattice-cli
   ```

4. Confirm the OIDC secret exists and the test role trusts the release-tag
   pattern.
5. Pause other CLI releases during the temporary repository-variable switch.

Create the real release through the corrected `release.sh` flow from subtask
060. Verify the tag-triggered run itself, not only the resulting files:

1. The event is `push` and the ref is the new CLI release tag.
2. Tag/version validation passes.
3. All four matrix jobs pass.
4. `Publish GitHub Release` passes and creates a release containing exactly the
   four current runtime archive names.
5. `Publish Downloads` passes using GitHub OIDC.
6. The testing bucket receives `install.sh`, `latest.txt`, and all four
   archives under the configured prefix.
7. The testing installer defaults to the testing base URL.
8. `latest.txt` contains the new release tag.
9. `smoke.sh --profile test --version <version>` passes.
10. Record the workflow run URL, release URL, S3 object evidence, and
    CloudFront invalidation ID.

Restore the production GitHub variables immediately after testing validation,
including on recoverable failure paths. Read them back and confirm the base URL,
bucket, distribution, prefix, and region point to production. Do not create
another tag merely to publish production; subtask 070 promotes the same GitHub
Release.

### Implementation decisions and open questions

- Requirement question: confirm the new public CLI version. Recommendation:
  `0.1.1`, because `0.1.0` already exists and cannot validate the current asset
  naming.
- Requirement question: decide which divergent `main` history is authoritative
  before execution. No release tag should be created until local `main` and
  `origin/main` are reconciled and the chosen release commit is pushed.
- Implementation decision: temporarily switch repository-level GitHub
  variables/secrets to the testing profile for the tag release, then restore
  production after validation. This preserves the existing workflow contract
  without introducing a second release workflow or profile encoded in the tag.
- Implementation decision: create or verify the `cli-release` environment
  explicitly before tagging so deployment behavior is known rather than
  relying on implicit environment creation.

### Documentation

- Update `deploy/aws-cli-downloads/README.md` with the exact test-target switch,
  read-back checks, production restoration command, and release recovery
  procedure.
- Update this task with the workflow run URL, GitHub Release URL, release tag,
  testing-domain smoke evidence, and restored production variable evidence.
- Update current-version user documentation only where the displayed version
  is intended to identify the latest release.

### Task checklist

- [x] Resolve the authoritative `main` history and establish a clean release worktree.
- [x] Obtain approval for the new release version.
- [x] Create and push the release commit on `main`.
- [x] Verify or create the `cli-release` GitHub environment.
- [x] Run local workflow validation and fast tests.
- [x] Run a green `workflow_dispatch` matrix on the exact release commit.
- [x] Switch GitHub release variables/secrets to the testing profile and verify them.
- [x] Create the release tag through subtask 060.
- [x] Verify the tag-triggered GitHub Release and OIDC download publication jobs.
- [x] Run and record testing-domain smoke verification.
- [x] Restore and verify production GitHub release configuration.
- [x] Record final evidence and mark this subtask complete.

### Requirement verification

- Workflow configuration requirements: `actionlint`, workflow inspection, and
  the exact-commit `workflow_dispatch` run.
- Matrix preservation: four successful target jobs in the tag-triggered run.
- GitHub Release publication: release URL plus four correctly named assets.
- Configured download publication: successful OIDC job plus GitHub variable
  read-back and testing S3/domain checks.
- Installer/latest/archive publication: testing-domain content inspection and
  `smoke.sh --profile test --version <version>`.
- CloudFront invalidation: recorded invalidation ID from the publication path.

### Additional implementation verification

- Verify the tag points to the same SHA as the pre-tag green dispatch run.
- Verify no release job used the production bucket while repository variables
  were intentionally set to testing.
- Verify production repository variables are restored after the campaign.

## Implementation Notes

- 2026-08-23: The user approved execution on the dedicated `main` worktree and
  approved version `0.1.1`.
- 2026-08-23: Local `main` and `origin/main` were verified at
  `a9abe07f1a22dd5cc86fe594e5397f5709bb64c7` before release changes began.
- 2026-08-23: Release preparation exposed a cancellation race where a request
  could be cancelled between early-cancellation inspection and live
  cancellation registration. Registration/cleanup are now synchronized, and
  active-provider cancellation tests wait for the provider's active marker.
- 2026-08-23: Local release validation passed:
  - `actionlint .github/workflows/release-crystal-lattice-cli.yml`
  - core fast suite: 465 passed, 26 deselected, 1 xfailed
  - application fast suite: 329 passed, 90 deselected
  - release/installer script tests: 12 passed
- 2026-08-23: Pre-tag workflow run `32661290455` built and smoke-tested
  all attempted archives, but GitHub rejected every `actions/upload-artifact`
  step because the repository artifact quota was full.
- 2026-08-23: Deleted 34 obsolete CLI workflow artifacts totaling about
  2.19 GiB. GitHub quota accounting did not refresh immediately, so the
  workflow was changed to upload tag-build archives directly to a draft GitHub
  Release. Manual dispatch now builds/smoke-tests without storing archives.
- 2026-08-23: Pre-tag run `32662372280` passed tests, draft-release preparation,
  and all four build/archive-smoke jobs on commit `7caaa64f`.
- 2026-08-23: Tag run `32666529964` created and published the `0.1.1` GitHub
  Release with all four current assets. `Publish Downloads` failed because the
  environment-scoped OIDC subject did not match the role's tag-ref trust.
- 2026-08-23: The reproducible fix restricts `cli-release` to
  `crystal-lattice-cli-v*` tags and adds the environment subject to the IAM
  trust. Future manual dispatch jobs do not attach the release environment;
  only the tag-gated AWS publish job remains environment-scoped.
- 2026-08-23: After the test role/environment update, rerunning only the failed
  job completed tag run `32666529964` successfully.
- 2026-08-23: Testing-domain full installer smoke passed for `0.1.1`;
  invalidation `IA4VIBTM5M4OY08L9325ML8WCK` completed for the workflow publish.

## Completion Notes

Added during completion on 2026-06-18.

Workflow dispatch run `27725996534` on `main` passed tests and all four matrix builds/smoke tests. The publish jobs were skipped because the run was `workflow_dispatch`, not a tag. Artifacts from that run were published manually to the testing domain with `publish-assets.sh`.

Later update added during completion on 2026-06-18:

Workflow dispatch run `27745015177` on `main` tested the uv-managed Python runtime changes. It passed test, Linux, `darwin-amd64`, and `darwin-arm64`, but failed `windows-amd64` archive smoke because the generated Windows launcher could not execute the packaged `python\Scripts\python.exe` path. The remaining workflow task is to fix that Windows launcher/runtime path issue, rerun the matrix, and then validate tag-triggered publish.

Final update added during completion on 2026-06-18:

Workflow dispatch run `27746631545` passed all tests and all four matrix build/archive-smoke jobs from `main`. Artifacts from that run were manually published to the testing download domain because `workflow_dispatch` intentionally skips tag-only publish jobs. The remaining workflow validation is a real tag-triggered publish path, including GitHub Release publication and OIDC upload through `publish-downloads`.

Completion update added on 2026-08-23:

- Released `crystal-lattice-cli-v0.1.1` from commit
  `7caaa64f31af94fca0d7b2a089c81d49d1c1ed0e`.
- Pre-tag workflow-dispatch run `32662372280` passed tests and all four
  build/archive-smoke jobs.
- Tag-triggered run `32666529964` passed tests, all four platform builds,
  GitHub Release publication, and OIDC publication to the testing download
  domain after the environment/IAM trust correction.
- GitHub Release:

  ```text
  https://github.com/dynamicprogrammingsolutions/crystal-lattice/releases/tag/crystal-lattice-cli-v0.1.1
  ```

- The workflow now uploads tag-build archives directly to a draft GitHub
  Release, avoiding GitHub Actions artifact-storage quota.
- Production GitHub variables/secrets were restored and verified after testing.
