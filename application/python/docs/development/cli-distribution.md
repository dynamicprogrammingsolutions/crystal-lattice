# CLI distribution implementation and verification

This page maps the current `crystal-lattice-cli` distribution implementation.
The [CLI distribution verification specification](specifications/cli-distribution/index.md)
defines the intended verification contract; this page does not redefine it.

## Distribution forms

The application package has two deliberately separate distribution forms.

| Distribution | Current role | Plugin behavior |
|---|---|---|
| Bundled-Python runtime archive | Shipped general CLI for installation and desktop/local use | Ships a normal Python runtime and built-in plugin sources. Default-config plugins are preinstalled; other supported plugins can install dynamically. |
| Optimized PyInstaller bundle | Config-specific frozen runtime produced from the full package or maintainer builder | Freezes selected plugins and rejects arbitrary dynamic plugin installation. |

The public installer consumes bundled-Python archives named
`crystal-lattice-python-runtime-v<version>-<platform>-<arch>`. Optimized
archives use a different layout, builder, and test suite.

## Current build and installation path

`scripts/build_crystal_lattice_python_runtime_package.py` stages:

- a Python runtime;
- Core and application source-shaped trees;
- built-in plugin sources;
- runtime and preinstalled-plugin manifests;
- Unix and Windows launchers;
- the inputs needed to produce a later optimized bundle.

With dependency installation enabled, the builder installs Core, the
application, and the default config's local plugin closure into the packaged
Python. `preinstalled-plugins.json` lets runtime plugin resolution import that
closure without copying it into user state.

`scripts/install.sh` is the user-facing installation authority. It downloads
or accepts a matching local archive, extracts it into a temporary staging
directory, replaces the versioned target under the install root, creates the
installed command in a suitable existing PATH directory, and verifies
`--runtime-layout-json` and `--help`.

The installed command is a small forwarding script that invokes the archive
launcher from its final versioned directory. On Windows the installer creates
both the Git Bash shell command and a `.cmd` command for native command lookup.

The principal local maintainer entry points are:

```bash
npm run build:bundle
npm run install:prod:local
```

Direct scripts back these npm commands. The bundled-Python build creates a
temporary host build venv and provisions an `uv`-managed Python 3.11 runtime
by default. The optimized PyInstaller build uses its own temporary build venv.
Neither installs or upgrades packages in the repository environment that
launched the command.

Set `CRYSTAL_PYTHON_RUNTIME` to build deliberately from another runtime
directory. `CRYSTAL_LATTICE_PYTHON_RUNTIME_ARCHIVE` lets the public installer
or either archive-based smoke use an existing matching archive.

Without `BIN_DIR`, the public installer selects an existing writable directory
already on PATH. It prefers a valid previous bundled-Python command,
`~/.local/bin`, and `~/bin`, then another suitable PATH directory. Installation
stops before replacing runtime state when no suitable directory exists.

## User-owned state

Archives and optimized bundles do not own mutable user data. The active config
directory owns configuration support files and the plugin installation cache.
Sessions, authentication state, and logs also remain outside the installed
runtime.

For the generated local config, these paths normally live under the
workspace's `.crystal/` directory. Replacing an installed runtime must not
replace that user state.

## Startup and credentials

The command can create and boot its default configuration without provider API
keys, optional web-search keys, or cloud credentials. Missing credential
placeholders in the generated default config resolve to empty strings and
appear as `env_missing` configuration warnings with the variable and config
path. Those warnings are not themselves among the plugin, mixin, merge, or
variant failures that stop application construction.

This does not make every missing environment placeholder safe. If an empty
resolved value makes a plugin path or another structural setting invalid, the
corresponding validator can still report its own fatal error.

Users do not need to export shell variables before launching the CLI. The
command supplies `.env` values to config resolution in this order:

1. `.env` beside the active config.
2. `./.crystal/.env`.
3. `~/.crystal/.env`.
4. The standard `.env` discovered from the working directory or its parents.

An already exported process value takes precedence over all `.env` files.
Earlier files in the list take precedence over later files. Loading these
files does not mutate the process environment.

API-backed model and tool operations still require the credentials expected by
the selected service. The default config can start and list those agents
before their credentials are configured. Request authentication and direct
environment reads remain owned by the selected provider or tool.

## Distribution smoke scenarios

The original implementation work used numbered levels as shorthand for adding
source installation, archive construction, and public installation
transformations. Maintained commands and documentation use descriptive names.

Run each scenario independently from the repository root:

```bash
npm run test:cli:source-install
npm run test:cli:archive
npm run test:cli:default-install
```

The source-installation smoke creates a fresh venv, installs only editable Core
and application packages without development extras, and boots the generated
source command. The default config's `path:` plugins install into a fresh
config-owned plugin cache. This scenario requires package-index network access
and normally takes several minutes.

The extracted-archive smoke builds or accepts a bundled-Python archive, unpacks
it without installer code, and executes its archive launcher directly. It
checks:

- required archive paths and manifests;
- launcher `--runtime-layout-json` behavior and runtime overrides;
- linked-library portability on macOS;
- credential-free default-config boot and the complete configured agent set;
- use of the preinstalled default-plugin closure;
- dynamic installation of packaged `generic-callback-app`, which must not be
  listed in `preinstalled-plugins.json`.

The default-installer smoke independently serves the checked-in public
installer, `latest.txt`, and archive from a loopback download endpoint. It runs
the normal `curl ... | bash` workflow without path, version, or command-name
overrides, replaces stale installation state, resolves `crystal-lattice` by
name through PATH, and boots it. It independently installs the same
non-preinstalled plugin into a different fresh cache.

Set
`CRYSTAL_LATTICE_PYTHON_RUNTIME_ARCHIVE` to reuse a matching prebuilt archive
for either archive-based scenario.

The archive-based scenarios may share that immutable archive, but they use
different extraction, home, workspace, config, plugin-cache, pip-cache,
installation, and command directories. Neither scenario invokes the other.

All boot probes isolate the workspace, `HOME`, `USERPROFILE`, config files,
plugin cache, and pip cache. Environment names are derived from placeholders in
the exact default-derived config under test; the probes supply no dummy values
and make no model or tool API request.

On POSIX, cleanup owns the command's process group. On Windows, `.cmd`
launchers run in a dedicated process group with a `CTRL_BREAK_EVENT` attempt
and `taskkill /T /F` fallback. Every path verifies that the server port closes.

The release workflow runs both root npm archive-based smokes for Linux AMD64,
macOS AMD64, macOS ARM64, and Windows AMD64 on native runners. Both use the one
archive built by their matrix job while retaining separate mutable state. The
default-installer step is still attempted after an archive-smoke failure when
archive location succeeded.

Existing deeper optimized-bundle tests target the separate PyInstaller layout
and remain manually gated.

## Maintainer entry points

- Runtime package builder:
  `scripts/build_crystal_lattice_python_runtime_package.py`
- Managed runtime/build orchestrator:
  `scripts/build_crystal_lattice_python_runtime_archive.py`
- Runtime archive smoke:
  `scripts/smoke_test_crystal_lattice_python_runtime_archive.py`
- Public default-installer smoke:
  `scripts/smoke_test_crystal_lattice_default_install.py`
- Source-installation smoke:
  `scripts/smoke_test_crystal_lattice_source_install.py`
- Distribution test runner: `scripts/run_cli_distribution_test.py`
- Shared config and boot probe: `scripts/crystal_lattice_cli_boot.py`
- Public installer: `scripts/install.sh`
- Local current-archive installer entry point:
  `scripts/install_current_crystal_lattice_archive.py`
- Isolated optimized-build orchestrator:
  `scripts/build_crystal_lattice_optimized_archive.py`
- Release workflow: `.github/workflows/release-crystal-lattice-cli.yml`
- Focused helper/script tests: `application/python/tests/test_cli_distribution_*.py`
