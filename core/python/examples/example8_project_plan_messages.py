"""
PROJECT_PLAN Example 4: Message History Manipulation (Ollama)
Preserves original message sequence and edits.
"""

import os
from agent_core import AgentCore
from plugins.openai_provider import OpenAICompatibleProvider
from agent_core.types import Session


def run_example():
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


if __name__ == "__main__":
    run_example()
