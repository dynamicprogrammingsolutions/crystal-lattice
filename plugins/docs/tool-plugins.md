# Tool plugins

Tool plugins (`ToolPlugin`) expose callable tools to the model and execute the
resulting tool calls inside the core/application tool loop.

This guide is the canonical tool-authoring companion to the general overview in
`docs/plugins/development.md`.

Runtime references (source of truth):

- Protocol/docstrings: `core/python/agent_core/types.py`
- Tool wrapper: `core/python/agent_core/plugin/tool.py`
- Defaulting/compatibility adapter: `core/python/agent_core/plugin/adapters.py`
- Tool discovery + execution: `core/python/agent_core/core.py`
- Application preview/tool loop: `core/python/agent_app/tool_loop.py`

Reference implementations:

- Simple object-payload tool: `core/python/plugins/file_reader_tool.py`
- Template package: `plugins/template-python-tools/src/template_python_tools/echo_tool.py`
- Payload-first + custom routing: `plugins/codex-tools/src/codex_tools/apply_patch_tool.py`
- Streaming shell-style tools: `plugins/codex-tools/src/codex_tools/base_shell_tool.py`

See also:

- [Provider extensions (tools + reasoning)](provider-extensions.md)
- [Node tool plugins](node-tool-plugins.md)
- [Bash tool plugins](bash-tool-plugins.md)
- [Packaging & loading plugins](plugin-packaging-and-loading.md)
- [Execution order (providers, extensions, features, tools)](plugin-execution-order.md)
- [Configuration schema (`get_config_schema`)](config-schema.md)
- [UI elements (`get_ui_elements` and `ui_type`)](ui-elements.md)
- [Testing & validation](testing-and-validation.md)

---

## What tool plugins are for

Tool plugins are the right place for model-invoked operations such as:

- file reads/writes
- shell execution
- structured calculators or search helpers
- custom/freeform tools such as patch editors or REPLs

Unlike providers, provider extensions, and features, tools do **not** share the
provider state dict. Each tool manages its own independent `state: dict` between
`init(...)`, `get_tool_schemas(...)`, `execute_tool(...)`, and related hooks.

Minimal core message flow:

1. Tool runs `init(config)`.
2. Tool returns one or more schemas from `get_tool_schemas(state)`.
3. Provider/provider extensions expose those schemas to the model.
4. Model emits tool-call objects.
5. Core inspects each tool call through the active interop registry.
6. Core routes the call to a tool.
7. Tool executes and returns a result dict.
8. Core formats the result into a `role="tool"` message.

Example final tool message shape:

```python
{
    "role": "tool",
    "content": "Result: 5",
    "metadata": {
        "tool_call_id": "call_1",
        "tool_name": "add",
        "tool_plugin": "calculator",
        "display": {"type": "text", "content": "Result: 5"},
    },
}
```

---

## Quickstart / development workflow

The fastest workflow is:

1. start from the Python tools template
2. implement one simple object-payload tool
3. test it through `AgentCore.execute_tool_calls(...)`
4. add previews/streaming/display formatting if needed
5. try it in a real application config via `path:` loading

### Step 0: start from the template package

Recommended starting point:

- `plugins/template-python-tools`

Note: the current template still demonstrates the legacy object-payload style.
That remains valid for classic function tools through the compatibility layer,
but new tools can also adopt the payload-first signatures shown on this page.

Typical repo layout:

```text
my-tools/
  pyproject.toml
  agent_plugin.json
  src/
    my_tools/
      __init__.py
      my_tool.py
  tests/
    test_my_tool.py
```

Example `agent_plugin.json`:

```json
{
  "entries": ["my_tools.my_tool.MyTool"],
  "subdirectory": "."
}
```

More packaging details: [Packaging & loading plugins](plugin-packaging-and-loading.md).

### Step 1: implement one small tool first

This is the recommended first implementation pattern for new Python tools:

```python
from __future__ import annotations

from typing import Any

from agent_core.types import ToolPlugin


class EchoTool(ToolPlugin):
    name = "echo_tool"
    version = "0.1.0"

    def init(self, config: dict[str, Any]) -> dict[str, Any]:
        return {"config": config}

    def get_tool_schemas(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "echo",
                    "description": "Echo back the provided value.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "value": {"type": "string"},
                        },
                        "required": ["value"],
                    },
                },
            }
        ]

    def format_tool_call_preview(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        *,
        payload_kind: str | None = None,
        payload_format: str | None = None,
        payload_metadata: dict[str, Any] | None = None,
        tool_call: dict[str, Any] | None = None,
    ) -> str:
        if tool_name != "echo" or not isinstance(payload, dict):
            return ""
        return f"echo value={payload.get('value')!r}"

    def execute_tool(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        *,
        payload_kind: str | None = None,
        payload_format: str | None = None,
        payload_metadata: dict[str, Any] | None = None,
        tool_call: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if tool_name != "echo":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        if not isinstance(payload, dict):
            return {"success": False, "error": "payload must be an object"}

        value = payload.get("value")
        if not isinstance(value, str):
            return {"success": False, "error": "value must be a string"}
        return {"success": True, "result": value}

    def format_tool_result(self, result: dict[str, Any], state: dict[str, Any]) -> str:
        if result.get("success"):
            return str(result.get("result") or "")
        return f"Error: {result.get('error')}"
```

### Step 2: write the first tests before adding complexity

Quick-feedback test loop:

```python
from agent_core import AgentCore


def test_echo_tool_round_trip():
    core = AgentCore()
    core.register_tool(EchoTool)

    tool_calls = [
        {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "echo",
                "arguments": {"value": "hello"},
            },
        }
    ]

    results = core.execute_tool_calls(tool_calls, config={})
    assert results[0]["role"] == "tool"
    assert results[0]["content"] == "hello"
    assert results[0]["metadata"]["tool_name"] == "echo"
```

Recommended command while iterating:

```bash
pytest plugins/my-tools/tests -q
```

### Step 3: try the tool in a real application config

After the first tests pass, load the tool package through the application layer.

Example config fragment:

```json
{
  "plugin_cache_dir": "~/.crystal/cache/plugins",
  "plugins": [
    "plugins.openai_provider.OpenAICompatibleProvider",
    "path:../my-tools"
  ],
  "provider": "openai_compatible",
  "model": "gpt-4o-mini"
}
```

That exercises the real request flow:

- tool enablement
- `get_tool_schemas(...)`
- provider/provider-extension schema injection
- model tool call generation
- tool execution
- tool message rendering in the terminal/app

---

## Tool protocol

The full protocol lives in `core/python/agent_core/types.py`. The most important
tool hooks are:

```python
class ToolPlugin(BasePlugin, Protocol):
    def init(self, config: dict[str, Any]) -> dict[str, Any]: ...

    def get_tool_schemas(self, state: dict[str, Any]) -> list[dict[str, Any]]: ...

    def get_tool_interop_contribution(
        self,
        state: dict[str, Any],
    ) -> ToolInteropContribution: ...

    def can_handle_tool_call(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        *,
        payload_kind: str | None = None,
        payload_format: str | None = None,
        payload_metadata: dict[str, Any] | None = None,
        tool_call: dict[str, Any] | None = None,
        tool_schema: dict[str, Any] | None = None,
    ) -> bool | None: ...

    def execute_tool(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        *,
        payload_kind: str | None = None,
        payload_format: str | None = None,
        payload_metadata: dict[str, Any] | None = None,
        tool_call: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...

    def format_tool_result(self, result: dict[str, Any], state: dict[str, Any]) -> str: ...

    def format_tool_call_preview(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        *,
        payload_kind: str | None = None,
        payload_format: str | None = None,
        payload_metadata: dict[str, Any] | None = None,
        tool_call: dict[str, Any] | None = None,
    ) -> str: ...

    def stream_tool(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        *,
        payload_kind: str | None = None,
        payload_format: str | None = None,
        payload_metadata: dict[str, Any] | None = None,
        tool_call: dict[str, Any] | None = None,
    ) -> Iterator[dict[str, Any]]: ...

    def to_display_format(
        self,
        text: str,
        result: dict[str, Any],
        state: dict[str, Any],
    ) -> dict[str, Any]: ...
```

Additional common hooks:

- `get_config_schema(...)`
- `get_ui_elements(...)`
- `get_tags(...)`
- `required_tags()` / `forbidden_tags()`
- `is_enabled(config, tags, models, context)`

### Recommended mental model

- `get_tool_schemas(...)` describes what the model can call
- `can_handle_tool_call(...)` optionally claims responsibility for a call
- `execute_tool(...)` performs the work and returns a result dict
- `format_tool_result(...)` produces the string the model sees
- `to_display_format(...)` produces richer UI-only output for humans

---

## Tool schemas and interop

### Tools are not limited to one schema format

`get_tool_schemas(...)` may return tool schemas in **any format understood by the
active interop registry**.

Common case: OpenAI-style function schema.

```python
def get_tool_schemas(self, state: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read a file from disk.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                    },
                    "required": ["file_path"],
                },
            },
        }
    ]
```

Custom/freeform example:

```python
def get_tool_schemas(self, state: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "type": "custom",
            "name": "apply_patch",
            "description": "Apply a freeform patch.",
            "format": {
                "type": "grammar",
                "syntax": "lark",
                "definition": "start: /.+/",
            },
        }
    ]
```

### Choosing among multiple schema variants

Some tools expose different schema variants depending on provider capabilities.
The tool init config may include `_tool_schema_target_formats`, which is a hint
from the active provider/extensions about which schema formats they can send.

Example pattern:

```python
def get_tool_schemas(self, state: dict[str, Any]) -> list[dict[str, Any]]:
    config = state.get("config") or {}
    targets = set(config.get("_tool_schema_target_formats") or [])

    if "openai.responses.custom.tool_schema" in targets:
        return [{
            "type": "custom",
            "name": "apply_patch",
            "description": "Apply a freeform patch.",
            "format": {"type": "grammar", "syntax": "lark", "definition": "start: /.+/"},
        }]

    return [{
        "type": "function",
        "function": {
            "name": "apply_patch",
            "parameters": {
                "type": "object",
                "properties": {"input": {"type": "string"}},
                "required": ["input"],
                "additionalProperties": False,
            },
        },
    }]
```

### Advanced: contribute custom accessors/adapters

Most tools do **not** need this. Use it only when your tool emits a schema or
call format that built-in/provider-contributed interop cannot already inspect.

Example shape:

```python
from agent_core.tool_interop import ToolInteropContribution


def get_tool_interop_contribution(self, state: dict[str, Any]) -> ToolInteropContribution:
    return ToolInteropContribution(
        schema_accessors=(MyCustomSchemaAccessor(),),
        call_accessors=(MyCustomToolCallAccessor(),),
    )
```

Important behavior:

- explicit/config-provided contributions are tried first
- provider / extension / tool contributions are tried next
- built-in defaults are used as fallback

That means tool-level contributions are additive, not all-or-nothing.

---

## Routing and execution

### Payload-first execution

Core no longer assumes every tool call is a JSON object of `arguments`.
Instead, the active call accessor extracts:

- `tool_name`, when available
- `payload`, the final payload object
- `payload_kind`, such as `object` or `text`
- `payload_format`, when available
- `payload_metadata`, when available

Example object payload tool:

```python
def execute_tool(
    self,
    tool_name: str | None,
    payload: Any,
    state: dict[str, Any],
    *,
    payload_kind: str | None = None,
    payload_format: str | None = None,
    payload_metadata: dict[str, Any] | None = None,
    tool_call: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if tool_name != "add" or not isinstance(payload, dict):
        return {"success": False, "error": "unsupported call"}
    return {
        "success": True,
        "result": float(payload.get("a", 0)) + float(payload.get("b", 0)),
    }
```

Example text payload tool:

```python
def execute_tool(
    self,
    tool_name: str | None,
    payload: Any,
    state: dict[str, Any],
    *,
    payload_kind: str | None = None,
    payload_format: str | None = None,
    payload_metadata: dict[str, Any] | None = None,
    tool_call: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if tool_name not in {None, "apply_patch"}:
        return {"success": False, "error": f"Unknown tool: {tool_name}"}
    if payload_kind != "text" or not isinstance(payload, str) or not payload:
        return {"success": False, "error": "expected raw patch text"}
    return {"success": True, "result": f"received {len(payload)} bytes"}
```

### Optional routing with `can_handle_tool_call(...)`

Core asks each tool `can_handle_tool_call(...)` before falling back to legacy
name-based matching. Returning:

- `True` claims the call
- `False` explicitly rejects it
- `None` means “no opinion; try legacy fallback”

This is useful when:

- the tool name is optional or absent
- multiple schemas share the same tool name
- routing depends on payload kind/format rather than name alone

Today, `tool_call` is the most useful advanced input for this hook. The
`tool_schema` argument may be `None` in the current core routing path, so do not
rely on it being populated.

Example:

```python
def can_handle_tool_call(
    self,
    tool_name: str | None,
    payload: Any,
    state: dict[str, Any],
    *,
    payload_kind: str | None = None,
    payload_format: str | None = None,
    payload_metadata: dict[str, Any] | None = None,
    tool_call: dict[str, Any] | None = None,
    tool_schema: dict[str, Any] | None = None,
) -> bool | None:
    if tool_name not in {None, "apply_patch"}:
        return False
    return payload_kind == "text" and isinstance(payload, str)
```

### Legacy dict-argument tools still work

Many existing tools still implement the older object-arguments contract:

```python
def execute_tool(self, tool_name: str, arguments: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    ...
```

That remains supported by the Python wrapper compatibility layer in
`core/python/agent_core/plugin/adapters.py`. New tools should prefer the
payload-first signature, but older object-payload tools do not need an immediate
rewrite.

---

## Results, previews, display payloads, and streaming

### `format_tool_result(...)` is what the model sees

The final string returned by `format_tool_result(...)` becomes the tool
message `content` sent back into the conversation.

Example:

```python
def format_tool_result(self, result: dict[str, Any], state: dict[str, Any]) -> str:
    if result.get("success"):
        return f"Read {result.get('bytes_read', 0)} bytes"
    return f"Error: {result.get('error')}"
```

### `to_display_format(...)` is for richer UI output

`to_display_format(...)` lets tools attach a richer display payload under
`metadata["display"]` without changing what the model sees.

Example:

```python
def to_display_format(
    self,
    text: str,
    result: dict[str, Any],
    state: dict[str, Any],
) -> dict[str, Any]:
    return {
        "type": "text",
        "content": text,
        "single_line": result.get("summary", text.splitlines()[0] if text else ""),
    }
```

Good uses for `display` payloads:

- showing the executed shell command and workdir
- showing changed files after a patch
- showing compact summaries in collapsed/mobile views

### `format_tool_call_preview(...)`

This hook is used by the application tool loop to preview tool calls before they
execute.

Example:

```python
def format_tool_call_preview(
    self,
    tool_name: str | None,
    payload: Any,
    state: dict[str, Any],
    *,
    payload_kind: str | None = None,
    payload_format: str | None = None,
    payload_metadata: dict[str, Any] | None = None,
    tool_call: dict[str, Any] | None = None,
) -> str:
    if tool_name == "read_file" and isinstance(payload, dict):
        return f"read_file {payload.get('file_path', '')}".strip()
    return ""
```

### `stream_tool(...)`

Use `stream_tool(...)` when the tool produces incremental output.

Rules used by `AgentCore.iter_tool_messages(...)`:

- a yielded dict containing `"success"` is treated as the final result dict
- a yielded dict containing `"part"` is treated as a partial display payload
- any other yielded dict is wrapped as `{"part": chunk}` for backward compatibility

Example:

```python
from collections.abc import Iterator


def stream_tool(
    self,
    tool_name: str | None,
    payload: Any,
    state: dict[str, Any],
    *,
    payload_kind: str | None = None,
    payload_format: str | None = None,
    payload_metadata: dict[str, Any] | None = None,
    tool_call: dict[str, Any] | None = None,
) -> Iterator[dict[str, Any]]:
    yield {"part": {"type": "text", "content": "starting..."}}
    yield {"part": {"type": "text", "content": "still working..."}}
    yield {"success": True, "result": "done"}
```

If you do **not** implement `stream_tool(...)`, the default adapter simply calls
`execute_tool(...)` once and yields that final result dict.

---

## Tool state and enablement

### State shape

Tool state is tool-owned. Keep it explicit and serializable.

Recommended pattern:

```python
def init(self, config: dict[str, Any]) -> dict[str, Any]:
    return {
        "config": config,
        "max_bytes": int(config.get("max_bytes", 1024 * 1024)),
    }
```

Guidelines:

- treat state as immutable by convention
- put derived config into state if it simplifies execution hooks
- avoid relying on long-lived instance attributes

### Tags and enablement

Tools can participate in tag-based enablement just like other plugin kinds.

Example:

```python
def required_tags(self) -> list[str]:
    return ["supports_tools"]


def is_enabled(
    self,
    config: dict[str, Any],
    tags: list[str],
    models: list[dict[str, Any]],
    context: dict[str, Any],
) -> bool | None:
    model = str(config.get("model") or "")
    if model.startswith("gpt-5"):
        return True
    return None
```

Use this for:

- model-specific tool exposure
- provider capability gating
- feature-flagged tools

---

## Testing tool plugins

Recommended test layers:

1. unit tests for the tool logic itself
2. `AgentCore.execute_tool_calls(...)` tests for end-to-end tool messages
3. preview/streaming tests when implementing `format_tool_call_preview(...)` or `stream_tool(...)`
4. application/provider integration tests only after the first three pass

### Unit test the pure execution path first

```python
def test_echo_tool_execute_direct():
    tool = EchoTool()
    state = tool.init({})
    result = tool.execute_tool("echo", {"value": "hello"}, state)
    assert result == {"success": True, "result": "hello"}
```

### Then test through `AgentCore`

```python
def test_echo_tool_core_round_trip():
    core = AgentCore()
    core.register_tool(EchoTool)
    results = core.execute_tool_calls(
        [
            {
                "id": "call_1",
                "type": "function",
                "function": {"name": "echo", "arguments": {"value": "hello"}},
            }
        ],
        config={},
    )
    assert results[0]["metadata"]["tool_name"] == "echo"
```

### Test advanced interop explicitly

If your tool emits nonstandard schemas/calls, add tests for:

- schema inspection
- call inspection
- routing via `can_handle_tool_call(...)`
- passthrough vs adaptation for different target formats

The new raw-input/custom tool tests in `core/python/tests/test_core_execute_tool_calls.py`
are a good reference pattern.

---

## Out-of-process tool hosts

This repo also supports out-of-process tool plugins:

- [Node tool plugins](node-tool-plugins.md) for JavaScript/TypeScript tools
- [Bash tool plugins](bash-tool-plugins.md) for shell-script-backed tools

Important current limitation:

- the in-process Python tool API is payload-first and can handle raw
  text/freeform payloads
- the current Node and Bash host contracts remain centered on classic
  object/function-style tool calls

So if you need advanced custom/freeform payload handling today, Python tools are
still the best fit.

---

## Reference implementations

- `core/python/plugins/file_reader_tool.py`: small, conventional object-payload tool
- `core/python/plugins/file_writer_tool.py`: object-payload write tool
- `plugins/template-python-tools/src/template_python_tools/echo_tool.py`: package template
- `plugins/codex-tools/src/codex_tools/apply_patch_tool.py`: payload-first raw-text tool with `can_handle_tool_call(...)`
- `plugins/codex-tools/src/codex_tools/base_shell_tool.py`: display payloads, previews, and streaming patterns