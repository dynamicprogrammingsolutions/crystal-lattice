"""Application plugin for the generic cost tracking reports.

Exposes session actions backed by the SQLite cost store:

- a cost report showing reset-aware totals per bucket and overall;
- a reset action that appends a reset marker for one specific bucket.

The store location is resolved the same way the cost tracking extension
resolves it, so both surfaces read and write the same database.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from . import cost_store


def _format_cost(value: Any) -> str:
    try:
        return f"${float(value):.6f}"
    except (TypeError, ValueError):
        return "$0.000000"


class CostTrackingAppPlugin:
    """Application plugin exposing cost report and reset actions."""

    name = "cost_tracking_app"
    version = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "cost_tracking": {
                "type": "object",
                "description": (
                    "Settings for the generic cost tracking reports and "
                    "reset action."
                ),
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
                "id": "cost_tracking_show_report",
                "label": "Show cost report",
                "icon": "bar-chart",
                "order": 12,
                "action_id": "show_cost_report",
                "param_map": {"session_id": "$session.session_id"},
                "dialog": {"kind": "none"},
            },
            {
                "ui_type": "session_action",
                "id": "cost_tracking_reset_bucket",
                "label": "Reset cost tracking",
                "icon": "rotate-ccw",
                "order": 13,
                "action_id": "reset_cost_tracking",
                "param_map": {"session_id": "$session.session_id"},
                "dialog": {
                    "kind": "form",
                    "title": "Reset cost tracking",
                    "inputs": [
                        {
                            "name": "bucket",
                            "type": "text",
                            "label": "Bucket",
                            "required": True,
                            "placeholder": "e.g. openai-responses-chatgpt",
                            "description": (
                                "Reset report totals for this provider-defined "
                                "cost bucket. Recorded history is preserved."
                            ),
                        },
                    ],
                },
            },
        ]

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        application_cfg = app_config.get("application")
        if not isinstance(application_cfg, dict):
            application_cfg = {}
        plugin_cfg = application_cfg.get("cost_tracking")
        if not isinstance(plugin_cfg, dict):
            plugin_cfg = {}
        return {"config": plugin_cfg}

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return [
            {
                "id": "show_cost_report",
                "label": "Show cost report",
                "description": (
                    "Return cost totals per provider-defined bucket and "
                    "overall, counted since each bucket's last reset."
                ),
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                },
            },
            {
                "id": "reset_cost_tracking",
                "label": "Reset cost tracking",
                "description": (
                    "Append a reset marker for one bucket so its report "
                    "totals start from now. Recorded history is preserved."
                ),
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                    "bucket": {"type": "string", "required": True},
                },
            },
        ]

    def execute_action(
        self,
        app: Any,
        action_id: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        if action_id == "show_cost_report":
            return self._show_cost_report(app, state, params)
        if action_id == "reset_cost_tracking":
            return self._reset_cost_tracking(app, state, params)
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
        override = session_config.get("cost_tracking_db_path")
        if not (isinstance(override, str) and override.strip()):
            override = self._plugin_config(state).get("db_path")
        config = (
            {"cost_tracking_db_path": override}
            if isinstance(override, str) and override.strip()
            else {}
        )
        return cost_store.resolve_cost_db_path(config)

    def _show_cost_report(
        self, app: Any, state: Dict[str, Any], params: Dict[str, Any]
    ) -> Dict[str, Any]:
        session_id = self._required_session_id(params)
        db_path = self._db_path(app, state, session_id)
        report = cost_store.bucket_report(db_path)

        lines: List[str] = ["## Cost report", ""]
        lines.append(f"- Total: `{_format_cost(report.get('total_cost'))}`")
        lines.append(f"- Requests: `{int(report.get('request_count') or 0):,}`")
        buckets = report.get("buckets")
        if isinstance(buckets, list) and buckets:
            lines.append("")
            lines.append("| Bucket | Total | Requests | Last reset |")
            lines.append("| --- | --- | --- | --- |")
            for entry in buckets:
                if not isinstance(entry, dict):
                    continue
                reset_at = entry.get("last_reset_at") or "never"
                lines.append(
                    f"| `{entry.get('bucket', '')}` "
                    f"| `{_format_cost(entry.get('total_cost'))}` "
                    f"| `{int(entry.get('request_count') or 0):,}` "
                    f"| {reset_at} |"
                )
        else:
            lines.append("")
            lines.append("No cost records yet.")
        lines.append("")
        lines.append(
            "Totals cover the requests recorded after each bucket's last "
            "reset; recorded history is preserved."
        )

        return {
            "display": {
                "format": "markdown",
                "title": "Cost report",
                "body": "\n".join(lines),
                "variant": "info",
                "presentation": "modal",
                "dismissible": True,
                "display_id": "cost-tracking-report",
            },
            "report": report,
        }

    def _reset_cost_tracking(
        self, app: Any, state: Dict[str, Any], params: Dict[str, Any]
    ) -> Dict[str, Any]:
        session_id = self._required_session_id(params)
        bucket = params.get("bucket")
        if not (isinstance(bucket, str) and bucket.strip()):
            raise ValueError("[cost_tracking] bucket is required to reset tracking")
        bucket = bucket.strip()

        db_path = self._db_path(app, state, session_id)
        marker = cost_store.reset_bucket(db_path, bucket=bucket)
        try:
            summary_config: Dict[str, Any] = dict(self._plugin_config(state))
            summary_config.update(self._session_config(app, session_id))
            cost_store.append_reset_summary_csv(
                db_path,
                summary_config,
                bucket=bucket,
                time=(
                    marker.get("reset_at")
                    if isinstance(marker.get("reset_at"), str)
                    else None
                ),
            )
        except Exception:
            # Best-effort: the summary CSV must never break the reset action.
            pass
        report = cost_store.bucket_report(db_path)

        body = (
            f"Appended a reset marker for bucket `{bucket}` at "
            f"`{marker.get('reset_at')}`. Report totals for this bucket now "
            "start from that time; recorded history is preserved."
        )
        return {
            "display": {
                "format": "markdown",
                "title": "Cost tracking reset",
                "body": body,
                "variant": "success",
                "presentation": "modal",
                "dismissible": True,
                "display_id": "cost-tracking-reset",
            },
            "reset": marker,
            "report": report,
        }

    @staticmethod
    def _required_session_id(params: Dict[str, Any]) -> str:
        session_id = params.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id is required")
        return session_id


__all__ = ["CostTrackingAppPlugin"]
