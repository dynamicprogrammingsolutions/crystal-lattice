"""
Example 11: OpenAI-compatible provider with tool-calling (FileReaderTool) on Ollama.

Requires:
- `ollama` running locally (default http://localhost:11434)
- A model that supports tool/function calling via OpenAI-compatible API

This example performs a simple non-streaming loop:
1) Ask the model to read a file via the read_file tool
2) If the model issues tool calls, the app executes them and appends tool results
3) Repeat until the model stops calling tools
"""

from __future__ import annotations

import os
import tempfile
from typing import Any, Dict, List, Tuple

from agent_core import AgentCore


def run_example() -> Tuple[str, Dict[str, Any]]:
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
    with tempfile.NamedTemporaryFile("w+", delete=False, dir=".") as tf:
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


if __name__ == "__main__":
    content, info = run_example()
    print("Model:", info.get("model"))
    print("Final assistant message:\n", content)
