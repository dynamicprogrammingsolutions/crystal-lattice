# CLI distribution verification technical specification

## Test-level model

The levels are ordered by the additional transformation they introduce. A
failure at a lower level must be resolved before a higher level is interpreted
as evidence about its own boundary.

| Level | Executed command | Clean boundary | Plugin expectation | Defect class isolated |
|---|---|---|---|---|
| 1. Source and lean Python environment | Console entry point installed from editable Core and application packages | Fresh venv, workspace, home, config directory, and plugin cache | Default `path:` plugins install dynamically into the clean cache | Dependency installation, plugin loading, and source application boot |
| 2. Bundled-Python archive | Launcher extracted from the current-platform shipped archive | Fresh workspace, home, config directory, and user plugin cache | Default plugin closure loads from the archive's preinstalled manifest; user cache remains empty | Runtime staging, bundled Python, launchers, manifests, dependencies, and portability |
| 3. Installed command | Wrapper produced by the local archive installer | Fresh install root, bin directory, workspace, home, config directory, and user plugin cache | Same preinstalled behavior as level 2 | Archive selection, staging replacement, installation, wrapper construction, and relocation |

Each level is available through one root npm command. Levels 2 and 3 consume
an already built current-platform archive. Their pytest process never invokes
the archive build or installs build dependencies.

Root orchestration may accept an archive through
`CRYSTAL_LATTICE_PYTHON_RUNTIME_ARCHIVE`; otherwise it completes an isolated
archive build before starting the consumer test. This variable is distinct
from the existing `CRYSTAL_LATTICE_BUNDLE_ARCHIVE` input used by optimized
PyInstaller tests.

The default build uses a normal isolated Nox environment. Build dependencies
are installed only there, never into the repository environment running the
orchestrator or a test. Unless `CRYSTAL_PYTHON_RUNTIME` supplies an explicit
runtime directory, Nox provisions an `uv`-managed Python 3.11 runtime under its
temporary directory and passes that runtime to the package builder.
Portability validation remains part of level 2; an accidental dependency on
the developer's active Python environment is not acceptable test setup.

## Common default-config boot contract

Every level starts an explicitly selected command with:

```text
--server --config-local --host 127.0.0.1 --port <reserved-port>
```

The probe:

1. Uses a fresh working directory.
2. Sets both `HOME` and `USERPROFILE` to one temporary user directory so
   `Path.home()` resolves away from developer state on POSIX and Windows.
3. Reads the exact default-config template under test, collects every variable
   referenced through `${env:...}`, and removes those names from the child
   process environment.
4. Places a controlled empty `.env` in the working directory so standard
   parent-directory discovery cannot load a developer file.
5. Removes inherited config, plugin-cache, Python-path, and runtime-layout
   variables that could make the command depend on developer state.
6. Waits for `GET /api/hello` to become ready.
7. Reads the generated `.crystal/config.json`.
8. Requires `GET /agents` to equal the complete set of agent identifiers in
   that generated config.
9. Enforces the level-specific plugin-cache expectation.
10. Terminates the process on success or failure and includes the bounded log
   tail in early-exit and timeout errors.

Subprocess output goes to a temporary file rather than an unread pipe because
dynamic plugin installation can produce enough output to block level 1.

The probe makes no provider request and must not contact a model API.

## Process-tree ownership

On POSIX, the probe starts the command in a new session. Cleanup signals the
entire process group with `SIGTERM`, waits for bounded graceful exit, and sends
`SIGKILL` to the group if needed.

On Windows, the probe executes archive and installed `.cmd` wrappers through
`cmd.exe` with `CREATE_NEW_PROCESS_GROUP`. Cleanup sends
`CTRL_BREAK_EVENT`, waits for bounded graceful exit, and then runs:

```text
taskkill /PID <wrapper-pid> /T /F
```

when the tree remains alive. The `/T` descendant cleanup is required because
the wrappers start the packaged Python as a child process.

Every cleanup path waits for the wrapper and confirms that the reserved
loopback port no longer accepts connections. Failure to stop the process tree
fails the smoke with the server log. Windows-specific helper coverage uses a
nested `.cmd` that starts a child Python server before native release smoke is
accepted as evidence.

## Credentials and normal startup

Starting the CLI, creating its default config, serving local HTTP endpoints,
and listing configured agents do not require values for the generated default
config's external environment placeholders or exported shell variables.

When `${env:NAME}` remains unresolved after process and `.env` lookup, the
config loader records an `env_missing` warning containing the variable name
and config path, substitutes the loader's normal empty value, and continues
resolution. The warning itself is nonfatal.

The target warning shape is additive to the existing diagnostic:

```json
{
  "type": "env_missing",
  "severity": "warning",
  "variable": "NAME",
  "path": "providers.example.api_key",
  "detail": "Environment variable 'NAME' is not set"
}
```

The resolved value is still subject to ordinary structural validation. For
example, an empty plugin path may independently produce a fatal `plugin_*`
error. This does not turn the earlier loader warning into a fatal credential or
plugin-authentication check.

The probe derives the environment names to remove from the default config
rather than maintaining a credential denylist. It does not add generic
secret-name filtering or inspect direct environment reads inside plugins.
Those nonstandard reads belong to the owning plugin's contract and are not
exercised because this probe makes no provider/tool request.

The CLI loads `.env` values for config resolution in this precedence order:

1. Existing process environment.
2. `.env` beside the active config.
3. `./.crystal/.env`.
4. `~/.crystal/.env`.
5. The standard `.env` discovered from the working directory or its parents.

Earlier `.env` locations win over later locations. Loaded values are
config-resolution inputs and do not need to be exported into the launching
shell or copied into the process environment.

API-backed functionality still requires credentials according to the selected
provider or tool contract. This specification neither defines a common
request-time credential error nor treats provider authentication as
distribution-test acceptance. Credential-free startup does not imply
anonymous API access or dummy production credentials.

The level probes inject no dummy values. Existing startup-only setup changes
only when it is directly consolidated with the shared probe. A repository-wide
cleanup of provider test environments is not part of this specification.

## Level 1

Level 1 creates a new venv and installs:

```text
pip install -e core/python -e application/python
```

The install omits development extras and repo-root plugin projects. The test
confirms representative development and default-plugin distributions are not
already present before booting the venv's generated `crystal-lattice` entry
point.

A successful boot must leave plugin installation metadata in the initially
empty config-owned plugin cache. This proves that default-config `path:`
projects and their dependencies traversed the supported dynamic installation
path rather than resolving from the parent repository environment.

This level intentionally uses package indexes for plugin dependencies. Network
or dependency-resolution failure is test evidence, not a reason to reuse the
developer environment.

## Level 2

Level 2 retains all existing archive smoke checks:

- required runtime files;
- runtime-package manifest;
- `--runtime-layout-json`;
- resolved built-in-plugin, packaged-Python, and preinstalled-manifest paths;
- macOS linked-library portability.

After structural validation, the smoke runs the common credential-free
default-config boot against the extracted archive launcher. The clean user
plugin cache must remain empty, proving that the default plugin closure came
from `preinstalled-plugins.json`.

The release workflow continues to call the same smoke script for
linux-amd64, darwin-amd64, darwin-arm64, and windows-amd64 on native runners.
No additional workflow, job, or matrix is part of this target.

## Level 3

Level 3 installs a level-2-compatible archive into temporary install and bin
directories. Test setup places stale target and staging content at the
expected paths before installation.

The installer must:

- select or accept the current-platform bundled-Python archive;
- replace stale staging and target directories through its staging swap;
- preserve archive contents in the final install directory;
- create the platform-appropriate wrapper command;
- pass its existing layout and help checks.

The test skips the installer's nested pre-install smoke because level 2 owns
archive validation. It then applies the common credential-free boot contract
to the installed wrapper. Production installation continues to run archive
smoke by default.

## Local commands and suite placement

The root commands are:

```text
npm run test:cli:clean-env
npm run test:cli:bundle
npm run test:cli:install
```

Python commands run through `scripts/repo_run.py`. Distribution tests carry
both `integration` and `slow_integration`; they are selected explicitly by
these commands and remain outside default and ordinary non-slow integration
runs.

## Optimized-bundle separation

Levels 1–3 use only the bundled-Python runtime layout and its
`bin/crystal-lattice` or `Scripts/crystal-lattice.cmd` launcher shape.

PyInstaller build code, archive selection, frozen-runtime policy, and test
gates remain separate. Existing optimized-bundle startup-only setup may lose
dummy values if it is directly consolidated with the common boot probe, but
that does not make an optimized archive an input to these levels or create a
broader provider-test cleanup requirement.
