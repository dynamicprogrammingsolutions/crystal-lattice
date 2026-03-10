"""Integration tests for OpenRouter models API.

Requires OPENROUTER_API_KEY environment variable.
"""

import os
import pytest

# Load .env file if it exists
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

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

    selected_model = next((model for model in models if model.get("id") == config_reasoning["model"]), None)

    print(
        f"Model: {config_reasoning['model']}, "
        f"Supported Parameters: {selected_model.get('supported_parameters') if selected_model else None}, "
        f"Tags: {tags}"
    )
    
    # Should always have these
    assert "provider:openrouter" in tags
    assert "openrouter" in tags
    assert "supports_streaming" in tags
    
    # Check if model has supported_parameters
    if selected_model and "supported_parameters" in selected_model:
        supported = selected_model["supported_parameters"]
        
        # If model supports reasoning, tag should reflect it
        if "reasoning" in supported:
            assert "supports_reasoning" in tags


@pytest.mark.integration
def test_get_models_returns_empty_on_api_failure():
    """Verify get_models returns an empty list when the API is unavailable."""
    provider = OpenRouterProvider()
    
    # Use invalid base_url to simulate API failure
    config = {
        "model": "test-model",
        "api_key": "invalid",
        "base_url": "https://invalid.example.com",
    }
    
    models = provider.get_models(config)
    
    assert models == []


@pytest.mark.integration  
def test_get_tags_returns_base_tags_when_no_model_data():
    """Verify get_tags returns only base tags when no model data is available."""
    provider = OpenRouterProvider()
    config = {"model": "test-model", "api_key": "invalid"}
    
    # Minimal model without supported_parameters
    models = [{"id": "test-model"}] 
    
    tags = provider.get_tags(config, models)
    
    assert tags == ["provider:openrouter", "openrouter", "supports_streaming"]
