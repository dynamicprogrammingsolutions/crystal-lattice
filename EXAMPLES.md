# Examples (Code + Tests)

Each example below includes:
- Actual code (identical to the file in `examples/`)
- Link to code file and its test
- Command to run the test for that example only

Note: Examples tests are placed in `examples/tests/` and are not part of the core test suite. Run them explicitly as shown.

---

## Echo Provider (streaming)
- Code: examples/echo_provider.py
- Test: examples/tests/example_echo_provider.py
- Run: `pytest examples/tests/example_echo_provider.py -q`

```python
# examples/echo_provider.py
"""
EchoProvider example (class-based provider plugin) derived from PLUGIN_EXAMPLES.md.
Streams characters of "Echo: <last user message>" as native chunks, and finalizes the full message.
"""
from typing import Any, Dict, List, Iterator, Tuple


class EchoProvider:
    name = "echo"
    version = "1.0.0"

    @staticmethod
    def get_config_schema() -> Dict[str, Any]:
        return {"model": {"type": "string", "default": "echo-1"}}

    @staticmethod
    def get_ui_elements() -> List[Dict[str, Any]]:
        return [{"type": "text", "key": "model", "label": "Model"}]

    @staticmethod
    def init(config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config, "runtime_state": {"accumulated": ""}}

    @staticmethod
    def update_state(state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        return {**state, "config": {**state.get("config", {}), **updates}}

    @staticmethod
    def initialize_request(native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]:
        return {**state, "runtime_state": {**state.get("runtime_state", {}), "accumulated": ""}}

    @staticmethod
    def to_native_messages(messages: List[Dict[str, Any]], state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return list(messages)

    @staticmethod
    def from_native_messages(native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return list(native_messages)

    @staticmethod
    def stream_api(native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        last_user = next((m for m in reversed(native_messages) if m.get("role") == "user"), {"content": ""})
        text = f"Echo: {last_user.get('content', '')}"
        for ch in text:
            yield {"content": ch}

    @staticmethod
    def process_chunk(
        native_chunk: Dict[str, Any],
        messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        acc = state.get("runtime_state", {}).get("accumulated", "") + native_chunk.get("content", "")
        new_state = {**state, "runtime_state": {**state.get("runtime_state", {}), "accumulated": acc}}
        partial = (
            [{"role": "assistant", "content": native_chunk.get("content", ""), "metadata": {}}]
            if native_chunk.get("content")
            else []
        )
        return [], partial, [], new_state

    @staticmethod
    def finalize(
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        content = state.get("runtime_state", {}).get("accumulated", "")
        if not content:
            return [], [], state
        final = [{"role": "assistant", "content": content, "metadata": {}}]
        return final, [], state

    @staticmethod
    def call_api(
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        last_user = next((m for m in reversed(native_messages) if m.get("role") == "user"), {"content": ""})
        content = f"Echo: {last_user.get('content', '')}"
        return ([{"role": "assistant", "content": content, "metadata": {}}], [], [], state)
```

---

## Prefix Extension
- Code: examples/prefix_extension.py
- Test: examples/tests/example_prefix_extension.py
- Run: `pytest examples/tests/example_prefix_extension.py -q`

```python
# examples/prefix_extension.py
"""
PrefixExtension example (class-based provider extension) derived from PLUGIN_EXAMPLES.md.
Adds a prefix to final assistant messages and counts processed chunks in metadata.
"""
from typing import Any, Dict, List, Tuple, Optional


class PrefixExtension:
    name: str = "prefix_extension"
    version: str = "1.0.0"
    target_provider: str = "echo"

    @staticmethod
    def get_config_schema() -> Dict[str, Any]:
        return {
            "enabled": {"type": "boolean", "default": True},
            "prefix": {"type": "string", "default": "[EXT]"},
        }

    @staticmethod
    def get_ui_elements() -> List[Dict[str, Any]]:
        return [
            {"type": "checkbox", "key": "enabled", "label": "Enable Extension"},
            {"type": "text", "key": "prefix", "label": "Prefix"},
        ]

    @staticmethod
    def init(config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        rs = {**state.get("runtime_state", {}), "extension_processed_chunks": 0}
        return {**state, "config": {**state.get("config", {}), **config}, "runtime_state": rs}

    @staticmethod
    def update_state(state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        return {**state, "config": {**state.get("config", {}), **updates}}

    @staticmethod
    def to_native_messages(messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return messages

    @staticmethod
    def from_native_messages(native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return messages

    @staticmethod
    def initialize_request(native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    @staticmethod
    def process_chunk(
        native_chunk: Optional[Dict[str, Any]],
        messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        if not state.get("config", {}).get("enabled", True):
            return partial_messages, final_messages, native_messages, state
        processed = state.get("runtime_state", {}).get("extension_processed_chunks", 0) + (
            1 if native_chunk is not None else 0
        )
        rs = {**state.get("runtime_state", {}), "extension_processed_chunks": processed}
        prefix = state.get("config", {}).get("prefix", "[EXT]")
        finals = (
            [
                {**m, "content": f"{prefix} {m['content']}"}
                for m in final_messages
            ]
            if final_messages
            else final_messages
        )
        if finals:
            last = finals[-1]
            finals[-1] = {
                **last,
                "metadata": {**last.get("metadata", {}), "extension_processed_chunks": processed},
            }
        return partial_messages, finals, native_messages, {**state, "runtime_state": rs}

    @staticmethod
    def finalize(
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
            finals[-1] = {**last, "metadata": {**last.get("metadata", {}), "extension_processed_chunks": count}}
        return finals, native_messages, state
```

---

## Web Search Feature
- Code: examples/web_search_feature.py
- Test: examples/tests/example_web_search_feature.py
- Run: `pytest examples/tests/example_web_search_feature.py -q`

```python
# examples/web_search_feature.py
"""
WebSearchFeature example (class-based feature plugin) derived from PLUGIN_EXAMPLES.md.
This feature marks finals with metadata when web_search_enabled is True.
"""
from typing import Any, Dict, List, Tuple


class WebSearchFeature:
    name: str = "web_search"
    version: str = "1.0.0"

    @staticmethod
    def get_config_schema() -> Dict[str, Any]:
        return {
            "web_search_enabled": {"type": "boolean", "default": False},
            "max_results": {"type": "integer", "default": 5},
        }

    @staticmethod
    def get_ui_elements() -> List[Dict[str, Any]]:
        return [
            {"type": "checkbox", "key": "web_search_enabled", "label": "Enable Web Search"},
            {"type": "number", "key": "max_results", "label": "Max Results", "condition": {"web_search_enabled": True}},
        ]

    @staticmethod
    def init(config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {**state, "config": {**state.get("config", {}), **config}, "capabilities": ["web_search"]}

    @staticmethod
    def update_state(state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        return {**state, "config": {**state.get("config", {}), **updates}}

    @staticmethod
    def initialize_request(native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    @staticmethod
    def to_native_messages(messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return messages

    @staticmethod
    def from_native_messages(native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return messages

    @staticmethod
    def finalize(
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        if not state.get("config", {}).get("web_search_enabled"):
            return final_messages, native_messages, state
        finals = [
            {**m, "metadata": {**m.get("metadata", {}), "web_search_used": True}}
            for m in final_messages
        ]
        return finals, native_messages, state
```

---

## File Reader Tool
- Code: examples/file_reader_tool.py
- Test: examples/tests/example_file_reader_tool.py
- Run: `pytest examples/tests/example_file_reader_tool.py -q`

```python
# examples/file_reader_tool.py
"""
FileReaderTool example (class-based tool plugin) derived from PLUGIN_EXAMPLES.md.
"""
import os
from typing import Any, Dict, List


class FileReaderTool:
    name: str = "file_reader"
    version: str = "1.0.0"

    @staticmethod
    def get_config_schema() -> Dict[str, Any]:
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

    @staticmethod
    def get_ui_elements() -> List[Dict[str, Any]]:
        return [{"type": "text", "key": "allowed_paths", "label": "Allowed Paths (comma-separated)"}]

    @staticmethod
    def init(config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config, "runtime_state": {}, "ui_state": {}, "capabilities": []}

    @staticmethod
    def update_state(state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        return {**state, "config": {**state["config"], **updates}}

    @staticmethod
    def get_tool_schemas(state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read contents of a text file",
                    "parameters": {
                        "type": "object",
                        "properties": {"file_path": {"type": "string", "description": "Path to the file to read"}},
                        "required": ["file_path"],
                    },
                },
            }
        ]

    @staticmethod
    def execute_tool(tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name != "read_file":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        file_path = arguments.get("file_path", "")
        allowed = state["config"].get("allowed_paths", ["."])
        if not any(os.path.abspath(file_path).startswith(os.path.abspath(base)) for base in allowed):
            return {"success": False, "error": f"Access denied: {file_path} not in allowed paths"}
        try:
            size = os.path.getsize(file_path)
            if size > state["config"].get("max_file_size", 1048576):
                return {"success": False, "error": f"File too large: {size} bytes"}
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"success": True, "result": content}
        except Exception as e:
            return {"success": False, "error": f"Error reading file: {str(e)}"}

    @staticmethod
    def format_tool_result(result: Dict[str, Any], state: Dict[str, Any]) -> str:
        return (
            f"File contents:\n{result['result']}" if result.get("success") else f"Error: {result.get('error')}"
        )
```

---

## PROJECT_PLAN Example 1: Basic API
- Code: examples/project_plan_example1_basic.py
- Test: examples/tests/example_project_plan_example1_basic.py
- Run: `pytest examples/tests/example_project_plan_example1_basic.py -q`

```python
# examples/project_plan_example1_basic.py
from agent_core import AgentCore
from plugins.providers.openai.python.openai_provider import OpenAICompatibleProvider

# Initialize core (stateless pipeline)
core = AgentCore()

# Register provider (just the class, no config)
core.register_provider(OpenAICompatibleProvider)

# Application manages config
config = {
    "model": "gpt-4o",
    "api_key": "sk-..."
}

# Application creates and manages session (immutable)
session = core.create_session()

# Add messages (returns new session each time)
session = core.add_message(session, "system", "You are a helpful assistant.")
session = core.add_message(session, "user", "What is 2+2?")

# Send request (returns new session + final messages)
session, messages = core.send_request(session, config)
print(messages[-1]["content"])  # "4"

# Messages now include the assistant response(s)
print(len(session.messages))  # 3

# Add another message (functional - returns new session)
session = core.add_message(session, "user", "What about 3+3?")

# Send again
session, messages = core.send_request(session, config)
print(messages[-1]["content"])  # "6"
```

---

## PROJECT_PLAN Example 2: Streaming
- Code: examples/project_plan_example2_streaming.py
- Test: examples/tests/example_project_plan_example2_streaming.py
- Run: `pytest examples/tests/example_project_plan_example2_streaming.py -q`

```python
# examples/project_plan_example2_streaming.py
from agent_core import AgentCore
from plugins.providers.openai.python.openai_provider import OpenAICompatibleProvider

# Core stores only pipeline
core = AgentCore()
core.register_provider(OpenAICompatibleProvider)

# Application manages config and session
config = {"model": "gpt-4o", "api_key": "sk-..."}
session = core.create_session()
session = core.add_message(session, "user", "Write a short poem")

# Stream response (functional - returns new session at end)
for chunk in core.send_request_stream(session, config):
    if chunk["type"] == "partial":
        print(chunk["message"]["content"], end="", flush=True)
    elif chunk["type"] == "final":
        # Get new session with response message
        session = chunk["session"]
        print("\n[Done]")
```

---

## PROJECT_PLAN Example 3: Tool Calls
- Code: examples/project_plan_example3_tool_calls.py
- Test: examples/tests/example_project_plan_example3_tool_calls.py
- Run: `pytest examples/tests/example_project_plan_example3_tool_calls.py -q` (expected to fail until provider emits tool calls)

```python
# examples/project_plan_example3_tool_calls.py
from agent_core import AgentCore
from plugins.providers.openai.python.openai_provider import OpenAICompatibleProvider
from my_plugins.file_reader_tool import FileReaderTool
import json

core = AgentCore()
core.register_provider(OpenAICompatibleProvider)
core.register_tool(FileReaderTool)

# Application manages config
config = {
    "model": "gpt-4",
    "api_key": "sk-...",
    "allowed_paths": ["."]  # Tool config mixed in
}

# Initialize tool state once (tool plugins are stateful)
tool_state = FileReaderTool.init(config)

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
        result = FileReaderTool.execute_tool(tool_name, arguments, tool_state)
        formatted = FileReaderTool.format_tool_result(result, tool_state)
        
        # Add tool result as message (functional)
        session = core.add_message(
            session,
            "tool",
            formatted,
            metadata={
                "tool_call_id": tool_call["id"],
                "name": tool_name
            }
        )
    
    # Loop continues with tool results in conversation
```

---

## PROJECT_PLAN Example 4: Message Manipulation
- Code: examples/project_plan_example4_messages.py
- Test: examples/tests/example_project_plan_example4_messages.py
- Run: `pytest examples/tests/example_project_plan_example4_messages.py -q`

```python
# examples/project_plan_example4_messages.py
from agent_core import AgentCore
from plugins.providers.openai.python.openai_provider import OpenAICompatibleProvider

core = AgentCore()
core.register_provider(OpenAICompatibleProvider)

config = {"model": "gpt-4", "api_key": "sk-..."}

session = core.create_session()

# Add multiple messages (functional chaining)
session = core.add_message(session, "system", "You are a helpful assistant.")
session = core.add_message(session, "user", "Hello")
session = core.add_message(session, "assistant", "Hi! How can I help?")
session = core.add_message(session, "user", "What's the weather?")

# Remove last message (functional)
from agent_core.types import Session
session = Session(
    session_id=session.session_id,
    messages=session.messages[:-1],
    metadata=session.metadata
)

# Add different message
session = core.add_message(session, "user", "Tell me a joke")

# Send request with modified history
session, messages = core.send_request(session, config)

# Clear conversation and start fresh (functional)
session = Session(
    session_id=session.session_id,
    messages=[],
    metadata=session.metadata
)
session = core.add_message(session, "user", "New conversation")
```

---

## PROJECT_PLAN Example 5: Configuration Updates
- Code: examples/project_plan_example5_config_updates.py
- Test: examples/tests/example_project_plan_example5_config_updates.py
- Run: `pytest examples/tests/example_project_plan_example5_config_updates.py -q`

```python
# examples/project_plan_example5_config_updates.py
from agent_core import AgentCore
from plugins.providers.openai.python.openai_provider import OpenAICompatibleProvider
from my_plugins.web_search_feature import WebSearchFeature

core = AgentCore()

# Register plugins (no config)
core.register_provider(OpenAICompatibleProvider)
core.register_feature(WebSearchFeature)

session = core.create_session()

# Application manages config
config1 = {
    "model": "gpt-4o",
    "api_key": "sk-...",
    "web_search_enabled": False
}

# Initial request without search
session = core.add_message(session, "user", "Latest AI news")
session, messages = core.send_request(session, config1)

# User enables search in UI - application updates config
config2 = {
    **config1,
    "web_search_enabled": True,
    "max_results": 10
}

# Next request uses search
session = core.add_message(session, "user", "More AI news")
session, messages = core.send_request(session, config2)
```

---

## PROJECT_PLAN Example 6: Full App (Not Implemented)
- Code: examples/project_plan_example6_app.py
- Test: examples/tests/example_project_plan_example6_app.py
- Run: `pytest examples/tests/example_project_plan_example6_app.py -q` (expected to fail)

```python
# examples/project_plan_example6_app.py
from fastapi import FastAPI, WebSocket
from agent_core import AgentCore
from plugins.providers.openai.python.openai_provider import OpenAICompatibleProvider
from my_plugins.web_search_feature import WebSearchFeature
from my_plugins.file_reader_tool import FileReaderTool
import json

app = FastAPI()

# Load and resolve config (application responsibility)
import os

def resolve_config(config):
    """Resolve ${env:...} and ${file:...} references"""
    resolved = {}
    for key, value in config.items():
        if isinstance(value, str):
            if value.startswith("${env:"):
                var_name = value[6:-1]
                resolved[key] = os.getenv(var_name)
            elif value.startswith("${file:"):
                file_path = value[7:-1]
                with open(os.path.expanduser(file_path)) as f:
                    resolved[key] = f.read().strip()
            else:
                resolved[key] = value
        else:
            resolved[key] = value
    return resolved

# Load config from file
with open("config.json") as f:
    config = json.load(f)

# Initialize core
core = AgentCore()

# Register plugins (just classes, no config)
core.register_provider(OpenAICompatibleProvider)
core.register_feature(WebSearchFeature)
core.register_tool(FileReaderTool)

# Application resolves and merges config
def get_agent_config(agent_name):
    """Resolve and merge config for an agent."""
    agent_config = config["agents"][agent_name]
    provider_name = agent_config.get("provider", "openai")
    
    # Start with provider defaults
    merged = resolve_config(config["providers"]["defaults"][provider_name].copy())
    
    # Merge agent-specific config (flat structure)
    merged.update(resolve_config(agent_config))
    
    return merged

# Application manages sessions
sessions = {}

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    if session_id not in sessions:
        sessions[session_id] = core.create_session(session_id)
    session = sessions[session_id]
    
    # Application manages config
    agent_config = get_agent_config("default")
    # Initialize tool state once per connection
    file_reader_state = FileReaderTool.init(agent_config)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "message":
                # Add user message (functional)
                session = core.add_message(session, "user", data["content"])
                
                # Tool loop (application logic)
                max_iterations = 5
                for i in range(max_iterations):
                    # Stream response (functional - pass config)
                    final_messages = []
                    async for chunk in core.send_request_stream_async(session, agent_config):
                        if chunk["type"] == "partial":
                            await websocket.send_json({
                                "type": "partial",
                                "content": chunk["message"]["content"]
                            })
                        elif chunk["type"] == "final":
                            session = chunk["session"]
                            final_messages = chunk["messages"]
                    
                    # Check for tool calls
                    tool_calls = (final_messages[-1] if final_messages else {}).get("metadata", {}).get("tool_calls", [])
                    
                    if not tool_calls:
                        # Done
                        await websocket.send_json({
                            "type": "final",
                            "messages": final_messages
                        })
                        break
                    
                    # Execute tools
                    for tool_call in tool_calls:
                        tool_name = tool_call["function"]["name"]
                        arguments = json.loads(tool_call["function"]["arguments"])
                        
                        # Notify frontend
                        await websocket.send_json({
                            "type": "tool_call",
                            "name": tool_name,
                            "arguments": arguments
                        })
                        
                        # Execute (stateful - pass initialized tool state)
                        result = FileReaderTool.execute_tool(
                            tool_name,
                            arguments,
                            file_reader_state
                        )
                        formatted = FileReaderTool.format_tool_result(
                            result,
                            file_reader_state
                        )
                        
                        # Add tool result (functional)
                        session = core.add_message(
                            session,
                            "tool",
                            formatted,
                            metadata={
                                "tool_call_id": tool_call["id"],
                                "name": tool_name
                            }
                        )
                    
                    # Continue loop with tool results
            
            elif data["type"] == "update_config":
                # Application updates its config
                agent_config = {**agent_config, **data["updates"]}
                sessions[session_id] = session  # Store updated session
    
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()

# Optional: allow tests to import and touch the app
def run_example():
    return app
```
