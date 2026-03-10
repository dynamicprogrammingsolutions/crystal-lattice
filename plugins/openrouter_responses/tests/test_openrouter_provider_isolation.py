"""Test that OpenRouter provider and extensions are properly isolated via tags.

This test verifies that when multiple providers and extensions are registered,
only the ones matching the configured provider (via tag-based dependency resolution)
are enabled, and others are disabled.
"""

from __future__ import annotations

from plugins.openai_provider import OpenAICompatibleProvider
from plugins.ollama_thinking_extension import OllamaThinkingExtension
from openrouter_responses_plugins.openrouter_responses_provider import OpenRouterResponsesProvider
from openrouter_responses_plugins.openrouter_responses_reasoning_extension import OpenRouterResponsesReasoningExtension


def test_openrouter_provider_tags_exclude_ollama_extension():
    """Test that OpenRouter provider tags don't satisfy Ollama extension requirements.

    This test verifies the core isolation mechanism:
    1. OpenRouter (/responses) provider provides: openrouter_responses, supports_reasoning (NOT supports_thinking)
    2. OpenRouter (/responses) reasoning extension requires: openrouter_responses, supports_reasoning → COMPATIBLE
    3. Ollama thinking extension requires: supports_thinking → NOT COMPATIBLE

    This ensures Ollama extension won't be activated with OpenRouter provider.
    """
    openrouter_provider = OpenRouterResponsesProvider()
    openrouter_reasoning = OpenRouterResponsesReasoningExtension()
    ollama_thinking = OllamaThinkingExtension()

    config = {"model": "test", "api_key": "test"}
    models = [{"id": "test", "supported_parameters": ["reasoning", "tools"]}]

    # Get OpenRouter provider tags
    provider_tags = openrouter_provider.get_tags(config, models)
    combined_tags = [*provider_tags, "feature:request_options"]

    print(f"\nOpenRouter provider tags: {provider_tags}")

    # Verify critical tags
    assert "openrouter_responses" in provider_tags, "Must have 'openrouter_responses' tag"
    assert "supports_reasoning" in provider_tags, "Must support reasoning"
    assert "supports_thinking" not in provider_tags, "Must NOT support thinking"

    # OpenRouter reasoning extension should be compatible
    reasoning_required = openrouter_reasoning.required_tags()
    reasoning_compatible = all(tag in combined_tags for tag in reasoning_required)
    assert reasoning_compatible, "OpenRouter reasoning must be compatible"

    print(f"✅ OpenRouter reasoning: COMPATIBLE (requires {reasoning_required})")

    # Ollama thinking extension should NOT be compatible
    ollama_required = ollama_thinking.required_tags()
    ollama_compatible = all(tag in provider_tags for tag in ollama_required)
    assert not ollama_compatible, "Ollama thinking must NOT be compatible"

    print(f"✅ Ollama thinking: INCOMPATIBLE (requires {ollama_required})")
    print("✅ Provider isolation verified: Ollama extension excluded from OpenRouter")


def test_openai_provider_tags_support_ollama_extension():
    """Test that OpenAI provider tags DO satisfy Ollama extension requirements.

    This is a contrast test showing that Ollama extension is compatible with
    OpenAI provider (has supports_thinking) but not with OpenRouter.
    """
    openai_provider = OpenAICompatibleProvider()
    ollama_thinking = OllamaThinkingExtension()

    config = {"model": "test", "api_key": "test", "base_url": "http://localhost:11434/v1"}

    # Get OpenAI provider tags
    provider_tags = openai_provider.get_tags(config, [])

    print(f"\nOpenAI provider tags: {provider_tags}")

    # Should have supports_thinking
    assert "supports_thinking" in provider_tags, "OpenAI must support thinking"

    # Ollama extension should be compatible
    ollama_required = ollama_thinking.required_tags()
    ollama_compatible = all(tag in provider_tags for tag in ollama_required)
    assert ollama_compatible, "Ollama thinking must be compatible with OpenAI"

    print(f"✅ Ollama thinking: COMPATIBLE with OpenAI (requires {ollama_required})")
    print("✅ Contrast verified: Ollama extension works with OpenAI but not OpenRouter")


def test_tag_based_extension_filtering():
    """Test that extensions are filtered based on provider tags.

    This test verifies the core principle:
    - OpenRouter (/responses) provider has 'openrouter_responses' tag
    - OpenRouter (/responses) reasoning extension requires 'openrouter_responses' tag
    - Ollama thinking extension does NOT require 'openrouter' tag but requires 'supports_thinking'
    - Therefore with OpenRouter, only reasoning extension should be compatible
    """
    openrouter_provider = OpenRouterResponsesProvider()
    openrouter_reasoning = OpenRouterResponsesReasoningExtension()
    openai_provider = OpenAICompatibleProvider()
    ollama_thinking = OllamaThinkingExtension()

    config = {"model": "test", "api_key": "test"}
    models = [{"id": "test", "supported_parameters": ["reasoning", "tools"]}]

    # Get provider tags
    provider_tags = openrouter_provider.get_tags(config, models)
    combined_tags = [*provider_tags, "feature:request_options"]

    print(f"OpenRouter provider tags: {provider_tags}")
    print(f"OpenRouter reasoning required: {openrouter_reasoning.required_tags()}")
    print(f"Ollama thinking required: {ollama_thinking.required_tags()}")

    # Check OpenRouter reasoning extension compatibility
    reasoning_required = openrouter_reasoning.required_tags()
    reasoning_compatible = all(tag in combined_tags for tag in reasoning_required)
    assert (
        reasoning_compatible
    ), "OpenRouter reasoning should be compatible with OpenRouter provider"

    # Check Ollama thinking extension compatibility with OpenRouter
    ollama_required = ollama_thinking.required_tags()
    ollama_compatible_with_openrouter = all(tag in provider_tags for tag in ollama_required)
    assert (
        not ollama_compatible_with_openrouter
    ), "Ollama thinking should NOT be compatible with OpenRouter provider"

    # Verify Ollama IS compatible with OpenAI provider
    openai_tags = openai_provider.get_tags(config, [])
    ollama_compatible_with_openai = all(tag in openai_tags for tag in ollama_required)
    assert (
        ollama_compatible_with_openai
    ), "Ollama thinking SHOULD be compatible with OpenAI provider"

    print("✅ Tag-based extension filtering works correctly")
    print(f"   - OpenRouter reasoning + OpenRouter: compatible={reasoning_compatible}")
    print(f"   - Ollama thinking + OpenRouter: compatible={ollama_compatible_with_openrouter}")
    print(f"   - Ollama thinking + OpenAI: compatible={ollama_compatible_with_openai}")


def test_openrouter_specific_tag_requirement():
    """Test that 'openrouter_responses' tag isolates /responses extensions."""
    openrouter_reasoning = OpenRouterResponsesReasoningExtension()

    required_tags = openrouter_reasoning.required_tags()

    # Must require provider-specific tag for proper isolation
    assert (
        "openrouter_responses" in required_tags
    ), "OpenRouter /responses reasoning must require 'openrouter_responses' tag"
    assert (
        "supports_reasoning" in required_tags
    ), "OpenRouter reasoning must require 'supports_reasoning' tag"
    assert (
        "feature:request_options" in required_tags
    ), "OpenRouter reasoning must require 'feature:request_options' tag"

    # Should have exactly these three requirements
    assert len(required_tags) == 3, "Should require exactly 3 tags"

    print("✅ OpenRouter /responses reasoning extension properly requires provider tag")
    print(f"   Required tags: {required_tags}")
