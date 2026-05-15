"""Tests for available-tools discovery and request-time tool gating."""

from __future__ import annotations

from typing import Any, Dict, Iterator, List, Optional, Tuple

from agent_core import AgentCore, ToolDescriptor
from agent_core.types import FeaturePlugin, ProviderPlugin
from plugins.openai_tools_extension import OpenAIToolsExtension
from plugins.tool_gating_feature import ToolGatingFeature

from .dummy_tool import DummyCalculator


class RecordingOpenAIProvider(ProviderPlugin):
    """Test provider that records the final request payload in assistant metadata."""

    name = "recording_openai_provider"
    version = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {"model": {"type": "string", "required": True}}

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        return []

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": dict(config)}

    def get_tags(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[str]:
        return ["provider:openai_compatible", "supports_tools"]

    def to_native_messages(
        self,
        messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        return list(messages)

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        return list(native_messages)

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        config = state.get("config") or {}
        payload = {"model": config.get("model", "test-model")}
        return list(native_messages), {
            **state,
            "request": {"payload": payload},
        }

    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        payload = dict((state.get("request") or {}).get("payload") or {})
        assistant = {
            "role": "assistant",
            "content": "ok",
            "metadata": {"payload": payload},
        }
        return [], [assistant], [*native_messages, assistant], state

    def stream_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Iterator[Dict[str, Any]]:
        yield from []


class AvailableToolsUiFeature(FeaturePlugin):
    """Expose the available tool catalog through UI schema for testing."""

    name = "available_tools_ui_feature"
    version = "1.0.0"

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        available_tools = (
            context.get("available_tools") if isinstance(context, dict) else []
        )
        effective_tools = context.get("tools") if isinstance(context, dict) else []
        names = [
            descriptor.tool_name
            for descriptor in (available_tools or [])
            if isinstance(descriptor, ToolDescriptor)
        ]
        effective_names = [
            descriptor.tool_name
            for descriptor in (effective_tools or [])
            if isinstance(descriptor, ToolDescriptor)
        ]
        return [
            {
                "ui_type": "config",
                "key": "available_tools_summary",
                "label": ",".join(names),
                "description": ",".join(effective_names),
            }
        ]


def _core() -> AgentCore:
    core = AgentCore()
    core.register_provider(RecordingOpenAIProvider, extensions=[OpenAIToolsExtension])
    core.register_tool(DummyCalculator)
    return core


def test_get_available_tools_returns_normalized_descriptors() -> None:
    core = _core()

    available_tools = core.get_available_tools({"model": "test-model"})

    assert [descriptor.tool_name for descriptor in available_tools] == ["add"]
    assert available_tools[0].plugin_name == "dummy_calculator"
    assert available_tools[0].schema["function"]["name"] == "add"
    assert available_tools[0].metadata["tool_kind"] == "function"


def test_get_ui_schema_passes_available_tools_in_context() -> None:
    core = _core()
    core.register_feature(AvailableToolsUiFeature)

    schema = core.get_ui_schema({"model": "test-model"})

    summary = next(
        item for item in schema if item.get("key") == "available_tools_summary"
    )
    assert summary["label"] == "add"
    assert summary["description"] == "add"


def test_disable_all_tools_filters_effective_tool_schemas() -> None:
    core = _core()
    core.register_feature(ToolGatingFeature)

    config = {"model": "test-model", "disable_all_tools": True}

    assert [
        descriptor.tool_name for descriptor in core.get_available_tools(config)
    ] == ["add"]
    assert core.get_tool_schemas(config) == []


def test_disable_all_tools_omits_tools_from_request_payload() -> None:
    core = _core()
    core.register_feature(ToolGatingFeature)

    enabled_config = {"model": "test-model"}
    enabled_session = core.create_session()
    enabled_session = core.add_message(
        enabled_session, "user", "hello", config=enabled_config
    )
    _enabled_session, enabled_finals = core.send_request(
        enabled_session, enabled_config
    )
    enabled_payload = enabled_finals[-1]["metadata"]["payload"]
    assert enabled_payload["tools"][0]["function"]["name"] == "add"
    assert enabled_payload["tool_choice"] == "auto"

    disabled_config = {"model": "test-model", "disable_all_tools": True}
    disabled_session = core.create_session()
    disabled_session = core.add_message(
        disabled_session, "user", "hello", config=disabled_config
    )
    _disabled_session, disabled_finals = core.send_request(
        disabled_session, disabled_config
    )
    disabled_payload = disabled_finals[-1]["metadata"]["payload"]
    assert "tools" not in disabled_payload
    assert "tool_choice" not in disabled_payload
