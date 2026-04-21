# Homebrew Distribution

Set up a Homebrew-based install path for macOS and Linux users that reuses the published GitHub Release binaries.

## Requirements checklist

- [ ] Decide the tap repository name and formula naming convention.
- [ ] Create a formula that selects the correct asset for macOS/Linux and CPU architecture.
- [ ] Document how release asset checksums are generated and updated per release.
- [ ] Publish installation instructions using `brew tap` and `brew install`.

Parent Task: `tasks/20260421-distribution-release-workstreams/000-main.md`

Depends On: `tasks/20260421-distribution-release-workstreams/030-github-releases-and-ci.md`

## Current state

- There is not yet a Homebrew tap or formula in the repo.
- The planned release architecture treats GitHub Releases as the upstream source of versioned binary archives.

## Proposed solution from conversation

- Start with a custom tap such as `your-org/homebrew-agent-terminal-app` or `your-org/homebrew-tap` rather than targeting `homebrew-core` immediately.
- Use a formula that downloads prebuilt release archives instead of building from Python source inside Homebrew.
- In the formula, select the correct URL and SHA-256 for `darwin`/`linux` and `arm64`/`amd64`, then install the `agent-terminal-app` binary into Homebrew's `bin`.
- Keep the formula small and stable by reusing the same GitHub Release assets already produced for direct downloads and the `curl` installer.

## Deliverables

- A tap repo plan and formula template.
- Release checksum update instructions.
- User-facing install command examples.