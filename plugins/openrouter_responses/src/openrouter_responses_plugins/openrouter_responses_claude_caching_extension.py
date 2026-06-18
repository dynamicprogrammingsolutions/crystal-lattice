from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from agent_core.types import ProviderExtensionPlugin


class OpenRouterResponsesClaudeCachingExtension(ProviderExtensionPlugin):
    """Inject Anthropic cache_control blocks when using Claude via OpenRouter `/responses`.

    This mirrors the chat-completions ClaudeCachingExtension but uses Responses-style
    input parts.
    """

    name: str = "openrouter_responses_claude_caching"
    version: str = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enable_claude_caching": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": "Enable Anthropic-style caching for anthropic/* models.",
            }
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
                "key": "enable_claude_caching",
                "label": "Enable Claude Caching (OpenRouter /responses)",
            },
            {
                "ui_type": "message_footer",
                "data": "metadata.cached_tokens",
                "template": "cached: {{data}}",
            },
        ]

    def get_tags(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[str]:
        return ["ext:openrouter_responses_claude_caching"]

    def required_tags(self) -> List[str]:
        return ["openrouter_responses"]

    def _should_enable_for_state(self, state: Dict[str, Any]) -> bool:
        config = state.get("config", {})
        if not isinstance(config, dict):
            return False
        if not config.get("enable_claude_caching", True):
            return False
        model = config.get("model")
        return isinstance(model, str) and model.startswith("anthropic/")

    def _inject_cache_breakpoint(
        self, native_messages: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], bool]:
        if not native_messages:
            return native_messages, False

        last = native_messages[-1]
        if not isinstance(last, dict) or last.get("type") != "message":
            return native_messages, False

        content = last.get("content")
        if not isinstance(content, list) or not content:
            return native_messages, False

        injected = False
        new_parts: List[Dict[str, Any]] = []
        for part in content:
            if not isinstance(part, dict) or injected:
                new_parts.append(part)
                continue
            if part.get("type") != "input_text":
                new_parts.append(part)
                continue
            text = part.get("text")
            if not isinstance(text, str) or not text:
                new_parts.append(part)
                continue
            new_parts.append({**part, "cache_control": {"type": "ephemeral"}})
            injected = True

        if not injected:
            return native_messages, False

        new_last = {**last, "content": new_parts}
        return [*native_messages[:-1], new_last], True

    def _strip_cache_control(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(msg, dict):
            return msg
        content = msg.get("content")
        if not isinstance(content, list):
            return msg
        new_parts: List[Dict[str, Any]] = []
        for part in content:
            if not isinstance(part, dict):
                new_parts.append(part)
                continue
            if "cache_control" in part:
                cleaned = {k: v for k, v in part.items() if k != "cache_control"}
                new_parts.append(cleaned)
            else:
                new_parts.append(part)
        return {**msg, "content": new_parts}

    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        return list(native_messages)

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # Infer cached_tokens from usage blocks. Provider-native history may
        # include non-message items (reasoning, tool calls), so avoid relying
        # on list alignment.
        enhanced: List[Dict[str, Any]] = []
        for msg in messages:
            core_md = dict(msg.get("metadata") or {})
            if "cached_tokens" not in core_md:
                usage = core_md.get("usage")
                if isinstance(usage, dict):
                    details = usage.get("input_tokens_details") or {}
                    if isinstance(details, dict) and "cached_tokens" in details:
                        core_md["cached_tokens"] = details.get("cached_tokens")
            enhanced.append({**msg, "metadata": core_md})
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

        return adjusted, {**state, "_claude_cache_injected": True}

    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:
        if not self._should_enable_for_state(state):
            return partial_messages, final_messages, native_messages, state

        cached_tokens = None
        if (
            isinstance(native_chunk, dict)
            and native_chunk.get("type") == "response.completed"
        ):
            resp = native_chunk.get("response") or {}
            if isinstance(resp, dict):
                usage = resp.get("usage") or {}
                if isinstance(usage, dict):
                    details = usage.get("input_tokens_details") or {}
                    if isinstance(details, dict) and "cached_tokens" in details:
                        cached_tokens = details.get("cached_tokens")

        if cached_tokens is None:
            return partial_messages, final_messages, native_messages, state

        accumulated = state.get("accumulator")
        if isinstance(accumulated, dict):
            internal_md = dict(accumulated.get("_metadata") or {})
            internal_md["cached_tokens"] = cached_tokens
            accumulated = {**accumulated, "_metadata": internal_md}
            state = {**state, "accumulator": accumulated}

        return partial_messages, final_messages, native_messages, state

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
