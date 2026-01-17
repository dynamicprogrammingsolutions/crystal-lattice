# Application Plugin Configuration

This page explains how to configure plugins in the application. It covers the `plugins` block, spec formats (dotted, local path, Git), placeholders, policy, and ready-to-use examples.

## Overview

- `plugins`: defines provider(s), extensions, features, tools, and application plugins.
- `plugin_cache_dir`: enables plugin installs and caching (for both `git+...` and `path:...`).
- `plugin_policy`: controls installation and security policy (see Policy & Security).

## Spec Formats

Each plugin reference is a “spec” that can take one of the following forms:

- Dotted class (no side effects)
  - `"pkg.module.Class"`

- Local path (single class)
  - String: `"path:/abs/or/rel::pkg.module.Class"`
  - Object: `{ "path": "/abs/or/rel", "entry": "pkg.module.Class" }`

  Local path specs are installed into `plugin_cache_dir` via `pip install --target ...`,
  then loaded from the installed cache directory.

- Local path (module-only or multiple classes)
  - Descriptor-driven module-only (recommended): `"path:/abs/or/rel"` or `{ "path": "/abs/or/rel" }`
  - Explicit module-only (legacy): `"path:/abs/or/rel::pkg"` or `{ "path": "/abs/or/rel", "entry": "pkg" }`
  - Entries list: `{ "path": "/abs/or/rel", "entries": ["pkg.module.ClassA", "pkg.module.ClassB"] }`
  - Local path plugin directories must be `pip` installable (`pyproject.toml` or `setup.py`).
  - Descriptor-driven module-only specs require `agent_plugin.json` (see Descriptor) and load exactly its `entries`.
  - Explicit module-only specs fall back to auto-discovery when no descriptor is present.

- Git installer (single class)
  - String: `"git+<url-or-local>[#<ref>]::pkg.module.Class"`
  - Object: `{ "git": "<url-or-local>", "ref": "tag-or-commit", "entry": "pkg.module.Class" }`

- Git installer (module-only or multiple classes)
  - Descriptor-driven module-only (recommended): `"git+<url-or-local>[#<ref>]"` or `{ "git": "<url-or-local>", "ref": "optional-tag-or-commit" }`
  - Explicit module-only (legacy): `{ "git": "<url-or-local>", "entry": "pkg" }` or `"git+<url-or-local>[#<ref>]::pkg"`
  - Entries list: `{ "git": "<url-or-local>", "entries": ["pkg.module.ClassA", "pkg.module.ClassB"] }`

Both local path and git object specs accept an optional `subdirectory` field
that selects a subfolder within the repo to install (useful for monorepos).

### Descriptor (agent_plugin.json)

When a module-only spec is used, the loader looks for an optional descriptor in
the install directory as `agent_plugin.json`.

This means the plugin's packaging should install `agent_plugin.json` as a
top-level data file (for example, via setuptools `data_files`).

```
{
  "entries": ["dev_plugins.file_reader_tool.FileReaderTool", "dev_plugins.file_writer_tool.FileWriterTool"],
  "kinds": { "dev_plugins.file_reader_tool.FileReaderTool": "tools" }
}
```

Optional fields:
- `subdirectory`: default install subdirectory for the repo (used when the config spec does not provide `subdirectory`).

If `entries` is present, only those classes are loaded (no extra discovery). Optional `kinds` overrides are applied per entry.

## Config Forms

- Mapping-by-kind (per-kind arrays):
```
{
  "plugins": {
    "providers": ["plugins.openai_provider.OpenAICompatibleProvider"],
    "extensions": ["plugins.openai_tools_extension.OpenAIToolsExtension"],
    "tools": [
      "path:${env:DEV_PLUGINS_DIR}::dev_plugins.file_reader_tool.FileReaderTool",
      { "path": "${env:DEV_PLUGINS_DIR}", "entries": [
        "dev_plugins.file_reader_tool.FileReaderTool",
        "dev_plugins.file_writer_tool.FileWriterTool"
      ]}
    ],
    "application": ["my_app.plugins.CustomAppPlugin"]
  }
}
```

- Flat list (auto-kind):
```
{
  "plugins": [
    "plugins.openai_provider.OpenAICompatibleProvider",
    "plugins.openai_tools_extension.OpenAIToolsExtension",
    "path:${env:DEV_PLUGINS_DIR}::dev_plugins.file_reader_tool.FileReaderTool",
    "path:${env:DEV_PLUGINS_DESC_DIR}",
    "git+https://github.com/acme/dev-plugins.git#v1.0.0"
  ]
}
```

- Canonical items (with optional kind):
```
{
  "plugins": [
    { "spec": "plugins.openai_provider.OpenAICompatibleProvider", "kind": "providers" },
    { "spec": { "git": "/local/repo", "entries": [
      "dev_plugins.file_reader_tool.FileReaderTool",
      "dev_plugins.file_writer_tool.FileWriterTool"
    ]}}
  ]
}
```

## Placeholders

- `${env:VAR}` is supported anywhere within strings. Missing env vars are logged as `env_missing` and replaced with an empty string.
- `${file:...}` is supported as a whole-string placeholder only.

## Policy & Security

- `plugin_cache_dir`: enables installs and caching.
- `plugin_policy`:
  - `allow_remote` (default false): allow `https/ssh` and similar remote Git URLs.
  - `allowed_git_hosts`: optional allowlist of hosts for remote Git (enforced when `allow_remote` is true).
  - `pip_args`: extra pip args for Git and local installs.
  - `install_deps` (default false): when false, installs run with `--no-deps`.
  - `sys_path_precedence`: core-first (append) by default.

Security guidance:
- Git installs run arbitrary code via pip; prefer pinned refs (tags/commits), and use `allowed_git_hosts` where possible.

Local path installs are also executed via `pip install` (against local source
trees), so treat them as code execution in the current environment.

## Troubleshooting

- Errors are logged during normalization and loading (e.g., `plugin_manager_load_errors`).
- You can also access them programmatically:
```
app = AgentApplication("config.json", "./sessions")
for err in app.get_config_errors():
    print(err.get("type"), err.get("detail"))
```

## See Also
- docs/plugins/development.md — authoring, packaging, and wiring guidelines
