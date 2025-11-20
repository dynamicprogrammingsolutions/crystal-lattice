"""
PROJECT_PLAN Example 3: Tool Calls Loop (Ollama)
Preserves original messages and uses FileReaderTool.
"""

import os
import json
from agent_core import AgentCore
from plugins.providers.openai.python.openai_provider import OpenAICompatibleProvider
from examples.example4_file_reader_tool import FileReaderTool


def run_example():
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

    # Loop continues with tool results in conversation


if __name__ == "__main__":
    run_example()
