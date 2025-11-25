"""
PROJECT_PLAN Example 2: Streaming with Low-Level API
Configured to call a local Ollama OpenAI-compatible endpoint.

Environment variables (optional):
- OLLAMA_HOST (default: http://localhost:11434)
- OLLAMA_MODEL (default: llama3.2:1b)
"""

import os
from agent_core import AgentCore
from plugins.openai_provider import OpenAICompatibleProvider


def run_example():
    # Core stores only pipeline
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


if __name__ == "__main__":
    run_example()
