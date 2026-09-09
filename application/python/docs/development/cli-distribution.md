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

`scripts/install_crystal_lattice_archive.py` extracts an archive into a
temporary staging directory, replaces the versioned target under the install
root, creates a wrapper in the selected bin directory, and verifies
`--runtime-layout-json` and `--help`.

The principal local maintainer entry points are:

```bash
npm run build:bundle
npm run install:prod:local
```

The Nox `build_bundle` and `install_prod_local` sessions back these commands.

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
appear as `env_missing` configuration diagnostics. Those diagnostics are not
themselves among the plugin, mixin, merge, or variant failures that stop
application construction.

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

## Current verification boundaries

The mandatory bundled-Python archive smoke currently checks:

- required archive paths;
- the runtime-package manifest;
- launcher `--runtime-layout-json` behavior and resolved runtime overrides;
- linked-library portability on macOS.

It does not yet start the application or resolve the generated default config.
The release workflow runs this structural smoke for Linux AMD64, macOS AMD64,
macOS ARM64, and Windows AMD64 on native runners.

The local production installer runs that archive smoke before installation.
After installation it verifies only the wrapper's layout output and help.

There is no current clean-venv source boot test, bundled-Python archive boot
test, or installed-wrapper boot test exposed through the planned three-level
root command model. Existing deeper bundle tests target the separate
PyInstaller layout and remain manually gated.

## Maintainer entry points

- Runtime package builder:
  `scripts/build_crystal_lattice_python_runtime_package.py`
- Runtime archive smoke:
  `scripts/smoke_test_crystal_lattice_python_runtime_archive.py`
- Local archive installer:
  `scripts/install_crystal_lattice_archive.py`
- Build/install sessions: `noxfile.py`
- Release workflow: `.github/workflows/release-crystal-lattice-cli.yml`
- Distribution tests: `application/python/tests/test_binary_distribution_*.py`

The archive smoke is the release-workflow extension point. Changing that
script changes the checks applied to every native release archive without
requiring another workflow job.
