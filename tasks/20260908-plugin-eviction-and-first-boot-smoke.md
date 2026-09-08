# Path Plugin Eviction Completeness And Shipped-Archive First-Boot Smoke

Two workstreams split from
`tasks/20260908-isolated-env-followup-fixes.md`: complete the `path:`
plugin loader's stale-module eviction (the root cause of the original
v0.1.2 release blocker), and add an automated first-boot test for the
shipped bundled-Python runtime archive so a clean install is verified
against the default config before publishing.

## Requirements checklist

- [x] Re-activating a `path:` plugin install evicts from `sys.modules`
  every stale module belonging to any distribution contained in the
  install dir, so a reload cannot mix the plugin cache's dependency
  versions with the host environment's already-imported copies.
- [x] The reload flow passes in an environment with deliberately skewed
  dependency versions (host copy older than what the plugin cache's
  dependencies require).
- [ ] The shipped bundled-Python runtime archive has an automated
  first-boot test that boots the installed launcher with the default
  config and verifies the application exposes its expected agents,
  without model access or real credentials, runnable in the release
  workflow per platform.
- [ ] The deeper installed-bundle E2E (default-config boot plus a real
  Ollama tool-call flow) supports both bundle layouts — the PyInstaller
  binary and the bundled-Python runtime archive — and remains
  environment-gated.
- [ ] Release workflow guard tests keep protecting the gate install
  lines and cover the new first-boot workflow step.

Split from: `tasks/20260908-isolated-env-followup-fixes.md`
(workstreams D and E; SPLIT INTO this task).

## Unresolved requirement questions and decisions

- **Q1 (execution approval): RESOLVED for workstream D only
  (2026-09-08)** — the user approved execution of the eviction correction
  in a separate worktree. Workstream E remains deferred and is not
  authorized by this approval.
- **Q2 (E design):** wire the first-boot variant into the release
  workflow as a mandatory per-platform step (recommended: yes — it
  needs no model, no real credentials, uses dummy API keys, and takes
  seconds; it is the only coverage that the actually shipped artifact
  boots with the default config) versus keeping it environment-gated
  like the Ollama E2E.
- **Q3 (E design, local):** extend
  `test_binary_distribution_bundle_e2e_ollama.py` versus add a sibling
  test module for the python-runtime layout. Recommendation: extend the
  existing module with a layout-aware executable resolver and split the
  first-boot assertions into their own test, keeping one installed-bundle
  E2E family.

## Supporting facts

### Confirmed runtime direction (user, 2026-09-08)

- Lean runtime installs only core; every plugin (including
  default-config ones) loads dynamically with automatic dependency
  installation; a slow first bootstrap is accepted. Default-config
  plugins are deliberately not preinstalled into the lean env because
  users may disable them or use a different config.
- Optimized bundle: plugins are preinstalled into the shipped env from a
  specific config and no dynamic plugin loading is assumed (enforced in
  the PyInstaller binary via `sys.frozen`; the bundled-Python archive
  keeps dynamic installs enabled outside the preinstalled manifest —
  accepted extension feature, decision Q5 of the parent task).
- Consequence: dynamic loading with automatic dependency installation is
  the supported primary path of the lean runtime, so the eviction defect
  is a defect of the supported path, not an edge case.

### Eviction defect mechanism (the original v0.1.2 release blocker)

- `PipTargetInstallStrategy.ensure_installed`
  (`core/python/agent_app/plugin_sources/install.py:49-118`) pip-installs
  the plugin and — `install_deps` defaults true (line 85) — its full
  dependency tree from live PyPI into the per-plugin cache dir.
- `_activate_sys_path` (lines 178-186) prepends the install dir to
  `sys.path` process-wide and calls `_evict_stale_modules`.
- `_evict_stale_modules` (188-215) evicts only modules whose top-level
  names are discovered by `_top_level_modules_for_install_dir`
  (217-242), which scans the available `*.dist-info/top_level.txt` files
  and returns as soon as their combined result is nonempty. That skips
  fallback discovery for dependency distributions without
  `top_level.txt` (such as typing_extensions), so their host-imported
  copies stay in `sys.modules`.
- After a re-activation, imports resolve the cache's newer dependency
  code against stale `sys.modules` parents → mixed-version import graph.
  Concrete failure: plugin-cache anyio 4.15.1 (needs
  `typing_extensions.sentinel`, added in typing_extensions 4.15.0)
  vs host typing_extensions 4.14.1 → ImportError in 4 reload tests; the
  v0.1.2 release failed at the local fast-tests stage and no tag was
  created.
- The repo `.venv` default narrows but does not close the window: the
  plugin cache resolves live PyPI at plugin-install time, later than
  `install:all`, so any upstream release in between re-arms the failure.

### First-boot coverage inventory (verified 2026-09-08)

- Mandatory release smoke (per platform, in the workflow):
  `scripts/smoke_test_crystal_lattice_python_runtime_archive.py` —
  structural only (required paths + launcher `--runtime-layout-json` +
  env-override assertions); no app boot, no config resolution, no plugin
  loading.
- Post-publish `deploy/aws-cli-downloads/smoke.sh`
  (`npm run release:cli:smoke`): runs the published installer into a
  temp root, then `--help` + layout JSON; no default-config boot.
- `application/python/tests/test_binary_distribution_bundle_e2e_ollama.py`
  boots an installed bundle with the default config (`--config-local`),
  asserts `/agents` exposes `ollama` and `cloud-script-author`, then runs
  a real Ollama/Qwen `read_file` tool-call flow — but it expects the
  PyInstaller binary layout (`crystal-lattice` at the extracted root) and
  is env-gated (`RUN_CRYSTAL_BUNDLE_OLLAMA_E2E=1` +
  `CRYSTAL_LATTICE_BUNDLE_ARCHIVE` + platform match + local Ollama); it
  does not support the shipped bundled-Python runtime layout
  (`bin/crystal-lattice` launcher inside the package dir).
- The CLI release ships the bundled-Python runtime archive
  (`release-crystal-lattice-cli.yml` builds
  `dist/crystal-lattice-python-runtime` and smoke-tests it structurally).

## Execution plan

Status: Approved

Approval scope: workstream D only. Workstream E remains deferred; its
requirements, questions, plan, and checklist items are retained for later
work but are not part of this execution.

### Workstream D — loader eviction completeness

In `_top_level_modules_for_install_dir`
(`core/python/agent_app/plugin_sources/install.py:217-242`), derive
top-level names per dist-info — `top_level.txt` when present, else a
`RECORD`-based top-level module scan (or dist-info-name fallback) — and
remove the early-return that skips dependency dist-infos.
`_evict_stale_modules` then evicts every matching module whose `__file__`
lies outside the install dir (exactly the stale host copies). Add a
regression test in `core/python/tests/test_plugin_manager_localpath.py`:
a fake dependency with two importable versions (host-old vs cache-new),
imported before and after a re-activation, asserting `sys.modules` no
longer holds the host copy. Acceptance:
`application/python/tests/test_application_reload_owner.py` passes in an
environment with a deliberately skewed typing_extensions/anyio pair.

### Workstream E — shipped-archive first-boot smoke

- Add layout-aware executable resolution to the installed-bundle E2E
  (PyInstaller root executable vs python-runtime `bin/crystal-lattice`
  launcher).
- Split `_assert_default_config_starts` (boot with dummy API keys +
  `/agents` assertions; no model needed) into a standalone no-model
  first-boot test.
- Wire the first-boot variant into `release-crystal-lattice-cli.yml`
  per platform, running against the built archive after the existing
  structural smoke (pending Q2).
- Add a guard test in `test_cli_download_release_scripts.py` asserting
  the new workflow step; keep the install-line guards green.

### Test rerun matrix

Discovered 2026-09-08; rerun everything below when this task completes.

For D (change: `core/python/agent_app/plugin_sources/install.py`):

- Direct blast radius — the core plugin-manager family (28 tests):
  `pytest core/python/tests/test_plugin_manager_localpath.py
  core/python/tests/test_plugin_manager_localpath_scoped_git_fingerprint.py
  core/python/tests/test_plugin_manager_git_install.py
  core/python/tests/test_plugin_manager_multi_entries_and_module.py -q`.
  The scoped-git-fingerprint suite directly exercises
  `PipTargetInstallStrategy.ensure_installed`; the regression test lands
  in the localpath suite.
- Original failure surface — the minimal reproducer pair from the
  v0.1.2 release failure: `application/python/tests/test_application_reload_owner.py`
  (5 tests, including
  `test_reload_action_returns_accepted_then_replaces_after_drain`) and
  `application/python/tests/test_application_actions_endpoints.py`.
- Standard gates (default filters): `pytest core/python/tests -q` and
  `pytest application/python/tests -q`.
- Special acceptance: `test_application_reload_owner.py` in a
  deliberately skewed environment (host typing_extensions older than the
  plugin cache's anyio requires) — the regression scenario itself.

For E (changes: the E2E test module, the release workflow, possibly the
smoke script):

- `application/python/tests/test_binary_distribution_bundle_e2e_ollama.py`
  — gated deep run:
  `RUN_CRYSTAL_BUNDLE_OLLAMA_E2E=1 CRYSTAL_LATTICE_BUNDLE_ARCHIVE=<archive>
  pytest application/python/tests/test_binary_distribution_bundle_e2e_ollama.py -q -rs -m 'integration and ollama'`;
  the split first-boot variant needs only the archive env var.
- `application/python/tests/test_python_runtime_archive_smoke.py`
  (2 tests) — unit tests of the python-runtime smoke script; rerun and
  extend if the smoke script changes.
- `application/python/tests/test_cli_download_release_scripts.py`
  (18 tests) — release workflow content and npm-wiring guards
  (`test_release_workflow_uses_single_writer_artifact_handoff`,
  `test_release_workflows_install_only_core_application_and_openai`,
  `release:cli:smoke` wiring).
- `application/python/tests/test_binary_distribution_optional_plugin_install.py`
  (gated `integration` + `CRYSTAL_LATTICE_BUNDLE_ARCHIVE`) —
  installed-bundle family regression check.
- `application/python/tests/test_binary_distribution_docker.py` (gated
  `integration and docker`) — same family, when Docker is available.
- `application/python/tests/test_repo_run_script.py` — only if npm
  scripts change (the exact-set `WRAPPED_SCRIPTS` assertion must be
  updated in lockstep).
- End-to-end: the release workflow's new first-boot step runs per
  platform on the next tag push; locally, build the archive
  (`npm run build:bundle`) and run the first-boot variant plus
  `python scripts/smoke_test_crystal_lattice_python_runtime_archive.py
  <archive>` against it.

Both workstreams: black + ruff on all modified files.

### Implementation decisions and open questions

See Q1–Q3 above. D's fix approach is decided (per-dist-info discovery
with a RECORD-based fallback; no material open questions). E's open
items are Q2 (mandatory versus gated workflow step) and Q3 (extend
versus sibling test module).

### Documentation

- D: no user-facing documentation; the eviction guarantee is internal
  loader behavior. Optionally note it in the plugin-sources development
  docs if they describe install caching.
- E: document the new first-boot smoke in the release documentation
  (`application/python/README.md` release section) and how to run the
  installed-bundle E2E locally for the python-runtime layout.

### Task checklist

- [x] D: per-dist-info top-level discovery; remove the early-return
- [x] D: eviction covers all discovered distributions
- [x] D: regression test (two-version dependency across re-activation)
- [x] D: skewed-env reload verification
- [ ] E: layout-aware executable resolution in the bundle E2E
- [ ] E: standalone first-boot test (boot + `/agents`, dummy keys)
- [ ] E: wire the first-boot variant into the release workflow
  (pending Q2)
- [ ] E: workflow guard test
- [ ] Test rerun matrix executed and green
- [ ] Documentation updates
- [x] Lint (black + ruff) on modified files

### Requirement verification

- Eviction completeness: the deterministic regression loads an older host
  dependency, activates a target containing the newer dependency, and
  passes after stale package and submodule eviction. The application-owner
  regression performs the same skew during a real replacement reload and
  imports an API available only in the newer target dependency.
- First-boot smoke for the shipped archive: deferred with workstream E;
  no acceptance evidence recorded yet.
- Both layouts in the deep E2E: deferred with workstream E; no acceptance
  evidence recorded yet.
- Guards: deferred with workstream E; the existing release guards were not
  changed by workstream D.

### Additional implementation verification

- The complete workstream D matrix passed, including both standard gates
  under their default filters. Workstream E's gated bundle and release
  checks were not run because that workstream remains deferred.

## Implementation Notes

- Execution started in the separate worktree
  `/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260908-plugin-eviction`
  on branch `task/20260908-plugin-eviction`, based on commit `13ff8e18`.
- Only workstream D is being executed. Workstream E remains deferred.
- Distribution discovery now evaluates each `*.dist-info` independently:
  valid `top_level.txt` names are preferred, `RECORD` supplies package and
  module names when needed, and the existing install-root scan remains the
  fallback for targets with absent or unusable metadata.
- The deterministic skew regression imports an old host dependency package
  and submodule, activates a target containing a new dependency discovered
  only through `RECORD`, verifies a plugin can import the new-only API, and
  confirms a second activation preserves modules already loaded from the
  target.
- Focused plugin-manager verification passed (29 passed, 1 integration test
  deselected by the default filter). The original reload-owner and action
  endpoint surfaces passed (19 passed).
- Full default-filter gates passed after the completed regression set:
  core 506 passed, 26 deselected, 1 expected failure; application 392
  passed, 1 skipped, 92 deselected. Black and Ruff passed for all three
  modified Python files.

## Completion Notes

- Workstream D is complete. Every distribution in a plugin target is now
  evaluated independently, so one distribution's `top_level.txt` no longer
  suppresses discovery of dependencies represented only by `RECORD`.
- `RECORD` discovery covers top-level Python modules, packages, namespace
  package contents, and compiled extension modules. Invalid paths,
  metadata directories, data directories, and non-importable files are
  ignored. Targets with missing or unusable distribution metadata retain
  the prior install-root fallback.
- Eviction still removes only matching modules loaded from outside the
  activated target. A second activation preserves modules already loaded
  from that target.
- Verification evidence:
  - Plugin-manager family: 29 passed, 1 integration test deselected.
  - Reload-owner and action endpoint surfaces before the combined
    regression: 19 passed.
  - Completed reload-owner regression file: 5 passed.
  - Full core gate: 506 passed, 26 deselected, 1 expected failure.
  - Full application gate: 392 passed, 1 skipped, 92 deselected.
  - Black, Ruff, and `git diff --check`: passed.
- No user-facing documentation changed because this correction restores
  internal loader consistency without changing the public plugin contract.
- Workstream E and its three requirements remain incomplete and deferred.
  No archive smoke, bundle E2E, release workflow, workflow guard, or
  release documentation files were changed.