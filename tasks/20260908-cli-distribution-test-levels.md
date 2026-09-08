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

- [ ] Level 1 — a test provisions a clean Python environment (fresh venv
  containing only the core and application packages, lean install without
  dev extras) and clean runtime files (fresh workspace, `HOME`,
  `CONFIG_DIR`, plugin cache), boots the CLI with the default config, and
  asserts the server becomes ready and exposes the default-config agents.
  The default-config `path:` plugins must install dynamically into the
  clean plugin cache during the boot.
- [ ] Level 1 — runnable locally via a root npm script.
- [ ] Level 2 — the shipped bundled-Python runtime archive's launcher boots
  with the default config and exposes the default-config agents, verified
  locally via a root npm script.
- [ ] Level 3 — the install script installs a built archive into temporary
  install/bin directories and the installed wrapper command boots with the
  default config and exposes the default-config agents, runnable locally
  via a root npm script.
- [ ] The release-workflow smoke test boots the archive with the default
  config (in addition to the current structural checks); no other CI
  changes.
- [ ] The two bundle strategies stay separated: levels 1–3 target the
  bundled-Python runtime archive (the shipped artifact); the PyInstaller
  optimized-bundle tier and its tests remain a separate suite — not
  conflated, not modified, not removed.
- [ ] Proper specification and documentation for the distribution/test-level
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
  The level tests must reference only the python-runtime archive layout.
- **Specification and documentation are deliberately unplanned**: the
  completion agent decides the specification scope, placement, audience, and
  required file set, and discovers the details during execution. It must
  follow the repository documentation standards (read the documentation and
  standards indexes before creating or moving anything; specifications
  describe intended targets; requirements track live implementation,
  verification, documentation, and evidence). The absence of a plan here is
  not permission to skip the requirement.
- **npm script naming** (proposal, implementation may adjust consistently):
  `test:cli:clean-env` (level 1), `test:cli:bundle` (level 2),
  `test:cli:install` (level 3).

## Supporting facts

All facts below verified against the tree on 2026-09-08 (HEAD `9c502711`).

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
- Boot needs dummy API keys so provider config resolution does not fail
  (Ollama E2E pattern): `OPENROUTER_API_KEY`, `OPENAI_API_KEY`,
  `GEMINI_API_KEY`, `TAVILY_API_KEY`, `FIREWORKS_API_KEY`, `ZAI_API_KEY`
  set to dummy values.
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
  wrapped set (`using_repo_run == WRAPPED_SCRIPTS`, 48 scripts after
  `9c502711`) — every newly wrapped script must be added to that set in
  lockstep, plus an exact-value assertion.
- Marker conventions: `integration` for multi-layer/network tests; the
  application default run excludes `integration` and `docker`. The level
  tests are opt-in via their npm scripts.

## Execution plan

Status: Draft

### Level 1 — clean environment + files boot test

1. New test `application/python/tests/test_cli_clean_environment_boot.py`
   (name may adjust), marked `integration`:
   - create a fresh venv under tmp; `pip install -e core/python -e
     application/python` (lean, no dev extras);
   - clean files: tmp workspace cwd, fresh `HOME`, `CONFIG_DIR`,
     `PLUGIN_CACHE_DIR`; dummy API keys per the list above;
   - boot the fresh venv's `crystal-lattice --server --config-local --host
     127.0.0.1 --port <free>`;
   - poll `GET /api/hello`; assert `GET /agents` contains `ollama` and
     `cloud-script-author` (same assertions as the Ollama E2E's
     `_assert_default_config_starts`);
   - assert the plugin cache dir is populated — proving the default-config
     `path:` plugins dynamically installed rather than being skipped.
2. Root npm script `test:cli:clean-env` via `repo_run.py`; add to
   `WRAPPED_SCRIPTS` plus an exact-value assertion.
3. Estimated cost ~3-6 minutes (venv + live-PyPI plugin installs + boot);
   requires network.

### Level 2 — minimum gap filling: boot-inclusive archive smoke

1. Extend `scripts/smoke_test_crystal_lattice_python_runtime_archive.py`
   with a default-config boot step after the structural validation: run the
   launcher `--server --config-local --host 127.0.0.1 --port <free>` in a
   temp workspace with dummy API keys, poll `/api/hello`, assert `/agents`
   contains the default agents, terminate. Reuse the boot-helper pattern
   from `test_binary_distribution_bundle_e2e_ollama.py`.
2. This automatically upgrades the release-workflow smoke (all matrix
   targets, native runners) and the `install_prod_local` pre-install smoke —
   no workflow edits.
3. Root npm script `test:cli:bundle`: build the current-platform archive
   (`nox -s build_bundle`) then run the extended smoke; add to
   `WRAPPED_SCRIPTS`.
4. Implementation-time verification: confirm the archive boot exercises the
   preinstalled path (default-config plugins preinstalled at build) and
   record whether any dynamic installs occur.

### Level 3 — minimum gap filling: installer + installed-command boot test

1. New test (e.g.,
   `application/python/tests/test_cli_install_script_boot.py`), marked
   `integration`:
   - obtain the current-platform python-runtime archive: prebuilt via an
     env-var override (mirroring `CRYSTAL_LATTICE_BUNDLE_ARCHIVE`), else
     build it;
   - run `scripts/install_crystal_lattice_archive.py <archive>
     --install-root <tmp> --bin-dir <tmp> --command-name <unique>` into
     temp directories;
   - boot the installed wrapper command with `--server --config-local` in a
     clean workspace, poll `/api/hello`, assert `/agents` contains the
     default agents;
   - this covers the currently untested installer logic: staging swap,
     wrapper creation, platform archive selection.
2. Root npm script `test:cli:install` via `repo_run.py`; add to
   `WRAPPED_SCRIPTS`.
3. Secondary (not required for the minimum): extend
   `verify_installed_command` in the installer and the post-publish
   `deploy/aws-cli-downloads/smoke.sh` with the same boot.

### Specification and documentation — deliberately unplanned

The specification and documentation requirement stands (see Requirements
checklist), but this task intentionally provides no plan for it. The
completion agent decides the specification scope, placement, audience, and
required file set; discovers the details during execution; and follows the
repository documentation standards, including reading the documentation and
standards indexes before creating or moving anything. Do not treat this
section's absence as a reason to skip the requirement.

### Task checklist

- [ ] Level 1: clean-env boot test
- [ ] Level 1: npm script + `WRAPPED_SCRIPTS` lockstep
- [ ] Level 2: boot-inclusive smoke extension
- [ ] Level 2: npm script + `WRAPPED_SCRIPTS` lockstep
- [ ] Level 3: installer boot test
- [ ] Level 3: npm script + `WRAPPED_SCRIPTS` lockstep
- [ ] Specification and documentation (unplanned — completion agent decides
  and discovers)

### Requirement verification

- Level 1: `npm run test:cli:clean-env` passes with only the repo venv
  provisioned (`install:venv` → `install:all`), an empty plugin cache, and
  no ambient plugin packages; the test's fresh venv contains only core +
  application; the plugin cache is populated by the boot.
- Level 2: `npm run test:cli:bundle` builds the archive and the smoke boots
  it with the default config; `/agents` contains the default agents.
- Level 3: `npm run test:cli:install` installs into temp dirs and the
  installed wrapper boots with the default config; `/agents` contains the
  default agents.
- CI smoke: the extended smoke script boots a built archive locally; the
  release workflow runs it unchanged on all targets.
- Separation: no PyInstaller-tier test is modified or conflated; the level
  tests reference only the python-runtime archive layout.
- Specification and documentation: verified against whatever scope the
  completion agent establishes, committed alongside the code that makes it
  true.

### Additional implementation verification

- `test_repo_run_script.py` passes after each `WRAPPED_SCRIPTS` addition
  (exact-set assertion).
- Lint (ruff + black) clean on all modified files.