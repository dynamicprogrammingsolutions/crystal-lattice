import os
from agent_core import AgentCore
from plugins.providers.openai.python.openai_provider import OpenAICompatibleProvider
from agent_core.types import Session


def run_example():
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


if __name__ == "__main__":
    run_example()

