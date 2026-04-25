"""Feature plugin that emits codex-variant tags for shell-command-family models.

This feature detects when the configured model belongs to the shell-command
family used by Codex CLI and emits the ``codex-variant`` tag.

The tag is used by shell tool selection to choose the appropriate
shell tool:
- codex-variant tag present → shell_command (string-based)
- codex-variant tag absent → shell (array-based)
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from agent_core.types import FeaturePlugin

from .model_family import is_shell_command_family_model


class CodexVariantFeature(FeaturePlugin):
    """Feature that emits ``codex-variant`` for shell-command-family models."""
    
    name: str = "codex_variant"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def get_ui_elements(
        self,
        config: Dict[str, Any],
        tags: List[str],
        models: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        return []

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        """Return codex-variant tag if the model auto-selects shell_command."""
        model = config.get("model", "")
        if not isinstance(model, str):
            return []

        if is_shell_command_family_model(model):
            return ["codex-variant"]
        return []

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        return list(native_messages), state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        return final_messages, native_messages, state


__all__ = ["CodexVariantFeature"]