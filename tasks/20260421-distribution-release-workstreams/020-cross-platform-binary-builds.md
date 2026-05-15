# Cross-Platform Binary Builds

Define and implement the reproducible build process that creates self-contained desktop/server binaries for Linux, macOS, and Windows.

## Requirements checklist

- [x] Choose the bundled binary format (`--onedir` vs `--onefile`) and document why.
- [x] Create a repeatable build command or script for Linux, macOS, and Windows.
- [x] Standardize output folder layout and archive naming for release assets.
- [x] Verify that the binaries include Python and do not require a system Python installation.

Parent Task: `tasks/20260421-distribution-release-workstreams/000-main.md`

Depends On: `tasks/20260421-distribution-release-workstreams/010-python-packaging-and-cli.md`

## Current state

- The Python package metadata exists, but there is not yet a checked-in binary build workflow in the repo.
- `application/python/pyproject.toml:5-29` defines the `crystal-lattice-cli` distribution, dependencies, and `crystal-lattice` console script, which makes it a good PyInstaller input.
- The planning discussion assumed three desktop/server targets: Linux, macOS, and Windows.

## Proposed solution from conversation

- Use PyInstaller as the initial bundling tool because it is straightforward and widely used for Python CLI/server tools.
- Prefer `--onedir` for the first release wave so the generated files stay separate and easier to inspect/debug than a single fused executable.
- Build one archive per platform, each containing the launcher plus its bundled Python runtime and dependencies.
- Adopt a consistent asset naming scheme such as:
  - `crystal-lattice-cli-v0.2.0-linux-amd64.tar.gz`
  - `crystal-lattice-cli-v0.2.0-darwin-arm64.tar.gz`
  - `crystal-lattice-cli-v0.2.0-windows-amd64.zip`
- The executable inside each archive should be named `crystal-lattice`.
- Treat these archives as the source artifacts that downstream installers and package managers consume.

## Deliverables

- Build script or documented commands for each target OS.
- Chosen artifact naming convention.
- Notes on any platform-specific caveats, especially Windows packaging and macOS architecture handling.

## Execution plan

Added during completion.

1. Add an application-owned runtime layout manifest and helper for bundle-owned and user-owned paths. Keep `CONFIG_DIR` derived from the selected config file, but move default config/session path policy and bundle-owned paths such as `BUILTIN_PLUGINS` into the manifest.
2. Use the runtime layout helper from terminal app startup paths, including `__main__.py`, direct terminal defaults, and direct FastAPI defaults, so all `AgentApplication` instances receive `BUILTIN_PLUGINS` through `env_overrides`.
3. Update default config bootstrapping to read bundled template assets from the runtime layout rather than hardcoded `Path(__file__).parent / "default_config"`, while excluding generated/auth/cache directories.
4. Add package-data metadata for non-Python runtime assets required by source installs and binary builds, without packaging generated auth or plugin cache material.
5. Remove tracked/generated auth material from the default config tree and add ignore rules so release bundles do not ship private auth/cache state.
6. Add a repeatable PyInstaller `--onedir` build script that reads the `crystal-lattice-cli` version, detects platform/architecture, includes app assets and sanitized repo-root `plugins/`, generates a bundled runtime manifest, and creates a versioned archive containing the `crystal-lattice` executable.
7. Add binary build dependencies and documentation for local platform builds, artifact naming, and the fact that PyInstaller builds must be produced on each target OS rather than cross-compiled.
8. Add focused tests for runtime layout resolution and packaging metadata. Verify on the current platform where possible; defer native Linux/macOS/Windows binary assertions to Task 3's CI matrix.

## Completion Notes

Added during completion.

- Added `agent_terminal_app/runtime_layout.json` and `agent_terminal_app/runtime_layout.py` as the central runtime layout manifest/helper. `CONFIG_DIR` remains derived from the selected config file, while the manifest defines bundle-owned paths such as `BUILTIN_PLUGINS` and default user paths such as config/session locations.
- Wired terminal app startup paths to pass manifest-derived `BUILTIN_PLUGINS` through `env_overrides`, including `__main__.py`, direct FastAPI defaults, and direct terminal defaults.
- Updated default config bootstrapping to read from the manifest-defined template directory and skip generated/private directories such as `auth`, `.plugin_cache`, and `__pycache__`.
- Removed tracked generated auth material from `application/python/agent_terminal_app/default_config/auth/` and added ignore rules for default-config auth/cache state.
- Added package-data metadata and a `binary` optional dependency group for PyInstaller builds.
- Added `scripts/build_crystal_lattice_binary.py`, which stages sanitized app assets, generates a bundled runtime manifest, copies sanitized repo-root `plugins/`, builds PyInstaller `--onedir`, verifies required/forbidden paths, and creates versioned release archives such as `crystal-lattice-cli-v0.1.0-darwin-arm64.tar.gz`.
- Updated `application/python/README.md` with binary build instructions, artifact naming, runtime layout behavior, and cross-platform caveats.
- Added runtime layout and packaging metadata tests.
- Added a Docker-backed Linux packaging integration test at `application/python/tests/test_binary_distribution_docker.py`, with Docker/smoke fixtures under `application/python/tests/fixtures/binary_distribution/`. It exports the staged Git index into a clean snapshot, builds the Linux bundle in a Python builder container, then validates the archive in a separate Ubuntu runtime container.
- Verified on the current macOS arm64 environment:
  - `pytest application/python/tests/test_packaging_metadata.py application/python/tests/test_runtime_layout.py -q`
  - `python -m py_compile scripts/build_crystal_lattice_binary.py application/python/agent_terminal_app/runtime_layout.py application/python/agent_terminal_app/__main__.py application/python/agent_terminal_app/server.py application/python/agent_terminal_app/terminal.py`
  - `crystal-lattice --runtime-layout-json` produces parseable source-layout JSON
  - `python scripts/build_crystal_lattice_binary.py`
  - `application/python/dist/crystal-lattice/crystal-lattice --help`
  - `application/python/dist/crystal-lattice/crystal-lattice --runtime-layout-json` produces parseable bundled-layout JSON with `BUILTIN_PLUGINS` under `_internal/plugins`
  - `dist/crystal-lattice/crystal-lattice-cli-v0.1.0-darwin-arm64.tar.gz` contains the executable, bundled runtime manifest, and bundled plugin tree, and does not contain default-config auth/cache directories
- Verified the Docker Linux packaging test with `pytest application/python/tests/test_binary_distribution_docker.py -q`
- Native Linux and Windows build assertions remain for Task 3's GitHub Actions matrix, because those binaries need to be built and tested on matching OS runners.