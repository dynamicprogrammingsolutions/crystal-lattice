"""Application plugin for the duration tracking report.

Exposes report and reset session actions backed by the SQLite duration
store. The report combines reset-aware current-project totals with fixed
seven-day cross-project views.

The store location is resolved the same way the duration tracking
feature resolves it, so both surfaces read and write the same
database. Reset markers preserve recorded history and affect only the
current-project report sections.
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
    """Application plugin exposing duration report, reset, and ingestion."""

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
            },
            {
                "ui_type": "session_action",
                "id": "duration_tracking_reset_project",
                "label": "Reset duration report",
                "icon": "rotate-ccw",
                "order": 15,
                "action_id": "reset_duration_tracking",
                "param_map": {"session_id": "$session.session_id"},
                "dialog": {
                    "kind": "confirm",
                    "title": "Reset duration report",
                    "message": (
                        "Start the current project's duration report from "
                        "now? Recorded history will be preserved."
                    ),
                },
            },
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
                    "Return reset-aware current-project totals and rankings, "
                    "plus fixed seven-day daily and cross-project views."
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
            {
                "id": "reset_duration_tracking",
                "label": "Reset duration report",
                "description": (
                    "Append a reset marker for the current project so its "
                    "report summary and rankings start from now. Recorded "
                    "history is preserved."
                ),
                "inputs": {
                    "session_id": {"type": "string", "required": True},
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
        if action_id == "reset_duration_tracking":
            return self._reset_duration_tracking(app, state, params)
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
        working_directory = self._resolve_working_directory(session_config)
        if working_directory is None:
            working_directory = self._resolve_working_directory(
                self._plugin_config(state)
            )
        if working_directory is None:
            raise ValueError(
                "[duration_tracking] working directory is required for the report"
            )

        project_summary = duration_store.project_totals_since_reset(
            db_path, working_directory=working_directory
        )
        daily_totals = duration_store.daily_duration_totals(db_path, days=7)
        top_projects = duration_store.top_projects_by_human_time_recent(
            db_path, days=7, limit=3
        )
        top_project_sessions = (
            duration_store.top_sessions_by_human_time_since_project_reset(
                db_path, working_directory=working_directory, limit=10
            )
        )
        top_recent_sessions = duration_store.top_sessions_by_human_time_recent(
            db_path, days=7, limit=10
        )
        top_llm_sessions = duration_store.top_sessions_by_llm_time_since_project_reset(
            db_path, working_directory=working_directory, limit=10
        )
        human_time_summary = duration_store.human_time_overall_totals(db_path)
        human_time_diagnostics, human_time = self._collect_human_time_diagnostics(
            db_path=db_path,
            state=state,
            session_id=session_id,
        )

        llm_total_ms = int(project_summary.get("llm_total_ms") or 0)
        tool_total_ms = int(project_summary.get("tool_total_ms") or 0)
        human_total_ms = int(project_summary.get("human_total_ms") or 0)
        request_count = int(project_summary.get("request_count") or 0)
        tool_call_count = int(project_summary.get("tool_call_count") or 0)
        reset_at = project_summary.get("last_reset_at")
        window_label = f"Since `{reset_at}`" if reset_at else "All recorded history"

        lines: List[str] = [
            "## Duration report",
            "",
            "### Current project since reset",
            "",
            f"- Project: `{_project_display_name(working_directory)}`",
            f"- Window: {window_label}",
            f"- LLM duration: `{_format_duration_ms(llm_total_ms)}`",
            f"- Tool duration: `{_format_duration_ms(tool_total_ms)}`",
            (
                "- LLM + tool duration: "
                f"`{_format_duration_ms(llm_total_ms + tool_total_ms)}`"
            ),
            f"- Human time: `{_format_duration_ms(human_total_ms)}`",
            (
                "- Session-less human time: "
                f"`{_format_duration_ms(int(project_summary.get('human_sessionless_ms') or 0))}`"
            ),
            f"- LLM calls: `{request_count:,}`",
        ]
        if request_count:
            lines.append(
                "- Average LLM call: "
                f"`{_format_duration_ms(int(llm_total_ms / request_count))}`"
            )
        lines.append(f"- Tool calls: `{tool_call_count:,}`")
        if tool_call_count:
            lines.append(
                "- Average tool call: "
                f"`{_format_duration_ms(int(tool_total_ms / tool_call_count))}`"
            )

        lines.extend(
            [
                "",
                "### Last 7 days",
                "",
                "| Day | LLM time | Tool time | Human time |",
                "| --- | --- | --- | --- |",
            ]
        )
        for day, totals in daily_totals.items():
            lines.append(
                f"| {day} "
                f"| `{_format_duration_ms(int(totals.get('llm_total_ms') or 0))}` "
                f"| `{_format_duration_ms(int(totals.get('tool_total_ms') or 0))}` "
                f"| `{_format_duration_ms(int(totals.get('human_total_ms') or 0))}` |"
            )

        if top_projects:
            lines.extend(
                [
                    "",
                    "### Top projects by human time — last 7 days",
                    "",
                    "| Project | Human time | Session-less human | LLM time | Tool time |",
                    "| --- | --- | --- | --- | --- |",
                ]
            )
            for entry in top_projects:
                lines.append(
                    f"| {_project_display_name(entry.get('working_directory') or '')} "
                    f"| `{_format_duration_ms(int(entry.get('human_total_ms') or 0))}` "
                    f"| `{_format_duration_ms(int(entry.get('human_sessionless_ms') or 0))}` "
                    f"| `{_format_duration_ms(int(entry.get('llm_total_ms') or 0))}` "
                    f"| `{_format_duration_ms(int(entry.get('tool_total_ms') or 0))}` |"
                )

        if top_project_sessions:
            lines.extend(
                [
                    "",
                    "### Top sessions by human time — current project since reset",
                    "",
                    "| Session | Human time | LLM time | Tool time |",
                    "| --- | --- | --- | --- |",
                ]
            )
            for entry in top_project_sessions:
                lines.append(
                    f"| `{entry.get('session_id', '')}` "
                    f"| `{_format_duration_ms(int(entry.get('human_total_ms') or 0))}` "
                    f"| `{_format_duration_ms(int(entry.get('llm_total_ms') or 0))}` "
                    f"| `{_format_duration_ms(int(entry.get('tool_total_ms') or 0))}` |"
                )

        if top_recent_sessions:
            lines.extend(
                [
                    "",
                    "### Top sessions by human time — last 7 days",
                    "",
                    "| Project | Session | Human time | LLM time | Tool time |",
                    "| --- | --- | --- | --- | --- |",
                ]
            )
            for entry in top_recent_sessions:
                lines.append(
                    f"| {_project_display_name(entry.get('working_directory') or '')} "
                    f"| `{entry.get('session_id', '')}` "
                    f"| `{_format_duration_ms(int(entry.get('human_total_ms') or 0))}` "
                    f"| `{_format_duration_ms(int(entry.get('llm_total_ms') or 0))}` "
                    f"| `{_format_duration_ms(int(entry.get('tool_total_ms') or 0))}` |"
                )

        if top_llm_sessions:
            lines.extend(
                [
                    "",
                    "### Top sessions by LLM duration — current project since reset",
                    "",
                    "| Session | LLM duration | LLM calls | Tool time | Human time |",
                    "| --- | --- | --- | --- | --- |",
                ]
            )
            for entry in top_llm_sessions:
                lines.append(
                    f"| `{entry.get('session_id', '')}` "
                    f"| `{_format_duration_ms(int(entry.get('llm_total_ms') or 0))}` "
                    f"| `{int(entry.get('request_count') or 0):,}` "
                    f"| `{_format_duration_ms(int(entry.get('tool_total_ms') or 0))}` "
                    f"| `{_format_duration_ms(int(entry.get('human_total_ms') or 0))}` |"
                )

        self._append_human_time_diagnostics(lines, human_time_diagnostics)
        lines.extend(
            [
                "",
                (
                    "The current-project summary and current-project rankings "
                    "start after that project's latest reset. Seven-day views "
                    "use fixed calendar dates and are not affected by resets."
                ),
            ]
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
            "report": project_summary,
            "project_summary_since_reset": project_summary,
            "daily_totals_last_7_days": daily_totals,
            "top_sessions": top_project_sessions,
            "top_projects": top_projects,
            "top_projects_last_7_days": top_projects,
            "top_sessions_project_since_reset": top_project_sessions,
            "top_sessions_last_7_days": top_recent_sessions,
            "top_sessions_by_llm_project_since_reset": top_llm_sessions,
            "human_time": human_time,
            "human_time_summary": human_time_summary,
            "human_time_top_sessions": top_project_sessions,
            "human_time_top_projects": top_projects,
            "human_time_diagnostics": human_time_diagnostics,
        }

    def _collect_human_time_diagnostics(
        self,
        *,
        db_path: Path,
        state: Dict[str, Any],
        session_id: str,
    ) -> tuple:
        """Return factual all-time collection diagnostics for the report."""

        diagnostics: Dict[str, Any] = {
            "session_collection_ready": False,
            "sessionless_collection_ready": False,
            "shared_store": False,
            "session": None,
            "application": None,
            "last_request_id": None,
            "last_processed_at": None,
        }
        application_working_directory = self._resolve_working_directory(
            self._plugin_config(state)
        )
        application_db_path = self._default_db_path(state)
        diagnostics.update(
            {
                "session_collection_ready": (application_working_directory is not None),
                "sessionless_collection_ready": (
                    application_working_directory is not None
                ),
                "shared_store": db_path.resolve() == application_db_path.resolve(),
            }
        )
        human_time: Optional[Dict[str, Any]] = None
        try:
            if application_working_directory is not None:
                session_diagnostics = duration_store.human_time_diagnostics(
                    application_db_path,
                    working_directory=application_working_directory,
                    session_id=session_id,
                )
                diagnostics["session"] = session_diagnostics
                if int(session_diagnostics.get("span_count") or 0) > 0:
                    human_time = {
                        "span_count": session_diagnostics["span_count"],
                        "total_ms": session_diagnostics["total_ms"],
                    }
        except Exception:
            diagnostics["session"] = None
        try:
            if application_working_directory is not None:
                diagnostics["application"] = duration_store.human_time_diagnostics(
                    application_db_path,
                    working_directory=application_working_directory,
                )
        except Exception:
            diagnostics["application"] = None

        candidates = [
            candidate
            for candidate in (
                diagnostics["session"],
                diagnostics["application"],
            )
            if isinstance(candidate, dict) and candidate.get("last_processed_at")
        ]
        if candidates:
            latest = max(candidates, key=lambda item: item["last_processed_at"])
            diagnostics["last_request_id"] = latest.get("last_request_id")
            diagnostics["last_processed_at"] = latest.get("last_processed_at")
        return diagnostics, human_time

    @staticmethod
    def _append_human_time_diagnostics(
        lines: List[str], diagnostics: Dict[str, Any]
    ) -> None:
        lines.extend(["", "### Human time diagnostics", ""])
        lines.append(
            "- Session collection: "
            f"`{'Ready' if diagnostics['session_collection_ready'] else 'Missing working directory'}`"
        )
        lines.append(
            "- Session-less collection: "
            f"`{'Ready' if diagnostics['sessionless_collection_ready'] else 'Missing application working directory'}`"
        )
        lines.append(
            "- Storage targets: "
            f"`{'Shared' if diagnostics['shared_store'] else 'Separate'}`"
        )
        session_diagnostics = diagnostics["session"]
        if isinstance(session_diagnostics, dict):
            span_count = int(session_diagnostics.get("span_count") or 0)
            lines.append(
                "- Current session stored total: "
                f"`{_format_duration_ms(int(session_diagnostics.get('total_ms') or 0))}` "
                f"across `{span_count:,}` stored "
                f"{'span' if span_count == 1 else 'spans'}"
            )
        application_diagnostics = diagnostics["application"]
        if isinstance(application_diagnostics, dict):
            span_count = int(application_diagnostics.get("span_count") or 0)
            lines.append(
                "- Application workspace stored total: "
                f"`{_format_duration_ms(int(application_diagnostics.get('total_ms') or 0))}` "
                f"across `{span_count:,}` stored "
                f"{'span' if span_count == 1 else 'spans'}"
            )
        if diagnostics["last_processed_at"]:
            lines.append(
                "- Last upload received: "
                f"`{diagnostics['last_processed_at']}` "
                f"(`{diagnostics['last_request_id']}`)"
            )
        else:
            lines.append("- Last upload received: `Never`")

    def _reset_duration_tracking(
        self, app: Any, state: Dict[str, Any], params: Dict[str, Any]
    ) -> Dict[str, Any]:
        session_id = self._required_session_id(params)
        session_config = self._session_config(app, session_id)
        working_directory = self._resolve_working_directory(session_config)
        if working_directory is None:
            working_directory = self._resolve_working_directory(
                self._plugin_config(state)
            )
        if working_directory is None:
            raise ValueError(
                "[duration_tracking] working directory is required to reset the report"
            )
        db_path = self._db_path_from_session_config(session_config, state)
        marker = duration_store.reset_project(
            db_path, working_directory=working_directory
        )
        report = duration_store.project_totals_since_reset(
            db_path, working_directory=working_directory
        )
        project_name = _project_display_name(working_directory)
        return {
            "display": {
                "format": "markdown",
                "title": "Duration report reset",
                "body": (
                    f"Started the duration report for `{project_name}` from "
                    f"`{marker.get('reset_at')}`. Recorded history was preserved. "
                    "Seven-day cross-project views are unchanged."
                ),
                "variant": "success",
                "presentation": "modal",
                "dismissible": True,
                "display_id": "duration-tracking-reset",
            },
            "reset": marker,
            "report": report,
            "project_summary_since_reset": report,
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
        working_directory: str,
    ) -> Optional[Dict[str, Any]]:
        """Attach application-level project attribution to one span."""

        if not isinstance(span, dict):
            return None
        session_id = span.get("session_id")
        if session_id is not None and (
            not isinstance(session_id, str) or not session_id
        ):
            return None
        return {**span, "working_directory": working_directory}

    def _record_human_time_spans(
        self, app: Any, state: Dict[str, Any], params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Record one frontend-reported human time span batch (machine-facing)."""

        _ = app
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

        working_directory = self._resolve_working_directory(self._plugin_config(state))
        if working_directory is None:
            raise ValueError(
                "duration tracking application working_directory is not configured"
            )
        db_path = self._default_db_path(state)
        resolved_spans: List[Dict[str, Any]] = []
        skipped = 0
        for span in spans:
            resolved = self._resolve_span_target(span, working_directory)
            if resolved is None:
                skipped += 1
                continue
            resolved_spans.append(resolved)

        totals: Dict[str, int] = {
            "recorded": 0,
            "merged": 0,
            "skipped": skipped,
            "absorbed": 0,
        }
        invalid_count = duration_store.count_invalid_human_time_spans(resolved_spans)
        totals["skipped"] += invalid_count
        if totals["skipped"] > 0:
            return {**totals, "duplicate": False}

        if not resolved_spans:
            return {**totals, "duplicate": False}

        result = duration_store.record_human_time_spans(
            db_path,
            working_directory=None,
            request_id=request_id,
            spans=resolved_spans,
        )
        return {
            **totals,
            **{key: value for key, value in result.items() if key != "duplicate"},
            "duplicate": bool(result.get("duplicate")),
        }


__all__ = ["DurationTrackingAppPlugin"]
