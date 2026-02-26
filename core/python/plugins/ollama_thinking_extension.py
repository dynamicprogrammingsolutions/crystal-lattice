"""Ollama thinking extension for OpenAI-compatible provider.

Adds `think: true` to requests when enabled and extracts reasoning/thinking
content from Ollama's OpenAI-compatible responses, exposing it in metadata.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from agent_core.types import ProviderExtensionPlugin


class OllamaThinkingExtension(ProviderExtensionPlugin):
    """Minimal provider extension to enable Ollama thinking.

    Responsibilities:
    - Add "think": true to the request payload when enabled via config.
    - Accumulate reasoning text from streaming chunks.
    - Attach reasoning into metadata on final assistant messages.
    - Emit partial reasoning updates during streaming via metadata.
    """

    name: str = "ollama_thinking"
    version: str = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:

        return {"think": {"type": "boolean", "required": False, "default": False}}

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "type": "checkbox",
                "key": "think",
                "label": "Enable Ollama Thinking",
            }
        ]

    # Uses adapter default get_models (no-op on models)

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        """Identify this extension for dependency resolution."""
        return ["ext:ollama_thinking"]

    def required_tags(self) -> List[str]:
        """Require reasoning/thinking support from the provider/models."""
        return ["supports_thinking"]

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:

        enabled = bool(config.get("think"))
        if not enabled:
            return state
        return {
            **state,
            "ollama_think_enabled": True,
        }

    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Leave provider-native messages unchanged.

        Reasoning text is treated as provider-native metadata that is
        accumulated during streaming and exposed via
        :meth:`from_native_messages` into message metadata. It should
        not be written back into new provider-native requests from core
        messages.
        """
        return native_messages

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # Enhance messages: add reasoning to metadata from native_messages
        if len(messages) == len(native_messages):
            enhanced_messages = [
                {
                    **message,
                    "metadata": {
                        **(message.get("metadata", {})),
                        "reasoning": native_msg.get("reasoning"),
                    },
                }
                for message, native_msg in zip(messages, native_messages)
            ]
            return enhanced_messages
        # If lengths differ, leave messages unchanged (no fallback)
        return messages

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        if not state.get("ollama_think_enabled"):
            return native_messages, state

        request = state.get("request") or {}
        new_state: Dict[str, Any] = {
            **state,
            "request": {
                **request,
                "payload": {**(dict(request.get("payload", {}))), "think": True},
            },
        }
        return native_messages, new_state


    def extract_delta(self, native_chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Extract a provider-native delta dictionary from a streaming chunk.

        Returns the first choice object when present, or an empty dict.
        """
        if "choices" in native_chunk and native_chunk["choices"]:
            return native_chunk["choices"][0]

        return {}

    def process_delta(
        self,
        delta: Dict[str, Any],
        current_partial: Dict[str, Any] | None = None,
        accumulated: Dict[str, Any] | None = None,
    ):
        """Accumulate reasoning text from streaming deltas.

        Updates both the current partial message (when present) and the shared
        accumulator (state["partial"]) with incremental reasoning fragments.
        """
        base = accumulated or {}
        d = delta.get("message") or delta.get("delta") or {}

        if not isinstance(d, dict) or "reasoning" not in d:
            return current_partial, base

        # And into the accumulator used by the provider's finalize()
        new_accumulated = self._merge_delta_content(
            base,
            {"reasoning": d.get("reasoning")},
            accumulate=["reasoning"],
        )
        return current_partial, new_accumulated

    def _merge_delta_content(
        self,
        current: Dict[str, Any],
        delta: Dict[str, Any],
        override: List[str] = [],
        accumulate: List[str] = [],
    ) -> Dict[str, Any]:
        return {
            **current,
            # For override keys, prefer the incoming delta value, falling back to current
            **{key: delta.get(key, current.get(key, "")) for key in override},
            # For accumulate keys, append incoming delta fragments to current value
            **{
                key: ((current.get(key) or "") + (delta.get(key) or ""))
                for key in accumulate
            },
        }

    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Update partial messages and accumulator with reasoning for each chunk.

        This extension no longer mutates finals or history during streaming; it
        only enriches provider-native partials and the shared accumulator. The
        provider's finalize() step then emits the full assistant message with
        accumulated reasoning.
        """
        delta = self.extract_delta(native_chunk or {})

        new_partial_messages = partial_messages
        accumulated = state.get("partial", {})

        if partial_messages:
            current_partial = partial_messages[-1]
            new_partial, accumulated = self.process_delta(
                delta=delta,
                current_partial=current_partial,
                accumulated=accumulated,
            )
            new_partial_messages = [*partial_messages[:-1], new_partial]

        return (
            new_partial_messages,
            final_messages,
            native_messages,
            {**state, "partial": accumulated},
        )

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        if not state.get("ollama_think_enabled"):
            return final_messages, native_messages, state

        # If we accumulated reasoning during streaming, attach it to the last final
        accumulated = state.get("partial") or {}
        reasoning_text = accumulated.get("reasoning") if isinstance(accumulated, dict) else None
        if reasoning_text:
            if final_messages:
                last_final = dict(final_messages[-1])
                last_final["reasoning"] = last_final.get("reasoning", "") + reasoning_text
                final_messages = [*final_messages[:-1], last_final]
            if native_messages:
                last_native = dict(native_messages[-1])
                last_native["reasoning"] = last_native.get("reasoning", "") + reasoning_text
                native_messages = [*native_messages[:-1], last_native]
        return final_messages, native_messages, state
