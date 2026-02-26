"""Duration feature.

Measures wall-clock timestamps and elapsed duration for each provider request.

Behavior:
- Captures a start timestamp in :meth:`initialize_request`.
- Captures an end timestamp and computes duration in :meth:`finalize`.
- Persists timing fields into provider-native message ``_metadata`` so that
  native-history rebuilds keep them intact.
- Exposes per-request duration on assistant messages via message footer UI.
- Exposes a per-turn cumulative duration ("turn duration") similar to the
  OpenRouter usage extension:
    * The turn resets after the most recent user/system message or after the
      most recent assistant message with *no* tool calls.
    * The per-turn duration is the sum of assistant durations since the reset
      point plus the current request duration.
    * "Turn duration" is only surfaced on assistant messages that do not
      include tool calls.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from agent_core.types import FeaturePlugin


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _format_duration_ms(duration_ms: int) -> str:
    if duration_ms < 0:
        duration_ms = 0

    if duration_ms < 1000:
        return f"{duration_ms}ms"

    seconds = duration_ms / 1000.0
    if seconds < 60:
        rendered = f"{seconds:.2f}".rstrip("0").rstrip(".")
        return f"{rendered}s"

    minutes = seconds / 60.0
    rendered = f"{minutes:.2f}".rstrip("0").rstrip(".")
    return f"{rendered}m"


def _has_tool_calls(native_msg: Dict[str, Any]) -> bool:
    tool_calls = native_msg.get("tool_calls")
    if isinstance(tool_calls, list) and tool_calls:
        return True

    internal_md = native_msg.get("_metadata") or {}
    if isinstance(internal_md, dict):
        md_tool_calls = internal_md.get("tool_calls")
        if isinstance(md_tool_calls, list) and md_tool_calls:
            return True

    return False


def _sum_assistant_durations_since_turn_start(native_history: List[Dict[str, Any]]) -> int:
    """Return cumulative assistant duration since the last turn separator."""

    last_sep_idx = -1
    for idx, msg in enumerate(native_history):
        if not isinstance(msg, dict):
            continue
        role = msg.get("role")
        if role in ("user", "system"):
            last_sep_idx = idx
            continue
        if role == "assistant" and not _has_tool_calls(msg):
            last_sep_idx = idx

    total_ms = 0
    for idx, msg in enumerate(native_history):
        if not isinstance(msg, dict):
            continue
        if idx <= last_sep_idx:
            continue
        if msg.get("role") != "assistant":
            continue
        internal_md = msg.get("_metadata") or {}
        if not isinstance(internal_md, dict):
            continue
        duration_ms = internal_md.get("duration_ms")
        if isinstance(duration_ms, (int, float)):
            try:
                total_ms += int(duration_ms)
            except Exception:
                pass

    return total_ms


class DurationExtension(FeaturePlugin):
    name: str = "duration_extension"
    version: str = "0.1.0"

    _STATE_KEY = "_duration_extension"

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
                "data": "metadata.duration_formatted",
                "template": "duration: {{data}}",
            },
            {
                "ui_type": "message_footer",
                "data": "metadata.turn_duration_formatted",
                "template": "turn duration: {{data}}",
            },
        ]

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        timing = {
            "duration_started_at": _now_iso(),
            "duration_started_at_mono": time.monotonic(),
        }
        return list(native_messages), {**state, self._STATE_KEY: timing}

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        if not final_messages:
            return final_messages, native_messages, state

        timing = state.get(self._STATE_KEY) or {}
        if not isinstance(timing, dict):
            return final_messages, native_messages, state

        started_at = timing.get("duration_started_at")
        started_at_mono = timing.get("duration_started_at_mono")
        if not isinstance(started_at, str) or not started_at:
            return final_messages, native_messages, state
        if not isinstance(started_at_mono, (int, float)):
            return final_messages, native_messages, state

        finished_at = _now_iso()
        try:
            duration_ms = int((time.monotonic() - float(started_at_mono)) * 1000)
        except Exception:
            duration_ms = 0
        duration_formatted = _format_duration_ms(duration_ms)

        history_offset = len(native_messages)
        if native_messages and len(final_messages) <= len(native_messages):
            history_offset = len(native_messages) - len(final_messages)

        history_before_current = (
            native_messages[:history_offset] if history_offset > 0 else []
        )
        base_turn_ms = _sum_assistant_durations_since_turn_start(history_before_current)
        turn_duration_ms = base_turn_ms + duration_ms
        turn_duration_formatted = _format_duration_ms(turn_duration_ms)

        def _stamp_assistant(native_msg: Dict[str, Any]) -> Dict[str, Any]:
            if native_msg.get("role") != "assistant":
                return native_msg

            internal_md = native_msg.get("_metadata") or {}
            if not isinstance(internal_md, dict):
                internal_md = {}

            merged_md = {
                **internal_md,
                "duration_started_at": started_at,
                "duration_finished_at": finished_at,
                "duration_ms": duration_ms,
                "duration_formatted": duration_formatted,
                "turn_duration_ms": turn_duration_ms,
                "turn_duration_formatted": turn_duration_formatted,
            }
            return {**native_msg, "_metadata": merged_md}

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
            if not isinstance(hist_msg, dict) or hist_msg.get("role") != "assistant":
                continue
            stamped_history[hist_idx] = _stamp_assistant(hist_msg)

        return stamped_finals, stamped_history, state

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        duration_keys = (
            "duration_started_at",
            "duration_finished_at",
            "duration_ms",
            "duration_formatted",
        )
        turn_keys = (
            "turn_duration_ms",
            "turn_duration_formatted",
        )

        if len(messages) == len(native_messages):
            out: List[Dict[str, Any]] = []
            for msg, native in zip(messages, native_messages):
                core_md_raw = msg.get("metadata")
                core_md: Dict[str, Any] = (
                    dict(core_md_raw) if isinstance(core_md_raw, dict) else {}
                )
                internal_md = native.get("_metadata") or {}
                if not isinstance(internal_md, dict):
                    internal_md = {}

                for key in duration_keys:
                    if key in internal_md and key not in core_md:
                        core_md[key] = internal_md.get(key)

                if _has_tool_calls(native):
                    for key in turn_keys:
                        core_md.pop(key, None)
                else:
                    for key in turn_keys:
                        if key in internal_md and key not in core_md:
                            core_md[key] = internal_md.get(key)

                out.append({**msg, "metadata": core_md})
            return out

        # If lengths differ, best-effort: operate on the last message only.
        if not messages:
            return messages

        out = list(messages)
        native_last = native_messages[-1] if native_messages and isinstance(native_messages[-1], dict) else {}
        core_last = dict(out[-1]) if isinstance(out[-1], dict) else {}
        core_md_raw = core_last.get("metadata")
        core_md = dict(core_md_raw) if isinstance(core_md_raw, dict) else {}
        internal_md = native_last.get("_metadata") or {}
        if isinstance(internal_md, dict):
            for key in duration_keys:
                core_md.setdefault(key, internal_md.get(key))

            if _has_tool_calls(native_last):
                for key in turn_keys:
                    core_md.pop(key, None)
            else:
                for key in turn_keys:
                    core_md.setdefault(key, internal_md.get(key))

        core_last["metadata"] = core_md
        out[-1] = core_last
        return out


__all__ = ["DurationExtension"]
