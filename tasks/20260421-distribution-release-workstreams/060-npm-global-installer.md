# NPM Global Installer

Evaluate and, if worthwhile, implement an npm-based global install experience that downloads the bundled Python binary at install time.

## Requirements checklist

- [ ] Decide whether npm distribution is in scope for the first release wave.
- [ ] If in scope, create a minimal npm package structure with a stable global command.
- [ ] Implement a platform-aware postinstall download flow that mirrors the release asset naming convention.
- [ ] Document tradeoffs versus `curl`, Homebrew, and Python-native installation.

Parent Task: `tasks/20260421-distribution-release-workstreams/000-main.md`

Depends On: `tasks/20260421-distribution-release-workstreams/030-github-releases-and-ci.md`

## Current state

- There is not yet an npm package for this project.
- The current product is Python-based, so npm would be a convenience distribution layer rather than the primary build system.

## Proposed solution from conversation

- Treat npm as optional and secondary to GitHub Releases and `curl` installation.
- If implemented, publish a small npm package that:
  - exposes `agent-terminal-app` in the `bin` field,
  - runs a `postinstall` script that detects OS/arch,
  - downloads the matching release archive from GitHub Releases,
  - stores the executable under the package directory,
  - launches it through a small Node wrapper.
- Keep the actual bundled Python binaries out of the npm tarball where possible, and instead fetch them during `npm install -g`.

## Deliverables

- Go/no-go recommendation for npm distribution.
- If approved, npm package skeleton and publishing notes.
- Comparison notes for maintainers on support burden and user fit.