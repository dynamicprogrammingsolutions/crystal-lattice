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
- application documentation used by local runtime guidance;
- built-in plugin sources;
- runtime and preinstalled-plugin manifests;
- Unix and Windows launchers;
- the inputs needed to produce a later optimized bundle.

With dependency installation enabled, the builder installs Core, the
application, and the default config's local plugin closure into the packaged
Python. `preinstalled-plugins.json` lets runtime plugin resolution import that
closure without copying it into user state.

`application/python/scripts/install.sh` and
`application/python/scripts/install.ps1` are the user-facing installation
authorities. Each downloads or accepts a matching local archive, extracts it
into a temporary staging directory, replaces the versioned target under the
install root, creates the installed command using platform-native PATH
behavior, and verifies `--runtime-layout-json` and `--help`.

The installed command is a small forwarding script that invokes the archive
launcher from its final versioned directory. The Bash installer creates a
POSIX forwarding command and, on Windows, a `.cmd` command. The PowerShell
installer creates a `.cmd` command and manages the fallback per-user PATH
entry without requiring administrator rights or profile edits.

The principal local maintainer entry points are:

```bash
npm run build:cli:archive
npm run install:cli:archive
```

Direct scripts back these npm commands. The bundled-Python build creates a
temporary host build venv and provisions an `uv`-managed Python 3.11 runtime
by default. The optimized PyInstaller build uses its own temporary build venv.
Neither installs or upgrades packages in the repository environment that
launched the command.

The remaining local entry points follow the same scoped naming convention:

```bash
npm run build:cli:optimized
npm run install:cli:dev
```

Set `CRYSTAL_PYTHON_RUNTIME` to build deliberately from another runtime
directory. `CRYSTAL_LATTICE_PYTHON_RUNTIME_ARCHIVE` lets the public installer
or either archive-based smoke use an existing matching archive. The same
archive override makes `npm run install:cli:archive` skip its default build
step and install that archive directly.

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
npm run test:cli:powershell-install
npm run test:cli:agent-access
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

The PowerShell-installer smoke independently serves `install.ps1`,
`latest.txt`, and the Windows archive. It runs the public
`irm .../install.ps1 | iex` shape, verifies command discovery in the installer
PowerShell process and a fresh `cmd.exe`, boots the default configuration, and
installs the designated non-preinstalled plugin into another fresh cache.

Each source/archive/installer smoke also runs a credential-free deterministic
headless probe. It sends one task through the actual `crystal-lattice run`
entry point and another through that runtime's packaged interpreter and
`open_runtime`, then verifies the full compiled access section and isolated
persisted sessions.

`test:cli:agent-access` is the separately gated real-provider scenario. It
runs once per native target against the extracted archive, uses production
shell/write tools to invoke both the CLI and SDK routes, and requires the
corresponding deterministic worker sessions. The OpenRouter key is removed
from the model-controlled process environment before any tool call.

Set
`CRYSTAL_LATTICE_PYTHON_RUNTIME_ARCHIVE` to reuse a matching prebuilt archive
for the direct archive or either installer scenario.

The direct archive, Bash installer, and PowerShell installer scenarios may
share that immutable archive, but they use different extraction, home,
workspace, config, plugin-cache, pip-cache, installation, and command
directories. No scenario invokes another.

All ordinary probes isolate the workspace, `HOME`, `USERPROFILE`, config
files, plugin cache, and pip cache. Environment names are derived from
placeholders in the exact default-derived config under test. They supply no
dummy credentials and contact no external model or tool service.

On POSIX, cleanup owns the command's process group. On Windows, `.cmd`
launchers run in a dedicated process group with a `CTRL_BREAK_EVENT` attempt
and `taskkill /T /F` fallback. Every path verifies that the server port closes.

The release workflow builds Linux AMD64/ARM64, macOS AMD64/ARM64, and Windows
AMD64/ARM64 archives on native runners. Every target runs the direct archive
smoke. macOS and Linux run the Bash installer; Windows AMD64 runs both Bash
and PowerShell; Windows ARM64 runs PowerShell. Applicable installer steps are
still attempted after an archive-smoke failure when archive location
succeeded.

Release tags additionally require the real agent-access scenario on every
target. Workflow dispatch runs it only when `run_agent_access` is selected.
Public pull-request jobs do not receive or run the provider credential.

Existing deeper optimized-bundle tests target the separate PyInstaller layout
and remain manually gated.

## Progress output

Application-owned Python entry points share a small progress helper under
`application/python/scripts/`. Long operations print numbered phases using
the same visible convention as `release:cli`:

```text
[1/4] Creating a clean source-installation environment
[2/4] Installing Core and the CLI from source
      $ python -m pip install ...
```

Human-readable dependency, build, and installation subprocesses inherit the
terminal's output streams, so their logs are visible immediately. Short
machine-readable checks remain captured for parsing.

Boot output continues going to a dedicated server log to avoid blocking on an
unread pipe during dynamic plugin installation. Before waiting, each smoke
prints that log path and periodically reports how long readiness is still
pending. Timeout and early-exit failures include a bounded log tail.

The public `install.sh` and `install.ps1` files are published as standalone
files, so each carries its own small progress helpers instead of importing or
sourcing repository-only code.

## Script ownership

Application-only CLI build/install wrappers, release-version maintenance,
distribution-smoke scenarios, and their focused helpers live under
`application/python/scripts/`. They are maintainer entry points, not importable
application package code, and the bundled-Python package builder excludes this
directory plus generated application `cache/` directories from the staged
application tree.

The root `scripts/` directory retains repository-wide utilities and these
cross-runtime packaging primitives:

- `build_cloud_runtime_plugin_bundle.py`
- `build_crystal_lattice_binary.py`
- `build_crystal_lattice_python_runtime_package.py`
- `build_plugin_packaging_support.py`
- `prepare_cloud_runtime_build_context.py`

Cloud-orchestrator source bundles consume this group, and the runtime package
explicitly copies the subset it needs into its own root `scripts/` directory.
That shipped internal layout remains separate from package maintainer script
placement.

## Maintainer entry points

- Runtime package builder:
  `scripts/build_crystal_lattice_python_runtime_package.py`
- Managed runtime/build orchestrator:
  `application/python/scripts/build_runtime_archive.py`
- Runtime archive smoke:
  `application/python/scripts/smoke_runtime_archive.py`
- Public default-installer smoke:
  `application/python/scripts/smoke_default_install.py`
- Public PowerShell-installer smoke:
  `application/python/scripts/smoke_powershell_install.py`
- Source-installation smoke:
  `application/python/scripts/smoke_source_install.py`
- Deterministic CLI/SDK helper:
  `application/python/scripts/headless_access_smoke.py`
- Real model-mediated CLI/SDK smoke:
  `application/python/scripts/smoke_agent_access.py`
- Distribution smoke runner:
  `application/python/scripts/run_distribution_smoke.py`
- Shared config and boot probe:
  `application/python/scripts/boot_smoke.py`
- Shared progress helper: `application/python/scripts/progress.py`
- Public Bash installer: `application/python/scripts/install.sh`
- Public PowerShell installer: `application/python/scripts/install.ps1`
- Local current-archive installer entry point:
  `application/python/scripts/install_current_archive.py`
- Local editable-development installer:
  `application/python/scripts/install_dev.py`
- Isolated optimized-build orchestrator:
  `application/python/scripts/build_optimized_archive.py`
- Release workflow: `.github/workflows/release-crystal-lattice-cli.yml`
- Focused helper/script tests: `application/python/tests/test_cli_distribution_*.py`
