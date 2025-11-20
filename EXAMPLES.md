# Examples

Note: Plugins use instance methods but should remain stateless (pure) and operate on explicit state objects. Plugin instances are short‑lived and scoped to a single request, just like the shared provider state managed by the provider wrapper. Tools rely on explicit ToolState and should not keep durable object state.

## PROJECT_PLAN Example 6: FastAPI/WebSocket App (Ollama)

PROJECT_PLAN Example 6: FastAPI/WebSocket App (Ollama)
Runs a simple WS endpoint using the core and plugins.

Usage (run_example)

```python
return app
```

- Code: `examples/example10_project_plan_app.py`
- Test: `examples/tests/test_example10_project_plan_app.py`
- Run: `pytest -q examples/tests/test_example10_project_plan_app.py`

## EchoProvider example (class-based provider plugin) derived from PLUGIN_EXAMPLES.md.

EchoProvider example (class-based provider plugin) derived from PLUGIN_EXAMPLES.md.
Streams characters of "Echo: <last user message>" as native chunks, and finalizes the full message.

Plugin code

```python
from typing import Any, Dict, List, Iterator, Tuple
from agent_core.types import ProviderPlugin

class EchoProvider(ProviderPlugin):
    name = "echo"
    version = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {"model": {"type": "string", "default": "echo-1"}}

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return [{"type": "text", "key": "model", "label": "Model"}]

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config, "runtime_state": {"accumulated": ""}}

    def update_state(self, state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        return {**state, "config": {**state.get("config", {}), **updates}}

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            **state,
            "runtime_state": {**state.get("runtime_state", {}), "accumulated": ""},
        }

    def to_native_messages(
        self,
        messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        return list(messages)

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        return list(native_messages)

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
        acc = state.get("runtime_state", {}).get("accumulated", "") + native_chunk.get(
            "content", ""
        )
        new_state = {
            **state,
            "runtime_state": {**state.get("runtime_state", {}), "accumulated": acc},
        }
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
        return [], partial, [], new_state

    def finalize(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        content = state.get("runtime_state", {}).get("accumulated", "")
        if not content:
            return [], [], state
        final = [{"role": "assistant", "content": content, "metadata": {}}]
        return final, [], state

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
        return (
            [{"role": "assistant", "content": content, "metadata": {}}],
            [],
            [],
            state,
        )
```

- Code: `examples/example1_echo_provider.py`
- Test: `examples/tests/test_example1_echo_provider.py`
- Run: `pytest -q examples/tests/test_example1_echo_provider.py`

## PrefixExtension example (class-based provider extension) derived from PLUGIN_EXAMPLES.md.

PrefixExtension example (class-based provider extension) derived from PLUGIN_EXAMPLES.md.
Adds a prefix to final assistant messages and counts processed chunks in metadata.

Plugin code

```python
from typing import Any, Dict, List, Tuple, Optional
from agent_core.types import ProviderExtensionPlugin

class PrefixExtension(ProviderExtensionPlugin):
    name: str = "prefix_extension"
    version: str = "1.0.0"
    target_provider: str = "echo"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enabled": {"type": "boolean", "default": True},
            "prefix": {"type": "string", "default": "[EXT]"},
        }

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return [
            {"type": "checkbox", "key": "enabled", "label": "Enable Extension"},
            {"type": "text", "key": "prefix", "label": "Prefix"},
        ]

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        rs = {**state.get("runtime_state", {}), "extension_processed_chunks": 0}
        return {
            **state,
            "config": {**state.get("config", {}), **config},
            "runtime_state": rs,
        }

    def update_state(self, state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        return {**state, "config": {**state.get("config", {}), **updates}}

    def to_native_messages(
        self,
        messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return messages

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return messages

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        return state

    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        if not state.get("config", {}).get("enabled", True):
            return partial_messages, final_messages, native_messages, state
        processed = state.get("runtime_state", {}).get(
            "extension_processed_chunks", 0
        ) + (1 if native_chunk is not None else 0)
        rs = {**state.get("runtime_state", {}), "extension_processed_chunks": processed}
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
        return partial_messages, finals, native_messages, {**state, "runtime_state": rs}

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
            count = state.get("runtime_state", {}).get("extension_processed_chunks", 0)
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

- Code: `examples/example2_prefix_extension.py`
- Test: `examples/tests/test_example2_prefix_extension.py`
- Run: `pytest -q examples/tests/test_example2_prefix_extension.py`

## WebSearchFeature example (class-based feature plugin) derived from PLUGIN_EXAMPLES.md.

WebSearchFeature example (class-based feature plugin) derived from PLUGIN_EXAMPLES.md.
This feature marks finals with metadata when web_search_enabled is True and prints a notice.

Plugin code

```python
from typing import Any, Dict, List, Tuple
from agent_core.types import FeaturePlugin

class WebSearchFeature:
    name: str = "web_search"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "web_search_enabled": {"type": "boolean", "default": False},
            "max_results": {"type": "integer", "default": 5},
        }

    def get_ui_elements(self) -> List[Dict[str, Any]]:
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
        return {
            **state,
            "config": {**state.get("config", {}), **config},
            "capabilities": ["web_search"],
        }

    def update_state(self, state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        return {**state, "config": {**state.get("config", {}), **updates}}

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        return state

    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return messages

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return messages

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

- Code: `examples/example3_web_search_feature.py`
- Test: `examples/tests/test_example3_web_search_feature.py`
- Run: `pytest -q examples/tests/test_example3_web_search_feature.py`

## FileReaderTool example (class-based tool plugin) derived from PLUGIN_EXAMPLES.md.

FileReaderTool example (class-based tool plugin) derived from PLUGIN_EXAMPLES.md.

Plugin code

```python
import os
from typing import Any, Dict, List
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

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "text",
                "key": "allowed_paths",
                "label": "Allowed Paths (comma-separated)",
            }
        ]

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "config": config,
            "runtime_state": {},
            "ui_state": {},
            "capabilities": [],
        }

    def update_state(self, state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        return {**state, "config": {**state["config"], **updates}}

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

- Code: `examples/example4_file_reader_tool.py`
- Test: `examples/tests/test_example4_file_reader_tool.py`
- Run: `pytest -q examples/tests/test_example4_file_reader_tool.py`

## PROJECT_PLAN Example 1: Basic Low-Level API Usage (Python)

PROJECT_PLAN Example 1: Basic Low-Level API Usage (Python)
Configured to call a local Ollama OpenAI-compatible endpoint.

Environment variables (optional):
- OLLAMA_HOST (default: http://localhost:11434)
- OLLAMA_MODEL (default: llama3.2:1b)

Usage (run_example)

```python
import os
from agent_core import AgentCore
from plugins.providers.openai.python.openai_provider import OpenAICompatibleProvider

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

- Code: `examples/example5_project_plan_basic.py`
- Test: `examples/tests/test_example5_project_plan_basic.py`
- Run: `pytest -q examples/tests/test_example5_project_plan_basic.py`

## PROJECT_PLAN Example 2: Streaming with Low-Level API

PROJECT_PLAN Example 2: Streaming with Low-Level API
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

- Code: `examples/example6_project_plan_streaming.py`
- Test: `examples/tests/test_example6_project_plan_streaming.py`
- Run: `pytest -q examples/tests/test_example6_project_plan_streaming.py`

## PROJECT_PLAN Example 3: Tool Calls Loop (Ollama)

PROJECT_PLAN Example 3: Tool Calls Loop (Ollama)
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

- Code: `examples/example7_project_plan_tool_calls.py`
- Test: `examples/tests/test_example7_project_plan_tool_calls.py`
- Run: `pytest -q examples/tests/test_example7_project_plan_tool_calls.py`

## PROJECT_PLAN Example 4: Message History Manipulation (Ollama)

PROJECT_PLAN Example 4: Message History Manipulation (Ollama)
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

# Remove last message (functional)
session = Session(
    session_id=session.session_id,
    messages=session.messages[:-1],
    metadata=session.metadata,
)

# Add different message
session = core.add_message(session, "user", "Tell me a joke")

# Send request with modified history
session, messages = core.send_request(session, config)

# Clear conversation and start fresh (functional)
session = Session(
    session_id=session.session_id, messages=[], metadata=session.metadata
)
session = core.add_message(session, "user", "New conversation")
```

- Code: `examples/example8_project_plan_messages.py`
- Test: `examples/tests/test_example8_project_plan_messages.py`
- Run: `pytest -q examples/tests/test_example8_project_plan_messages.py`

## PROJECT_PLAN Example 5: Config Updates + Web Search Feature (Ollama)

PROJECT_PLAN Example 5: Config Updates + Web Search Feature (Ollama)
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

- Code: `examples/example9_project_plan_config_updates.py`
- Test: `examples/tests/test_example9_project_plan_config_updates.py`
- Run: `pytest -q examples/tests/test_example9_project_plan_config_updates.py`
