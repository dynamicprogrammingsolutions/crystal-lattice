# Prepare Manual Test Commands

Prepare clear, copy/paste-friendly command blocks for developers who will run the binary release manual test and assess the developer UX.

## Requirements checklist

- [ ] Prepare release workflow dry-run commands.
- [ ] Prepare official release/tag commands.
- [ ] Prepare artifact download and verification commands.
- [ ] Prepare macOS/Linux bash installer commands.
- [ ] Prepare pinned install commands.
- [ ] Prepare custom-domain install commands.
- [ ] Prepare Windows archive extraction and verification commands.
- [ ] Prepare fresh config/session setup commands.
- [ ] Prepare real LLM/tool-call validation commands or HTTP requests.
- [ ] Prepare custom user plugin commands.
- [ ] Prepare bundled non-default plugin commands.
- [ ] Prepare cleanup commands.
- [ ] Add an evidence template developers can fill in while testing.

Parent Task: `tasks/20260614-binary-release-e2e-manual-test/000-main.md`

Depends On: `tasks/20260614-binary-release-e2e-manual-test/010-define-manual-test-matrix.md`

## Context

The current release docs are in `application/python/README.md`, especially:

- `Release And Distribution`
- `Curl Installer / S3 Downloads`
- `GitHub Release Workflow`
- `Local Nox Scripts`

The installer supports override variables:

```bash
INSTALL_ROOT="$HOME/.local/opt/crystal-lattice-cli"
BIN_DIR="$HOME/.local/bin"
COMMAND_NAME="crystal-lattice"
CRYSTAL_LATTICE_DOWNLOAD_BASE_URL="https://example.com/crystal-lattice-cli"
```

`CRYSTAL_LATTICE_DOWNLOAD_BASE_URL` must point to a URL base containing:

- `install.sh`
- `latest.txt`
- platform release archives

## Commands To Prepare

Prepare commands in a human-friendly sequence. Prefer variables at the top of each block, for example:

```bash
VERSION="0.1.0"
DOWNLOAD_BASE_URL="https://downloads.crystallattice.dev.dynamicprogrammingsolutions.com/crystal-lattice-cli"
INSTALL_ROOT="$(mktemp -d)/opt/crystal-lattice-cli"
BIN_DIR="$(mktemp -d)/bin"
```

Prepare a latest install command:

```bash
curl -fsSL "$DOWNLOAD_BASE_URL/install.sh" | \
  CRYSTAL_LATTICE_DOWNLOAD_BASE_URL="$DOWNLOAD_BASE_URL" \
  INSTALL_ROOT="$INSTALL_ROOT" \
  BIN_DIR="$BIN_DIR" \
  bash
```

Prepare a pinned install command in the correct pipeline shape:

```bash
curl -fsSL "$DOWNLOAD_BASE_URL/install.sh" | \
  VERSION="$VERSION" \
  CRYSTAL_LATTICE_DOWNLOAD_BASE_URL="$DOWNLOAD_BASE_URL" \
  INSTALL_ROOT="$INSTALL_ROOT" \
  BIN_DIR="$BIN_DIR" \
  bash
```

Note: setting `VERSION=...` before `curl` only applies it to `curl`; the pinned version must be available to the `bash` process that executes the installer.

Prepare verification commands:

```bash
"$BIN_DIR/crystal-lattice" --help
"$BIN_DIR/crystal-lattice" --runtime-layout-json
```

Prepare cleanup commands that do not delete unrelated user state:

```bash
rm -rf "$INSTALL_ROOT"
rm -f "$BIN_DIR/crystal-lattice"
```

## Evidence Template

Include this template in the final command handoff:

```text
Tester:
Date:
Platform:
Machine architecture:
Artifact version:
Artifact source URL:
Install command used:
Runtime layout result:
Default config result:
Provider/API key path:
LLM prompt:
Tool call observed:
Custom user plugin:
Custom user plugin result:
Bundled non-default plugin:
Bundled plugin result:
Cleanup result:
UX notes:
Failure details:
```

## Docs Friction To Watch

While preparing commands, flag any small README changes that would make the workflow easier. Likely candidates:

- pinned install command shape
- custom domain install example
- manual release verification checklist
- fresh checkout dev/prod install commands
- Windows archive install notes
