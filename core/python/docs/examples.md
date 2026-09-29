# Examples

This catalog is generated from the runnable examples under `core/python/examples`.

Plugin instances are short-lived and operate on explicit state objects. Providers, extensions, and features share provider state during a request; tools keep separate state.

Some examples and tests require a local service or hosted provider. Run them only with their integration marker and prerequisites enabled; a skipped gated test is not evidence that the integration ran.

## Example 10: FastAPI app and console client with Ollama.

This example shows how to wrap ``agent_core.AgentCore`` in a small
HTTP JSON application and pair it with a tiny console client.

The responsibilities mirror ``agent_app.AgentApplication`` in a
simplified way but stay on the core API level:

- the application owns a single AgentCore instance
- the application owns provider configuration
- the application owns session storage (in memory here)
- HTTP handlers translate HTTP JSON into core ``Session`` / messages
- a console client runs in-process and calls the same helpers as the HTTP routes

Out of the box the app is configured to use
``plugins.openai_provider.OpenAICompatibleProvider`` against a local
Ollama /v1 endpoint.

Environment variables (optional):
- OLLAMA_HOST (default: http://localhost:11434)
- OLLAMA_MODEL (default: llama3.2:1b)
- EXAMPLE10_PROVIDER (default: "openai_compatible"; can be set to
  "echo_openai_like" for offline/testing use)

Usage (API server):
- Run directly with the example script:

    $ python core/python/examples/example10_fastapi_console_ollama.py

  This will start a FastAPI app on http://127.0.0.1:8000.

- Or run with uvicorn explicitly:

    $ uvicorn examples.example10_fastapi_console_ollama:app --reload

Usage (console client):
- Run in a terminal:

    $ python core/python/examples/example10_fastapi_console_ollama.py --console

  This mode does not require the HTTP server; it calls the same
  helper functions that the FastAPI routes use.

Provider selection:
- By default the app uses the OpenAI-compatible provider with Ollama.
- For offline/testing use you can either:

  * set ``EXAMPLE10_PROVIDER=echo_openai_like`` in the environment, or
  * pass ``{"config_overrides": {"provider": "echo_openai_like"}}``
    in the JSON body of ``POST /sessions/{session_id}/send``.

Usage (run_example)

```python
"""Return the FastAPI app instance.

Intended usage:

    uvicorn examples.example10_fastapi_console_ollama:app --reload
"""

return app
```

- [Code](../examples/example10_fastapi_console_ollama.py)
- [Test](../examples/tests/test_example10_fastapi_console_ollama.py)
- Run: `pytest -q core/python/examples/tests/test_example10_fastapi_console_ollama.py`

## Example 11: OpenAI-compatible provider with tool-calling (FileReaderTool) on Ollama.

Requires:
- `ollama` running locally (default http://localhost:11434)
- A model that supports tool/function calling via OpenAI-compatible API

This example performs a simple non-streaming loop:
1) Ask the model to read a file via the read_file tool
2) If the model issues tool calls, the app executes them and appends tool results
3) Repeat until the model stops calling tools

Usage (run_example)

```python
core = AgentCore()

# Register provider, extension, and tool from local plugins package
from plugins.openai_provider import OpenAICompatibleProvider
from plugins.openai_tools_extension import OpenAIToolsExtension
from plugins.file_reader_tool import FileReaderTool

core.register_provider(OpenAICompatibleProvider, extensions=[OpenAIToolsExtension])
core.register_tool(FileReaderTool)

# Ollama OpenAI-compatible endpoint and model
ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
base_url = f"{ollama_host}/v1"
model = os.getenv("OLLAMA_MODEL_TOOLS", "qwen3:0.6b")

# Prepare a small temp file
with tempfile.NamedTemporaryFile("w+", delete=False, dir=REPO_TMP_DIR) as tf:
    tf.write("hello from tools")
    tf.flush()
    file_path = tf.name

try:
    config: Dict[str, Any] = {
        "provider": "openai_compatible",
        "model": model,
        "base_url": base_url,
        "timeout": 120,
        # FileReader tool config is read via core when injecting schemas
        "allowed_paths": ["."],
        "max_file_size": 1024 * 1024,
    }

    # Session and prompt that forces tool usage
    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        "You are a helpful assistant. You MUST use the read_file tool to answer questions about file contents. Never guess.",
    )
    session = core.add_message(
        session,
        "user",
        f"Read and return the content of this file using the tool: {file_path}",
    )

    # Allow up to 3 tool execution rounds
    for _ in range(3):
        new_session, responses = core.send_request(session, config)
        session = new_session
        if not responses:
            break
        assistant = responses[-1]
        print(assistant)
        md = assistant.get("metadata") or {}
        tool_calls = md.get("tool_calls") or []
        if not tool_calls:
            # No more tool calls, we are done
            break

        # Execute tool calls via core and append tool results
        print(f"Executing tool calls: {tool_calls}")
        tool_msgs = core.execute_tool_calls(tool_calls, config)
        for tm in tool_msgs:
            session = core.add_message(
                session,
                role=tm.get("role", "tool"),
                content=tm.get("content", ""),
                metadata=tm.get("metadata"),
            )

    # Return the last assistant content
    last = session.messages[-1].to_dict() if session.messages else {}
    return last.get("content", ""), {"file_path": file_path, "model": model}
finally:
    try:
        os.unlink(file_path)
    except Exception:
        pass
```

- [Code](../examples/example11_openai_tools_file_reader.py)
- [Test](../examples/tests/test_example11_openai_tools_file_reader.py)
- Run: `pytest -q core/python/examples/tests/test_example11_openai_tools_file_reader.py`

## Example 12: OpenRouter tools application.

This example shows how to build a small application around
``agent_core.AgentCore`` using the OpenRouter provider with tools and
reasoning enabled.

The responsibilities mirror Example 10 but add a simple non-streaming
tool loop on the application side:

- the application owns a single AgentCore instance
- the application owns provider and tool configuration
- the application owns session storage (in memory here)
- HTTP handlers translate HTTP JSON into core ``Session`` / messages
- the /send route runs a tool loop around ``AgentCore.send_request``
- a console client reuses the same helpers in-process

Out of the box the app is configured to use
``openrouter_plugins.openrouter_provider.OpenRouterProvider`` with
``openai/gpt-5-mini`` on OpenRouter. Tools are provided by
``FileReaderTool`` (read_file) and ``FileWriterTool`` (write_file).

This example requires the OpenRouter plugin bundle to be installed:

    $ python -m pip install -e plugins/openrouter

Environment variables (optional, but OPENROUTER_API_KEY is required for real calls):
- OPENROUTER_API_KEY (no default)
- OPENROUTER_MODEL (default: openai/gpt-5-mini)
- OPENROUTER_BASE_URL (default: https://openrouter.ai/api/v1)

Usage (API server):

    $ python core/python/examples/example12_openrouter_tools_app.py

This starts a FastAPI app on http://127.0.0.1:8000.

Usage (console client):

    $ python core/python/examples/example12_openrouter_tools_app.py --console

The console client talks to the same in-process helpers and runs the
same non-streaming tool loop as the HTTP API.

Tool loop behaviour (/sessions/{session_id}/send):

- merges application config with optional ``config_overrides``
- calls ``AgentCore.send_request`` once per loop
- inspects the last assistant message for ``metadata.tool_calls``
- executes tool calls via ``AgentCore.execute_tool_calls``
- appends tool results as ``role="tool"`` messages
- repeats until there are no more tool calls or ``max_loops`` is hit

The Example 12 test configures ``allowed_paths`` and
``working_directory`` per request so tools can safely read and write
Python files in a temporary directory when solving a coding puzzle.

Usage (run_example)

```python
"""Return the FastAPI app instance.

Intended usage::

    uvicorn examples.example12_openrouter_tools_app:app --reload
"""

return app
```

- [Code](../examples/example12_openrouter_tools_app.py)
- [Test](../examples/tests/test_example12_openrouter_tools_app.py)
- Run: `pytest -q core/python/examples/tests/test_example12_openrouter_tools_app.py`

## Example 13: Application-layer OpenRouter tools app.

This example mirrors Example 12 (OpenRouter + tools coding puzzle) but
is built on top of the higher-level :class:`agent_app.AgentApplication`
API instead of calling :class:`agent_core.AgentCore` directly.

Key points compared to Example 12:

- Uses a JSON config file to declare providers, plugins, and agents
- Uses filesystem-backed sessions via ``FilesystemSessionStore``
- Uses the application-layer non-streaming tool loop
- Exposes a thin FastAPI wrapper with the same basic routes:
  - ``POST /sessions`` – create session for an agent
  - ``POST /sessions/{session_id}/messages`` – append message
  - ``POST /sessions/{session_id}/send`` – send request (non-streaming by default)
- Supports per-request ``config_overrides`` and an optional ``max_loops``
  parameter that limits tool loop depth by temporarily overriding the
  application tool-loop configuration.

Configuration is loaded from the JSON file next to this module:

- ``example13_openrouter_tools_app_layer_config.json``

That config declares:

- Provider ``openrouter_tools`` with:
  - provider: ``"openrouter"`` (OpenRouterProvider)
  - model: ``"openai/gpt-5-mini"`` (can be changed in the file)
  - api_key: ``${env:OPENROUTER_API_KEY}`` (loaded via python-dotenv)
  - base_url: ``"https://openrouter.ai/api/v1"``
  - tools config: ``allowed_paths``, ``max_file_size``, ``working_directory``
  - reasoning config: ``enable_reasoning=True``, ``reasoning_effort="low"``
- Plugins:
  - ``path:../../../plugins/openrouter`` (loads ``openrouter_plugins.*``)
  - ``plugins.file_reader_tool.FileReaderTool``
  - ``plugins.file_writer_tool.FileWriterTool``
- Agent ``default`` bound to provider ``openrouter_tools``

Environment variables (via .env at repo root):
- OPENROUTER_API_KEY (required for real calls)
- OPENROUTER_MODEL / OPENROUTER_BASE_URL: can be set by editing the
  config file or by using per-request ``config_overrides``.

Usage (API server):

    $ python core/python/examples/example13_openrouter_tools_app_layer.py

Usage (console client):

    $ python core/python/examples/example13_openrouter_tools_app_layer.py --console

Console mode uses the same application-layer tool loop as the HTTP API.

Usage (run_example)

```python
"""Return the FastAPI app instance for uvicorn usage.

Intended usage::

    uvicorn examples.example13_openrouter_tools_app_layer:app --reload
"""

return app
```

- [Code](../examples/example13_openrouter_tools_app_layer.py)
- [Test](../examples/tests/test_example13_openrouter_tools_app_layer.py)
- Run: `pytest -q core/python/examples/tests/test_example13_openrouter_tools_app_layer.py`

## Example 1: Character-streaming echo provider.

Streams characters of "Echo: <last user message>" as native chunks, and finalizes the full message.

Plugin code

```python
from typing import Any, Dict, Iterator, List, Optional, Tuple
from agent_core.types import ProviderPlugin

class EchoProvider(ProviderPlugin):
    name = "echo"
    version = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {"model": {"type": "string", "default": "echo-1"}}

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return [{"type": "text", "key": "model", "label": "Model"}]

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        # Provider state is an opaque dict owned by the provider and its
        # extensions/features. This example only tracks an accumulated string
        # during streaming.
        return {"config": config, "accumulated": ""}

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        return list(native_messages), {**state, "accumulated": ""}

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        return native_messages

    def stream_api(
        self,
        native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        last_user = next(
            (m for m in reversed(native_messages) if m.get("role") == "user"),
            {"content": ""},
        )
        text = f"Echo: {last_user.get('content', '')}"
        for ch in text:
            yield {"content": ch}

    def process_chunk(
        self,
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        acc = state.get("accumulated", "") + native_chunk.get("content", "")
        new_state = {**state, "accumulated": acc}
        partial = (
            [
                {
                    "role": "assistant",
                    "content": native_chunk.get("content", ""),
                    "metadata": {},
                }
            ]
            if native_chunk.get("content")
            else []
        )
        # Keep provider-native history unchanged during streaming.
        return partial, [], list(native_messages), new_state

    def finalize(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        content = state.get("accumulated", "")
        if not content:
            return [], list(native_messages), state
        final = {"role": "assistant", "content": content, "metadata": {}}
        return [final], [*native_messages, final], {**state, "accumulated": ""}

    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        last_user = next(
            (m for m in reversed(native_messages) if m.get("role") == "user"),
            {"content": ""},
        )
        content = f"Echo: {last_user.get('content', '')}"
        final = {"role": "assistant", "content": content, "metadata": {}}
        return [], [final], [*native_messages, final], state
```

- [Code](../examples/example1_echo_provider.py)
- [Test](../examples/tests/test_example1_echo_provider.py)
- Run: `pytest -q core/python/examples/tests/test_example1_echo_provider.py`

## Example 2: Prefix provider extension.

Adds a prefix to final assistant messages and counts processed chunks in metadata.

Plugin code

```python
from typing import Any, Dict, List, Tuple, Optional
from agent_core.types import ProviderExtensionPlugin

class PrefixExtension(ProviderExtensionPlugin):
    name: str = "prefix_extension"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enabled": {"type": "boolean", "default": True},
            "prefix": {"type": "string", "default": "[EXT]"},
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return [
            {"type": "checkbox", "key": "enabled", "label": "Enable Extension"},
            {"type": "text", "key": "prefix", "label": "Prefix"},
        ]

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {
            **state,
            "config": {**state.get("config", {}), **config},
            "extension_processed_chunks": 0,
        }

    def process_chunk(
            self,
            native_chunk: Optional[Dict[str, Any]],
            partial_messages: List[Dict[str, Any]],
            final_messages: List[Dict[str, Any]],
            native_messages: List[Dict[str, Any]],
            state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        if not state.get("config", {}).get("enabled", True):
            return partial_messages, final_messages, native_messages, state
        processed = state.get("extension_processed_chunks", 0) + (
            1 if native_chunk is not None else 0
        )
        prefix = state.get("config", {}).get("prefix", "[EXT]")
        finals = (
            [{**m, "content": f"{prefix} {m['content']}"} for m in final_messages]
            if final_messages
            else final_messages
        )
        if finals:
            last = finals[-1]
            finals[-1] = {
                **last,
                "metadata": {
                    **last.get("metadata", {}),
                    "extension_processed_chunks": processed,
                },
            }
        return partial_messages, finals, native_messages, {
            **state,
            "extension_processed_chunks": processed,
        }

    def finalize(
            self,
            final_messages: List[Dict[str, Any]],
            native_messages: List[Dict[str, Any]],
            state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        if not state.get("config", {}).get("enabled", True):
            return final_messages, native_messages, state
        prefix = state.get("config", {}).get("prefix", "[EXT]")
        finals = [{**m, "content": f"{prefix} {m['content']}"} for m in final_messages]
        if finals:
            count = state.get("extension_processed_chunks", 0)
            last = finals[-1]
            finals[-1] = {
                **last,
                "metadata": {
                    **last.get("metadata", {}),
                    "extension_processed_chunks": count,
                },
            }
        return finals, native_messages, state
```

- [Code](../examples/example2_prefix_extension.py)
- [Test](../examples/tests/test_example2_prefix_extension.py)
- Run: `pytest -q core/python/examples/tests/test_example2_prefix_extension.py`

## Example 3: Configurable web-search feature.

This feature marks finals with metadata when web_search_enabled is True and prints a notice.

Plugin code

```python
from typing import Any, Dict, List, Optional, Tuple

class WebSearchFeature:
    name: str = "web_search"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "web_search_enabled": {"type": "boolean", "default": False},
            "max_results": {"type": "integer", "default": 5},
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "type": "checkbox",
                "key": "web_search_enabled",
                "label": "Enable Web Search",
            },
            {
                "type": "number",
                "key": "max_results",
                "label": "Max Results",
                "condition": {"web_search_enabled": True},
            },
        ]

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {**state, "config": {**state.get("config", {}), **config}}

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        if not state.get("config", {}).get("web_search_enabled"):
            return final_messages, native_messages, state
        # Print a simple notice to stdout when enabled
        max_results = state.get("config", {}).get("max_results")
        print(
            f"[WebSearchFeature] Search enabled; annotating finals (max_results={max_results})"
        )
        finals = [
            {**m, "metadata": {**m.get("metadata", {}), "web_search_used": True}}
            for m in final_messages
        ]
        return finals, native_messages, state
```

- [Code](../examples/example3_web_search_feature.py)
- [Test](../examples/tests/test_example3_web_search_feature.py)
- Run: `pytest -q core/python/examples/tests/test_example3_web_search_feature.py`

## Example 4: Sandboxed file-reader tool.

Plugin code

```python
import os
from typing import Any, Dict, List, Optional
from agent_core.types import ToolPlugin

class FileReaderTool(ToolPlugin):
    name: str = "file_reader"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "allowed_paths": {
                "type": "array",
                "items": {"type": "string"},
                "default": ["."],
                "description": "Allowed base paths for file reading",
            },
            "max_file_size": {
                "type": "integer",
                "default": 1048576,
                "description": "Maximum file size in bytes",
            },
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "type": "text",
                "key": "allowed_paths",
                "label": "Allowed Paths (comma-separated)",
            }
        ]

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        # Tool state is an opaque dict owned by the tool. This example
        # only relies on configuration values.
        return {"config": config}

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read contents of a text file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file to read",
                            }
                        },
                        "required": ["file_path"],
                    },
                },
            }
        ]

    def execute_tool(
        self,
        tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        if tool_name != "read_file":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        file_path = arguments.get("file_path", "")
        allowed = state["config"].get("allowed_paths", ["."])
        if not any(
            os.path.abspath(file_path).startswith(os.path.abspath(base))
            for base in allowed
        ):
            return {
                "success": False,
                "error": f"Access denied: {file_path} not in allowed paths",
            }
        try:
            size = os.path.getsize(file_path)
            if size > state["config"].get("max_file_size", 1048576):
                return {"success": False, "error": f"File too large: {size} bytes"}
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"success": True, "result": content}
        except Exception as e:
            return {"success": False, "error": f"Error reading file: {str(e)}"}

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        return (
            f"File contents:\n{result['result']}"
            if result.get("success")
            else f"Error: {result.get('error')}"
        )
```

- [Code](../examples/example4_file_reader_tool.py)
- [Test](../examples/tests/test_example4_file_reader_tool.py)
- Run: `pytest -q core/python/examples/tests/test_example4_file_reader_tool.py`

## Example 5: Basic low-level API usage with Ollama.

Configured to call a local Ollama OpenAI-compatible endpoint.

Environment variables (optional):
- OLLAMA_HOST (default: http://localhost:11434)
- OLLAMA_MODEL (default: llama3.2:1b)

Usage (run_example)

```python
import os
from agent_core import AgentCore
from plugins.openai_provider import OpenAICompatibleProvider

# Initialize core (stateless pipeline)
core = AgentCore()

# Register provider (just the class, no config)
core.register_provider(OpenAICompatibleProvider)

# Discover Ollama endpoint/model from env
ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
base_url = f"{ollama_host}/v1"
model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

# Application manages config
config = {
    "provider": "openai_compatible",
    "model": model,
    "base_url": base_url,
    # No API key required for local Ollama
    "timeout": 60,
}

# Application creates and manages session (immutable)
session = core.create_session()

# Add messages (returns new session each time)
session = core.add_message(session, "system", "You are a helpful assistant.")
session = core.add_message(session, "user", "What is 2+2?")

# Send request (returns new session + final messages)
session, messages = core.send_request(session, config)
print(messages[-1]["content"])  # expect some text

# Messages now include the assistant response(s)
print(len(session.messages))  # expect 3

# Add another message (functional - returns new session)
session = core.add_message(session, "user", "What about 3+3?")

# Send again
session, messages = core.send_request(session, config)
print(messages[-1]["content"])  # expect some text
```

- [Code](../examples/example5_basic_ollama.py)
- [Test](../examples/tests/test_example5_basic_ollama.py)
- Run: `pytest -q core/python/examples/tests/test_example5_basic_ollama.py`

## Example 6: Streaming with the low-level API and Ollama.

Configured to call a local Ollama OpenAI-compatible endpoint.

Environment variables (optional):
- OLLAMA_HOST (default: http://localhost:11434)
- OLLAMA_MODEL (default: llama3.2:1b)

Usage (run_example)

```python
core = AgentCore()
core.register_provider(OpenAICompatibleProvider)

# Discover Ollama endpoint/model from env
ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
base_url = f"{ollama_host}/v1"
model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

# Application manages config and session
config = {
    "provider": "openai_compatible",
    "model": model,
    "base_url": base_url,
    "timeout": 60,
}
session = core.create_session()
session = core.add_message(session, "user", "Write a short poem")

# Stream response (functional - returns new session at end)
for chunk in core.send_request_stream(session, config):
    if chunk["type"] == "partial":
        print(chunk["message"].get("content", ""), end="", flush=True)
    elif chunk["type"] == "final":
        # Get new session with response message
        session = chunk["session"]
        print("\n[Done]")
```

- [Code](../examples/example6_streaming_ollama.py)
- [Test](../examples/tests/test_example6_streaming_ollama.py)
- Run: `pytest -q core/python/examples/tests/test_example6_streaming_ollama.py`

## Example 7: Tool-call loop with Ollama.

Preserves original messages and uses FileReaderTool.

Usage (run_example)

```python
core = AgentCore()
core.register_provider(OpenAICompatibleProvider)
core.register_tool(FileReaderTool)

# Discover Ollama endpoint/model from env
ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
base_url = f"{ollama_host}/v1"
model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

# Application manages config (mixing tool config)
config = {
    "provider": "openai_compatible",
    "model": model,
    "base_url": base_url,
    "timeout": 60,
    "allowed_paths": ["."],
}

# Initialize tool state once (tool plugins are stateful)
tool_state = FileReaderTool().init(config)

session = core.create_session()
session = core.add_message(session, "user", "Read the contents of README.md")

# Application handles tool loop
max_iterations = 5
for i in range(max_iterations):
    # Send request (functional)
    session, messages = core.send_request(session, config)

    # Check for tool calls
    tool_calls = messages[-1].get("metadata", {}).get("tool_calls", [])

    if not tool_calls:
        # No tools, we're done
        print("Assistant:", messages[-1]["content"])
        break

    # Execute tools (application responsibility)
    for tool_call in tool_calls:
        tool_name = tool_call["function"]["name"]
        arguments = json.loads(tool_call["function"]["arguments"])

        # Execute tool (stateful - pass initialized state)
        result = FileReaderTool().execute_tool(tool_name, arguments, tool_state)
        formatted = FileReaderTool().format_tool_result(result, tool_state)

        # Add tool result as message (functional)
        session = core.add_message(
            session,
            "tool",
            formatted,
            metadata={"tool_call_id": tool_call["id"], "name": tool_name},
        )
```

- [Code](../examples/example7_tool_calls_ollama.py)
- [Test](../examples/tests/test_example7_tool_calls_ollama.py)
- Run: `pytest -q core/python/examples/tests/test_example7_tool_calls_ollama.py`

## Example 8: Message history manipulation with Ollama.

Preserves original message sequence and edits.

Usage (run_example)

```python
core = AgentCore()
core.register_provider(OpenAICompatibleProvider)

# Discover Ollama endpoint/model from env
ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
base_url = f"{ollama_host}/v1"
model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

config = {
    "provider": "openai_compatible",
    "model": model,
    "base_url": base_url,
    "timeout": 60,
}

session = core.create_session()

# Add multiple messages (functional chaining)
session = core.add_message(session, "system", "You are a helpful assistant.")
session = core.add_message(session, "user", "Hello")
session = core.add_message(session, "assistant", "Hi! How can I help?")
session = core.add_message(session, "user", "What's the weather?")

# Remove last message (functional): since we change history, drop native history metadata first
md = dict(session.metadata)
md.pop("native_messages", None)
md.pop("native_messages_integrity", None)
session = Session(
    session_id=session.session_id,
    messages=session.messages[:-1],
    metadata=md,
)

# Add different message
session = core.add_message(session, "user", "Tell me a joke")

# Send request with modified history
session, messages = core.send_request(session, config)

# Clear conversation and start fresh (functional): drop native history metadata first
md2 = dict(session.metadata)
md2.pop("native_messages", None)
md2.pop("native_messages_integrity", None)
session = Session(
    session_id=session.session_id, messages=[], metadata=md2
)
session = core.add_message(session, "user", "New conversation")
```

- [Code](../examples/example8_message_history_ollama.py)
- [Test](../examples/tests/test_example8_message_history_ollama.py)
- Run: `pytest -q core/python/examples/tests/test_example8_message_history_ollama.py`

## Example 9: Configuration updates and a web-search feature with Ollama.

Preserves original prompts and prints when search is enabled.

Usage (run_example)

```python
core = AgentCore()

# Register plugins (no config)
core.register_provider(OpenAICompatibleProvider)
core.register_feature(WebSearchFeature)

session = core.create_session()

# Discover Ollama endpoint/model from env
ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
base_url = f"{ollama_host}/v1"
model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

# Application manages config
config1 = {
    "provider": "openai_compatible",
    "model": model,
    "base_url": base_url,
    "timeout": 60,
    "web_search_enabled": False,
}

# Initial request without search
session = core.add_message(
    session,
    "system",
    "Your task is to find the latest news in a topic. Return the most important 3 news with just the headline. No summary is needed, just a short headline.",
)
session = core.add_message(session, "user", "Latest AI news")
session, messages = core.send_request(session, config1)
print(messages[-1]["content"])
print(messages[-1]["metadata"])

# User enables search in UI - application updates config
config2 = {
    **config1,
    "web_search_enabled": True,
    "max_results": 10,
}

# Next request uses search
session = core.add_message(session, "user", "More AI news")
session, messages = core.send_request(session, config2)
print(messages[-1]["content"])
print(messages[-1]["metadata"])
```

- [Code](../examples/example9_config_updates_ollama.py)
- [Test](../examples/tests/test_example9_config_updates_ollama.py)
- Run: `pytest -q core/python/examples/tests/test_example9_config_updates_ollama.py`
