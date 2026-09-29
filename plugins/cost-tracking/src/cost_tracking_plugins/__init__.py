"""Generic cost tracking plugin.

Records per-request cost rows for providers that emit the ``cost_tracking``
capability tag into a SQLite store, feeds the chat status bar a store-backed
session total aggregated by workspace + session id, and exposes report and
per-bucket reset actions.
"""

from .cost_store import (
    DEFAULT_COST_DB_RELATIVE_PATH,
    bucket_report,
    known_buckets,
    record_request_usage,
    resolve_cost_db_path,
    reset_bucket,
    session_totals,
)
from .cost_tracking_app_plugin import CostTrackingAppPlugin
from .cost_tracking_extension import CostTrackingExtension

__all__ = [
    "DEFAULT_COST_DB_RELATIVE_PATH",
    "CostTrackingAppPlugin",
    "CostTrackingExtension",
    "bucket_report",
    "known_buckets",
    "record_request_usage",
    "resolve_cost_db_path",
    "reset_bucket",
    "session_totals",
]
