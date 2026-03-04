from __future__ import annotations

from typing import Any

from agent_core.types import ProviderExtensionPlugin

from reference_openai_compatible_provider._extension_accumulator import (
    AccumulatorExtensionMixin,
    _merge_delta_content,
)


class OpenAICompatibleReasoningExtension(AccumulatorExtensionMixin, ProviderExtensionPlugin):
    name = "reference_openai_reasoning"
    version = "0.1.0"

    def required_tags(self) -> list[str]:
        return ["provider:openai_compatible", "supports_thinking"]

    def get_config_schema(self) -> dict[str, Any]:
        return {"think": {"type": "boolean", "required": False, "default": False}}

    def get_ui_elements(
        self,
        config: dict[str, Any],
        tags: list[str],
        models: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return [{"type": "checkbox", "key": "think", "label": "Enable thinking"}]

    def init(self, config: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        enabled = bool(config.get("think"))
        return {**state, "_think_enabled": enabled}

    def initialize_request(self, native_messages: list[dict[str, Any]], state: dict[str, Any]):
        if not state.get("_think_enabled"):
            return native_messages, state

        req = state.get("request") or {}
        payload = dict(req.get("payload") or {})
        # Ollama's OpenAI-compatible endpoint uses `think: true` to enable
        # reasoning/thinking deltas.
        payload["think"] = True
        return native_messages, {**state, "request": {**req, "payload": payload}}

    def extract_delta(self, native_chunk: dict[str, Any]) -> dict[str, Any]:
        choice0 = (native_chunk.get("choices") or [{}])[0]
        return choice0 if isinstance(choice0, dict) else {}

    def process_delta(self, delta: dict[str, Any], accumulated: dict[str, Any] | None):
        base = accumulated or {}
        d = delta.get("delta") or delta.get("message") or {}
        frag = d.get("reasoning") if isinstance(d, dict) else None
        if not isinstance(frag, str) or not frag:
            return None, base

        new_acc = _merge_delta_content(base, {"reasoning": frag}, accumulate=("reasoning",))
        return {"reasoning": frag}, new_acc

    def from_native_messages(
        self, native_messages: list[dict[str, Any]], messages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        if len(messages) != len(native_messages):
            return messages

        out: list[dict[str, Any]] = []
        for msg, nm in zip(messages, native_messages):
            md = dict(msg.get("metadata") or {})
            reasoning = nm.get("reasoning")
            if isinstance(reasoning, str) and reasoning:
                md["reasoning"] = reasoning
            out.append({**msg, "metadata": md})
        return out
