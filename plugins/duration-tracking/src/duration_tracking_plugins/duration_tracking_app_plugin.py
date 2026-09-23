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
            }
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
        db_path = self._db_path(app, state, session_id)
        report = duration_store.overall_totals(db_path)
        top_sessions = duration_store.top_sessions(db_path)
        top_projects = duration_store.top_projects(db_path)

        lines: List[str] = ["## Duration report", ""]
        lines.append(
            f"- Total duration: `{_format_duration_ms(int(report.get('total_ms') or 0))}`"
        )
        lines.append(f"- Requests: `{int(report.get('request_count') or 0):,}`")
        request_count = int(report.get("request_count") or 0)
        if request_count > 0:
            average = int(report.get("total_ms") or 0) / request_count
            lines.append(f"- Average: `{_format_duration_ms(int(average))}`")

        # Tool duration surfaces as separate lines, never merged into the
        # LLM total.
        tool_call_count = int(report.get("tool_call_count") or 0)
        tool_total_ms = int(report.get("tool_total_ms") or 0)
        if tool_call_count > 0:
            lines.append(f"- Tools: `{_format_duration_ms(tool_total_ms)}`")
            lines.append(f"- Tool calls: `{tool_call_count:,}`")
            tool_average = tool_total_ms / tool_call_count
            lines.append(f"- Tool average: `{_format_duration_ms(int(tool_average))}`")

        if request_count > 0:
            lines.append("")
            lines.append("### Top sessions")
            lines.append("")
            lines.append("| Project | Session | Total | Requests | Tools |")
            lines.append("| --- | --- | --- | --- | --- |")
            for entry in top_sessions:
                lines.append(
                    f"| {_project_display_name(entry.get('working_directory') or '')} "
                    f"| `{entry.get('session_id', '')}` "
                    f"| `{_format_duration_ms(int(entry.get('total_ms') or 0))}` "
                    f"| `{int(entry.get('request_count') or 0):,}` "
                    f"| `{_format_duration_ms(int(entry.get('tool_total_ms') or 0))}` |"
                )

            if top_projects:
                lines.append("")
                lines.append("### Top projects")
                lines.append("")
                lines.append("| Project | Total | Requests | Tools |")
                lines.append("| --- | --- | --- | --- |")
                for entry in top_projects:
                    lines.append(
                        f"| {_project_display_name(entry.get('working_directory') or '')} "
                        f"| `{_format_duration_ms(int(entry.get('total_ms') or 0))}` "
                        f"| `{int(entry.get('request_count') or 0):,}` "
                        f"| `{_format_duration_ms(int(entry.get('tool_total_ms') or 0))}` |"
                    )
        else:
            lines.append("")
            lines.append("No duration records yet.")

        lines.append("")
        lines.append(
            "Duration totals cover all recorded requests; there are no "
            "reset windows."
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
        }

    @staticmethod
    def _required_session_id(params: Dict[str, Any]) -> str:
        session_id = params.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id is required")
        return session_id


__all__ = ["DurationTrackingAppPlugin"]
