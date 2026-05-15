# GitHub Releases And CI

Automate testing, cross-platform binary compilation, and GitHub Release publishing from version tags.

## Requirements checklist

- [x] Define the tag naming convention that triggers releases.
- [x] Add a GitHub Actions workflow that runs tests before building artifacts.
- [x] Build Linux, macOS, and Windows release assets in a matrix.
- [x] Upload assets to a GitHub Release associated with the release tag.
- [x] Ensure the resulting asset names match the conventions expected by installers.

Parent Task: `tasks/20260421-distribution-release-workstreams/000-main.md`

Depends On: `tasks/20260421-distribution-release-workstreams/010-python-packaging-and-cli.md`, `tasks/20260421-distribution-release-workstreams/020-cross-platform-binary-builds.md`

## Current state

- There is not yet a checked-in release workflow for the Python app.
- Existing package metadata in `core/python/pyproject.toml:5-43` and `application/python/pyproject.toml:5-29` provides the version anchors needed for a tag-based release process.
- The intended release host from planning is GitHub Releases, with CI building artifacts during the release flow rather than maintainers compiling locally.

## Proposed solution from conversation

- Use a tag-driven GitHub Actions workflow, triggered by tags such as `crystal-lattice-cli-v0.2.0`.
- Structure the workflow in two stages:
  - a test job that runs once,
  - a matrix build job for `ubuntu-latest`, `macos-latest`, and `windows-latest`.
- In each matrix job:
  - install Python,
  - install the project plus bundling tools,
  - run the chosen binary build command,
  - run `crystal-lattice --runtime-layout-json` from the built output and assert it emits parseable JSON with bundled paths,
  - assert required archive contents exist and generated/private default-config auth/cache paths are absent,
  - archive the output into a versioned `.tar.gz` or `.zip`.
- Use a release action such as `softprops/action-gh-release` to create or update the GitHub Release and upload every platform artifact.
- Make GitHub Releases the canonical source for binary downloads used by `curl`, Homebrew, and optional npm distribution.

## Deliverables

- `.github/workflows/release.yml` or equivalent.
- Release/tag naming documentation.
- A maintainer checklist for version bump, tag creation, and release verification.

## Execution plan

Added during completion.

1. Add a cross-platform archive smoke-test helper that can validate both `.tar.gz` and `.zip` release archives. It should extract the archive, assert the bundled executable and runtime assets exist, assert generated/private auth/cache paths are absent, run `--help`, run `--runtime-layout-json`, and verify the runtime layout is bundled with `BUILTIN_PLUGINS` under `_internal/plugins`.
2. Add a GitHub Actions workflow triggered by `workflow_dispatch` and tags matching `crystal-lattice-cli-v*`.
3. Add a fast test gate that runs the non-integration core and application pytest suites before any release builds.
4. Add a native build matrix for `linux-amd64`, `darwin-amd64`, `darwin-arm64`, and `windows-amd64`. Use current GitHub-hosted macOS labels that cover both Intel and Apple Silicon runners.
5. In each build job, install the project with binary extras, run `scripts/build_crystal_lattice_binary.py` with the explicit matrix platform/architecture, smoke-test the produced archive, and upload it as a workflow artifact.
6. Add a publish job that only runs for tag pushes. It should download the platform artifacts and create or update a GitHub Release with the archives attached.
7. Validate that release tags match `application/python/pyproject.toml`'s package version so accidental mismatched releases fail early.
8. Update release documentation with the tag convention, dry-run workflow, artifact names, and maintainer checklist.

## Completion Notes

Added during completion.

- Added `.github/workflows/release-crystal-lattice-cli.yml`.
- The workflow runs on `workflow_dispatch` and tags matching `crystal-lattice-cli-v*`.
- Manual runs act as dry runs: they run tests, build and smoke-test every binary archive, and upload workflow artifacts without publishing a GitHub Release.
- Tag pushes validate that the tag matches `application/python/pyproject.toml`'s `project.version`, run the same test/build matrix, then publish the archives to GitHub Releases.
- The build matrix creates four release assets: `linux-amd64`, `darwin-amd64`, `darwin-arm64`, and `windows-amd64`.
- Added `scripts/smoke_test_crystal_lattice_archive.py` to validate `.tar.gz` and `.zip` archives by checking bundled files, rejecting private/generated default-config paths, running `--help`, and verifying bundled runtime layout JSON.
- Updated `application/python/README.md` with the release workflow, dry-run command, local `actionlint`/`act` validation commands, tag convention, expected artifacts, and maintainer checklist.
- Added `requests>=2.31.0` to `agent-core` dependencies after an `act` clean-environment run showed core provider tests import `plugins.openai_provider`, which requires `requests`.
- The workflow test job installs `plugins/openai_responses[dev]` because several application tests import that repo-root plugin directly and need its declared `openai` dependency in a clean CI environment.
- Local `act` verification passed for the workflow `test` job in a Linux amd64 container. A filtered `linux-amd64` build job also completed the native build, archive discovery, and smoke test locally; it only failed at `actions/upload-artifact` because local `act` does not provide GitHub's artifact runtime token by default.