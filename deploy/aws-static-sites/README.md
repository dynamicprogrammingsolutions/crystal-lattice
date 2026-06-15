# AWS Static Sites Deployment

This deployment hosts the Crystal Lattice landing website and documentation site
on AWS using private S3 buckets, CloudFront Origin Access Control, ACM, and
Route 53.

The current testing domains are intentionally separate from the later launch
domains:

- Website: `https://crystallattice.dev.dynamicprogrammingsolutions.com`
- Docs: `https://docs.crystallattice.dev.dynamicprogrammingsolutions.com`

Later launch domains:

- Website: `https://crystallattice.dev`
- Docs: `https://docs.crystallattice.dev`

## What The Stack Creates

- One private S3 bucket for `landing_page/dist`.
- One private S3 bucket for `docs_site/dist`.
- S3 public access blocks and bucket-owner-enforced object ownership.
- CloudFront Origin Access Control for both S3 origins.
- One ACM certificate in `us-east-1` covering both testing domains.
- DNS validation records for the ACM certificate.
- One CloudFront distribution per site.
- Route 53 `A` and `AAAA` alias records for both testing domains.
- Short cache policy for HTML/directory-index content.
- Long cache policy for fingerprinted assets.
- Conservative security response headers.
- A CloudFront Function that rewrites directory URLs such as `/mobile/` and
  `/plugin-development/` to nested `index.html` files.

The deployment is idempotent. Re-running `up.sh` uses
`aws cloudformation deploy`, so unchanged infrastructure becomes a no-op and
changed infrastructure is updated in place.

## Prerequisites

- AWS CLI configured locally.
- Permission to create S3 buckets, CloudFront distributions, CloudFront
  functions, CloudFront policies, ACM certificates, and Route 53 records.
- A public Route 53 hosted zone for `dynamicprogrammingsolutions.com`.
- Deploy in `us-east-1`; CloudFront requires ACM certificates in `us-east-1`.
- `ALLOW_AWS_DEPLOY=1` for commands that create, sync, or delete AWS resources.

Confirm the hosted zone:

```bash
aws route53 list-hosted-zones-by-name \
  --dns-name dynamicprogrammingsolutions.com. \
  --query "HostedZones[?Name=='dynamicprogrammingsolutions.com.' && Config.PrivateZone==\`false\`].[Id,Name]" \
  --output table
```

## Up

### Ready-To-Use Test Deployment

Create or update the AWS testing infrastructure, build both sites for the
testing domains, upload artifacts, and invalidate CloudFront:

```bash
export PUBLIC_CRYSTAL_LATTICE_SITE_URL=https://crystallattice.dev.dynamicprogrammingsolutions.com
export PUBLIC_CRYSTAL_LATTICE_DOCS_URL=https://docs.crystallattice.dev.dynamicprogrammingsolutions.com

ALLOW_AWS_DEPLOY=1 deploy/aws-static-sites/up.sh \
  --stack-name crystal-lattice-static-sites-test \
  --region us-east-1 \
  --hosted-zone-name dynamicprogrammingsolutions.com \
  --landing-domain crystallattice.dev.dynamicprogrammingsolutions.com \
  --docs-domain docs.crystallattice.dev.dynamicprogrammingsolutions.com \
  --bucket-name-prefix crystal-lattice-static-test

yarn --cwd landing_page install --frozen-lockfile
yarn --cwd landing_page build
python -m pip install -r docs_site/requirements.txt
python docs_site/scripts/build_mkdocs_site.py

ALLOW_AWS_DEPLOY=1 deploy/aws-static-sites/sync.sh \
  --stack-name crystal-lattice-static-sites-test \
  --region us-east-1
```

Tear down the testing deployment and remove its stack-managed subdomain records:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-static-sites/down.sh \
  --stack-name crystal-lattice-static-sites-test \
  --region us-east-1
```

### Ready-To-Use Production Deployment

Production public URLs are the build defaults. This command assumes the
`crystallattice.dev` public hosted zone already exists in Route 53:

```bash
unset PUBLIC_CRYSTAL_LATTICE_SITE_URL
unset PUBLIC_CRYSTAL_LATTICE_DOCS_URL

ALLOW_AWS_DEPLOY=1 deploy/aws-static-sites/up.sh \
  --stack-name crystal-lattice-static-sites-prod \
  --region us-east-1 \
  --hosted-zone-name crystallattice.dev \
  --landing-domain crystallattice.dev \
  --docs-domain docs.crystallattice.dev \
  --bucket-name-prefix crystal-lattice-prod

yarn --cwd landing_page install --frozen-lockfile
yarn --cwd landing_page build
python -m pip install -r docs_site/requirements.txt
python docs_site/scripts/build_mkdocs_site.py

ALLOW_AWS_DEPLOY=1 deploy/aws-static-sites/sync.sh \
  --stack-name crystal-lattice-static-sites-prod \
  --region us-east-1
```

Tear down the production deployment and remove its stack-managed domain records:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-static-sites/down.sh \
  --stack-name crystal-lattice-static-sites-prod \
  --region us-east-1
```

Use explicit production build URLs if you prefer not to rely on defaults:

```bash
export PUBLIC_CRYSTAL_LATTICE_SITE_URL=https://crystallattice.dev
export PUBLIC_CRYSTAL_LATTICE_DOCS_URL=https://docs.crystallattice.dev
```

## GitHub Actions Setup

The deploy workflow uses GitHub Actions OIDC to assume a narrow AWS role. Do not
create long-lived AWS access keys for this deployment path.

The helper scripts read CloudFormation stack outputs automatically. You do not
need to copy values from `up.sh` into GitHub by hand.

### Ready-To-Use Test GitHub Setup

After the test static stack exists, create or update the AWS OIDC role:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-static-sites/create-github-oidc-role.sh \
  --profile test \
  --static-stack-name crystal-lattice-static-sites-test \
  --role-stack-name crystal-lattice-static-sites-github-oidc-test \
  --region us-east-1 \
  --github-owner dynamicprogrammingsolutions \
  --github-repo crystal-lattice \
  --github-branch main
```

Preview the GitHub repository variable/secret updates:

```bash
deploy/aws-static-sites/configure-github-actions-vars.sh \
  --profile test \
  --repo dynamicprogrammingsolutions/crystal-lattice \
  --static-stack-name crystal-lattice-static-sites-test \
  --role-stack-name crystal-lattice-static-sites-github-oidc-test \
  --region us-east-1 \
  --dry-run
```

Apply the GitHub repository variable/secret updates:

```bash
deploy/aws-static-sites/configure-github-actions-vars.sh \
  --profile test \
  --repo dynamicprogrammingsolutions/crystal-lattice \
  --static-stack-name crystal-lattice-static-sites-test \
  --role-stack-name crystal-lattice-static-sites-github-oidc-test \
  --region us-east-1
```

Run the workflow manually:

```bash
gh workflow run deploy-static-sites.yml \
  --repo dynamicprogrammingsolutions/crystal-lattice \
  --ref main
```

### Testing Workflow Changes From A Branch

GitHub must know about a workflow before `gh workflow run` can find it. If
`.github/workflows/deploy-static-sites.yml` exists only on a feature branch and
has never been merged to the repository default branch, this command can return
`HTTP 404: Not Found`:

```bash
gh workflow run deploy-static-sites.yml \
  --repo dynamicprogrammingsolutions/crystal-lattice \
  --ref task/20260614-aws-static-sites-docs-deployment
```

After the workflow file exists on the default branch, you can manually dispatch
it against another branch:

```bash
export BRANCH_NAME="task/20260614-aws-static-sites-docs-deployment"

gh workflow run deploy-static-sites.yml \
  --repo dynamicprogrammingsolutions/crystal-lattice \
  --ref "$BRANCH_NAME"
```

When testing from a branch, update the AWS OIDC role trust policy to trust that
branch:

```bash
export BRANCH_NAME="task/20260614-aws-static-sites-docs-deployment"

ALLOW_AWS_DEPLOY=1 deploy/aws-static-sites/create-github-oidc-role.sh \
  --profile test \
  --static-stack-name crystal-lattice-static-sites-test \
  --role-stack-name crystal-lattice-static-sites-github-oidc-test \
  --region us-east-1 \
  --github-owner dynamicprogrammingsolutions \
  --github-repo crystal-lattice \
  --github-branch "$BRANCH_NAME"
```

After branch testing, restore the role trust policy to `main`:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-static-sites/create-github-oidc-role.sh \
  --profile test \
  --static-stack-name crystal-lattice-static-sites-test \
  --role-stack-name crystal-lattice-static-sites-github-oidc-test \
  --region us-east-1 \
  --github-owner dynamicprogrammingsolutions \
  --github-repo crystal-lattice \
  --github-branch main
```

Check workflow runs and logs:

```bash
gh run list \
  --repo dynamicprogrammingsolutions/crystal-lattice \
  --workflow deploy-static-sites.yml \
  --limit 5

gh run view \
  --repo dynamicprogrammingsolutions/crystal-lattice \
  --log
```

### Ready-To-Use Production GitHub Setup

After the production static stack exists, create or update the AWS OIDC role:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-static-sites/create-github-oidc-role.sh \
  --profile prod \
  --static-stack-name crystal-lattice-static-sites-prod \
  --role-stack-name crystal-lattice-static-sites-github-oidc-prod \
  --region us-east-1 \
  --github-owner dynamicprogrammingsolutions \
  --github-repo crystal-lattice \
  --github-branch main
```

Preview the GitHub repository variable/secret updates:

```bash
deploy/aws-static-sites/configure-github-actions-vars.sh \
  --profile prod \
  --repo dynamicprogrammingsolutions/crystal-lattice \
  --static-stack-name crystal-lattice-static-sites-prod \
  --role-stack-name crystal-lattice-static-sites-github-oidc-prod \
  --region us-east-1 \
  --dry-run
```

Apply the GitHub repository variable/secret updates:

```bash
deploy/aws-static-sites/configure-github-actions-vars.sh \
  --profile prod \
  --repo dynamicprogrammingsolutions/crystal-lattice \
  --static-stack-name crystal-lattice-static-sites-prod \
  --role-stack-name crystal-lattice-static-sites-github-oidc-prod \
  --region us-east-1
```

Run the workflow manually:

```bash
gh workflow run deploy-static-sites.yml \
  --repo dynamicprogrammingsolutions/crystal-lattice \
  --ref main
```

The GitHub configuration script sets these repository variables:

- `AWS_REGION`
- `LANDING_BUCKET`
- `DOCS_BUCKET`
- `LANDING_CLOUDFRONT_DISTRIBUTION_ID`
- `DOCS_CLOUDFRONT_DISTRIBUTION_ID`
- `PUBLIC_CRYSTAL_LATTICE_SITE_URL`
- `PUBLIC_CRYSTAL_LATTICE_DOCS_URL`

It sets `AWS_ROLE_TO_ASSUME` as a repository secret.

Deploy or update the testing stack:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-static-sites/up.sh \
  --stack-name crystal-lattice-static-sites-test \
  --region us-east-1 \
  --hosted-zone-name dynamicprogrammingsolutions.com \
  --landing-domain crystallattice.dev.dynamicprogrammingsolutions.com \
  --docs-domain docs.crystallattice.dev.dynamicprogrammingsolutions.com \
  --bucket-name-prefix crystal-lattice-static-test
```

The command prints values needed by GitHub Actions:

```text
AWS_REGION=us-east-1
HOSTED_ZONE_ID=...
LANDING_BUCKET=...
DOCS_BUCKET=...
LANDING_CLOUDFRONT_DISTRIBUTION_ID=...
DOCS_CLOUDFRONT_DISTRIBUTION_ID=...
LANDING_URL=https://crystallattice.dev.dynamicprogrammingsolutions.com
DOCS_URL=https://docs.crystallattice.dev.dynamicprogrammingsolutions.com
```

You can print the same values later:

```bash
deploy/aws-static-sites/outputs.sh \
  --stack-name crystal-lattice-static-sites-test \
  --region us-east-1
```

## Build Content

Both static sites use production public URLs by default:

```text
PUBLIC_CRYSTAL_LATTICE_SITE_URL=https://crystallattice.dev
PUBLIC_CRYSTAL_LATTICE_DOCS_URL=https://docs.crystallattice.dev
```

For the temporary testing stack, set the public build URLs explicitly so
canonical URLs, cross-site links, generated Markdown links, and `llms.txt` all
point at the live testing domains:

```bash
export PUBLIC_CRYSTAL_LATTICE_SITE_URL=https://crystallattice.dev.dynamicprogrammingsolutions.com
export PUBLIC_CRYSTAL_LATTICE_DOCS_URL=https://docs.crystallattice.dev.dynamicprogrammingsolutions.com
```

Build the landing site:

```bash
cd landing_page
yarn install --frozen-lockfile
yarn build
cd ..
```

Build the docs site:

```bash
python -m pip install -r docs_site/requirements.txt
python docs_site/scripts/build_mkdocs_site.py
```

The convenience build script runs:

```bash
python docs_site/scripts/prepare_mkdocs_site.py
(cd docs_site && mkdocs build)
python docs_site/scripts/refresh_reference_snapshots.py
```

For strict validation after docs warnings are cleaned up:

```bash
(cd docs_site && mkdocs build --strict)
```

For local development with local cross-links:

```bash
PUBLIC_CRYSTAL_LATTICE_SITE_URL=http://localhost:4321 \
PUBLIC_CRYSTAL_LATTICE_DOCS_URL=http://localhost:8001 \
yarn --cwd landing_page dev
```

```bash
PUBLIC_CRYSTAL_LATTICE_SITE_URL=http://localhost:4321 \
PUBLIC_CRYSTAL_LATTICE_DOCS_URL=http://localhost:8001 \
python docs_site/scripts/prepare_mkdocs_site.py
(cd docs_site && mkdocs serve -a 127.0.0.1:8001)
```

For final production builds, omit the variables or set them explicitly:

```bash
PUBLIC_CRYSTAL_LATTICE_SITE_URL=https://crystallattice.dev \
PUBLIC_CRYSTAL_LATTICE_DOCS_URL=https://docs.crystallattice.dev \
yarn --cwd landing_page build
```

```bash
PUBLIC_CRYSTAL_LATTICE_SITE_URL=https://crystallattice.dev \
PUBLIC_CRYSTAL_LATTICE_DOCS_URL=https://docs.crystallattice.dev \
python docs_site/scripts/build_mkdocs_site.py
```

## Sync Content

Upload both built sites and invalidate CloudFront:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-static-sites/sync.sh \
  --stack-name crystal-lattice-static-sites-test \
  --region us-east-1
```

The sync script:

- uploads `landing_page/dist/` to the landing bucket with `--delete`;
- uploads `docs_site/dist/` to the docs bucket with `--delete`;
- re-uploads generated `docs_site/dist/**/*.md`,
  `docs_site/dist/llms.txt`, and `docs_site/dist/llms-full.txt` as
  `text/plain; charset=utf-8` so browsers and LLM tools open them inline;
- invalidates both CloudFront distributions.

## Validation

Check the live URLs:

```bash
curl -I https://crystallattice.dev.dynamicprogrammingsolutions.com
curl -I https://docs.crystallattice.dev.dynamicprogrammingsolutions.com
curl -I https://docs.crystallattice.dev.dynamicprogrammingsolutions.com/llms.txt
curl -I https://docs.crystallattice.dev.dynamicprogrammingsolutions.com/llms-full.txt
```

Confirm the S3 buckets are not public:

```bash
LANDING_BUCKET="$(deploy/aws-static-sites/outputs.sh --stack-name crystal-lattice-static-sites-test --region us-east-1 | awk -F= '/^LANDING_BUCKET=/{print $2}')"
DOCS_BUCKET="$(deploy/aws-static-sites/outputs.sh --stack-name crystal-lattice-static-sites-test --region us-east-1 | awk -F= '/^DOCS_BUCKET=/{print $2}')"

aws s3api get-public-access-block --bucket "$LANDING_BUCKET"
aws s3api get-public-access-block --bucket "$DOCS_BUCKET"
aws s3api get-bucket-policy-status --bucket "$LANDING_BUCKET"
aws s3api get-bucket-policy-status --bucket "$DOCS_BUCKET"
```

## Down

`down.sh` empties the two stack-managed buckets, deletes the CloudFormation
stack, and removes the stack-managed Route 53 testing subdomain records:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-static-sites/down.sh \
  --stack-name crystal-lattice-static-sites-test \
  --region us-east-1
```

This removes:

- `crystallattice.dev.dynamicprogrammingsolutions.com` alias records;
- `docs.crystallattice.dev.dynamicprogrammingsolutions.com` alias records;
- ACM DNS validation records managed by the certificate resource;
- CloudFront distributions and OACs;
- the stack-managed S3 buckets after they are emptied.

## GitHub Actions Values

For the later GitHub Actions deployment task, use:

```bash
deploy/aws-static-sites/outputs.sh \
  --stack-name crystal-lattice-static-sites-test \
  --region us-east-1
```

Map the output to repository variables or secrets:

- `AWS_REGION`
- `LANDING_BUCKET`
- `DOCS_BUCKET`
- `LANDING_CLOUDFRONT_DISTRIBUTION_ID`
- `DOCS_CLOUDFRONT_DISTRIBUTION_ID`

The deploy role ARN will be created in the GitHub Actions AWS deploy task.