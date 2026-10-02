from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "sync_tasks_v7.py"
SPEC = importlib.util.spec_from_file_location("sync_tasks_v7", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
sync_tasks_v7 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync_tasks_v7)


def test_bundled_tasks_v7_matches_canonical() -> None:
    assert sync_tasks_v7.BUNDLED.read_bytes() == sync_tasks_v7.CANONICAL.read_bytes()


def test_tasks_v7_sync_updates_and_checks_drift(tmp_path: Path) -> None:
    canonical = tmp_path / "TASKS-v7.md"
    bundled = tmp_path / "TASKS_v7.md"
    canonical.write_text("canonical\n", encoding="utf-8")
    bundled.write_text("stale\n", encoding="utf-8")

    with pytest.raises(ValueError, match="differs from canonical task guidance"):
        sync_tasks_v7.synchronize(canonical, bundled, check=True)

    assert sync_tasks_v7.synchronize(canonical, bundled)
    assert bundled.read_text(encoding="utf-8") == "canonical\n"
    assert not sync_tasks_v7.synchronize(canonical, bundled)
    assert not sync_tasks_v7.synchronize(canonical, bundled, check=True)