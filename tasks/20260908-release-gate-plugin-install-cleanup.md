# Release Gate Plugin Install Cleanup

Stop the CLI release and CI test gates from pip-installing repo-internal
plugin and shared helper packages, and make the gated test suites
self-sufficient in a clean environment.

## Requirements checklist

- [x] The CLI release and CI test gates install no repo-internal plugin or
  shared helper packages; only the core package, the application package, and
  the `openai` external dependency are installed.
- [x] Both release test gates pass in a clean environment containing only
  `core/python[dev]`, `application/python`, and `openai`.
- [x] Application test modules import plugin code through self-provided
  source paths rather than environment-installed plugin packages or
  collection-order `sys.path` leakage from other test modules.
- [x] Importing the light compaction feature modules of the claude-tools and
  kimi-tools plugins does not require their tool dependency trees (shared
  helper packages and their external dependencies), while the package
  re-export surface stays compatible.
- [x] Automated guards prevent plugin and shared helper packages from
  re-entering the gate install lines.
- [x] Every automatic install site of plugin/shared packages is audited;
  sites whose purpose is legitimate environment provisioning remain
  unchanged.

Policy constraint (user): the default and supported way is a clean
environment for an installation. Conflicted environments are not supported;
the gates must work on the intended default.

## Supporting facts

- Background: the v0.1.2 CLI release attempt failed at the local fast-tests
  stage (4 `test_application_reload_owner.py` failures); no tag was created.
  Root cause: the `path:` plugin loader pip-installs plugins with live-PyPI
  dependencies into a per-plugin cache dir, prepends it to `sys.path`, and
  evicts modules from `sys.modules` (`_evict_stale_modules` trusts
  `*.dist-info/top_level.txt`, which most modern dist-infos omit). The reload
  test then imported anyio 4.15.1 from the leaked cache dir while
  `typing_extensions` stayed at the environment's 4.14.1 (no `sentinel`) →
  ImportError. Environment-specific; clean environments pass.
- Nothing in `core/python/tests` imports `openai_responses`. Application
  tests need only the plugin's external `openai` dependency at collection
  time: six modules import `openai_responses_plugins` from a self-inserted
  src path, and the plugin modules import `openai`. The plugin package
  install itself was unnecessary.
- The workflow test jobs installed three shared helper packages because two
  application test files import `claude_tools.claude_compaction_feature`,
  and the eager `claude_tools/__init__.py` imported every tool module, which
  import the shared helpers and their external dependencies (`mcp`,
  `aiohttp`, `trafilatura`).
- The manual ChatGPT integration test imported `openai_responses_plugins`
  and `feature_system_message` before its own `sys.path` inserts and only
  collected successfully because alphabetically earlier test modules leaked
  those paths.
- Install-site audit found four sites: the release workflow test job, the
  `public-ci.yml` python-unit-tests job, `release.sh`, and
  `scripts/install_crystal_lattice_cli_dev.py` (dev-CLI provisioner; installs
  a runnable provider deliberately and never installed the shared helpers).

## Execution plan

Status: Approved

Reduce the three gate install lines to
`python -m pip install -e "core/python[dev]" -e application/python openai`
(`release.sh`, `release-crystal-lattice-cli.yml`, `public-ci.yml`). Make the
application test modules that import plugin code self-sufficient via
src-path inserts. Restructure the manual ChatGPT integration test so its
`sys.path` inserts precede its imports. Add guard tests asserting the
release script and both workflows never reinstall plugin/shared packages.
Audit every automatic install site and leave the dev-CLI provisioner
unchanged. Verify both gates in a clean venv containing only the new install
set, run the affected plugin suites, lint, and commit on `develop` once
verified.

### Implementation decisions and open questions

- Decision: `openai` stays in the gate install lines. It is an external
  PyPI dependency of modules imported at collection time, not a repo-internal
  package, so it does not violate the add/remove/rename coupling concern.
- Decision: `scripts/install_crystal_lattice_cli_dev.py` stays unchanged; its
  purpose is provisioning a runnable dev CLI, not satisfying test gates.
- Decision (revised during execution): PEP 562 lazy exports in the plugin
  package inits replaced the planned shared-helper src-path inserts in test
  files; see Implementation Notes.
- Open (deferred, out of scope): `path:` loader hermeticity — live-PyPI
  dependency resolution, `sys.path` activation, and the `top_level.txt`
  eviction gap remain the mechanism behind the original release blocker.
- Open (deferred, out of scope): pre-existing kimi Moonshot fixture setup
  errors and claude live-backend integration failures; unrelated to this
  correction.

### Documentation

No documentation changes required. The gate install set was not documented
anywhere (verified by grep across docs and READMEs); release documentation
describes usage, not internal install lines.

### Task checklist

- [x] Audit all automatic install sites of plugin/shared packages
- [x] Reduce the `release.sh` install line
- [x] Reduce the release workflow install line
- [x] Reduce the `public-ci.yml` install line
- [x] Restructure the manual ChatGPT integration test imports
- [x] Add lazy exports to `claude_tools/__init__.py`
- [x] Add lazy exports to `kimi_tools/__init__.py`
- [x] Add guard tests for the install lines
- [x] Verify both gates in a clean venv
- [x] Validate the lazy exports against the claude-tools and kimi-tools
  plugin suites
- [x] Lint all modified files
- [x] Commit on `develop`

### Requirement verification

- Gates install no plugin/shared packages: the three install lines plus
  `test_release_script_install_line_avoids_plugin_packages` and
  `test_release_workflows_install_only_core_application_and_openai`
  (release-script suite: 18/18 passed).
- Clean-environment gate pass: fresh venv with only `core/python[dev]`,
  `application/python`, and `openai` — core gate 504 passed, 26 deselected,
  1 xfailed; application gate 378 passed, 1 skipped, 92 deselected.
- Test self-sufficiency: the full application suite collects in the clean
  venv with zero plugin/shared packages installed; the manual test now
  inserts its plugin src paths before importing.
- Light imports without tool dependency trees: `claude_tools` and
  `kimi_tools` compaction feature modules import in the clean venv with no
  shared helpers or external tool deps present; the re-export surface is
  preserved (claude-tools default-filtered suite 115 passed, 9 deselected;
  kimi-tools suite 260 passed, 2 skipped).
- Guards: the two new tests, both passing.
- Audit: four sites audited; the dev-CLI provisioner intentionally unchanged.

### Additional implementation verification

- black and ruff clean on all modified files.
- The 3 kimi Moonshot setup errors were confirmed pre-existing by stashing
  the new `kimi_tools/__init__.py` and re-running with the original
  (identical errors).
- The 6 claude-tools failures are live-backend integration tests
  (Ollama/Gemini credentials) outside the default-filtered suite.

## Implementation Notes

- The first approach (shared-helper src-path inserts in the two claude test
  files) failed clean-venv verification: the import chain continues through
  `mcp_shared` into the external `mcp` SDK, and src inserts cannot provide
  external dependencies. The root cause was the eager plugin package inits
  importing every tool module; the fix became PEP 562 lazy exports, and the
  added test-file inserts were removed as unnecessary.
- `kimi_tools` has the same eager-init pattern; discovered when the gate
  error moved to `test_kimi_default_config_compaction_integration.py` after
  the claude fix. Fixed identically; its original init never re-exported the
  compaction feature, so its lazy init preserves the exact prior surface.
- Mid-execution confusion, no work lost: the agent shell's working directory
  had drifted to the main worktree, so relative-path checks made it appear
  the edits had been wiped; the edits (written via absolute paths) were
  intact in the develop worktree all along. The user confirmed and directed
  completion there.
- The original release blocker remains environment-specific: the shared
  pyenv environment has `typing_extensions` 4.14.1, so a local `release.sh`
  run from that environment still needs a clean venv or a typing_extensions
  upgrade. The clean-environment default passes, per the stated policy.

## Completion Notes

- Outcome: committed as `0879f6b3` on `develop` ("fix: stop installing
  plugin packages in release test gates"), 7 files, +118/−39. Working tree
  clean; not pushed. Files: the three install-line sites, the manual
  ChatGPT integration test, the release-script guard tests, and the
  `claude_tools`/`kimi_tools` package inits. The two claude compaction test
  files ended unchanged (inserts added, then removed once the lazy exports
  made them unnecessary).
- Requirement evidence: as recorded in Requirement verification; all six
  requirements are complete.
- Verification performed: clean-venv gates (core 504 passed; application
  378 passed, 1 skipped), release-script suite 18/18, claude-tools suite
  (default filter 115 passed; re-export subset 38 passed), kimi-tools suite
  (260 passed, 2 skipped), black/ruff clean.
- Plan deviations: lazy exports replaced the planned src-path inserts (root
  fix after the external-dependency discovery); `kimi_tools` was added to
  scope when its identical pattern surfaced.
- Issues discovered beyond scope, flagged for separate attention:
  `path:` loader non-hermeticity (live-PyPI resolution, `sys.path`
  activation, `top_level.txt` eviction gap) — the mechanism behind the
  original release blocker; pre-existing kimi Moonshot fixture setup errors
  (aiohttp fixture drift in the shared environment); claude-tools
  live-backend integration failures (credentials); the shared environment's
  `typing_extensions` 4.14.1 still blocks a local release run from that
  environment.
- Deferred: the loader hermeticity fix; end-to-end release-flow verification
  after merging `develop` to `main` (the 0.1.2 release remains untagged).