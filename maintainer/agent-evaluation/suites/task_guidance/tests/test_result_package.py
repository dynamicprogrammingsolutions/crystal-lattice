"""Synthetic coverage for task-guidance result-package generation.

The completed b0/b1 evaluation datasets no longer serve as suite fixtures.
These tests build a small synthetic evaluation — one handoff scenario and one
decomposition scenario, one producer cell, every stage kind — and exercise
the real collection, projection, rendering, and checking path end to end
without any model request.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from agent_eval.result_packages import (
    check_result_package,
    render_result_package,
)

from ..configuration import DEFAULT_BUNDLE
from ..fixtures import FIXTURE_VERSION, fixture_sha256
from ..result_package import (
    QUALITY_DIMENSIONS,
    _build_case_views,
    _build_index_views,
    collect,
)
from ..scenarios import SCENARIOS
from ..topology import task_tree

SYNTHETIC_DATASET_ID = "task-guidance-synthetic"
SYNTHETIC_LABEL = "synthetic package fixture"
SYNTHETIC_ATTEMPTS = {
    "producer": "syn-r1",
    "handoff": "syn-r1",
    "semantic": "syn-m1",
}
HANDOFF_SCENARIO_ID = "tg02-fastapi-pagination-handoff"
DECOMPOSITION_SCENARIO_ID = "tg04-flask-vue-discovery-decomposition"
SYNTHETIC_CELLS = (
    f"{HANDOFF_SCENARIO_ID}:glm:max",
    f"{DECOMPOSITION_SCENARIO_ID}:glm:max",
)
PRODUCER_RUN_ID = "synthetic-tg02-producer"
CONTINUATION_RUN_ID = "synthetic-tg02-continuation"


def _scenario(scenario_id: str):
    for scenario in SCENARIOS:
        if scenario.scenario_id == scenario_id:
            return scenario
    raise KeyError(scenario_id)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _session(
    workspace: str,
    *,
    prompt: str,
    response: str,
    compiled: str | None,
    run_id: str,
) -> dict[str, Any]:
    messages: list[dict[str, Any]] = []
    if compiled is not None:
        messages.append(
            {
                "role": "system",
                "content": "compiled",
                "metadata": {
                    "compiled_content": (
                        "You are the agent working in" f" {workspace}.\n\n{compiled}"
                    )
                },
            }
        )
    messages.append({"role": "user", "content": prompt, "metadata": {}})
    messages.append(
        {
            "role": "assistant",
            "content": "I will inspect the workspace first.",
            "metadata": {
                "tool_calls": [
                    {
                        "function": {
                            "name": "Bash",
                            "arguments": json.dumps({"command": f"ls {workspace}"}),
                        }
                    }
                ]
            },
        }
    )
    messages.append(
        {"role": "tool", "content": "tasks/\n", "metadata": {"tool_name": "Bash"}}
    )
    messages.append({"role": "assistant", "content": response, "metadata": {}})
    return {"session_id": f"session-{run_id}", "messages": messages, "metadata": {}}


SYNTHETIC_RUN_LABEL = "syn-r1"


def _write_run(
    root: Path,
    *,
    run_id: str,
    record_name: str,
    record: dict[str, Any],
    session: dict[str, Any],
    parent_run_id: str | None = None,
    sample_index: int = 0,
) -> Path:
    run_dir = root / "glm" / "runs" / run_id
    (run_dir / "records").mkdir(parents=True)
    (run_dir / "raw" / "environment").mkdir(parents=True)
    workspace = f"/tmp/synthetic-task-guidance/{run_id}/workspace"
    result = {
        "run_id": run_id,
        "workspace": workspace,
        "parent_run_id": parent_run_id,
        "status": "completed",
        "error": None,
    }
    (run_dir / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (run_dir / "records" / record_name).write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (run_dir / "records" / "run-model.json").write_text(
        json.dumps(
            {
                "schema": 1,
                "label": SYNTHETIC_RUN_LABEL,
                "identity": f"identity-{run_id}",
                "cache_hit": False,
                "sample_index": sample_index,
                "run_id": run_id,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (run_dir / "raw" / "environment" / "crystal-lattice-session.json").write_text(
        json.dumps(session, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (run_dir / "raw" / "environment" / "crystal-lattice-observation.json").write_text(
        json.dumps(
            {
                "request_count": 1,
                "tool_event_count": 2,
                "mutation_count": 1,
                "error_count": 0,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return run_dir


def _delivery(compiled: str) -> dict[str, Any]:
    return {
        "agents_occurrences": 1,
        "tasks_occurrences": 1,
        "tool_family_matches": True,
        "suite_wrapper_absent": True,
        "compiled_sha256": _sha(compiled),
        "active_tools": ["claude_bash_tool", "claude_read_tool"],
    }


def _tool_metrics() -> dict[str, int]:
    return {
        "list": 0,
        "mutation": 1,
        "other": 0,
        "read": 2,
        "search": 1,
        "shell": 1,
        "total": 5,
    }


def _producer_record(
    scenario_id: str, *, response: str, task_file: str
) -> dict[str, Any]:
    scenario = _scenario(scenario_id)
    task_files = {f"tasks/synthetic-{scenario_id}.md": task_file}
    return {
        "schema_version": 1,
        "dataset_id": SYNTHETIC_DATASET_ID,
        "scenario_id": scenario_id,
        "category": scenario.category,
        "project": scenario.target["project"],
        "fixture": {
            "version": FIXTURE_VERSION,
            "sha256": fixture_sha256(scenario.fixture_id),
        },
        "target_sha256": _sha(scenario.target_path.read_text(encoding="utf-8")),
        "target": scenario.target,
        "prompt": scenario.prompt,
        "producer": {
            "profile": "glm",
            "model": "glm-5.3-flash:cloud",
            "reasoning_effort": "max",
        },
        "run_attempt": SYNTHETIC_ATTEMPTS["producer"],
        "changed_paths": sorted(task_files),
        "task_files": task_files,
        "task_tree": task_tree(task_files),
        "tool_metrics": _tool_metrics(),
        "delivery": _delivery("synthetic compiled guidance"),
        "response": response,
        "valid": True,
        "invalid_reasons": [],
    }


def _handoff_record(scenario_id: str, *, variant: str, response: str) -> dict[str, Any]:
    scenario = _scenario(scenario_id)
    task_files = {
        f"tasks/synthetic-{scenario_id}-{variant}.md": (
            f"# Synthetic {variant} handoff\n\nPreserves the approved plan.\n"
        )
    }
    return {
        "schema_version": 1,
        "dataset_id": SYNTHETIC_DATASET_ID,
        "scenario_id": scenario_id,
        "variant": variant,
        "target": scenario.target,
        "target_sha256": _sha(scenario.target_path.read_text(encoding="utf-8")),
        "producer": {
            "profile": "glm",
            "model": "glm-5.3-flash:cloud",
            "reasoning_effort": "max",
        },
        "run_attempt": SYNTHETIC_ATTEMPTS["handoff"],
        "task_files": task_files,
        "tool_metrics": _tool_metrics(),
        "delivery": _delivery("synthetic compiled guidance"),
        "response": response,
        "valid": True,
        "invalid_reasons": [],
    }


def _continuation_record(scenario_id: str, *, response: str) -> dict[str, Any]:
    scenario = _scenario(scenario_id)
    return {
        "schema_version": 1,
        "dataset_id": SYNTHETIC_DATASET_ID,
        "scenario_id": scenario_id,
        "target": scenario.target,
        "producer": {
            "profile": "glm",
            "model": "glm-5.3-flash:cloud",
            "reasoning_effort": "max",
        },
        "run_attempt": SYNTHETIC_ATTEMPTS["producer"],
        "task_files": {
            f"tasks/synthetic-{scenario_id}.md": (
                "# Synthetic continuation task\n\nContinues the plan.\n"
            )
        },
        "task_creation_tool_metrics": _tool_metrics(),
        "continuation_tool_metrics": _tool_metrics(),
        "response": response,
        "valid": True,
        "invalid_reasons": [],
    }


def _control_record(scenario_id: str, *, response: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "dataset_id": SYNTHETIC_DATASET_ID,
        "scenario_id": scenario_id,
        "variant": "incomplete",
        "producer": {
            "profile": "glm",
            "model": "glm-5.3-flash:cloud",
            "reasoning_effort": "max",
        },
        "run_attempt": SYNTHETIC_ATTEMPTS["handoff"],
        "task_files": {
            f"tasks/synthetic-{scenario_id}-incomplete.md": (
                "# Incomplete handoff\n\nAdd pagination somehow.\n"
            )
        },
        "tool_metrics": _tool_metrics(),
        "response": response,
        "valid": True,
        "invalid_reasons": [],
    }


def _task_creation_judgment(scenario_id: str, *, score: int) -> dict[str, Any]:
    return {
        "producer": {"profile": "glm", "reasoning_effort": "max"},
        "outcome_coverage": "complete",
        "missing_outcomes": [],
        "added_obligations": [],
        "semantic_deliverable_count": 1,
        "actual_task_count": 1,
        "deliverable_mappings": [
            {
                "deliverable_id": "synthetic-deliverable",
                "task_paths": [f"tasks/synthetic-{scenario_id}.md"],
                "coverage": "complete",
                "coherence": "coherent",
                "reason": "one task covers the single deliverable",
            }
        ],
        "mergeable_groups": [],
        "unmatched_tasks": [],
        "overpacked_tasks": [],
        "valid_layer_boundaries": [],
        "automatic_layer_fragments": [],
        "dependency_issues": [],
        "crossing_ownership": "complete",
        "fragmentation_severity": "none",
        "fragmentation_ratio": 1.0,
        "quality_metrics": {
            dimension: {"status": "none", "score": score, "occurrences": []}
            for dimension in QUALITY_DIMENSIONS
        },
        "partition_quality_score": score,
        "handoff_quality_score": score,
        "overall_success_percentage": float(score),
        "summary": "synthetic judgment",
    }


def _handoff_judgment(
    scenario_id: str,
    *,
    variant: str,
    stage: str,
    score: int,
) -> dict[str, Any]:
    return {
        "stage": stage,
        "variant": variant,
        "producer": {"profile": "glm", "reasoning_effort": "max"},
        "plan_coverage": "complete",
        "missing_outcomes": [],
        "lost_facts_or_decisions": [],
        "invented_scope_or_decisions": [],
        "testing_boundary": "decisive",
        "documentation_boundary": "appropriate",
        "task_self_contained": True,
        "broad_rediscovery": False,
        "handoff_quality_score": score,
        "efficiency_interpretation": "synthetic interpretation",
        "summary": f"synthetic {variant} judgment",
    }


def _semantic_record(
    scenario_id: str, *, judgment: dict[str, Any], producer_record: dict[str, Any]
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "dataset_id": SYNTHETIC_DATASET_ID,
        "scenario_id": scenario_id,
        "producer_attempt": SYNTHETIC_ATTEMPTS["producer"],
        "semantic_attempt": SYNTHETIC_ATTEMPTS["semantic"],
        "producer_records": [producer_record],
        "invalid_producer_records": [],
        "assessment": {
            "schema_version": 2,
            "scenario_id": scenario_id,
            "assessments": [judgment],
        },
        "summary": {
            "assessment_count": 1,
            "average_partition_quality": float(judgment["partition_quality_score"]),
        },
    }


def _handoff_semantic_record(
    scenario_id: str,
    *,
    judgments: list[dict[str, Any]],
    fresh_records: list[dict[str, Any]],
    same_agent_record: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "dataset_id": SYNTHETIC_DATASET_ID,
        "scenario_id": scenario_id,
        "producer_attempt": SYNTHETIC_ATTEMPTS["producer"],
        "handoff_attempt": SYNTHETIC_ATTEMPTS["handoff"],
        "semantic_attempt": SYNTHETIC_ATTEMPTS["semantic"],
        "fresh_records": fresh_records,
        "same_agent_records": [same_agent_record],
        "assessment": {
            "schema_version": 1,
            "scenario_id": scenario_id,
            "assessments": judgments,
        },
    }


def _semantic_quality(records: list[dict[str, Any]]) -> dict[str, Any]:
    judgments = [
        judgment
        for record in records
        for judgment in record["assessment"]["assessments"]
    ]
    dimensions = {
        dimension: {
            "affected_assessments": 0,
            "average_score": 100.0,
            "occurrence_count": 0,
            "status_counts": {"none": len(judgments)},
        }
        for dimension in QUALITY_DIMENSIONS
    }
    cohort = {
        "assessment_count": len(judgments),
        "overall_success_percentage": 100.0,
        "dimensions": dimensions,
    }
    return {"cohorts": {"all": cohort, "glm:max": cohort}}


def _synthetic_frozen(
    *,
    producer_records: list[dict[str, Any]],
    handoff_records: list[dict[str, Any]],
    continuation_record: dict[str, Any],
    control_record: dict[str, Any],
    semantic_records: list[dict[str, Any]],
    handoff_semantic_record: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "dataset_id": SYNTHETIC_DATASET_ID,
        "label": SYNTHETIC_LABEL,
        "attempts": dict(SYNTHETIC_ATTEMPTS),
        "status": {
            "producers": {
                "expected": len(producer_records),
                "present": len(producer_records),
                "valid": len(producer_records),
                "invalid": 0,
                "missing": [],
            },
            "handoffs": {
                "expected": len(handoff_records),
                "present": len(handoff_records),
                "valid": len(handoff_records),
                "invalid": 0,
                "missing": [],
            },
            "same_agent": {
                "expected": 1,
                "present": 1,
                "valid": 1,
                "invalid": 0,
                "missing": [],
            },
            "semantics": {
                "expected": len(semantic_records),
                "present": len(semantic_records),
                "missing": [],
            },
            "handoff_semantics": {"expected": 1, "present": 1, "missing": []},
            "negative_controls": {"expected": 1, "present": 1, "missing": []},
            "provider_blockers": {"identities": [], "present": 0},
        },
        "semantic_quality": _semantic_quality(semantic_records),
        "producer_records": producer_records,
        "handoff_records": handoff_records,
        "same_agent_records": [continuation_record],
        "negative_control_records": [control_record],
        "semantic_records": semantic_records,
        "handoff_semantic_records": [handoff_semantic_record],
        "provider_blocker_records": [],
    }


def _build_synthetic_evaluation(root: Path) -> dict[str, Path]:
    """Write one synthetic handoff cell and one decomposition cell."""

    handoff_producer = _producer_record(
        HANDOFF_SCENARIO_ID,
        response="Created the pagination task.",
        task_file="# Synthetic notes pagination\n\nOne deliverable.\n",
    )
    decomposition_producer = _producer_record(
        DECOMPOSITION_SCENARIO_ID,
        response="Created the discovery decomposition task.",
        task_file="# Synthetic book discovery\n\nOne deliverable.\n",
    )
    retain = _handoff_record(
        HANDOFF_SCENARIO_ID,
        variant="retain",
        response="Planned from the retained plan.",
    )
    omit = _handoff_record(
        HANDOFF_SCENARIO_ID,
        variant="omit",
        response="Replanned from the omit handoff.",
    )
    continuation = _continuation_record(
        HANDOFF_SCENARIO_ID,
        response="Continued planning from the generated task.",
    )
    control = _control_record(
        HANDOFF_SCENARIO_ID,
        response="Planned from the incomplete handoff.",
    )
    handoff_semantic = _handoff_semantic_record(
        HANDOFF_SCENARIO_ID,
        judgments=[
            _handoff_judgment(
                HANDOFF_SCENARIO_ID, variant="retain", stage="fresh-agent", score=90
            ),
            _handoff_judgment(
                HANDOFF_SCENARIO_ID, variant="omit", stage="fresh-agent", score=80
            ),
            _handoff_judgment(
                HANDOFF_SCENARIO_ID, variant="incomplete", stage="fresh-agent", score=40
            ),
            _handoff_judgment(
                HANDOFF_SCENARIO_ID,
                variant="generated-task",
                stage="same-agent",
                score=85,
            ),
        ],
        fresh_records=[retain, omit, control],
        same_agent_record=continuation,
    )
    handoff_semantic_record = handoff_semantic
    semantic_records = [
        _semantic_record(
            HANDOFF_SCENARIO_ID,
            judgment=_task_creation_judgment(HANDOFF_SCENARIO_ID, score=100),
            producer_record=handoff_producer,
        ),
        _semantic_record(
            DECOMPOSITION_SCENARIO_ID,
            judgment=_task_creation_judgment(DECOMPOSITION_SCENARIO_ID, score=100),
            producer_record=decomposition_producer,
        ),
    ]
    frozen = _synthetic_frozen(
        producer_records=[handoff_producer, decomposition_producer],
        handoff_records=[retain, omit],
        continuation_record=continuation,
        control_record=control,
        semantic_records=semantic_records,
        handoff_semantic_record=handoff_semantic_record,
    )

    artifact_root = root / "artifact"
    artifact_root.mkdir(parents=True, exist_ok=True)
    _write_run(
        artifact_root,
        run_id=PRODUCER_RUN_ID,
        record_name="task-guidance-producer.json",
        record=handoff_producer,
        session=_session(
            f"/tmp/synthetic-task-guidance/{PRODUCER_RUN_ID}/workspace",
            prompt=handoff_producer["prompt"],
            response=handoff_producer["response"],
            compiled="synthetic compiled guidance",
            run_id=PRODUCER_RUN_ID,
        ),
    )
    _write_run(
        artifact_root,
        run_id="synthetic-tg02-retain",
        record_name="task-guidance-handoff-plan.json",
        record=retain,
        session=_session(
            "/tmp/synthetic-task-guidance/synthetic-tg02-retain/workspace",
            prompt="Plan from the retained handoff.",
            response=retain["response"],
            compiled="synthetic compiled guidance",
            run_id="synthetic-tg02-retain",
        ),
    )
    _write_run(
        artifact_root,
        run_id="synthetic-tg02-omit",
        record_name="task-guidance-handoff-plan.json",
        record=omit,
        session=_session(
            "/tmp/synthetic-task-guidance/synthetic-tg02-omit/workspace",
            prompt="Plan from the omit handoff.",
            response=omit["response"],
            compiled="synthetic compiled guidance",
            run_id="synthetic-tg02-omit",
        ),
    )
    # The continuation session retains no system message, so its delivered
    # instructions must be inherited from the producer run.
    _write_run(
        artifact_root,
        run_id=CONTINUATION_RUN_ID,
        record_name="task-guidance-same-agent-plan.json",
        record=continuation,
        session=_session(
            f"/tmp/synthetic-task-guidance/{CONTINUATION_RUN_ID}/workspace",
            prompt="Continue planning from the generated task.",
            response=continuation["response"],
            compiled=None,
            run_id=CONTINUATION_RUN_ID,
        ),
        parent_run_id=PRODUCER_RUN_ID,
    )
    _write_run(
        artifact_root,
        run_id="synthetic-tg02-control",
        record_name="task-guidance-negative-control.json",
        record=control,
        session=_session(
            "/tmp/synthetic-task-guidance/synthetic-tg02-control/workspace",
            prompt="Plan from the incomplete handoff.",
            response=control["response"],
            compiled="synthetic compiled guidance",
            run_id="synthetic-tg02-control",
        ),
    )
    _write_run(
        artifact_root,
        run_id="synthetic-tg02-semantic",
        record_name="task-guidance-semantic.json",
        record=semantic_records[0],
        session=_session(
            "/tmp/synthetic-task-guidance/synthetic-tg02-semantic/workspace",
            prompt="Assess the synthetic tg02 producers.",
            response=json.dumps(semantic_records[0]["assessment"], indent=2),
            compiled="synthetic assessor guidance",
            run_id="synthetic-tg02-semantic",
        ),
    )
    _write_run(
        artifact_root,
        run_id="synthetic-tg02-handoff-semantic",
        record_name="task-guidance-handoff-semantic.json",
        record=handoff_semantic_record,
        session=_session(
            "/tmp/synthetic-task-guidance/synthetic-tg02-handoff-semantic/workspace",
            prompt="Assess the synthetic tg02 handoffs.",
            response=json.dumps(handoff_semantic_record["assessment"], indent=2),
            compiled="synthetic assessor guidance",
            run_id="synthetic-tg02-handoff-semantic",
        ),
    )
    _write_run(
        artifact_root,
        run_id="synthetic-tg04-producer",
        record_name="task-guidance-producer.json",
        record=decomposition_producer,
        session=_session(
            "/tmp/synthetic-task-guidance/synthetic-tg04-producer/workspace",
            prompt=decomposition_producer["prompt"],
            response=decomposition_producer["response"],
            compiled="synthetic compiled guidance",
            run_id="synthetic-tg04-producer",
        ),
    )
    _write_run(
        artifact_root,
        run_id="synthetic-tg04-semantic",
        record_name="task-guidance-semantic.json",
        record=semantic_records[1],
        session=_session(
            "/tmp/synthetic-task-guidance/synthetic-tg04-semantic/workspace",
            prompt="Assess the synthetic tg04 producers.",
            response=json.dumps(semantic_records[1]["assessment"], indent=2),
            compiled="synthetic assessor guidance",
            run_id="synthetic-tg04-semantic",
        ),
    )

    frozen_path = root / "synthetic-frozen.json"
    frozen_path.write_text(
        json.dumps(frozen, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {
        "artifact_root": artifact_root,
        "frozen_path": frozen_path,
        "frozen": frozen,
        "producer_records": [handoff_producer, decomposition_producer],
        "handoff_records": [retain, omit],
        "continuation_record": continuation,
        "control_record": control,
        "semantic_records": semantic_records,
        "handoff_semantic_record": handoff_semantic_record,
        "bundle": DEFAULT_BUNDLE,
    }


def _collect_synthetic(root: Path, *, name: str = "package") -> Path:
    paths = _build_synthetic_evaluation(root)
    package_dir = root / name
    collect(
        package_dir=package_dir,
        artifact_root=paths["artifact_root"],
        frozen_path=paths["frozen_path"],
        cells=list(SYNTHETIC_CELLS),
        bundle=DEFAULT_BUNDLE,
    )
    return package_dir


def _collect_twice(root: Path) -> tuple[Path, Path]:
    """Collect the same synthetic evaluation into two package directories.

    Both directories share the leaf name: the package name is the output
    directory name, so differently named directories would legitimately
    produce different manifests.
    """

    paths = _build_synthetic_evaluation(root)
    packages = []
    for parent in ("first", "second"):
        package_dir = root / parent / "package"
        collect(
            package_dir=package_dir,
            artifact_root=paths["artifact_root"],
            frozen_path=paths["frozen_path"],
            cells=list(SYNTHETIC_CELLS),
            bundle=DEFAULT_BUNDLE,
        )
        packages.append(package_dir)
    return packages[0], packages[1]


def _per_subject_handoff_record(
    scenario_id: str,
    *,
    variant: str,
    stage: str,
    score: int,
) -> dict[str, Any]:
    """One per-subject handoff judgment: variant distinguishes the runs."""

    return {
        "schema_version": 2,
        "dataset_id": SYNTHETIC_DATASET_ID,
        "scenario_id": scenario_id,
        "subject": {"profile": "glm", "reasoning_effort": "max", "sample_index": 0},
        "assessment": {
            "variant": variant,
            "stage": stage,
            "handoff_quality_score": score,
            "plan_coverage": "complete",
            "documentation_boundary": "respected",
            "testing_boundary": "respected",
            "task_self_contained": True,
            "broad_rediscovery": False,
            "lost_facts_or_decisions": [],
            "invented_scope_or_decisions": [],
            "missing_outcomes": [],
        },
        "summary": f"Synthetic {variant} judgment.",
    }


def _per_subject_task_creation_record(
    scenario_id: str,
    *,
    profile: str,
    effort: str,
    score: int,
) -> dict[str, Any]:
    """One per-subject task-creation judgment for one producer cell."""

    judgment = _task_creation_judgment(scenario_id, score=score)
    judgment.pop("producer")
    return {
        "schema_version": 2,
        "dataset_id": SYNTHETIC_DATASET_ID,
        "scenario_id": scenario_id,
        "subject": {
            "profile": profile,
            "reasoning_effort": effort,
            "sample_index": 0,
        },
        "assessment": judgment,
        "summary": {"average_partition_quality": float(score)},
    }


def test_collect_renders_each_task_creation_subject_of_one_scenario(
    tmp_path: Path,
) -> None:
    """Per-subject task-creation judgments of one scenario collect per cell.

    One scenario's producer cells (for example glm-max and gpt-high) are
    distinct subjects with the same sample index; each judgment must
    render at its own location instead of colliding on ``s0``.
    """

    paths = _build_synthetic_evaluation(tmp_path)
    frozen = paths["frozen"]
    records = [
        _per_subject_task_creation_record(
            HANDOFF_SCENARIO_ID, profile="glm", effort="max", score=100
        ),
        _per_subject_task_creation_record(
            HANDOFF_SCENARIO_ID, profile="gpt", effort="high", score=90
        ),
    ]
    frozen["semantic_records"] = records
    frozen["status"]["semantics"] = {
        "expected": 2,
        "present": 2,
        "missing": [],
    }
    for record in records:
        subject = record["subject"]
        run_id = (
            f"synthetic-tg02-semantic-{subject['profile']}-"
            f"{subject['reasoning_effort']}"
        )
        _write_run(
            paths["artifact_root"],
            run_id=run_id,
            record_name="task-guidance-semantic.json",
            record=record,
            session=_session(
                f"/tmp/synthetic-task-guidance/{run_id}/workspace",
                prompt=(
                    "Assess the synthetic tg02 producer"
                    f" {subject['profile']} {subject['reasoning_effort']}."
                ),
                response=json.dumps(record["assessment"], indent=2),
                compiled="synthetic assessor guidance",
                run_id=run_id,
            ),
        )
    paths["frozen_path"].write_text(
        json.dumps(frozen, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    package_dir = tmp_path / "package"
    collect(
        package_dir=package_dir,
        artifact_root=paths["artifact_root"],
        frozen_path=paths["frozen_path"],
        cells=list(SYNTHETIC_CELLS),
        bundle=DEFAULT_BUNDLE,
    )
    for cell in ("glm-max", "gpt-high"):
        assessment_prefix = (
            f"scenarios/{HANDOFF_SCENARIO_ID}/{cell}/assessment/task-creation"
        )
        assert (package_dir / assessment_prefix / "s0" / "run.json").is_file()


def test_collect_renders_each_judgment_of_one_subject(
    tmp_path: Path,
) -> None:
    """Two judgments of one subject collect as numbered judgments.

    Repeated invocations under one label judge the same subject twice;
    the frozen records name their runs, and the collection numbers the
    judgments so every run renders at its own location instead of
    collapsing onto the newest matching run.
    """

    paths = _build_synthetic_evaluation(tmp_path)
    frozen = paths["frozen"]
    records = []
    for run_id, score in (
        ("synthetic-tg02-handoff-retain-1", 90),
        ("synthetic-tg02-handoff-retain-2", 70),
    ):
        record = _per_subject_handoff_record(
            HANDOFF_SCENARIO_ID, variant="retain", stage="fresh-agent", score=score
        )
        record["run_id"] = run_id
        records.append(record)
        _write_run(
            paths["artifact_root"],
            run_id=run_id,
            record_name="task-guidance-handoff-semantic.json",
            record=record,
            session=_session(
                f"/tmp/synthetic-task-guidance/{run_id}/workspace",
                prompt="Assess the synthetic tg02 retain handoff.",
                response=json.dumps(record["assessment"], indent=2),
                compiled="synthetic assessor guidance",
                run_id=run_id,
            ),
        )
    frozen["handoff_semantic_records"] = records
    frozen["status"]["handoff_semantics"] = {
        "expected": 2,
        "present": 2,
        "missing": [],
    }
    paths["frozen_path"].write_text(
        json.dumps(frozen, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    package_dir = tmp_path / "package"
    collect(
        package_dir=package_dir,
        artifact_root=paths["artifact_root"],
        frozen_path=paths["frozen_path"],
        cells=list(SYNTHETIC_CELLS),
        bundle=DEFAULT_BUNDLE,
    )
    prefix = f"scenarios/{HANDOFF_SCENARIO_ID}/glm-max/assessment/handoff/retain/s0"
    for ordinal, run_id in (
        ("j1", "synthetic-tg02-handoff-retain-1"),
        ("j2", "synthetic-tg02-handoff-retain-2"),
    ):
        run = json.loads(
            (package_dir / prefix / ordinal / "run.json").read_text(encoding="utf-8")
        )
        assert run["run_id"] == run_id


def test_collect_uses_the_named_run_of_each_producer_sample(
    tmp_path: Path,
) -> None:
    """The producer page shows the exact run of its frozen record.

    A cell with two samples keeps both in the frozen dataset; the
    collected page must render the first sample's own run, not the newest
    raw run of the cell.
    """

    paths = _build_synthetic_evaluation(tmp_path)
    frozen = paths["frozen"]
    first = dict(frozen["producer_records"][0])
    first["run_id"] = PRODUCER_RUN_ID
    second = dict(first)
    second["run_id"] = "synthetic-tg02-producer-second"
    second["response"] = "Created the pagination task, second sample."
    frozen["producer_records"][0] = first
    frozen["producer_records"].insert(1, second)
    _write_run(
        paths["artifact_root"],
        run_id="synthetic-tg02-producer-second",
        record_name="task-guidance-producer.json",
        record=second,
        session=_session(
            "/tmp/synthetic-task-guidance/synthetic-tg02-producer-second/workspace",
            prompt=second["prompt"],
            response=second["response"],
            compiled="synthetic compiled guidance",
            run_id="synthetic-tg02-producer-second",
        ),
    )
    paths["frozen_path"].write_text(
        json.dumps(frozen, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    package_dir = tmp_path / "package"
    collect(
        package_dir=package_dir,
        artifact_root=paths["artifact_root"],
        frozen_path=paths["frozen_path"],
        cells=list(SYNTHETIC_CELLS),
        bundle=DEFAULT_BUNDLE,
    )
    run = json.loads(
        (
            package_dir / f"scenarios/{HANDOFF_SCENARIO_ID}/glm-max/s0/run.json"
        ).read_text(encoding="utf-8")
    )
    assert run["run_id"] == PRODUCER_RUN_ID


def test_collect_renders_each_handoff_variant_of_one_subject(
    tmp_path: Path,
) -> None:
    """Per-subject handoff judgments of one subject collect per variant.

    The retain, omit, generated-task, and incomplete judgments of one
    producer cell share the subject mapping; only the assessment variant
    distinguishes them. Collection must map each frozen record to its own
    assessor run instead of collapsing them onto the newest match.
    """

    paths = _build_synthetic_evaluation(tmp_path)
    frozen = paths["frozen"]
    records = [
        _per_subject_handoff_record(
            HANDOFF_SCENARIO_ID, variant="retain", stage="fresh-agent", score=90
        ),
        _per_subject_handoff_record(
            HANDOFF_SCENARIO_ID, variant="omit", stage="fresh-agent", score=80
        ),
    ]
    frozen["handoff_semantic_records"] = records
    frozen["status"]["handoff_semantics"] = {
        "expected": 2,
        "present": 2,
        "missing": [],
    }
    for record in records:
        variant = record["assessment"]["variant"]
        run_id = f"synthetic-tg02-handoff-{variant}"
        _write_run(
            paths["artifact_root"],
            run_id=run_id,
            record_name="task-guidance-handoff-semantic.json",
            record=record,
            session=_session(
                f"/tmp/synthetic-task-guidance/{run_id}/workspace",
                prompt=f"Assess the synthetic tg02 {variant} handoff.",
                response=json.dumps(record["assessment"], indent=2),
                compiled="synthetic assessor guidance",
                run_id=run_id,
            ),
        )
    paths["frozen_path"].write_text(
        json.dumps(frozen, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    package_dir = tmp_path / "package"
    collect(
        package_dir=package_dir,
        artifact_root=paths["artifact_root"],
        frozen_path=paths["frozen_path"],
        cells=list(SYNTHETIC_CELLS),
        bundle=DEFAULT_BUNDLE,
    )
    assessment_prefix = f"scenarios/{HANDOFF_SCENARIO_ID}/glm-max/assessment/handoff"
    for variant in ("retain", "omit"):
        assert (package_dir / assessment_prefix / variant / "s0" / "run.json").is_file()
    results = (
        package_dir / f"scenarios/{HANDOFF_SCENARIO_ID}/assessment/handoff/results.md"
    ).read_text(encoding="utf-8")
    assert "(retain, fresh-agent)" in results
    assert "(omit, fresh-agent)" in results


def test_collect_builds_complete_synthetic_package(tmp_path: Path) -> None:
    package_dir = _collect_synthetic(tmp_path)

    expected_top = {
        "index.md",
        "matrix.md",
        "costs.md",
        "costs.csv",
        "manifest.json",
        "aggregate.json",
        "report-config.toml",
    }
    assert expected_top <= {
        path.name for path in package_dir.iterdir() if path.is_file()
    }
    handoff_prefix = f"scenarios/{HANDOFF_SCENARIO_ID}"
    cell_prefix = f"{handoff_prefix}/glm-max"
    expected_files = {
        f"{handoff_prefix}/target.md",
        f"{cell_prefix}/s0/run.json",
        f"{cell_prefix}/s0/session.md",
        f"{cell_prefix}/s0/task-files/tasks/synthetic-{HANDOFF_SCENARIO_ID}.md",
        f"{cell_prefix}/plan-retain/s0/run.json",
        f"{cell_prefix}/plan-retain/s0/session.md",
        f"{cell_prefix}/plan-omit/s0/run.json",
        f"{cell_prefix}/plan-omit/s0/session.md",
        f"{cell_prefix}/continuation/s0/run.json",
        f"{cell_prefix}/continuation/s0/session.md",
        f"{cell_prefix}/control/s0/run.json",
        f"{cell_prefix}/control/s0/session.md",
        f"{handoff_prefix}/assessment/task-creation/run.json",
        f"{handoff_prefix}/assessment/task-creation/session.md",
        f"{handoff_prefix}/assessment/task-creation/results.md",
        f"{handoff_prefix}/assessment/handoff/run.json",
        f"{handoff_prefix}/assessment/handoff/session.md",
        f"{handoff_prefix}/assessment/handoff/results.md",
        f"{handoff_prefix}/results.md",
        f"scenarios/{DECOMPOSITION_SCENARIO_ID}/target.md",
        f"scenarios/{DECOMPOSITION_SCENARIO_ID}/glm-max/s0/run.json",
        f"scenarios/{DECOMPOSITION_SCENARIO_ID}/results.md",
        f"scenarios/{DECOMPOSITION_SCENARIO_ID}/assessment/task-creation/results.md",
        "shared/configs/glm-max.json",
        "shared/configs/glm-assessor-max.json",
    }
    collected = {
        path.relative_to(package_dir).as_posix()
        for path in package_dir.rglob("*")
        if path.is_file()
    }
    assert expected_files <= collected

    # The continuation inherits the producer's compiled system message and
    # bounds its inherited prefix with the parent session.
    continuation_run = json.loads(
        (package_dir / f"{cell_prefix}/continuation/s0/run.json").read_text(
            encoding="utf-8"
        )
    )
    assert continuation_run["lineage"]["parent_run_id"] == PRODUCER_RUN_ID
    producer_session = json.loads(
        (
            tmp_path
            / "artifact"
            / "glm"
            / "runs"
            / PRODUCER_RUN_ID
            / "raw"
            / "environment"
            / "crystal-lattice-session.json"
        ).read_text(encoding="utf-8")
    )
    assert continuation_run["lineage"]["inherited_prefix"]["length"] == len(
        producer_session["messages"]
    )
    assert continuation_run["system_message"]["availability"]["state"] == "inherited"
    producer_run = json.loads(
        (package_dir / f"{cell_prefix}/s0/run.json").read_text(encoding="utf-8")
    )
    assert (
        continuation_run["system_message"]["path"]
        == producer_run["system_message"]["path"]
    )
    assert producer_run["system_message"]["availability"]["state"] == "captured"

    # The assessor config records the assessment request overrides faithfully.
    assessor_config = json.loads(
        (package_dir / "shared/configs/glm-assessor-max.json").read_text(
            encoding="utf-8"
        )
    )
    assert assessor_config["request_overrides"]["include_tasks"] is False
    subject_config = json.loads(
        (package_dir / "shared/configs/glm-max.json").read_text(encoding="utf-8")
    )
    assert subject_config["request_overrides"]["include_tasks"] is True

    # Aggregate details link every judgment to its run and rendering.
    aggregate = json.loads((package_dir / "aggregate.json").read_text(encoding="utf-8"))
    details = aggregate["assessment_details"]
    assert [row["kind"] for row in details] == ["task-creation"] * 2 + ["handoff"] * 4
    assert details[0]["run_path"] == f"scenarios/{HANDOFF_SCENARIO_ID}/glm-max/s0"
    assert details[2]["run_path"] == f"{cell_prefix}/continuation/s0"
    assert details[3]["run_path"] == f"{cell_prefix}/control/s0"
    assert details[4]["run_path"] == f"{cell_prefix}/plan-omit/s0"
    assert details[5]["run_path"] == f"{cell_prefix}/plan-retain/s0"
    assert aggregate["invalid_records"] == []

    # The matrix links run directories and judgment renderings.
    matrix = (package_dir / "matrix.md").read_text(encoding="utf-8")
    assert f"]({cell_prefix}/plan-omit/s0)" in matrix
    assert f"]({handoff_prefix}/assessment/task-creation/results.md)" in matrix
    assert "| GLM max |" in matrix

    # Session transcripts keep the model response verbatim.
    producer_session_md = (package_dir / f"{cell_prefix}/s0/session.md").read_text(
        encoding="utf-8"
    )
    assert "Created the pagination task." in producer_session_md
    assert "<workspace>" in producer_session_md

    # Costs stay unknown for synthetic GLM runs without usage metadata.
    costs_csv = (package_dir / "costs.csv").read_text(encoding="utf-8")
    data_lines = costs_csv.strip().splitlines()[1:]
    assert len(data_lines) == 9
    assert all(",unavailable," in line for line in data_lines)


def test_synthetic_package_check_render_and_determinism(tmp_path: Path) -> None:
    package_dir = _collect_synthetic(tmp_path)

    assert (
        check_result_package(
            package_dir, view_builders=[_build_index_views, _build_case_views]
        )
        == []
    )

    manifest = json.loads((package_dir / "manifest.json").read_text(encoding="utf-8"))
    generated = set(manifest["files"]["generated"])
    assert {"index.md", "matrix.md", "costs.md", "costs.csv"} <= generated
    before = {
        relative: (package_dir / relative).read_bytes()
        for relative in (
            path.relative_to(package_dir).as_posix()
            for path in package_dir.rglob("*")
            if path.is_file()
        )
    }
    for relative in generated:
        (package_dir / relative).unlink()
    render_result_package(
        package_dir, view_builders=[_build_index_views, _build_case_views]
    )
    after = {
        relative: (package_dir / relative).read_bytes()
        for relative in (
            path.relative_to(package_dir).as_posix()
            for path in package_dir.rglob("*")
            if path.is_file()
        )
    }
    assert before == after

    # A second collection from the same synthetic inputs is byte-identical.
    first, second = _collect_twice(tmp_path / "determinism")
    first_files = {
        path.relative_to(first).as_posix(): path.read_bytes()
        for path in first.rglob("*")
        if path.is_file()
    }
    second_files = {
        path.relative_to(second).as_posix(): path.read_bytes()
        for path in second.rglob("*")
        if path.is_file()
    }
    assert first_files == second_files


def test_collect_reports_missing_raw_run(tmp_path: Path) -> None:
    paths = _build_synthetic_evaluation(tmp_path)
    control_dir = paths["artifact_root"] / "glm" / "runs" / "synthetic-tg02-control"
    control_dir.rename(tmp_path / "removed-control")

    try:
        collect(
            package_dir=tmp_path / "package",
            artifact_root=paths["artifact_root"],
            frozen_path=paths["frozen_path"],
            cells=list(SYNTHETIC_CELLS),
            bundle=DEFAULT_BUNDLE,
        )
    except FileNotFoundError as error:
        assert "task-guidance-negative-control.json" in str(error)
        assert "incomplete" in str(error)
    else:
        raise AssertionError("collect accepted a missing raw control run")


def test_collect_exports_invalid_samples_beside_valid_evidence(
    tmp_path: Path,
) -> None:
    """A failed sample of one cell exports beside the valid one.

    The valid sample claims the sample index its run model recorded;
    the provider-failed re-run under another label fills the next free
    index and carries an ``invalid.md`` note recording why it failed.
    """

    paths = _build_synthetic_evaluation(tmp_path)
    frozen = paths["frozen"]
    invalid = _producer_record(
        HANDOFF_SCENARIO_ID,
        response="The provider failed before any task file was written.",
        task_file="",
    )
    invalid["task_files"] = {}
    invalid["changed_paths"] = []
    invalid["valid"] = False
    invalid["invalid_reasons"] = ['run failure: None, ("provider outage",)']
    invalid["run_id"] = "synthetic-tg02-producer-failed"
    _write_run(
        paths["artifact_root"],
        run_id="synthetic-tg02-producer-failed",
        record_name="task-guidance-producer.json",
        record=invalid,
        session=_session(
            "/tmp/synthetic-task-guidance/synthetic-tg02-producer-failed/workspace",
            prompt="Create the synthetic pagination task.",
            response="The provider failed before any task file was written.",
            compiled="synthetic compiled guidance",
            run_id="synthetic-tg02-producer-failed",
        ),
    )
    frozen["producer_records"][0]["run_id"] = PRODUCER_RUN_ID
    frozen["producer_records"].append(invalid)
    paths["frozen_path"].write_text(
        json.dumps(frozen, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    package_dir = tmp_path / "package"
    collect(
        package_dir=package_dir,
        artifact_root=paths["artifact_root"],
        frozen_path=paths["frozen_path"],
        cells=list(SYNTHETIC_CELLS),
        bundle=DEFAULT_BUNDLE,
    )
    cell = package_dir / f"scenarios/{HANDOFF_SCENARIO_ID}/glm-max"
    assert (cell / "s0" / "run.json").is_file()
    note = (cell / "s1" / "invalid.md").read_text(encoding="utf-8")
    assert "**provider failure**" in note
    assert "run failure: None" in note
    assert f"`{SYNTHETIC_RUN_LABEL}`" in note

    matrix = (package_dir / "matrix.md").read_text(encoding="utf-8")
    assert "## Invalid records — provider failures" in matrix
    assert "## Invalid records — validity failures" not in matrix
    assert "provider outage" in matrix

    results = (package_dir / f"scenarios/{HANDOFF_SCENARIO_ID}/results.md").read_text(
        encoding="utf-8"
    )
    assert "| valid |" in results
    assert "| invalid |" in results
    assert f"({cell.name}/s1/invalid.md)" in results


def test_collect_renders_file_fidelity_and_readability_beside_subjects(
    tmp_path: Path,
) -> None:
    """Fidelity and readability judgments live inside the judged cell.

    Both assessor runs sit under ``<cell>/assessment/``, their grades
    render in the producer sample's ``assessment.md``, the scenario
    ``results.md`` producer row carries them, and the matrix gains the
    fidelity and readability cohort tables.
    """

    paths = _build_synthetic_evaluation(tmp_path)
    frozen = paths["frozen"]
    fidelity = {
        "schema_version": 1,
        "scenario_id": HANDOFF_SCENARIO_ID,
        "subject": {"profile": "glm", "reasoning_effort": "max", "sample_index": 0},
        "assessment": {
            "dimensions": {
                "plan_design_completeness": {"grade": "complete", "findings": []},
                "durable_context_preservation": {
                    "grade": "partial",
                    "findings": [
                        {
                            "where": "Supporting details",
                            "quote": "…",
                            "why": "dropped the ordering guarantee",
                        }
                    ],
                },
                "section_appropriateness": {"grade": "complete", "findings": []},
                "plan_justification": {"grade": "justified", "findings": []},
                "task_kind_fit": {"grade": "fits", "findings": []},
            },
            "mistakes": [
                {
                    "where": "Requirements",
                    "quote": "…",
                    "why": "invented a delivery constraint",
                }
            ],
            "summary": "Synthetic fidelity judgment.",
        },
        "summary": "Synthetic fidelity judgment.",
    }
    readability = {
        "schema_version": 1,
        "scenario_id": HANDOFF_SCENARIO_ID,
        "subject": {"profile": "glm", "reasoning_effort": "max", "sample_index": 0},
        "assessment": {
            "sections": {
                "Requirements checklist": {"grade": "readable", "findings": []},
                "Supporting details": {
                    "grade": "partial",
                    "findings": [
                        {
                            "where": "Supporting details",
                            "quote": "…",
                            "why": "one dense paragraph carries three facts",
                        }
                    ],
                },
            },
            "navigation": {"grade": "navigable", "findings": []},
            "mistakes": [],
            "summary": "Synthetic readability judgment.",
        },
        "summary": "Synthetic readability judgment.",
    }
    for name, record_name, record in (
        ("file-fidelity", "task-guidance-file-fidelity.json", fidelity),
        ("file-readability", "task-guidance-file-readability.json", readability),
    ):
        record["run_id"] = f"synthetic-tg02-{name}"
        _write_run(
            paths["artifact_root"],
            run_id=f"synthetic-tg02-{name}",
            record_name=record_name,
            record=record,
            session=_session(
                f"/tmp/synthetic-task-guidance/synthetic-tg02-{name}/workspace",
                prompt=f"Assess the synthetic tg02 files ({name}).",
                response=json.dumps(record["assessment"], indent=2),
                compiled="synthetic assessor guidance",
                run_id=f"synthetic-tg02-{name}",
            ),
        )
    frozen["file_fidelity_records"] = [fidelity]
    frozen["file_readability_records"] = [readability]
    frozen["status"]["file_fidelity"] = {"expected": 1, "present": 1, "missing": []}
    frozen["status"]["file_readability"] = {"expected": 1, "present": 1, "missing": []}
    paths["frozen_path"].write_text(
        json.dumps(frozen, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    package_dir = tmp_path / "package"
    collect(
        package_dir=package_dir,
        artifact_root=paths["artifact_root"],
        frozen_path=paths["frozen_path"],
        cells=list(SYNTHETIC_CELLS),
        bundle=DEFAULT_BUNDLE,
    )
    cell = package_dir / f"scenarios/{HANDOFF_SCENARIO_ID}/glm-max"
    assert (cell / "assessment" / "file-fidelity" / "s0" / "run.json").is_file()
    assert (cell / "assessment" / "file-readability" / "s0" / "run.json").is_file()
    subject_note = (cell / "s0" / "assessment.md").read_text(encoding="utf-8")
    assert "## file-fidelity assessment" in subject_note
    assert "durable_context_preservation: **partial** (1 findings)" in subject_note
    assert "## file-readability assessment" in subject_note
    assert "Supporting details: **partial**" in subject_note
    assert "Navigation: **navigable**" in subject_note

    results = (package_dir / f"scenarios/{HANDOFF_SCENARIO_ID}/results.md").read_text(
        encoding="utf-8"
    )
    producer_rows = [
        line for line in results.splitlines() if line.startswith("| [`glm-max`]")
    ]
    assert producer_rows and "context partial" in producer_rows[0]
    assert "1/2 readable" in producer_rows[0]

    matrix = (package_dir / "matrix.md").read_text(encoding="utf-8")
    assert "## Task-file fidelity" in matrix
    assert "## Task-file fidelity detail" in matrix
    assert "## Task-file readability" in matrix
    assert "## Task-file readability detail" in matrix
    assert f"](scenarios/{HANDOFF_SCENARIO_ID}/glm-max/s0/assessment.md)" in matrix


def test_collect_renders_plan_content_judgment_beside_its_subject(
    tmp_path: Path,
) -> None:
    """A plan-content judgment lives inside the judged plan-stage cell.

    The assessor run sits under ``<cell>/assessment/plan-content/``, the
    grades render in the judged plan sample's ``assessment.md``, the
    scenario ``results.md`` plan-stage row carries the coverage, and the
    matrix gains the plan-content cohort and detail tables.
    """

    paths = _build_synthetic_evaluation(tmp_path)
    frozen = paths["frozen"]
    requirements: dict[str, dict[str, str]] = {
        f"PLAN-{index}": {"grade": "conveyed", "finding": ""} for index in range(1, 6)
    }
    requirements["GENERIC-1"] = {
        "grade": "partial",
        "finding": "the URL-pattern decision is not marked open",
    }
    for index in range(2, 9):
        requirements[f"GENERIC-{index}"] = {"grade": "conveyed", "finding": ""}
    requirements["GENERIC-9"] = {"grade": "self-contained", "finding": ""}
    requirements["GENERIC-10"] = {"grade": "proportionate", "finding": ""}
    assessment = {
        "stage": "fresh-agent",
        "variant": "omit",
        "requirements": requirements,
        "missed_requirements": [],
        "coverage": round(14 / 15, 3),
        "summary": "Synthetic plan-content judgment.",
    }
    record = {
        "schema_version": 1,
        "scenario_id": HANDOFF_SCENARIO_ID,
        "subject": {"profile": "glm", "reasoning_effort": "max", "sample_index": 0},
        "assessment": assessment,
        "summary": "Synthetic plan-content judgment.",
    }
    record["run_id"] = "synthetic-tg02-plan-content"
    _write_run(
        paths["artifact_root"],
        run_id="synthetic-tg02-plan-content",
        record_name="task-guidance-plan-content.json",
        record=record,
        session=_session(
            "/tmp/synthetic-task-guidance/synthetic-tg02-plan-content/workspace",
            prompt="Assess the synthetic tg02 presented plan.",
            response=json.dumps(assessment, indent=2),
            compiled="synthetic assessor guidance",
            run_id="synthetic-tg02-plan-content",
        ),
    )
    frozen["plan_content_records"] = [record]
    frozen["status"]["plan_contents"] = {"expected": 1, "present": 1, "missing": []}
    paths["frozen_path"].write_text(
        json.dumps(frozen, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    package_dir = tmp_path / "package"
    collect(
        package_dir=package_dir,
        artifact_root=paths["artifact_root"],
        frozen_path=paths["frozen_path"],
        cells=list(SYNTHETIC_CELLS),
        bundle=DEFAULT_BUNDLE,
    )
    cell = package_dir / f"scenarios/{HANDOFF_SCENARIO_ID}/glm-max"
    assessor_run = cell / "assessment" / "plan-content" / "omit" / "s0" / "run.json"
    assert assessor_run.is_file()
    subject_note = (cell / "plan-omit" / "s0" / "assessment.md").read_text(
        encoding="utf-8"
    )
    assert "## plan-content assessment" in subject_note
    assert "Top-grade coverage: **93%**" in subject_note
    assert "GENERIC-1: **partial**" in subject_note
    assert "](../../assessment/plan-content/omit/s0/session.md)" in subject_note

    results = (package_dir / f"scenarios/{HANDOFF_SCENARIO_ID}/results.md").read_text(
        encoding="utf-8"
    )
    plan_rows = [
        line
        for line in results.splitlines()
        if "`plan-omit`" in line and line.startswith("|")
    ]
    assert plan_rows and plan_rows[0].rstrip().endswith("| 93% |")

    matrix = (package_dir / "matrix.md").read_text(encoding="utf-8")
    assert "## Presented-plan content" in matrix
    assert "| GENERIC-1 | 0% |" in matrix
    assert "| omit | 1 | 93% |" in matrix
    assert "## Presented-plan content detail" in matrix
    assert (
        f"](scenarios/{HANDOFF_SCENARIO_ID}/{cell.name}/plan-omit/s0/assessment.md)"
        in matrix
    )
    assert (
        f"scenarios/{HANDOFF_SCENARIO_ID}/assessment/plan-content/results.md" in matrix
    )


def test_collect_renders_quality_judgment_beside_its_subject(
    tmp_path: Path,
) -> None:
    """A task-quality judgment lives inside the judged cell's subtree.

    The assessor run sits under ``<cell>/assessment/task-quality/``, the
    grades render as ``assessment.md`` beside the judged sample, the
    scenario ``results.md`` row carries them, and the matrix gains the
    quality cohort and detail tables.
    """

    paths = _build_synthetic_evaluation(tmp_path)
    frozen = paths["frozen"]
    record = {
        "schema_version": 2,
        "dataset_id": SYNTHETIC_DATASET_ID,
        "scenario_id": HANDOFF_SCENARIO_ID,
        "subject": {"profile": "glm", "reasoning_effort": "max", "sample_index": 0},
        "assessment": {
            "task_kind": "development",
            "dimensions": {
                "plan_design_completeness": {
                    "grade": "complete",
                    "occurrences": [],
                },
                "durable_context_preservation": {
                    "grade": "partial",
                    "occurrences": [
                        {
                            "description": "dropped the verification approach",
                            "evidence": "plan section",
                        }
                    ],
                },
                "findability": {"grade": "complete", "occurrences": []},
                "section_appropriateness": {"grade": "complete", "occurrences": []},
                "plan_justification": {"grade": "justified", "occurrences": []},
                "task_kind_fit": {"grade": "fits", "occurrences": []},
            },
            "summary": "Synthetic quality judgment.",
        },
        "summary": "Synthetic quality judgment.",
    }
    record["run_id"] = "synthetic-tg02-quality"
    _write_run(
        paths["artifact_root"],
        run_id="synthetic-tg02-quality",
        record_name="task-guidance-quality.json",
        record=record,
        session=_session(
            "/tmp/synthetic-task-guidance/synthetic-tg02-quality/workspace",
            prompt="Assess the synthetic tg02 task files.",
            response=json.dumps(record["assessment"], indent=2),
            compiled="synthetic assessor guidance",
            run_id="synthetic-tg02-quality",
        ),
    )
    frozen["quality_records"] = [record]
    frozen["status"]["quality"] = {"expected": 1, "present": 1, "missing": []}
    paths["frozen_path"].write_text(
        json.dumps(frozen, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    package_dir = tmp_path / "package"
    collect(
        package_dir=package_dir,
        artifact_root=paths["artifact_root"],
        frozen_path=paths["frozen_path"],
        cells=list(SYNTHETIC_CELLS),
        bundle=DEFAULT_BUNDLE,
    )
    cell = package_dir / f"scenarios/{HANDOFF_SCENARIO_ID}/glm-max"
    assessor_run = cell / "assessment" / "task-quality" / "s0" / "run.json"
    assert assessor_run.is_file()
    subject_note = (cell / "s0" / "assessment.md").read_text(encoding="utf-8")
    assert "## task-quality assessment" in subject_note
    assert "durable_context_preservation: **partial**" in subject_note
    assert "](../assessment/task-quality/s0/session.md)" in subject_note

    results = (package_dir / f"scenarios/{HANDOFF_SCENARIO_ID}/results.md").read_text(
        encoding="utf-8"
    )
    assert "context partial" in results

    matrix = (package_dir / "matrix.md").read_text(encoding="utf-8")
    assert "## Task-file quality" in matrix
    assert "| All | 1 | 83% |" in matrix
    assert "## Task-file quality detail" in matrix
    assert f"](scenarios/{HANDOFF_SCENARIO_ID}/{cell.name}/s0/assessment.md)" in matrix
