# AWS Static Hosting Infrastructure

Provision AWS static hosting for the website and documentation site using private S3 buckets, CloudFront, ACM, and Route 53.

## Requirements checklist

- [x] Confirm Route 53 hosted zone support for `dynamicprogrammingsolutions.com` temporary testing subdomains.
- [x] Request/validate ACM certificates in `us-east-1` for `cl-static-test.dynamicprogrammingsolutions.com` and `docs.cl-static-test.dynamicprogrammingsolutions.com`.
- [x] Create private S3 bucket for the website artifacts.
- [x] Create private S3 bucket for the docs artifacts.
- [x] Create CloudFront distribution for `cl-static-test.dynamicprogrammingsolutions.com`.
- [x] Create CloudFront distribution for `docs.cl-static-test.dynamicprogrammingsolutions.com`.
- [x] Configure CloudFront Origin Access Control for both S3 origins.
- [x] Create Route 53 alias records pointing both domains to their CloudFront distributions.
- [x] Record bucket names and CloudFront distribution IDs for GitHub Actions.

Parent Task: `tasks/20260614-aws-static-sites-docs-deployment/000-main.md`

Depends On: `tasks/20260614-aws-static-sites-docs-deployment/010-design-and-docs-alignment.md`

## Target Architecture

Website:

- Testing domain: `cl-static-test.dynamicprogrammingsolutions.com`
- Final domain later: `crystallattice.dev`
- Build output: `landing_page/dist`
- Suggested bucket: `crystallattice-prod-site`
- CloudFront default root object: `index.html`
- Certificate region: `us-east-1`

Docs:

- Testing domain: `docs.cl-static-test.dynamicprogrammingsolutions.com`
- Final domain later: `docs.crystallattice.dev`
- Build output: `site`
- Suggested bucket: `crystallattice-prod-docs`
- CloudFront default root object: `index.html`
- Certificate region: `us-east-1`

Use private S3 buckets. Do not use public S3 website hosting as the primary production path. CloudFront should access S3 through Origin Access Control.

## Implementation Notes

AWS CLI and GitHub CLI are available in the local environment. Infrastructure may be created manually with AWS CLI, Terraform, CDK, or CloudFormation. If choosing a tool, prefer something reproducible and commit the infrastructure definition unless the user explicitly wants manual setup only.

CloudFront behavior recommendations:

- Redirect HTTP to HTTPS.
- Enable Brotli and gzip compression.
- Use managed cache policies where possible.
- Use `index.html` as the default root object.
- Configure a real `404.html` for docs if available.
- Only use SPA-style `403`/`404` fallback to `/index.html` for the landing site if Astro routes require it after testing.

Cache guidance:

- HTML: shorter TTL or cache invalidation on each deploy.
- Fingerprinted assets such as Astro `_astro/` files: long TTL.
- Docs assets: can use moderate/long TTL with CloudFront invalidation on deploy.

Security/header guidance:

- Add security headers through CloudFront response headers policy where practical.
- Avoid overly aggressive CSP until the Astro and MkDocs generated pages are checked.

## Outputs Needed For Later Tasks

Record these values somewhere safe for the GitHub Actions task:

- `LANDING_BUCKET`
- `DOCS_BUCKET`
- `LANDING_CLOUDFRONT_DISTRIBUTION_ID`
- `DOCS_CLOUDFRONT_DISTRIBUTION_ID`
- `AWS_REGION`
- hosted zone ID, if workflow or future automation will update DNS

## Validation

Before GitHub Actions automation, test manual upload if possible:

```bash
aws s3 sync landing_page/dist/ "s3://${LANDING_BUCKET}/" --delete
aws cloudfront create-invalidation --distribution-id "${LANDING_CLOUDFRONT_DISTRIBUTION_ID}" --paths "/*"

aws s3 sync site/ "s3://${DOCS_BUCKET}/" --delete
aws cloudfront create-invalidation --distribution-id "${DOCS_CLOUDFRONT_DISTRIBUTION_ID}" --paths "/*"
```

Manual checks:

- `https://cl-static-test.dynamicprogrammingsolutions.com` resolves through CloudFront.
- `https://docs.cl-static-test.dynamicprogrammingsolutions.com` resolves through CloudFront.
- TLS certificate is valid for both domains.
- S3 buckets are not publicly listable/readable.
- CloudFront can read bucket objects through OAC.

## Execution plan

Added during completion after user approval.

Implement the AWS static hosting setup as a reproducible CloudFormation-based
deployment under `deploy/aws-static-sites/`, with small AWS CLI wrapper scripts
for idempotent deploy/update, content sync, output discovery, and teardown.

Use a separate live testing subdomain from the earlier task defaults:

- Website: `https://cl-static-test.dynamicprogrammingsolutions.com`
- Docs: `https://docs.cl-static-test.dynamicprogrammingsolutions.com`

Execution approach:

1. Add a CloudFormation template that creates private S3 buckets, public access
   blocks, CloudFront Origin Access Control, CloudFront distributions, a shared
   ACM certificate in `us-east-1`, DNS validation records, Route 53 alias
   records, conservative security response headers, and a viewer-request
   CloudFront Function that maps directory-style URLs to `index.html`.
2. Keep the stack idempotent through `aws cloudformation deploy`. Re-running the
   `up` command should update changed infrastructure and no-op when unchanged.
3. Add wrapper scripts:
   - `up.sh` to validate/deploy the stack and print outputs.
   - `sync.sh` to upload `landing_page/dist/` and `site/`, apply inline text
     content types to generated docs Markdown and LLM text files, and invalidate
     CloudFront.
   - `outputs.sh` to print values needed by GitHub Actions.
   - `down.sh` to empty buckets, delete the stack, and remove the stack-managed
     testing subdomain records.
4. Add a README with exact commands for checking the hosted zone, deploying,
   building/syncing content, retrieving GitHub Actions values, and tearing down
   the temporary testing stack.
5. Validate the CloudFormation template locally with AWS CLI.
6. Deploy the testing stack with AWS CLI and leave it running for user
   verification.
7. Build the Astro landing site and MkDocs docs site, then sync both outputs to
   the newly created buckets and invalidate both CloudFront distributions.
8. Verify the live testing URLs with HTTP checks, confirm the generated docs LLM
   files are accessible, and confirm the S3 buckets are not publicly readable.
9. Update this task checklist and completion notes with the live URLs, bucket
   names, distribution IDs, hosted zone ID, validation commands, and any
   remaining caveats.

## Completion Notes

Added during completion.

Implemented reproducible AWS static hosting infrastructure under
`deploy/aws-static-sites/`:

- `static-sites.yaml` provisions private S3 buckets, CloudFront OAC, CloudFront
  distributions, a shared ACM certificate, Route 53 validation/alias records,
  cache policies, conservative security response headers, and a CloudFront
  Function for directory-style `index.html` routing.
- `up.sh` validates and deploys/updates the CloudFormation stack idempotently.
- `sync.sh` uploads `landing_page/dist/` and `site/`, re-uploads generated docs
  Markdown and LLM text files as `text/plain; charset=utf-8`, and invalidates
  both CloudFront distributions.
- `outputs.sh` prints values needed by the later GitHub Actions task.
- `down.sh` empties the stack-managed buckets, deletes the stack, and removes
  the stack-managed testing subdomain records.
- `README.md` documents hosted zone checks, deploy, build, sync, validation,
  outputs, and teardown commands.

Live testing deployment left running for user verification:

- Website: `https://cl-static-test.dynamicprogrammingsolutions.com`
- Docs: `https://docs.cl-static-test.dynamicprogrammingsolutions.com`

AWS outputs:

- `AWS_REGION=us-east-1`
- `HOSTED_ZONE_ID=ZEJFIL16PTJ4`
- `LANDING_BUCKET=crystal-lattice-static-test-site-874087778966`
- `DOCS_BUCKET=crystal-lattice-static-test-docs-874087778966`
- `LANDING_CLOUDFRONT_DISTRIBUTION_ID=EOQGKB4AKRNYA`
- `DOCS_CLOUDFRONT_DISTRIBUTION_ID=E3G8LQ983VB2F2`
- `LANDING_CLOUDFRONT_DOMAIN=d2i20kj5p3alz8.cloudfront.net`
- `DOCS_CLOUDFRONT_DOMAIN=d1xzzaoifmrzmt.cloudfront.net`
- `CERTIFICATE_ARN=arn:aws:acm:us-east-1:874087778966:certificate/8a255ea3-82e3-47db-a58a-39cf6b0e955c`

Domain/config adjustment:

- Switched the active testing domain references from
  `crystallattice.dev.dynamicprogrammingsolutions.com` to
  `cl-static-test.dynamicprogrammingsolutions.com`.
- Switched docs testing references from
  `docs.crystallattice.dev.dynamicprogrammingsolutions.com` to
  `docs.cl-static-test.dynamicprogrammingsolutions.com`.
- Updated `mkdocs.yml`, landing page config/content, docs home link, and related
  task handoff files so generated canonical URLs and `llms.txt` links match the
  live testing deployment.

Validation performed:

- `aws --region us-east-1 cloudformation validate-template --template-body file://deploy/aws-static-sites/static-sites.yaml` succeeded.
- Confirmed public Route 53 hosted zone for `dynamicprogrammingsolutions.com`:
  `ZEJFIL16PTJ4`.
- `ALLOW_AWS_DEPLOY=1 deploy/aws-static-sites/up.sh ...` created/updated stack
  `crystal-lattice-static-sites-test`.
- `yarn install --frozen-lockfile && yarn build` in `landing_page/` succeeded.
- `python -m pip install -r docs/requirements.txt` succeeded; dependencies were
  already installed.
- `python docs_site/scripts/prepare_mkdocs_site.py && mkdocs build` succeeded.
  MkDocs still reports the known non-strict warnings from earlier tasks:
  griffe docstring indentation warnings in `core.py` and one mkdocs-autorefs
  warning for `"content"`.
- `ALLOW_AWS_DEPLOY=1 deploy/aws-static-sites/sync.sh ...` uploaded both sites,
  fixed inline content types for generated Markdown/LLM text, and invalidated
  both distributions.
- `curl -I -L` returned HTTP 200 for:
  `https://cl-static-test.dynamicprogrammingsolutions.com`,
  `https://cl-static-test.dynamicprogrammingsolutions.com/mobile/`,
  `https://docs.cl-static-test.dynamicprogrammingsolutions.com`,
  `https://docs.cl-static-test.dynamicprogrammingsolutions.com/plugin-development/`,
  `https://docs.cl-static-test.dynamicprogrammingsolutions.com/llms.txt`, and
  `https://docs.cl-static-test.dynamicprogrammingsolutions.com/llms-full.txt`.
- Confirmed `llms.txt`, `llms-full.txt`, and generated docs Markdown are served
  from S3 with `Content-Type: text/plain; charset=utf-8`.
- Confirmed both S3 buckets have all public access block flags enabled and
  `PolicyStatus.IsPublic=false`.

Teardown command, when this testing deployment is no longer needed:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-static-sites/down.sh \
  --stack-name crystal-lattice-static-sites-test \
  --region us-east-1
```

Follow-up added after user review:

- Added dynamic public URL configuration for both the landing site and docs site.
- Production domains are now the defaults:
  - `PUBLIC_CRYSTAL_LATTICE_SITE_URL=https://crystallattice.dev`
  - `PUBLIC_CRYSTAL_LATTICE_DOCS_URL=https://docs.crystallattice.dev`
- The current testing deployment should be built with explicit overrides:
  - `PUBLIC_CRYSTAL_LATTICE_SITE_URL=https://cl-static-test.dynamicprogrammingsolutions.com`
  - `PUBLIC_CRYSTAL_LATTICE_DOCS_URL=https://docs.cl-static-test.dynamicprogrammingsolutions.com`
- Added a **Website Home** top-level docs menu item that points back to the
  configured website URL.
- Documented local, test, and production build options in
  `landing_page/README.md`, `docs_site/README.md`, and
  `deploy/aws-static-sites/README.md`.
