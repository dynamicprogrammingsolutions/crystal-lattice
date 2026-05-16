# Bash tool plugins

Bash tool plugins are out-of-process `ToolPlugin` implementations backed by a
single `bash` script. They are a good fit for small shell-native tools, command
wrappers, and simple file/text utilities that are easiest to express as shell
scripts.

This page is the canonical authoring guide for `bash_tool` plugins.

Runtime references (source of truth):

- Loader / plugin source: `core/python/agent_app/plugin_sources/bash_tool.py`
- Python proxy plugin: `core/python/agent_core/tool_hosts/bash_tool_plugin.py`
- Config + file contract: `docs/plugins/application-config.md`

Reference implementations:

- Template: `plugins/template-bash-tool`
- Minimal real example: `plugins/bash-read-line-range`

See also:

- [Tool plugins](tool-plugins.md)
- [Packaging & loading plugins](plugin-packaging-and-loading.md)
- [Testing & validation](testing-and-validation.md)

---

## What Bash tools are for

Use a Bash tool when:

- the tool is naturally a shell script
- you want a very small dependency footprint
- the tool mainly wraps existing CLI utilities
- the logic is straightforward enough to express through shell subcommands

Prefer an in-process Python tool when:

- you need richer data structures or complex validation
- you need the payload-first/custom-freeform Python tool API
- you want easier portability or deeper unit testing

Important current limitations:

- one bash tool file maps to one tool
- the schema contract is currently centered on classic function-style schemas
- the bash host does not expose the newer Python payload-first/custom-freeform contract directly

---

## Development workflow

Recommended workflow:

1. start from `plugins/template-bash-tool`
2. implement `schema`, `preview`, and `run`
3. test the script directly from the shell
4. test it through the Python plugin manager
5. load it in a real app config with `allow_bash_tools: true`

### Step 0: package layout

Minimal repo layout:

```text
my-bash-tool/
  agent_plugin.json
  my_tool.bash
  pyproject.toml
  tests/
    test_my_tool.py
```

Example `agent_plugin.json`:

```json
{
  "bash_tools": [
    { "file": "my_tool.bash" }
  ]
}
```

For single-file tools, you can also skip the repo descriptor and load the file
directly via a `bash_tool.file` config spec.

### Step 1: write the bash tool file

Each bash tool file is invoked as:

```bash
bash /abs/path/to/tool.bash <subcommand> [args...]
```

Supported subcommands:

- `schema`
- `preview`
- `run`
- `error` (optional)

Runtime environment variables injected by the host include:

- `AGENT_TOOL_PYTHON`
  - absolute path to the exact Python interpreter running the bash tool host
  - useful for bash tools that need to invoke helper Python scripts without
    rediscovering `python3` through `PATH`
- `AGENT_TOOL_TIMED_OUT`
  - set to `1` when the host invokes the optional `error` subcommand after a timeout
- `AGENT_TOOL_TIMEOUT_SECONDS`
  - timeout value associated with a timed-out invocation

Minimal working example:

```bash
#!/usr/bin/env bash
set -euo pipefail

subcommand="${1:-}"
shift || true

case "$subcommand" in
  schema)
    cat <<'JSON'
{
  "id": "template_bash_echo",
  "version": "0.1.0",
  "args_mode": "positional",
  "positional": [
    {"name": "value", "required": true},
    {"name": "uppercase", "default": false}
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "template_bash_echo",
        "description": "Echo a value (optionally uppercase it).",
        "parameters": {
          "type": "object",
          "properties": {
            "value": {"type": "string"},
            "uppercase": {"type": "boolean", "default": false}
          },
          "required": ["value", "uppercase"]
        }
      }
    }
  ]
}
JSON
    ;;

  preview)
    value="${1:-}"
    uppercase="${2:-false}"
    echo "template_bash_echo value=$(printf %q "$value") uppercase=$uppercase"
    ;;

  run)
    value="${1:-}"
    uppercase="${2:-false}"
    if [[ "$uppercase" == "true" ]]; then
      printf '%s' "$value" | tr '[:lower:]' '[:upper:]'
    else
      printf '%s' "$value"
    fi
    ;;

  error)
    exit_code="${1:-1}"
    echo "Error: template_bash_echo failed (exit_code=$exit_code)"
    exit 0
    ;;

  *)
    echo "Usage: $0 {schema|preview|run|error}" >&2
    exit 2
    ;;
esac
```

This mirrors `plugins/template-bash-tool/template_bash_echo.bash`.

### Step 2: load it in config

Single-file form:

```json
{
  "plugins": [
    { "bash_tool": { "file": "./tools/my_tool.bash" } }
  ],
  "plugin_policy": {
    "allow_bash_tools": true
  }
}
```

Directory form:

```json
{
  "plugins": [
    { "bash_tool": { "path": "./plugins/my-bash-tool" } }
  ],
  "plugin_policy": {
    "allow_bash_tools": true
  }
}
```

Git form:

```json
{
  "plugins": [
    {
      "bash_tool": {
        "git": "https://github.com/acme/my-bash-tool.git",
        "ref": "v0.1.0"
      }
    }
  ],
  "plugin_policy": {
    "allow_bash_tools": true
  }
}
```

String shortcuts:

```json
{
  "plugins": [
    "bash:./plugins/my-bash-tool",
    "bash+git:https://github.com/acme/my-bash-tool.git#v0.1.0"
  ],
  "plugin_policy": {
    "allow_bash_tools": true
  }
}
```

---

## Bash tool file contract

### `schema`

`schema` must print a JSON object to stdout.

Required fields:

```json
{
  "id": "my_tool",
  "version": "0.1.0",
  "args_mode": "flags",
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "my_tool",
        "parameters": {
          "type": "object",
          "properties": {}
        }
      }
    }
  ]
}
```

Current v1 constraints:

- exactly one tool schema per bash file
- `schema.id` must match `tools[0].function.name`

Optional fields:

- `config_keys`
  - list of config keys that the host should expose to the bash subprocess
  - each key is passed as an environment variable named:
    - `AGENT_TOOL_CONFIG_<UPPER_SNAKE_CASE_KEY>`
  - only scalar config values are passed through; lists/dicts are ignored

Example:

```json
{
  "id": "send_to_kindle",
  "version": "0.1.0",
  "args_mode": "json",
  "config_keys": [
    "send_to_kindle_smtp_user",
    "send_to_kindle_default_to"
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "send_to_kindle",
        "parameters": {"type": "object", "properties": {}}
      }
    }
  ]
}
```

### `preview`

`preview` should print a short single-line preview to stdout and exit 0.

Example:

```bash
preview)
  path="${1:-}"
  echo "read_line_range path=$(printf %q "$path")"
  ;;
```

If `preview` exits non-zero, the host falls back to an empty preview string.

### `run`

`run` is the actual tool execution path. Stdout becomes streamed output and
contributes to the final tool message.

Example:

```bash
run)
  path="${1:-}"
  start="${2:-1}"
  end="${3:-1}"
  sed -n "${start},${end}p" "$path"
  ;;
```

### `error` (optional)

When `run` fails or times out, the host may invoke:

```bash
bash tool.bash error <exit_code> [args...]
```

If `error` exits 0 and prints non-empty stdout, that text becomes the final
tool message content. Otherwise the host falls back to default formatting.

On timeout, the host sets:

- `AGENT_TOOL_TIMED_OUT=1`
- `AGENT_TOOL_TIMEOUT_SECONDS=<n>`

In normal `schema` / `preview` / `run` / `error` invocations, the host also sets:

- `AGENT_TOOL_PYTHON=<sys.executable>`

This lets bash tools reliably reuse the same Python environment as the host.
Recommended pattern:

```bash
PYTHON_BIN="${AGENT_TOOL_PYTHON:-$(command -v python3)}"
"${PYTHON_BIN}" ./helper.py
```

---

## Argument passing

The contract is selected by `args_mode`.

### `flags`

Arguments are converted to CLI flags.

Rules:

- scalar: `--name <value>`
- boolean `true`: `--name`
- boolean `false`: `--no-name`

Example schema fragment:

```json
{
  "args_mode": "flags"
}
```

### `positional`

Arguments are mapped to ordered argv values using `schema.positional`.

Example:

```json
{
  "args_mode": "positional",
  "positional": [
    { "name": "path", "required": true },
    { "name": "start_line", "required": true },
    { "name": "end_line", "required": true },
    { "name": "show_line_numbers", "default": false }
  ]
}
```

This is the mode used by `plugins/bash-read-line-range`.

### `json`

For `json` mode, the host calls:

- `run --args-json`
- `preview --args-json`
- `error <code> --args-json`

The JSON arguments object is written to stdin.

This is useful when:

- arguments are awkward to represent as flags/positionals
- you want to parse them with `jq`

Example pattern:

```bash
run)
  if [[ "${1:-}" == "--args-json" ]]; then
    args_json="$(cat)"
    value="$(printf '%s' "$args_json" | jq -r '.value')"
    printf '%s' "$value"
    exit 0
  fi
  ;;
```

---

## Runtime behavior

### Working directory

The host uses `config["working_directory"]` when present to set the subprocess
cwd. If it is absent, the default shell/process cwd is used.

### Selected config propagation

When a bash tool schema declares `config_keys`, the host reads those keys from
the resolved request config (`state["config"]`) and exposes them as
environment variables:

- config key: `send_to_kindle_smtp_user`
- subprocess env: `AGENT_TOOL_CONFIG_SEND_TO_KINDLE_SMTP_USER`

This is the recommended way for bash tools to consume agent/provider/mixin
defaults that may themselves come from `${env:...}` placeholders in config.

Recommended pattern:

```bash
SMTP_USER="${AGENT_TOOL_CONFIG_SEND_TO_KINDLE_SMTP_USER:-}"
```

### Python interpreter propagation

The host exports:

- `AGENT_TOOL_PYTHON`

with the value of the host process's `sys.executable`.

This is the preferred interpreter for bash tools that call Python helpers
because it preserves:

- the same virtual environment or packaged runtime as the host
- the same installed dependencies
- the same certificate store / interpreter-specific runtime behavior

Prefer this over rediscovering `python3` via shell `PATH` when possible.

### Streaming

Tool stdout is streamed as partial output.

When enabled by policy, stderr may also be streamed.

The final tool message is emitted after the process exits and formatting is
applied.

### Timeouts

The host uses:

- `plugin_policy.bash_timeout_seconds` when provided at load time
- otherwise the default timeout in `BashToolPlugin`

If the process times out, it is reported as a failure and the optional `error`
subcommand may still be used to format the final tool message.

### Tool name handling

The current bash host assumes one tool per file and enforces that the tool name
matches the schema/file identity. This is why `schema.id` and
`tools[0].function.name` must match.

---

## Testing Bash tools

Recommended layers:

1. direct shell testing of `schema`, `preview`, `run`, and `error`
2. Python plugin-manager tests
3. full app config tests with `allow_bash_tools: true`

### Direct shell checks

These are the fastest loop when developing:

```bash
bash ./my_tool.bash schema
bash ./my_tool.bash preview hello true
bash ./my_tool.bash run hello true
bash ./my_tool.bash error 1
```

### Python-side tests

Useful pattern:

```bash
pytest plugins/template-bash-tool/tests -q
pytest plugins/bash-read-line-range/tests -q
```

Good things to verify:

- schema JSON is valid
- `id` matches the function name
- argument passing works for the chosen `args_mode`
- timeout/failure formatting is reasonable
- directory and single-file loading both work
- helper scripts use `AGENT_TOOL_PYTHON` correctly when Python is involved
- declared `config_keys` arrive as expected in subprocess env

---

## Common pitfalls

- Forgetting to enable `plugin_policy.allow_bash_tools`
- Loading a bash tool repo with `path:...` instead of `bash:...` or `{"bash_tool": ...}`
- Printing invalid JSON from `schema`
- Mismatching `schema.id` and `tools[0].function.name`
- Returning multiple tools from one file
- Relying on shell features or external commands not present in target environments
- Forgetting to quote shell arguments safely
- Assuming the bash host supports the in-process Python payload-first/freeform API

---

## Reference examples

- `plugins/template-bash-tool`
- `plugins/bash-read-line-range`
- `docs/plugins/application-config.md`