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
_SESSION_METADATA_PREFIXES = ("duration_session_", "tool_duration_session_")


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
                    "Show the store-backed session duration total in the "
                    "chat status bar."
                ),
            },
            "duration_breakdown": {
                "type": "string",
                "required": False,
                "default": "none",
                "label": "Duration breakdown",
                "options": ["none", "totals", "averages"],
                "description": (
                    "Show the session duration breakdown as separate "
                    "status bar fields: 'none' keeps only the total "
                    "footer, 'totals' shows the request count, 'averages' "
                    "shows the request count and per-request average. "
                    "Both variants are always stored in message metadata."
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

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        _ = context
        mode = config.get("duration_breakdown") if isinstance(config, dict) else None
        if mode not in ("none", "totals", "averages"):
            mode = "none"

        # The config element is always contributed (like the cost plugin's
        # breakdown setting) so the choice stays editable in the UI even
        # when the status bar elements are gated off.
        elements: List[Dict[str, Any]] = [
            {
                "ui_type": "config",
                "type": "select",
                "key": "duration_breakdown",
                "label": "Duration breakdown",
                "description": (
                    "Show the session duration breakdown as separate status "
                    "bar fields."
                ),
                "options": [
                    {"value": "none", "label": "None"},
                    {"value": "totals", "label": "Totals"},
                    {"value": "averages", "label": "Averages"},
                ],
                "default": mode,
            }
        ]

        if (
            isinstance(config, dict)
            and config.get("show_duration_status_total") is False
        ):
            return elements

        elements.append(
            self._status_bar_element(
                "metadata.duration_session_total_formatted", "Total duration: {{data}}"
            )
        )

        if mode == "totals":
            elements.append(
                self._status_bar_element(
                    "metadata.duration_session_requests_formatted", "requests: {{data}}"
                )
            )
            elements.extend(
                (
                    self._status_bar_element(
                        "metadata.tool_duration_session_total_formatted",
                        "tools: {{data}}",
                    ),
                    self._status_bar_element(
                        "metadata.tool_duration_session_calls_formatted",
                        "tool calls: {{data}}",
                    ),
                )
            )
        elif mode == "averages":
            elements.extend(
                (
                    self._status_bar_element(
                        "metadata.duration_session_requests_formatted",
                        "requests: {{data}}",
                    ),
                    self._status_bar_element(
                        "metadata.duration_session_average_formatted",
                        "average: {{data}}",
                    ),
                    self._status_bar_element(
                        "metadata.tool_duration_session_total_formatted",
                        "tools: {{data}}",
                    ),
                    self._status_bar_element(
                        "metadata.tool_duration_session_calls_formatted",
                        "tool calls: {{data}}",
                    ),
                    self._status_bar_element(
                        "metadata.tool_duration_session_average_formatted",
                        "tool average: {{data}}",
                    ),
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

        source = self._find_duration_metadata(
            [item for item in final_messages if isinstance(item, dict)]
        )
        if source is None:
            return final_messages, native_messages, state

        totals_md = self._record_and_build_metadata(source, state)
        if not totals_md:
            return final_messages, native_messages, state

        new_finals: List[Dict[str, Any]] = [
            (
                self._attach_internal_md(item, totals_md)
                if isinstance(item, dict)
                else item
            )
            for item in final_messages
        ]

        new_native = list(native_messages)
        if len(new_native) >= len(new_finals):
            start = len(new_native) - len(new_finals)
            for rel_idx in range(len(new_finals)):
                native_item = new_native[start + rel_idx]
                if isinstance(native_item, dict):
                    new_native[start + rel_idx] = self._attach_internal_md(
                        native_item, totals_md
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
            native_indices = metadata.get("native_indices")
            if not isinstance(native_indices, list):
                out.append(message)
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
                }
                if candidate:
                    extra_md = candidate

            if not extra_md:
                out.append(message)
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
    def _find_duration_metadata(
        cls, items: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        for item in reversed(items):
            internal = item.get("_metadata")
            if isinstance(internal, dict) and cls._is_duration_record_source(internal):
                return internal
        return None

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
        return metadata

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
