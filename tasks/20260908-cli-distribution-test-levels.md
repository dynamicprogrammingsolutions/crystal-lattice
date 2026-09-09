# CLI Distribution User-Workflow Verification

Make source installation, direct archive use, and default installation of the
shipped CLI independently testable through the same root npm commands used by
native release CI, with realistic plugin installation and terminal command
discovery.

The original task used levels 1–3 as ordering shorthand. The maintained names
are source-installation smoke, extracted-archive smoke, and default-installer
smoke:

1. **Source-installation smoke** — no bundling; provisions a fresh
   environment and boots from source files. Catches plugin install errors
   and app-boot issues in a clean environment earliest (the original
   release-blocker error class).
2. **Extracted-archive smoke** — unpacks the shipped bundled-Python runtime
   archive and executes its launcher directly.
3. **Default-installer smoke** — runs the public default installer and then
   executes `crystal-lattice` by name from a supported terminal.

## Requirements checklist

- [x] Level 1 — a test provisions a clean Python environment (fresh venv
  containing only the core and application packages, lean install without
  dev extras) and clean runtime files (fresh workspace, `HOME`,
  `CONFIG_DIR`, plugin cache), boots the CLI with the default config, and
  asserts the server becomes ready and exposes the default-config agents.
  The default-config `path:` plugins must install dynamically into the
  clean plugin cache during the boot.
- [x] Level 1 — runnable locally via a root npm script.
- [x] Level 2 — the shipped bundled-Python runtime archive's launcher boots
  with the default config and exposes the default-config agents, verified
  locally via a root npm script.
- [x] Level 3 — the install script installs a built archive into temporary
  install/bin directories and the installed wrapper command boots with the
  default config and exposes the default-config agents, runnable locally
  via a root npm script.
- [x] Credential-free first start — the generated default config boots and
  exposes its agents when values for its external `${env:...}` placeholders
  are absent from both the process environment and discovered `.env` files.
  The config loader reports unresolved environment placeholders as nonfatal
  `env_missing` warnings; a separately invalid resolved structure may still
  produce its own fatal validation error. Levels 1–3 must not inject dummy
  values merely to bypass configuration resolution.
- [x] Normal CLI use does not require users to export shell environment
  variables. The CLI loads API credentials from the documented `.env`
  locations associated with the active config, project, or user. API-backed
  functionality still requires the real credentials defined by its owning
  provider or tool contract, but provider/tool authentication behavior is not
  part of the distribution test-level contract.
- [x] The release-workflow smoke test boots the archive with the default
  config (in addition to the current structural checks); no other CI
  changes.
- [x] The two bundle strategies stay separated: levels 1–3 target the
  bundled-Python runtime archive (the shipped artifact); the PyInstaller
  optimized-bundle tier and its tests remain a separate suite — not
  conflated, not removed, and not behaviorally changed. Startup-only test
  setup in that suite may be changed solely to remove unnecessary dummy
  credentials required by the credential-free first-start requirement.
- [x] Proper specification and documentation for the distribution/test-level
  model are created (deliberately unplanned — see Execution plan).

### Approved post-completion requirements

- [x] The extracted-archive smoke follows the direct user workflow: it
  independently unpacks the shipped archive, executes the archive launcher
  directly, and does not call or depend on installer scenario code.
- [x] The default-installer smoke follows the direct user workflow: it runs
  the public download installer with default install root, command name, and
  automatic command-directory selection, then resolves and executes
  `crystal-lattice` by name rather than by a known absolute install path.
- [x] The extracted-archive and default-installer smokes each begin with
  separate fresh home, workspace, config, plugin-cache, pip-cache, install,
  and command-directory state. Sharing the immutable built archive is allowed;
  neither smoke may reuse mutable state or installation results from the
  other.
- [x] Both archive-based smokes use a config derived from the packaged default
  to load a real packaged Python plugin that is absent from
  `preinstalled-plugins.json`. Each smoke independently triggers installation
  through packaged Python and asserts plugin-specific metadata in its own
  previously empty cache.
- [x] Each scenario remains independently interpretable. Archive validation,
  direct archive boot, public installation, installed-command boot, and plugin
  installation are not collapsed in a way that permits one scenario or shared
  mutable state to hide a defect in another.
- [x] Root npm commands invoke the direct source-installation,
  extracted-archive, and default-installer acceptance implementations. Native
  release jobs invoke the archive and installer npm commands directly against
  the archive built by that job.
- [ ] Native release CI runs both archive-based smokes on every release target.
  Runtime may increase; optimization is acceptable only when it preserves both
  direct workflows, separate mutable state, and failure evidence without
  disproportionate orchestration.
- [x] Without `BIN_DIR`, the public installer selects an existing suitable
  writable directory already on PATH and installs the default
  `crystal-lattice` command there, making it immediately resolvable by name in
  the supported terminal environment. An explicit `BIN_DIR` remains
  available.
- [x] If no suitable PATH directory exists, the default installer fails before
  replacing installation state with an actionable message instead of
  completing an installation whose command is not discoverable.
- [x] Build, install, and smoke orchestration has one clear implementation
  owner per behavior. Local npm and CI use the same acceptance entry points;
  scenario code may share lower-level helpers but may not invoke another
  scenario as a substitute.
- [x] Specifications, current documentation, commands, tests, and diagnostics
  use descriptive names for scenarios and components. Historical level
  terminology appears only where its meaning is explicitly introduced.

## Constraints and decisions

- **CI stays unchanged** (user decision): CI rightly covers 3 OSes via the
  release matrix (linux-amd64, darwin-amd64, darwin-arm64, windows-amd64,
  each built and smoked on its native runner). The only CI-facing change is
  the content of the existing smoke script, which the release workflow
  already runs per target.
- **Two bundle strategies are separated** (user-confirmed): the
  bundled-Python runtime archive is the shipped artifact with dynamic plugin
  installation allowed; the PyInstaller optimized bundle is the
  config-specific hermetic tier (frozen runtimes reject dynamic installs).
  The level tests must reference only the python-runtime archive layout. The
  credential cleanup may remove startup-only dummy values from an existing
  PyInstaller test, but must not adapt that test into the three-level suite or
  change its bundle behavior.
- **Specification and documentation are deliberately unplanned**: the
  completion agent decides the specification scope, placement, audience, and
  required file set, and discovers the details during execution. It must
  follow the repository documentation standards (read the documentation and
  standards indexes before creating or moving anything; specifications
  describe intended targets; requirements track live implementation,
  verification, documentation, and evidence). The absence of a plan here is
  not permission to skip the requirement.
- **Credentials are request-time capabilities, not startup prerequisites**
  (user decision): default-config startup must not require credentials for
  providers or optional tools that have not been invoked. Distribution probes
  make no provider/tool API requests and run without dummy credentials.
  Provider-specific direct environment reads and request authentication remain
  owned by those plugins.
- **No shell export is required for normal use** (user decision): users may
  configure API keys in `.env` files discovered by the CLI. Process
  environment values remain supported and take precedence, but setup
  instructions and first-start behavior must not require users to export
  variables before launching the command. APIs that require credentials still
  require their corresponding configured keys when invoked.
- **npm script naming** (proposal, implementation may adjust consistently):
  `test:cli:clean-env` (level 1), `test:cli:bundle` (level 2),
  `test:cli:install` (level 3).

## Supporting facts

The original inventory below was verified against the tree on 2026-09-08 at
HEAD `9c502711`. The plan was reassessed later that day at HEAD `584f54a4`;
current-tree corrections and additional findings appear after the inventory.

### Current coverage inventory

- **Level 1: nothing anywhere.** No test provisions a clean environment and
  boots the CLI from source files with the default config.
- **Level 2: structural only.** The release workflow
  (`release-crystal-lattice-cli.yml`, tag-triggered) builds each archive on
  its native runner and runs
  `scripts/smoke_test_crystal_lattice_python_runtime_archive.py`, which
  checks required paths, runs the launcher's `--runtime-layout-json` and
  validates layout/env overrides, and checks macOS `otool -L` portability.
  No app boot, no config, no plugin loading. `install_prod_local` (nox)
  runs the same smoke before installing.
- **Level 3: structural only.**
  `scripts/install_crystal_lattice_archive.py` (behind `install_prod_local`)
  runs the structural smoke, installs via a staging swap into the install
  root, writes a bin wrapper, and `verify_installed_command` runs only
  `--runtime-layout-json` + `--help`. The post-publish
  `deploy/aws-cli-downloads/smoke.sh` downloads `install.sh` from the public
  endpoint, installs into a test root, and also stops at `--help` + layout.
  No test covers the installer logic (staging swap, wrapper creation,
  platform archive selection) and nothing boots an installed command.
- **public-ci.yml (PRs):** unit tests only — no distribution coverage.
- **The only existing default-config boot assertion** is
  `_assert_default_config_starts` in
  `application/python/tests/test_binary_distribution_bundle_e2e_ollama.py`
  (lines 149-189): boots `--config-local`, polls `GET /api/hello`, asserts
  `GET /agents` contains `ollama` and `cloud-script-author`. It is
  quadruple-gated (`RUN_CRYSTAL_BUNDLE_OLLAMA_E2E=1` +
  `CRYSTAL_LATTICE_BUNDLE_ARCHIVE` + platform match + live Ollama, whose
  model pull runs before the boot), marked integration+ollama, in no
  workflow, and expects the **PyInstaller** layout (`crystal-lattice` at the
  extracted root) — it does not cover the shipped archive layout
  (`bin/crystal-lattice`).
- **PyInstaller tier (separate, keep separate):**
  `test_binary_distribution_docker.py` (clean `ubuntu:22.04`, `--help` +
  layout only, manual), the Ollama E2E above,
  `test_binary_distribution_optional_plugin_install.py` (frozen runtime
  rejects dynamic installs),
  `test_cloud_validation_installed_bundle.py`,
  `test_cloud_script_author_installed_bundle_real_api.py` — all PyInstaller
  layout, all manual/gated, none in CI.

### Level 1 mechanics

- `application/python` exposes the console command
  (`[project.scripts] crystal-lattice = "agent_terminal_app.__main__:main"`),
  so `pip install -e core/python -e application/python` into a fresh venv
  provides the real `crystal-lattice` command.
- Editable install is required, not incidental:
  `_default_builtin_plugins_dir()`
  (`core/python/agent_app/config.py:32-40`) resolves `<repo>/plugins` from
  the source layout — the same plugin set the bundle ships. A non-editable
  install would resolve the plugins dir wrongly.
- The default config
  (`application/python/agent_terminal_app/default_config/config.json`) loads
  ~28 plugins, nearly all `path:${env:BUILTIN_PLUGINS}/<name>`;
  `plugin_cache_dir` resolves to `${env:CONFIG_DIR}/.plugin_cache/plugins`.
- Dynamic install policy: `install_deps` defaults to true (resolved Q4 in
  `tasks/20260908-isolated-env-followup-fixes.md` — keep). A clean source
  environment is not frozen, so the default-config plugins install
  dynamically with live PyPI at plugin-install time. This is exactly the
  error class that blocked the v0.1.2 release (plugin cache anyio 4.15.1 vs
  environment typing_extensions 4.14.1) and what level 1 must catch early.
- The existing Ollama E2E boot helper sets dummy values for
  `OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`,
  `TAVILY_API_KEY`, `FIREWORKS_API_KEY`, and `ZAI_API_KEY`. Those values
  mask credential-free startup and are not needed by its default-config boot
  assertion; real model-request portions of provider tests still need their
  actual selected-provider credentials.
- Readiness/agent assertions: poll `GET /api/hello`; assert `GET /agents`.
- The test itself runs under the repo venv's pytest, but the boot subprocess
  uses the fresh venv's `crystal-lattice` — the repo venv's installed plugin
  packages cannot mask clean-env failures.
- Fresh-venv scratch pattern is established (used for the plugin-suite
  extras verification recorded in
  `tasks/20260908-isolated-env-followup-fixes.md`).

### Level 2 mechanics

- The shipped artifact is built by
  `scripts/build_crystal_lattice_python_runtime_package.py`. With
  dependency installation enabled (the release path), it preinstalls the
  **default config's** plugins into the packaged Python
  (`install_preinstalled_default_plugins`, lines 427-471) and writes
  `preinstalled-plugins.json`. A default-config boot of the archive is
  therefore the hermetic preinstalled path; plugins outside the default
  config would dynamically install (the archive is not frozen;
  `CRYSTAL_PLUGIN_PYTHON` points at the packaged Python).
- Archive layout: `bin/crystal-lattice` launcher (`Scripts/crystal-lattice.cmd`
  on Windows), packaged `python/`, `plugins/`, `preinstalled-plugins.json`,
  `runtime-package.json`.
- Each release matrix target builds and smokes on its **native runner**
  (`runs-on: ${{ matrix.runner }}`), and the current smoke already executes
  the launcher (`--runtime-layout-json`) — so a default-config boot in the
  smoke runs natively on every target; no cross-platform execution problem.
- `nox -s build_bundle` already builds the current-platform python-runtime
  archive (`noxfile.py:23-26`); `build:optimized` remains the separate
  PyInstaller tier.
- Extending the smoke script automatically upgrades both the release
  workflow (all targets) and the `install_prod_local` pre-install smoke —
  no workflow edits.

### Level 3 mechanics

- `scripts/install_crystal_lattice_archive.py` supports `--install-root`,
  `--bin-dir`, `--command-name`, and `--skip-smoke-test` — enough to
  install into temp directories from a test. `current_platform_archive()`
  reads the version from `application/python/pyproject.toml` and picks the
  archive from `dist/crystal-lattice-python-runtime`.
- The bin wrapper is a `sh exec` script on Unix and a `@cmd` shim on
  Windows (`install_command`).
- Archive-based test gating precedent: `CRYSTAL_LATTICE_BUNDLE_ARCHIVE`
  env var + platform-match skip (used by the PyInstaller tests) — the level
  2/3 tests can mirror this with a prebuilt-archive override.

### npm-script wiring conventions

- All Python-invoking root npm scripts run through `scripts/repo_run.py`
  (commit `bcab1836`).
  `application/python/tests/test_repo_run_script.py` asserts the exact
  wrapped set (`using_repo_run == WRAPPED_SCRIPTS`, currently 50 scripts) —
  every newly wrapped script must be added to that set in lockstep, plus an
  exact-value assertion.
- Marker conventions: `integration` for multi-layer/network tests; the
  application default run excludes `integration` and `docker`. The level
  tests are opt-in via their npm scripts.

### Reassessment findings at HEAD `584f54a4`

- The package that owns this behavior is `application/python`: it owns the
  command, runtime archive builder, installer, release smoke, and current
  distribution documentation. Root npm scripts are contributor entry points,
  not a reason to place the specification at repository scope.
- No application-owned specification directory or focused distribution
  development page currently exists. Distribution, release, Nox, and
  PyInstaller details are concentrated in the large package README.
- The current default config declares 20 agents and includes a direct
  Anthropic provider. A reliable probe should compare `GET /agents` with all
  keys in the copied default config rather than checking only `ollama` and
  `cloud-script-author`.
- Missing `${env:...}` values currently resolve to empty strings and produce
  `env_missing` configuration diagnostics. `AgentApplication` treats
  plugin/mixin/merge/variant errors as startup-fatal but does not treat
  `env_missing` as fatal.
- The CLI currently reads `.env` values, without installing them into the
  process environment, in this order: beside the active config, local
  `./.crystal/.env`, user `~/.crystal/.env`, then the standard `.env` found
  from the working directory. Already exported process values take precedence.
- A temporary bundled-Python archive boot with `OPENROUTER_API_KEY`,
  `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `FIREWORKS_API_KEY`, `ZAI_API_KEY`,
  `GEMINI_API_KEY`, and `TAVILY_API_KEY` explicitly absent succeeded and
  exposed all 20 agents. Credential-free startup is therefore current behavior
  that needs an explicit contract and regression coverage, not dummy test
  configuration.
- A temporary boot of the existing current-platform bundled-Python archive
  created the local default config, exposed all 20 agents, and left the clean
  user plugin cache empty. This confirms the intended preinstalled-plugin
  invariant for levels 2 and 3.
- That existing archive fails the current macOS portability smoke because it
  was built from a pyenv/Homebrew Python with absolute library references.
  Release CI avoids this by passing an `uv`-managed relocatable runtime to the
  builder. Local tests should preserve the portability failure as valid
  evidence, allow an explicit relocatable runtime, and allow reuse of an
  already built current-platform archive.
- Server output must go to a temporary log file rather than an unread pipe.
  Dynamic plugin installation can emit enough output to fill a pipe and block
  level 1 before readiness.
- The level tests are broad, network-dependent, and potentially several
  minutes long. They should carry both `integration` and `slow_integration`
  and remain outside default and ordinary non-slow integration runs.

## Execution plan

Status: Approved

Implement this in three ordered passes. First establish the target
specification and an honest current-state implementation page. Then implement
the shared probe and all three test levels. Finally update current
documentation and requirement evidence to describe only the behavior that was
actually delivered.

#### Pass 1 — specification and initial current-state documentation

Create an application-owned specification at
`application/python/docs/development/specifications/cli-distribution/`.
This is the narrowest authoritative scope because the application package owns
the CLI command, both bundle strategies, runtime archive, installer, and
release smoke. No existing specification covers their verification model.

Use a proportional three-file set:

- `index.md` — scope, ownership, goals/non-goals, the distinction between the
  shipped bundled-Python archive and optimized PyInstaller output, and links;
- `technical-spec.md` — the three ordered failure-isolation levels, clean-state
  contract, credential-free default-config boot/readiness contract,
  config-loader warning behavior, `.env` credential-loading boundary,
  provider/tool ownership boundary, plugin-install expectations, archive
  selection/override behavior, native release smoke, local command contract,
  and failure diagnostics;
- `requirements.md` — stable `CLIDIST-*` requirements with separate
  implementation, verification, documentation, and evidence state.

A separate product specification or decision record would add little value:
this is a maintainer verification contract, and the user-confirmed strategy
and CI decisions fit clearly in the index and technical specification.

Create
`application/python/docs/development/cli-distribution.md` as the initial
current implementation map and link both it and the specification from
`application/python/docs/development/index.md`. Before behavior changes, that
page will document only current facts: the two distribution strategies,
shipped archive ownership, build/install/smoke entry points, user-state
boundaries, credential-free startup, `.env` credential loading, preinstalled
versus dynamic plugin behavior, and the then-current structural verification
gap. It will explicitly map implementation to the specification without
redefining the target.

#### Pass 2 — shared boot contract and three test levels

Add one standard-library helper under `scripts/` for all default-config boot
probes. It will:

- start an explicitly supplied command with `--server --config-local` on a
  reserved loopback port in a fresh workspace;
- point both `HOME` and `USERPROFILE` at one temporary user directory so
  `Path.home()` and the CLI's user-level `.env` lookup cannot reach developer
  state on POSIX or Windows;
- remove inherited Python, Crystal runtime-layout, config, and plugin-cache
  variables that could mask isolation defects;
- read the exact default-config template under test, collect every
  `${env:...}` variable name from it, remove those names from the child
  environment, and inject no dummy replacements;
- place a controlled empty `.env` in the temporary workspace so standard
  parent-directory discovery cannot load a developer file;
- write subprocess output to a temporary log, poll `GET /api/hello`, report
  early exit or timeout with the log tail, and always terminate/kill the
  process;
- parse the newly copied `.crystal/config.json` and require `GET /agents` to
  equal its complete `agents` key set;
- support an expected populated plugin cache for level 1 and an expected empty
  plugin cache for levels 2 and 3.

The probe owns the launched process tree. On POSIX it starts a new session and
sends `SIGTERM`, then `SIGKILL` if needed, to the process group. On Windows it
launches the `.cmd` command through `cmd.exe` with
`CREATE_NEW_PROCESS_GROUP`, attempts `CTRL_BREAK_EVENT`, and falls back to
`taskkill /PID <wrapper-pid> /T /F`. Cleanup waits for the wrapper and verifies
that the loopback port no longer accepts connections. A Windows-only helper
test uses a nested `.cmd` and child Python server to verify descendant cleanup.

Do not add generic secret-name patterns, a growing credential denylist, or
special handling for plugins that read process environment variables directly.
The distribution contract ends at config loading. Remove dummy values from the
new level probes and from an existing startup-only helper only when that helper
is directly consolidated with the shared probe. A broader test cleanup does
not block levels 1–3.

Add focused config-loader coverage:

- an unresolved `${env:NAME}` produces a nonfatal `env_missing` warning with
  its variable and config path, while a later structural validator remains
  free to report an independent fatal error caused by the resolved value;
- with `NAME` absent from the process, a config-adjacent `.env` value resolves
  the placeholder without requiring a shell export or mutating `os.environ`.

Provider-request tests remain responsible for their own authentication
contracts. The distribution boot probes make no external provider requests
and do not inventory provider/tool credential behavior.

Use one slow integration test module in `application/python/tests` for the
three levels. Archive-consuming tests receive an already built
current-platform archive and must never invoke Nox or install build
dependencies from inside a running pytest process.

A standard-library root runner orchestrates each npm command. For levels 2 and
3 it accepts `CRYSTAL_LATTICE_PYTHON_RUNTIME_ARCHIVE` as an already built
input or invokes the isolated Nox `build_bundle` session and waits for it to
finish before starting pytest. The distinct archive-variable name avoids
conflating these tests with the existing
`CRYSTAL_LATTICE_BUNDLE_ARCHIVE` PyInstaller suite.

Convert `build_bundle` from `python=False` to a normal isolated Nox session.
Install Core, application binary extras, and `uv` only inside that Nox
environment. Unless `CRYSTAL_PYTHON_RUNTIME` explicitly supplies a runtime,
the session provisions an `uv`-managed Python 3.11 under its temporary
directory and passes it to the existing builder's `--python-runtime` option.
The repository venv is orchestration-only and is never a pip-install target.

Level 1 will:

1. Create a fresh venv under pytest's temporary directory.
2. Install only editable `core/python` and `application/python`, without dev
   extras or repo-root plugin projects.
3. Assert selected dev/plugin distributions are absent so the parent repo
   venv cannot silently satisfy the boot.
4. Boot the fresh venv's actual `crystal-lattice` entry point through the
   shared probe with clean runtime files and no credentials.
5. Require a populated plugin cache containing installation metadata, proving
   that default-config `path:` plugins and dependencies were installed
   dynamically.

Level 2 will extend
`scripts/smoke_test_crystal_lattice_python_runtime_archive.py` so its public
archive-validation path performs the shared default-config boot after all
existing structural/layout/portability checks. It will require the clean user
plugin cache to remain empty while values for default-config external
placeholders are absent, proving both config-loader-safe startup and that the
default plugin closure came from the archive's preinstalled manifest. The
release workflow already calls this script with each native archive, so no
workflow file changes are needed.

Level 3 will:

1. Prepare stale target/staging sentinels under temporary install directories
   to exercise replacement through the staging swap.
2. Run `scripts/install_crystal_lattice_archive.py` with the selected archive,
   temporary `--install-root`/`--bin-dir`, and a unique command name.
   Use `--skip-smoke-test` here so level 3 isolates installer/wrapper behavior
   instead of rerunning level 2 inside the installer.
3. Assert the stale paths were replaced and the platform-appropriate wrapper
   was created.
4. Boot that installed wrapper through the shared probe without credentials
   and require the clean user plugin cache to remain empty.
5. Add focused unit coverage for current-platform archive selection so the
   explicit prebuilt-archive path does not leave that installer branch
   unverified.

Add the three agreed root scripts:

- `test:cli:clean-env`
- `test:cli:bundle`
- `test:cli:install`

Each will invoke its exact slow-integration test through
`scripts/repo_run.py`. Add all three to `WRAPPED_SCRIPTS` and add exact command
assertions in `test_repo_run_script.py`.

#### Pass 3 — current documentation and evidence

After each behavior is verified, update the focused distribution development
page with the three root commands, prerequisites, expected failure boundary,
network/runtime costs, optional archive/runtime environment variables, release
smoke behavior, credential-free first-start contract, provider/tool ownership
boundary, `.env` setup path, and the explicit PyInstaller-suite separation.
Add a concise pointer and command summary to the package README's
testing/distribution guidance rather than duplicating the full maintainer
contract there. Update the configuration and placeholder guides so user-facing
instructions do not imply that shell exports are required.

Update `requirements.md` only with evidence actually obtained. New current
claims and completed requirement states ship with their implementation.
Prepare and build the documentation site from authored sources; do not edit
`docs_site/prepared/` or `docs_site/dist/`.

### Implementation decisions and open questions

- **Decision — specification owner and size:** use the application package
  and the three-file `cli-distribution` specification described above. It is
  substantial enough to preserve the cross-script/native-platform contract
  but does not need a separate product or decisions page.
- **Decision — one boot probe:** share one standard-library implementation
  between release smoke and integration tests. The acceptance behavior and
  diagnostics must not drift by level.
- **Decision — full default-agent contract:** compare `/agents` with every
  agent declared by the freshly copied default config. Do not preserve the
  older two-agent sentinel assertion.
- **Decision — loader-derived environment isolation:** derive names to remove
  from the exact default config's `${env:...}` placeholders. Use a fresh
  workspace plus temporary `HOME` and `USERPROFILE`, and block parent `.env`
  discovery with a controlled workspace file. Do not maintain a credential
  list or inspect plugin-specific direct environment reads.
- **Decision — loader warning boundary:** unresolved environment placeholders
  are config-loader `env_missing` warnings, not plugin warnings. Record the
  variable and config path and continue resolution; downstream structural
  validation remains independently fatal when appropriate.
- **Decision — `.env` is the normal credential setup path:** document and
  verify config-adjacent/project/user `.env` loading without requiring shell
  exports. Preserve explicit process-environment support and precedence for
  automation and advanced use.
- **Decision — provider/tool ownership:** current user docs state that
  API-backed functionality still needs credentials, but this specification
  does not define or verify every plugin's environment reads, authentication,
  or missing-credential request errors.
- **Decision — narrow dummy cleanup:** the three level probes inject no dummy
  values. Existing startup-only setup changes only when directly replaced by
  the shared helper; repository-wide test cleanup is not a completion
  dependency.
- **Decision — cache evidence:** level 1 requires real plugin installation
  metadata; levels 2 and 3 require no user plugin installation. This
  distinguishes the dynamic source path from the preinstalled archive path.
- **Decision — archive override naming:** reserve
  `CRYSTAL_LATTICE_PYTHON_RUNTIME_ARCHIVE` for these tests and leave the
  existing PyInstaller `CRYSTAL_LATTICE_BUNDLE_ARCHIVE` contract untouched.
- **Decision — archive consumers do not build:** pytest receives an already
  built archive. Nox/build dependency installation must finish in an isolated
  environment before the archive-consuming test process starts.
- **Decision — installer isolation:** skip its nested pre-install smoke in
  level 3 because level 2 owns archive validation. The production installer
  continues to run the smoke by default.
- **Decision — CI boundary:** modify only the smoke script already invoked by
  release CI. Do not edit workflow files or add these tests to public CI.
- **Decision — optimized bundles:** do not modify PyInstaller build code,
  gates, archive variables, or behavior. Its existing default-config startup
  preflight may lose dummy values only if directly consolidated with the
  shared boot helper; otherwise its tests remain separate.
- **Decision — isolated archive construction (user-approved):** the root
  runner completes a normal isolated Nox `build_bundle` session before
  starting archive-consuming pytest. No build-time pip command targets the
  repository environment.
- **Decision — deterministic local runtime (user-approved):** the isolated Nox
  session automatically provisions an `uv`-managed Python 3.11 runtime,
  matching release CI's runtime family. `CRYSTAL_PYTHON_RUNTIME` and
  `CRYSTAL_LATTICE_PYTHON_RUNTIME_ARCHIVE` remain optional overrides.
- **Decision — Windows process-tree cleanup (user-approved):** launch `.cmd`
  wrappers through `cmd.exe` in a new process group, try
  `CTRL_BREAK_EVENT`, fall back to `taskkill /T /F`, wait for exit, and verify
  the server port closes. POSIX uses `SIGTERM`/`SIGKILL` against a new process
  group.
- **Open questions:** none blocking implementation. A platform-specific
  deviation discovered by native execution returns the plan to Draft if it
  changes shipped behavior or weakens process-tree ownership.

### Documentation

- Specification sources:
  `application/python/docs/development/specifications/cli-distribution/`
  (`index.md`, `technical-spec.md`, `requirements.md`).
- Current maintainer implementation page:
  `application/python/docs/development/cli-distribution.md`.
- Discoverability:
  `application/python/docs/development/index.md`.
- Concise current user/contributor entry-point updates:
  `application/python/README.md`, including the credential-free startup and
  provider/tool authentication ownership boundary.
- Current configuration guidance:
  `application/python/docs/configuration.md` and
  `application/python/docs/configuration-placeholders.md`, including `.env`
  discovery and the distinction between configuring a key and exporting it.
- Validation: run documentation preparation and MkDocs build from authored
  sources after the final current-behavior update.

### Task checklist

- [x] Create and index the application-owned CLI distribution specification
  and initial requirements state.
- [x] Create and index the honest current-state distribution implementation
  page before changing test behavior.
- [x] Resolve and approve isolated archive construction, Windows process-tree
  cleanup, and deterministic local runtime provisioning.
- [x] Add the shared isolated default-config boot probe and focused helper
  coverage.
- [x] Derive environment removals from default-config placeholders, isolate
  `HOME`/`USERPROFILE` and `.env` lookup, and inject no dummy values.
- [x] Cover config-loader `env_missing` warnings without weakening detection of
  independent fatal structural errors.
- [x] Cover `.env` credential loading with no corresponding exported process
  variables or process-environment mutation.
- [x] Level 1: add the lean fresh-venv/dynamic-plugin-install boot test.
- [x] Level 1: add the root npm script and `WRAPPED_SCRIPTS` assertions.
- [x] Level 2: extend archive smoke with preinstalled default-config boot.
- [x] Level 2: add archive setup/override support and the root npm script.
- [x] Level 3: add staging/install/wrapper/default-config boot coverage and
  focused platform-selection coverage.
- [x] Level 3: add the root npm script and `WRAPPED_SCRIPTS` assertions.
- [x] Update current README/development documentation for delivered behavior.
- [x] Update `CLIDIST-*` live state and evidence.
- [x] Run acceptance, regression, formatting, and documentation verification.

### Requirement verification

- Level 1: `npm run test:cli:clean-env` provisions a fresh lean venv, proves
  ambient plugin/dev packages are absent, boots from source with clean files
  while default-config external placeholder values are absent, matches the
  complete default agent set, and leaves plugin installation metadata in the
  previously empty cache.
- Level 2: `npm run test:cli:bundle` builds or accepts a current-platform
  bundled-Python archive, passes structural/portability checks, boots its
  launcher with clean files and no external placeholder values, matches the
  complete default agent set, and leaves the user plugin cache empty.
- Level 3: `npm run test:cli:install` builds or accepts the same archive,
  replaces stale staging/target state in temporary directories, creates the
  platform wrapper, boots that wrapper without external placeholder values,
  matches the complete default agent set, and leaves the user plugin cache
  empty.
- Credential-free startup: all three probes explicitly show the recognized
  default-config placeholder names were removed from the child environment,
  isolated config/user `.env` locations contain no inherited values, startup
  and `/agents` succeed, and loader `env_missing` warnings remain nonfatal.
- Normal use without shell exports: focused CLI/config coverage starts with
  a referenced variable absent from the process, loads a sentinel value from
  an active-config `.env`, and verifies config resolution receives it without
  shell setup or `os.environ` mutation. Current user docs identify `.env` as
  the normal key setup path and state that API-backed functionality still
  requires credentials defined by its provider or tool.
- CI smoke: the extended smoke script boots a built archive locally; the
  unchanged release workflow invokes it for all four native matrix targets.
- Separation: diff inspection and test/archive-variable names show that no
  PyInstaller build path was modified or used by levels 1–3; any PyInstaller
  test edit is limited to deleting unnecessary startup-only dummy credentials.
- Specification and documentation: the application development index reaches
  the specification and current implementation page; requirement rows contain
  concrete implementation/test/doc evidence; README claims match passing
  commands; documentation preparation and build succeed.

### Additional implementation verification

- Run the focused unit tests for archive smoke, installer archive selection,
  boot-probe helpers, and exact root-script wiring.
- Run focused config-loader and CLI `.env` tests; do not make the distribution
  suite depend on real-provider credential tests.
- Run the application fast suite with its normal non-integration filter.
- Run all three root npm commands explicitly; a skipped test is not a pass.
- Run Ruff and Black check mode on modified Python files.
- Run `python docs_site/scripts/prepare_mkdocs_site.py` and the MkDocs build.
- Inspect the final diff to confirm no release workflow, generated docs tree,
  or PyInstaller-tier file changed.

Primary risks are live-PyPI drift and latency in level 1, archive-build latency
in levels 2/3, host-bound local Python runtimes on macOS, loopback-port races,
and Windows `.cmd` process cleanup. The clean environment and cache assertions
are intentional even when they make dependency regressions visible; the
shared probe's bounded polling, log-tail diagnostics, and terminate/kill
fallback limit operational ambiguity.

## Implementation Notes

- 2026-09-08: The user approved documentation-first execution, added
  credential-free startup and no-shell-export requirements, and directed that
  the specification and initial current documentation be created in a separate
  worktree before test implementation.
- 2026-09-08: Inspection confirmed that missing credential placeholders are
  currently nonfatal and that the packaged CLI boots with all provider keys
  absent. The first implementation pass preserves that behavior as an explicit
  contract and removes test-only credential masking.
- 2026-09-08: Created the application-owned `cli-distribution` specification
  (`index.md`, `technical-spec.md`, and `requirements.md`), the current
  distribution implementation map, and current README/configuration guidance
  for credential-free startup and `.env` key loading. Linked the new pages
  from the application development index before changing test behavior.
- 2026-09-08: Initial documentation verification passed: focused `.env` and
  config-resolution tests passed (3 tests), documentation-site preparation
  completed, and MkDocs built successfully with only pre-existing navigation,
  link, and generated-reference warnings. A temporary packaged CLI boot also
  exposed all 20 default agents with provider, web-search, cloud-orchestrator,
  and saved-ChatGPT credential variables absent.
- 2026-09-08: Independent review identified blocking gaps in build-environment
  isolation, Windows process-tree cleanup, and deterministic local runtime
  provisioning. The execution plan returned to Draft pending resolution.
- 2026-09-08: The user clarified and approved the configuration boundary:
  missing environment warnings belong to the config loader; probe cleanup is
  derived from placeholders in the config under test; `HOME`, `USERPROFILE`,
  and `.env` discovery are isolated; direct plugin environment reads and a
  repository-wide dummy-credential audit are out of scope.
- 2026-09-08: Preserved the previous specification/current-documentation
  baseline in commit `4e631ba9`, then revised the task and specification for
  the agreed loader-owned warning and targeted environment-isolation model.
  Documentation preparation and MkDocs build passed after the revision with
  only the previously observed repository warnings.
- 2026-09-08: The user approved the remaining review resolutions. Archive
  construction will run in an isolated Nox environment before pytest,
  automatically use an `uv`-managed Python 3.11 runtime by default, and use
  explicit POSIX/Windows process-tree cleanup with a closed-port assertion.
  The execution plan returned to Approved.
- 2026-09-08: Implemented the config-loader warning metadata, focused
  config-adjacent `.env` resolution coverage, and the shared isolated boot
  helper. The helper derives environment removals from the config, isolates
  `HOME`/`USERPROFILE`, owns POSIX/Windows process trees, captures log tails,
  validates the complete generated agent set, checks plugin-cache state, and
  verifies port closure. Focused verification passed: 51 tests passed and the
  Windows-only nested `.cmd` test was skipped on macOS; Ruff and Black checks
  passed. Native Windows cleanup remained pending at that checkpoint.
- 2026-09-09: Level 1 passed directly in 228.50 seconds and through
  `npm run test:cli:clean-env` in 241.50 seconds. Both runs created a fresh
  lean venv and dynamically installed the default plugin closure without
  provider credentials or model API calls.
- 2026-09-09: The first isolated level-2 build stopped before archive creation
  because `uv` creates a hidden `.temp` directory alongside its runtime. The
  locator was corrected to select one non-hidden, non-symlink runtime
  directory. The rerun provisioned CPython 3.11.16, built the portable archive
  in about two minutes, and `npm run test:cli:bundle` passed; the standalone
  release smoke also passed.
- 2026-09-09: Level 3 passed in 24.76 seconds with the verified archive and in
  21.72 seconds after an independent default isolated build. Stale staging and
  target directories were replaced, the installed wrapper booted, and its
  plugin cache stayed empty.
- 2026-09-09: Repository-environment isolation was checked around both archive
  builds: the SHA-256 of `pip freeze` remained
  `6e85c3100badd634bb09a8ebbbd630bba5fa7eb789bd9f5f6dc3611ada3d5829`.
  Focused distribution/config/script verification passed 69 tests with one
  expected Windows-only skip. Fast regressions passed: Core 506 passed with
  one expected xfail; application 394 passed with two skips and existing
  deprecation warnings.
- 2026-09-09: Final focused verification after the structural-error regression
  passed 70 tests with one expected Windows-only skip. Ruff and Black passed
  for all changed Python files, targeted Pyright passed with zero errors, and
  documentation preparation/MkDocs build succeeded with existing repository
  warnings. Repository-wide Pyright remains a pre-existing failed baseline
  (2,288 errors across unrelated Core/plugin/generated build trees plus a
  missing configured `examples` directory).
- 2026-09-09: Pushed commit `fedcaacb` and dispatched the existing release
  workflow against the task branch. GitHub Actions
  [run 34328869249](https://github.com/dynamicprogrammingsolutions/crystal-lattice/actions/runs/34328869249)
  passed the test job and boot-inclusive archive smoke on Linux AMD64, macOS
  AMD64, macOS ARM64, and Windows AMD64. The Windows `.cmd` launcher and
  process-tree cleanup passed natively. Release and download publication jobs
  were correctly skipped for the manual dispatch.

## Completion Notes

- Delivered all three root CLI distribution test levels, a shared
  credential-free default-config boot probe, isolated/deterministic archive
  construction, boot-inclusive release smoke, config-loader warning metadata,
  specification, requirements, and current user/maintainer documentation.
- Local acceptance passed on macOS ARM64: level 1 dynamically installed the
  default plugin closure in a fresh lean venv; level 2 built and booted the
  bundled-Python archive; level 3 replaced stale install state and booted the
  installed wrapper. Both archive builds left the repository Python
  environment unchanged.
- Native release evidence passed on Linux AMD64, macOS AMD64, macOS ARM64, and
  Windows AMD64 in GitHub Actions run `34328869249`. The manual run did not
  publish release or download assets.
- Fast regression evidence passed: Core 506 passed with one expected xfail;
  application 394 passed with two skips; focused task coverage passed 70 tests
  with the Windows-only local helper test skipped on macOS. Ruff, applicable
  Black checks, targeted Pyright, documentation preparation, and MkDocs build
  passed.
- The first isolated build exposed an `uv` runtime-directory locator issue
  caused by its hidden `.temp` directory. Selection now requires one
  non-hidden, non-symlink runtime directory, and both subsequent independent
  builds passed.
- Repository-wide Pyright remains outside this task's completion boundary: its
  existing baseline reports 2,288 unrelated errors and scans generated plugin
  build trees plus a missing configured `examples` directory.
- Cross-platform level-3 execution was not part of the approved CI scope. A
  cumulative one-boot release smoke or a Windows-only installed-wrapper check
  can be considered as post-completion follow-up.

## Post-completion follow-up

On September 9, 2026, the user expanded the completed distribution
verification scope. The strengthened target requires direct and independent
extracted-archive and public default-installer smokes, dynamic installation of
a non-preinstalled packaged plugin in separate caches, immediate
`crystal-lattice` command discovery through an existing PATH directory, native
CI invocation through the same npm commands used locally, descriptive
terminology, and simplification of duplicate orchestration.

This extension supersedes two decisions from the completed plan:

- Native release CI may now change to run both archive-based npm smokes on
  every target.
- Archive-based smokes no longer require an empty user plugin cache after
  boot. They begin empty, install one designated non-preinstalled plugin, and
  verify that exact installation independently.

The original completion notes remain the record of the earlier delivered
scope. New work and evidence are recorded below.

### Follow-up implementation notes

- 2026-09-09: The user approved the strengthened target and authorized removal
  of Nox when direct npm/script orchestration preserved isolation. The
  follow-up plan moved to Approved.
- 2026-09-09: Replaced pytest-owned acceptance scenarios with three standalone
  source-installation, extracted-archive, and default-installer smoke scripts.
  Root npm commands invoke those scripts through one thin archive
  build/selection dispatcher.
- 2026-09-09: Both archive-based smokes now copy the packaged default config,
  add `generic-callback-app`, prove it is absent from the preinstalled
  manifest, and independently verify its exact installation metadata in
  separate plugin and pip caches. Direct local npm runs passed in 25.1 seconds
  for the extracted archive and 21.5 seconds for the public default installer
  against the newly built macOS ARM64 archive.
- 2026-09-09: The public installer now selects an existing suitable writable
  PATH directory, avoids incompatible existing source/virtualenv commands,
  fails before installation when no candidate exists, supports matching local
  archives, and writes both shell and `.cmd` commands on Windows. The direct
  installer smoke serves the real script/archive/latest marker over loopback,
  uses no install-path or command-name override, resolves `crystal-lattice` by
  name, and boots it.
- 2026-09-09: Removed `noxfile.py`, replaced the Nox development dependency
  with `uv`, added temporary-venv direct orchestrators for bundled-Python and
  optimized builds, deleted the duplicate Python production installer, and
  routed local production installation through `install.sh`. The direct
  bundled build provisioned CPython 3.11.16 and preserved the worktree
  `pip freeze` hash
  `c173945f88d82974d9c600756086aa0ef1b36c4c8b16eb2878990962ab7b421a`;
  the isolated optimized-build `--help` path also passed.
- 2026-09-09: Focused helper, installer, runner, package-script, and release
  workflow coverage passed 52 tests with one expected Windows-only skip.
  Core fast regression passed 507 tests with one expected xfail; application
  fast regression passed 404 tests with one skip and existing deprecation
  warnings. Ruff, Black, targeted Pyright, shell syntax, workflow YAML,
  documentation preparation, and MkDocs build passed. The updated native
  workflow is implemented; native matrix execution remains pending.
- 2026-09-09: Final source-installation verification passed after restoring
  direct first-run `--config-local` generation. The archive-based smokes keep
  explicit default-derived configs only to add the non-preinstalled plugin
  probe.
- 2026-09-09: Native GitHub Actions run
  [34369660671](https://github.com/dynamicprogrammingsolutions/crystal-lattice/actions/runs/34369660671)
  passed both smokes on Linux AMD64, macOS AMD64, and macOS ARM64. Windows
  passed the extracted-archive smoke but the default-installer smoke resolved
  `bash` to the Windows Subsystem for Linux launcher, which had no installed
  distribution, instead of Git Bash. Added a shared resolver that derives Git
  Bash from Git for Windows PATH/install roots and is used by both the direct
  installer smoke and local production installation. Focused tests and the
  macOS default-installer smoke passed after the fix; native rerun pending.

### Follow-up execution plan

Status: Approved

Implement the follow-up in four checkpoints so direct user paths remain easy
to inspect and native failures can be attributed without coupling the two
archive-based smokes.

#### Checkpoint 1 — names, shared low-level helpers, and direct npm entry points

- Replace historical level-oriented command and test identifiers with
  source-installation, extracted-archive, and default-installer names. Use
  `test:cli:source-install`, `test:cli:archive`, and
  `test:cli:default-install`.
- Keep `scripts/run_cli_distribution_test.py` as a thin archive
  build/selection dispatcher, but have it invoke standalone scenario entry
  points directly instead of starting pytest.
- Add or extract focused helpers for isolated config creation, adding the
  designated plugin probe, inspecting the preinstalled manifest and plugin
  metadata, readiness, and process-tree cleanup.
- Keep pytest for unit tests, failure-path tests, script-contract tests, and
  optional wrappers around a direct scenario; do not maintain a second
  acceptance implementation inside pytest.

#### Checkpoint 2 — independent extracted-archive smoke

- Keep the existing archive smoke as the authoritative extracted-archive
  scenario.
- Extract the archive into a fresh directory using installer-independent code,
  retain structural/manifest/runtime-layout and macOS portability checks, and
  execute the archive launcher directly.
- Copy the packaged default config into a fresh config directory and append
  `path:${env:BUILTIN_PLUGINS}/generic-callback-app` to the global plugin list.
  First prove that this plugin is absent from `preinstalled-plugins.json`.
- Boot through the archive launcher with a unique home, workspace, config,
  plugin cache, and home-level pip cache. Require all default agents,
  candidate-specific `plugin_metadata.json`, and no redundant user-cache
  installation for default preinstalled plugins.

#### Checkpoint 3 — public default installer and immediate PATH discovery

- Make `scripts/install.sh` the default-installer acceptance boundary. Serve
  the checked-in installer, `latest.txt`, and the current native archive from
  an isolated loopback HTTP endpoint and run the normal `curl ... | bash`
  workflow without `VERSION`, `INSTALL_ROOT`, `BIN_DIR`, or `COMMAND_NAME`.
- Add deterministic automatic bin-directory selection. Reuse the parent of an
  existing `crystal-lattice` command when suitable; otherwise prefer existing
  PATH-listed `~/.local/bin` and `~/bin`, then the first remaining safe,
  writable, absolute PATH directory. Reject relative, current-directory,
  system-temporary-directory, world-writable, and
  active-virtual-environment candidates.
- Fail before replacing installation state if no automatic candidate is
  available. Preserve explicit `BIN_DIR` behavior for advanced/local use.
- On Windows, write both the Git Bash forwarding script and a `.cmd` command
  into the selected PATH directory.
- In the smoke, construct a controlled existing PATH directory under the
  isolated home, let the installer select it, prove command discovery by name,
  and boot by the resolved `crystal-lattice` command. Use a separate
  default-derived config and separate plugin/pip caches, then independently
  verify installation of `generic-callback-app`.
- Remove the repository-only Python archive installer if all consumers can
  use the public installer with a documented local-archive input. If a
  bootstrap or platform constraint requires retaining it, narrow it to the
  explicit local/offline use case and add focused parity tests rather than
  preserving duplicate smoke orchestration.

#### Checkpoint 4 — native CI, current documentation, and evidence

- Create the repository `.venv` needed by `scripts/repo_run.py` in each native
  build job, then invoke `npm run test:cli:archive` and
  `npm run test:cli:default-install` with the archive already built by that
  job.
- Keep the two npm invocations as separate workflow steps. Run the installer
  step with an `always()` condition gated on successful archive location so it
  still produces independent evidence after an archive-smoke failure.
- Update current user and implementation documentation only after behavior
  passes. Explain each named smoke, archive launcher, installed command,
  preinstalled plugin, user plugin cache, default PATH selection, override,
  and failure behavior where first used.
- Run both local archive-based npm commands with separate builds and with one
  shared prebuilt immutable archive; then run the full native matrix. Record
  separate command/cache evidence for both scenarios.

### Implementation decisions and open questions

- **Recommendation — direct installer boundary:** use the public
  `scripts/install.sh` path for default-installer acceptance. The current
  Python installer invoked with temporary absolute paths is useful unit/local
  coverage but is not the downloaded user's default workflow.
- **Recommendation — designated plugin:** use `generic-callback-app`. It is a
  packaged installable Python plugin outside the default preinstalled closure,
  has no model/API requirement, and has no external dependency or OS side
  effect. The smoke fails explicitly if it later becomes preinstalled.
- **Recommendation — independent state:** sharing the native archive build is
  safe because it is immutable input. Every mutable directory and cache is
  created by, owned by, and deleted after one scenario invocation.
- **Recommendation — CI independence:** retain two boots and two plugin
  installations. The additional runtime is accepted because removing either
  would weaken a direct workflow. The second smoke still runs after a failure
  in the first when the archive exists.
- **Recommendation — PATH behavior:** select an existing writable PATH
  directory instead of modifying shell profiles. This makes the command
  available in the current shell and avoids persistent profile edits.
  Explicit `BIN_DIR` remains available when automatic selection cannot satisfy
  a user's policy.
- **Recommendation — Windows command:** create both shell and `.cmd` commands
  and verify Git Bash plus native `cmd.exe` name resolution on the Windows
  runner.
- **Recommendation — simplification:** remove the Python archive installer if
  a small, documented local-archive input lets Nox and developers use the
  public installer. Retain it only if inspection finds a concrete bootstrap or
  platform capability that the shell installer cannot provide without greater
  complexity.
- **Decision — PATH and installer authority (user-approved):** implement the
  recommended automatic PATH-directory selection and consolidate
  user-facing/default installation on the public shell installer.
- **Decision — Nox simplification (user-approved):** Nox may be removed when
  direct npm/script orchestration preserves isolated build dependencies,
  deterministic relocatable Python provisioning, explicit runtime/archive
  overrides, and existing local build/install behavior.

### Documentation

- The target is updated first in
  `application/python/docs/development/specifications/cli-distribution/`.
- After implementation, update the application README and package
  installation guides with current automatic PATH behavior and the explicit
  override.
- Update the current distribution implementation page with the three named
  npm commands, direct scenario ownership, dynamic plugin probe, separate
  cache contract, and native workflow invocation.
- Update download/deployment maintainer documentation if the public installer
  gains a local-archive input or changes the files it writes on Windows.
- Remove the specification's temporary active-follow-up section after all
  affected requirements are verified.

### Task checklist

- [x] Rename scenario commands, tests, messages, and maintained documentation.
- [x] Refactor root scenario commands to invoke direct standalone acceptance
  implementations instead of pytest orchestration.
- [x] Add shared config/plugin-probe/cache-evidence helpers and focused tests.
- [x] Strengthen the extracted-archive smoke with independent dynamic plugin
  installation.
- [x] Add safe automatic PATH-directory selection and failure behavior to the
  public installer.
- [x] Add the Windows shell and `.cmd` command pair.
- [x] Add the direct public default-installer smoke through a loopback download
  endpoint and command-name resolution.
- [x] Consolidate or explicitly narrow the repository-only Python installer.
- [ ] Run both root archive-based smokes independently in every native release
  matrix job.
- [x] Update current user/maintainer documentation and requirement evidence.
- [ ] Run focused, fast-regression, local distribution, documentation, and
  native matrix verification.

### Requirement verification

- `CLIDIST-020`, `CLIDIST-052`: `npm run test:cli:archive` independently
  extracts the archive, runs its launcher directly, starts from empty
  plugin/pip caches, proves the candidate is not preinstalled, boots all
  default agents, and records candidate-specific installation metadata.
- `CLIDIST-030`, `CLIDIST-080`, `CLIDIST-081`: with an isolated home and
  controlled existing PATH directory, `npm run test:cli:default-install`
  downloads through the public installer with defaults, replaces stale
  installation state, is discoverable and executable as `crystal-lattice`,
  and fails before mutation when no suitable automatic directory exists.
- `CLIDIST-051`: independently captured paths and cache metadata show the two
  archive-based npm invocations share only the immutable archive.
- `CLIDIST-040`, `CLIDIST-050`, `CLIDIST-091`: package-script contract tests
  prove local and CI commands use the same direct entry points; every native
  matrix target reports separate archive and default-installer results.
- `CLIDIST-090`: specification and current documentation introduce concrete
  component/scenario names, and searches show unexplained historical level
  terminology has been removed from maintained commands, tests, diagnostics,
  and touched current documentation.

### Additional implementation verification

- Unit-test PATH candidate ordering, unsafe/relative/unwritable rejection,
  existing-command upgrades, explicit override behavior, and no-candidate
  failure on POSIX and Windows path forms.
- Unit-test shell and `.cmd` wrapper contents, argument forwarding, paths with
  spaces, and command-name collision behavior.
- Verify the extracted-archive smoke does not import or invoke installer
  scenario code and the default-installer smoke does not invoke archive-smoke
  orchestration.
- Verify both smokes reject a pre-populated plugin cache and assert the exact
  probe-plugin metadata rather than any cache entry.
- Run installer unit tests, distribution helper tests, root-script contract
  tests, and the application fast suite.
- Run `npm run test:cli:archive` and
  `npm run test:cli:default-install` with separate locally built archives,
  then repeat both against one explicitly supplied prebuilt archive.
- Run Ruff, applicable Black checks, targeted Pyright, documentation
  preparation, and MkDocs build.
- Push and dispatch the native release workflow; require separate successful
  archive and default-installer npm steps on Linux AMD64, macOS AMD64, macOS
  ARM64, and Windows AMD64.
