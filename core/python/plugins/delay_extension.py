from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import time

from agent_core.types import ProviderExtensionPlugin


class DelayExtension(ProviderExtensionPlugin):
    """Provider extension that adds an artificial delay per request.

    Intended for manual testing of cancellation and latency handling. When
    enabled via config, it sleeps for ``delay_seconds`` during
    ``initialize_request``.
    """

    name: str = "delay_extension"
    version: str = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enable_delay_extension": {
                "type": "boolean",
                "required": False,
                "default": False,
            },
            "delay_seconds": {
                "type": "number",
                "required": False,
                "default": 0.0,
                "minimum": 0.0,
            },
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "type": "checkbox",
                "key": "enable_delay_extension",
                "label": "Enable artificial delay",
            },
            {
                "type": "number",
                "key": "delay_seconds",
                "label": "Delay per request (seconds)",
            },
        ]

    def init(
        self,
        config: Dict[str, Any],
        state: Dict[str, Any],
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        if not config.get("enable_delay_extension"):
            return state

        delay = float(config.get("delay_seconds") or 0.0)
        if delay < 0.0:
            delay = 0.0

        return {
            **state,
            "delay_extension": {"enabled": True, "delay_seconds": delay},
        }

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:

        de_state = state.get("delay_extension")
        if not isinstance(de_state, dict) or not de_state.get("enabled"):
            return native_messages, state

        delay = float(de_state.get("delay_seconds") or 0.0)
        if delay > 0.0:
            time.sleep(delay)

        return native_messages, state

