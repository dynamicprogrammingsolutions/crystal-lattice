from __future__ import annotations

"""Provider extension template (skeleton).

Provider extensions run alongside the provider:

- Hot path: observe/transform per-chunk partials via `process_chunk`
- Cold path: observe/transform finals via `finalize`

This skeleton is intentionally a no-op. Add provider-specific logic (tool call
accumulation, reasoning extraction, citations, caching metadata, etc.).
"""

from typing import Any, Dict, List, Optional, Tuple

from agent_core.types import ProviderExtensionPlugin


class TemplateProviderExtension(ProviderExtensionPlugin):
    name: str = "template_extension"
    version: str = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return []

    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        # TODO: add tags advertised by this extension.
        return []

    def required_tags(self) -> List[str]:
        # TODO: return tags required for this extension to enable.
        return []

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        return list(native_messages), state

    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        return partial_messages, final_messages, native_messages, state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        return final_messages, native_messages, state


__all__ = ["TemplateProviderExtension"]
