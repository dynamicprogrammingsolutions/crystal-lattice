"""
RequestOptionsFeature plugin.

Merges arbitrary request options from config into the OpenAI-compatible
provider request payload during initialize_request.

Config keys (flat, optional):
- request_options: dict[Any, Any]  # merged into state["request"]["payload"]
- request_options_ui: dict[str, Any]  # defines UI controls for request_options

When request_options_ui is defined, the plugin generates:
- Flat config keys like "request_options__temperature" in get_config_schema()
- UI elements with flat keys in get_ui_elements()
- During init(), flat keys are extracted and merged into request_options

This keeps the feature simple and provider-agnostic while working
naturally with the OpenAI-compatible provider (which reads
state["request"]["payload"] when building the JSON body).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

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

    For dynamic UI controls, add ``request_options_ui``:

    .. code-block:: python

        config = {
            "request_options": {"temperature": 0.7},
            "request_options_ui": {
                "temperature": "number",
                "max_tokens": ["512", "1024", "2048"],
            }
        }

    This generates flat config keys like ``request_options__temperature``
    and UI elements with those keys. During ``init()``, flat keys are
    extracted and merged into ``request_options``.

    During :meth:`initialize_request`, the plugin merges these options into
    ``state["request"]["payload"]`` so the provider call can include any
    additional OpenAI-style parameters. Keys from ``request_options``
    override existing payload keys.
    """

    name: str = "request_options"
    version: str = "0.2.0"
    priority: int = 200  # Run after extensions that prepare request_options (e.g., verbosity, reasoning)

    # Prefix for flat UI keys
    FLAT_KEY_PREFIX: str = "request_options__"

    # ---- Config / UI ----
    def _generate_flat_schema_entry(
        self, option_name: str, ui_spec: Any
    ) -> Dict[str, Any] | None:
        """Generate a flat config schema entry for a request_options_ui item.

        Args:
            option_name: The option name (e.g., "temperature")
            ui_spec: The UI spec (array for select, "string", or "number")

        Returns:
            Schema entry dict or None if spec is invalid
        """
        if isinstance(ui_spec, list):
            # Array → select dropdown with enum
            options = [str(v) for v in ui_spec if isinstance(v, str)]
            if options:
                return {
                    "type": "string",
                    "enum": options,
                    "description": f"UI select for request_options.{option_name}",
                }
        elif ui_spec == "string":
            return {
                "type": "string",
                "description": f"UI text input for request_options.{option_name}",
            }
        elif ui_spec == "number":
            return {
                "type": "number",
                "description": f"UI number input for request_options.{option_name}",
            }
        return None

    def get_config_schema(self) -> Dict[str, Any]:
        """Return JSON schema for this feature's configuration.

        Keys used by this feature:
        - ``request_options``: arbitrary mapping merged into request payload.
        - ``request_options_ui``: declarative UI element definitions that
          generate flat config keys like ``request_options__temperature``.
        """

        # Base schema with the two main keys
        schema: Dict[str, Any] = {
            "request_options": {
                "type": "object",
                "default": {},
                "description": (
                    "Additional request JSON options merged into the provider "
                    "payload during initialize_request. Keys override any "
                    "existing payload values."
                ),
            },
            "request_options_ui": {
                "type": "object",
                "default": {},
                "description": (
                    "Declarative UI element definitions that generate flat "
                    "config keys. Each key names a request_options field: "
                    "array values create select dropdowns (enum), 'string' "
                    "creates text input, 'number' creates number input. "
                    "Generated flat keys use the prefix 'request_options__'."
                ),
                "additionalProperties": {
                    "oneOf": [
                        {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Options for a select dropdown",
                        },
                        {
                            "type": "string",
                            "enum": ["string", "number"],
                            "description": "Input type: 'string' for text, 'number' for numeric",
                        },
                    ]
                },
            },
        }

        return schema

    @staticmethod
    def _generate_ui_elements_from_options(
        options_config: Dict[str, Any],
        key_prefix: str = "request_options__",
    ) -> List[Dict[str, Any]]:
        """Generate UI elements from request_options_ui config.

        Args:
            options_config: Dict mapping keys to:
                - list of strings → select dropdown
                - "string" → text input
                - "number" → number input
            key_prefix: Prefix for generated element keys

        Returns:
            List of UI element dictionaries with flat keys for get_ui_elements().
        """
        elements: List[Dict[str, Any]] = []

        for key, value in (options_config or {}).items():
            if not isinstance(key, str) or not key:
                continue

            # Convert snake_case key to Title Case label
            label = key.replace("_", " ").title()
            flat_key = f"{key_prefix}{key}"

            if isinstance(value, list):
                # Array → select dropdown
                options = [
                    {"value": str(v), "label": str(v)}
                    for v in value
                    if isinstance(v, str)
                ]
                if options:
                    elements.append({
                        "type": "select",
                        "key": flat_key,
                        "label": label,
                        "options": options,
                    })
            elif value == "string":
                # String type → text input
                elements.append({
                    "type": "text",
                    "key": flat_key,
                    "label": label,
                })
            elif value == "number":
                # Number type → number input
                elements.append({
                    "type": "number",
                    "key": flat_key,
                    "label": label,
                })
            # Unknown types are silently skipped

        return elements

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Generate UI elements from request_options_ui config.

        Elements have flat keys like "request_options__temperature".
        """
        cfg = config or {}
        options_ui = cfg.get("request_options_ui")

        if not isinstance(options_ui, dict):
            return []

        return self._generate_ui_elements_from_options(
            options_ui, key_prefix=self.FLAT_KEY_PREFIX
        )

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
        """Merge config into shared state, extracting flat UI keys.

        Flat keys like "request_options__temperature" are extracted and
        merged into "request_options". The flat keys are removed from the
        resulting config to keep the state clean.

        The plugin itself remains stateless; request options are read from
        ``state["config"]`` during :meth:`initialize_request`.
        """
        # Extract flat keys and build request_options overlay
        overlay: Dict[str, Any] = {}
        prefix = self.FLAT_KEY_PREFIX

        for key, value in config.items():
            if key.startswith(prefix):
                # Extract the actual option name (e.g., "temperature" from "request_options__temperature")
                option_name = key[len(prefix) :]
                if option_name:
                    overlay[option_name] = value

        # Get existing request_options or empty dict
        existing_options = dict(config.get("request_options", {}))

        # Merge overlay into existing options (overlay takes precedence)
        merged_options = {**existing_options, **overlay}

        # Build new config without flat keys but with merged request_options
        new_config: Dict[str, Any] = {
            k: v for k, v in config.items() if not k.startswith(prefix)
        }
        new_config["request_options"] = merged_options

        return {**state, "config": {**state.get("config", {}), **new_config}}

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
