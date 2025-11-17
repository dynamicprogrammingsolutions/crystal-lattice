# AI Agent Platform - Plugin Examples

This document provides complete, working examples of each plugin type.

## Example 1: Basic OpenAI Provider

```python
# openai_provider.py

from dataclasses import dataclass
from typing import Dict, Any, Iterator, AsyncIterator

@dataclass
class OpenAIProvider:
    """
    OpenAI provider plugin (stateless)
    All methods are pure functions or I/O operations
    """
    
    name: str = "openai"
    version: str = "1.0.0"
    
    @staticmethod
    def get_config_schema() -> Dict[str, Any]:
        """Return configuration schema"""
        return {
            "model": {"type": "string", "required": True},
            "api_key": {"type": "string", "required": True},
            "base_url": {"type": "string", "default": "https://api.openai.com/v1"}
        }
    
    @staticmethod
    def get_capabilities() -> list[str]:
        """Return provider capabilities"""
        return ["text_generation", "streaming", "tool_calling"]
    
    @staticmethod
    def to_native_messages(messages: list[Dict], config: Dict) -> list[Dict]:
        """Convert to OpenAI format (pure function)"""
        return [
            {
                "role": msg["role"],
                "content": msg["content"],
                **msg.get("metadata", {})
            }
            for msg in messages
        ]
    
    @staticmethod
    def build_request_body(messages: list[Dict], config: Dict) -> Dict:
        """Build OpenAI request (pure function)"""
        return {
            "model": config["model"],
            "messages": messages,
            "stream": True
        }
    
    @staticmethod
    def process_chunk(native_chunk: Dict) -> str:
        """Process streaming chunk (pure function)"""
        delta = native_chunk.get("choices", [{}])[0].get("delta", {})
        return delta.get("content", "")
    
    @staticmethod
    def finalize_message(content: str, config: Dict) -> Dict:
        """Create final message (pure function)"""
        return {
            "role": "assistant",
            "content": content,
            "metadata": {}
        }
    
    @staticmethod
    async def stream_api(body: Dict, config: Dict) -> AsyncIterator[Dict]:
        """Make streaming API call (I/O operation)"""
        import httpx
        import json
        
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{config['base_url']}/chat/completions",
                json=body,
                headers={"Authorization": f"Bearer {config['api_key']}"},
                timeout=30.0
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        yield json.loads(data)
```

## Example 2: Provider Extension for Thinking Blocks

```python
# thinking_extension.py

name = "thinking_blocks"
version = "1.0.0"
target_provider = "openai"

def get_config_schema():
    return {
        "extract_thinking": {"type": "boolean", "default": True}
    }

def get_ui_elements():
    return [
        {
            "type": "checkbox",
            "key": "extract_thinking",
            "label": "Show Reasoning Process"
        }
    ]

def init(config):
    return {
        "config": config,
        "runtime_state": {
            "thinking_blocks": [],
            "current_thinking": ""
        }
    }

def update_state(state, updates):
    return {
        **state,
        "config": {**state["config"], **updates}
    }

def process_chunk(native_chunk, provider_state, extension_state):
    """Extract thinking blocks from chunks"""
    if not extension_state["config"]["extract_thinking"]:
        return "", extension_state
    
    # Check for thinking block markers
    delta = native_chunk.get("choices", [{}])[0].get("delta", {})
    content = delta.get("content", "")
    
    # Simple example: detect <thinking>...</thinking> tags
    if "<thinking>" in content:
        new_state = {
            **extension_state,
            "runtime_state": {
                **extension_state["runtime_state"],
                "in_thinking": True
            }
        }
        return "", new_state
    
    if extension_state["runtime_state"].get("in_thinking"):
        if "</thinking>" in content:
            # End of thinking block
            thinking = extension_state["runtime_state"]["current_thinking"]
            new_state = {
                **extension_state,
                "runtime_state": {
                    **extension_state["runtime_state"],
                    "thinking_blocks": extension_state["runtime_state"]["thinking_blocks"] + [thinking],
                    "current_thinking": "",
                    "in_thinking": False
                }
            }
            return "", new_state
        else:
            # Accumulate thinking content
            new_state = {
                **extension_state,
                "runtime_state": {
                    **extension_state["runtime_state"],
                    "current_thinking": extension_state["runtime_state"]["current_thinking"] + content
                }
            }
            return "", new_state
    
    return "", extension_state

def enhance_final_message(message, metadata, state):
    """Add thinking blocks to metadata"""
    thinking_blocks = state["runtime_state"]["thinking_blocks"]
    
    if thinking_blocks:
        enhanced_metadata = {
            **metadata,
            "thinking_blocks": thinking_blocks
        }
        return message, enhanced_metadata
    
    return message, metadata
```

## Example 3: Web Search Feature with Citations

```python
# web_search_feature.py

name = "web_search"
version = "1.0.0"

def get_config_schema():
    return {
        "web_search_enabled": {"type": "boolean", "default": False},
        "max_results": {"type": "integer", "default": 5}
    }

def get_ui_elements():
    return [
        {
            "type": "checkbox",
            "key": "web_search_enabled",
            "label": "Enable Web Search"
        },
        {
            "type": "number",
            "key": "max_results",
            "label": "Max Results",
            "condition": {"web_search_enabled": True}
        }
    ]

def init(config):
    return {
        "config": config,
        "capabilities": ["web_search"],
        "runtime_state": {}
    }

def update_state(state, updates):
    return {
        **state,
        "config": {**state["config"], **updates}
    }

def can_handle(capability_id, state):
    return (
        capability_id == "web_search" and
        state["config"]["web_search_enabled"]
    )

def modify_request_body(body, state):
    """Add search parameters to request"""
    if not state["config"]["web_search_enabled"]:
        return body
    
    return {
        **body,
        "search": {
            "enabled": True,
            "max_results": state["config"]["max_results"]
        }
    }

def process_final_message(message, conversation_state, state):
    """Extract and format citations from metadata"""
    if "citations" not in message.get("metadata", {}):
        return message
    
    citations = message["metadata"]["citations"]
    
    # Add citation markers to content
    content = message["content"]
    for i, citation in enumerate(citations, 1):
        content += f"\n[{i}] {citation['title']}: {citation['url']}"
    
    return {
        **message,
        "content": content,
        "metadata": {
            **message.get("metadata", {}),
            "formatted_citations": True
        }
    }

def format_display(display, message, state):
    """Enhance display with citation UI"""
    citations = message.get("metadata", {}).get("citations", [])
    
    if citations:
        return {
            **display,
            "citations": citations,
            "has_citations": True
        }
    
    return display
```

## Example 4: File Reader Tool Plugin

```python
# file_reader_tool.py
import os

name = "file_reader"
version = "1.0.0"

def get_config_schema():
    return {
        "allowed_paths": {
            "type": "array",
            "items": {"type": "string"},
            "default": ["."],
            "description": "Allowed base paths for file reading"
        },
        "max_file_size": {
            "type": "integer",
            "default": 1048576,  # 1MB
            "description": "Maximum file size in bytes"
        }
    }

def get_ui_elements():
    return [
        {
            "type": "text",
            "key": "allowed_paths",
            "label": "Allowed Paths (comma-separated)"
        }
    ]

def init(config):
    return {
        "config": config,
        "runtime_state": {}
    }

def update_state(state, updates):
    return {
        **state,
        "config": {**state["config"], **updates}
    }

def get_tool_schemas(state):
    """Return tool definition for LLM"""
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
                            "description": "Path to the file to read"
                        }
                    },
                    "required": ["file_path"]
                }
            }
        }
    ]

def execute_tool(tool_name, arguments, state):
    """Execute file read operation"""
    if tool_name != "read_file":
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}"
        }
    
    file_path = arguments.get("file_path")
    
    # Security: Check if path is allowed
    allowed_paths = state["config"]["allowed_paths"]
    if not any(file_path.startswith(base) for base in allowed_paths):
        return {
            "success": False,
            "error": f"Access denied: {file_path} not in allowed paths"
        }
    
    # Check file size
    try:
        file_size = os.path.getsize(file_path)
        if file_size > state["config"]["max_file_size"]:
            return {
                "success": False,
                "error": f"File too large: {file_size} bytes"
            }
    except OSError as e:
        return {
            "success": False,
            "error": f"Cannot access file: {str(e)}"
        }
    
    # Read file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "success": True,
            "result": content
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error reading file: {str(e)}"
        }

def format_tool_result(result, state):
    """Format result for LLM"""
    if result["success"]:
        return f"File contents:\n{result['result']}"
    else:
        return f"Error: {result['error']}"
```
