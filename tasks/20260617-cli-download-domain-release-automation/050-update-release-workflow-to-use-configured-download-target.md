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

## Completion Notes

Added during completion on 2026-06-18.

Workflow dispatch run `27725996534` on `main` passed tests and all four matrix builds/smoke tests. The publish jobs were skipped because the run was `workflow_dispatch`, not a tag. Artifacts from that run were published manually to the testing domain with `publish-assets.sh`.

Later update added during completion on 2026-06-18:

Workflow dispatch run `27745015177` on `main` tested the uv-managed Python runtime changes. It passed test, Linux, `darwin-amd64`, and `darwin-arm64`, but failed `windows-amd64` archive smoke because the generated Windows launcher could not execute the packaged `python\Scripts\python.exe` path. The remaining workflow task is to fix that Windows launcher/runtime path issue, rerun the matrix, and then validate tag-triggered publish.

Final update added during completion on 2026-06-18:

Workflow dispatch run `27746631545` passed all tests and all four matrix build/archive-smoke jobs from `main`. Artifacts from that run were manually published to the testing download domain because `workflow_dispatch` intentionally skips tag-only publish jobs. The remaining workflow validation is a real tag-triggered publish path, including GitHub Release publication and OIDC upload through `publish-downloads`.
