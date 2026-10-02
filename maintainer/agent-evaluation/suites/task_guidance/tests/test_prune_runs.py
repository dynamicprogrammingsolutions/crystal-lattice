"""Prune-runs retention: the selection semantics decide what stays."""

from __future__ import annotations

import json
import os
from pathlib import Path

from ..prune_runs import main, plan


PRODUCER_RECORD = "task-guidance-producer.json"
SEMANTIC_RECORD = "task-guidance-semantic.json"


def _write_run(
    root: Path,
    run_id: str,
    record_name: str,
    record: dict[str, object],
    *,
    label: str | None,
    cache_hit: bool = False,
    profile: str = "glm",
) -> Path:
    run_dir = root / profile / "runs" / run_id
    (run_dir / "records").mkdir(parents=True)
    (run_dir / "raw").mkdir()
    (run_dir / "raw" / "session.bin").write_bytes(b"x" * 1024)
    (run_dir / "records" / record_name).write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if label is not None:
        (run_dir / "records" / "run-model.json").write_text(
            json.dumps(
                {
                    "schema": 1,
                    "label": label,
                    "identity": f"identity-{run_id}",
                    "cache_hit": cache_hit,
                    "sample_index": 0,
                    "run_id": run_id,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
    return run_dir


def _producer_record(
    scenario: str = "tg01-eleventy-archive-handoff",
    profile: str = "glm",
    effort: str = "max",
) -> dict[str, object]:
    return {
        "scenario_id": scenario,
        "producer": {"profile": profile, "reasoning_effort": effort},
        "valid": True,
    }


def _assessment_record(
    scenario: str = "tg01-eleventy-archive-handoff",
) -> dict[str, object]:
    return {
        "scenario_id": scenario,
        "subject": {"profile": "glm", "reasoning_effort": "max", "sample_index": 0},
    }


def _plan(root: Path, keep: str) -> tuple[list[tuple[Path, str]], list[Path]]:
    drops, keeps, _ = plan(root, keep_labels=keep.split(","))
    return drops, keeps


def test_kept_label_runs_are_retained_and_others_dropped(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    kept = _write_run(
        root, "run-kept", PRODUCER_RECORD, _producer_record(), label="keep-1"
    )
    dropped = _write_run(
        root, "run-old", PRODUCER_RECORD, _producer_record(), label=None
    )
    record_path = dropped / "records" / PRODUCER_RECORD
    value = json.loads(record_path.read_text(encoding="utf-8"))
    value["run_attempt"] = "old-1"
    record_path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")

    drops, keeps = _plan(root, "keep-1")

    assert [path for path, _ in drops] == [dropped]
    assert "old-1" in drops[0][1]
    assert keeps == [kept]
    assert dropped.exists() and kept.exists()  # dry run deletes nothing


def test_superseded_legacy_record_is_dropped(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    older = _write_run(
        root, "run-older", PRODUCER_RECORD, _producer_record(), label=None
    )
    newer = _write_run(
        root, "run-newer", PRODUCER_RECORD, _producer_record(), label=None
    )
    for run_dir, stamp in ((older, 1_000_000), (newer, 2_000_000)):
        record_path = run_dir / "records" / PRODUCER_RECORD
        value = json.loads(record_path.read_text(encoding="utf-8"))
        value["run_attempt"] = "keep-1"
        record_path.write_text(json.dumps(value, sort_keys=True) + "\n")
        os.utime(record_path, (stamp, stamp))

    drops, keeps = _plan(root, "keep-1")

    assert [path for path, _ in drops] == [older]
    assert "superseded" in drops[0][1]
    assert keeps == [newer]


def test_managed_replays_drop_only_when_genuine_samples_exist(
    tmp_path: Path,
) -> None:
    root = tmp_path / "artifacts"
    genuine = _write_run(
        root, "run-genuine", PRODUCER_RECORD, _producer_record(), label="keep-1"
    )
    replay = _write_run(
        root,
        "run-replay",
        PRODUCER_RECORD,
        _producer_record(),
        label="keep-1",
        cache_hit=True,
    )
    only_replay = _write_run(
        root,
        "run-only-replay",
        SEMANTIC_RECORD,
        _assessment_record(),
        label="keep-1",
        cache_hit=True,
    )

    drops, keeps = _plan(root, "keep-1")

    assert [path for path, _ in drops] == [replay]
    assert "cache replay" in drops[0][1]
    assert keeps == [genuine, only_replay]


def test_every_genuine_sample_of_a_cell_is_kept(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    first = _write_run(
        root, "run-s0", PRODUCER_RECORD, _producer_record(), label="keep-1"
    )
    second = _write_run(
        root, "run-s1", PRODUCER_RECORD, _producer_record(), label="keep-1"
    )

    drops, keeps = _plan(root, "keep-1")

    assert drops == []
    assert keeps == [first, second]


def test_unclassified_run_dirs_are_kept_and_reported(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    _write_run(root, "run-kept", PRODUCER_RECORD, _producer_record(), label="keep-1")
    bare = root / "glm" / "runs" / "run-in-flight"
    (bare / "records").mkdir(parents=True)

    drops, keeps, bare_dirs = plan(root, keep_labels=["keep-1"])

    assert drops == []
    assert bare_dirs == [bare]
    assert len(keeps) == 1


def test_execute_removes_drops_and_optionally_the_cache(
    tmp_path: Path, capsys: object
) -> None:
    root = tmp_path / "artifacts"
    kept = _write_run(
        root, "run-kept", PRODUCER_RECORD, _producer_record(), label="keep-1"
    )
    dropped = _write_run(
        root, "run-old", PRODUCER_RECORD, _producer_record(), label=None
    )
    record_path = dropped / "records" / PRODUCER_RECORD
    value = json.loads(record_path.read_text(encoding="utf-8"))
    value["run_attempt"] = "old-1"
    record_path.write_text(json.dumps(value, sort_keys=True) + "\n")
    cache = root / "cache" / "glm" / "entries"
    cache.mkdir(parents=True)
    (cache / "entry.json").write_text("{}", encoding="utf-8")

    assert main(["--artifact-root", str(root), "--keep-labels", "keep-1"]) == 0
    assert dropped.exists() and cache.exists()  # dry run

    assert (
        main(
            [
                "--artifact-root",
                str(root),
                "--keep-labels",
                "keep-1",
                "--cache",
                "--execute",
            ]
        )
        == 0
    )
    assert not dropped.exists()
    assert kept.exists()
    assert not cache.exists()
    output = capsys.readouterr().out
    assert "removed 1 run directory(ies)" in output
