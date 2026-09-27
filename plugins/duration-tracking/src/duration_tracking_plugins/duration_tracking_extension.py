"""Duration tracking feature plugin.

Records one row per measured provider request into the SQLite duration
store and stamps the store-backed session totals into message metadata
so the chat status bar can show totals aggregated by workspace +
session id instead of stateless per-message values.

Measurement stays in the timestamp extension's duration feature
(``DurationExtension``), which stamps per-request duration facts onto
the assistant owner message. This plugin runs after it in the feature
finalize chain (higher priority number) and records from those stamps;
it never measures time itself.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

from agent_core.types import FeaturePlugin

from . import duration_store


def _format_duration_ms(duration_ms: int) -> str:
    """Render a duration the same way the duration feature renders its stamps."""

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


# Metadata keys promoted to public message metadata. The per-message
# duration stamps (``duration_ms`` and friends) belong to the duration
# feature; this plugin promotes only its own session-total keys.
_SESSION_METADATA_PREFIXES = (
    "duration_session_",
    "tool_duration_session_",
    "human_time_session_",
    "human_time_turn_",
)

_PRIMARY_DURATION_MODES = ("hidden", "llm", "llm_tools")
_ADDITIONAL_TIME_MODES = ("none", "tools", "human", "tools_human")
_DURATION_STATISTICS_MODES = ("none", "counts", "counts_averages")


class DurationTrackingExtension(FeaturePlugin):
    name: str = "duration_tracking"
    version: str = "0.1.0"
    priority: int = 210

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "track_durations": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": (
                    "Record per-request duration rows in the SQLite " "duration store."
                ),
            },
            "duration_tracking_db_path": {
                "type": "string",
                "required": False,
                "description": (
                    "Optional path override for the duration store. "
                    "Defaults to a duration-tracking/duration-tracking.sqlite3 "
                    "file under the Crystal data directory."
                ),
            },
            "show_duration_status_total": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": (
                    "Legacy fallback for showing the store-backed LLM "
                    "duration total. Use duration_primary instead."
                ),
            },
            "duration_breakdown": {
                "type": "string",
                "required": False,
                "default": "none",
                "label": "Duration breakdown",
                "options": ["none", "totals", "averages"],
                "description": (
                    "Legacy fallback for duration statistics and separate "
                    "tool fields. Use duration_statistics and "
                    "duration_additional_fields instead."
                ),
            },
            "duration_primary": {
                "type": "string",
                "required": False,
                "label": "Primary duration",
                "options": list(_PRIMARY_DURATION_MODES),
                "description": (
                    "Choose whether the main status field is hidden, shows "
                    "LLM duration only, or shows combined LLM and tool duration."
                ),
            },
            "duration_additional_fields": {
                "type": "string",
                "required": False,
                "label": "Additional time fields",
                "options": list(_ADDITIONAL_TIME_MODES),
                "description": (
                    "Choose whether tool duration, human time, both, or "
                    "neither are shown separately. Human time also enables "
                    "the completed-turn human-time message footer."
                ),
            },
            "duration_statistics": {
                "type": "string",
                "required": False,
                "label": "Duration statistics",
                "options": list(_DURATION_STATISTICS_MODES),
                "description": (
                    "Choose whether visible machine-duration categories show "
                    "call counts and averages."
                ),
            },
            "track_duration_tracking_summary_csv": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": (
                    "Append per-request rows with rolling session totals "
                    "to the summary CSV beside the SQLite store."
                ),
            },
            "duration_tracking_summary_csv_path": {
                "type": "string",
                "required": False,
                "description": (
                    "Optional path override for the summary CSV. Defaults "
                    "to duration-tracking-summary.csv beside the duration "
                    "store."
                ),
            },
        }

    # ------------------------------------------------------------------
    # UI elements
    # ------------------------------------------------------------------

    @staticmethod
    def _status_bar_element(data_path: str, template: str) -> Dict[str, Any]:
        return {
            "ui_type": "status_bar",
            "data": data_path,
            "template": template,
            "condition": {"path": data_path, "exists": True},
        }

    @staticmethod
    def _message_footer_element(data_path: str, template: str) -> Dict[str, Any]:
        return {
            "ui_type": "message_footer",
            "data": data_path,
            "template": template,
            "condition": {
                "all": [
                    {"path": data_path, "exists": True},
                    {"path": "role", "eq": "assistant"},
                    {"path": "metadata.tool_calls", "empty": True},
                ]
            },
        }

    @staticmethod
    def _additional_mode(*, tools: bool, human: bool) -> str:
        if tools and human:
            return "tools_human"
        if tools:
            return "tools"
        if human:
            return "human"
        return "none"

    @classmethod
    def _display_modes(cls, config: Optional[Dict[str, Any]]) -> Tuple[str, str, str]:
        cfg = config if isinstance(config, dict) else {}

        primary = cfg.get("duration_primary")
        if primary not in _PRIMARY_DURATION_MODES:
            primary = (
                "hidden" if cfg.get("show_duration_status_total") is False else "llm"
            )

        legacy_breakdown = cfg.get("duration_breakdown")
        if legacy_breakdown not in ("none", "totals", "averages"):
            legacy_breakdown = "none"

        additional = cfg.get("duration_additional_fields")
        if additional not in _ADDITIONAL_TIME_MODES:
            legacy_tools = primary != "hidden" and legacy_breakdown in (
                "totals",
                "averages",
            )
            legacy_human = cfg.get("show_human_time_status_total") is not False
            additional = cls._additional_mode(tools=legacy_tools, human=legacy_human)

        statistics = cfg.get("duration_statistics")
        if statistics not in _DURATION_STATISTICS_MODES:
            if primary == "hidden":
                statistics = "none"
            elif legacy_breakdown == "totals":
                statistics = "counts"
            elif legacy_breakdown == "averages":
                statistics = "counts_averages"
            else:
                statistics = "none"

        return primary, additional, statistics

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        _ = context
        primary, additional, statistics = self._display_modes(config)

        elements: List[Dict[str, Any]] = [
            {
                "ui_type": "config",
                "type": "select",
                "key": "duration_primary",
                "label": "Primary duration",
                "description": (
                    "Choose the meaning of the main session duration field."
                ),
                "options": [
                    {"value": "hidden", "label": "Hidden"},
                    {"value": "llm", "label": "LLM only"},
                    {"value": "llm_tools", "label": "LLM + tools"},
                ],
                "default": primary,
            },
            {
                "ui_type": "config",
                "type": "select",
                "key": "duration_additional_fields",
                "label": "Additional time fields",
                "description": (
                    "Show tool duration, human time, both, or neither "
                    "as additional fields."
                ),
                "options": [
                    {"value": "none", "label": "None"},
                    {"value": "tools", "label": "Tools"},
                    {"value": "human", "label": "Human"},
                    {"value": "tools_human", "label": "Tools + human"},
                ],
                "default": additional,
            },
            {
                "ui_type": "config",
                "type": "select",
                "key": "duration_statistics",
                "label": "Duration statistics",
                "description": "Show call counts and optional averages.",
                "options": [
                    {"value": "none", "label": "None"},
                    {"value": "counts", "label": "Counts"},
                    {
                        "value": "counts_averages",
                        "label": "Counts + averages",
                    },
                ],
                "default": statistics,
            },
        ]

        if primary == "llm":
            elements.append(
                self._status_bar_element(
                    "metadata.duration_session_total_formatted",
                    "LLM duration: {{data}}",
                )
            )
        elif primary == "llm_tools":
            elements.append(
                self._status_bar_element(
                    "metadata.duration_session_combined_total_formatted",
                    "Duration: {{data}}",
                )
            )

        show_tools = additional in ("tools", "tools_human")
        show_human = additional in ("human", "tools_human")
        if show_tools:
            elements.append(
                self._status_bar_element(
                    "metadata.tool_duration_session_total_formatted",
                    "Tool duration: {{data}}",
                )
            )
        if show_human:
            elements.extend(
                (
                    self._status_bar_element(
                        "metadata.human_time_session_total_formatted",
                        "Human time: {{data}}",
                    ),
                    self._message_footer_element(
                        "metadata.human_time_turn_delta_formatted",
                        "human time: {{data}}",
                    ),
                )
            )

        if statistics != "none":
            if primary != "hidden":
                elements.append(
                    self._status_bar_element(
                        "metadata.duration_session_requests_formatted",
                        "LLM calls: {{data}}",
                    )
                )
                if statistics == "counts_averages":
                    elements.append(
                        self._status_bar_element(
                            "metadata.duration_session_average_formatted",
                            "LLM average: {{data}}",
                        )
                    )
            if show_tools or primary == "llm_tools":
                elements.append(
                    self._status_bar_element(
                        "metadata.tool_duration_session_calls_formatted",
                        "Tool calls: {{data}}",
                    )
                )
                if statistics == "counts_averages":
                    elements.append(
                        self._status_bar_element(
                            "metadata.tool_duration_session_average_formatted",
                            "Tool average: {{data}}",
                        )
                    )
        return elements

    # ------------------------------------------------------------------
    # Request pipeline
    # ------------------------------------------------------------------

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        _ = context
        if not final_messages:
            return final_messages, native_messages, state

        # Re-finalize guard: finals already carrying the session totals
        # were processed in this request and must not record twice.
        if any(
            isinstance(item, dict)
            and isinstance(item.get("_metadata"), dict)
            and "duration_session_total" in item["_metadata"]
            for item in final_messages
        ):
            return final_messages, native_messages, state

        owner_idx = self._find_duration_owner_index(final_messages)
        if owner_idx is None:
            return final_messages, native_messages, state
        owner = final_messages[owner_idx]
        if not isinstance(owner, dict):
            return final_messages, native_messages, state
        source = owner.get("_metadata")
        if not isinstance(source, dict):
            return final_messages, native_messages, state

        machine_totals_md = self._record_and_build_metadata(source, state)
        if not machine_totals_md:
            return final_messages, native_messages, state
        human_totals_md = (
            self._build_human_time_metadata(state)
            if owner.get("role") == "assistant" and not self._has_tool_calls(owner)
            else {}
        )
        turn_md = self._human_time_turn_metadata(
            owner,
            final_messages=final_messages,
            native_messages=native_messages,
            totals_md=human_totals_md,
        )

        new_finals: List[Dict[str, Any]] = []
        for idx, item in enumerate(final_messages):
            if not isinstance(item, dict):
                new_finals.append(item)
                continue
            extra = (
                machine_totals_md
                if idx != owner_idx
                else {**machine_totals_md, **human_totals_md, **turn_md}
            )
            new_finals.append(self._attach_internal_md(item, extra))

        new_native = list(native_messages)
        if len(new_native) >= len(new_finals):
            start = len(new_native) - len(new_finals)
            for rel_idx in range(len(new_finals)):
                native_item = new_native[start + rel_idx]
                if isinstance(native_item, dict):
                    extra = (
                        machine_totals_md
                        if rel_idx != owner_idx
                        else {**machine_totals_md, **human_totals_md, **turn_md}
                    )
                    new_native[start + rel_idx] = self._attach_internal_md(
                        native_item, extra
                    )

        return new_finals, new_native, state

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
        state: Optional[Dict[str, Any]] = None,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Promote store-backed ``duration_session_*`` metadata to public metadata.

        Mirrors the cost tracking projection: assistant messages carry
        ``native_indices`` pointing at their native items, and the stamped
        session totals are read from those items.
        """

        _ = (state, context)
        out: List[Dict[str, Any]] = []
        for message in messages:
            if not isinstance(message, dict) or message.get("role") != "assistant":
                out.append(message)
                continue

            metadata_raw = message.get("metadata")
            metadata = dict(metadata_raw) if isinstance(metadata_raw, dict) else {}
            has_tool_calls = self._has_tool_calls(message)
            removed_human_metadata = False
            if has_tool_calls:
                filtered_metadata = {
                    key: value
                    for key, value in metadata.items()
                    if not (
                        isinstance(key, str) and key.startswith("human_time_")
                    )
                }
                removed_human_metadata = filtered_metadata != metadata
                metadata = filtered_metadata
            projected_message = (
                {**message, "metadata": metadata}
                if removed_human_metadata
                else message
            )
            native_indices = metadata.get("native_indices")
            if not isinstance(native_indices, list):
                out.append(projected_message)
                continue

            extra_md: Dict[str, Any] = {}
            for index in native_indices:
                if not isinstance(index, int) or not (
                    0 <= index < len(native_messages)
                ):
                    continue
                native_item = native_messages[index]
                if not isinstance(native_item, dict):
                    continue
                internal = native_item.get("_metadata")
                if not isinstance(internal, dict):
                    continue
                candidate = {
                    key: value
                    for key, value in internal.items()
                    if isinstance(key, str)
                    and key.startswith(_SESSION_METADATA_PREFIXES)
                    and not (has_tool_calls and key.startswith("human_time_"))
                }
                if candidate:
                    extra_md = candidate

            if not extra_md:
                out.append(projected_message)
                continue

            merged = dict(metadata)
            for key, value in extra_md.items():
                if key not in merged:
                    merged[key] = value
            out.append({**message, "metadata": merged})

        return out

    def finalize_tool_call(
        self,
        tool_message: Dict[str, Any],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Record one tool-call duration row from the stamped message.

        Runs after the duration feature in the tool-call hook chain, so
        the received core message already carries the per-call stamps in
        ``metadata``. Reads only that message plus the context facts —
        never the session history — and returns the message and state
        unchanged. Best-effort: store failures are swallowed so
        recording can never break tool execution.
        """

        self._record_tool_call_row(tool_message, state, context=context)
        return tool_message, state

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _record_tool_call_row(
        self,
        tool_message: Dict[str, Any],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record one tool-call row from the message stamps and context facts.

        Best-effort by contract: any failure is swallowed here so
        recording can never break tool execution.
        """

        try:
            metadata = tool_message.get("metadata")
            if not isinstance(metadata, dict):
                return
            if not self._is_duration_record_source(metadata):
                return

            ctx = context if isinstance(context, dict) else {}
            config = ctx.get("config")
            if not isinstance(config, dict):
                config = state.get("config") if isinstance(state, dict) else None
            if isinstance(config, dict) and config.get("track_durations") is False:
                return

            db_path = duration_store.resolve_duration_db_path(
                config if isinstance(config, dict) else None
            )
            finished_at = self._optional_str(metadata.get("duration_finished_at"))
            duration_store.record_tool_duration(
                db_path,
                session_id=self._optional_str(ctx.get("session_id")),
                working_directory=self._working_directory(config),
                model=(
                    config.get("model")
                    if isinstance(config, dict) and isinstance(config.get("model"), str)
                    else None
                ),
                request_id=self._optional_str(ctx.get("request_id")),
                tool_call_id=self._optional_str(ctx.get("tool_call_id")),
                tool_name=self._optional_str(ctx.get("tool_name")),
                tool_plugin=self._optional_str(ctx.get("tool_plugin")),
                duration_ms=int(metadata["duration_ms"]),
                duration_started_at=self._optional_str(
                    metadata.get("duration_started_at")
                ),
                duration_finished_at=finished_at,
                tool_error=self._optional_str(ctx.get("tool_error")),
                time=finished_at if finished_at else duration_store.utcnow_iso(),
            )
        except Exception:
            # Best-effort by contract: duration tracking failures must
            # never break tool execution.
            return

    @staticmethod
    def _is_duration_record_source(internal: Dict[str, Any]) -> bool:
        """The full duration stamp triple marks a measured request owner."""

        duration_ms = internal.get("duration_ms")
        if isinstance(duration_ms, bool) or not isinstance(duration_ms, (int, float)):
            return False
        if int(duration_ms) < 0:
            return False
        for key in ("duration_started_at", "duration_finished_at"):
            value = internal.get(key)
            if not isinstance(value, str) or not value:
                return False
        return True

    @classmethod
    def _find_duration_owner_index(cls, items: List[Dict[str, Any]]) -> Optional[int]:
        for idx in range(len(items) - 1, -1, -1):
            item = items[idx]
            if not isinstance(item, dict) or item.get("role") != "assistant":
                continue
            internal = item.get("_metadata")
            if isinstance(internal, dict) and cls._is_duration_record_source(internal):
                return idx
        return None

    @staticmethod
    def _has_tool_calls(message: Dict[str, Any]) -> bool:
        tool_calls = message.get("tool_calls")
        if isinstance(tool_calls, list) and tool_calls:
            return True
        for metadata_key in ("_metadata", "metadata"):
            internal = message.get(metadata_key)
            if not isinstance(internal, dict):
                continue
            tool_calls = internal.get("tool_calls")
            if isinstance(tool_calls, list) and tool_calls:
                return True
        return False

    @staticmethod
    def _human_total(message: Dict[str, Any]) -> Optional[int]:
        internal = message.get("_metadata")
        if not isinstance(internal, dict):
            return None
        value = internal.get("human_time_session_total")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        return max(0, int(value))

    @classmethod
    def _human_time_turn_metadata(
        cls,
        owner: Dict[str, Any],
        *,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        totals_md: Dict[str, Any],
    ) -> Dict[str, Any]:
        if owner.get("role") != "assistant" or cls._has_tool_calls(owner):
            return {}

        current_value = totals_md.get("human_time_session_total")
        if isinstance(current_value, bool) or not isinstance(
            current_value, (int, float)
        ):
            return {}
        current_total = max(0, int(current_value))

        history_offset = len(native_messages)
        if native_messages and len(final_messages) <= len(native_messages):
            history_offset = len(native_messages) - len(final_messages)
        history = native_messages[:history_offset]

        previous_total: Optional[int] = None
        found_previous_final = False
        for message in reversed(history):
            if not isinstance(message, dict):
                continue
            if message.get("role") != "assistant" or cls._has_tool_calls(message):
                continue
            found_previous_final = True
            previous_total = cls._human_total(message)
            break

        if found_previous_final and previous_total is None:
            return {}
        baseline = previous_total if previous_total is not None else 0
        if current_total < baseline:
            return {}

        delta = current_total - baseline
        return {
            "human_time_turn_delta": delta,
            "human_time_turn_delta_formatted": _format_duration_ms(delta),
        }

    def _record_and_build_metadata(
        self, internal: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Record one duration row (best-effort) and return the stamp metadata."""

        config = state.get("config") if isinstance(state, dict) else None
        if isinstance(config, dict) and config.get("track_durations") is False:
            return {}

        if not self._is_duration_record_source(internal):
            return {}

        db_path = duration_store.resolve_duration_db_path(
            config if isinstance(config, dict) else None
        )
        working_directory = self._working_directory(config)
        session_id = self._session_id_from_state(state)
        request_id = self._request_id_from_state(state)
        model = (
            config.get("model")
            if isinstance(config, dict) and isinstance(config.get("model"), str)
            else None
        )

        duration_ms = int(internal["duration_ms"])
        started_at = self._optional_str(internal.get("duration_started_at"))
        finished_at = self._optional_str(internal.get("duration_finished_at"))
        row_time = finished_at if finished_at else duration_store.utcnow_iso()

        recorded = False
        try:
            recorded = duration_store.record_request_duration(
                db_path,
                session_id=session_id,
                working_directory=working_directory,
                model=model,
                request_id=request_id,
                duration_ms=duration_ms,
                duration_started_at=started_at,
                duration_finished_at=finished_at,
                time=row_time,
            )
        except Exception:
            # Best-effort by contract: duration tracking failures must
            # never break the request pipeline.
            return {}

        if recorded:
            try:
                duration_store.append_request_summary_csv(
                    db_path,
                    config if isinstance(config, dict) else None,
                    session_id=session_id,
                    working_directory=working_directory,
                    model=model,
                    duration_ms=duration_ms,
                    time=row_time,
                )
            except Exception:
                # Best-effort: the summary CSV must never break the
                # request pipeline either.
                pass

        if working_directory is None or session_id is None:
            return {}

        try:
            totals = duration_store.session_totals(
                db_path, working_directory=working_directory, session_id=session_id
            )
            tool_totals = duration_store.tool_session_totals(
                db_path, working_directory=working_directory, session_id=session_id
            )
        except Exception:
            return {}

        total_ms = int(totals.get("total_ms") or 0)
        request_count = int(totals.get("request_count") or 0)
        metadata: Dict[str, Any] = {
            "duration_session_total": total_ms,
            "duration_session_total_formatted": _format_duration_ms(total_ms),
            "duration_session_requests": request_count,
        }
        if request_count > 0:
            metadata["duration_session_requests_formatted"] = f"{request_count:,}"
            average = total_ms / request_count
            metadata["duration_session_average"] = average
            metadata["duration_session_average_formatted"] = _format_duration_ms(
                int(average)
            )

        tool_total_ms = int(tool_totals.get("total_ms") or 0)
        tool_call_count = int(tool_totals.get("call_count") or 0)
        metadata["tool_duration_session_total"] = tool_total_ms
        metadata["tool_duration_session_total_formatted"] = _format_duration_ms(
            tool_total_ms
        )
        metadata["tool_duration_session_calls"] = tool_call_count
        if tool_call_count > 0:
            metadata["tool_duration_session_calls_formatted"] = f"{tool_call_count:,}"
            tool_average = tool_total_ms / tool_call_count
            metadata["tool_duration_session_average"] = tool_average
            metadata["tool_duration_session_average_formatted"] = _format_duration_ms(
                int(tool_average)
            )
        combined_total_ms = total_ms + tool_total_ms
        metadata["duration_session_combined_total"] = combined_total_ms
        metadata["duration_session_combined_total_formatted"] = _format_duration_ms(
            combined_total_ms
        )

        return metadata

    def _build_human_time_metadata(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Return store-backed human totals for a completed assistant turn."""

        config = state.get("config") if isinstance(state, dict) else None
        if isinstance(config, dict) and config.get("track_durations") is False:
            return {}
        working_directory = self._working_directory(config)
        session_id = self._session_id_from_state(state)
        if working_directory is None or session_id is None:
            return {}
        db_path = duration_store.resolve_duration_db_path(
            config if isinstance(config, dict) else None
        )
        try:
            human_totals = duration_store.human_time_session_totals(
                db_path, working_directory=working_directory, session_id=session_id
            )
        except Exception:
            return {}
        human_total_ms = int(human_totals.get("total_ms") or 0)
        return {
            "human_time_session_total": human_total_ms,
            "human_time_session_total_formatted": _format_duration_ms(
                human_total_ms
            ),
        }

    @staticmethod
    def _attach_internal_md(
        item: Dict[str, Any], extra_md: Dict[str, Any]
    ) -> Dict[str, Any]:
        base_md = item.get("_metadata")
        merged: Dict[str, Any] = {}
        if isinstance(base_md, dict):
            merged.update(base_md)
        merged.update(extra_md)
        return {**item, "_metadata": merged}

    @staticmethod
    def _optional_str(value: Any) -> Optional[str]:
        return value if isinstance(value, str) and value else None

    @staticmethod
    def _session_id_from_state(state: Optional[Dict[str, Any]]) -> Optional[str]:
        context = state.get("_request_context") if isinstance(state, dict) else None
        if isinstance(context, dict):
            value = context.get("session_id")
            if isinstance(value, str) and value:
                return value
        return None

    @staticmethod
    def _request_id_from_state(state: Optional[Dict[str, Any]]) -> Optional[str]:
        context = state.get("_request_context") if isinstance(state, dict) else None
        if isinstance(context, dict):
            value = context.get("request_id")
            if isinstance(value, str) and value:
                return value
        return None

    @staticmethod
    def _working_directory(config: Any) -> Optional[str]:
        if not isinstance(config, dict):
            return None
        raw = config.get("working_directory")
        if not isinstance(raw, str) or not raw.strip():
            return None
        return os.path.abspath(os.path.expanduser(raw))


__all__ = ["DurationTrackingExtension"]
