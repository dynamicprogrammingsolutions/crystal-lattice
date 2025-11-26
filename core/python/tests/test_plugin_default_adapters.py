from __future__ import annotations

from typing import Any, Dict, Iterator, List, Tuple

import pytest

from agent_core.plugin.adapters import (
    FeatureDefaultsAdapter,
    ProviderDefaultsAdapter,
    ProviderExtensionDefaultsAdapter,
    ToolDefaultsAdapter,
)


class _BareProvider:
    name = "bare_provider"
    version = "1.0.0"

    # Required I/O entry points with minimal behavior
    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        Dict[str, Any],
    ]:
        return [], [], list(native_messages), state

    def stream_api(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        return iter(())

    def process_chunk(
        self,
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        Dict[str, Any],
    ]:
        return [], [], list(native_messages), state

    def finalize(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        return [], list(native_messages), state


def test_provider_defaults_adapter_models_and_tags_defaults() -> None:
    provider = ProviderDefaultsAdapter(_BareProvider())
    config: Dict[str, Any] = {"model": "m1"}

    models = provider.get_models(config)
    assert models == [{"id": "m1"}]

    tags = provider.get_tags(config, models)
    assert tags == []


def test_provider_defaults_adapter_message_conversion_defaults() -> None:
    provider = ProviderDefaultsAdapter(_BareProvider())
    state = provider.init({"model": "m1"})

    core_messages = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "there"},
    ]
    native = provider.to_native_messages(core_messages, state)
    assert native == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "there"},
    ]

    # Default from_native_messages should normalize to core messages with metadata
    back = provider.from_native_messages(native, state)
    assert back == [
        {"role": "user", "content": "hi", "metadata": {}},
        {"role": "assistant", "content": "there", "metadata": {}},
    ]


def test_extension_and_feature_default_to_native_identity_on_native_messages() -> None:
    class ExtNoTransforms:
        name = "ext_noop"
        version = "0.0.1"

    class FeatNoTransforms:
        name = "feat_noop"
        version = "0.0.1"

    ext = ProviderExtensionDefaultsAdapter(ExtNoTransforms())
    feat = FeatureDefaultsAdapter(FeatNoTransforms())

    messages = [{"role": "user", "content": "core"}]
    native_messages = [{"role": "assistant", "content": "native"}]

    # to_native_messages must default to returning native_messages, not messages
    assert ext.to_native_messages(messages, native_messages) == native_messages
    assert feat.to_native_messages(messages, native_messages) == native_messages

    # from_native_messages should default to passthrough for core messages
    assert ext.from_native_messages(native_messages, messages) == messages
    assert feat.from_native_messages(native_messages, messages) == messages


def test_tag_and_required_tag_normalization_across_adapters() -> None:
    class WeirdFeature:
        name = "weird_feature"
        version = "1.0.0"

        def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> Any:
            # Return a dict to exercise _safe_list path
            return {"a": 1, "b": 2}

        def required_tags(self) -> Any:
            return ("x", "y")

    feat = FeatureDefaultsAdapter(WeirdFeature())
    tags = feat.get_tags({}, [])
    # dict -> list(keys) -> strings
    assert sorted(tags) == ["a", "b"]

    req = feat.required_tags()
    assert sorted(req) == ["x", "y"]


def test_tool_defaults_adapter_execute_and_format_defaults() -> None:
    class BareTool:
        name = "bare_tool"
        version = "1.0.0"

    tool = ToolDefaultsAdapter(BareTool())
    state = tool.init({"foo": "bar"})
    assert state == {"config": {"foo": "bar"}}

    # Unknown tool when execute_tool is missing
    result = tool.execute_tool("do_thing", {"x": 1}, state)
    assert result["success"] is False
    assert "Unknown tool" in str(result.get("error", ""))

    formatted = tool.format_tool_result(result, state)
    assert formatted.startswith("Error:")

    # Success formatting when plugin returns a dict with success=True
    ok_result = {"success": True, "result": 42}
    assert tool.format_tool_result(ok_result, state) == "Result: 42"


def test_tool_defaults_adapter_normalizes_get_tool_schemas() -> None:
    class WeirdSchemasTool:
        name = "schemas_tool"
        version = "1.0.0"

        def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
            return {"config": config}

        def get_tool_schemas(self, state: Dict[str, Any]) -> Any:
            # Return a tuple with a mix of dicts and non-dicts
            return (
                {"type": "function", "function": {"name": "ok"}},
                "ignore-me",
            )

        def execute_tool(
            self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]
        ) -> Dict[str, Any]:
            return {"success": True, "result": None}

        def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
            return "ok"

    tool = ToolDefaultsAdapter(WeirdSchemasTool())
    state = tool.init({})

    schemas = tool.get_tool_schemas(state)
    assert schemas == [{"type": "function", "function": {"name": "ok"}}]


@pytest.mark.parametrize("adapter_cls", [ProviderExtensionDefaultsAdapter, FeatureDefaultsAdapter])
def test_adapter_init_and_initialize_request_default_passthrough(adapter_cls: Any) -> None:
    class NoLifecycle:
        name = "no_lifecycle"
        version = "0.0.1"

    adapter = adapter_cls(NoLifecycle())
    state: Dict[str, Any] = {"k": "v"}
    config: Dict[str, Any] = {"x": 1}

    # init should return the same state by default
    new_state = adapter.init(config, state)
    assert new_state is state

    # initialize_request should also default to passthrough
    newer_state = adapter.initialize_request([], state)
    assert newer_state is state
