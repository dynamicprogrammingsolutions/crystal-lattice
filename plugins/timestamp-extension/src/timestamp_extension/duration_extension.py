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
    priority: int = 200

    _SHOW_DURATION_KEY = "duration_extension_show_duration"

    _STATE_KEY = "_duration_extension"

    @staticmethod
    def _turn_metadata(native_msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        internal_md = native_msg.get("_metadata") or {}
        if not isinstance(internal_md, dict):
            return None
        turn = internal_md.get("turn")
        return turn if isinstance(turn, dict) else None

    @classmethod
    def _turn_id(cls, native_msg: Dict[str, Any]) -> Any:
        turn = cls._turn_metadata(native_msg)
        if not isinstance(turn, dict):
            return None
        value = turn.get("id")
        if isinstance(value, (str, int, float)) and not isinstance(value, bool):
            return value
        return None

    @classmethod
    def _turn_has_tool_calls(cls, native_msg: Dict[str, Any]) -> Optional[bool]:
        turn = cls._turn_metadata(native_msg)
        if not isinstance(turn, dict):
            return None
        value = turn.get("has_tool_calls")
        return value if isinstance(value, bool) else None

    @classmethod
    def _sum_assistant_durations_for_turn(
        cls, native_history: List[Dict[str, Any]], turn_id: Any
    ) -> int:
        total_ms = 0
        for msg in native_history:
            if not isinstance(msg, dict) or msg.get("role") != "assistant":
                continue
            if cls._turn_id(msg) != turn_id:
                continue
            internal_md = msg.get("_metadata") or {}
            if not isinstance(internal_md, dict):
                continue
            duration_ms = internal_md.get("duration_ms")
            if isinstance(duration_ms, (int, float)) and not isinstance(duration_ms, bool):
                try:
                    total_ms += int(duration_ms)
                except Exception:
                    pass
        return total_ms

    @classmethod
    def _base_turn_duration_ms(cls, native_history: List[Dict[str, Any]], current_msg: Dict[str, Any]) -> int:
        turn_id = cls._turn_id(current_msg)
        if turn_id is not None:
            return cls._sum_assistant_durations_for_turn(native_history, turn_id)
        return _sum_assistant_durations_since_turn_start(native_history)

    @classmethod
    def _turn_input_tokens(cls, native_msg: Dict[str, Any]) -> Optional[int]:
        internal_md = native_msg.get("_metadata") or {}
        if not isinstance(internal_md, dict):
            return None
        value = internal_md.get("usage_turn_input_tokens_cumulative")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return max(0, int(value))
        return None

    @classmethod
    def _turn_output_tokens(cls, native_msg: Dict[str, Any]) -> Optional[int]:
        internal_md = native_msg.get("_metadata") or {}
        if not isinstance(internal_md, dict):
            return None
        value = internal_md.get("usage_turn_output_tokens_cumulative")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return max(0, int(value))
        return None

    @classmethod
    def _turn_tps_tokens(cls, native_msg: Dict[str, Any]) -> Optional[int]:
        output_tokens = cls._turn_output_tokens(native_msg)
        if isinstance(output_tokens, int):
            return output_tokens
        return cls._turn_input_tokens(native_msg)

    @classmethod
    def _should_surface_turn_metrics(cls, native_msg: Dict[str, Any]) -> bool:
        turn_has_tool_calls = cls._turn_has_tool_calls(native_msg)
        if isinstance(turn_has_tool_calls, bool):
            return not turn_has_tool_calls
        return not _has_tool_calls(native_msg)

    @staticmethod
    def _format_turn_tps(turn_tps: float) -> str:
        rendered = f"{turn_tps:.2f}".rstrip("0").rstrip(".")
        return f"{rendered} tok/s"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            self._SHOW_DURATION_KEY: {
                "type": "boolean",
                "default": True,
                "description": "Show per-message duration footers.",
            },
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        show_duration = True
        if isinstance(config, dict) and self._SHOW_DURATION_KEY in config:
            show_duration = bool(config.get(self._SHOW_DURATION_KEY))

        elements: List[Dict[str, Any]] = [
            {
                "ui_type": "config",
                "type": "checkbox",
                "key": self._SHOW_DURATION_KEY,
                "label": "Show duration",
                "description": "Show per-message duration in message footers.",
            }
        ]

        if show_duration:
            elements.extend(
                [
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
                    {
                        "ui_type": "message_footer",
                        "data": "metadata.turn_tps_formatted",
                        "template": "turn TPS: {{data}}",
                    },
                ]
            )

        return elements

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
        def _stamp_assistant(native_msg: Dict[str, Any]) -> Dict[str, Any]:
            if native_msg.get("role") != "assistant":
                return native_msg

            internal_md = native_msg.get("_metadata") or {}
            if not isinstance(internal_md, dict):
                internal_md = {}

            base_turn_ms = self._base_turn_duration_ms(history_before_current, native_msg)
            turn_duration_ms = base_turn_ms + duration_ms
            turn_duration_formatted = _format_duration_ms(turn_duration_ms)

            merged_md = {
                **internal_md,
                "duration_started_at": started_at,
                "duration_finished_at": finished_at,
                "duration_ms": duration_ms,
                "duration_formatted": duration_formatted,
                "turn_duration_ms": turn_duration_ms,
                "turn_duration_formatted": turn_duration_formatted,
            }

            turn_tps_tokens = self._turn_tps_tokens(native_msg)
            if isinstance(turn_tps_tokens, int) and turn_duration_ms > 0:
                turn_tps = (float(turn_tps_tokens) * 1000.0) / float(turn_duration_ms)
                merged_md["turn_tps"] = turn_tps
                merged_md["turn_tps_formatted"] = self._format_turn_tps(turn_tps)
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
            "turn_tps",
            "turn_tps_formatted",
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

                if not self._should_surface_turn_metrics(native):
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

            if not self._should_surface_turn_metrics(native_last):
                for key in turn_keys:
                    core_md.pop(key, None)
            else:
                for key in turn_keys:
                    core_md.setdefault(key, internal_md.get(key))

        core_last["metadata"] = core_md
        out[-1] = core_last
        return out


__all__ = ["DurationExtension"]
