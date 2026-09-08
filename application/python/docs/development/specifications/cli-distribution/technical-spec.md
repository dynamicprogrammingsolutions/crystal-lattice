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

Each level is available through one root npm command. Levels 2 and 3 may use a
current-platform archive supplied through
`CRYSTAL_LATTICE_PYTHON_RUNTIME_ARCHIVE`; otherwise their test setup builds
one. This variable is distinct from the existing
`CRYSTAL_LATTICE_BUNDLE_ARCHIVE` input used by optimized PyInstaller tests.

Local archive builds may select a relocatable Python directory through
`CRYSTAL_PYTHON_RUNTIME`. When no directory is supplied, the current local
builder behavior remains available. Portability validation is part of level 2,
so a host-bound Python runtime is a meaningful test failure.

## Common default-config boot contract

Every level starts an explicitly selected command with:

```text
--server --config-local --host 127.0.0.1 --port <reserved-port>
```

The probe:

1. Uses a fresh working directory and home.
2. Removes inherited config, plugin-cache, Python-path, runtime-layout, and
   credential variables that could make the command depend on developer
   state.
3. Waits for `GET /api/hello` to become ready.
4. Reads the generated `.crystal/config.json`.
5. Requires `GET /agents` to equal the complete set of agent identifiers in
   that generated config.
6. Enforces the level-specific plugin-cache expectation.
7. Terminates the process on success or failure and includes the bounded log
   tail in early-exit and timeout errors.

Subprocess output goes to a temporary file rather than an unread pipe because
dynamic plugin installation can produce enough output to block level 1.

The probe makes no provider request and must not contact a model API.

## Credentials and normal startup

Starting the CLI, creating its default config, serving local HTTP endpoints,
and listing configured agents do not require provider API keys, optional
web-search keys, cloud-orchestrator credentials, or exported shell variables.

Missing credential placeholders may produce nonfatal configuration diagnostics
or user-facing warnings. They must not become a fatal startup error and must
not hide agents whose provider will need credentials later.

The boot probe removes at least:

- `OPENROUTER_API_KEY`
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `FIREWORKS_API_KEY`
- `ZAI_API_KEY`
- `GEMINI_API_KEY`
- `TAVILY_API_KEY`
- `CLOUD_ORCHESTRATOR_TOKEN`
- `CHATGPT_CREDENTIALS`

It does not replace them with dummy values.

The CLI loads `.env` values for config resolution in this precedence order:

1. Existing process environment.
2. `.env` beside the active config.
3. `./.crystal/.env`.
4. `~/.crystal/.env`.
5. The standard `.env` discovered from the working directory or its parents.

Earlier `.env` locations win over later locations. Loaded values are
config-resolution inputs and do not need to be exported into the launching
shell or copied into the process environment.

When an invoked provider or tool calls a credentialed API, its corresponding
real credential remains required. The operation reports missing or invalid
credentials at that use boundary. Credential-free startup does not imply
anonymous API access, dummy production credentials, or suppression of
configuration diagnostics.

Default-config tests that do not make provider requests must not inject
unrelated dummy credentials solely to force an empty diagnostics list. A real
provider integration keeps only credentials used by its selected request
path.

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
gates remain separate. Existing optimized-bundle startup-only setup may remove
unnecessary dummy credentials to honor the common credential-free startup
contract, but that does not make an optimized archive an input to these
levels.