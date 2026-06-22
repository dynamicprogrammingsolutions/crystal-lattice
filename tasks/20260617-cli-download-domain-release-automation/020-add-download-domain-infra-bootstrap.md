# Add Download Domain Infrastructure Bootstrap

Add `deploy/aws-cli-downloads` infrastructure scripts that create/update the download bucket, CloudFront distribution, ACM certificate, Route 53 records, outputs, and teardown flow.

## Requirements checklist

- [x] Add `deploy/aws-cli-downloads/downloads.yaml`.
- [x] Add `deploy/aws-cli-downloads/lib/common.sh`.
- [x] Add `deploy/aws-cli-downloads/up.sh`.
- [x] Add `deploy/aws-cli-downloads/down.sh`.
- [x] Add `deploy/aws-cli-downloads/outputs.sh`.
- [x] Add stack outputs for bucket, distribution ID, CloudFront domain, certificate ARN, hosted zone ID, public base URL, and prefix.
- [x] Ensure `up.sh` provisions infrastructure and bootstraps installer upload only; it must not build release archives.
- [x] Ensure destructive AWS actions require `ALLOW_AWS_DEPLOY=1`.
- [x] Add README documentation for infrastructure bootstrap.
- [x] Test CloudFormation validation locally.
- [x] Test stack creation/update against the testing domain.
- [ ] Test teardown only if safe for the testing stack.

Parent Task: `tasks/20260617-cli-download-domain-release-automation/000-main.md`

Depends On: `tasks/20260617-cli-download-domain-release-automation/010-design-download-hosting-and-release-boundaries.md`

## Infrastructure Shape

Create a private S3 origin served through CloudFront:

```text
Route 53 alias
  -> CloudFront distribution
    -> private S3 bucket via Origin Access Control
```

The CloudFormation template should create:

- private S3 bucket
- S3 public access block
- bucket-owner-enforced object ownership
- CloudFront Origin Access Control
- CloudFront distribution
- ACM certificate in `us-east-1`
- Route 53 DNS validation records
- Route 53 `A` and `AAAA` aliases for the configured download domain
- bucket policy allowing CloudFront read-only access
- cache behavior suitable for installer/latest/archive downloads

## Script Behavior

`up.sh` should look like the static-sites script style:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/up.sh \
  --profile test \
  --stack-name crystal-lattice-cli-downloads-test \
  --region us-east-1 \
  --hosted-zone-name dynamicprogrammingsolutions.com \
  --download-domain download.crystallattice.dev.dynamicprogrammingsolutions.com \
  --bucket-name-prefix crystal-lattice-cli-downloads-test \
  --prefix crystal-lattice-cli
```

`up.sh` may call `upload-installer.sh` after the stack exists, but it must not fail just because release archives do not exist yet unless explicitly asked to validate archives.

`outputs.sh` should print shell-friendly values:

```text
AWS_REGION=
DOWNLOADS_BUCKET=
DOWNLOADS_PREFIX=
DOWNLOADS_BASE_URL=
DOWNLOADS_CLOUDFRONT_DISTRIBUTION_ID=
DOWNLOADS_CLOUDFRONT_DOMAIN=
CERTIFICATE_ARN=
HOSTED_ZONE_ID=
```

## Documentation Requirements

Add README sections for:

- prerequisites
- test infrastructure bootstrap
- production infrastructure bootstrap
- stack outputs
- expected AWS resources
- teardown
- what `up.sh` does not do

Make it explicit that official platform archives come from GitHub Actions, not local `up.sh`.

## Testing Requirements

Run and record:

```bash
aws --region us-east-1 cloudformation validate-template \
  --template-body file://deploy/aws-cli-downloads/downloads.yaml
```

Then test against the testing domain/profile:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/up.sh --profile test ...
deploy/aws-cli-downloads/outputs.sh --profile test ...
```

Verify:

- CloudFormation stack reaches a complete state
- Route 53 alias records exist
- CloudFront distribution exists
- S3 bucket is not publicly readable/listable
- CloudFront can serve uploaded test objects after `upload-installer.sh` exists

## Completion Notes

Added during completion on 2026-06-18.

The testing stack was created successfully:

```text
stack: crystal-lattice-cli-downloads-test
domain: download.crystallattice.dev.dynamicprogrammingsolutions.com
bucket: crystal-lattice-cli-downloads-test-874087778966
CloudFront distribution: E2SBEYDBKC4Y7A
```

The bucket public access block and policy status were checked and the bucket is not public. Teardown was intentionally not tested because the live testing stack is still useful for the remaining release smoke work.
