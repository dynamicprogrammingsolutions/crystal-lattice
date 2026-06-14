# AWS Static Hosting Infrastructure

Provision AWS static hosting for the website and documentation site using private S3 buckets, CloudFront, ACM, and Route 53.

## Requirements checklist

- [ ] Confirm Route 53 hosted zone support for `dynamicprogrammingsolutions.com` temporary testing subdomains.
- [ ] Request/validate ACM certificates in `us-east-1` for `crystallattice.dev.dynamicprogrammingsolutions.com` and `docs.crystallattice.dev.dynamicprogrammingsolutions.com`.
- [ ] Create private S3 bucket for the website artifacts.
- [ ] Create private S3 bucket for the docs artifacts.
- [ ] Create CloudFront distribution for `crystallattice.dev.dynamicprogrammingsolutions.com`.
- [ ] Create CloudFront distribution for `docs.crystallattice.dev.dynamicprogrammingsolutions.com`.
- [ ] Configure CloudFront Origin Access Control for both S3 origins.
- [ ] Create Route 53 alias records pointing both domains to their CloudFront distributions.
- [ ] Record bucket names and CloudFront distribution IDs for GitHub Actions.

Parent Task: `tasks/20260614-aws-static-sites-docs-deployment/000-main.md`

Depends On: `tasks/20260614-aws-static-sites-docs-deployment/010-design-and-docs-alignment.md`

## Target Architecture

Website:

- Testing domain: `crystallattice.dev.dynamicprogrammingsolutions.com`
- Final domain later: `crystallattice.dev`
- Build output: `landing_page/dist`
- Suggested bucket: `crystallattice-prod-site`
- CloudFront default root object: `index.html`
- Certificate region: `us-east-1`

Docs:

- Testing domain: `docs.crystallattice.dev.dynamicprogrammingsolutions.com`
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

- `https://crystallattice.dev.dynamicprogrammingsolutions.com` resolves through CloudFront.
- `https://docs.crystallattice.dev.dynamicprogrammingsolutions.com` resolves through CloudFront.
- TLS certificate is valid for both domains.
- S3 buckets are not publicly listable/readable.
- CloudFront can read bucket objects through OAC.
