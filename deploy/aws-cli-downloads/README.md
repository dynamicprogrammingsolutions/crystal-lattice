# AWS CLI Downloads Deployment

This deployment hosts Crystal Lattice CLI release downloads on AWS using a
private S3 bucket, CloudFront Origin Access Control, ACM, and Route 53.

It is intentionally separate from the binary build itself. Official release
archives are built by the GitHub Actions matrix in
`.github/workflows/release-crystal-lattice-cli.yml`. The scripts here provision
the download endpoint, upload a domain-specific installer, configure GitHub
publishing credentials, promote existing GitHub Release assets, and smoke-test
the public download URL.

## Domains

Testing profile default:

```text
https://download.crystallattice.dev.dynamicprogrammingsolutions.com/crystal-lattice-cli
```

Production profile default:

```text
https://download.crystallattice.dev/crystal-lattice-cli
```

The scripts keep the host and path prefix configurable so the cutover from the
testing domain to production does not require rewriting release scripts.

## What The Stack Creates

- One private S3 bucket for CLI release assets.
- S3 public access blocks and bucket-owner-enforced object ownership.
- CloudFront Origin Access Control for the S3 origin.
- One ACM certificate in `us-east-1`.
- DNS validation records for the ACM certificate.
- One CloudFront distribution for the download domain.
- Route 53 `A` and `AAAA` alias records for the download domain.
- Short cache policy for `install.sh` and `latest.txt`.
- Long cache policy for immutable versioned `.tar.gz` and `.zip` archives.
- Conservative security response headers.

The public URL layout is:

```text
<base-url>/install.sh
<base-url>/latest.txt
<base-url>/crystal-lattice-python-runtime-v<version>-linux-amd64.tar.gz
<base-url>/crystal-lattice-python-runtime-v<version>-darwin-amd64.tar.gz
<base-url>/crystal-lattice-python-runtime-v<version>-darwin-arm64.tar.gz
<base-url>/crystal-lattice-python-runtime-v<version>-windows-amd64.zip
```

## Prerequisites

- AWS CLI configured locally.
- GitHub CLI authenticated locally for `gh` commands.
- Permission to create S3 buckets, CloudFront distributions, CloudFront
  policies, ACM certificates, IAM roles, and Route 53 records.
- Deploy in `us-east-1`; CloudFront certificates must be in `us-east-1`.
- `ALLOW_AWS_DEPLOY=1` for commands that create, update, upload, or delete AWS
  resources.

Confirm the testing hosted zone:

```bash
aws route53 list-hosted-zones-by-name \
  --dns-name dynamicprogrammingsolutions.com. \
  --query "HostedZones[?Name=='dynamicprogrammingsolutions.com.' && Config.PrivateZone==\`false\`].[Id,Name]" \
  --output table
```

Confirm the production hosted zone:

```bash
aws route53 list-hosted-zones-by-name \
  --dns-name crystallattice.dev. \
  --query "HostedZones[?Name=='crystallattice.dev.' && Config.PrivateZone==\`false\`].[Id,Name]" \
  --output table
```

## Test Infrastructure

Create or update the testing download infrastructure and upload a
testing-domain installer:

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

`up.sh` provisions infrastructure and uploads `install.sh`. It does not build
release archives. The GitHub Actions matrix builds official platform archives.

Print stack outputs:

```bash
deploy/aws-cli-downloads/outputs.sh --profile test
```

Upload or refresh only the installer:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/upload-installer.sh --profile test
```

Optionally bootstrap `latest.txt` while testing:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/upload-installer.sh \
  --profile test \
  --latest-version 0.1.0
```

Inspect the generated installer without uploading:

```bash
deploy/aws-cli-downloads/upload-installer.sh \
  --profile test \
  --base-url https://download.crystallattice.dev.dynamicprogrammingsolutions.com/crystal-lattice-cli \
  --print
```

## Production Infrastructure

Create or update the production download infrastructure:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/up.sh \
  --profile prod \
  --stack-name crystal-lattice-cli-downloads-prod \
  --region us-east-1 \
  --hosted-zone-name crystallattice.dev \
  --download-domain download.crystallattice.dev \
  --bucket-name-prefix crystal-lattice-cli-downloads-prod \
  --prefix crystal-lattice-cli
```

## GitHub Actions Setup

The release workflow uses GitHub Actions OIDC. Do not create long-lived AWS
access keys for this path.

After the testing download stack exists, create or update the AWS OIDC role:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/create-github-oidc-role.sh \
  --profile test \
  --github-owner dynamicprogrammingsolutions \
  --github-repo crystal-lattice \
  --github-branch main
```

The role trusts release tags matching:

```text
refs/tags/crystal-lattice-cli-v*
```

It also trusts one branch for workflow testing, defaulting to `main`.

Preview GitHub variable/secret updates:

```bash
deploy/aws-cli-downloads/configure-github-actions-vars.sh \
  --profile test \
  --repo dynamicprogrammingsolutions/crystal-lattice \
  --dry-run
```

Apply GitHub variable/secret updates:

```bash
deploy/aws-cli-downloads/configure-github-actions-vars.sh \
  --profile test \
  --repo dynamicprogrammingsolutions/crystal-lattice
```

The script sets:

```text
AWS_REGION
CLI_DOWNLOADS_BUCKET
CLI_DOWNLOADS_PREFIX
CLI_DOWNLOADS_BASE_URL
CLI_DOWNLOADS_CLOUDFRONT_DISTRIBUTION_ID
CLI_DOWNLOADS_AWS_ROLE_TO_ASSUME
```

For production, run the same commands with `--profile prod` after the
production stack exists.

## Manual Asset Publish

Publish already-built local release assets to the testing domain:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/publish-assets.sh \
  --profile test \
  --assets-dir dist/crystal-lattice-python-runtime \
  --version 0.1.0
```

This validates all four expected archives, uploads a generated installer,
writes `latest.txt`, uploads archives, and invalidates CloudFront.

## Release Orchestration

Dry-run a release:

```bash
deploy/aws-cli-downloads/release.sh \
  --profile test \
  --version 0.1.0 \
  --dry-run
```

Create and push the release tag, then watch GitHub Actions:

```bash
deploy/aws-cli-downloads/release.sh \
  --profile test \
  --version 0.1.0 \
  --push-tag \
  --watch
```

The script validates the local version and tag, then lets GitHub Actions run
the official matrix build. It does not build all release archives locally.

## Promote Existing GitHub Release

Promote an existing GitHub Release to the testing domain:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/promote-github-release.sh \
  --profile test \
  --version 0.1.0 \
  --repo dynamicprogrammingsolutions/crystal-lattice
```

Promote the same GitHub Release to production:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/promote-github-release.sh \
  --profile prod \
  --version 0.1.0 \
  --repo dynamicprogrammingsolutions/crystal-lattice
```

Use promotion when the artifacts already exist and only the download domain or
`latest.txt` target needs to change.

For `0.1.0`, the original GitHub Release used older asset names and cannot be
promoted with `promote-github-release.sh`. If you validated artifacts from a
workflow-dispatch run instead, download those artifacts and publish the local
asset directory:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/publish-assets.sh \
  --profile prod \
  --assets-dir /path/to/release-assets \
  --version 0.1.0
```

## Smoke Testing

Smoke-test the testing download URL:

```bash
deploy/aws-cli-downloads/smoke.sh --profile test
```

Smoke-test a specific URL/version:

```bash
deploy/aws-cli-downloads/smoke.sh \
  --base-url https://download.crystallattice.dev.dynamicprogrammingsolutions.com/crystal-lattice-cli \
  --version 0.1.0
```

On macOS and Linux, the smoke script also runs the installer into temporary
paths and verifies:

```bash
crystal-lattice --help
crystal-lattice --runtime-layout-json
```

On Windows, run the shell installer from Git Bash/MSYS/Cygwin. The installer
detects `MINGW*`, `MSYS*`, and `CYGWIN*` from `uname -s`, downloads the
`windows-amd64` `.zip` archive, and writes a Bash shim that calls the bundled
`Scripts/crystal-lattice.cmd` launcher.

Skip installer execution and only check URLs/content:

```bash
deploy/aws-cli-downloads/smoke.sh --profile test --skip-install
```

## Test To Production Cutover

Recommended cutover:

1. Deploy/update the testing stack.
2. Configure GitHub variables/secrets for testing.
3. Run or promote a release to the testing domain.
4. Run `deploy/aws-cli-downloads/smoke.sh --profile test`.
5. Deploy/update the production stack.
6. Configure GitHub variables/secrets for production.
7. Promote the same GitHub Release to production, or publish the validated
   workflow artifacts with `publish-assets.sh` if the GitHub Release assets do
   not use the current `crystal-lattice-python-runtime-v<version>-...` names.
8. Run `deploy/aws-cli-downloads/smoke.sh --profile prod`.
9. Update `scripts/install.sh` `DEFAULT_DOWNLOAD_BASE_URL` if production is now
   the canonical default.
10. Update `README.md` and `application/python/README.md` install commands.
11. Create a follow-up release so the published source installer default is
   canonical.

Pinned install examples should set `VERSION` for the `bash` process:

```bash
curl -fsSL https://download.crystallattice.dev/crystal-lattice-cli/install.sh | \
  VERSION=0.1.0 \
  bash
```

Override the base URL without changing the installer default:

```bash
curl -fsSL https://download.crystallattice.dev/crystal-lattice-cli/install.sh | \
  CRYSTAL_LATTICE_DOWNLOAD_BASE_URL=https://download.crystallattice.dev.dynamicprogrammingsolutions.com/crystal-lattice-cli \
  bash
```

## Teardown

Delete the testing stack and empty its bucket first:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/down.sh --profile test
```

Delete production only when intentionally retiring the endpoint:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/down.sh --profile prod
```
