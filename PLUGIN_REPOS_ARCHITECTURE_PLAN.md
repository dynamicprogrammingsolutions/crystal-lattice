# Plugin Repositories (New Architecture) — Plan & TODO

This plan introduces a repo-root `plugins/` directory that contains *real* plugin repositories used by the terminal app configuration (`application/python/agent_terminal_app/config_openrouter_app_layer.json`).

Important note:
- The repo-root `plugins/` directory is intentionally *not* a Python package (no `plugins/__init__.py`).
- The legacy built-in plugin import path `plugins.*` continues to resolve to `core/python/plugins`.
- Each repo below ships its own distinct Python package name (e.g. `codex_tools`, `openrouter_plugins`, `feature_*`) to avoid import ambiguity.

## Target Layout

- `plugins/codex-tools/`
  - Python package: `codex_tools`
  - Contents: `ShellTool`, `ApplyPatchTool`
  - Descriptor: `codex_tools/agent_plugin.json`

- `plugins/openrouter/`
  - Python package: `openrouter_plugins`
  - Contents: `OpenRouterProvider`, OpenRouter extensions (reasoning, tools, websearch)
  - Descriptor: `openrouter_plugins/agent_plugin.json` with `entries` + `kinds`

- `plugins/feature-system-message/`
  - Python package: `feature_system_message`
  - Contents: `SystemMessageFeature`
  - Descriptor: `feature_system_message/agent_plugin.json`

- `plugins/feature-file-context/`
  - Python package: `feature_file_context`
  - Contents: `FileContextFeature`
  - Dependencies: includes heavy deps in packaging metadata (e.g. `GitPython`)
  - Descriptor: `feature_file_context/agent_plugin.json`

- `plugins/feature-web-context/`
  - Python package: `feature_web_context`
  - Contents: `WebContextFeature`
  - Dependencies: includes heavy deps in packaging metadata (e.g. `trafilatura`)
  - Descriptor: `feature_web_context/agent_plugin.json`

## Config Target

Update `application/python/agent_terminal_app/config_openrouter_app_layer.json` to:
- Provide a real `plugin_cache_dir` so the application uses `PluginManager`.
- Replace `plugins.*` references with `path:` module-only specs pointing at the new repos.
- Keep application plugins as-is (application plugins migration is explicitly deferred).

Cache policy:
- Default `plugin_cache_dir` for real use: `~/.crystal/cache/plugins`.
- Tests should override HOME (or set an explicit cache dir) to keep runs isolated.

## Path Resolution Improvement

To make configs robust regardless of CWD:
- Inject `plugin_policy.base_dir = <directory containing config file>` when `AgentApplication` constructs a `PluginManager`.
- Resolve relative LocalPath specs and relative local-Git URLs against `plugin_policy.base_dir`.
- (Optional but recommended) Resolve `plugin_cache_dir` relative to base_dir if not absolute.

## TODO (ordered)

1. [x] Create repo-root `plugins/` directory and repo subdirectories
2. [x] Create `plugins/codex-tools/` (pyproject, README, `codex_tools/*`, descriptor)
3. [x] Create `plugins/openrouter/` (pyproject, README, `codex_openrouter/*`, descriptor with kinds)
4. [x] Create `plugins/feature-system-message/` (pyproject, README, package, descriptor)
5. [x] Create `plugins/feature-file-context/` (pyproject, README, package, descriptor, heavy deps)
6. [x] Create `plugins/feature-web-context/` (pyproject, README, package, descriptor, heavy deps)
7. [x] Update `AgentApplication` to inject `plugin_policy.base_dir` and resolve `plugin_cache_dir` relative to base_dir
8. [x] Update loaders to resolve relative LocalPath and local Git paths using `policy.base_dir`
9. [x] Update `application/python/agent_terminal_app/config_openrouter_app_layer.json` to use the new plugin repos
10. [x] Add/adjust a lightweight test that validates the config loads and plugins resolve without calling OpenRouter
11. [x] Run targeted test suites (core plugin manager tests + application config tests)
12. [ ] Quick docs note (optional): mention `plugins/` repo layout and how the config wires them
13. [x] Add regression test: repo-root `plugins/` dir does not shadow built-in `core/python/plugins`
14. [x] Move plugin-specific tests into the corresponding plugin repositories
