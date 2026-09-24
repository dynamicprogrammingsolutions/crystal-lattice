"""Package-adapter tests: frozen identity, both schemas, per-sample rows.

The dataset registry is gone: ``collect`` reads the dataset identity from
the frozen dataset file. The adapter renders the historical batched
assessment schema and the per-subject schema side by side, and judgments
render per-sample rows — one row per subject sample, carrying the sample
index — wherever a cell produced more than one sample.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..result_package import (
    _assessment_details,
    _matrix_detail_sections,
    main,
)
from .test_result_package import (
    SYNTHETIC_CELLS,
    SYNTHETIC_RUN_LABEL,
    _build_synthetic_evaluation,
    _handoff_judgment,
    _task_creation_judgment,
    HANDOFF_SCENARIO_ID,
)


# --- Both assessment schemas render ---------------------------------------


def _batched_semantic_record() -> dict:
    judgment = _task_creation_judgment(HANDOFF_SCENARIO_ID, score=95)
    return {
        "schema_version": 1,
        "scenario_id": HANDOFF_SCENARIO_ID,
        "producer_attempt": "b0-v5-r1",
        "semantic_attempt": "b0-metrics1",
        "assessment": {
            "schema_version": 2,
            "scenario_id": HANDOFF_SCENARIO_ID,
            "assessments": [judgment],
        },
        "summary": {"assessment_count": 1},
    }


def _per_subject_semantic_record(*, sample_index: int = 0) -> dict:
    return {
        "schema_version": 2,
        "scenario_id": HANDOFF_SCENARIO_ID,
        "subject": {
            "profile": "gpt",
            "reasoning_effort": "high",
            "sample_index": sample_index,
        },
        "assessment": _task_creation_judgment(HANDOFF_SCENARIO_ID, score=95),
        "summary": {"partition_quality_score": 95},
    }


def _batched_handoff_record() -> dict:
    judgment = _handoff_judgment(
        HANDOFF_SCENARIO_ID, variant="retain", stage="fresh-agent", score=95
    )
    return {
        "schema_version": 1,
        "scenario_id": HANDOFF_SCENARIO_ID,
        "producer_attempt": "b0-v5-r1",
        "handoff_attempt": "b0-v5-r1",
        "semantic_attempt": "b0-metrics1",
        "fresh_records": [],
        "same_agent_records": [],
        "assessment": {
            "schema_version": 1,
            "scenario_id": HANDOFF_SCENARIO_ID,
            "assessments": [judgment],
        },
    }


def _per_subject_handoff_judgment() -> dict:
    return {
        "stage": "fresh-agent",
        "variant": "retain",
        "plan_coverage": "complete",
        "missing_outcomes": [],
        "lost_facts_or_decisions": [],
        "invented_scope_or_decisions": [],
        "testing_boundary": "decisive",
        "documentation_boundary": "appropriate",
        "task_self_contained": True,
        "broad_rediscovery": False,
        "handoff_quality_score": 95,
        "efficiency_interpretation": "Read the task and reused it.",
        "summary": "Complete.",
    }


def _per_subject_handoff_record(*, sample_index: int = 1) -> dict:
    judgment = _per_subject_handoff_judgment()
    return {
        "schema_version": 2,
        "scenario_id": HANDOFF_SCENARIO_ID,
        "subject": {
            "profile": "glm",
            "reasoning_effort": "max",
            "sample_index": sample_index,
        },
        "assessment": judgment,
    }


def test_assessment_details_render_both_schemas() -> None:
    frozen = {
        "semantic_records": [
            _batched_semantic_record(),
            _per_subject_semantic_record(),
        ],
        "handoff_semantic_records": [
            _batched_handoff_record(),
            _per_subject_handoff_record(),
        ],
    }

    rows = _assessment_details(frozen)

    task_rows = [row for row in rows if row["kind"] == "task-creation"]
    assert [(row["profile"], row["reasoning_effort"]) for row in task_rows] == [
        ("glm", "max"),
        ("gpt", "high"),
    ]
    assert task_rows[0]["sample_index"] is None
    assert task_rows[1]["sample_index"] == 0
    handoff_rows = [row for row in rows if row["kind"] == "handoff"]
    assert len(handoff_rows) == 2
    assert handoff_rows[0]["sample_index"] is None
    assert handoff_rows[1]["sample_index"] == 1
    assert handoff_rows[1]["variant"] == "retain"


def test_matrix_details_render_per_sample_rows() -> None:
    frozen = {
        "semantic_records": [
            _per_subject_semantic_record(sample_index=0),
            _per_subject_semantic_record(sample_index=1),
        ],
        "handoff_semantic_records": [],
    }
    aggregate = {"assessment_details": _assessment_details(frozen)}

    markdown = "\n".join(_matrix_detail_sections(aggregate))

    assert "Sample" in markdown
    assert "s0" in markdown
    assert "s1" in markdown


# --- Collect reads the dataset identity from the frozen file --------------


def test_collect_reads_identity_from_the_frozen_dataset(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    pieces = _build_synthetic_evaluation(root)
    frozen = dict(pieces["frozen"])
    frozen["labels"] = [SYNTHETIC_RUN_LABEL]
    frozen.pop("attempts")
    frozen["bundle"] = {
        "path": str(pieces["bundle"]),
        "compilation_sha256": "0" * 64,
    }
    frozen_path = tmp_path / "frozen.json"
    frozen_path.write_text(json.dumps(frozen), encoding="utf-8")
    package = tmp_path / "packages" / "synthetic-frozen-package"

    code = main(
        [
            "collect",
            "--frozen",
            str(frozen_path),
            "--output",
            str(package),
            "--artifact-root",
            str(pieces["artifact_root"]),
            "--cells",
            *SYNTHETIC_CELLS,
            "--no-reconstruction",
        ]
    )

    assert code == 0
    manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
    identity = manifest["identity"]
    assert identity["dataset_id"] == frozen["dataset_id"]
    assert identity["label"] == frozen["label"]
    assert identity["name"] == package.name
    assert identity["labels"] == [SYNTHETIC_RUN_LABEL]
    assert "attempts" not in identity
