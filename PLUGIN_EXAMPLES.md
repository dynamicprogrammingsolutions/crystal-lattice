# AI Agent Platform - Plugin Examples

This document provides concise, working-style examples of each plugin type using the current lifecycle and types.

## Example 1: Basic Echo Provider (native, streaming)

```python
# echo_provider.py
from typing import Dict, Any, List, Iterator, Tuple

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
        return {"config": config, "runtime_state": {}}

    @staticmethod
    def update_state(state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        return {**state, "config": {**state.get("config", {}), **updates}}

    @staticmethod
    def initialize_request(native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Dict[str, Any]:
        # Reset per-turn runtime data (called with native messages)
        return {**state, "runtime_state": {"accumulated": ""}}

    @staticmethod
    def to_native_messages(messages: List[Dict[str, Any]], state: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Echo provider uses same shape for native messages
        return list(messages)

    @staticmethod
    def from_native_messages(native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Identity conversion for this example
        return list(native_messages)

    @staticmethod
    def stream_api(native_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        # Stream "Echo: <last user>" one character at a time as native chunks
        last_user = next((m for m in reversed(native_messages) if m["role"] == "user"), {"content": ""})
        text = f"Echo: {last_user['content']}"
        for ch in text:
            yield {"content": ch}

    @staticmethod
    def process_chunk(
        native_chunk: Dict[str, Any],
        messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        # Accumulate partial content and emit PartialMessage
        acc = state["runtime_state"].get("accumulated", "") + native_chunk.get("content", "")
        new_state = {**state, "runtime_state": {**state["runtime_state"], "accumulated": acc}}
        partial = [{"role": "assistant", "content": native_chunk.get("content", ""), "metadata": {}}]
        # No final/native outputs per chunk beyond the partial for this echo
        return [], partial, [], new_state

    @staticmethod
    def finalize(
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        # Emit one final assistant message from accumulated content
        content = state["runtime_state"].get("accumulated", "")
        final = [{"role": "assistant", "content": content, "metadata": {}}]
        return final, [], state

    @staticmethod
    def call_api(
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        # Non-streaming: return the echo directly as a final message
        last_user = next((m for m in reversed(native_messages) if m["role"] == "user"), {"content": ""})
        content = f"Echo: {last_user['content']}"
        final = [{"role": "assistant", "content": content, "metadata": {}}]
        return final, [], [], state
```

## Example 2: Provider Extension (chunk counting + prefix)

```python
# prefix_extension.py
name = "prefix_extension"
version = "1.0.0"
target_provider = "echo"

def get_config_schema():
    return {"enabled": {"type": "boolean", "default": True}, "prefix": {"type": "string", "default": "[EXT]"}}

def get_ui_elements():
    return [
        {"type": "checkbox", "key": "enabled", "label": "Enable Extension"},
        {"type": "text", "key": "prefix", "label": "Prefix"}
    ]

# Shared-state lifecycle

def init(config, state):
    rs = {**state.get("runtime_state", {}), "extension_processed_chunks": 0}
    return {**state, "config": {**state.get("config", {}), **config}, "runtime_state": rs}

def update_state(state, updates):
    return {**state, "config": {**state.get("config", {}), **updates}}

# Stateless transforms (optional)

def to_native_messages(messages, native_messages):
    return native_messages

def from_native_messages(native_messages, messages):
    return native_messages

# Request lifecycle

def initialize_request(native_messages, state):
    return state

# Hot path processing

def process_chunk(native_chunk, messages, state, partial_messages, final_messages, native_messages):
    if not state.get("config", {}).get("enabled", True):
        return partial_messages, final_messages, native_messages, state
    processed = state.get("runtime_state", {}).get("extension_processed_chunks", 0) + (1 if native_chunk is not None else 0)
    rs = {**state.get("runtime_state", {}), "extension_processed_chunks": processed}
    prefix = state.get("config", {}).get("prefix", "[EXT]")
    finals = [
        {**m, "content": f"{prefix} {m['content']}"}
        for m in final_messages
    ] if final_messages else final_messages
    if finals:
        last = finals[-1]
        finals[-1] = {**last, "metadata": {**last.get("metadata", {}), "extension_processed_chunks": processed}}
    return partial_messages, finals, native_messages, {**state, "runtime_state": rs}

# Finalization (cold path)

def finalize(messages, final_messages, native_messages, state):
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

## Example 3: Web Search Feature (finalize-only)

```python
# web_search_feature.py
name = "web_search"
version = "1.0.0"

def get_config_schema():
    return {"web_search_enabled": {"type": "boolean", "default": False}, "max_results": {"type": "integer", "default": 5}}

def get_ui_elements():
    return [
        {"type": "checkbox", "key": "web_search_enabled", "label": "Enable Web Search"},
        {"type": "number", "key": "max_results", "label": "Max Results", "condition": {"web_search_enabled": True}},
    ]

# Shared-state lifecycle

def init(config, state):
    return {**state, "config": {**state.get("config", {}), **config}, "capabilities": ["web_search"]}

def update_state(state, updates):
    return {**state, "config": {**state.get("config", {}), **updates}}

def initialize_request(native_messages, state):
    return state

# Stateless transforms (optional)

def to_native_messages(messages, native_messages):
    return native_messages

def from_native_messages(native_messages, messages):
    return native_messages

# Finalize (returns tuple)

def finalize(messages, final_messages, native_messages, state):
    if not state.get("config", {}).get("web_search_enabled"):
        return final_messages, native_messages, state
    finals = [
        {**m, "metadata": {**m.get("metadata", {}), "web_search_used": True}}
        for m in final_messages
    ]
    return finals, native_messages, state
```

## Example 4: File Reader Tool Plugin

```python
# file_reader_tool.py
import os

name = "file_reader"
version = "1.0.0"

def get_config_schema():
    return {
        "allowed_paths": {"type": "array", "items": {"type": "string"}, "default": ["."], "description": "Allowed base paths for file reading"},
        "max_file_size": {"type": "integer", "default": 1048576, "description": "Maximum file size in bytes"},
    }

def get_ui_elements():
    return [{"type": "text", "key": "allowed_paths", "label": "Allowed Paths (comma-separated)"}]

def init(config):
    return {"config": config, "runtime_state": {}}

def update_state(state, updates):
    return {**state, "config": {**state["config"], **updates}}

def get_tool_schemas(state):
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

def execute_tool(tool_name, arguments, state):
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

def format_tool_result(result, state):
    return f"File contents:\n{result['result']}" if result.get("success") else f"Error: {result.get('error')}"
```