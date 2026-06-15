# GitHub Actions AWS Deploy

Add a GitHub Actions workflow that builds both static sites and deploys them to AWS using narrow GitHub OIDC credentials.

## Requirements checklist

- [x] Create or document an AWS IAM role trusted by GitHub Actions OIDC for this repository and branch.
- [x] Scope IAM permissions to only the two S3 buckets and two CloudFront distributions.
- [x] Add user-run script/documentation for GitHub Actions variables/secrets for bucket names, distribution IDs, region, public URLs, and role ARN.
- [x] Add a workflow that builds the Astro landing site.
- [x] Add a workflow step that prepares and builds the MkDocs site.
- [x] Deploy both build outputs to S3 with `--delete`.
- [x] Upload generated docs Markdown files and LLM text files with explicit inline-readable content types in S3.
- [x] Invalidate both CloudFront distributions.
- [x] Keep the disabled GitHub Pages workflow disabled or remove it after confirming the AWS path is live.

Parent Task: `tasks/20260614-aws-static-sites-docs-deployment/000-main.md`

Depends On: `tasks/20260614-aws-static-sites-docs-deployment/020-plugin-docs-and-llm-access.md`

Depends On: `tasks/20260614-aws-static-sites-docs-deployment/030-aws-static-hosting-infra.md`

Depends On: `tasks/20260614-aws-static-sites-docs-deployment/035-docs-site-layout-cleanup.md`

## Repo References

- `.github/workflows/publish-docs.yml.disabled:1-53` is an old disabled GitHub Pages workflow. It is useful as a reminder that docs builds need Python setup and `mkdocs build --strict`, but deployment should target AWS instead of GitHub Pages.
- `landing_page/package.json` has `yarn build` for the Astro site.
- `docs_site/requirements.txt` is the docs dependency source.
- The docs workflow should use `python docs_site/scripts/build_mkdocs_site.py`, which prepares MkDocs inputs, builds `docs_site/dist/`, and refreshes generated reference Markdown under `docs/reference/`.

## AWS OIDC Notes

Use GitHub Actions OIDC. Do not create long-lived AWS access keys unless the user explicitly requests that fallback.

The IAM trust policy should be limited to the actual repository and deployment branch. Example conditions to adapt:

```json
{
  "StringEquals": {
    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
  },
  "StringLike": {
    "token.actions.githubusercontent.com:sub": "repo:dynamicprogrammingsolutions/crystal-lattice:ref:refs/heads/main"
  }
}
```

The deploy role should only need:

- `s3:ListBucket` on both deployment buckets.
- `s3:PutObject` and `s3:DeleteObject` on both bucket object ARNs.
- `cloudfront:CreateInvalidation` on the two distributions, if resource scoping is available in the policy used.

## GitHub Configuration

Store these as GitHub repository variables or secrets:

- `AWS_ROLE_TO_ASSUME`
- `AWS_REGION`
- `LANDING_BUCKET`
- `DOCS_BUCKET`
- `LANDING_CLOUDFRONT_DISTRIBUTION_ID`
- `DOCS_CLOUDFRONT_DISTRIBUTION_ID`
- `PUBLIC_CRYSTAL_LATTICE_SITE_URL`
- `PUBLIC_CRYSTAL_LATTICE_DOCS_URL`

The values are not credentials, but `AWS_ROLE_TO_ASSUME` is often kept as a secret or environment variable by convention.

The public URL values are build-time configuration. They default to the future
production domains in code (`https://crystallattice.dev` and
`https://docs.crystallattice.dev`), so the current temporary AWS testing
workflow should set:

- `PUBLIC_CRYSTAL_LATTICE_SITE_URL=https://crystallattice.dev.dynamicprogrammingsolutions.com`
- `PUBLIC_CRYSTAL_LATTICE_DOCS_URL=https://docs.crystallattice.dev.dynamicprogrammingsolutions.com`

## Workflow Shape

Create `.github/workflows/deploy-static-sites.yml`.

Triggers:

```yaml
on:
  workflow_dispatch: {}
  push:
    branches:
      - main
    paths:
      - "landing_page/**"
      - "docs/**"
      - "plugins/docs/**"
      - "docs_site/**"
      - ".github/workflows/deploy-static-sites.yml"
```

Permissions:

```yaml
permissions:
  contents: read
  id-token: write
```

Core deployment commands:

```bash
aws s3 sync landing_page/dist/ "s3://${LANDING_BUCKET}/" --delete
aws cloudfront create-invalidation \
  --distribution-id "${LANDING_CLOUDFRONT_DISTRIBUTION_ID}" \
  --paths "/*"

aws s3 sync docs_site/dist/ "s3://${DOCS_BUCKET}/" --delete
find docs_site/dist -name '*.md' -print0 | while IFS= read -r -d '' file; do
  key="${file#docs_site/dist/}"
  aws s3 cp "$file" "s3://${DOCS_BUCKET}/${key}" \
    --content-type "text/plain; charset=utf-8" \
    --metadata-directive REPLACE
done
for file in docs_site/dist/llms.txt docs_site/dist/llms-full.txt; do
  test -f "$file" || continue
  key="${file#docs_site/dist/}"
  aws s3 cp "$file" "s3://${DOCS_BUCKET}/${key}" \
    --content-type "text/plain; charset=utf-8" \
    --metadata-directive REPLACE
done
aws cloudfront create-invalidation \
  --distribution-id "${DOCS_CLOUDFRONT_DISTRIBUTION_ID}" \
  --paths "/*"
```

The second docs upload pass is required so generated Markdown and LLM text files
open inline in browsers instead of downloading. Apply it to:

- `docs_site/dist/**/*.md`
- `docs_site/dist/llms.txt`
- `docs_site/dist/llms-full.txt`

Use `text/plain; charset=utf-8` rather than `text/markdown` for widest browser
inline rendering behavior.

## Validation

Run the workflow manually with `workflow_dispatch`.

Check:

- AWS credentials are assumed through OIDC.
- No AWS access key ID or secret access key is stored in GitHub.
- The Astro and MkDocs build steps receive `PUBLIC_CRYSTAL_LATTICE_SITE_URL`
  and `PUBLIC_CRYSTAL_LATTICE_DOCS_URL`.
- The landing build completes.
- The docs build uses `python docs_site/scripts/build_mkdocs_site.py`.
- Generated Markdown and LLM text files in S3 have `Content-Type: text/plain; charset=utf-8`.
- S3 sync deletes removed files.
- CloudFront invalidations are created for both distributions.

## Execution plan

Added during completion after user approval.

Implement GitHub Actions deployment with AWS OIDC while keeping major mutating
GitHub operations explicit and user-run. The workflow and scripts should be
committed, but creating/updating GitHub variables, secrets, and workflow runs
should not happen automatically during this task unless the user explicitly asks.

### User-run mutation boundary

This task may add files, templates, scripts, and documentation. It may validate
templates and script syntax locally. It may use AWS CLI for read-only inspection
and CloudFormation template validation.

Do not automatically perform these actions:

- Set GitHub repository variables.
- Set GitHub repository secrets.
- Trigger the GitHub Actions workflow.
- Create long-lived AWS access keys.

Provide convenience scripts so the user can perform those actions with `gh` and
`aws` when ready.

### Artifacts to add

Add these files:

- `.github/workflows/deploy-static-sites.yml`
- `deploy/aws-static-sites/github-oidc-role.yaml`
- `deploy/aws-static-sites/create-github-oidc-role.sh`
- `deploy/aws-static-sites/configure-github-actions-vars.sh`

Update these existing files:

- `deploy/aws-static-sites/README.md`
- `tasks/20260614-aws-static-sites-docs-deployment/040-github-actions-aws-deploy.md`
- `tasks/20260614-aws-static-sites-docs-deployment/000-main.md`, only when the
  task is complete.

### Workflow implementation

Create `.github/workflows/deploy-static-sites.yml`.

The workflow should:

- Trigger on `workflow_dispatch`.
- Trigger on pushes to `main` that touch static-site or docs deployment inputs:
  - `landing_page/**`
  - `docs/**`
  - `plugins/docs/**`
  - `docs_site/**`
  - `deploy/aws-static-sites/**`
  - `.github/workflows/deploy-static-sites.yml`
- Use GitHub OIDC permissions only:
  - `contents: read`
  - `id-token: write`
- Use `aws-actions/configure-aws-credentials` with
  `secrets.AWS_ROLE_TO_ASSUME`.
- Read build/deploy configuration from GitHub repository variables:
  - `AWS_REGION`
  - `LANDING_BUCKET`
  - `DOCS_BUCKET`
  - `LANDING_CLOUDFRONT_DISTRIBUTION_ID`
  - `DOCS_CLOUDFRONT_DISTRIBUTION_ID`
  - `PUBLIC_CRYSTAL_LATTICE_SITE_URL`
  - `PUBLIC_CRYSTAL_LATTICE_DOCS_URL`

The workflow should build the landing site with:

```bash
yarn --cwd landing_page install --frozen-lockfile
yarn --cwd landing_page build
```

The workflow should build the docs site with:

```bash
python -m pip install --upgrade pip
python -m pip install -r docs_site/requirements.txt
python docs_site/scripts/build_mkdocs_site.py
```

The workflow should deploy the landing site with:

```bash
aws s3 sync landing_page/dist/ "s3://${LANDING_BUCKET}/" --delete
aws cloudfront create-invalidation \
  --distribution-id "${LANDING_CLOUDFRONT_DISTRIBUTION_ID}" \
  --paths "/*"
```

The workflow should deploy the docs site with:

```bash
aws s3 sync docs_site/dist/ "s3://${DOCS_BUCKET}/" --delete
```

Then it must re-upload generated Markdown and LLM files with inline-readable
content types:

```bash
find docs_site/dist -name '*.md' -print0 | while IFS= read -r -d '' file; do
  key="${file#docs_site/dist/}"
  aws s3 cp "$file" "s3://${DOCS_BUCKET}/${key}" \
    --content-type "text/plain; charset=utf-8" \
    --metadata-directive REPLACE
done

for file in docs_site/dist/llms.txt docs_site/dist/llms-full.txt; do
  test -f "$file" || continue
  key="${file#docs_site/dist/}"
  aws s3 cp "$file" "s3://${DOCS_BUCKET}/${key}" \
    --content-type "text/plain; charset=utf-8" \
    --metadata-directive REPLACE
done
```

Finally, invalidate the docs CloudFront distribution.

### AWS OIDC role template

Add `deploy/aws-static-sites/github-oidc-role.yaml`.

The template should create a narrowly scoped IAM role for GitHub Actions OIDC.
It should support one trusted repository and one trusted branch.

Parameters:

- `GitHubOwner`
- `GitHubRepo`
- `GitHubBranch`
- `RoleName`
- `CreateOidcProvider`
- `ExistingOidcProviderArn`
- `LandingBucket`
- `DocsBucket`
- `LandingDistributionId`
- `DocsDistributionId`

The role trust policy should allow only:

```text
repo:<GitHubOwner>/<GitHubRepo>:ref:refs/heads/<GitHubBranch>
```

The deploy role permissions should be limited to:

- `s3:ListBucket` on the two deployment buckets.
- `s3:PutObject` and `s3:DeleteObject` on objects in the two deployment buckets.
- `cloudfront:CreateInvalidation` on the two CloudFront distributions.

The template should output:

- `AwsRoleToAssume`
- `GitHubOwner`
- `GitHubRepo`
- `GitHubBranch`
- `OidcProviderArn`

### AWS role creation script

Add `deploy/aws-static-sites/create-github-oidc-role.sh`.

This is a user-run convenience script. It should not require users to manually
copy output from `deploy/aws-static-sites/up.sh`.

It should:

- Require `ALLOW_AWS_DEPLOY=1`.
- Accept static hosting stack options:
  - `--static-stack-name`
  - `--region`
- Accept role stack/repo options:
  - `--role-stack-name`
  - `--role-name`
  - `--github-owner`
  - `--github-repo`
  - `--github-branch`
- Read the static hosting outputs automatically via
  `deploy/aws-static-sites/outputs.sh`.
- Detect whether the AWS account already has the GitHub OIDC provider:
  `token.actions.githubusercontent.com`.
- Deploy `github-oidc-role.yaml` with either:
  - `CreateOidcProvider=true`, when no provider exists, or
  - `CreateOidcProvider=false` and `ExistingOidcProviderArn=<arn>`, when one
    already exists.
- Print the role stack output, especially `AWS_ROLE_TO_ASSUME`.

### GitHub configuration script

Add `deploy/aws-static-sites/configure-github-actions-vars.sh`.

This is a user-run convenience script. It should read AWS/CloudFormation outputs
automatically and then call `gh`.

It should:

- Accept:
  - `--repo`
  - `--profile test|prod`
  - `--static-stack-name`
  - `--role-stack-name`
  - `--region`
  - `--site-url`
  - `--docs-url`
  - `--role-arn`
- Default test public URLs to:
  - `https://crystallattice.dev.dynamicprogrammingsolutions.com`
  - `https://docs.crystallattice.dev.dynamicprogrammingsolutions.com`
- Default production public URLs to:
  - `https://crystallattice.dev`
  - `https://docs.crystallattice.dev`
- Read these from the static hosting stack outputs:
  - `LANDING_BUCKET`
  - `DOCS_BUCKET`
  - `LANDING_CLOUDFRONT_DISTRIBUTION_ID`
  - `DOCS_CLOUDFRONT_DISTRIBUTION_ID`
  - `AWS_REGION`
- Read `AWS_ROLE_TO_ASSUME` from the role stack output unless `--role-arn` is
  provided.
- Use `gh variable set` for non-secret values:
  - `AWS_REGION`
  - `LANDING_BUCKET`
  - `DOCS_BUCKET`
  - `LANDING_CLOUDFRONT_DISTRIBUTION_ID`
  - `DOCS_CLOUDFRONT_DISTRIBUTION_ID`
  - `PUBLIC_CRYSTAL_LATTICE_SITE_URL`
  - `PUBLIC_CRYSTAL_LATTICE_DOCS_URL`
- Use `gh secret set AWS_ROLE_TO_ASSUME` for the role ARN by default. The ARN is
  not a credential by itself, but keeping deploy identity in secrets is a
  conservative convention.
- Print a short summary of variables/secrets configured.

### README updates

Update `deploy/aws-static-sites/README.md` with user-ready commands for:

- Creating/updating the test static hosting stack.
- Tearing down the test static hosting stack.
- Creating/updating the production static hosting stack.
- Tearing down the production static hosting stack.
- Creating/updating the GitHub OIDC deploy role.
- Configuring GitHub Actions variables/secrets with `gh`.
- Manually dispatching the workflow with `gh workflow run`.

The README should explain that `configure-github-actions-vars.sh` reads stack
outputs automatically, so the user does not need to copy values from `up.sh`.

### Validation

Run local validation:

```bash
bash -n \
  deploy/aws-static-sites/up.sh \
  deploy/aws-static-sites/down.sh \
  deploy/aws-static-sites/sync.sh \
  deploy/aws-static-sites/outputs.sh \
  deploy/aws-static-sites/create-github-oidc-role.sh \
  deploy/aws-static-sites/configure-github-actions-vars.sh \
  deploy/aws-static-sites/lib/common.sh
```

Validate CloudFormation templates:

```bash
aws --region us-east-1 cloudformation validate-template \
  --template-body file://deploy/aws-static-sites/static-sites.yaml

aws --region us-east-1 cloudformation validate-template \
  --template-body file://deploy/aws-static-sites/github-oidc-role.yaml
```

Validate local builds with the test public URLs:

```bash
export PUBLIC_CRYSTAL_LATTICE_SITE_URL=https://crystallattice.dev.dynamicprogrammingsolutions.com
export PUBLIC_CRYSTAL_LATTICE_DOCS_URL=https://docs.crystallattice.dev.dynamicprogrammingsolutions.com
yarn --cwd landing_page install --frozen-lockfile
yarn --cwd landing_page build
python -m pip install -r docs_site/requirements.txt
python docs_site/scripts/build_mkdocs_site.py
```

Do not run these commands unless explicitly asked:

```bash
deploy/aws-static-sites/configure-github-actions-vars.sh ...
gh workflow run deploy-static-sites.yml ...
```

## Completion Notes

Added during completion.

Implemented GitHub Actions AWS deployment support without mutating GitHub
repository settings.

Files added:

- `.github/workflows/deploy-static-sites.yml`
- `deploy/aws-static-sites/github-oidc-role.yaml`
- `deploy/aws-static-sites/create-github-oidc-role.sh`
- `deploy/aws-static-sites/configure-github-actions-vars.sh`

Files updated:

- `deploy/aws-static-sites/README.md`
- `tasks/20260614-aws-static-sites-docs-deployment/040-github-actions-aws-deploy.md`

Workflow behavior:

- Builds the Astro landing site with `yarn --cwd landing_page install
  --frozen-lockfile` and `yarn --cwd landing_page build`.
- Builds docs with `python docs_site/scripts/build_mkdocs_site.py`.
- Assumes AWS credentials through GitHub OIDC using
  `secrets.AWS_ROLE_TO_ASSUME`.
- Reads deploy configuration from GitHub repository variables.
- Syncs `landing_page/dist/` and `docs_site/dist/` to S3 with `--delete`.
- Re-uploads generated docs Markdown files, `llms.txt`, and `llms-full.txt` as
  `text/plain; charset=utf-8`.
- Invalidates both CloudFront distributions.

AWS role support:

- Added `github-oidc-role.yaml` to create/update a narrow deploy role trusted by
  one GitHub repo and branch.
- The role grants only S3 list/write/delete for the two deployment buckets and
  CloudFront invalidation for the two target distributions.
- Added `create-github-oidc-role.sh`, which reads static hosting stack outputs
  automatically and detects whether the AWS account already has the GitHub OIDC
  provider before deploying the role stack.

GitHub configuration support:

- Added `configure-github-actions-vars.sh`, which reads stack outputs
  automatically and uses `gh variable set` / `gh secret set` to configure the
  repository.
- The script supports `--profile test|prod`.
- `AWS_ROLE_TO_ASSUME` is configured as a GitHub secret by convention.
- The script supports `--dry-run` for previewing `gh` commands before mutation.

User-run commands documented in `deploy/aws-static-sites/README.md`:

- Ready-to-use test static hosting deploy and teardown.
- Ready-to-use production static hosting deploy and teardown.
- Ready-to-use test GitHub OIDC role creation.
- Ready-to-use test GitHub variable/secret configuration.
- Ready-to-use production GitHub OIDC role creation.
- Ready-to-use production GitHub variable/secret configuration.
- Manual `gh workflow run deploy-static-sites.yml` command.

Validation performed:

- `bash -n` passed for:
  - `deploy/aws-static-sites/up.sh`
  - `deploy/aws-static-sites/down.sh`
  - `deploy/aws-static-sites/sync.sh`
  - `deploy/aws-static-sites/outputs.sh`
  - `deploy/aws-static-sites/create-github-oidc-role.sh`
  - `deploy/aws-static-sites/configure-github-actions-vars.sh`
  - `deploy/aws-static-sites/lib/common.sh`
- `aws --region us-east-1 cloudformation validate-template --template-body file://deploy/aws-static-sites/github-oidc-role.yaml` succeeded.
- `aws --region us-east-1 cloudformation validate-template --template-body file://deploy/aws-static-sites/static-sites.yaml` succeeded.
- `actionlint .github/workflows/deploy-static-sites.yml` passed.
- Lightweight workflow content checks passed for workflow dispatch, AWS
  credential action, docs build script, and inline text content type handling.
- Test URL landing build passed with:
  - `PUBLIC_CRYSTAL_LATTICE_SITE_URL=https://crystallattice.dev.dynamicprogrammingsolutions.com`
  - `PUBLIC_CRYSTAL_LATTICE_DOCS_URL=https://docs.crystallattice.dev.dynamicprogrammingsolutions.com`
- Test URL docs build passed with the same public URL env vars. MkDocs still
  reports the known non-strict griffe/autoref warnings from earlier tasks.

Not performed:

- Did not run `configure-github-actions-vars.sh`.
- Did not create or update GitHub repository variables/secrets.
- Did not trigger `deploy-static-sites.yml`.
- Did not create long-lived AWS access keys.
