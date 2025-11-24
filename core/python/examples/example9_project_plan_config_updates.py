"""
PROJECT_PLAN Example 5: Config Updates + Web Search Feature (Ollama)
Preserves original prompts and prints when search is enabled.
"""

import os
from agent_core import AgentCore
from plugins.openai_provider import OpenAICompatibleProvider
from examples.example3_web_search_feature import WebSearchFeature


def run_example():
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


if __name__ == "__main__":
    run_example()
