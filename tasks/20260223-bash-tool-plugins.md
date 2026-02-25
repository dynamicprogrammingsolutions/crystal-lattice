# Bash Tool Plugins (single-file, self-describing) — implementation plan

## Description

Enable **tool plugins** to be authored as **single `.bash` files** that are:

- **Self-contained** (the file includes its own tool schema, not in comments)
- **Self-describing** (the tool schema is returned by invoking the script)
- **Streaming-friendly** (stdout/stderr are streamed as tool partials)

This design integrates with the existing Python `agent_core` tool orchestration and the application-level plugin loader (`agent_app.plugin_manager.PluginManager`).

---

## What exists today (relevant constraints)

### Tool plugin contract + streaming semantics

- `ToolPlugin` protocol and streaming semantics: `core/python/agent_core/types.py`.
- `AgentCore.iter_tool_messages` forwards dicts with a `"part"` key as partials and expects a final result dict containing a `"success"` key.

Implication: A bash-backed tool must be able to:

- Provide OpenAI tool schemas
- Execute with streaming partial output
- Provide a final `{ "success": ... }` result

### Application-level plugin loading

- `PluginManager` resolves a flat plugin list from config using pluggable `PluginSource`s.

Implication: Bash tools must be supported via a new `PluginSource` that returns a Python tool plugin class.

---

## Goal / non-goals

### Goal

- Load bash tool plugins from app config.
- Each plugin is a **single `.bash` file**.
- The file returns its own schema via a `schema` subcommand (JSON on stdout).
- The file supports `preview` (one-line preview string).
- The file supports `run` (executes the tool while stdout/stderr stream to the UI).

### Non-goals (v1)

- Sandboxing beyond policy gating + timeouts.
- Advanced formatting hooks beyond `preview` (and the optional `error` hook).
- Complex tool state round-tripping.
- Multiple tools defined in one bash file (supported later if needed; v1 is 1 file → 1 tool plugin id).

---

## Proposed design

### 0) Spec formats (Option 1: explicit `bash_tool` only)

This task uses **Option 1**: bash plugins are only loaded via explicit bash specs.

Supported spec formats:

- Single file (object): `{ "bash_tool": { "file": "./plugins/bash-read-line-range/read_line_range.bash" } }`
- Local repo/directory (object): `{ "bash_tool": { "path": "./plugins/bash-tools" } }`
- Git repo (object): `{ "bash_tool": { "git": "https://...", "ref": "vX.Y.Z", "subdirectory": "optional/subdir" } }`

String shortcuts (to match `path:...` and `git+...` while avoiding ambiguity):

- Local file or directory: `"bash:/abs/or/rel"`
  - If the resolved path is a file, it is treated as a single-file plugin.
  - If the resolved path is a directory, it is treated as a repo/directory plugin.
- Git repo: `"bash+git:<url-or-local>[#<ref>]"`

`path:...` and `git+...` specs remain reserved for Python plugin repos in v1.

### 1) Bash tool file contract (CLI interface)

Each bash tool plugin is invoked as:

```bash
bash /abs/path/to/tool.bash <subcommand> [args...]
```

Subcommands (first positional argument):

- `schema`
  - Prints **JSON** to stdout.
  - Exit 0 on success; non-zero on error.
- `preview`
  - Prints a **single line** of plain text to stdout.
  - Exit 0 on success.
- `run`
  - Executes the tool.
  - Writes tool output to stdout (streamed).
  - May write diagnostics to stderr (optionally streamed).
  - Exit code determines success/failure.
- `error` (optional)
  - Called when `run` fails (non-zero exit code) or times out.
  - Invoked as: `bash tool.bash error <exit_code> [args...]`.
  - When it exits 0 and prints non-empty stdout, stdout becomes the final tool message content (what the LLM sees).

Notes:

- The schema must be produced as executable output (e.g. heredoc `cat <<'JSON' ... JSON`).
- The schema must not be encoded in comments.

### 1.1) Directory/git plugin manifest (explicit inclusion)

For plugins loaded from a **local directory** or a **git repo**, require an explicit manifest file (same filename as Python plugin packages) that enumerates which bash files to include.

Manifest filename (v1):

- `agent_plugin.json`

Example `agent_plugin.json` (bash tools):

```json
{
  "bash_tools": [
    {"file": "read_line_range.bash"},
    {"file": "tools/grep_context.bash"}
  ]
}
```

Rules:

- `bash_tools[].file` is a path relative to the manifest directory.
- Each referenced file must implement the `schema` / `preview` / `run` contract described above.
- Tool plugin id is taken from each file's `schema.id`.
- The loader does not automatically include every `*.bash` file; only those listed in the manifest are included.

Notes:

- The manifest filename matches Python plugin repos (`agent_plugin.json`), but the shape differs:
  - Python plugin repos use `entries: ["pkg.module.Class", ...]`.
  - Bash tool repos use `bash_tools: [{"file": "..."}, ...]`.
  - Because bash repos are only loaded via explicit `bash_tool` specs in v1, this shape difference is not ambiguous.

  The `kinds` field is intentionally omitted here. In existing Python manifests,
  `kinds` is an optional mapping (not a list) from entry to kind. For bash tool
  repos the kind is always `tools`, so it would be redundant.

### 2) Schema JSON returned from `schema`

The `schema` subcommand returns a JSON object with at least:

```json
{
  "id": "read_line_range",
  "version": "0.1.0",
  "args_mode": "positional",
  "positional": [
    {"name": "path", "required": true},
    {"name": "start_line", "required": true},
    {"name": "end_line", "required": true},
    {"name": "show_line_numbers", "required": false, "default": false}
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "read_line_range",
        "description": "Read lines [start_line,end_line] from a file (optionally with line numbers).",
        "parameters": {
          "type": "object",
          "properties": {
            "path": {"type": "string"},
            "start_line": {"type": "integer"},
            "end_line": {"type": "integer"},
            "show_line_numbers": {"type": "boolean", "default": false}
          },
          "required": ["path", "start_line", "end_line"]
        }
      }
    }
  ]
}
```

Definitions:

- `id`: plugin id / tool plugin `name` visible to the app.
- `version`: informational.
- `args_mode`: controls how Python passes tool call arguments into the script:
  - `"flags"`: Option 3 (argv flags) for simple scalar params.
  - `"positional"`: argv positional parameters for very simple tools.
  - `"json"`: Option 1 (stdin JSON + `jq`) for complex params.
- `tools`: list of OpenAI tool schemas.

Constraints (v1):

- `args_mode=flags` only supports scalar argument values: `string`, `integer`, `number`, `boolean`.
- `args_mode=positional` only supports scalar argument values: `string`, `integer`, `number`, `boolean`.
- `args_mode=json` requires `jq` to be available for parsing inside bash.

### 3) Argument passing rules

#### `args_mode = "flags"` (simple params; preferred for simple tasks)

Python maps `arguments` to argv:

- Strings/numbers/integers: `--<name> <value>`
- Booleans:
  - `true` → `--<name>`
  - `false` → `--no-<name>`

Example:

```bash
bash tool.bash run --path ./file.txt --start 10 --end 20 --number
```

Suggested bash parsing template (portable; does not require `getopt`):

```bash
parse_flags() {
  path=""
  start=""
  end=""
  number="true"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --path)
        path="${2-}"; shift 2 ;;
      --start)
        start="${2-}"; shift 2 ;;
      --end)
        end="${2-}"; shift 2 ;;

      --number)
        number="true"; shift ;;
      --no-number)
        number="false"; shift ;;

      --path=*)
        path="${1#*=}"; shift ;;
      --start=*)
        start="${1#*=}"; shift ;;
      --end=*)
        end="${1#*=}"; shift ;;

      --)
        shift; break ;;

      *)
        echo "unknown arg: $1" >&2
        return 2 ;;
    esac
  done

  [[ -n "$path" ]] || { echo "--path is required" >&2; return 2; }
  [[ -n "$start" && "$start" =~ ^[0-9]+$ ]] || { echo "--start must be int" >&2; return 2; }
  [[ -n "$end" && "$end" =~ ^[0-9]+$ ]] || { echo "--end must be int" >&2; return 2; }
}
```

#### `args_mode = "positional"` (very simple tools)

In positional mode, the schema JSON includes an explicit ordered mapping defining how named tool arguments become positional argv parameters.

Example schema fields:

```json
{
  "args_mode": "positional",
  "positional": [
    {"name": "path", "required": true},
    {"name": "start_line", "required": true},
    {"name": "end_line", "required": true},
    {"name": "show_line_numbers", "required": false, "default": false}
  ]
}
```

Rules:

- `positional[i].name` must match a property name in the OpenAI `parameters.properties`.
- Each entry may include:
  - `required` (boolean)
  - `default` (scalar)
- Python may omit trailing non-provided arguments (especially when the last entries have defaults).

Invocation shape:

```bash
bash tool.bash run <arg1> <arg2> <arg3> ...
```

Python should omit trailing empty/defaulted arguments when they occur at the end of the argv list.

#### `args_mode = "json"` (complex params; requires jq)

Python calls:

```bash
bash tool.bash run --args-json
```

and writes the JSON `arguments` object to stdin.

The bash tool parses parameters using `jq`, e.g.:

```bash
args_json="$(cat)"
path="$(jq -r '.path' <<<"$args_json")"
```

### 4) Streaming + final result mapping

`BashToolPlugin.stream_tool(...)` should:

- Spawn the bash subprocess.
- Stream output as tool partials:
  - For stdout chunks: yield `{ "part": { "type": "text", "content": <chunk>, "stream": "stdout" } }`
  - For stderr chunks (optional): yield `{ "part": { "type": "text", "content": <chunk>, "stream": "stderr" } }`
- When the process exits, yield a final result dict:

```json
{
  "success": true,
  "exit_code": 0,
  "stdout": "...",
  "stderr": "..."
}
```

Preview:

- `format_tool_call_preview(...)` calls `bash tool.bash preview ...` (using the same args passing rules as `run`) and returns stdout stripped to a single line.

Formatting:

- Do not implement additional formatting hooks beyond preview in v1.

---

## Implementation tasks (phased)

### Phase 1 — Core tool wrapper

Add a new tool plugin implementation:

- `core/python/agent_core/tool_hosts/bash_tool_plugin.py`

Responsibilities:

- Execute `schema`, parse JSON, validate required fields.
- Return `tools` from `get_tool_schemas`.
- Implement `format_tool_call_preview` via `preview` subcommand.
- Implement `stream_tool` and `execute_tool`.
- Enforce timeouts and propagate non-zero exit codes into `{success: false}`.

Policy-driven settings (initial proposal):

- `plugin_policy.bash_timeout_seconds` (default: 60)
- `plugin_policy.bash_stream_stderr` (default: false)

### Phase 2 — Application/plugin manager integration

Add a new plugin source:

- `core/python/agent_app/plugin_sources/bash_tool.py` (`BashToolSource`)

Config forms:

- Single file:
  - `{ "bash_tool": { "file": "./plugins/my_tool.bash" } }`
- Local directory:
  - `{ "bash_tool": { "path": "./plugins/bash-tools" } }` (requires `agent_plugin.json`)
- Git repo (optional, policy-gated):
  - `{ "bash_tool": { "git": "https://...", "ref": "vX.Y.Z", "subdirectory": "..." } }` (requires `agent_plugin.json` at repo root or under `subdirectory`)

String forms:

- `"bash:./plugins/my_tool.bash"`
- `"bash:./plugins/bash-tools"`
- `"bash+git:https://example.com/acme/bash-tools.git#v0.1.0"`

Caching:

- Cache under `plugin_cache_dir/bash/<safe_id>@<revision>/...`.

Resolution returns Python classes:

- `BashToolSource.resolve(...)` returns a dynamically generated subclass of `BashToolPlugin` with class attributes set (`bash_entry`, `name/id`, etc).

Update plugin manager default sources order so `BashToolSource` is considered before Python repo sources.

### Phase 3 — Example plugins

Add a simple production-ready example tool under repo-root `plugins/`:

1) `plugins/bash-read-line-range/read_line_range.bash`
   - `args_mode=positional`
   - Implements `sed -n <start>,<end>p` and optional `nl -ba` numbering.
   - `preview` prints one line like:
     `read_line_range path=... start_line=... end_line=... show_line_numbers=false`.

Test-only examples used by the core test suite should live under `core/python/tests`
(prefer `core/python/tests/fixtures`).

### Phase 4 — Tests

Add tests under `core/python/tests`:

1) Plugin resolution test
   - Loads `{ "bash_tool": { "file": ... } }` (use a fixture under `core/python/tests/fixtures`).
   - Asserts plugin is classified as a tool.

2) Schema test
   - Calls `get_tool_schemas` and asserts the expected tool function schema is present.

3) Preview test
   - Calls `format_tool_call_preview` and asserts a single-line string.

4) Streaming execution test
   - Runs `stream_tool` against a fixture file.
   - Asserts at least two `"part"` events and final `{success: true}`.

Skipping/marking:

- `args_mode=json` tests should skip if `jq` is unavailable.

### Phase 5 — Docs

Update docs to describe:

- `bash_tool` config spec
- The `schema` / `preview` / `run` contract
- `args_mode` and argument passing rules
- Caveats (buffering, GNU/BSD differences, security)

---

## Caveats / design notes

### Streaming caveats

- Streaming is best-effort.
- Some pipelines may buffer when stdout is not a TTY.
- Consider optional `stdbuf` usage when present, but do not require it.

### Platform differences

- `sed` / `nl` behavior can differ between GNU/Linux and macOS/BSD.
- Examples should prefer portable options when possible.

### Security

- Bash plugins are arbitrary code execution.
- Must be policy-gated (e.g. `plugin_policy.allow_bash_tools`, `plugin_policy.allow_remote`).
- Always apply timeouts.

### Argument safety

- Python must use `subprocess.Popen([...])` (no shell).
- Bash scripts must quote expansions (e.g. `"$path"`).
