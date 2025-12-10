from __future__ import annotations

from typing import Any, Dict, List, Tuple

from agent_core.types import FeaturePlugin


class ClaudeCachingFeature(FeaturePlugin):
    """Feature plugin that injects Anthropic cache_control via OpenRouter.

    This feature only applies when:
    - The selected provider is OpenRouter (provider tag: ``"openrouter"``)
    - The configured model id starts with ``"anthropic/"``

    Behavior:
    - During :meth:`initialize_request`, wraps the *last* provider-native
      message in an Anthropic-style text block list and attaches
      ``{"cache_control": {"type": "ephemeral"}}``. The resulting shape
      matches the Claude caching API when used through OpenRouter's
      ``/chat/completions`` endpoint.
    - During :meth:`finalize`, strips any ``cache_control`` annotations from
      the retained provider-native history so that ephemeral cache markers are
      not persisted in ``session.metadata["native_messages"]``.

    The actual cache hit behavior is handled by OpenRouter/Anthropic. This
    feature only shapes the outbound payload and cleans up the stored
    provider-native history.
    """

    name: str = "claude_caching"
    version: str = "0.1.0"

    # ---- Config / UI ----
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enable_claude_caching": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": (
                    "Enable Anthropic-style caching for models whose id "
                    "starts with 'anthropic/'. Applies only when using the "
                    "OpenRouter provider."
                ),
            }
        }

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "checkbox",
                "key": "enable_claude_caching",
                "label": "Enable Claude Caching (Anthropic via OpenRouter)",
            }
        ]

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        """Advertise this feature for discovery.

        No hard dependency on provider tags here; selection is based on
        config/model at initialize_request time.
        """

        return ["feature:claude_caching"]

    def required_tags(self) -> List[str]:
        """Require OpenRouter provider.

        This ensures the feature is only active when the OpenRouter
        provider is selected (provider tags include "openrouter").
        """

        return ["openrouter"]

    # ---- Lifecycle ----
    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Merge configuration into shared state.

        The feature reads ``enable_claude_caching`` and ``model`` from
        ``state["config"]`` during :meth:`initialize_request`.
        """

        return {**state, "config": {**state.get("config", {}), **config}}

    # ---- Stateless transforms ----
    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # This feature operates only during initialize_request/finalize.
        return native_messages

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # No core-message transformation; only native history is adjusted.
        return messages

    # ---- Request initialization ----
    def _should_enable_for_state(self, state: Dict[str, Any]) -> bool:
        config = state.get("config", {})
        if not isinstance(config, dict):
            return False

        if not config.get("enable_claude_caching", True):
            return False

        model = config.get("model")
        if not isinstance(model, str) or not model.startswith("anthropic/"):
            return False

        return True

    def _inject_cache_breakpoint(
        self, native_messages: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], bool]:
        if not native_messages:
            return native_messages, False

        last = native_messages[-1]
        content = last.get("content")

        # Skip if content is already a list of blocks; avoid double-wrapping.
        if isinstance(content, list):
            return native_messages, False

        if not isinstance(content, str) or not content:
            return native_messages, False

        # Build Anthropic-style text block list with a single ephemeral block.
        blocks: List[Dict[str, Any]] = [
            {
                "type": "text",
                "text": content,
                "cache_control": {"type": "ephemeral"},
            },
        ]

        new_last = {**last, "content": blocks}
        new_messages = [*native_messages[:-1], new_last]
        return new_messages, True

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:

        if not self._should_enable_for_state(state):
            return native_messages, state

        adjusted, injected = self._inject_cache_breakpoint(native_messages)
        if not injected:
            return native_messages, state

        # Remember that we injected cache markup so finalize can strip it
        # before native history is persisted.
        new_state = {**state, "_claude_cache_injected": True}
        return adjusted, new_state

    # ---- Finalize ----
    def _strip_cache_control(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(msg, dict):
            return msg
        content = msg.get("content")
        if not isinstance(content, list):
            return msg
        new_blocks: List[Dict[str, Any]] = []
        for block in content:
            if not isinstance(block, dict):
                new_blocks.append(block)
                continue
            if "cache_control" in block:
                cleaned = {k: v for k, v in block.items() if k != "cache_control"}
                new_blocks.append(cleaned)
            else:
                new_blocks.append(block)
        return {**msg, "content": new_blocks}

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:

        if not state.get("_claude_cache_injected"):
            return final_messages, native_messages, state

        cleaned_history = [self._strip_cache_control(m) for m in native_messages]
        return final_messages, cleaned_history, state
