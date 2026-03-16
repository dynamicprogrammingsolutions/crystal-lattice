# Application Plugin Configuration

This page explains how to configure plugins in the application. It covers the `plugins` block, spec formats (dotted, local path, Git), placeholders, policy, and ready-to-use examples.

## Overview

- top-level `plugins`: global plugin package specs shared by all agents.
- provider-level `plugins`: additional plugin package specs for agents using that provider config.
- agent-level `plugins`: additional plugin package specs for that agent only.
- session metadata `plugins`: still means explicit enabled plugin ids, not plugin package specs.
- `disabled_plugins`: config-level shorthand for disabling plugin ids by default after the merged catalog is built.
- `plugin_cache_dir`: enables plugin installs and caching (for both `git+...` and `path:...`).
- `plugin_policy`: controls installation and security policy (see Policy & Security).

## Built-in Placeholder Environment Variables

When the application resolves placeholders, it now provides a few path-oriented
environment variables automatically. These can still be overridden explicitly
by the embedding app through `AgentApplication(..., env_overrides=...)`.

- `CONFIG_DIR`: absolute path to the directory containing the active config file
- `WORKING_DIR`: absolute path to the current working directory
- `BUILTIN_PLUGINS`: default built-in plugin bundle directory for the current install layout

These are especially useful for portable configs:

```json
{
  "plugin_cache_dir": "${env:CONFIG_DIR}/.plugin_cache/plugins",
  "plugins": [
    "path:${env:BUILTIN_PLUGINS}/openrouter",
    "path:${env:BUILTIN_PLUGINS}/feature-system-message"
  ],
  "agents": {
    "default": {
      "provider": "openrouter_tools",
      "system_message": {
        "template": "{{AGENTS}}",
        "variables": {
          "AGENTS": {
            "text": "${file:${env:WORKING_DIR}/AGENTS.md}"
          }
        }
      }
    }
  }
}
```

## Configuration Layers

`plugins` intentionally has different semantics depending on where it appears:

- top level: plugin package specs loaded for every agent
- provider config: plugin package specs added for agents that use that provider
- agent config: plugin package specs added only for that agent
- session metadata: explicit enabled plugin ids controlled by the existing session UI/API flow

`disabled_plugins` is available at the top level, provider level, and agent level. It is always a list of plugin ids, never plugin package specs.

### Merge Order

The effective plugin catalog for a session is built in this order:

1. Load top-level `plugins`.
2. Load `plugins` from the selected provider config.
3. Load `plugins` from the selected agent config.
4. Deduplicate by plugin id with first registration winning.
5. Compute the default enabled set by taking the merged catalog and removing ids listed in merged `disabled_plugins`.
6. If session metadata contains `plugins`, use that explicit enabled-id list instead of the config-derived default.

This means provider-level and agent-level packages are additive. They do not replace the global packages.

### Duplicate Plugin Ids

When multiple config layers contribute plugin classes with the same plugin id, the first registration wins.

- global package beats provider package for the same plugin id
- provider package beats agent package for the same plugin id

This is especially important for tool families that reuse names such as `read_file` or `glob`.

## Example: Global + Provider + Agent

```json
{
  "plugin_cache_dir": "${env:PLUGIN_CACHE_DIR}",
  "providers": {
    "openrouter_codex": {
      "provider": "openrouter",
      "model": "openai/gpt-5-mini",
      "api_key": "${env:OPENROUTER_API_KEY}",
      "plugins": [
        "path:${env:REPO_ROOT}/plugins/codex-tools"
      ],
      "disabled_plugins": ["apply_patch"]
    },
    "openrouter_gemini": {
      "provider": "openrouter",
      "model": "google/gemini-2.5-flash-lite",
      "api_key": "${env:OPENROUTER_API_KEY}",
      "plugins": [
        "path:${env:REPO_ROOT}/plugins/gemini-tools"
      ]
    }
  },
  "plugins": [
    "path:${env:REPO_ROOT}/plugins/openrouter",
    "path:${env:REPO_ROOT}/plugins/feature-request-options"
  ],
  "disabled_plugins": ["openrouter_usage"],
  "agents": {
    "codex-agent": {
      "provider": "openrouter_codex"
    },
    "gemini-agent": {
      "provider": "openrouter_gemini",
      "plugins": [
        "path:${env:REPO_ROOT}/plugins/session-title-app"
      ],
      "disabled_plugins": ["session_title_app"]
    }
  }
}
```

In that example:

- every agent gets the global OpenRouter provider package
- `codex-agent` also gets `codex-tools` from its provider config
- `gemini-agent` also gets `gemini-tools` from its provider config
- `gemini-agent` adds one more package from its agent config
- the default enabled set is the merged catalog minus top-level, provider-level, and agent-level `disabled_plugins`
- if a session later stores `metadata.plugins`, that explicit enabled-id list overrides the config-derived default

## Migration Note

Older configs could use agent-level `plugins` as a list of enabled plugin ids. That meaning is no longer supported.

Use:

- agent/provider/top-level `plugins` for plugin package specs
- config-level `disabled_plugins` for default opt-outs
- session metadata `plugins` for explicit per-session enabled plugin ids

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
- plugins/docs/plugin-packaging-and-loading.md — packaging and loader behavior for local/git plugin packages
- plugins/codex-tools/README.md — Codex-style tool package quickstart
- plugins/gemini-tools/README.md — Gemini-style tool package quickstart
- plugins/qwen-tools/README.md — Qwen-style tool package quickstart
- plugins/grok-tools/README.md — Grok-style tool package quickstart
- docs/reference/tool-host-protocol.md — the NDJSON tool host protocol
