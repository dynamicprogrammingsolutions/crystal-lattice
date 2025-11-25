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

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "checkbox",
                "key": "think",
                "label": "Enable Ollama Thinking",
            }
        ]

    def get_models(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Forward model descriptors without modification.

        The thinking extension does not influence model discovery.
        """
        return list(models)

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
        # Put back reasoning from metadata if they exist
        if len(messages) == len(native_messages):
            enhanced_native_messages = [{**native_msg, "reasoning": message.get("metadata", {}).get("reasoning")} for message, native_msg in zip(messages, native_messages)]
            return enhanced_native_messages
        else:
            return native_messages

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # Enhance messages: add reasoning to metadata from native_messages
        if len(messages) == len(native_messages):
            enhanced_messages = [
                {**message, "metadata": {**(message.get("metadata", {})), "reasoning": native_msg.get("reasoning")}}
                for message, native_msg in zip(messages, native_messages)
            ]
            return enhanced_messages
        # If lengths differ, leave messages unchanged (no fallback)
        return messages
                
    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not state.get("ollama_think_enabled"):
            return state
        
        request = state.get("request") or {}
        return {**state, "request": {**request, "payload": {**(dict(request.get("payload", {}))), "think": True}}}

    def extract_delta(self, native_chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract a provider-native delta dictionary from a streaming chunk.
        Return the first choice if present.
        """
        if "choices" in native_chunk and native_chunk["choices"]:
            return dict(native_chunk["choices"][0])
        
        return {}
    
    def process_delta(
        self, delta: Dict[str, Any], current_partial: Dict[str, Any]|None = None, current_final: Dict[str, Any]|None = None, accumulated = {}
    ):
        """
        Enhance the partial or final message with additional information from delta.
        Returns (partial_message, final_message).
        """
        if "message" in delta and current_final is not None:
            # This is a full message, not a delta. example: {'index': 0, 'message': {'role': 'assistant', 'content': "Here's a short poem:\n\nSilent stars shine bright and far,\nA midnight sky, with dreams afar.\nThe moon glows soft, like silver hue,\nAs
            new_final = self._merge_delta_content(current_final, delta.get("message") or {}, override=["reasoning"])
            return current_partial, new_final, accumulated
        
        if "delta" in delta and current_partial is not None:
            # This is a delta. example: {'index': 0, 'delta': {'role': 'assistant', 'content': 'Sil'}, 'finish_reason': None}
            delta_content = delta.get("delta", {})
            new_partial = self._merge_delta_content(current_partial, delta_content, accumulate=["reasoning"])
            accumulated = self._merge_delta_content(accumulated, delta_content, accumulate=["reasoning"])
            return new_partial, current_final, accumulated

        return current_partial, current_final, accumulated

    def _merge_delta_content(self, current: Dict[str, Any], delta: Dict[str, Any], override: List[str] = [], accumulate: List[str] = []) -> Dict[str, Any]:
        return {
            **current,
            # For override keys, prefer the incoming delta value, falling back to current
            **{key: delta.get(key, current.get(key, "")) for key in override},
            # For accumulate keys, append incoming delta fragments to current value
            **{key: (current.get(key, "") + delta.get(key, "")) for key in accumulate}
        }

    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        state: Dict[str, Any],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]
    ]:       
        delta = self.extract_delta(native_chunk or {})
        
        new_partial_messages = partial_messages
        new_final_messages = final_messages
        new_native_messages = native_messages
        accumulated = state.get("partial", {})
        
        if len(final_messages) > 0:
            new_partial_message, new_final_message, accumulated = self.process_delta(delta=delta, current_final=final_messages[-1], accumulated = accumulated)
            new_final_messages = [*(final_messages[:-1] or []), new_final_message]
            new_native_messages = [*(native_messages[:-1] or []), new_final_message]

        if len(partial_messages) > 0:
            new_partial_message, new_final_message, accumulated = self.process_delta(delta=delta, current_partial=partial_messages[-1], accumulated = accumulated)
            # Do not write reasoning into metadata for partial messages; emit native-only
            new_partial_messages = [*(partial_messages[:-1] or []), new_partial_message]

        return new_partial_messages, new_final_messages, new_native_messages, {**state, "partial": accumulated}

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
