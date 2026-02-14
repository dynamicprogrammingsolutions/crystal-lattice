"""Integration tests for OpenRouter models API.

Requires OPENROUTER_API_KEY environment variable.
"""

import os
import pytest

from openrouter_plugins.openrouter_provider import OpenRouterProvider


@pytest.mark.integration
def test_fetch_models_from_api_success():
    """Fetch models from OpenRouter API and verify structure."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set; skipping models API integration test")
    
    provider = OpenRouterProvider()
    config = {
        "model": "openai/gpt-4o",
        "api_key": api_key,
        "base_url": "https://openrouter.ai/api/v1",
    }
    
    # Fetch models directly via internal method
    models = provider._fetch_models_from_api(config)
    
    # Should return a list of models
    assert isinstance(models, list)
    assert len(models) > 0
    
    # Each model should have required fields
    for model in models[:10]:  # Check first 10
        assert "id" in model
        assert isinstance(model["id"], str)
        # Optional but commonly present fields
        if "supported_parameters" in model:
            assert isinstance(model["supported_parameters"], list)


@pytest.mark.integration
def test_get_models_with_api_caching():
    """Verify get_models fetches from API and caches at provider instance level."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")
    
    provider = OpenRouterProvider()
    config = {
        "model": "openai/gpt-4o",
        "api_key": api_key,
    }
    
    # Provider cache should start empty
    assert provider._api_models_cache is None
    
    # First call should fetch from API
    models1 = provider.get_models(config)
    assert isinstance(models1, list)
    assert len(models1) > 0
    assert models1[0]["id"] == "openai/gpt-4o"
    
    # Provider instance cache should now be populated
    assert provider._api_models_cache is not None
    assert isinstance(provider._api_models_cache, list)
    
    # Second call should use instance cache
    models2 = provider.get_models(config)
    assert models2 == models1


@pytest.mark.integration
def test_get_tags_uses_real_model_capabilities():
    """Verify get_tags detects capabilities from API data."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")
    
    provider = OpenRouterProvider()
    
    # Test with a model known to support reasoning
    config_reasoning = {
        "model": "openai/o1",
        "api_key": api_key,
    }
    
    models = provider.get_models(config_reasoning)
    tags = provider.get_tags(config_reasoning, models)
    
    # Should always have these
    assert "provider:openrouter" in tags
    assert "openrouter" in tags
    assert "supports_streaming" in tags
    
    # Check if model has supported_parameters
    if models and "supported_parameters" in models[0]:
        supported = models[0]["supported_parameters"]
        
        # If model supports reasoning, tag should reflect it
        if "reasoning" in supported:
            assert "supports_reasoning" in tags


@pytest.mark.integration
def test_get_models_fallback_on_api_failure():
    """Verify fallback to minimal model descriptor when API unavailable."""
    provider = OpenRouterProvider()
    
    # Use invalid base_url to simulate API failure
    config = {
        "model": "test-model",
        "api_key": "invalid",
        "base_url": "https://invalid.example.com",
    }
    
    models = provider.get_models(config)
    
    # Should still return minimal model descriptor
    assert isinstance(models, list)
    assert len(models) == 1
    assert models[0]["id"] == "test-model"
    
    # Should NOT have supported_parameters (minimal fallback)
    assert "supported_parameters" not in models[0] or models[0].get("supported_parameters") is None


@pytest.mark.integration  
def test_get_tags_fallback_when_no_model_data():
    """Verify get_tags falls back to common capabilities when no model data."""
    provider = OpenRouterProvider()
    config = {"model": "test-model", "api_key": "invalid"}
    
    # Minimal model without supported_parameters
    models = [{"id": "test-model"}] 
    
    tags = provider.get_tags(config, models)
    
    # Should include fallback tags
    assert "provider:openrouter" in tags
    assert "supports_streaming" in tags
    assert "supports_tools" in tags  # Fallback assumption
    assert "supports_reasoning" in tags  # Fallback assumption
