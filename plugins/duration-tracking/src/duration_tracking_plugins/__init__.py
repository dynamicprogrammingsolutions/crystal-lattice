"""Duration tracking plugin.

Records per-request duration rows into a SQLite store, feeds the chat
status bar store-backed session totals aggregated by workspace + session
id, and exposes a report action. Measurement stays in the timestamp
extension's duration feature; this package records from its stamps.
"""

from .duration_store import (
    DEFAULT_DURATION_DB_RELATIVE_PATH,
    overall_totals,
    record_request_duration,
    resolve_duration_db_path,
    session_totals,
    top_projects,
    top_sessions,
    utcnow_iso,
)
from .duration_tracking_app_plugin import DurationTrackingAppPlugin
from .duration_tracking_extension import DurationTrackingExtension

__all__ = [
    "DEFAULT_DURATION_DB_RELATIVE_PATH",
    "DurationTrackingAppPlugin",
    "DurationTrackingExtension",
    "overall_totals",
    "record_request_duration",
    "resolve_duration_db_path",
    "session_totals",
    "top_projects",
    "top_sessions",
    "utcnow_iso",
]
