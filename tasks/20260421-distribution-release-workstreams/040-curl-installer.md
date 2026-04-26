# Curl Installer

Provide a one-line shell installer that detects the user platform, downloads the correct release asset, and installs the command locally.

## Requirements checklist

- [x] Add an install script that supports latest-release install and pinned-version install.
- [x] Detect supported OS and architecture combinations.
- [x] Download the matching GitHub Release archive and install the command into a configurable directory.
- [x] Document default install location, PATH behavior, and manual review instructions.

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

## Execution plan

Added during completion.

1. Add `scripts/install.sh` as a Bash installer for Unix-like systems. It should support `VERSION=0.1.0`, `VERSION=crystal-lattice-cli-v0.1.0`, or latest-version install via a `latest.txt` file.
2. Default downloads to a public S3 base URL, but keep the base configurable with an environment variable so the project can later switch to CloudFront, GitHub Releases, or another bucket without changing installer logic.
3. Detect `darwin-amd64`, `darwin-arm64`, and `linux-amd64` for the shell installer. Leave Windows to the zip asset/manual or future PowerShell installer.
4. Install from the downloaded archive into `~/.local/opt/crystal-lattice-cli/<archive-stem>/` and link `~/.local/bin/crystal-lattice`, matching the local production rehearsal layout.
5. Verify the installed command by running `--help` and `--runtime-layout-json`, asserting the runtime layout is bundled.
6. Add a small S3 publishing helper so release assets and `install.sh` can be uploaded to the public bucket with one command.
7. Create the public S3 bucket using AWS CLI, disable bucket-level public-access blocking for this download bucket, add a read-only `s3:GetObject` bucket policy, and upload the current `0.1.0` assets plus `latest.txt`.
8. Document the public S3 install URL, pinned install, review-first install, configurable locations, and how to turn off/change the bucket later.

## Completion Notes

Added during completion.

- Created public S3 bucket `crystal-lattice-downloads-874087778966` in `us-east-1` for installer/download hosting while the GitHub repository remains private.
- Configured the bucket for public object reads with a bucket policy granting `s3:GetObject` on `arn:aws:s3:::crystal-lattice-downloads-874087778966/*`. Public listing is not granted.
- Added `scripts/install.sh`, a Bash installer that reads `latest.txt` when `VERSION` is unset, supports pinned `VERSION=0.1.0` / `VERSION=crystal-lattice-cli-v0.1.0`, detects `darwin-amd64`, `darwin-arm64`, and `linux-amd64`, downloads the matching `.tar.gz`, installs under `~/.local/opt/crystal-lattice-cli`, links `~/.local/bin/crystal-lattice`, and verifies bundled runtime layout.
- Added `scripts/publish_crystal_lattice_s3.py` to publish `install.sh`, `latest.txt`, and the four release archives to the S3 download prefix.
- Published the current `crystal-lattice-cli-v0.1.0` release assets from GitHub Releases to `https://crystal-lattice-downloads-874087778966.s3.us-east-1.amazonaws.com/crystal-lattice-cli`.
- Updated `application/python/README.md` with latest install, pinned install, review-first install, supported platforms, default paths, override variables, S3 publishing, and commands to disable public S3 access.
- Verified public unauthenticated access to `latest.txt`, `install.sh`, and the `darwin-arm64` archive.
- Verified latest and pinned public S3 installer runs into temporary install roots on macOS arm64 and both installed commands report bundled runtime layout.