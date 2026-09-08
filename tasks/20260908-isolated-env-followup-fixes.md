# Isolated Environment Follow-up Fixes

Follow-ups to the repository `.venv` / `scripts/repo_run.py` change
(`bcab1836`): route the CLI release local gate through the repository venv,
wire the remaining plugin test suites into the npm-script venv default with
declared test dependencies, exclude live-backend tests from
tool-compat-shared's default run, and complete the `path:` plugin loader's
stale-module eviction.

Status: A–C complete and committed (`bcab1836`, `bea899ba`); D pending
(Q2, execution declined 2026-09-08).

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
  environment. (Inclusion pending open question Q2; execution declined
  2026-09-08.)

## Unresolved requirement questions and decisions

- **Q1 (boundary, blocking A and the npm-script part of B): RESOLVED** —
  folded into the in-flight change; landed as commit `bcab1836` together
  with the venv wrapper work.
- **Q2 (scope, blocking D): OPEN** — A–C are landed, so D is the only
  remaining workstream in this task. The user declined immediate execution
  (2026-09-08); keeping D here versus splitting it into a dedicated task
  remains the user's call. D is self-contained: one discovery function in
  `core/python/agent_app/plugin_sources/install.py` plus a regression test
  in `core/python/tests/test_plugin_manager_localpath.py`.
- **Q3 (design, part of B): RESOLVED** — share `.venv`. Both release gates
  pass in the populated venv with plugin extras installed (core 504
  passed; application 390 passed, 1 skipped).
- **Q4 (policy, out of scope, recorded):** `install_deps` default for
  repo-internal `path:` plugins (live-PyPI resolution at plugin-install time).
  The `.venv` model makes `install_deps: false` (venv as single dependency
  authority) more attractive, but changing it is a product decision beyond
  this task.

## Supporting facts

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

Status: A–C executed and committed; D pending (Q2).

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

### Workstream D — loader eviction completeness (PENDING, Q2)

In `_top_level_modules_for_install_dir`, derive top-level names per
dist-info (`top_level.txt` when present, else a `RECORD`-based top-level
module scan or dist-info-name fallback) and remove the early-return that
skips dependency dist-infos. `_evict_stale_modules` then evicts every
matching module whose `__file__` lies outside the install dir. Add a
regression test simulating a dependency with two importable versions
(host-old vs cache-new) across a re-activation, asserting `sys.modules` no
longer holds the host copy. Verify `test_application_reload_owner.py`
passes in an environment with a deliberately skewed
typing_extensions/anyio pair.

### Implementation decisions and open questions

See Unresolved requirement questions and decisions (Q1–Q4) above: Q1 and
Q3 are resolved; Q2 remains open and blocks D only. Local decisions taken
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
- [ ] D: eviction discovery fix + regression test (pending Q2)
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
- Eviction completeness: not verified — D not executed (pending Q2).

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