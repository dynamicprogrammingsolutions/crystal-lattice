from __future__ import annotations

from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider
from openai_responses_plugins.openai_responses_reasoning_extension import (
    OpenAIResponsesReasoningExtension,
)
from openai_responses_plugins.openai_responses_tools_extension import OpenAIResponsesToolsExtension
from openai_responses_plugins.openai_responses_usage_extension import OpenAIResponsesUsageExtension
from openai_responses_plugins.openai_responses_verbosity_extension import (
    OpenAIResponsesVerbosityExtension,
)


def test_provider_metadata_and_tags() -> None:
    provider = OpenAIResponsesProvider()
    assert provider.name == "openai_responses"
    assert provider.version == "0.1.0"

    schema = provider.get_config_schema()
    assert "model" in schema
    assert "api_key" in schema
    assert "base_url" in schema
    assert "timeout" in schema

    tags = provider.get_tags({"model": "gpt-5-mini"}, [{"id": "gpt-5-mini"}])
    assert "provider:openai_responses" in tags
    assert "openai_responses" in tags
    assert "supports_streaming" in tags


def test_extension_metadata_and_required_tags() -> None:
    tools = OpenAIResponsesToolsExtension()
    reasoning = OpenAIResponsesReasoningExtension()
    usage = OpenAIResponsesUsageExtension()
    verbosity = OpenAIResponsesVerbosityExtension()

    assert tools.name == "openai_responses_tools"
    assert reasoning.name == "openai_responses_reasoning"
    assert usage.name == "openai_responses_usage"
    assert verbosity.name == "openai_responses_verbosity"

    assert tools.required_tags() == ["openai_responses", "supports_tools"]
    assert reasoning.required_tags() == [
        "openai_responses",
        "supports_reasoning",
        "feature:request_options",
    ]
    assert usage.required_tags() == ["openai_responses"]
    assert verbosity.required_tags() == ["openai_responses", "supports_verbosity"]
