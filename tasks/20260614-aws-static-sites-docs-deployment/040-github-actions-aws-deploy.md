# GitHub Actions AWS Deploy

Add a GitHub Actions workflow that builds both static sites and deploys them to AWS using narrow GitHub OIDC credentials.

## Requirements checklist

- [ ] Create or document an AWS IAM role trusted by GitHub Actions OIDC for this repository and branch.
- [ ] Scope IAM permissions to only the two S3 buckets and two CloudFront distributions.
- [ ] Add non-secret GitHub Actions variables or secrets for bucket names, distribution IDs, region, and role ARN.
- [ ] Add a workflow that builds the Astro landing site.
- [ ] Add a workflow step that prepares and builds the MkDocs site.
- [ ] Deploy both build outputs to S3 with `--delete`.
- [ ] Invalidate both CloudFront distributions.
- [ ] Keep the disabled GitHub Pages workflow disabled or remove it after confirming the AWS path is live.

Parent Task: `tasks/20260614-aws-static-sites-docs-deployment/000-main.md`

Depends On: `tasks/20260614-aws-static-sites-docs-deployment/020-plugin-docs-and-llm-access.md`

Depends On: `tasks/20260614-aws-static-sites-docs-deployment/030-aws-static-hosting-infra.md`

## Repo References

- `.github/workflows/publish-docs.yml.disabled:1-53` is an old disabled GitHub Pages workflow. It is useful as a reminder that docs builds need Python setup and `mkdocs build --strict`, but deployment should target AWS instead of GitHub Pages.
- `landing_page/package.json` has `yarn build` for the Astro site.
- `docs/requirements.txt` is the docs dependency source.
- The docs workflow must include the plugin docs copy step before `mkdocs build --strict`.

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

The values are not credentials, but `AWS_ROLE_TO_ASSUME` is often kept as a secret or environment variable by convention.

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
      - "mkdocs.yml"
      - "docs/requirements.txt"
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

aws s3 sync site/ "s3://${DOCS_BUCKET}/" --delete
aws cloudfront create-invalidation \
  --distribution-id "${DOCS_CLOUDFRONT_DISTRIBUTION_ID}" \
  --paths "/*"
```

## Validation

Run the workflow manually with `workflow_dispatch`.

Check:

- AWS credentials are assumed through OIDC.
- No AWS access key ID or secret access key is stored in GitHub.
- The landing build completes.
- The docs build runs plugin-docs copy before `mkdocs build --strict`.
- S3 sync deletes removed files.
- CloudFront invalidations are created for both distributions.
