"""Feature plugin that emits codex-variant tag for Codex models.

This feature detects when the configured model is a Codex variant
(model name ends with "-codex") and emits the "codex-variant" tag.

The tag is used by shell tool selection to choose the appropriate
shell tool:
- codex-variant tag present → shell_command (string-based)
- codex-variant tag absent → shell (array-based)
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from agent_core.types import FeaturePlugin


class CodexVariantFeature(FeaturePlugin):
    """Feature that emits codex-variant tag for Codex models.
    
    A model is considered a Codex variant if its name matches a codex pattern.
    Valid codex model patterns:
    - Ends with "-codex" (e.g., "openai/gpt-5.2-codex")
    - Ends with "-codex-mini" (e.g., "openai/gpt-5.1-codex-mini")
    - Ends with "-codex-max" (e.g., "openai/gpt-5.1-codex-max")
    
    Examples:
    - "openai/gpt-5.2-codex" → codex-variant
    - "openai/gpt-5.3-codex" → codex-variant
    - "openai/gpt-5.1-codex-mini" → codex-variant
    - "openai/gpt-5.1-codex-max" → codex-variant
    - "openai/gpt-5" → not a codex variant
    """
    
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
        """Return codex-variant tag if model name matches codex pattern."""
        model = config.get("model", "")
        if not isinstance(model, str):
            return []
        
        # Check for codex variant patterns
        if model.endswith("-codex") or model.endswith("-codex-mini") or model.endswith("-codex-max"):
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