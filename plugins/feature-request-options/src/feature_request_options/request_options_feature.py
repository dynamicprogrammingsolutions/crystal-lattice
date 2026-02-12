"""
RequestOptionsFeature plugin.

Merges arbitrary request options from config into the OpenAI-compatible
provider request payload during initialize_request.

Config keys (flat, optional):
- request_options: dict[Any, Any]  # merged into state["request"]["payload"]

This keeps the feature simple and provider-agnostic while working
naturally with the OpenAI-compatible provider (which reads
state["request"]["payload"] when building the JSON body).
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from agent_core.types import FeaturePlugin


class RequestOptionsFeature(FeaturePlugin):
    """Feature plugin that injects request options into provider payload.

    The application supplies a flat config containing ``request_options``:

    .. code-block:: python

        config = {
            "model": "gpt-4o",
            "base_url": "https://api.openai.com/v1",
            "request_options": {"temperature": 0.3, "max_tokens": 512},
        }

    During :meth:`initialize_request`, the plugin merges these options into
    ``state["request"]["payload"]`` so the provider call can include any
    additional OpenAI-style parameters. Keys from ``request_options``
    override existing payload keys.
    """

    name: str = "request_options"
    version: str = "0.1.0"
    priority: int = 200  # Run after extensions that prepare request_options (e.g., verbosity, reasoning)

    # ---- Config / UI ----
    def get_config_schema(self) -> Dict[str, Any]:
        """Return JSON schema for this feature's configuration.

        Only a single key is used:
        - ``request_options``: arbitrary mapping merged into request payload.
        """

        return {
            "request_options": {
                "type": "object",
                "default": {},
                "description": (
                    "Additional request JSON options merged into the provider "
                    "payload during initialize_request. Keys override any "
                    "existing payload values."
                ),
            }
        }

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        # No dedicated UI; configuration is JSON-only for now.
        return []

    # Uses adapter default get_models (no-op on models)

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        """Identify this feature for dependency resolution."""
        return ["feature:request_options"]

    def required_tags(self) -> List[str]:
        """This feature does not require any specific tags."""
        return []

    # ---- Lifecycle ----
    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Merge config into shared state.

        The plugin itself remains stateless; request options are read from
        ``state["config"]`` during :meth:`initialize_request`.
        """

        return {**state, "config": {**state.get("config", {}), **config}}

    # ---- Stateless transforms (no-ops for this feature) ----
    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return native_messages

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return messages

    # ---- Request initialization ----
    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:

        """Merge ``request_options`` from config into request payload.

        Works best with the OpenAI-compatible provider, which expects
        ``state["request"]`` to contain ``{"url", "payload", "headers", "timeout"}``.
        If either the request structure or ``request_options`` are missing,
        the state and native_messages are returned unchanged.
        """

        config = state.get("config", {})
        options = config.get("request_options")
        if not isinstance(options, dict) or not options:
            return native_messages, state

        request = state.get("request") or {}
        payload = dict(request.get("payload", {}))

        # Merge arbitrary request options, letting them override existing keys.
        merged_payload = {**payload, **options}

        new_state: Dict[str, Any] = {
            **state,
            "request": {**request, "payload": merged_payload},
        }
        return native_messages, new_state


    # ---- Finalize (no-op) ----
    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        return final_messages, native_messages, state
