# CLI Distribution Test Levels

Make all three installation/boot levels of the shipped CLI artifact testable
locally through root npm scripts, extend the release-workflow smoke to boot
the archive with the default config, and create proper specification and
documentation for the model.

Level model (user-confirmed):

1. **Clean Python environment + files** — no bundling; provisions a fresh
   environment and boots from source files. Catches plugin install errors
   and app-boot issues in a clean environment earliest (the original
   release-blocker error class).
2. **Bundled archive** — the shipped bundled-Python runtime archive. Given
   level 1 works, this catches issues in the bundle script.
3. **Bundled archive + install script** — the installed command. Given
   levels 1+2 work, this catches issues in the installation.

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
- [ ] Run acceptance, regression, formatting, and documentation verification.

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
- 2026-09-08: Implemented the config-loader warning metadata, focused
  config-adjacent `.env` resolution coverage, and the shared isolated boot
  helper. The helper derives environment removals from the config, isolates
  `HOME`/`USERPROFILE`, owns POSIX/Windows process trees, captures log tails,
  validates the complete generated agent set, checks plugin-cache state, and
  verifies port closure. Focused verification passed: 51 tests passed and the
  Windows-only nested `.cmd` test was skipped on macOS; Ruff and Black checks
  passed. Native Windows cleanup remains pending release-matrix execution.
