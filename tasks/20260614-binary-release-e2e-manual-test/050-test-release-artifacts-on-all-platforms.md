# Test Release Artifacts On All Platforms

Manually test the GitHub Actions-built release artifacts on every supported platform and record install/runtime evidence.

## Requirements checklist

- [ ] Test Linux amd64 bash installer flow.
- [ ] Test macOS Intel bash installer flow.
- [ ] Test macOS Apple Silicon bash installer flow.
- [ ] Test Windows amd64 `.zip` archive flow.
- [ ] Verify latest install on macOS/Linux.
- [ ] Verify pinned install on macOS/Linux.
- [ ] Verify custom-domain download path.
- [ ] Verify runtime layout reports `python-runtime`.
- [ ] Verify default config starts without source-checkout paths.
- [ ] Record per-platform evidence and failures.

Parent Task: `tasks/20260614-binary-release-e2e-manual-test/000-main.md`

Depends On:

- `tasks/20260614-binary-release-e2e-manual-test/020-prepare-manual-test-commands.md`
- `tasks/20260614-binary-release-e2e-manual-test/030-set-up-temporary-download-domain.md`

## Context

Official release artifacts are produced by `.github/workflows/release-crystal-lattice-cli.yml`. The workflow builds release archives under `dist/crystal-lattice-python-runtime` on each platform runner, smoke-tests them with `scripts/smoke_test_crystal_lattice_python_runtime_archive.py`, and uploads them to the GitHub Release and S3 download location.

Expected artifact names:

```text
crystal-lattice-python-runtime-v<version>-linux-amd64.tar.gz
crystal-lattice-python-runtime-v<version>-darwin-amd64.tar.gz
crystal-lattice-python-runtime-v<version>-darwin-arm64.tar.gz
crystal-lattice-python-runtime-v<version>-windows-amd64.zip
```

## macOS/Linux Installer Checks

Use isolated install locations where possible:

```bash
VERSION="<version>"
DOWNLOAD_BASE_URL="https://downloads.crystallattice.dev.dynamicprogrammingsolutions.com/crystal-lattice-cli"
TEST_ROOT="$(mktemp -d)"
INSTALL_ROOT="$TEST_ROOT/opt/crystal-lattice-cli"
BIN_DIR="$TEST_ROOT/bin"

curl -fsSL "$DOWNLOAD_BASE_URL/install.sh" | \
  CRYSTAL_LATTICE_DOWNLOAD_BASE_URL="$DOWNLOAD_BASE_URL" \
  INSTALL_ROOT="$INSTALL_ROOT" \
  BIN_DIR="$BIN_DIR" \
  bash

"$BIN_DIR/crystal-lattice" --help
"$BIN_DIR/crystal-lattice" --runtime-layout-json
```

Pinned install:

```bash
curl -fsSL "$DOWNLOAD_BASE_URL/install.sh" | \
  VERSION="$VERSION" \
  CRYSTAL_LATTICE_DOWNLOAD_BASE_URL="$DOWNLOAD_BASE_URL" \
  INSTALL_ROOT="$INSTALL_ROOT" \
  BIN_DIR="$BIN_DIR" \
  bash
```

The runtime layout output must include:

```json
{
  "layout": "python-runtime"
}
```

Also verify that bundled plugin paths point inside the installed bundle, not the source checkout.

## Windows Archive Checks

Prepare a Windows-specific command block during completion. It should cover:

- download `.zip`
- extract into a temporary directory
- run the packaged command from the extracted bundle
- verify `--help`
- verify `--runtime-layout-json`
- verify default config can be initialized/used

If Windows lacks a direct installer wrapper, record that as current expected behavior, not a failure.

## Evidence Template

For each platform:

```text
Platform:
Architecture:
OS version:
Shell:
Artifact URL:
Install method:
Version:
latest.txt result:
Pinned install result:
runtime-layout-json summary:
Default config result:
Unexpected source-checkout references:
Pass/fail:
Notes:
```

## Cleanup

Use the prepared cleanup commands from `020-prepare-manual-test-commands.md`. Ensure cleanup only removes test-specific install roots and temp paths.
