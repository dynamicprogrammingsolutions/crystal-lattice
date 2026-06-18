# Add Domain-Aware Installer Upload

Add scripts that generate and upload a domain-correct `install.sh` for the selected download profile, plus optional `latest.txt` bootstrap support.

## Requirements checklist

- [x] Add `deploy/aws-cli-downloads/upload-installer.sh`.
- [x] Generate installer content from `scripts/install.sh` with the selected base URL.
- [x] Preserve executable shell script behavior and existing installer overrides.
- [x] Upload generated `install.sh` to the configured bucket/prefix.
- [x] Optionally upload `latest.txt` when a version/tag is provided.
- [x] Set correct content types and cache-control metadata.
- [x] Invalidate CloudFront paths for `install.sh` and `latest.txt`.
- [x] Document installer generation and override behavior.
- [x] Test generated installer content against the testing domain.
- [x] Test current-platform installer run against the testing domain when matching artifacts exist.

Parent Task: `tasks/20260617-cli-download-domain-release-automation/000-main.md`

Depends On:

- `tasks/20260617-cli-download-domain-release-automation/010-design-download-hosting-and-release-boundaries.md`
- `tasks/20260617-cli-download-domain-release-automation/020-add-download-domain-infra-bootstrap.md`

## Why This Is Needed

`scripts/install.sh` currently contains a hardcoded `DEFAULT_DOWNLOAD_BASE_URL`. If the file is uploaded unchanged to another domain, this command:

```bash
curl -fsSL https://<new-domain>/crystal-lattice-cli/install.sh | bash
```

can still fetch `latest.txt` and archives from the old default URL. The upload path must produce an installer whose default base URL matches the selected test or production domain.

The installer should still support runtime override variables:

```bash
CRYSTAL_LATTICE_DOWNLOAD_BASE_URL=
DOWNLOAD_BASE_URL=
INSTALL_ROOT=
BIN_DIR=
COMMAND_NAME=
VERSION=
```

## Expected Command

Testing profile:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/upload-installer.sh \
  --profile test
```

Explicit base URL:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/upload-installer.sh \
  --stack-name crystal-lattice-cli-downloads-test \
  --region us-east-1 \
  --base-url https://download.crystallattice.dev.dynamicprogrammingsolutions.com/crystal-lattice-cli
```

Optional latest bootstrap:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/upload-installer.sh \
  --profile test \
  --latest-version 0.1.0
```

The script should normalize `latest.txt` to:

```text
crystal-lattice-cli-v<version>
```

## Documentation Requirements

Add README documentation for:

- why installer generation is domain-aware
- how to upload only the installer
- how to upload a temporary `latest.txt`
- how to inspect generated installer content before upload
- how to use `CRYSTAL_LATTICE_DOWNLOAD_BASE_URL` for override testing

## Testing Requirements

Run on testing profile:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/upload-installer.sh --profile test
curl -fsSL https://download.crystallattice.dev.dynamicprogrammingsolutions.com/crystal-lattice-cli/install.sh | rg "DEFAULT_DOWNLOAD_BASE_URL"
curl -fsSI https://download.crystallattice.dev.dynamicprogrammingsolutions.com/crystal-lattice-cli/install.sh
```

Verify:

- generated `DEFAULT_DOWNLOAD_BASE_URL` matches the testing domain
- installer still passes shell syntax checks:

  ```bash
  bash -n <generated-installer>
  ```

- `install.sh` is served with a reasonable shell/text content type
- CloudFront invalidation is created after upload

If release archives already exist on the testing domain, also test:

```bash
TEST_ROOT="$(mktemp -d)"
curl -fsSL https://download.crystallattice.dev.dynamicprogrammingsolutions.com/crystal-lattice-cli/install.sh | \
  INSTALL_ROOT="$TEST_ROOT/opt" \
  BIN_DIR="$TEST_ROOT/bin" \
  bash
"$TEST_ROOT/bin/crystal-lattice" --runtime-layout-json
```

## Completion Notes

Added during completion on 2026-06-18.

`install.sh` is served from the testing domain and contains the expected default:

```text
DEFAULT_DOWNLOAD_BASE_URL="https://download.crystallattice.dev.dynamicprogrammingsolutions.com/crystal-lattice-cli"
```

The current-platform installer run was attempted after publishing matching artifacts. It initially failed on macOS because the packaged `darwin-arm64` Python runtime depended on `/Library/Frameworks/Python.framework/Versions/3.11/Python`, which was not present on the smoke-test machine. This was fixed by switching the release workflow to uv-managed standalone Python runtimes and adding portability smoke checks.

After publishing artifacts from green workflow run `27746631545`, the current-platform installer smoke passed against:

```text
https://download.crystallattice.dev.dynamicprogrammingsolutions.com/crystal-lattice-cli
```
