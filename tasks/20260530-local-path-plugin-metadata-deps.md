# Local Path Plugin Metadata Dependencies

Track the cleanup of local-path plugin dependency handling so `agent_app` no longer hardcodes specific shared plugin package names and no longer disables pip cache broadly for sibling local dependencies.

## Requirements checklist

- [ ] Add explicit plugin-owned metadata for local workspace sibling dependencies.
- [ ] Remove hardcoded shared dependency names from `core/python/agent_app/plugin_sources/local_path.py`.
- [ ] Remove the broad `--no-cache-dir` workaround for local sibling dependencies.
- [ ] Preserve stale-cache correctness by expanding plugin fingerprints to declared local workspace dependencies.
- [ ] Preserve latest-install `sys.path` precedence and stale module eviction behavior.
- [ ] Update tests to cover descriptor metadata, cache-key expansion, and install orchestration.
- [ ] Update plugin packaging/loading documentation and affected plugin descriptors.

## Background

The current local-path plugin loader has a boundary violation in:

- `core/python/agent_app/plugin_sources/local_path.py`

It contains a hardcoded tuple of shared package names:

- `tool-compat-shared`
- `web-fetch-shared`
- `mcp-shared`
- `skill-shared`
- `gemini-compaction-app`

Those names are not used because core needs them for import resolution. They were introduced as a stale-cache workaround for local plugins that declare sibling `file://...` dependencies in `setup.py`, for example:

- `plugins/codex-tools/setup.py`
- `plugins/kimi-tools/setup.py`
- `plugins/gemini-tools/setup.py`
- `plugins/qwen-tools/setup.py`
- `plugins/grok-tools/setup.py`
- `plugins/claude-tools/setup.py`
- `plugins/gemini-compaction-feature/setup.py`

The actual problem is:

1. Local-path plugin revisions are cache-keyed by plugin fingerprints.
2. Fingerprinting was previously scoped to the plugin project directory.
3. Some plugins later started depending on sibling local workspace packages via `file://...`.
4. A sibling package could change without changing the parent plugin project fingerprint.
5. The parent plugin install could then be incorrectly reused from cache.

The current hardcoded-name workaround scans project declaration text for specific sibling package names, fingerprints those sibling directories too, and records them as `local_dependencies`. This works, but it makes `agent_app` aware of specific repo plugin package names and must be manually extended whenever a new shared local package is introduced.

Separately, the install layer currently contains broad cache handling for these cases in:

- `core/python/agent_app/plugin_sources/install.py`

Specifically, `_pip_cache_args()` returns `["--no-cache-dir"]` whenever `request.metadata["local_dependencies"]` is present. This is broader than desired; the intended cleanup is to keep pip caching enabled and instead make cache correctness come from expanded fingerprints and explicit dependency-aware install orchestration.

## Relevant commit history

These commits are the key history to understand before changing the behavior.

### 1. `7c4008fd0f064cab842af4bd537ac657f1a83312`

Message:

- `Scope local-path Git fingerprint to plugin project directory, include scope in fingerprint, handle legacy fingerprints, and add test`

Why it matters:

- This changed local-path fingerprinting to be scoped to the plugin project directory.
- That was a reasonable boundary improvement by itself.
- It also created the precondition for the later stale-cache issue once sibling local dependencies were introduced.

Relevant files:

- `core/python/agent_app/plugin_sources/local_path.py`
- `core/python/tests/test_plugin_manager_localpath_scoped_git_fingerprint.py`

### 2. `2189dcf51e8c6416539870e5f53c2124a53d3f3c`

Message:

- `Fix plugin dependency installation boundaries`

Why it matters:

- `install_deps` in `core/python/agent_app/plugin_sources/install.py` changed to default to `True`.
- Several plugins started declaring sibling local dependencies in `setup.py`.
- This made the stale-cache issue structurally possible: sibling package changes could matter without changing the parent plugin project fingerprint.

Relevant files:

- `core/python/agent_app/plugin_sources/install.py`
- `plugins/codex-tools/setup.py`
- `plugins/kimi-tools/setup.py`

### 3. `b1844cf43aeb8ba54f26cf9ef1be4103174a7a35`

Message:

- `Add Kimi ReadMediaFile with provider-native image results`

Why it matters:

- This introduced the hardcoded `_LOCAL_PATH_DEPENDENCY_NAMES` list in `local_path.py`.
- It added the first direct workaround for the stale sibling-dependency cache problem:
  - `_fingerprint_local_path_dependencies()`
  - `_combine_fingerprints()`
  - `metadata["local_dependencies"]`
  - local-path-specific install policy that appended `--no-cache-dir`
- It also added regression coverage proving a sibling dependency change changes the parent plugin revision.

Relevant files:

- `core/python/agent_app/plugin_sources/local_path.py`
- `core/python/tests/test_plugin_manager_localpath_scoped_git_fingerprint.py`

### 4. `4d6525f896ef176c94bfdafaaa08a2c24e2c9a25`

Message:

- `Use pip cache for plugin dependency installs`

Why it matters:

- This moved pip cache handling into the installer and plugin manager.
- It removed the local-path-specific `_install_policy()` helper.
- It introduced the generic `pip_cache_dir` policy behavior.
- This commit touched the same area, but it was not the full stale-cache fix.

Relevant files:

- `core/python/agent_app/plugin_manager.py`
- `core/python/agent_app/plugin_sources/install.py`
- `core/python/agent_app/plugin_sources/local_path.py`

### 5. `491e332d48440273ef9351d4dc8b14c257d9c6e4`

Message:

- `Add shared background task runtime and Claude TaskStop support.`

Why it matters:

- This is the main complementing fix for the same stale-cache problem.
- It added:
  - `metadata["local_dependency_versions"]`
  - `_install_dir_matches_request()`
  - installed distribution version checks
- It also restored special pip handling for local sibling dependencies by making `_pip_cache_args()` return `--no-cache-dir` when `local_dependencies` are present.
- This same commit changed import precedence behavior to make the latest installed plugin take precedence:
  - remove path if already present
  - `sys.path.insert(0, value)`
  - evict stale modules from `sys.modules`
  - `importlib.invalidate_caches()`

This commit is important because not all of its behavior should be removed. The `sys.path` precedence and stale module eviction are still desirable and should remain.

Relevant files:

- `core/python/agent_app/plugin_sources/install.py`
- `core/python/agent_app/plugin_sources/local_path.py`
- `core/python/tests/test_plugin_manager_localpath.py`
- `core/python/tests/test_plugin_manager_localpath_scoped_git_fingerprint.py`

### 6. `93cd714cd8a5cb52fd80641006cc97c82bd526e3`

Message:

- `Add Codex skill activation support`

Why it matters:

- This expanded the hardcoded workaround by adding `skill-shared` to `_LOCAL_PATH_DEPENDENCY_NAMES`.
- It is evidence that the current approach is not scalable and leaks repo topology into core.

Relevant files:

- `core/python/agent_app/plugin_sources/local_path.py`
- `plugins/codex-tools/setup.py`

## Current behavior that should change

Current local-path resolution uses core-owned heuristics to discover a parent plugin's local workspace sibling dependencies. The loader:

- scans declaration text for hardcoded package names
- fingerprints those sibling directories
- stores `local_dependencies`
- sometimes disables pip cache broadly when such dependencies are present

This should be replaced with plugin-owned metadata.

## Proposed metadata format

Add an optional field to `agent_plugin.json`:

```json
{
  "entries": [
    "codex_tools.shell_tool.ShellArrayTool"
  ],
  "subdirectory": ".",
  "kinds": {
    "codex_tools.shell_tool.ShellArrayTool": "tools"
  },
  "local_workspace_dependencies": [
    {
      "name": "tool-compat-shared",
      "path": "../tool-compat-shared"
    },
    {
      "name": "mcp-shared",
      "path": "../mcp-shared"
    },
    {
      "name": "skill-shared",
      "path": "../skill-shared"
    }
  ]
}
```

Rules:

- `local_workspace_dependencies` is optional.
- Each item is an object with:
  - `name`: required distribution/project name
  - `path`: required relative path from the descriptor root
- The resolved path must point to an installable local project (`pyproject.toml` or `setup.py`).
- This metadata is for workspace-local installable packages, not plugin entry points.

## Proposed implementation plan

### 1. Extend descriptor parsing

Update:

- `core/python/agent_app/plugin_sources/descriptor.py`

Changes:

- Extend `PluginDescriptor` to include `local_workspace_dependencies`.
- Parse and validate the new field from `agent_plugin.json`.
- Reject malformed metadata with a clear descriptor validation error.

### 2. Replace hardcoded dependency name scanning

Update:

- `core/python/agent_app/plugin_sources/local_path.py`

Changes:

- Remove `_LOCAL_PATH_DEPENDENCY_NAMES`.
- Remove declaration-text scanning for hardcoded sibling package names.
- Replace sibling dependency discovery with descriptor-driven `local_workspace_dependencies`.

### 3. Expand parent plugin fingerprints using declared dependencies

Update:

- `core/python/agent_app/plugin_sources/local_path.py`

Changes:

- For each declared local workspace dependency:
  - resolve its path relative to the descriptor root
  - fingerprint it using the same git/file fingerprint logic already used for local projects
- Combine those fingerprints into the parent plugin fingerprint so any declared sibling dependency change changes the parent revision too.
- Store dependency fingerprint and revision metadata in the install request metadata for reuse checks.

Important note:

- This expanded fingerprint is the intended stale-cache solution.
- The broad `--no-cache-dir` workaround should be removed rather than retained.

### 4. Orchestrate explicit dependency installs

Update:

- `core/python/agent_app/plugin_sources/local_path.py`
- `core/python/agent_app/plugin_sources/install.py`

Changes:

- Explicitly install each declared local workspace dependency as its own local project before installing the parent plugin.
- Then install the parent plugin with `install_deps: false` so pip does not independently re-resolve workspace sibling `file://...` dependencies during the parent install.

Reasoning:

- This makes dependency handling explicit and deterministic at the loader level.
- It avoids using broad pip-cache disabling as a safety net.
- It also makes reuse decisions depend on dependency-specific revisions rather than wheel cache behavior.

### 5. Keep the good parts of the later installer logic

Preserve behavior from `491e332d48440273ef9351d4dc8b14c257d9c6e4` in:

- `core/python/agent_app/plugin_sources/install.py`

Keep:

- latest-install precedence on `sys.path`
- duplicate path removal before insert
- stale module eviction from `sys.modules`
- `importlib.invalidate_caches()`
- install-dir metadata matching and reuse checks

### 6. Remove the broad no-cache behavior

Update:

- `core/python/agent_app/plugin_sources/install.py`

Changes:

- Remove the special `if request.metadata.get("local_dependencies"): return ["--no-cache-dir"]` branch from `_pip_cache_args()`.
- Keep normal pip cache support through `pip_cache_dir`.

### 7. Shift reuse checks to dependency revision metadata

Update:

- `core/python/agent_app/plugin_sources/install.py`
- `core/python/agent_app/plugin_sources/local_path.py`

Changes:

- Store dependency revision/fingerprint metadata for declared local workspace dependencies in `plugin_metadata.json`.
- Make `_install_dir_matches_request()` compare the current requested dependency revisions/fingerprints against the installed metadata.
- Keep `local_dependency_versions` only if it is still useful for diagnostics, but do not rely on broad cache disabling for correctness.

### 8. Add a guard against undeclared sibling local dependencies

Update:

- `core/python/agent_app/plugin_sources/local_path.py`

Changes:

- If a plugin project still contains repo-local sibling `file://...` dependencies in packaging config but does not declare them in `agent_plugin.json`, return a clear resolution error.

Goal:

- Future omissions should fail loudly instead of silently reintroducing stale-cache behavior.

### 9. Migrate affected plugin descriptors

Update `agent_plugin.json` in plugins that currently use sibling local dependencies, including at least:

- `plugins/codex-tools/agent_plugin.json`
- `plugins/kimi-tools/agent_plugin.json`
- `plugins/gemini-tools/agent_plugin.json`
- `plugins/qwen-tools/agent_plugin.json`
- `plugins/grok-tools/agent_plugin.json`
- `plugins/claude-tools/agent_plugin.json`
- `plugins/gemini-compaction-feature/agent_plugin.json`

Keep in mind:

- The plugin manager should stop depending on hardcoded names.
- Existing `setup.py` sibling `file://...` references may still remain for developer installs, but correctness for plugin-manager-driven installs should come from descriptor metadata plus dependency-aware orchestration.

## Tests to update or add

### Core tests

Update or add coverage in:

- `core/python/tests/test_plugin_manager_localpath.py`
- `core/python/tests/test_plugin_manager_localpath_scoped_git_fingerprint.py`

Required coverage:

- Descriptor parsing accepts `local_workspace_dependencies`.
- Malformed metadata is rejected clearly.
- Declared sibling dependency changes change the parent plugin revision.
- Parent plugin installs no longer rely on broad `--no-cache-dir`.
- Declared local workspace dependencies are installed first.
- Parent plugin install uses explicit dependency-aware orchestration.
- Existing latest-install `sys.path` precedence and stale module eviction behavior still works.

### Regression target

Ensure there is still a regression test proving:

- changing a declared local workspace dependency invalidates parent plugin cache reuse even if the parent plugin files did not change

## Documentation to update

Update docs that describe plugin packaging and descriptors, especially:

- `plugins/docs/plugin-packaging-and-loading.md`
- any plugin authoring docs that describe `agent_plugin.json`

Document:

- the new `local_workspace_dependencies` field
- when to use it
- that it replaces core hardcoded shared package name heuristics
- that declared local workspace dependencies expand the parent plugin cache fingerprint
- that the plugin manager explicitly installs declared local workspace dependencies

## Notes for the implementing agent

- Do not remove the `sys.path` precedence and stale module eviction behavior from `install.py`; that solved a different but related correctness problem.
- The cleanup target is the heuristic shared-package-name list and the broad no-cache workaround, not the later import freshness fixes.
- Prefer making descriptor metadata the single source of truth for local workspace sibling dependencies.