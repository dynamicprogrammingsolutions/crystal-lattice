# Application Plugin Configuration

This page explains how to configure plugins in the application. It covers the `plugins` block, spec formats (dotted, local path, Git), placeholders, policy, and ready-to-use examples.

## Overview

- `plugins`: defines provider(s), extensions, features, tools, and application plugins.
- `plugin_cache_dir`: enables plugin installs and caching (for both `git+...` and `path:...`).
- `plugin_policy`: controls installation and security policy (see Policy & Security).

## Spec Formats

Each plugin reference is a “spec” that can take one of the following forms:

- Dotted class (no installation)
  - `"pkg.module.Class"`

- Local plugin repo (descriptor-driven; recommended)
  - `"path:/abs/or/rel"`

  The repo is installed into `plugin_cache_dir` via `pip install --target ...`, then
  plugin classes are loaded from `agent_plugin.json`.

- Git plugin repo (descriptor-driven; recommended)
  - `"git+<url-or-local>[#<ref>]"`

- Verbose object spec (explicit single-class target)
  - Local: `{ "path": "/abs/or/rel", "subdirectory": "optional/subdir", "entry": "pkg.module.Class" }`
  - Git: `{ "git": "<url-or-local>", "ref": "tag-or-commit", "subdirectory": "optional/subdir", "entry": "pkg.module.Class" }`

- JavaScript/TypeScript tool plugins (Node.js)
  - Local directory: `{ "node_tool": { "path": "./path/to/js-tool" } }`
  - Git repo: `{ "node_tool": { "git": "https://github.com/acme/my-js-tool.git", "ref": "v0.1.0" } }`
  - Single file: `{ "node_tool": { "file": "./my_tool.js", "id": "my_tool", "entry": "my_tool.js" } }`

For repos, `subdirectory` selects a subfolder within the repo to install (useful for monorepos).

### Descriptor (agent_plugin.json)

For repo specs (`path:...` or `git+...`), the loader reads `agent_plugin.json`.
The plugin's packaging should install it as a top-level data file.

```
{
  "entries": ["dev_plugins.file_reader_tool.FileReaderTool", "dev_plugins.file_writer_tool.FileWriterTool"],
}
```

Optional fields:
- `subdirectory`: default install subdirectory (used when the config spec does not provide `subdirectory`).

Other fields may exist for authoring convenience; the loader only requires `entries`.

### Descriptor (Node.js tools via package.json)

For `node_tool` directory specs, the loader reads `package.json#agent.tools`.

Example:

```
{
  "name": "@acme/my-js-tools",
  "version": "0.1.0",
  "type": "module",
  "agent": {
    "kinds": ["tools"],
    "tools": [
      { "id": "echo", "entry": "dist/index.js" },
      { "id": "reverse", "entry": "dist/index.js", "export": "reverseTool" }
    ]
  }
}
```

When `export` is present, the Node tool host selects `module[export]`; otherwise it uses the default export.

## Config Forms

- Flat list (auto-kind via duck-typing):
```
{
  "plugins": [
    "plugins.openai_provider.OpenAICompatibleProvider",
    "plugins.openai_tools_extension.OpenAIToolsExtension",
    { "path": "${env:DEV_PLUGINS_DIR}", "entry": "dev_plugins.file_reader_tool.FileReaderTool" },
    "path:${env:DEV_PLUGINS_DESC_DIR}",
    "git+https://github.com/acme/dev-plugins.git#v1.0.0"
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

Node.js tool policy keys:
- `node_timeout_seconds` (default 60): timeout per tool RPC.
- `node_install_deps` (default false): run dependency install in cached copies.
- `node_build` (default false): run a build command in cached copies.
- `node_package_manager` (default `npm`): `npm`, `pnpm`, or `yarn`.
- `node_allow_install_scripts` (default false): allow install-time scripts.
- `node_build_command` (default `npm run build`): override build command.

Security guidance:
- Git installs run arbitrary code via pip; prefer pinned refs (tags/commits), and use `allowed_git_hosts` where possible.

Local path installs are also executed via `pip install` (against local source
trees), so treat them as code execution in the current environment.

## Troubleshooting

- Errors are logged during resolution (e.g., `plugin_manager_resolve_errors`).
- You can also access them programmatically:
```
app = AgentApplication("config.json", "./sessions")
for err in app.get_config_errors():
    print(err.get("type"), err.get("detail"))
```

## See Also
- docs/plugins/development.md — authoring, packaging, and wiring guidelines
- docs/reference/tool-host-protocol.md — the NDJSON tool host protocol
