from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from agent_core.types import ProviderExtensionPlugin


class ClaudeCachingExtension(ProviderExtensionPlugin):
    """Inject Anthropic cache_control blocks when using Claude via OpenRouter.

    This extension only applies when:
    - The selected provider is OpenRouter (provider tag: ``"openrouter"``)
    - The configured model id starts with ``"anthropic/"``

    Behavior:
    - During :meth:`initialize_request`, wraps the last provider-native message
      in an Anthropic-style text block list and attaches
      ``{"cache_control": {"type": "ephemeral"}}``.
    - During :meth:`process_chunk`, reads ``cached_tokens`` from
      ``usage.prompt_tokens_details.cached_tokens`` on streaming chunks and
      stores it in the shared provider state.
    - During :meth:`finalize`, strips any ``cache_control`` annotations from
      the retained provider-native history.
    - During :meth:`from_native_messages`, mirrors cached token counts into
      core message metadata under ``metadata["cached_tokens"]``.
    """

    name: str = "claude_caching_extension"
    version: str = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enable_claude_caching": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": (
                    "Enable Anthropic-style caching for models whose id starts "
                    "with 'anthropic/'. Applies only when using the OpenRouter provider."
                ),
            }
        }

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "checkbox",
                "key": "enable_claude_caching",
                "label": "Enable Claude Caching (Anthropic via OpenRouter)",
            },
            {
                "ui_type": "message_footer",
                "data": "metadata.cached_tokens",
                "template": "cached: {{data}}",
            },
        ]

    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        return ["ext:claude_caching"]

    def required_tags(self) -> List[str]:
        return ["openrouter"]

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

        if isinstance(content, list):
            return native_messages, False

        if not isinstance(content, str) or not content:
            return native_messages, False

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

    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return list(native_messages)

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        enhanced: List[Dict[str, Any]] = []

        if len(messages) == len(native_messages):
            for msg, native in zip(messages, native_messages):
                core_md = dict(msg.get("metadata") or {})
                internal_md = native.get("_metadata") or {}
                if isinstance(internal_md, dict) and "cached_tokens" in internal_md:
                    core_md["cached_tokens"] = internal_md.get("cached_tokens")
                enhanced.append({**msg, "metadata": core_md})
            return enhanced

        enhanced.extend(messages)
        if native_messages and messages:
            internal_md = native_messages[-1].get("_metadata") or {}
            if isinstance(internal_md, dict) and "cached_tokens" in internal_md:
                cached = internal_md.get("cached_tokens")
                last_msg = dict(messages[-1])
                core_md = dict(last_msg.get("metadata") or {})
                core_md["cached_tokens"] = cached
                enhanced[-1] = {**last_msg, "metadata": core_md}

        return enhanced

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {**state, "config": {**state.get("config", {}), **config}}

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        if not self._should_enable_for_state(state):
            return list(native_messages), state

        adjusted, injected = self._inject_cache_breakpoint(native_messages)
        if not injected:
            return list(native_messages), state

        new_state = {**state, "_claude_cache_injected": True}
        return adjusted, new_state

    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        Dict[str, Any],
    ]:
        if not self._should_enable_for_state(state):
            return partial_messages, final_messages, native_messages, state

        cached_tokens = None
        if isinstance(native_chunk, dict):
            usage = native_chunk.get("usage") or {}
            if isinstance(usage, dict):
                details = usage.get("prompt_tokens_details") or {}
                if isinstance(details, dict) and "cached_tokens" in details:
                    cached_tokens = details.get("cached_tokens")
        if cached_tokens is None:
            return partial_messages, final_messages, native_messages, state

        accumulated = state.get("partial")
        if isinstance(accumulated, dict):
            internal_md = dict(accumulated.get("_metadata") or {})
            internal_md["cached_tokens"] = cached_tokens
            accumulated = {**accumulated, "_metadata": internal_md}
            new_state = {**state, "partial": accumulated}
        else:
            new_state = state

        return partial_messages, final_messages, native_messages, new_state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        if not self._should_enable_for_state(state):
            return final_messages, native_messages, state

        cleaned_history = [self._strip_cache_control(m) for m in native_messages]
        return final_messages, cleaned_history, state
