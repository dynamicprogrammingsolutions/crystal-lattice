"""Timestamp feature.

Adds a ``timestamp`` field to message metadata and exposes it as a
``message_footer`` UI element that terminal renderers can display.

This feature only *allocates* new timestamps in two places:

- When a new core message is appended and converted to provider-native
  form (``to_native_messages`` for the single appended message).
- When an assistant message is received from the provider
  (``finalize`` for provider-native final assistant messages).

The feature does not allocate timestamps during native→core conversion;
it only surfaces timestamps already present in provider-native
``_metadata``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from agent_core.types import FeaturePlugin


class TimestampExtension(FeaturePlugin):
    """Feature plugin that annotates messages with a timestamp."""

    name: str = "timestamp_extension"
    version: str = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
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
        """Attach a timestamp to a single newly-appended message.

        The core calls this hook both for full-history conversions and
        for single-message conversions (when appending via
        :meth:`AgentCore.add_message`). This feature only annotates the
        *single* appended message and otherwise leaves history unchanged
        to avoid index-misalignment bugs when provider-native history
        contains synthetic messages.
        """

        if len(messages) != 1 or not native_messages:
            return native_messages

        core_md = messages[0].get("metadata") or {}
        if not isinstance(core_md, dict):
            core_md = {}

        # Messages already in a session with native history carry
        # native_indices; do not allocate timestamps during request
        # preparation.
        if "native_indices" in core_md:
            return native_messages

        ts = core_md.get("timestamp")
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
        """Surface existing provider-native timestamps onto core messages.

        This hook never allocates timestamps; it only copies
        ``_metadata.timestamp`` from provider-native messages when
        available.
        """

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
        """Attach timestamps to provider-native final messages.

        For assistant messages produced by the provider, ensure that
        ``_metadata.timestamp`` is present so that subsequent
        :meth:`from_native_messages` calls can surface it onto core
        message metadata. This also updates the full provider-native
        history returned by the provider so timestamps are preserved
        across native-history rebuilds.
        """

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
