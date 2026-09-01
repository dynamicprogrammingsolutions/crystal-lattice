# Plugin configuration

This guide covers plugin package specs, loading layers, enablement, install
policy, and external tool-host packages.

## Loading layers

`plugins` has different meanings by location:

- top level: package specs loaded for every agent;
- provider config: package specs added for agents using that provider;
- agent config: package specs added only for that agent;
- session metadata: explicit enabled plugin IDs, not package specs.

Provider-level and agent-level packages are additive.

`disabled_plugins` is available at top-level, provider, and agent scope and is
always a list of plugin IDs.

## Effective catalog order

1. Load top-level package specs.
2. Load selected-provider package specs.
3. Load selected-agent package specs.
4. Deduplicate by plugin ID with first registration winning.
5. Remove plugins whose class has `default_enabled = False`.
6. Re-enable IDs listed in `enabled_plugins`.
7. Remove IDs listed in merged `disabled_plugins`.
8. If session metadata contains `plugins`, use that explicit enabled-ID list.

For duplicate plugin IDs:

- global beats provider;
- provider beats agent.

## Runtime enablement

During request processing:

1. Providers and enabled plugins contribute tags.
2. `is_enabled(config, tags, models, context)` may explicitly enable or
   disable a plugin.
3. Otherwise `required_tags()` and `forbidden_tags()` apply.
4. `force_enabled_plugins` bypasses normal tag checks.

## Package spec formats

Supported forms include:

- dotted class: `"pkg.module.Class"`;
- local descriptor package: `"path:/abs/or/relative"`;
- Git descriptor package: `"git+<url-or-local>[#<ref>]"`;
- verbose local mapping:

  ```json
  {
    "path": "/abs/or/relative",
    "subdirectory": "optional/subdir",
    "entry": "pkg.module.Class"
  }
  ```

- verbose Git mapping:

  ```json
  {
    "git": "<url-or-local>",
    "ref": "tag-or-commit",
    "subdirectory": "optional/subdir",
    "entry": "pkg.module.Class"
  }
  ```

- Node tool packages through `node_tool`;
- Bash tool packages through `bash_tool`.

Examples:

```json
{
  "plugins": [
    "pkg.module.Provider",
    "path:${env:BUILTIN_PLUGINS}/openrouter",
    "git+https://github.com/acme/dev-plugins.git#v1.0.0",
    {
      "path": "./plugins/local-provider",
      "entry": "local_provider.Provider"
    },
    {
      "node_tool": {
        "path": "./tools/javascript"
      }
    },
    {
      "bash_tool": {
        "file": "./tools/read_file.bash"
      }
    }
  ]
}
```

String shortcuts:

- `node:/path`
- `node+git:<url-or-local>[#<ref>]`
- `bash:/path`
- `bash+git:<url-or-local>[#<ref>]`

## Python package descriptors

Local and Git plugin repositories use `agent_plugin.json`:

```json
{
  "entries": [
    "dev_plugins.file_reader_tool.FileReaderTool",
    "dev_plugins.file_writer_tool.FileWriterTool"
  ]
}
```

`subdirectory` may define a default package subdirectory.

## Node tool descriptors

Node directories use `package.json#agent.tools`:

```json
{
  "name": "@acme/my-js-tools",
  "version": "0.1.0",
  "type": "module",
  "agent": {
    "kinds": ["tools"],
    "tools": [
      {"id": "echo", "entry": "dist/index.js"},
      {"id": "reverse", "entry": "dist/index.js", "export": "reverseTool"}
    ]
  }
}
```

When `export` is present, the host selects that module export. Otherwise it
uses the default export.

## Bash tool descriptors and commands

Bash tool repositories declare:

```json
{
  "bash_tools": [
    {"file": "read_line_range.bash"},
    {"file": "tools/grep_context.bash"}
  ]
}
```

Each Bash tool supports:

```text
bash tool.bash schema
bash tool.bash preview [arguments]
bash tool.bash run [arguments]
bash tool.bash error <exit-code> [arguments]
```

`schema` returns an object containing an ID, version, argument mode, and one
OpenAI-style tool schema. Supported argument modes are:

- `flags`: scalar values become `--name <value>`; booleans become `--name` or
  `--no-name`;
- `positional`: `schema.positional` declares ordered names, required flags, and
  optional scalar defaults;
- `json`: the host invokes `run --args-json` and writes the JSON arguments
  object to stdin.

The schema contains:

```json
{
  "id": "my_tool",
  "version": "0.1.0",
  "args_mode": "flags",
  "tools": [],
  "config_keys": ["my_setting"]
}
```

The initial Bash tool contract supports exactly one tool schema per file, and
`schema.id` must match the tool function name.

Optional `config_keys` are read from effective request config and exported as
`AGENT_TOOL_CONFIG_<UPPERCASE_KEY>`.

The host also sets:

- `AGENT_TOOL_PYTHON`;
- `AGENT_TOOL_TIMED_OUT=1` after a timeout;
- `AGENT_TOOL_TIMEOUT_SECONDS`.

Tool stdout streams as partial tool events. Policy can also enable stderr
streaming.

When `run` fails or times out, the host may invoke:

```text
bash tool.bash error <exit-code> [arguments]
```

Successful non-empty output from `error` becomes the final tool message.
Otherwise the host falls back to a bounded exit-code and stderr/stdout
summary.

## Global, provider, and agent example

```json
{
  "plugin_cache_dir": "${env:CONFIG_DIR}/.plugin_cache/plugins",
  "plugins": [
    "path:${env:BUILTIN_PLUGINS}/openrouter",
    "path:${env:BUILTIN_PLUGINS}/feature-request-options"
  ],
  "disabled_plugins": ["openrouter_usage"],
  "providers": {
    "openrouter_codex": {
      "provider": "openrouter",
      "model": "openai/gpt-5-mini",
      "api_key": "${env:OPENROUTER_API_KEY}",
      "plugins": [
        "path:${env:BUILTIN_PLUGINS}/codex-tools"
      ],
      "disabled_plugins": ["apply_patch"]
    },
    "openrouter_gemini": {
      "provider": "openrouter",
      "model": "google/gemini-2.5-flash-lite",
      "api_key": "${env:OPENROUTER_API_KEY}",
      "plugins": [
        "path:${env:BUILTIN_PLUGINS}/gemini-tools"
      ]
    }
  },
  "agents": {
    "codex-agent": {
      "provider": "openrouter_codex"
    },
    "gemini-agent": {
      "provider": "openrouter_gemini",
      "plugins": [
        "path:${env:BUILTIN_PLUGINS}/session-title-app"
      ],
      "disabled_plugins": ["session_title_app"]
    }
  }
}
```

Every agent receives the global packages. Provider and agent packages are then
added, and all applicable `disabled_plugins` values contribute to the default
enabled set.

## Install and security policy

`plugin_cache_dir` enables installation and caching.

Python policy keys include:

- `allow_remote` (default `false`): allow remote Git URLs;
- `allowed_git_hosts`: optional allowlist used when remote Git is enabled;
- `pip_args`: additional pip arguments;
- `pip_cache_dir`: pip download/build cache, normally beside the plugin install
  cache;
- `install_deps` (default `false`): omit `--no-deps` when enabled.

Node policy keys include:

- `node_timeout_seconds` (default `60`);
- `node_install_deps` (default `true`);
- `node_build` (default `true`);
- `node_package_manager`: force `npm`, `pnpm`, or `yarn`; when omitted, infer
  from `packageManager` or lockfiles and fall back to npm;
- `node_allow_install_scripts` (default `true`);
- `node_build_command`: override the normal package-manager build command.

Bash policy keys include:

- `allow_bash_tools` (default `false`);
- `bash_timeout_seconds` (default `60`);
- `bash_error_timeout_seconds` (default `5`);
- `bash_stream_stderr` (default `false`).

Git and local path installation can execute package build/install code. Prefer
pinned refs and trusted sources, and use host allowlists for remote Git.

## Troubleshooting

Plugin loading and installation failures are available through
`AgentApplication.get_config_errors()`. Common types include invalid package
specs, installation-policy rejection, missing descriptors, and import errors.

## Migration from enabled-ID agent lists

Agent/provider/top-level `plugins` now means package specs. Older agent configs
that used `plugins` as enabled IDs must use:

- package specs in `plugins`;
- default opt-outs in `disabled_plugins`;
- explicit per-session enabled IDs in session metadata `plugins`.

## See also

- [Plugin system overview](../../../plugins/docs/overview.md)
- [Packaging and loading plugins](../../../plugins/docs/plugin-packaging-and-loading.md)
- [Tool host protocol](/reference/tool-host-protocol/)