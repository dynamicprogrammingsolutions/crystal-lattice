from __future__ import annotations

"""Test-only timestamp feature.

This lives in the application package so that application-layer tests can
exercise footer rendering without depending on repo-root plugins.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from agent_core.types import FeaturePlugin


class TimestampExtension(FeaturePlugin):
    name: str = "timestamp_extension"
    version: str = "0.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return [
            {
                "ui_type": "message_footer",
                "data": "metadata.timestamp",
                "template": "{{data}}",
                "metadata": {"format": "datetime"},
            }
        ]

    def to_native_messages(
        self,
        messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if len(messages) != 1 or not native_messages:
            return native_messages

        md = messages[0].get("metadata") or {}
        if not isinstance(md, dict) or "native_indices" in md:
            return native_messages

        ts = md.get("timestamp")
        if not isinstance(ts, str) or not ts:
            ts = datetime.now(timezone.utc).isoformat()

        out: List[Dict[str, Any]] = []
        for native in native_messages:
            meta = native.get("_metadata") or {}
            if not isinstance(meta, dict):
                meta = {}
            if not isinstance(meta.get("timestamp"), str) or not meta.get("timestamp"):
                meta = {**meta, "timestamp": ts}
            out.append({**native, "_metadata": meta})
        return out

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if len(messages) != len(native_messages):
            return messages

        out: List[Dict[str, Any]] = []
        for msg, native in zip(messages, native_messages):
            md = msg.get("metadata") or {}
            if not isinstance(md, dict):
                md = {}
            if isinstance(md.get("timestamp"), str) and md.get("timestamp"):
                out.append(msg)
                continue
            meta = native.get("_metadata") or {}
            if not isinstance(meta, dict):
                meta = {}
            ts = meta.get("timestamp")
            if isinstance(ts, str) and ts:
                out.append({**msg, "metadata": {**md, "timestamp": ts}})
            else:
                out.append(msg)
        return out

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        if not final_messages:
            return final_messages, native_messages, state

        ts = datetime.now(timezone.utc).isoformat()

        def _stamp_assistant(native_msg: Dict[str, Any]) -> Dict[str, Any]:
            if native_msg.get("role") != "assistant":
                return native_msg
            meta = native_msg.get("_metadata") or {}
            if not isinstance(meta, dict):
                meta = {}
            if isinstance(meta.get("timestamp"), str) and meta.get("timestamp"):
                return native_msg
            return {**native_msg, "_metadata": {**meta, "timestamp": ts}}

        stamped_finals = [_stamp_assistant(m) for m in final_messages]

        if not native_messages or len(stamped_finals) > len(native_messages):
            return stamped_finals, native_messages, state

        start = len(native_messages) - len(stamped_finals)
        stamped_history = list(native_messages)
        for offset, final_msg in enumerate(stamped_finals):
            if final_msg.get("role") != "assistant":
                continue
            hist_idx = start + offset
            hist_msg = stamped_history[hist_idx]
            if hist_msg.get("role") != "assistant":
                continue
            stamped_history[hist_idx] = _stamp_assistant(hist_msg)

        return stamped_finals, stamped_history, state


__all__ = ["TimestampExtension"]
