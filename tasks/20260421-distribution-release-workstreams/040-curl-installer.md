# Curl Installer

Provide a one-line shell installer that detects the user platform, downloads the correct release asset, and installs the command locally.

## Requirements checklist

- [ ] Add an install script that supports latest-release install and pinned-version install.
- [ ] Detect supported OS and architecture combinations.
- [ ] Download the matching GitHub Release archive and install the command into a configurable directory.
- [ ] Document default install location, PATH behavior, and manual review instructions.

Parent Task: `tasks/20260421-distribution-release-workstreams/000-main.md`

Depends On: `tasks/20260421-distribution-release-workstreams/030-github-releases-and-ci.md`

## Current state

- There is not yet an installer script in the repo dedicated to release downloads.
- This installer is expected to consume GitHub Release assets produced by the binary and CI subtasks.

## Proposed solution from conversation

- Add a script such as `scripts/install.sh` that users can run via:

  ```bash
  curl -fsSL https://raw.githubusercontent.com/<org>/<repo>/main/scripts/install.sh | bash
  ```

- Have the script:
  - detect `uname -s` / `uname -m`,
  - fetch the latest GitHub Release tag via the GitHub API unless `VERSION` is provided,
  - construct the expected asset filename,
  - download and extract the matching archive,
  - install `crystal-lattice` into `$HOME/.local/bin` by default,
  - allow `INSTALL_DIR` override for custom or privileged installs.
- Also document the safer review-first path: download the script, inspect it, then run it locally.

## Deliverables

- `scripts/install.sh`.
- README usage examples for latest and pinned installs.
- Platform support table and error behavior for unsupported systems.