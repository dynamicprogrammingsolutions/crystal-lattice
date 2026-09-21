from __future__ import annotations

import os
from pathlib import Path


def record_paths(artifact_root: Path, record_name: str) -> tuple[Path, ...]:
    """Return record files without traversing transient run workspaces."""
    values: set[Path] = set()
    for pattern in (
        f"*/runs/*/records/{record_name}",
        f"runs/*/records/{record_name}",
        f"*/records/{record_name}",
        f"records/{record_name}",
    ):
        values.update(artifact_root.glob(pattern))
    return tuple(sorted(values))


def selected_dataset_id() -> str:
    return os.getenv(
        "AGENT_EVAL_TASK_DATASET_ID",
        "task-guidance-b0-20260919",
    ).strip()