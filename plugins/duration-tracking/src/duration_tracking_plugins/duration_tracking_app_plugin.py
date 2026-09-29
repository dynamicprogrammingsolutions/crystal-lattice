"""Application plugin for the duration tracking report.

Exposes one session action backed by the SQLite duration store: a
report showing the overall recorded duration, the request count, the
per-request average, and the top sessions and projects by duration.

The store location is resolved the same way the duration tracking
feature resolves it, so both surfaces read and write the same
database. Duration is factual history: the report has no reset
windows.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent_app.app_plugins import ApplicationPlugin

from . import duration_store
from .duration_tracking_extension import _format_duration_ms


def _project_display_name(working_directory: str) -> str:
    """Resolve a working directory to a project name.

    Reads ``projects.json`` under the Crystal data directory
    (``CRYSTAL_DATA_DIR``, default ``~/.crystal``) and returns the
    project's ``name`` for the exact path, falling back to the raw path.
    Best-effort: unreadable or malformed files fall back silently.
    """

    data_dir = os.environ.get("CRYSTAL_DATA_DIR")
    base = (
        Path(data_dir)
        if isinstance(data_dir, str) and data_dir
        else Path.home() / ".crystal"
    )
    try:
        payload = json.loads((base / "projects.json").read_text(encoding="utf-8"))
    except Exception:
        return working_directory
    if not isinstance(payload, dict):
        return working_directory
    projects = payload.get("projects")
    if not isinstance(projects, dict):
        return working_directory
    entry = projects.get(working_directory)
    if isinstance(entry, dict):
        name = entry.get("name")
        if isinstance(name, str) and name:
            return name
    return working_directory


class DurationTrackingAppPlugin(ApplicationPlugin):
    """Application plugin exposing the duration report action."""

    name = "duration_tracking_app"
    version = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "duration_tracking": {
                "type": "object",
                "description": ("Settings for the duration tracking report action."),
            }
        }

    def get_ui_elements(
        self,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        _ = (state, config, context)
        return [
            {
                "ui_type": "session_action",
                "id": "duration_tracking_show_report",
                "label": "Show duration report",
                "icon": "bar-chart",
                "order": 14,
                "action_id": "show_duration_report",
                "param_map": {"session_id": "$session.session_id"},
                "dialog": {"kind": "none"},
            }
        ]

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        application_cfg = app_config.get("application")
        if not isinstance(application_cfg, dict):
            application_cfg = {}
        plugin_cfg = application_cfg.get("duration_tracking")
        if not isinstance(plugin_cfg, dict):
            plugin_cfg = {}
        configured_working_directory = plugin_cfg.get("working_directory")
        if not (
            isinstance(configured_working_directory, str)
            and configured_working_directory.strip()
        ):
            runtime_working_directory = os.environ.get("WORKING_DIR")
            if isinstance(runtime_working_directory, str) and runtime_working_directory:
                plugin_cfg = {
                    **plugin_cfg,
                    "working_directory": runtime_working_directory,
                }
        return {"config": plugin_cfg}

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return [
            {
                "id": "show_duration_report",
                "label": "Show duration report",
                "description": (
                    "Return the overall recorded duration, request count, "
                    "and average, plus the top sessions and projects by "
                    "duration."
                ),
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                },
            },
            {
                "id": "record_human_time_spans",
                "label": "Record human time spans",
                "description": (
                    "Record frontend-reported human time spans (session id "
                    "or null, from, to) in batches; deduplicated by the "
                    "frontend-assigned request id."
                ),
                "inputs": {
                    "request_id": {"type": "string", "required": True},
                    "spans": {"type": "array", "required": True},
                },
            },
        ]

    def get_commands(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return []

    def execute_action(
        self,
        app: Any,
        action_id: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        if action_id == "show_duration_report":
            return self._show_duration_report(app, state, params)
        if action_id == "record_human_time_spans":
            return self._record_human_time_spans(app, state, params)
        raise KeyError(f"Unknown action_id {action_id!r}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _plugin_config(self, state: Dict[str, Any]) -> Dict[str, Any]:
        raw = state.get("config")
        return raw if isinstance(raw, dict) else {}

    def _session_config(self, app: Any, session_id: str) -> Dict[str, Any]:
        ctx = app.load_session(session_id)
        if ctx is None:
            raise KeyError(f"Session {session_id!r} not found")
        _core, base_config, _session = ctx
        return base_config if isinstance(base_config, dict) else {}

    def _db_path(self, app: Any, state: Dict[str, Any], session_id: str) -> Path:
        session_config = self._session_config(app, session_id)
        return self._db_path_from_session_config(session_config, state)

    def _db_path_from_session_config(
        self, session_config: Dict[str, Any], state: Dict[str, Any]
    ) -> Path:
        override = session_config.get("duration_tracking_db_path")
        if not (isinstance(override, str) and override.strip()):
            override = self._plugin_config(state).get("db_path")
        config = (
            {"duration_tracking_db_path": override}
            if isinstance(override, str) and override.strip()
            else {}
        )
        return duration_store.resolve_duration_db_path(config)

    def _show_duration_report(
        self, app: Any, state: Dict[str, Any], params: Dict[str, Any]
    ) -> Dict[str, Any]:
        session_id = self._required_session_id(params)
        session_config = self._session_config(app, session_id)
        db_path = self._db_path_from_session_config(session_config, state)
        report = duration_store.overall_totals(db_path)
        top_sessions = duration_store.top_sessions(db_path)
        top_projects = duration_store.top_projects(db_path)
        human_time_summary = duration_store.human_time_overall_totals(db_path)
        human_time_top_sessions = duration_store.top_human_time_sessions(
            db_path, limit=10
        )
        human_time_top_projects = duration_store.top_human_time_projects(
            db_path, limit=3
        )

        llm_total_ms = int(report.get("total_ms") or 0)
        tool_total_ms = int(report.get("tool_total_ms") or 0)
        combined_total_ms = llm_total_ms + tool_total_ms
        report = {**report, "combined_total_ms": combined_total_ms}

        lines: List[str] = ["## Duration report", ""]
        lines.append(f"- LLM duration: `{_format_duration_ms(llm_total_ms)}`")
        lines.append(f"- Tool duration: `{_format_duration_ms(tool_total_ms)}`")
        lines.append(
            f"- LLM + tool duration: `{_format_duration_ms(combined_total_ms)}`"
        )
        lines.append(
            "- Total human time: "
            f"`{_format_duration_ms(int(human_time_summary.get('total_ms') or 0))}`"
        )
        request_count = int(report.get("request_count") or 0)
        lines.append(f"- LLM calls: `{request_count:,}`")
        if request_count > 0:
            average = llm_total_ms / request_count
            lines.append(f"- Average LLM call: `{_format_duration_ms(int(average))}`")

        tool_call_count = int(report.get("tool_call_count") or 0)
        lines.append(f"- Tool calls: `{tool_call_count:,}`")
        if tool_call_count > 0:
            tool_average = tool_total_ms / tool_call_count
            lines.append(
                f"- Average tool call: `{_format_duration_ms(int(tool_average))}`"
            )

        # Human time (subtasks 030/035): show the current session's total and
        # compact collection diagnostics. Best-effort: a store failure never
        # breaks the duration report.
        human_time: Optional[Dict[str, Any]] = None
        human_time_diagnostics: Dict[str, Any] = {
            "session_collection_ready": False,
            "sessionless_collection_ready": False,
            "shared_store": False,
            "session": None,
            "application": None,
            "last_request_id": None,
            "last_processed_at": None,
        }
        working_directory = self._resolve_working_directory(session_config)
        application_working_directory = self._resolve_working_directory(
            self._plugin_config(state)
        )
        application_db_path = self._default_db_path(state)
        human_time_diagnostics.update(
            {
                "session_collection_ready": working_directory is not None,
                "sessionless_collection_ready": (
                    application_working_directory is not None
                ),
                "shared_store": db_path.resolve() == application_db_path.resolve(),
            }
        )
        try:
            if working_directory is not None:
                session_diagnostics = duration_store.human_time_diagnostics(
                    db_path,
                    working_directory=working_directory,
                    session_id=session_id,
                )
                human_time_diagnostics["session"] = session_diagnostics
                human_time = {
                    "span_count": session_diagnostics["span_count"],
                    "total_ms": session_diagnostics["total_ms"],
                }
        except Exception:
            human_time = None
            human_time_diagnostics["session"] = None
        try:
            if application_working_directory is not None:
                human_time_diagnostics["application"] = (
                    duration_store.human_time_diagnostics(
                        application_db_path,
                        working_directory=application_working_directory,
                    )
                )
        except Exception:
            human_time_diagnostics["application"] = None

        candidates = [
            candidate
            for candidate in (
                human_time_diagnostics["session"],
                human_time_diagnostics["application"],
            )
            if isinstance(candidate, dict) and candidate.get("last_processed_at")
        ]
        if candidates:
            latest = max(candidates, key=lambda item: item["last_processed_at"])
            human_time_diagnostics["last_request_id"] = latest.get("last_request_id")
            human_time_diagnostics["last_processed_at"] = latest.get(
                "last_processed_at"
            )

        if human_time and int(human_time.get("span_count") or 0) > 0:
            lines.append(
                "- Current session human time: "
                f"`{_format_duration_ms(int(human_time.get('total_ms') or 0))}`"
            )
        else:
            human_time = None

        lines.extend(["", "### Human time", ""])
        human_span_count = int(human_time_summary.get("span_count") or 0)
        lines.append("- Stored spans: " f"`{human_span_count:,}`")
        if human_time_top_sessions:
            lines.extend(
                [
                    "",
                    "#### Top sessions by human time",
                    "",
                    "| Project | Session | Human time | Spans |",
                    "| --- | --- | --- | --- |",
                ]
            )
            for entry in human_time_top_sessions:
                lines.append(
                    f"| {_project_display_name(entry.get('working_directory') or '')} "
                    f"| `{entry.get('session_id', '')}` "
                    f"| `{_format_duration_ms(int(entry.get('total_ms') or 0))}` "
                    f"| `{int(entry.get('span_count') or 0):,}` |"
                )
        if human_time_top_projects:
            lines.extend(
                [
                    "",
                    "#### Top projects by human time",
                    "",
                    "| Project | Human time | Session-less | Spans |",
                    "| --- | --- | --- | --- |",
                ]
            )
            for entry in human_time_top_projects:
                lines.append(
                    f"| {_project_display_name(entry.get('working_directory') or '')} "
                    f"| `{_format_duration_ms(int(entry.get('total_ms') or 0))}` "
                    f"| `{_format_duration_ms(int(entry.get('sessionless_ms') or 0))}` "
                    f"| `{int(entry.get('span_count') or 0):,}` |"
                )
        if human_span_count == 0:
            lines.extend(["", "No human time records yet."])

        lines.extend(["", "### Human time diagnostics", ""])
        lines.append(
            "- Session collection: "
            f"`{'Ready' if human_time_diagnostics['session_collection_ready'] else 'Missing working directory'}`"
        )
        lines.append(
            "- Session-less collection: "
            f"`{'Ready' if human_time_diagnostics['sessionless_collection_ready'] else 'Missing application working directory'}`"
        )
        lines.append(
            "- Storage targets: "
            f"`{'Shared' if human_time_diagnostics['shared_store'] else 'Separate'}`"
        )
        session_diagnostics = human_time_diagnostics["session"]
        if isinstance(session_diagnostics, dict):
            session_span_count = int(session_diagnostics.get("span_count") or 0)
            lines.append(
                "- Current session: "
                f"`{_format_duration_ms(int(session_diagnostics.get('total_ms') or 0))}` "
                f"across `{session_span_count:,}` stored "
                f"{'span' if session_span_count == 1 else 'spans'}"
            )
        application_diagnostics = human_time_diagnostics["application"]
        if isinstance(application_diagnostics, dict):
            application_span_count = int(application_diagnostics.get("span_count") or 0)
            lines.append(
                "- Application workspace: "
                f"`{_format_duration_ms(int(application_diagnostics.get('total_ms') or 0))}` "
                f"across `{application_span_count:,}` stored "
                f"{'span' if application_span_count == 1 else 'spans'}"
            )
        if human_time_diagnostics["last_processed_at"]:
            lines.append(
                "- Last upload received: "
                f"`{human_time_diagnostics['last_processed_at']}` "
                f"(`{human_time_diagnostics['last_request_id']}`)"
            )
        else:
            lines.append("- Last upload received: `Never`")

        if request_count > 0:
            lines.append("")
            lines.append("### Top sessions by LLM duration")
            lines.append("")
            lines.append(
                "| Project | Session | LLM duration | LLM calls | "
                "Tool duration | Combined |"
            )
            lines.append("| --- | --- | --- | --- | --- | --- |")
            for entry in top_sessions:
                entry_llm_ms = int(entry.get("total_ms") or 0)
                entry_tool_ms = int(entry.get("tool_total_ms") or 0)
                lines.append(
                    f"| {_project_display_name(entry.get('working_directory') or '')} "
                    f"| `{entry.get('session_id', '')}` "
                    f"| `{_format_duration_ms(entry_llm_ms)}` "
                    f"| `{int(entry.get('request_count') or 0):,}` "
                    f"| `{_format_duration_ms(entry_tool_ms)}` "
                    f"| `{_format_duration_ms(entry_llm_ms + entry_tool_ms)}` |"
                )

            if top_projects:
                lines.append("")
                lines.append("### Top projects by LLM duration")
                lines.append("")
                lines.append(
                    "| Project | LLM duration | LLM calls | Tool duration | Combined |"
                )
                lines.append("| --- | --- | --- | --- | --- |")
                for entry in top_projects:
                    entry_llm_ms = int(entry.get("total_ms") or 0)
                    entry_tool_ms = int(entry.get("tool_total_ms") or 0)
                    lines.append(
                        f"| {_project_display_name(entry.get('working_directory') or '')} "
                        f"| `{_format_duration_ms(entry_llm_ms)}` "
                        f"| `{int(entry.get('request_count') or 0):,}` "
                        f"| `{_format_duration_ms(entry_tool_ms)}` "
                        f"| `{_format_duration_ms(entry_llm_ms + entry_tool_ms)}` |"
                    )
        else:
            lines.append("")
            lines.append("No duration records yet.")

        lines.append("")
        lines.append(
            "LLM and tool duration totals cover all recorded calls; there "
            "are no reset windows."
        )

        return {
            "display": {
                "format": "markdown",
                "title": "Duration report",
                "body": "\n".join(lines),
                "variant": "info",
                "presentation": "modal",
                "dismissible": True,
                "display_id": "duration-tracking-report",
            },
            "report": report,
            "top_sessions": top_sessions,
            "top_projects": top_projects,
            "human_time": human_time,
            "human_time_summary": human_time_summary,
            "human_time_top_sessions": human_time_top_sessions,
            "human_time_top_projects": human_time_top_projects,
            "human_time_diagnostics": human_time_diagnostics,
        }

    @staticmethod
    def _required_session_id(params: Dict[str, Any]) -> str:
        session_id = params.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id is required")
        return session_id

    # ------------------------------------------------------------------
    # Human time span ingestion (subtask 030)
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_working_directory(config: Any) -> Optional[str]:
        """Mirror the tracking extension's working-directory resolution."""

        if not isinstance(config, dict):
            return None
        raw = config.get("working_directory")
        if not isinstance(raw, str) or not raw.strip():
            return None
        return os.path.abspath(os.path.expanduser(raw))

    def _default_db_path(self, state: Dict[str, Any]) -> Path:
        override = self._plugin_config(state).get("db_path")
        config = (
            {"duration_tracking_db_path": override}
            if isinstance(override, str) and override.strip()
            else {}
        )
        return duration_store.resolve_duration_db_path(config)

    def _resolve_span_target(
        self,
        span: Any,
        app: Any,
        state: Dict[str, Any],
        default_db_path: Path,
    ) -> Optional[Dict[str, Any]]:
        """Resolve one span's store location and working directory.

        Spans with a session id follow their session's resolved config (the
        same keying as the LLM/tool rows); unknown sessions skip the span.
        Session-less spans use the plugin config's ``working_directory``
        (defaulted from the runtime ``WORKING_DIR`` during initialization);
        without either value they cannot be keyed and skip.
        """

        if not isinstance(span, dict):
            return None
        session_id = span.get("session_id")
        if session_id is None:
            plugin_wd = self._resolve_working_directory(self._plugin_config(state))
            if plugin_wd is None:
                return None
            return {**span, "working_directory": plugin_wd}
        if not isinstance(session_id, str) or not session_id:
            return None
        ctx = app.load_session(session_id)
        if ctx is None:
            return None
        base_config = ctx[1] if isinstance(ctx, tuple) and len(ctx) > 1 else None
        base_config = base_config if isinstance(base_config, dict) else {}
        working_directory = self._resolve_working_directory(base_config)
        if working_directory is None:
            return None
        override = base_config.get("duration_tracking_db_path")
        db_path = (
            Path(override).expanduser()
            if isinstance(override, str) and override.strip()
            else default_db_path
        )
        return {**span, "working_directory": working_directory, "_db_path": db_path}

    def _record_human_time_spans(
        self, app: Any, state: Dict[str, Any], params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Record one frontend-reported human time span batch (machine-facing)."""

        request_id = params.get("request_id")
        if not isinstance(request_id, str) or not request_id.strip():
            raise ValueError("request_id is required")
        spans = params.get("spans")
        if not isinstance(spans, list):
            raise ValueError("spans must be a list")
        if len(spans) > duration_store.HUMAN_TIME_SPANS_BATCH_CAP:
            raise ValueError(
                "spans batch exceeds the "
                f"{duration_store.HUMAN_TIME_SPANS_BATCH_CAP}-span cap"
            )

        default_db_path = self._default_db_path(state)
        resolved_spans: List[tuple[Path, Dict[str, Any]]] = []
        skipped = 0
        for span in spans:
            resolved = self._resolve_span_target(span, app, state, default_db_path)
            if resolved is None:
                skipped += 1
                continue
            db_path = resolved.pop("_db_path", default_db_path)
            resolved_spans.append((db_path, resolved))

        totals: Dict[str, int] = {
            "recorded": 0,
            "merged": 0,
            "skipped": skipped,
            "absorbed": 0,
        }
        invalid_count = duration_store.count_invalid_human_time_spans(
            [span for _db_path, span in resolved_spans]
        )
        totals["skipped"] += invalid_count
        if totals["skipped"] > 0:
            return {**totals, "duplicate": False}

        groups: Dict[Path, List[Dict[str, Any]]] = {}
        for db_path, resolved in resolved_spans:
            groups.setdefault(db_path, []).append(resolved)

        all_duplicates = bool(groups)
        for db_path, group_spans in groups.items():
            result = duration_store.record_human_time_spans(
                db_path,
                working_directory=None,
                request_id=request_id,
                spans=group_spans,
            )
            for key, value in result.items():
                if isinstance(value, bool):
                    continue
                totals[key] = totals.get(key, 0) + int(value)
            all_duplicates = all_duplicates and bool(result.get("duplicate"))
        return {**totals, "duplicate": all_duplicates}


__all__ = ["DurationTrackingAppPlugin"]
