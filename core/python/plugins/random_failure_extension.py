from __future__ import annotations

from typing import Any, Dict, List, Tuple

from agent_core.types import ProviderExtensionPlugin


# Global state for RandomFailureExtension so that failures
# accumulate across requests for a running process.
_RF_STATE: Dict[str, Any] = {
    "enabled": False,
    "every": 3,
    "counter": 0,
}


class RandomFailureExtension(ProviderExtensionPlugin):
    """Provider extension that fails every Nth request.

    Intended for manual testing of error handling. When enabled, it
    increments a *global* counter on each request and raises a
    ``RuntimeError`` from ``finalize`` when the counter is a multiple of
    ``random_failure_every`` (default: 3).
    """

    name: str = "random_failure_extension"
    version: str = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enable_random_failure": {
                "type": "boolean",
                "required": False,
                "default": False,
            },
            "random_failure_every": {
                "type": "integer",
                "required": False,
                "default": 3,
                "minimum": 1,
            },
        }

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "checkbox",
                "key": "enable_random_failure",
                "label": "Enable random failures",
            },
            {
                "type": "number",
                "key": "random_failure_every",
                "label": "Fail every Nth request",
            },
        ]

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Configure global failure behaviour from application config.

        This does *not* store anything in the provider state; instead it
        updates the module-level ``_RF_STATE`` so the counter persists
        across requests.
        """

        global _RF_STATE

        if not config.get("enable_random_failure"):
            _RF_STATE["enabled"] = False
            return state

        every = int(config.get("random_failure_every") or 3)
        if every <= 0:
            every = 3

        _RF_STATE["enabled"] = True
        _RF_STATE["every"] = every
        # Preserve existing counter so failures continue across config reloads.

        return state

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        global _RF_STATE

        if not _RF_STATE.get("enabled"):
            return state

        counter = int(_RF_STATE.get("counter") or 0) + 1
        _RF_STATE["counter"] = counter
        return state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        global _RF_STATE

        if not _RF_STATE.get("enabled"):
            return final_messages, native_messages, state

        counter = int(_RF_STATE.get("counter") or 0)
        every = int(_RF_STATE.get("every") or 3)

        if every > 0 and counter % every == 0:
            raise RuntimeError("RandomFailureExtension: simulated failure")

        return final_messages, native_messages, state
