from __future__ import annotations

import threading
import time

from agent_core.core import AgentCore
from agent_core.model_cache import ModelDiscoveryCache
from agent_core.plugin.provider import ProviderWrapper


class MockProvider:
    name: str = "mock_provider"
    version: str = "1.0.0"
    get_models_call_count = 0

    def get_models(self, config):
        type(self).get_models_call_count += 1
        return [{"id": config.get("model", "default")}]


class AlternateMockProvider(MockProvider):
    name: str = "alternate_mock_provider"


class ModelTransformFeature:
    name: str = "model_transform_feature"
    version: str = "1.0.0"

    def get_models(self, config, models):
        _ = config
        return [{**model, "feature": "transformed"} for model in models]


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


def test_shared_model_cache_reuses_models_across_fresh_cores():
    cache = ModelDiscoveryCache()
    MockProvider.get_models_call_count = 0
    config = {"model": "gpt-4o", "api_key": "test"}

    core1 = AgentCore(model_cache=cache)
    core2 = AgentCore(model_cache=cache)

    models1 = core1._get_models_for_config(ProviderWrapper(MockProvider), config)
    models2 = core2._get_models_for_config(ProviderWrapper(MockProvider), config)

    assert MockProvider.get_models_call_count == 1
    assert models2 == models1


def test_standalone_cores_do_not_share_model_cache_by_default():
    MockProvider.get_models_call_count = 0
    config = {"model": "gpt-4o", "api_key": "test"}

    core1 = AgentCore()
    core2 = AgentCore()

    core1._get_models_for_config(ProviderWrapper(MockProvider), config)
    core2._get_models_for_config(ProviderWrapper(MockProvider), config)

    assert MockProvider.get_models_call_count == 2


def test_shared_model_cache_separates_configs_and_provider_signatures():
    cache = ModelDiscoveryCache()
    MockProvider.get_models_call_count = 0
    AlternateMockProvider.get_models_call_count = 0

    core = AgentCore(model_cache=cache)
    core._get_models_for_config(ProviderWrapper(MockProvider), {"model": "a"})
    core._get_models_for_config(ProviderWrapper(MockProvider), {"model": "b"})
    core._get_models_for_config(ProviderWrapper(AlternateMockProvider), {"model": "a"})

    assert MockProvider.get_models_call_count == 2
    assert AlternateMockProvider.get_models_call_count == 1


def test_shared_model_cache_separates_feature_signatures():
    cache = ModelDiscoveryCache()
    MockProvider.get_models_call_count = 0
    config = {"model": "gpt-4o", "api_key": "test"}

    core_without_feature = AgentCore(model_cache=cache)
    core_with_feature = AgentCore(model_cache=cache)
    core_with_feature.register_feature(ModelTransformFeature)

    models1 = core_without_feature._get_models_for_config(
        ProviderWrapper(MockProvider),
        config,
    )
    models2 = core_with_feature._get_models_for_config(
        ProviderWrapper(MockProvider),
        config,
    )

    assert MockProvider.get_models_call_count == 2
    assert models1 == [{"id": "gpt-4o"}]
    assert models2 == [{"id": "gpt-4o", "feature": "transformed"}]


def test_empty_model_results_use_shorter_ttl():
    now = 100.0

    def clock() -> float:
        return now

    cache = ModelDiscoveryCache(
        success_ttl_seconds=1000.0,
        empty_ttl_seconds=1.0,
        clock=clock,
    )
    calls = 0

    def compute():
        nonlocal calls
        calls += 1
        return []

    assert cache.get_or_compute(("empty",), compute) == []
    assert cache.get_or_compute(("empty",), compute) == []
    assert calls == 1

    now = 101.1
    assert cache.get_or_compute(("empty",), compute) == []
    assert calls == 2


def test_model_cache_does_not_cache_exceptions():
    cache = ModelDiscoveryCache()
    calls = 0

    def fail_then_succeed():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("temporary failure")
        return [{"id": "recovered"}]

    try:
        cache.get_or_compute(("flaky",), fail_then_succeed)
    except RuntimeError:
        pass

    assert cache.get_or_compute(("flaky",), fail_then_succeed) == [
        {"id": "recovered"}
    ]
    assert calls == 2


def test_model_cache_single_flight_for_concurrent_callers():
    cache = ModelDiscoveryCache()
    calls = 0
    lock = threading.Lock()
    release = threading.Event()

    def compute():
        nonlocal calls
        with lock:
            calls += 1
        release.wait(timeout=5)
        return [{"id": "shared"}]

    results = []

    def worker():
        results.append(cache.get_or_compute(("same",), compute))

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for thread in threads:
        thread.start()

    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        with lock:
            if calls == 1:
                break
        time.sleep(0.01)

    release.set()
    for thread in threads:
        thread.join(timeout=5)

    assert calls == 1
    assert results == [[{"id": "shared"}]] * 5
