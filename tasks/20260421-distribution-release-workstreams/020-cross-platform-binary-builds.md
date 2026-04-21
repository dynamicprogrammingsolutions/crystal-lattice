# Cross-Platform Binary Builds

Define and implement the reproducible build process that creates self-contained desktop/server binaries for Linux, macOS, and Windows.

## Requirements checklist

- [ ] Choose the bundled binary format (`--onedir` vs `--onefile`) and document why.
- [ ] Create a repeatable build command or script for Linux, macOS, and Windows.
- [ ] Standardize output folder layout and archive naming for release assets.
- [ ] Verify that the binaries include Python and do not require a system Python installation.

Parent Task: `tasks/20260421-distribution-release-workstreams/000-main.md`

Depends On: `tasks/20260421-distribution-release-workstreams/010-python-packaging-and-cli.md`

## Current state

- The Python package metadata exists, but there is not yet a checked-in binary build workflow in the repo.
- `application/python/pyproject.toml:5-26` defines the app package and its dependencies, which makes it a good PyInstaller input once the CLI entrypoint is stabilized.
- The planning discussion assumed three desktop/server targets: Linux, macOS, and Windows.

## Proposed solution from conversation

- Use PyInstaller as the initial bundling tool because it is straightforward and widely used for Python CLI/server tools.
- Prefer `--onedir` for the first release wave so the generated files stay separate and easier to inspect/debug than a single fused executable.
- Build one archive per platform, each containing the launcher plus its bundled Python runtime and dependencies.
- Adopt a consistent asset naming scheme such as:
  - `agent-terminal-app-v0.2.0-linux-amd64.tar.gz`
  - `agent-terminal-app-v0.2.0-darwin-arm64.tar.gz`
  - `agent-terminal-app-v0.2.0-windows-amd64.zip`
- Treat these archives as the source artifacts that downstream installers and package managers consume.

## Deliverables

- Build script or documented commands for each target OS.
- Chosen artifact naming convention.
- Notes on any platform-specific caveats, especially Windows packaging and macOS architecture handling.