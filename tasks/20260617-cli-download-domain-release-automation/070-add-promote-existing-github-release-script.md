# Add Promote Existing GitHub Release Script

Add a script that promotes already-built GitHub Release assets to the selected test or production download domain without rebuilding platform artifacts.

## Requirements checklist

- [x] Add `deploy/aws-cli-downloads/promote-github-release.sh`.
- [x] Download release assets from GitHub for a given version/tag.
- [x] Validate all four expected release archives are present.
- [x] Generate/upload a domain-correct `install.sh`.
- [x] Upload release archives to the selected bucket/prefix.
- [x] Write/upload `latest.txt`.
- [x] Invalidate CloudFront.
- [x] Reuse or call `publish-assets.sh` for local asset upload.
- [x] Document promotion flow in the README.
- [ ] Test promotion against the testing domain.
- [x] Document production promotion from test-validated artifacts.

Parent Task: `tasks/20260617-cli-download-domain-release-automation/000-main.md`

Depends On:

- `tasks/20260617-cli-download-domain-release-automation/030-add-domain-aware-installer-upload.md`
- `tasks/20260617-cli-download-domain-release-automation/040-add-github-oidc-role-and-vars-setup.md`

## Purpose

This script supports switching from the testing download domain to the production download domain without asking developers to rebuild platform artifacts locally.

The source of truth is a completed GitHub Release such as:

```text
crystal-lattice-cli-v0.2.0
```

The script should fetch those release assets, validate them, upload them to the selected download stack, generate the correct installer for that domain, update `latest.txt`, and smoke-test or print the smoke command.

## Expected Commands

Promote to testing domain:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/promote-github-release.sh \
  --profile test \
  --version 0.2.0 \
  --repo dynamicprogrammingsolutions/crystal-lattice
```

Promote the same release to production:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/promote-github-release.sh \
  --profile prod \
  --version 0.2.0 \
  --repo dynamicprogrammingsolutions/crystal-lattice
```

The script should support a `--dry-run` mode that prints `gh` and `aws` commands without mutating AWS.

## Local Asset Publish Helper

If adding `publish-assets.sh`, it should accept:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/publish-assets.sh \
  --profile test \
  --assets-dir /path/to/release-assets \
  --version 0.2.0
```

This helper should validate artifact names and upload:

```text
install.sh
latest.txt
crystal-lattice-python-runtime-v<version>-linux-amd64.tar.gz
crystal-lattice-python-runtime-v<version>-darwin-amd64.tar.gz
crystal-lattice-python-runtime-v<version>-darwin-arm64.tar.gz
crystal-lattice-python-runtime-v<version>-windows-amd64.zip
```

## Documentation Requirements

README must include:

- when to use promotion instead of a new release
- how to promote a GitHub Release to the testing domain
- how to promote the same release to production
- how to inspect downloaded assets
- how to avoid accidentally changing `latest.txt`
- rollback options, such as promoting the previous version

## Testing Requirements

Against the testing domain:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/promote-github-release.sh \
  --profile test \
  --version <existing-version> \
  --dry-run
```

Then, when approved:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/promote-github-release.sh \
  --profile test \
  --version <existing-version>
```

Verify:

- all expected assets were downloaded from GitHub
- all expected assets were uploaded to the testing bucket/prefix
- `latest.txt` contains the expected tag
- generated installer points at the testing domain
- CloudFront invalidation was created
- `smoke.sh` passes on the testing domain

## Completion Notes

Added during completion on 2026-06-18.

The promotion script exists, but it was not used for the live testing-domain publish because the existing `crystal-lattice-cli-v0.1.0` GitHub Release assets use older asset names. The current installer and `publish-assets.sh` expect `crystal-lattice-python-runtime-v0.1.0-*` archive names.
