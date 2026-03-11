from __future__ import annotations

from plugins.ollama_thinking_extension import OllamaThinkingExtension
from plugins.openai_provider import OpenAICompatibleProvider

from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider
from openai_responses_plugins.openai_responses_reasoning_extension import (
    OpenAIResponsesReasoningExtension,
)
from openai_responses_plugins.openai_responses_tools_extension import (
    OpenAIResponsesToolsExtension,
)
from openai_responses_plugins.openai_responses_verbosity_extension import (
    OpenAIResponsesVerbosityExtension,
)


def test_openai_responses_provider_tags_exclude_openai_compatible_and_ollama_extensions() -> None:
    provider = OpenAIResponsesProvider()
    reasoning = OpenAIResponsesReasoningExtension()
    ollama_thinking = OllamaThinkingExtension()

    provider_tags = provider.get_tags({"model": "gpt-5-mini"}, [{"id": "gpt-5-mini"}])
    available_tags = [*provider_tags, "feature:request_options"]

    assert "openai_responses" in provider_tags
    assert "supports_reasoning" in provider_tags
    assert "supports_thinking" not in provider_tags
    assert "provider:openai_compatible" not in provider_tags

    assert set(reasoning.required_tags()).issubset(available_tags)
    assert not set(ollama_thinking.required_tags()).issubset(provider_tags)


def test_openai_compatible_provider_does_not_activate_openai_responses_extensions() -> None:
    provider = OpenAICompatibleProvider()
    tools = OpenAIResponsesToolsExtension()
    reasoning = OpenAIResponsesReasoningExtension()
    verbosity = OpenAIResponsesVerbosityExtension()

    provider_tags = provider.get_tags(
        {
            "model": "gpt-4.1-mini",
            "api_key": "test-key",
            "base_url": "http://localhost:11434/v1",
        },
        [],
    )
    available_tags = [*provider_tags, "feature:request_options"]

    assert "provider:openai_compatible" in provider_tags
    assert "openai_responses" not in provider_tags

    assert not set(tools.required_tags()).issubset(available_tags)
    assert not set(reasoning.required_tags()).issubset(available_tags)
    assert not set(verbosity.required_tags()).issubset(available_tags)