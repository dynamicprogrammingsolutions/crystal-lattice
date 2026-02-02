"""Echo-only feature that preserves metadata needed by terminal `/list` tests.

By design, arbitrary `Message.metadata` is not automatically preserved when the
core rebuilds messages from provider-native history (`native_messages`).

This feature is intentionally narrow and exists to support tests that use the
EchoOpenAILikeProvider: it preserves only the fields the terminal list renderer
expects.

Preserved keys (via provider-native `_metadata`):
- `reasoning`
- `tool_calls`
- `tool_call_id`
"""

from __future__ import annotations

from typing import Any, Dict, List

from agent_core.types import FeaturePlugin


class EchoProviderMetadataPreserver(FeaturePlugin):
    name = "echo_provider_metadata_preserver"
    version = "0.1.0"

    _KEYS = ("reasoning", "tool_calls", "tool_call_id")

    @staticmethod
    def _select_metadata(metadata: Any) -> Dict[str, Any]:
        if not isinstance(metadata, dict) or not metadata:
            return {}

        selected: Dict[str, Any] = {}

        reasoning = metadata.get("reasoning")
        if isinstance(reasoning, str) and reasoning:
            selected["reasoning"] = reasoning

        tool_calls = metadata.get("tool_calls")
        if isinstance(tool_calls, list) and tool_calls:
            selected["tool_calls"] = tool_calls

        tool_call_id = metadata.get("tool_call_id")
        if isinstance(tool_call_id, str) and tool_call_id:
            selected["tool_call_id"] = tool_call_id

        return selected

    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        updated = [dict(m) if isinstance(m, dict) else {} for m in native_messages]

        for idx, core_msg in enumerate(messages[: len(updated)]):
            if not isinstance(core_msg, dict):
                continue
            selected = self._select_metadata(core_msg.get("metadata"))
            if not selected:
                continue

            existing = updated[idx].get("_metadata")
            if isinstance(existing, dict) and existing:
                filtered_existing = {k: v for k, v in existing.items() if k in self._KEYS}
            else:
                filtered_existing = {}

            updated[idx]["_metadata"] = {**filtered_existing, **selected}

        return updated

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        updated = [dict(m) if isinstance(m, dict) else {} for m in messages]

        for idx, native_msg in enumerate(native_messages[: len(updated)]):
            if not isinstance(native_msg, dict):
                continue
            preserved = native_msg.get("_metadata")
            if not isinstance(preserved, dict) or not preserved:
                continue

            selected = {
                k: preserved.get(k)
                for k in self._KEYS
                if preserved.get(k) is not None
            }
            if not selected:
                continue

            current_md = updated[idx].get("metadata")
            merged_md: Dict[str, Any] = dict(current_md) if isinstance(current_md, dict) else {}
            for key, value in selected.items():
                merged_md.setdefault(key, value)

            if merged_md:
                updated[idx]["metadata"] = merged_md

        return updated
