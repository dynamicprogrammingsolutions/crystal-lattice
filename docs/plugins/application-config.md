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

- Bash tool plugins (single-file or manifest-driven)
  - Single file: `{ "bash_tool": { "file": "./tools/my_tool.bash" } }`
  - Local directory: `{ "bash_tool": { "path": "./plugins/bash-tools" } }` (requires `agent_plugin.json` with `bash_tools`)
  - Git repo: `{ "bash_tool": { "git": "https://github.com/acme/bash-tools.git", "ref": "v0.1.0", "subdirectory": "optional/subdir" } }` (requires `agent_plugin.json` with `bash_tools`)

String shortcuts:
- Local directory or single file: `"node:/abs/or/rel"`
- Git repo: `"node+git:<url-or-local>[#<ref>]"`

Bash string shortcuts:
- Local directory or single file: `"bash:/abs/or/rel"`
- Git repo: `"bash+git:<url-or-local>[#<ref>]"`

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

### Descriptor (bash tool repos via agent_plugin.json)

For `bash_tool` directory/git specs, the loader reads `agent_plugin.json` and requires a `bash_tools` list.

Example:

```
{
  "bash_tools": [
    {"file": "read_line_range.bash"},
    {"file": "tools/grep_context.bash"}
  ]
}
```

The `kinds` field is intentionally omitted for bash tool repos (bash repos are always tools).

## Bash Tool File Contract

Each bash tool file is executed as:

```
bash /abs/path/to/tool.bash <subcommand> [args...]
```

Subcommands:
- `schema`: prints JSON schema to stdout.
- `preview`: prints a single-line preview string.
- `run`: executes the tool and writes output to stdout (streamed).
- `error` (optional): formats the final tool message text on failure.

### Schema JSON

`schema` must return a JSON object containing at least:

```
{
  "id": "my_tool",
  "version": "0.1.0",
  "args_mode": "flags",
  "tools": [ ... OpenAI tool schemas ... ]
}
```

v1 constraints:
- Exactly one tool schema per file.
- `schema.id` must match `tools[0].function.name`.

### Argument Passing (`args_mode`)

- `flags`:
  - Scalars: `--name <value>`
  - Booleans: `true` → `--name`, `false` → `--no-name`
- `positional`:
  - `schema.positional` defines the ordered argv mapping:
    - Each entry is `{ "name": "...", "required": true|false, "default": <scalar> }`.
    - Values are passed in order as plain argv strings.
    - Trailing non-provided arguments with defaults may be omitted.
- `json`:
  - Python calls: `run --args-json` (and `preview --args-json` / `error <code> --args-json`).
  - The JSON `arguments` object is written to stdin.
  - Tools are expected to parse it with `jq`.

### Error Formatting Hook (`error`)

When `run` fails (non-zero exit code) or times out, the host may call:

```
bash tool.bash error <exit_code> [args...]
```

If `error` exits 0 and prints non-empty stdout, that text is used as the final
tool message `content` (what the LLM sees). Otherwise, the host falls back to a
default formatting including exit code + stderr/stdout.

On timeout, the host sets:
- `AGENT_TOOL_TIMED_OUT=1`
- `AGENT_TOOL_TIMEOUT_SECONDS=<n>`

### Streaming

Tool stdout is streamed as tool partial events. When enabled by policy,
stderr is also streamed. The final tool message is sent after the process
exits.

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
- `node_install_deps` (default true): run a package manager install step in cached copies.
- `node_build` (default true): run a build step in cached copies (uses `package.json#scripts.build` when present).
- `node_package_manager`:
  - If set: force `npm`, `pnpm`, or `yarn` for all Node tool plugins.
  - If omitted: inferred from `package.json#packageManager` (preferred) or lockfiles (`pnpm-lock.yaml`, `yarn.lock`), falling back to `npm`.
- `node_allow_install_scripts` (default true): allow install-time scripts.
- `node_build_command`: optional global override for the build command (otherwise uses `<pm> run build`).

Bash tool policy keys:
- `allow_bash_tools` (default false): enable `bash_tool` plugin loading.
- `bash_timeout_seconds` (default 60): timeout for `schema`/`preview`/`run`.
- `bash_error_timeout_seconds` (default 5): timeout for the optional `error` hook.
- `bash_stream_stderr` (default false): stream stderr as tool partials.

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
