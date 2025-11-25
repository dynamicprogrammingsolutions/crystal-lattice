"""Tests for tag-based plugin dependency resolution in AgentCore.

These tests exercise the internal `_resolve_plugins_for_config` method using
simple dummy providers, extensions, features, and tools with predictable
`get_models`, `get_tags`, and `required_tags` behavior.

The focus is on:
- Extension-provided tags enabling dependent features
- Multi-step dependency chains (A depends on B, B depends on C)
- Provider-only tags enabling or disabling features/tools
- Caching of `get_models` / `get_tags` across repeated resolutions
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Tuple

from agent_core import AgentCore


# ---------------------------------------------------------------------------
# Shared helpers / minimal protocol implementations
# ---------------------------------------------------------------------------


@dataclass
class BasicDependencyProvider:
    """Minimal provider for dependency resolution tests.

    - Returns a single model whose id is taken from config["model"] or a
      default.
    - Emits provider tags based on simple config flags so tests can drive
      which capabilities are present.
    """

    name: str = "dep_provider"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:  # pragma: no cover - unused
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:  # pragma: no cover
        return []

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": dict(config)}

    def get_models(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        model = config.get("model", "default-model")
        return [{"id": str(model)}]

    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        tags: List[str] = ["provider:dep_provider"]
        if config.get("enable_extension"):
            tags.append("enable_extension")
        if config.get("supports_tools"):
            tags.append("supports_tools")
        if config.get("supports_reasoning"):
            tags.append("supports_reasoning")
        return tags

    # The remaining methods are not used by these tests but are provided to
    # keep the provider structurally compatible with the protocol.

    def to_native_messages(
        self, messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:  # pragma: no cover - unused
        return list(messages)

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:  # pragma: no cover - unused
        return list(native_messages)

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:  # pragma: no cover - unused
        return state

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
    ]:  # pragma: no cover - unused
        return [], [], native_messages, state

    def finalize(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:  # pragma: no cover - unused
        return [], native_messages, state

    def to_display_format(
        self, message: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:  # pragma: no cover - unused
        return message

    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        Dict[str, Any],
    ]:  # pragma: no cover - unused
        return [], [], native_messages, state

    def stream_api(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:  # pragma: no cover - unused
        if False:
            yield {}
        return


# ---------------------------------------------------------------------------
# Dummy extensions / features / tools for specific scenarios
# ---------------------------------------------------------------------------


class StreamingExtension:
    """Extension that advertises streaming support via a tag.

    Provides tag ``"supports_streaming"``; has no tag requirements.
    """

    name: str = "streaming_extension"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:  # pragma: no cover - unused
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:  # pragma: no cover
        return []

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def get_models(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return list(models)

    def get_tags(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[str]:
        return ["supports_streaming"]

    def required_tags(self) -> List[str]:
        return []

    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:  # pragma: no cover - unused
        return native_messages

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:  # pragma: no cover - unused
        return messages

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:  # pragma: no cover - unused
        return state

    def process_chunk(
        self,
        native_chunk,
        state: Dict[str, Any],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
    ) -> Tuple[
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        Dict[str, Any],
    ]:  # pragma: no cover - unused
        return partial_messages, final_messages, native_messages, state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:  # pragma: no cover - unused
        return final_messages, native_messages, state


class StreamingFeature:
    """Feature that requires streaming support and advertises its own tag."""

    name: str = "streaming_feature"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:  # pragma: no cover - unused
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:  # pragma: no cover
        return []

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def get_models(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return list(models)

    def get_tags(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[str]:
        return ["feature:streaming"]

    def required_tags(self) -> List[str]:
        return ["supports_streaming"]

    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:  # pragma: no cover - unused
        return native_messages

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:  # pragma: no cover - unused
        return messages

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:  # pragma: no cover - unused
        return state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:  # pragma: no cover - unused
        return final_messages, native_messages, state


class ConditionalExtension:
    """Extension enabled only when provider emits "enable_extension" tag.

    When enabled, it contributes tag ``"ext:conditional"`` used by
    ConditionalFeature below.
    """

    name: str = "conditional_extension"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:  # pragma: no cover - unused
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:  # pragma: no cover
        return []

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def get_models(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return list(models)

    def get_tags(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[str]:
        return ["ext:conditional"]

    def required_tags(self) -> List[str]:
        return ["enable_extension"]

    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:  # pragma: no cover - unused
        return native_messages

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:  # pragma: no cover - unused
        return messages

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:  # pragma: no cover - unused
        return state

    def process_chunk(
        self,
        native_chunk,
        state: Dict[str, Any],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
    ) -> Tuple[
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        Dict[str, Any],
    ]:  # pragma: no cover - unused
        return partial_messages, final_messages, native_messages, state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:  # pragma: no cover - unused
        return final_messages, native_messages, state


class ConditionalFeature:
    """Feature that depends on ConditionalExtension's tag."""

    name: str = "conditional_feature"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:  # pragma: no cover - unused
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:  # pragma: no cover
        return []

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def get_models(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return list(models)

    def get_tags(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[str]:
        return ["feature:conditional"]

    def required_tags(self) -> List[str]:
        return ["ext:conditional"]

    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:  # pragma: no cover - unused
        return native_messages

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:  # pragma: no cover - unused
        return messages

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:  # pragma: no cover - unused
        return state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:  # pragma: no cover - unused
        return final_messages, native_messages, state


class ToolsFeature:
    """Feature that requires provider tool support and advertises its tag."""

    name: str = "tools_feature"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:  # pragma: no cover - unused
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:  # pragma: no cover
        return []

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def get_models(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return list(models)

    def get_tags(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[str]:
        return ["feature:tools"]

    def required_tags(self) -> List[str]:
        return ["supports_tools"]

    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:  # pragma: no cover - unused
        return native_messages

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:  # pragma: no cover - unused
        return messages

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:  # pragma: no cover - unused
        return state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:  # pragma: no cover - unused
        return final_messages, native_messages, state


class DummyTool:
    """Tool that requires provider/tool support via tags."""

    name: str = "dummy_tool"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:  # pragma: no cover - unused
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:  # pragma: no cover
        return []

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": dict(config)}

    def get_tags(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[str]:
        return ["tool:dummy"]

    def required_tags(self) -> List[str]:
        return ["supports_tools"]

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "do_dummy",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]

    def execute_tool(
        self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:  # pragma: no cover - unused
        return {"success": True, "result": None}

    def format_tool_result(
        self, result: Dict[str, Any], state: Dict[str, Any]
    ) -> str:  # pragma: no cover - unused
        return "ok"


# Complex dependency graph: A -> B -> C, where C provides the root tag.


class RootFeatureC:
    """Root feature C that provides a base tag for the chain."""

    name: str = "feature_c_root"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:  # pragma: no cover
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:  # pragma: no cover
        return []

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def get_models(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return list(models)

    def get_tags(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[str]:
        # C provides the base capability for the chain.
        return ["tag:c"]

    def required_tags(self) -> List[str]:
        # No requirements; always eligible when registered.
        return []

    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:  # pragma: no cover
        return native_messages

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:  # pragma: no cover
        return messages

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:  # pragma: no cover
        return state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:  # pragma: no cover
        return final_messages, native_messages, state


class MidFeatureB:
    """Intermediate feature B that depends on C and provides its own tag."""

    name: str = "feature_b_mid"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:  # pragma: no cover
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:  # pragma: no cover
        return []

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def get_models(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return list(models)

    def get_tags(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[str]:
        return ["tag:b"]

    def required_tags(self) -> List[str]:
        return ["tag:c"]

    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:  # pragma: no cover
        return native_messages

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:  # pragma: no cover
        return messages

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:  # pragma: no cover
        return state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:  # pragma: no cover
        return final_messages, native_messages, state


class TopFeatureA:
    """Top-level feature A that depends on B.

    Required tag chain: A -> B -> C, with C providing the root tag.
    """

    name: str = "feature_a_top"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:  # pragma: no cover
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:  # pragma: no cover
        return []

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def get_models(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return list(models)

    def get_tags(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[str]:
        return ["tag:a"]

    def required_tags(self) -> List[str]:
        return ["tag:b"]

    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:  # pragma: no cover
        return native_messages

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:  # pragma: no cover
        return messages

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:  # pragma: no cover
        return state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:  # pragma: no cover
        return final_messages, native_messages, state


# Circular-ish dependency example: X depends on Y, Y depends on X.


class FeatureX:
    name: str = "feature_x"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:  # pragma: no cover
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:  # pragma: no cover
        return []

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def get_models(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return list(models)

    def get_tags(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[str]:
        return ["tag:x"]

    def required_tags(self) -> List[str]:
        return ["tag:y"]

    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:  # pragma: no cover
        return native_messages

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:  # pragma: no cover
        return messages

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:  # pragma: no cover
        return state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:  # pragma: no cover
        return final_messages, native_messages, state


class FeatureY:
    name: str = "feature_y"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:  # pragma: no cover
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:  # pragma: no cover
        return []

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def get_models(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return list(models)

    def get_tags(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[str]:
        return ["tag:y"]

    def required_tags(self) -> List[str]:
        return ["tag:x"]

    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:  # pragma: no cover
        return native_messages

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:  # pragma: no cover
        return messages

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:  # pragma: no cover
        return state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:  # pragma: no cover
        return final_messages, native_messages, state


# Provider with counters for caching tests


class CountingProvider:
    name: str = "counting_provider"
    version: str = "1.0.0"

    models_calls: int = 0
    tags_calls: int = 0

    def get_config_schema(self) -> Dict[str, Any]:  # pragma: no cover
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:  # pragma: no cover
        return []

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": dict(config)}

    def get_models(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        type(self).models_calls += 1
        model = config.get("model", "default")
        return [{"id": str(model)}]

    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        type(self).tags_calls += 1
        return ["provider:counting"]

    def to_native_messages(
        self, messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:  # pragma: no cover
        return messages

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:  # pragma: no cover
        return native_messages

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:  # pragma: no cover
        return state

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
    ]:  # pragma: no cover
        return [], [], native_messages, state

    def finalize(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:  # pragma: no cover
        return [], native_messages, state

    def to_display_format(
        self, message: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:  # pragma: no cover
        return message

    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        Dict[str, Any],
    ]:  # pragma: no cover
        return [], [], native_messages, state

    def stream_api(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:  # pragma: no cover
        if False:
            yield {}
        return


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_extension_tag_enables_dependent_feature() -> None:
    """Extension's tag makes a dependent feature eligible.

    - StreamingExtension contributes "supports_streaming".
    - StreamingFeature requires "supports_streaming".
    """

    core = AgentCore()
    core.register_provider(BasicDependencyProvider, extensions=[StreamingExtension])
    core.register_feature(StreamingFeature)

    config: Dict[str, Any] = {"model": "m1"}
    provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)  # type: ignore[attr-defined]

    assert provider.name == "dep_provider"
    assert [e.name for e in exts] == ["streaming_extension"]
    assert [f.name for f in feats] == ["streaming_feature"]
    assert tools == []
    assert "supports_streaming" in tags
    assert "feature:streaming" in tags


def test_conditional_extension_and_feature_chain_based_on_provider_tag() -> None:
    """Feature requires tag from a conditional extension; disabling the
    extension (by removing its required provider tag) disables the feature.

    Provider emits "enable_extension" only when config["enable_extension"] is
    true. ConditionalExtension requires that tag and emits "ext:conditional",
    which ConditionalFeature then requires.
    """

    core = AgentCore()
    core.register_provider(BasicDependencyProvider, extensions=[ConditionalExtension])
    core.register_feature(ConditionalFeature)

    # When provider emits enable_extension, both extension and feature are enabled.
    config_on: Dict[str, Any] = {"model": "m1", "enable_extension": True}
    _prov1, exts1, feats1, _tools1, tags1 = core._resolve_plugins_for_config(config_on)  # type: ignore[attr-defined]

    assert [e.name for e in exts1] == ["conditional_extension"]
    assert [f.name for f in feats1] == ["conditional_feature"]
    assert "enable_extension" in tags1
    assert "ext:conditional" in tags1
    assert "feature:conditional" in tags1

    # Without the provider tag, extension and dependent feature are both disabled.
    config_off: Dict[str, Any] = {"model": "m1", "enable_extension": False}
    _prov2, exts2, feats2, _tools2, tags2 = core._resolve_plugins_for_config(config_off)  # type: ignore[attr-defined]

    assert exts2 == []
    assert feats2 == []
    assert "ext:conditional" not in tags2
    assert "feature:conditional" not in tags2


def test_complex_dependency_chain_a_depends_on_b_depends_on_c() -> None:
    """A three-node dependency graph A -> B -> C behaves as expected.

    - C provides tag "tag:c" (no requirements).
    - B requires "tag:c" and provides "tag:b".
    - A requires "tag:b" and provides "tag:a".

    When C is registered, all three are enabled. When C is missing, B and A
    are both disabled after fixpoint iteration.
    """

    # Case 1: full chain C, B, A registered -> all enabled.
    core_full = AgentCore()
    core_full.register_provider(BasicDependencyProvider)
    core_full.register_feature(RootFeatureC)
    core_full.register_feature(MidFeatureB)
    core_full.register_feature(TopFeatureA)

    config: Dict[str, Any] = {"model": "m1"}
    _prov_f, _exts_f, feats_f, _tools_f, tags_f = core_full._resolve_plugins_for_config(config)  # type: ignore[attr-defined]

    assert {f.name for f in feats_f} == {
        "feature_c_root",
        "feature_b_mid",
        "feature_a_top",
    }
    assert "tag:c" in tags_f
    assert "tag:b" in tags_f
    assert "tag:a" in tags_f

    # Case 2: C is not registered -> B and A lose their requirements transitively.
    core_partial = AgentCore()
    core_partial.register_provider(BasicDependencyProvider)
    core_partial.register_feature(MidFeatureB)
    core_partial.register_feature(TopFeatureA)

    _prov_p, _exts_p, feats_p, _tools_p, tags_p = core_partial._resolve_plugins_for_config(config)  # type: ignore[attr-defined]

    # Neither B nor A should be enabled when the root tag from C is missing.
    assert feats_p == []
    assert "tag:c" not in tags_p
    assert "tag:b" not in tags_p
    assert "tag:a" not in tags_p


def test_circular_dependencies_still_resolve_to_fixpoint() -> None:
    """Two features that depend on each other's tags do not cause divergence.

    FeatureX provides "tag:x" and requires "tag:y".
    FeatureY provides "tag:y" and requires "tag:x".

    The algorithm reaches a fixpoint and keeps both enabled, since their tags
    collectively satisfy both sets of requirements.
    """

    core = AgentCore()
    core.register_provider(BasicDependencyProvider)
    core.register_feature(FeatureX)
    core.register_feature(FeatureY)

    config: Dict[str, Any] = {"model": "m1"}
    _prov, _exts, feats, _tools, tags = core._resolve_plugins_for_config(config)  # type: ignore[attr-defined]

    assert {f.name for f in feats} == {"feature_x", "feature_y"}
    # Both tags should be present in the final tag set.
    assert "tag:x" in tags
    assert "tag:y" in tags


def test_provider_only_tags_enable_features_and_tools() -> None:
    """Provider tags alone control enablement of tools and dependent features.

    - BasicDependencyProvider emits "supports_tools" when config["supports_tools"]
      is True.
    - ToolsFeature and DummyTool both require "supports_tools".
    """

    core = AgentCore()
    core.register_provider(BasicDependencyProvider)
    core.register_feature(ToolsFeature)
    core.register_tool(DummyTool)

    config_on: Dict[str, Any] = {"model": "m1", "supports_tools": True}
    _prov1, _exts1, feats1, tools1, tags1 = core._resolve_plugins_for_config(config_on)  # type: ignore[attr-defined]

    assert {f.name for f in feats1} == {"tools_feature"}
    assert {t.name for t in tools1} == {"dummy_tool"}
    assert "supports_tools" in tags1

    config_off: Dict[str, Any] = {"model": "m1", "supports_tools": False}
    _prov2, _exts2, feats2, tools2, tags2 = core._resolve_plugins_for_config(config_off)  # type: ignore[attr-defined]

    assert feats2 == []
    assert tools2 == []
    assert "supports_tools" not in tags2


def test_dependency_resolution_caches_models_and_tags_per_config() -> None:
    """`_resolve_plugins_for_config` caches `get_models` and `get_tags` calls.

    For the same provider+config, provider.get_models and provider.get_tags are
    only invoked once each, even if resolution is called multiple times.

    Changing the model in config invalidates the cache and causes another
    round of model and tag computation.
    """

    CountingProvider.models_calls = 0
    CountingProvider.tags_calls = 0

    core = AgentCore()
    core.register_provider(CountingProvider)

    config1: Dict[str, Any] = {"model": "m1"}

    # First resolution populates caches.
    _ = core._resolve_plugins_for_config(config1)  # type: ignore[attr-defined]
    # Second resolution should hit both model and dependency caches.
    _ = core._resolve_plugins_for_config(config1)  # type: ignore[attr-defined]

    assert CountingProvider.models_calls == 1
    assert CountingProvider.tags_calls == 1

    # Changing the model should invalidate caches and trigger another round.
    config2: Dict[str, Any] = {"model": "m2"}
    _ = core._resolve_plugins_for_config(config2)  # type: ignore[attr-defined]

    assert CountingProvider.models_calls == 2
    assert CountingProvider.tags_calls == 2
