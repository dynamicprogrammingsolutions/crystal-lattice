# Add GitHub OIDC Role And Variables Setup

Add scripts and CloudFormation needed for GitHub Actions to publish CLI release assets to the configured download bucket/domain using narrow OIDC permissions.

## Requirements checklist

- [x] Add `deploy/aws-cli-downloads/github-oidc-role.yaml`.
- [x] Add `deploy/aws-cli-downloads/create-github-oidc-role.sh`.
- [x] Add `deploy/aws-cli-downloads/configure-github-actions-vars.sh`.
- [x] Scope IAM role permissions to the downloads bucket/prefix and CloudFront distribution.
- [x] Trust GitHub Actions OIDC for release tags.
- [x] Support temporary branch trust for workflow testing from the main worktree when needed.
- [x] Configure GitHub variables/secrets via `gh`.
- [x] Document GitHub OIDC setup and variable/secret setup.
- [x] Test role creation against the testing stack.
- [x] Test GitHub variable/secret setup with `--dry-run`, then real setup when approved.

Parent Task: `tasks/20260617-cli-download-domain-release-automation/000-main.md`

Depends On: `tasks/20260617-cli-download-domain-release-automation/020-add-download-domain-infra-bootstrap.md`

## Required GitHub Configuration

The release workflow should read values like:

```text
vars.CLI_DOWNLOADS_BUCKET
vars.CLI_DOWNLOADS_PREFIX
vars.CLI_DOWNLOADS_BASE_URL
vars.CLI_DOWNLOADS_CLOUDFRONT_DISTRIBUTION_ID
vars.AWS_REGION
secrets.CLI_DOWNLOADS_AWS_ROLE_TO_ASSUME
```

Name choices can be adjusted during implementation, but they should be CLI-download-specific to avoid colliding with static site deployment variables.

## OIDC Trust Requirements

The role must support release tag workflow runs:

```text
repo:dynamicprogrammingsolutions/crystal-lattice:ref:refs/tags/crystal-lattice-cli-v*
```

For workflow testing, support an explicit branch trust option, for example:

```bash
--github-branch main
```

or:

```bash
--github-ref-pattern refs/heads/main
```

Document how to temporarily trust a test branch and restore trust afterward.

## Permission Scope

The role should allow only:

- `s3:PutObject`
- `s3:PutObjectTagging` if needed
- `s3:GetObject` if the workflow verifies uploads
- `s3:ListBucket` scoped to the configured prefix
- `cloudfront:CreateInvalidation` for the configured distribution

Do not grant broad account-wide S3 or CloudFront permissions.

## Documentation Requirements

`deploy/aws-cli-downloads/README.md` must include:

- ready-to-use test role setup command
- ready-to-use production role setup command
- dry-run GitHub variables/secrets command
- apply GitHub variables/secrets command
- branch testing guidance
- release-tag trust explanation

## Testing Requirements

Run against testing stack:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/create-github-oidc-role.sh \
  --profile test \
  --github-owner dynamicprogrammingsolutions \
  --github-repo crystal-lattice
```

Preview GitHub configuration:

```bash
deploy/aws-cli-downloads/configure-github-actions-vars.sh \
  --profile test \
  --repo dynamicprogrammingsolutions/crystal-lattice \
  --dry-run
```

When approved, apply it:

```bash
deploy/aws-cli-downloads/configure-github-actions-vars.sh \
  --profile test \
  --repo dynamicprogrammingsolutions/crystal-lattice
```

Verify:

- role output ARN is present
- repository variables match testing stack outputs
- repository secret is set
- workflow can assume the role from the allowed ref during a test run

## Completion Notes

Added during completion on 2026-06-18.

Created testing OIDC role:

```text
arn:aws:iam::874087778966:role/CrystalLatticeCliDownloadsGitHubDeployRoleTest
```

Configured GitHub variables/secrets for `dynamicprogrammingsolutions/crystal-lattice`. The role currently trusts both release tags and `refs/heads/main` to support the requested main-branch workflow testing. Remove or narrow the branch trust after release validation if desired.
