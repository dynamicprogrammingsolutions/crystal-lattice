"""Timestamp extension plugin package.

This repository ships feature plugins that attach timing-related metadata to
messages for display in UIs (e.g. message footers).
"""

from .duration_extension import DurationExtension
from .timestamp_extension import TimestampExtension

__all__ = [
    "DurationExtension",
    "TimestampExtension",
]
