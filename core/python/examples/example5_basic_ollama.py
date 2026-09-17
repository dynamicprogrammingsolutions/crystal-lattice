"""
Example 5: Basic low-level API usage with Ollama.
Configured to call a local Ollama OpenAI-compatible endpoint.

Environment variables (optional):
- OLLAMA_HOST (default: http://localhost:11434)
- OLLAMA_MODEL (default: llama3.2:1b)
"""


def run_example():

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


if __name__ == "__main__":
    run_example()
