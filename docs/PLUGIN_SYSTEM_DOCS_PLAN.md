# Plugin System Documentation Plan and TODO

## Goals
- Provide comprehensive documentation for plugin authors about packaging, structure, metadata, and “how to wire” plugins into the application.
- Provide a separate application configuration page that explains all plugin-related config fields and supported spec formats with examples.
- Ensure newly added classes/methods are documented with practical docstrings and usage examples.

## Deliverables
- Update: `docs/plugins/development.md` (authoring + packaging + wiring)
- New: `docs/plugins/application-config.md` (application config for plugins)
- Code docstrings: `agent_app/plugin_manager.py`, `agent_app/application_future.py` (accessors), loaders in `plugin_manager.py`
- Navigation updates (mkdocs): add the new page under Plugins

## Outline

### A. Plugin Development (update docs/plugins/development.md)
1) Authoring plugins
- Supported kinds: ProviderPlugin, ProviderExtensionPlugin, FeaturePlugin, ToolPlugin, Application Plugin (app layer)
- Required/optional methods per kind, behavior, lifecycle notes
- Stable IDs (`name`), `version`, and duck-typing used by auto-kind detection

2) Packaging & layout
- Package layout (example):
  - `dev_plugins/` with `__init__.py`, one or more modules that define plugin classes
  - Optional `agent_plugin.json` descriptor in package root
- Distributable packaging options:
  - Using `pyproject.toml` (PEP 517/518) with setuptools
  - Minimal `setup.py` for local development
- Versioning and dependencies

3) Descriptor (agent_plugin.json)
- Purpose: declare entries and optional kinds; overrides auto-discovery
- Location: under the importable package root (preferred) or install dir
- Schema:
  - `entries: string[]` — dotted paths to plugin classes
  - `kinds: Record<string, "providers"|"tools"|"extensions"|"features"|"application">` (optional)
- Example file with two tool entries

4) Wiring each plugin kind (how to reference in config)
- Provider: dotted class, local path, git; example JSON snippets
- Extension: how to enable; ordering with other extensions
- Feature: when and why; simple example
- Tool: single class, entries list, module-only package with descriptor
- Application plugin: dotted class and local path/git form

5) Best practices
- Keep state immutable, use adapters’ defaults
- Security considerations for tooling (I/O), and for Git distribution

### B. Application Configuration (new docs/plugins/application-config.md)
1) Overview
- Where the `plugins` block lives; relation to agents; `plugin_cache_dir`; `plugin_policy`

2) Plugin spec forms
- Dotted class
- Local path (string/object): single class, module-only, entries list
- Git (string/object): single class, module-only, entries list
- Descriptor interaction and precedence vs discovery

3) Full config forms
- Mapping-by-kind with arrays
- Flat list with auto-kind
- Canonical list entries with optional `kind`

4) Placeholders & resolution
- `${env:VAR}` (embedded supported), `${file:...}` (whole-string)
- Debugging placeholder issues (`get_config_errors`, logged errors)

5) Policy & security
- `allow_remote` (default false), `allowed_git_hosts` allowlist
- `pip_args`, `sys_path_precedence` (append default; core-first)
- Guidance: pin refs, vet repositories

6) Examples (copy/paste ready)
- Local path (mixed single class and entries list)
- Git module-only with descriptor
- Canonical-only config with explicit kinds

7) Troubleshooting
- Common loader errors; how they’re logged; how to surface from `AgentApplication.get_config_errors()`

### C. Code Docstrings (new/improved)
- `core/python/agent_app/plugin_manager.py`
  - Class `PluginManager`: purpose, usage, policy fields
  - Method `normalize_plugins(plugins_raw)`: accepted forms, return shape, example
  - Method `load_plugins(canonical_items)`: behavior, supported spec forms, return structure, examples (entries list, module-only, descriptor)
  - Helper `_discover_module`: discovery rules (only providers/tools/extensions/application; module-defined classes only)
  - Classes `LocalPathSource` and `GitInstallerSource`: supports/prepare/load docstrings with spec examples and side effects
- `core/python/agent_app/application_future.py`
  - Method `get_config_errors()`: description and example usage for debugging

- Cross-reference docstrings: link to `docs/plugins/development.md` and `docs/plugins/application-config.md`

### D. MkDocs Navigation
- Update `mkdocs.yml` to add:
  - Plugins → Development (updated)
  - Plugins → Application Configuration (new)

## TODO (ordered)
1. [x] Expand `docs/plugins/development.md` with packaging, descriptor, and wiring sections (A.1–A.5)
2. [x] Add new `docs/plugins/application-config.md` with full structure (B.1–B.7)
3. [x] Add/expand docstrings in `agent_app/plugin_manager.py` (PluginManager, LocalPathSource, GitInstallerSource, normalize_plugins, load_plugins, _discover_module)
4. [x] Add docstring to `AgentApplication.get_config_errors()` with usage snippet
5. [x] Add cross-links in docstrings to the two docs pages
6. [x] Update `mkdocs.yml` navigation to include the new page under Plugins
7. [x] Add example snippets and ensure JSON examples validate (lint pass)
8. [x] Quick proofreading pass and consistency check for terms (module-only, entries list, descriptor)

## Examples To Include (snippets)
- Packaging (pyproject.toml) for `dev_plugins`, minimal `setup.py`
- Agent plugin descriptor `agent_plugin.json` with two entries and kind override
- Config mapping-by-kind + local path entries list
- Config canonical list with dotted class + git module-only
- Debugging: retrieving `get_config_errors()` output

## Acceptance
- Docs build without errors; pages appear in nav
- Snippets are copy-paste runnable within tests/fixtures layout
- Docstrings provide clear guidance and link to docs pages
