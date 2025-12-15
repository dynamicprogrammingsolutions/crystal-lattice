"""Timestamp feature.

Adds a `timestamp` field to message metadata and exposes it as a
message_footer UI element that terminal renderers can display.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from agent_core.types import FeaturePlugin


class TimestampExtension(FeaturePlugin):
    """Feature plugin that annotates messages with a timestamp.

    Timestamps are attached to provider-native messages via an internal
    ``_metadata.timestamp`` field and surfaced to core messages via
    ``metadata.timestamp`` in :meth:`from_native_messages`. This allows
    timestamps to be preserved across native-history rebuilds and makes
    them available to UIs via :meth:`get_ui_elements`, which contributes
    a single ``"message_footer"`` element referencing
    ``metadata.timestamp`` so terminal UIs can render the timestamp
    beneath each message.
    """

    name: str = "timestamp_extension"
    version: str = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return [
            {
                "ui_type": "message_footer",
                "data": "metadata.timestamp",
                "template": "{{data}}",
            }
        ]

    def to_native_messages(
        self,
        messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Attach or propagate timestamps in provider-native messages.

        This runs on all core→native conversions, including when a new
        user or tool message is appended via :meth:`AgentCore.add_message`
        and when existing sessions are prepared for a request. For each
        message/native pair, the logic is:

        - If the core message already has ``metadata.timestamp``, reuse it.
        - Else, if the native message has ``_metadata.timestamp``, reuse it.
        - Else, assign a new timestamp for this call.

        The resolved timestamp is stored on the native message under
        ``_metadata.timestamp`` so that it can later be surfaced back to
        the core via :meth:`from_native_messages`.
        """

        if not messages or not native_messages:
            return native_messages

        # Single timestamp per batch when we need to allocate a new one.
        now_ts = datetime.now(timezone.utc).isoformat()
        out: List[Dict[str, Any]] = []

        for idx, native in enumerate(native_messages):
            if idx < len(messages) and isinstance(messages[idx], dict):
                core_msg = messages[idx]
            else:
                core_msg = {}

            if not isinstance(native, dict):
                out.append(native)
                continue

            # Existing core metadata (if any).
            core_md = core_msg.get("metadata") or {}
            if not isinstance(core_md, dict):
                core_md = {}

            # Existing native-side _metadata (if any).
            raw_meta = native.get("_metadata") or {}
            meta = raw_meta if isinstance(raw_meta, dict) else {}

            ts_val = core_md.get("timestamp") or meta.get("timestamp")
            if not isinstance(ts_val, str) or not ts_val:
                ts_val = now_ts

            new_meta = {**meta, "timestamp": ts_val}
            out.append({**native, "_metadata": new_meta})

        # Preserve any trailing native messages beyond the core messages.
        if len(native_messages) > len(out):
            out.extend(native_messages[len(out) :])

        return out

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Surface provider-native timestamps onto core messages.

        For each core message, prefer an existing ``metadata.timestamp``
        value when present; otherwise, attempt to read
        ``_metadata.timestamp`` from the corresponding native message.
        As a last resort, a new timestamp is allocated.
        """

        if not messages:
            return messages

        out: List[Dict[str, Any]] = []
        now_ts = datetime.now(timezone.utc).isoformat()

        for idx, msg in enumerate(messages):
            if not isinstance(msg, dict):
                out.append(msg)
                continue

            md = msg.get("metadata") or {}
            if not isinstance(md, dict):
                md = {}

            # Existing core timestamp, if any.
            ts_val = md.get("timestamp")

            # Prefer timestamp from native _metadata when core metadata
            # does not already include one.
            if (not isinstance(ts_val, str) or not ts_val) and idx < len(native_messages):
                native = native_messages[idx]
                if isinstance(native, dict):
                    raw_meta = native.get("_metadata") or {}
                    if isinstance(raw_meta, dict):
                        native_ts = raw_meta.get("timestamp")
                        if isinstance(native_ts, str) and native_ts:
                            ts_val = native_ts

            if not isinstance(ts_val, str) or not ts_val:
                ts_val = now_ts

            new_md = {**md, "timestamp": ts_val}
            out.append({**msg, "metadata": new_md})

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
        message metadata.
        """

        if not final_messages:
            return final_messages, native_messages, state

        ts = datetime.now(timezone.utc).isoformat()
        out_finals: List[Dict[str, Any]] = []

        for msg in final_messages:
            if not isinstance(msg, Dict):
                out_finals.append(msg)
                continue

            raw_meta = msg.get("_metadata") or {}
            meta = raw_meta if isinstance(raw_meta, dict) else {}

            if not isinstance(meta.get("timestamp"), str) or not meta.get("timestamp"):
                meta = {**meta, "timestamp": ts}

            out_finals.append({**msg, "_metadata": meta})

        return out_finals, native_messages, state
