# GitHub Releases And CI

Automate testing, cross-platform binary compilation, and GitHub Release publishing from version tags.

## Requirements checklist

- [ ] Define the tag naming convention that triggers releases.
- [ ] Add a GitHub Actions workflow that runs tests before building artifacts.
- [ ] Build Linux, macOS, and Windows release assets in a matrix.
- [ ] Upload assets to a GitHub Release associated with the release tag.
- [ ] Ensure the resulting asset names match the conventions expected by installers.

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