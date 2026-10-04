"""Suite-integration tests: the runner assembles over the run-model layer.

The harness composes request identities through the layer's
``request_identity`` — run labels are structurally absent from the cache
key — and executes every stage through ``RunModel`` (``fresh`` and
``samples`` semantics). The freeze and results adapters delegate record
selection to the consolidation core: labels select cells (latest label per
cell by default, every sample of the listed labels explicitly), legacy
attempt records stay readable, expected sets derive from the configuration
manifest and stage catalog, and the frozen dataset records the guidance
bundle provenance.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from agent_eval.runner import RunModel, request_identity

from .. import freeze
from ..configuration import (
    AGENTS,
    DEFAULT_BUNDLE,
    negative_control,
    selected_bundle,
)
from ..fixtures import AssessmentWorkspaceFactory, TaskGuidanceWorkspaceFactory
from ..handoffs import (
    CanonicalHandoffWorkspaceFactory,
    GeneratedTaskWorkspaceFactory,
)
from ..results import consolidate_results, render_summary
from ..runner import (
    RUNNER_VERSION,
    TaskGuidanceHarness,
    assessment_identity,
    continuation_identity,
    from_plan_identity,
    handoff_plan_identity,
    planning_session_identity,
    task_creation_identity,
)
from ..scenarios import scenario_by_id
from ..stages import STAGES


SCENARIO = scenario_by_id("tg01-eleventy-archive-handoff")


# --- Identities compose through the layer ---------------------------------


def test_task_creation_identity_composes_through_the_layer() -> None:
    identity = task_creation_identity(
        agent_name="glm",
        scenario=SCENARIO,
        reasoning_effort="max",
        workspace_fingerprint={"fixture": "v5"},
        target_sha256="abc123",
    )

    assert identity == request_identity(
        namespace="task-guidance",
        version=RUNNER_VERSION,
        components={
            "stage": "task-creation",
            "agent": "glm",
            "model": AGENTS["glm"]["model"],
            "scenario": SCENARIO.scenario_id,
            "effort": "max",
            "workspace_fingerprint": {"fixture": "v5"},
            "target_sha256": "abc123",
        },
    )
    changed = task_creation_identity(
        agent_name="glm",
        scenario=SCENARIO,
        reasoning_effort="high",
        workspace_fingerprint={"fixture": "v5"},
        target_sha256="abc123",
    )
    assert changed != identity


def test_handoff_plan_identity_includes_the_variant() -> None:
    base = {
        "agent_name": "gpt",
        "scenario": SCENARIO,
        "reasoning_effort": "high",
        "workspace_fingerprint": {"fixture": "v5"},
    }
    retain = handoff_plan_identity(variant="retain", **base)
    omit = handoff_plan_identity(variant="omit", **base)

    assert retain != omit
    assert retain == handoff_plan_identity(variant="retain", **base)
    assert retain.startswith("task-guidance:")


def test_planning_session_identity_includes_the_variant() -> None:
    base = {
        "agent_name": "glm",
        "scenario": SCENARIO,
        "reasoning_effort": "max",
        "workspace_fingerprint": {"fixture": "v5"},
    }
    guided = planning_session_identity(variant="guided", **base)
    unguided = planning_session_identity(variant="unguided", **base)

    assert guided != unguided
    assert guided == planning_session_identity(variant="guided", **base)
    assert guided.startswith("task-guidance:")
    # The reasoning-state variant is part of the cache identity.
    assert guided != planning_session_identity(
        variant="guided",
        thinking="strip",
        **base,
    )


def test_from_plan_identity_includes_variant_and_parent_identity() -> None:
    base = {
        "agent_name": "gpt",
        "scenario": SCENARIO,
        "reasoning_effort": "high",
    }
    standard = from_plan_identity(
        variant="standard",
        parent_identity="task-guidance:v1:plan-a",
        **base,
    )

    assert standard != from_plan_identity(
        variant="omit-plan",
        parent_identity="task-guidance:v1:plan-a",
        **base,
    )
    assert standard != from_plan_identity(
        variant="standard",
        parent_identity="task-guidance:v1:plan-b",
        **base,
    )
    assert standard == from_plan_identity(
        variant="standard",
        parent_identity="task-guidance:v1:plan-a",
        **base,
    )


def test_continuation_identity_includes_the_parent_identity() -> None:
    first = continuation_identity(
        agent_name="glm",
        scenario=SCENARIO,
        reasoning_effort="max",
        parent_identity="task-guidance:v1:parent-hash",
    )
    other_parent = continuation_identity(
        agent_name="glm",
        scenario=SCENARIO,
        reasoning_effort="max",
        parent_identity="task-guidance:v1:different-hash",
    )

    assert first != other_parent
    assert first == continuation_identity(
        agent_name="glm",
        scenario=SCENARIO,
        reasoning_effort="max",
        parent_identity="task-guidance:v1:parent-hash",
    )


def test_assessment_identity_includes_the_prompt() -> None:
    base = {
        "agent_name": "glm",
        "test_id": "task-guidance-assessment-demo",
        "reasoning_effort": "max",
    }
    first = assessment_identity(prompt="judge this", **base)
    changed = assessment_identity(prompt="judge that", **base)

    assert first != changed
    assert first == assessment_identity(prompt="judge this", **base)


# --- The harness executes through the run model ---------------------------


def _dummy_run(run_id: str = "run-1") -> SimpleNamespace:
    return SimpleNamespace(
        run_id=run_id,
        name="dummy",
        value=None,
        workspace=None,
        artifact_dir=None,
        error=None,
        cache_hit=False,
        changed_paths=(),
        record=lambda *args, **kwargs: None,
    )


def test_harness_owns_one_labeled_run_model(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AGENT_EVAL_ARTIFACT_ROOT", str(tmp_path))

    harness = TaskGuidanceHarness("glm", label="assembly-shot")
    try:
        assert isinstance(harness.model, RunModel)
        assert harness.model.label == "assembly-shot"
    finally:
        harness.close()

    default = TaskGuidanceHarness("glm")
    try:
        assert default.model.label  # generated when not given
    finally:
        default.close()


def test_stage_runs_compose_layer_identities_and_pass_execution_options(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AGENT_EVAL_ARTIFACT_ROOT", str(tmp_path))
    harness = TaskGuidanceHarness("glm", label="assembly")
    try:
        captured: list[dict[str, object]] = []

        def fake_run(model, name, program, *, identity, workspace, **kwargs):
            captured.append({"name": name, "identity": identity, **kwargs})
            return _dummy_run()

        monkeypatch.setattr(RunModel, "run", fake_run)

        factory = TaskGuidanceWorkspaceFactory(
            scenario=SCENARIO,
            bundle=selected_bundle(),
        )
        (run,) = harness.run_task_creation(
            scenario=SCENARIO,
            reasoning_effort="max",
            fresh=True,
        )
        assert run.run_id == "run-1"
        assert len(captured) == 1
        assert captured[0]["fresh"] is True
        assert captured[0]["identity"] == task_creation_identity(
            agent_name="glm",
            scenario=SCENARIO,
            reasoning_effort="max",
            workspace_fingerprint=factory.fingerprint(),
            target_sha256=hashlib.sha256(SCENARIO.target_path.read_bytes()).hexdigest(),
        )

        handoff_factory = CanonicalHandoffWorkspaceFactory(
            scenario=SCENARIO,
            variant="retain",
            bundle=selected_bundle(),
        )
        harness.run_plan_from_handoff(
            scenario=SCENARIO,
            variant="retain",
            reasoning_effort="max",
        )
        assert captured[1]["identity"] == handoff_plan_identity(
            agent_name="glm",
            scenario=SCENARIO,
            variant="retain",
            reasoning_effort="max",
            workspace_fingerprint=handoff_factory.fingerprint(),
        )
    finally:
        harness.close()


def test_sample_counts_execute_through_the_layer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AGENT_EVAL_ARTIFACT_ROOT", str(tmp_path))
    harness = TaskGuidanceHarness("glm", label="assembly")
    try:
        captured: list[dict[str, object]] = []

        def fake_samples(model, name, program, *, identity, count, **kwargs):
            captured.append({"identity": identity, "count": count})
            return tuple(_dummy_run(f"run-{i}") for i in range(count))

        monkeypatch.setattr(RunModel, "run_samples", fake_samples)

        runs = harness.run_task_creation(
            scenario=SCENARIO,
            reasoning_effort="max",
            samples=3,
        )
        assert len(runs) == 3
        assert captured[0]["count"] == 3
    finally:
        harness.close()


def test_continuation_reads_the_parent_identity_from_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AGENT_EVAL_ARTIFACT_ROOT", str(tmp_path))
    harness = TaskGuidanceHarness("glm", label="assembly")
    try:
        captured: list[dict[str, object]] = []

        def fake_run(model, name, program, *, identity, workspace, **kwargs):
            captured.append(
                {
                    "name": name,
                    "identity": identity,
                    "workspace": workspace,
                    **kwargs,
                }
            )
            return _dummy_run()

        monkeypatch.setattr(RunModel, "run", fake_run)

        parent_dir = tmp_path / "glm" / "runs" / "parent-run"
        (parent_dir / "records").mkdir(parents=True)
        (parent_dir / "records" / "run-model.json").write_text(
            json.dumps(
                {
                    "schema": 1,
                    "label": "assembly",
                    "identity": "task-guidance:v1:parent-hash",
                    "cache_hit": False,
                    "sample_index": 0,
                    "run_id": "parent-run",
                }
            ),
            encoding="utf-8",
        )
        parent = SimpleNamespace(
            run_id="parent-run",
            workspace=tmp_path / "parent-workspace",
            artifact_dir=parent_dir,
        )
        (tmp_path / "parent-workspace").mkdir()

        harness.continue_same_agent_plan(
            parent=parent,
            scenario=SCENARIO,
            reasoning_effort="max",
        )
        assert len(captured) == 1
        assert captured[0]["identity"] == continuation_identity(
            agent_name="glm",
            scenario=SCENARIO,
            reasoning_effort="max",
            parent_identity="task-guidance:v1:parent-hash",
        )
        assert captured[0]["workspace"] == parent.workspace
        assert captured[0]["continue_from"] is parent
    finally:
        harness.close()


# --- Stage mechanics match the catalog -------------------------------------

WORKSPACE_ORIGINS = {
    "fixture-project": TaskGuidanceWorkspaceFactory,
    "canonical-handoff": CanonicalHandoffWorkspaceFactory,
    "generated-task": GeneratedTaskWorkspaceFactory,
    "assessment-stub": AssessmentWorkspaceFactory,
}


@pytest.mark.parametrize("stage", sorted(STAGES))
def test_stage_executor_matches_the_catalog_workspace_and_parentage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stage: str,
) -> None:
    """Every stage run starts the way its catalog entry declares.

    Three stages share an earlier run: the continuation (parent's
    workspace and session prefix), the generated-file plan (the parent's
    written files rebuilt into a fresh workspace), and the from-plan
    creation (a planning session's workspace and session prefix
    continued); every other stage starts parentless from its declared
    workspace origin.
    """

    spec = STAGES[stage]
    monkeypatch.setenv("AGENT_EVAL_ARTIFACT_ROOT", str(tmp_path))
    harness = TaskGuidanceHarness("glm", label="assembly")
    try:
        captured: list[dict[str, object]] = []

        def fake_run(model, name, program, *, identity, workspace, **kwargs):
            captured.append(
                {"name": name, "identity": identity, "workspace": workspace, **kwargs}
            )
            return _dummy_run()

        monkeypatch.setattr(RunModel, "run", fake_run)

        parent = None
        if stage in ("continuation", "generated-plan", "task-creation-from-plan"):
            parent_dir = tmp_path / "glm" / "runs" / "parent-run"
            (parent_dir / "records").mkdir(parents=True)
            (parent_dir / "records" / "run-model.json").write_text(
                json.dumps(
                    {
                        "schema": 1,
                        "label": "assembly",
                        "identity": "task-guidance:v1:parent-hash",
                        "cache_hit": False,
                        "sample_index": 0,
                        "run_id": "parent-run",
                    }
                ),
                encoding="utf-8",
            )
            parent = SimpleNamespace(
                run_id="parent-run",
                workspace=tmp_path / "parent-workspace",
                artifact_dir=parent_dir,
            )
            (tmp_path / "parent-workspace").mkdir()

        if stage == "task-creation":
            harness.run_task_creation(
                scenario=SCENARIO,
                reasoning_effort="max",
            )
        elif stage == "planning-session":
            harness.run_planning_session(
                scenario=SCENARIO,
                variant="guided",
                reasoning_effort="max",
            )
        elif stage == "task-creation-from-plan":
            assert parent is not None
            harness.run_task_creation_from_plan(
                parent=parent,
                scenario=SCENARIO,
                variant="standard",
                reasoning_effort="max",
            )
        elif stage == "handoff-plan":
            harness.run_plan_from_handoff(
                scenario=SCENARIO,
                variant="retain",
                reasoning_effort="max",
            )
        elif stage == "continuation":
            assert parent is not None
            harness.continue_same_agent_plan(
                parent=parent,
                scenario=SCENARIO,
                reasoning_effort="max",
            )
        elif stage == "negative-control":
            harness.run_negative_control(category="handoff")
        elif stage == "generated-plan":
            assert parent is not None
            parent_value = SimpleNamespace(task_files={"tasks/demo.md": "# Demo\n"})
            monkeypatch.setattr(
                "suites.task_guidance.runner.run_identity",
                lambda run: "task-guidance:v1:parent-hash",
            )
            harness.run_plan_from_generated(
                parent=SimpleNamespace(
                    value=parent_value,
                    workspace=None,
                    run_id="parent-run",
                ),
                scenario=SCENARIO,
                reasoning_effort="max",
            )
        else:
            harness.run_assessment(
                test_id=f"task-guidance-{stage}-demo",
                prompt="judge this",
                reasoning_effort="max",
            )

        assert len(captured) == 1
        executed = captured[0]
        if spec.workspace == "parent":
            assert spec.parent is not None
            assert executed["workspace"] is parent.workspace
            assert executed["continue_from"] is parent
        else:
            assert isinstance(executed["workspace"], WORKSPACE_ORIGINS[spec.workspace])
            assert executed["continue_from"] is None
        if stage == "negative-control":
            # The control plans from the designated incomplete variant.
            control = negative_control("handoff")
            assert control is not None
            assert executed["workspace"].variant == control["variant"]
    finally:
        harness.close()


# --- The adapters delegate selection to the consolidation core ------------


def _write_run_record(
    root: Path,
    agent: str,
    run_id: str,
    record_name: str,
    value: dict[str, object],
    *,
    label: str | None = None,
    sample_index: int = 0,
    modified: float = 1000.0,
) -> None:
    records = root / agent / "runs" / run_id / "records"
    records.mkdir(parents=True, exist_ok=True)
    path = records / record_name
    path.write_text(json.dumps(value), encoding="utf-8")
    if label is not None:
        (records / "run-model.json").write_text(
            json.dumps(
                {
                    "schema": 1,
                    "label": label,
                    "identity": f"identity-{run_id}",
                    "cache_hit": False,
                    "sample_index": sample_index,
                    "run_id": run_id,
                }
            ),
            encoding="utf-8",
        )
    for record_path in records.iterdir():
        os.utime(record_path, (modified, modified))


def _producer_record(
    *,
    scenario_id: str = "tg01-eleventy-archive-handoff",
    agent: str = "glm",
    effort: str = "max",
    valid: bool = True,
    response: str = "demo",
) -> dict[str, object]:
    return {
        "scenario_id": scenario_id,
        "producer": {"profile": agent, "reasoning_effort": effort},
        "valid": valid,
        "invalid_reasons": [] if valid else ["provider errors: provider limit"],
        "response": response,
        "task_files": {},
        "tool_metrics": {},
    }


def test_consolidation_selects_the_latest_label_per_cell_by_default(
    tmp_path: Path,
) -> None:
    _write_run_record(
        tmp_path,
        "glm",
        "early",
        STAGES["task-creation"].record,
        _producer_record(response="early"),
        label="l1",
        modified=1000.0,
    )
    _write_run_record(
        tmp_path,
        "glm",
        "late",
        STAGES["task-creation"].record,
        _producer_record(response="late"),
        label="l2",
        modified=2000.0,
    )

    value = consolidate_results(tmp_path)
    assert value["labels"] == ["l2"]
    assert [record["response"] for record in value["producer_records"]] == ["late"]
    assert "l2" in value["selection"]
    assert "l1" not in value["selection"]


def test_consolidation_freezes_every_sample_of_listed_labels(
    tmp_path: Path,
) -> None:
    _write_run_record(
        tmp_path,
        "glm",
        "s1",
        STAGES["task-creation"].record,
        _producer_record(response="one"),
        label="l1",
        sample_index=0,
        modified=1000.0,
    )
    _write_run_record(
        tmp_path,
        "glm",
        "s2",
        STAGES["task-creation"].record,
        _producer_record(response="two"),
        label="l2",
        sample_index=0,
        modified=2000.0,
    )

    value = consolidate_results(tmp_path, labels=["l1", "l2"])
    assert value["labels"] == ["l1", "l2"]
    assert sorted(record["response"] for record in value["producer_records"]) == [
        "one",
        "two",
    ]


def test_consolidation_still_reads_legacy_attempt_records(
    tmp_path: Path,
) -> None:
    _write_run_record(
        tmp_path,
        "glm",
        "legacy",
        STAGES["task-creation"].record,
        {
            **_producer_record(response="legacy"),
            "run_attempt": "legacy-r1",
        },
        modified=1000.0,
    )

    value = consolidate_results(tmp_path)
    assert [record["response"] for record in value["producer_records"]] == ["legacy"]


def test_frozen_dataset_records_bundle_provenance_and_schema(
    tmp_path: Path,
) -> None:
    _write_run_record(
        tmp_path,
        "glm",
        "s1",
        STAGES["task-creation"].record,
        _producer_record(),
        label="l1",
    )
    provenance = {
        "path": "/repos/guidance/current",
        "compilation_sha256": "abc123",
    }

    value = consolidate_results(tmp_path, labels=["l1"], bundle=provenance)
    assert value["schema_version"] == 2
    assert value["bundle"] == provenance
    assert value["labels"] == ["l1"]
    assert "l1" in render_summary(value)


def test_consolidation_reports_provider_blockers_per_provider_cell(
    tmp_path: Path,
) -> None:
    _write_run_record(
        tmp_path,
        "glm",
        "ok",
        STAGES["task-creation"].record,
        _producer_record(scenario_id="tg01-eleventy-archive-handoff"),
        label="l1",
        modified=1000.0,
    )
    _write_run_record(
        tmp_path,
        "gpt",
        "blocked",
        STAGES["task-creation"].record,
        _producer_record(
            scenario_id="tg02-fastapi-pagination-handoff",
            agent="gpt",
            effort="high",
            valid=False,
        ),
        label="l1",
        modified=1000.0,
    )

    value = consolidate_results(tmp_path, labels=["l1"])
    blockers = value["provider_blocker_records"]
    assert len(blockers) == 1
    assert blockers[0]["producer"]["profile"] == "gpt"
    assert value["status"]["provider_blockers"]["present"] == 1


# --- The freeze CLI is generic ---------------------------------------------


def test_freeze_cli_takes_generic_arguments_and_records_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AGENT_EVAL_GUIDANCE_BUNDLE", raising=False)
    _write_run_record(
        tmp_path,
        "glm",
        "s1",
        STAGES["task-creation"].record,
        _producer_record(),
        label="l1",
    )
    output = tmp_path / "frozen" / "dataset.json"

    code = freeze.main(
        [
            "--artifact-root",
            str(tmp_path),
            "--labels",
            "l1",
            "--dataset-id",
            "test-dataset",
            "--label",
            "test run",
            "--output",
            str(output),
        ]
    )

    assert code == 0
    value = json.loads(output.read_text(encoding="utf-8"))
    assert value["dataset_id"] == "test-dataset"
    assert value["label"] == "test run"
    assert value["labels"] == ["l1"]
    assert value["bundle"]["path"] == str(DEFAULT_BUNDLE)
    assert value["bundle"]["compilation_sha256"]
    assert output.with_suffix(".md").is_file()
