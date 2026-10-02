"""Run labels: pure provenance, one per live invocation."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4


def generate_run_label() -> str:
    """Return a fresh auto label for one live invocation.

    Labels are provenance only: they identify batches of runs in
    consolidation and never take part in any cache identity.
    """

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"r-{stamp}-{uuid4().hex[:4]}"
