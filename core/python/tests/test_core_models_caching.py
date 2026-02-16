
from agent_core.core import AgentCore
from agent_core.plugin.provider import ProviderWrapper

class MockProvider:
    name: str = "mock_provider"
    version: str = "1.0.0"
    get_models_call_count = 0

    def get_models(self, config):
        MockProvider.get_models_call_count += 1
        return [{"id": config.get("model", "default")}]

def test_get_models_caching():
    core = AgentCore()
    MockProvider.get_models_call_count = 0
    
    # ProviderWrapper will instantiate MockProvider
    provider = ProviderWrapper(MockProvider)
    
    config = {"model": "gpt-4o", "api_key": "test"}
    
    # First call - should call provider
    models1 = core._get_models_for_config(provider, config)
    assert MockProvider.get_models_call_count == 1
    assert models1[0]["id"] == "gpt-4o"
    
    # Second call with same config - should be cached
    models2 = core._get_models_for_config(provider, config)
    assert MockProvider.get_models_call_count == 1
    assert models2 == models1
    
    # Third call with different config - should call provider again
    config2 = {"model": "claude-3", "api_key": "test"}
    models3 = core._get_models_for_config(provider, config2)
    assert MockProvider.get_models_call_count == 2
    assert models3[0]["id"] == "claude-3"
