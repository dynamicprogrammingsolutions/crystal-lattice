# Isolated Environment Follow-up Fixes

Follow-ups to the repository `.venv` / `scripts/repo_run.py` change
(`bcab1836`): route the CLI release local gate through the repository venv,
wire the remaining plugin test suites into the npm-script venv default with
declared test dependencies, exclude live-backend tests from
tool-compat-shared's default run, and complete the `path:` plugin loader's
stale-module eviction.

Status: A–C complete and committed (`bcab1836`, `bea899ba`); D and E
SPLIT INTO `tasks/20260908-plugin-eviction-and-first-boot-smoke.md`
(2026-09-08); no remaining workstreams in this task.

## Requirements checklist

- [x] The CLI release npm scripts (`release:cli`, `release:cli:plan`,
  `release:cli:smoke`) run the release local gate inside the repository
  `.venv`, so the gate's pip install and both pytest suites execute in the
  isolated environment rather than the ambient one.
- [x] The plugin suites without npm scripts (kimi-tools, claude-tools,
  web-fetch-shared, tool-compat-shared) are runnable through the repository
  `.venv` via npm scripts, consistent with the existing `test:plugins:*`
  convention.
- [x] The `aiohttp_server` fixture resolves in the kimi-tools,
  web-fetch-shared, and tool-compat-shared suites in a clean `.venv`
  provisioned only from declared dev extras (`pytest-aiohttp` declared by
  kimi-tools and tool-compat-shared; `pytest-asyncio` declared by
  kimi-tools).
- [x] tool-compat-shared's default test run excludes integration
  (live-backend) tests, matching the sibling packages' `addopts`
  convention. (claude-tools had the identical gap and received the same
  fix; see Implementation Notes.)
- [ ] Re-activating a `path:` plugin install evicts all stale modules
  belonging to any distribution in the install dir, so reload tests pass
  even when the plugin cache resolves newer dependency versions than the
  environment. (Required by the confirmed runtime direction; SPLIT INTO
  `tasks/20260908-plugin-eviction-and-first-boot-smoke.md`.)

## Unresolved requirement questions and decisions

- **Q1 (boundary, blocking A and the npm-script part of B): RESOLVED** —
  folded into the in-flight change; landed as commit `bcab1836` together
  with the venv wrapper work.
- **Q2 (scope, blocking D): RESOLVED (2026-09-08)** — D and E are SPLIT
  INTO `tasks/20260908-plugin-eviction-and-first-boot-smoke.md`, which
  carries the execution-approval question, the full defect explanation,
  and the test rerun matrix. D remains a required fix for the supported
  lean-runtime path per the confirmed direction (see Q4).
- **Q3 (design, part of B): RESOLVED** — share `.venv`. Both release gates
  pass in the populated venv with plugin extras installed (core 504
  passed; application 390 passed, 1 skipped).
- **Q4 (policy): RESOLVED (2026-09-08, user-confirmed direction)** — keep
  `install_deps: true`. The intended architecture is: the lean runtime
  installs only core; every plugin (including default-config ones) loads
  dynamically with automatic dependency installation, and a slow first
  bootstrap is accepted; default-config plugins are deliberately NOT
  preinstalled into the lean env because users may disable them or use a
  different config. Hermeticity comes from the optimized bundle, where
  plugins are preinstalled into the shipped env from a specific config and
  no dynamic plugin loading is assumed. The earlier `install_deps: false`
  proposal is withdrawn; it contradicts this model.
- **Q5 (decision): OPEN** — "no dynamic plugin loading" is enforced only
  in the PyInstaller binary (`sys.frozen` disables dynamic installs,
  `install.py:50-58,130-135`; verified by
  `test_binary_distribution_optional_plugin_install.py`). The
  bundled-Python runtime archive is not frozen, so dynamic installs stay
  enabled for anything outside the preinstalled manifest, and there is no
  policy switch to disable dynamic installs in non-frozen runtimes.
  Recommendation: accept as an extension feature of the bundled-Python
  archive (users can add plugins; the shipped set is preinstalled either
  way) and document it; add a disable flag only if a deployment needs it.
- **Q6 (deviation, decision): OPEN** — `scripts/install_crystal_lattice_cli_dev.py:47-60`
  preinstalls `plugins/openai_responses` (editable) into the dev venv,
  contrary to the confirmed direction (the default config loads it via
  `path:`). Recommendation: verify nothing in the dev-CLI flow depends on
  it being importable without dynamic install, then remove it from the
  installer.
- **Q7 (gap, decision): OPEN** — the shipped CLI artifact (bundled-Python
  runtime archive) has no installed-bundle E2E. The existing
  `test_binary_distribution_bundle_e2e_ollama.py` boots an installed bundle
  with the default config and asserts `/agents`, but expects the
  PyInstaller binary layout (`crystal-lattice` at the extracted root) and
  is env-gated; the mandatory release-workflow smoke
  (`smoke_test_crystal_lattice_python_runtime_archive.py`) is
  structural-only (paths + `--runtime-layout-json`, no app boot, no
  config, no plugin loading), and the post-publish `smoke.sh` stops at
  `--help` + layout JSON. Recommendation: extend the E2E (or add a
  sibling) to accept the python-runtime layout (`bin/crystal-lattice`),
  split the default-config first-boot assertions (boot + `/agents` with
  dummy keys; no model needed, CI-cheap) from the gated Ollama tool-call
  flow, and wire the first-boot variant into the release workflow per
  platform.

## Supporting facts

### Confirmed runtime direction (2026-09-08) — verified against the code

- Lean runtime: installing only `core/python` + `application/python` is
  sufficient. The default config
  (`application/python/agent_terminal_app/default_config/config.json:575-603`)
  references every plugin as `path:${env:BUILTIN_PLUGINS}/<name>`; the one
  dotted spec (`plugins.tool_gating_feature.ToolGatingFeature`) ships inside
  `agent-core`. No default-config plugin expects a preinstalled package.
- Dynamic loading: the `path:` loader pip-installs each plugin plus its
  dependencies (live PyPI) into the per-config cache
  (`${env:CONFIG_DIR}/.plugin_cache/plugins`) on first use, cached by
  revision fingerprint — the accepted slow first bootstrap.
- Bundled-Python runtime package
  (`scripts/build_crystal_lattice_python_runtime_package.py`):
  `install_app_dependencies` installs core+app into the shipped python;
  `install_preinstalled_default_plugins` discovers plugins across
  top-level, provider, and agent specs
  (`collect_unique_declared_plugin_specs`, `config.py:229-243`), resolves
  transitive `local_workspace_dependencies`, installs them into the
  shipped env, and writes `preinstalled-plugins.json`; `runtime_layout.json`
  exposes it as `preinstalled_plugin_manifest`, so the loader imports those
  plugins directly (`local_path.py:335-362`).
- Optimized PyInstaller bundle (`scripts/build_crystal_lattice_binary.py`):
  plugins pip-installed into the build env, descriptors staged with
  `preinstalled: true` (`build_plugin_packaging_support.py:316-329`),
  collected as hidden imports; `sys.frozen` disables dynamic installs.
- Because dynamic loading with automatic dependency installation is the
  supported lean-runtime mechanism, the eviction gap below is a defect of
  the supported path, not an edge case (basis for Q2/Q4 reframing).

### Clean-install / first-boot coverage inventory (verified 2026-09-08)

- Release workflow (mandatory, per platform):
  `scripts/smoke_test_crystal_lattice_python_runtime_archive.py` — extract,
  required paths, launcher `--runtime-layout-json`, env-override assertions.
  No app boot, no config resolution, no plugin loading.
- Post-publish `deploy/aws-cli-downloads/smoke.sh`
  (`npm run release:cli:smoke`): runs the published installer into a temp
  root, then `--help` + `--runtime-layout-json`. No default-config boot.
- `application/python/tests/test_binary_distribution_bundle_e2e_ollama.py`
  (gated: `integration and ollama` marks + `RUN_CRYSTAL_BUNDLE_OLLAMA_E2E=1`
  + `CRYSTAL_LATTICE_BUNDLE_ARCHIVE` + platform match + local Ollama):
  extracts a built archive, boots the installed executable with
  `--config-local` (default config), asserts `/agents` exposes `ollama` and
  `cloud-script-author`, then runs a real Ollama/Qwen `read_file` tool-call
  flow. This is the "install and run the default config" test, but it
  expects the PyInstaller binary layout (`crystal-lattice` at the extracted
  root) and does not support the bundled-Python runtime layout
  (`bin/crystal-lattice`), which is what the CLI release ships.
- `test_binary_distribution_optional_plugin_install.py` (gated
  `integration`): frozen bundle rejects optional plugin install.
- `test_binary_distribution_docker.py` (gated `integration and docker`):
  Docker bundle smoke.
- Deviation: `scripts/install_crystal_lattice_cli_dev.py:47-60` preinstalls
  `plugins/openai_responses` into the dev venv (see Q6).

### Prior facts

- The venv wrapper change is committed as `bcab1836` on `develop`:
  `scripts/repo_run.py` runs a command with `.venv/bin` prepended to
  `PATH` and `VIRTUAL_ENV` set (an active `VIRTUAL_ENV` wins; no `.venv` →
  fail with `npm run install:venv` instructions). It resolves but does not
  create or populate the venv. All Python-invoking npm scripts are wrapped;
  `nox` is part of `core/python[dev]` extras;
  `application/python/tests/test_repo_run_script.py` asserts the exact set
  `using_repo_run == WRAPPED_SCRIPTS` (48 scripts after this task), so any
  newly wrapped script must be added to that set in lockstep. `_release_env`
  in `test_cli_download_release_scripts.py` pins the test runner's
  interpreter dir first on `PATH` (fixes pyenv-shim `python` resolution for
  release.sh tests).
- `release:cli`/`release:cli:plan`/`release:cli:smoke` are wrapped as
  `python scripts/repo_run.py bash deploy/...` in `bcab1836`;
  `release:cli:version:bump-patch` stays unwrapped
  (environment-independent).
- `install:all` provisions `.venv` with only `core/python[dev]` +
  `application/python`; `install:plugins` (added in `bcab1836`) provisions
  the four plugin suites with their dev extras.
- A single `pip install` with all four `-e "plugins/<name>[dev]"` targets
  fails with `ResolutionImpossible`: kimi-tools and claude-tools declare
  their shared helpers as direct `file://` dependencies, and pip cannot
  take one project from two different direct-URL sources in one
  resolution. `install:plugins` therefore chains two pip commands —
  bundles first (`kimi-tools`, `claude-tools`), then the shared libs
  (`tool-compat-shared`, `web-fetch-shared`). The reverse order silently
  replaces the editable shared-lib installs with regular copies when the
  bundles reinstall their `file://` dependencies (verified via
  `__file__` in a scratch venv).
- `aiohttp_server` fixture findings (verified 2026-09-08, pre-fix): kimi-tools 3
  errors (`TestMoonshotBackend`; dev extras declared only `pytest`; the test
  module also imports `pytest_asyncio` undeclared); web-fetch-shared 10
  errors (its dev extras already declared `pytest-aiohttp>=1.0.0` — purely
  environmental in the old shared env); tool-compat-shared 5 errors
  (`TestTavilyProviderMockHTTP`; dev extras declared only `pytest-asyncio`).
  The fixture comes from `pytest-aiohttp` (entry-point plugin) or
  `aiohttp.pytest_plugin` (requires `pytest_plugins` registration in the
  suite's top-level conftest).
- kimi-tools tests have no `conftest.py`;
  `test_kimi_web_search_tool.py` imports `tool_compat_shared` from the
  environment (no src-path insert), so that suite needs the packages
  installed into `.venv`.
- claude-tools had the same missing default integration filter as
  tool-compat-shared: its 5 default-run failures were all
  `integration`-marked live Ollama tests
  (`test_claude_read_tool_ollama_integration.py`). Fixed alongside C in
  `bea899ba`.
- Pre-existing tool-compat-shared failure (not fixed, flagged):
  `test_search_engine.py::test_glob_search_sorts_recent_files_first_and_matches_case_insensitively`
  — the case-insensitive glob returns only 2 of the 3 expected files
  (`UPPER.TXT` is dropped). Reproduces with both the `.venv` and pyenv
  runners on the pre-change tree; unrelated to this task.
- Loader eviction gap (`core/python/agent_app/plugin_sources/install.py`):
  `_evict_stale_modules` evicts only discovered top-level names;
  `_top_level_modules_for_install_dir` trusts
  `*.dist-info/top_level.txt` and early-returns on the first hit, so
  dependency dist-infos without `top_level.txt` (anyio,
  typing_extensions) are never evicted from `sys.modules` → mixed-version
  import graph after re-activation. This was the mechanism of the original
  release blocker (cache anyio 4.15.1 vs host typing_extensions 4.14.1).
  The `.venv` default narrows but does not close the window: the plugin
  cache resolves live PyPI at plugin-install time, later than
  `install:all`.
- Release-gate guard tests live in
  `application/python/tests/test_cli_download_release_scripts.py` and
  assert the gate install lines; the release wrap changes PATH
  resolution only, not the install lines.

## Execution plan

Status: A–C executed and committed; D and E SPLIT INTO
`tasks/20260908-plugin-eviction-and-first-boot-smoke.md`.

### Workstream A — release gate isolation (DONE, `bcab1836`)

Wrapped the three release npm scripts as
`python scripts/repo_run.py bash deploy/...` (`repo_run` prepends
`.venv/bin` to `PATH`, so release.sh's bare `python` resolves to the venv
for both the version read and the local gate). Kept
`release:cli:version:bump-patch` unwrapped (environment-independent).
Added the three scripts to `WRAPPED_SCRIPTS` in `test_repo_run_script.py`
plus exact-value assertions, and updated the stale unwrapped release
assertions in `test_cli_download_release_scripts.py`. Verified with the
wiring suite (12/12), the 18 release-script guard tests (install line
unchanged: `-e "core/python[dev]" -e application/python openai`), and a
live `release.sh --dry-run` through `repo_run` (version 0.1.1 resolved
from `.venv` at step 1/5, then the expected dirty-worktree refusal on
`develop`).

### Workstream B — plugin suite wiring under the venv default (DONE, `bcab1836`)

- Dev extras: kimi-tools += `pytest-aiohttp>=1.0.0`, `pytest-asyncio>=0.21.0`;
  tool-compat-shared += `pytest-aiohttp>=1.0.0`.
- npm scripts `test:plugins:kimi`, `test:plugins:claude`,
  `test:plugins:web-fetch-shared`, `test:plugins:tool-compat-shared`
  routed through `repo_run.py`; all four added to `WRAPPED_SCRIPTS`.
- Provisioning: `install:plugins` runs two chained pip installs through
  `repo_run.py` — bundles first, then shared libs (see Supporting facts
  for why a single four-`-e` command fails); `install:all` stays minimal
  (core + application only). Q3 resolved: shared `.venv`.
- Verified in a fresh scratch venv replicating `install:venv` →
  `install:all` → `install:plugins`: kimi 257 passed / 8 skipped, claude
  115 passed / 9 deselected (`-m "not integration"`), web-fetch-shared 85
  passed, tool-compat-shared 154 passed / 1 skipped / 3 deselected
  (`-m "not integration"`); all previously erroring fixture tests pass.
  Both release gates pass in the populated `.venv` (core 504 passed;
  application 390 passed, 1 skipped).

### Workstream C — tool-compat-shared default filter (DONE, `bea899ba`)

Added `addopts = "-m 'not integration'"` to its
`[tool.pytest.ini_options]`, plus the same for claude-tools (identical
gap; scope addition beyond the original plan, flagged to the user — see
Implementation Notes). Verified: default runs deselect the integration
classes (claude 115 passed / 9 deselected; tool-compat 154 passed / 3
deselected, only the pre-existing glob failure remains) and
`-m integration` still collects all 12 integration tests across both
suites.

### Workstream D — loader eviction completeness (SPLIT INTO
`tasks/20260908-plugin-eviction-and-first-boot-smoke.md`)

Mechanism of the defect: when a `path:` plugin is (re)installed,
`_activate_sys_path` (`install.py:178-186`) prepends the install dir to
`sys.path` process-wide and then evicts stale modules. Eviction
(`_evict_stale_modules`, `install.py:188-215`) only covers top-level names
discovered by `_top_level_modules_for_install_dir` (`install.py:217-242`),
which trusts `*.dist-info/top_level.txt` and early-returns on the first hit
— so dependency distributions installed alongside the plugin (anyio,
typing_extensions) are never evicted from `sys.modules`. After a
re-activation, imports resolve the plugin cache's newer dependency code
against `sys.modules` entries that still point at the host environment's
older copies → mixed-version import graph (the original release blocker:
cache anyio 4.15.1 vs host typing_extensions 4.14.1).

Fix: in `_top_level_modules_for_install_dir`, derive top-level names per
dist-info (`top_level.txt` when present, else a `RECORD`-based top-level
module scan or dist-info-name fallback) and remove the early-return that
skips dependency dist-infos. `_evict_stale_modules` then evicts every
matching module whose `__file__` lies outside the install dir. Add a
regression test simulating a dependency with two importable versions
(host-old vs cache-new) across a re-activation, asserting `sys.modules` no
longer holds the host copy. Verify `test_application_reload_owner.py`
passes in an environment with a deliberately skewed
typing_extensions/anyio pair.

### Workstream E — first-boot smoke for the shipped archive (SPLIT INTO
`tasks/20260908-plugin-eviction-and-first-boot-smoke.md`)

Extend `test_binary_distribution_bundle_e2e_ollama.py` (or add a sibling)
to accept the bundled-Python runtime archive layout (`bin/crystal-lattice`
launcher inside the package dir). Split the default-config first-boot
assertions (boot with dummy API keys + `/agents` check; no model needed)
into a CI-cheap variant wired into the release workflow per platform;
keep the Ollama tool-call flow env-gated as today.

### Implementation decisions and open questions

See Unresolved requirement questions and decisions (Q1–Q7) above: Q1,
Q2, Q3, and Q4 are resolved; Q5–Q7 are decisions recorded 2026-09-08
(Q7's implementation is SPLIT INTO
`tasks/20260908-plugin-eviction-and-first-boot-smoke.md`). Local
decisions taken
during execution: extras version floors follow the existing declarations
in sibling pyprojects; `install:plugins` installs only the four suites
that gained npm scripts, not every plugin in `plugins/`; the
`install:plugins` pip commands run bundles before shared libs (see
Supporting facts).

### Documentation

Done in `bcab1836`: root `README.md` gained the `install:plugins` step in
the venv flow and a note that the release npm scripts run the local gate
in `.venv`; `application/python/README.md`'s release section notes the gate
runs in the repository venv via the npm scripts. No user-facing product
documentation changes; this is dev tooling.

### Task checklist

- [x] A: wrap the three release npm scripts; update `WRAPPED_SCRIPTS`
- [x] A: release-wrap verification (wiring suite, dry-run smoke, 18 guard
  tests)
- [x] B: dev extras for kimi-tools and tool-compat-shared
- [x] B: npm scripts for the four suites; update `WRAPPED_SCRIPTS`
- [x] B: `install:plugins` provisioning script
- [x] B: fresh-`.venv` verification of all four suites and both gates
- [x] C: tool-compat-shared `addopts` + verification
- [ ] D: eviction discovery fix + regression test (SPLIT INTO
  `tasks/20260908-plugin-eviction-and-first-boot-smoke.md`)
- [ ] E: first-boot smoke for the shipped python-runtime archive
  (SPLIT INTO `tasks/20260908-plugin-eviction-and-first-boot-smoke.md`)
- [x] Documentation updates

### Requirement verification

- Release gate runs in `.venv`: the three release npm scripts route
  through `repo_run.py` (exact-value assertions in
  `test_repo_run_script.py`, 12/12); a live `release.sh --dry-run` through
  `repo_run` resolved version 0.1.1 from `.venv` (step 1/5) before the
  expected dirty-worktree refusal; the 18 release-script guard tests pass
  with the gate install line unchanged
  (`-e "core/python[dev]" -e application/python openai`). The full gate
  was not executed end-to-end locally (requires a clean `main` at
  `origin/main`); its commands resolve from `.venv` by construction via
  the same PATH prepend the fake-venv unit tests verify.
- Plugin suites runnable via npm in `.venv`: the four `test:plugins:*`
  scripts pass in the current populated `.venv` (kimi 264 passed / 1
  skipped; claude 115 passed / 9 deselected; web-fetch-shared 85 passed;
  tool-compat-shared 154 passed / 3 deselected with only the pre-existing
  glob failure) and in a fresh scratch venv provisioned exactly as
  `install:venv` → `install:all` → `install:plugins`.
- `aiohttp_server` resolves from declared extras: in that fresh venv, the
  previously erroring tests all pass (kimi 257 passed / 8 skipped;
  web-fetch-shared 85 passed; tool-compat-shared 154 passed) with no
  manual package installs.
- Default run excludes live backends: tool-compat-shared's and
  claude-tools' default runs deselect their integration classes
  (`-m integration` still collects all 12 across both suites).
- Eviction completeness: not verified here — D SPLIT INTO
  `tasks/20260908-plugin-eviction-and-first-boot-smoke.md`.

### Additional implementation verification

- `test_repo_run_script.py` passes after each `WRAPPED_SCRIPTS` change
  (exact-set assertion; 48 wrapped scripts).
- Both release gates pass in the populated `.venv` (Q3 evidence): core
  504 passed / 26 deselected / 1 xfailed; application 390 passed / 1
  skipped / 92 deselected.
- black and ruff clean on all modified files (the 36 pre-existing core
  lint errors are unchanged and out of scope).

## Implementation Notes

- The single four-`-e` `install:plugins` pip command failed with
  `ResolutionImpossible` (direct-URL conflict: kimi/claude declare the
  shared helpers as `file://` dependencies while the same dirs were
  explicit `-e` targets). Two chained commands fix it, and the order
  matters: bundles first leaves all four packages editable; shared-libs
  first silently downgrades the shared libs to regular copies when the
  bundles reinstall their `file://` dependencies (verified via
  `__file__` in a scratch venv).
- claude-tools was added to workstream C: its default run failed 5
  `integration`-marked live Ollama tests for the same missing-`addopts`
  reason as tool-compat-shared, and the new
  `npm run test:plugins:claude` would otherwise fail by default. Scope
  addition beyond the original plan, flagged to the user.
- The fresh-venv verification used a scratch venv under `/tmp`
  replicating the npm flow, leaving the developer `.venv` untouched.
- New pre-existing failure flagged (not fixed):
  `tool-compat-shared/tests/test_search_engine.py::test_glob_search_sorts_recent_files_first_and_matches_case_insensitively`
  — case-insensitive glob drops `UPPER.TXT` (2 of 3 files returned);
  reproduces with both runners on the pre-change tree.

## Completion Notes

- Outcome: A+B folded into the venv wrapper change and committed as
  `bcab1836` ("feat: run Python npm scripts and release gate in the repo
  venv", 10 files, +511/−68); C committed as `bea899ba` ("test: exclude
  live-backend tests from claude and tool-compat default runs", 2 files,
  +2). On `develop`; not pushed. D not executed — the user declined
  immediate execution; it remains the only open workstream (Q2).
- Plan deviations: claude-tools added to C (see Implementation Notes);
  `install:plugins` became two chained pip commands instead of one (pip
  direct-URL limitation); the planned release-specific fake-venv test
  was covered by the existing fake-venv mechanism tests plus exact-value
  wiring assertions instead.
- Issues discovered beyond scope, flagged for separate attention: the
  tool-compat-shared case-insensitive glob failure (pre-existing); the 36
  pre-existing core lint errors.
- Deferred: workstream D (loader eviction completeness) — see its plan
  above.