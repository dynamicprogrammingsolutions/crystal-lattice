# AWS Static Sites Deployment

This deployment hosts the Crystal Lattice landing website and documentation site
on AWS using private S3 buckets, CloudFront Origin Access Control, ACM, and
Route 53.

The current testing domains are intentionally separate from the later launch
domains:

- Website: `https://cl-static-test.dynamicprogrammingsolutions.com`
- Docs: `https://docs.cl-static-test.dynamicprogrammingsolutions.com`

Later launch domains:

- Website: `https://crystallattice.dev`
- Docs: `https://docs.crystallattice.dev`

## What The Stack Creates

- One private S3 bucket for `landing_page/dist`.
- One private S3 bucket for `site`.
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

Deploy or update the testing stack:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-static-sites/up.sh \
  --stack-name crystal-lattice-static-sites-test \
  --region us-east-1 \
  --hosted-zone-name dynamicprogrammingsolutions.com \
  --landing-domain cl-static-test.dynamicprogrammingsolutions.com \
  --docs-domain docs.cl-static-test.dynamicprogrammingsolutions.com \
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
LANDING_URL=https://cl-static-test.dynamicprogrammingsolutions.com
DOCS_URL=https://docs.cl-static-test.dynamicprogrammingsolutions.com
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
export PUBLIC_CRYSTAL_LATTICE_SITE_URL=https://cl-static-test.dynamicprogrammingsolutions.com
export PUBLIC_CRYSTAL_LATTICE_DOCS_URL=https://docs.cl-static-test.dynamicprogrammingsolutions.com
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
python -m pip install -r docs/requirements.txt
python docs_site/scripts/prepare_mkdocs_site.py
mkdocs build
```

For strict validation after docs warnings are cleaned up:

```bash
mkdocs build --strict
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
mkdocs serve -a 127.0.0.1:8001
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
mkdocs build
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
- uploads `site/` to the docs bucket with `--delete`;
- re-uploads generated `site/**/*.md`, `site/llms.txt`, and
  `site/llms-full.txt` as `text/plain; charset=utf-8` so browsers and LLM tools
  open them inline;
- invalidates both CloudFront distributions.

## Validation

Check the live URLs:

```bash
curl -I https://cl-static-test.dynamicprogrammingsolutions.com
curl -I https://docs.cl-static-test.dynamicprogrammingsolutions.com
curl -I https://docs.cl-static-test.dynamicprogrammingsolutions.com/llms.txt
curl -I https://docs.cl-static-test.dynamicprogrammingsolutions.com/llms-full.txt
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

- `cl-static-test.dynamicprogrammingsolutions.com` alias records;
- `docs.cl-static-test.dynamicprogrammingsolutions.com` alias records;
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