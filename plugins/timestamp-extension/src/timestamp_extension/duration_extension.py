"""Duration feature.

Measures wall-clock timestamps and elapsed duration for each provider request
and each tool call.

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
- Measures per-tool-call duration in :meth:`finalize_tool_call` from the
  framework-provided context facts (``started_at``/``finished_at``, wall and
  monotonic) and stamps it on the tool-result message metadata. The
  per-turn tool duration ("tool turn") sums tool-result durations since the
  last turn separator plus the current call, scanned from the session
  history available in the tool-call context. The framework never computes
  durations; this plugin owns the measurement.
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


def _sum_assistant_durations_since_turn_start(
    native_history: List[Dict[str, Any]],
) -> int:
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


def _core_message_has_tool_calls(core_msg: Dict[str, Any]) -> bool:
    """Return whether a core message dict carries tool calls."""
    tool_calls = core_msg.get("tool_calls")
    if isinstance(tool_calls, list) and tool_calls:
        return True
    metadata = core_msg.get("metadata") or {}
    if isinstance(metadata, dict):
        md_tool_calls = metadata.get("tool_calls")
        if isinstance(md_tool_calls, list) and md_tool_calls:
            return True
    return False


def _sum_tool_durations_since_turn_start(session_messages: List[Dict[str, Any]]) -> int:
    """Return cumulative tool-result duration since the last turn separator.

    Scans core session messages: the turn resets after the most recent
    user/system message or assistant message with no tool calls. Only
    ``role == "tool"`` messages contribute, so assistant LLM durations
    never leak into the tool turn.
    """

    last_sep_idx = -1
    for idx, msg in enumerate(session_messages):
        if not isinstance(msg, dict):
            continue
        role = msg.get("role")
        if role in ("user", "system"):
            last_sep_idx = idx
            continue
        if role == "assistant" and not _core_message_has_tool_calls(msg):
            last_sep_idx = idx

    total_ms = 0
    for idx, msg in enumerate(session_messages):
        if not isinstance(msg, dict):
            continue
        if idx <= last_sep_idx:
            continue
        if msg.get("role") != "tool":
            continue
        metadata = msg.get("metadata") or {}
        if not isinstance(metadata, dict):
            continue
        duration_ms = metadata.get("duration_ms")
        if isinstance(duration_ms, (int, float)) and not isinstance(duration_ms, bool):
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
    def _sum_durations_for_turn(
        cls, native_history: List[Dict[str, Any]], turn_id: Any
    ) -> int:
        total_ms = 0
        for msg in native_history:
            if not isinstance(msg, dict):
                continue
            if cls._turn_id(msg) != turn_id:
                continue
            internal_md = msg.get("_metadata") or {}
            if not isinstance(internal_md, dict):
                continue
            duration_ms = internal_md.get("duration_ms")
            if isinstance(duration_ms, (int, float)) and not isinstance(
                duration_ms, bool
            ):
                try:
                    total_ms += int(duration_ms)
                except Exception:
                    pass
        return total_ms

    @classmethod
    def _base_turn_duration_ms(
        cls, native_history: List[Dict[str, Any]], current_msg: Dict[str, Any]
    ) -> int:
        turn_id = cls._turn_id(current_msg)
        if turn_id is not None:
            return cls._sum_durations_for_turn(native_history, turn_id)
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

    @staticmethod
    def _format_turn_tps(turn_tps: float) -> str:
        rendered = f"{turn_tps:.2f}".rstrip("0").rstrip(".")
        return rendered

    @classmethod
    def _is_duration_owner_candidate(cls, native_msg: Dict[str, Any]) -> bool:
        if not isinstance(native_msg, dict):
            return False
        internal_md = native_msg.get("_metadata") or {}
        if not isinstance(internal_md, dict):
            return False
        if isinstance(internal_md.get("turn"), dict):
            return True
        if isinstance(internal_md.get("usage"), dict):
            return True
        return native_msg.get("role") == "assistant"

    @classmethod
    def _select_duration_owner_index(
        cls, final_messages: List[Dict[str, Any]]
    ) -> Optional[int]:
        if not final_messages:
            return None

        for idx in range(len(final_messages) - 1, -1, -1):
            msg = final_messages[idx]
            if not isinstance(msg, dict):
                continue
            internal_md = msg.get("_metadata") or {}
            if not isinstance(internal_md, dict):
                continue
            if isinstance(internal_md.get("turn"), dict):
                return idx

        for idx in range(len(final_messages) - 1, -1, -1):
            msg = final_messages[idx]
            if not isinstance(msg, dict):
                continue
            internal_md = msg.get("_metadata") or {}
            if not isinstance(internal_md, dict):
                continue
            if isinstance(internal_md.get("usage"), dict):
                return idx

        for idx in range(len(final_messages) - 1, -1, -1):
            msg = final_messages[idx]
            if isinstance(msg, dict) and msg.get("role") == "assistant":
                return idx

        for idx in range(len(final_messages) - 1, -1, -1):
            if isinstance(final_messages[idx], dict):
                return idx

        return None

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
                    {
                        "ui_type": "message_footer",
                        "data": "metadata.turn_tool_duration_formatted",
                        "template": "tool turn: {{data}}",
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

    def finalize_tool_call(
        self,
        tool_message: Dict[str, Any],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Stamp per-call and per-turn tool duration on the tool message.

        The measurement is owned by this plugin: the framework provides only
        raw facts in the context (``started_at``/``finished_at`` wall and
        monotonic timestamps, captured around execution). Without valid facts
        the message is returned unchanged — no fabricated values.

        The per-turn tool duration ("tool turn") sums tool-result durations
        from the session history available in the context (only
        ``role == "tool"`` messages since the last turn separator) plus the
        current call. Without a session in the context, only the per-call
        fields are stamped.
        """
        ctx = context if isinstance(context, dict) else {}

        started_at_mono = ctx.get("started_at_mono")
        finished_at_mono = ctx.get("finished_at_mono")
        if not isinstance(started_at_mono, (int, float)) or isinstance(
            started_at_mono, bool
        ):
            return tool_message, state
        if not isinstance(finished_at_mono, (int, float)) or isinstance(
            finished_at_mono, bool
        ):
            return tool_message, state

        started_at = ctx.get("started_at")
        finished_at = ctx.get("finished_at")
        if not isinstance(started_at, str) or not started_at:
            return tool_message, state
        if not isinstance(finished_at, str) or not finished_at:
            return tool_message, state

        try:
            duration_ms = max(
                0, int((float(finished_at_mono) - float(started_at_mono)) * 1000)
            )
        except Exception:
            return tool_message, state

        metadata = tool_message.get("metadata")
        merged: Dict[str, Any] = dict(metadata) if isinstance(metadata, dict) else {}
        merged.update(
            {
                "duration_started_at": started_at,
                "duration_finished_at": finished_at,
                "duration_ms": duration_ms,
                "duration_formatted": _format_duration_ms(duration_ms),
            }
        )

        session = ctx.get("session")
        session_messages = (
            session.get("messages") if isinstance(session, dict) else None
        )
        if isinstance(session_messages, list):
            turn_tool_ms = (
                _sum_tool_durations_since_turn_start(session_messages) + duration_ms
            )
            merged["turn_tool_duration_ms"] = turn_tool_ms
            merged["turn_tool_duration_formatted"] = _format_duration_ms(turn_tool_ms)

        return {**tool_message, "metadata": merged}, state

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
        owner_rel_idx = self._select_duration_owner_index(final_messages)

        def _stamp_owner(native_msg: Dict[str, Any]) -> Dict[str, Any]:
            if not self._is_duration_owner_candidate(native_msg):
                return native_msg

            internal_md = native_msg.get("_metadata") or {}
            if not isinstance(internal_md, dict):
                internal_md = {}

            base_turn_ms = self._base_turn_duration_ms(
                history_before_current, native_msg
            )
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

        stamped_finals = list(final_messages)
        if owner_rel_idx is not None and isinstance(
            stamped_finals[owner_rel_idx], dict
        ):
            stamped_finals[owner_rel_idx] = _stamp_owner(stamped_finals[owner_rel_idx])

        if not native_messages or len(stamped_finals) > len(native_messages):
            return stamped_finals, native_messages, state

        start = len(native_messages) - len(stamped_finals)
        stamped_history = list(native_messages)
        if owner_rel_idx is not None:
            hist_idx = start + owner_rel_idx
            if 0 <= hist_idx < len(stamped_history):
                hist_msg = stamped_history[hist_idx]
                if isinstance(hist_msg, dict):
                    stamped_history[hist_idx] = _stamp_owner(hist_msg)

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
            "turn_tool_duration_ms",
            "turn_tool_duration_formatted",
        )

        def _merge_duration_metadata(
            core_msg: Dict[str, Any],
            native_candidates: List[Dict[str, Any]],
        ) -> Dict[str, Any]:
            core_md_raw = core_msg.get("metadata")
            core_md: Dict[str, Any] = (
                dict(core_md_raw) if isinstance(core_md_raw, dict) else {}
            )

            chosen_internal: Optional[Dict[str, Any]] = None
            for native in native_candidates:
                if not isinstance(native, dict):
                    continue
                internal_md = native.get("_metadata") or {}
                if not isinstance(internal_md, dict):
                    continue
                if any(key in internal_md for key in duration_keys + turn_keys):
                    chosen_internal = internal_md

            if not isinstance(chosen_internal, dict):
                return {**core_msg, "metadata": core_md}

            for key in duration_keys:
                if key in chosen_internal and key not in core_md:
                    core_md[key] = chosen_internal.get(key)

            for key in turn_keys:
                if key in chosen_internal and key not in core_md:
                    core_md[key] = chosen_internal.get(key)

            return {**core_msg, "metadata": core_md}

        if len(messages) == len(native_messages):
            out: List[Dict[str, Any]] = []
            for msg, native in zip(messages, native_messages):
                out.append(_merge_duration_metadata(msg, [native]))
            return out

        out: List[Dict[str, Any]] = []
        for msg in messages:
            if not isinstance(msg, dict):
                out.append(msg)
                continue

            metadata_raw = msg.get("metadata")
            metadata = metadata_raw if isinstance(metadata_raw, dict) else {}
            native_indices = metadata.get("native_indices")
            if isinstance(native_indices, list):
                native_candidates = [
                    native_messages[index]
                    for index in native_indices
                    if isinstance(index, int) and 0 <= index < len(native_messages)
                ]
                out.append(_merge_duration_metadata(msg, native_candidates))
                continue

            out.append(msg)

        return out


__all__ = ["DurationExtension"]
