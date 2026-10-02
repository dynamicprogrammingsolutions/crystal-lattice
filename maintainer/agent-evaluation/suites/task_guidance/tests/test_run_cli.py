"""Tests for the parallel run CLI: stage selection, case planning,
parallelism configuration, and dependency-safe ordering."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ..run import (
    ALL_STAGES,
    STAGE_GROUPS,
    load_parallelism,
    plan_cases,
    run_evaluation,
    selected_stages,
)


def test_all_stages_cover_every_group_in_dependency_order() -> None:
    assert ALL_STAGES == tuple(stage for group in STAGE_GROUPS for stage in group)
    producers, dependents, assessments = STAGE_GROUPS
    assert "task-creation" in producers
    assert "continuation" in dependents
    assert "plan-content-assessment" in assessments


def test_stage_selection_preserves_dependency_order() -> None:
    assert selected_stages("plan-content-assessment,task-creation") == (
        "task-creation",
        "plan-content-assessment",
    )


def test_stage_selection_rejects_unknown_stages() -> None:
    with pytest.raises(SystemExit, match="unknown stages"):
        selected_stages("task-creation,nonsense")


def test_plan_cases_slices_by_scenario_and_agent() -> None:
    jobs = plan_cases(("task-creation",), scenarios={"tg01-eleventy-archive-handoff"})
    assert jobs
    assert all(case.scenario_id == "tg01-eleventy-archive-handoff" for _, case in jobs)
    gpt_only = plan_cases(("task-creation",), agents={"gpt"})
    assert gpt_only and all(case.agent == "gpt" for _, case in gpt_only)


def test_plan_cases_orders_assessments_after_producers() -> None:
    stages = selected_stages("all")
    order = {stage: index for index, stage in enumerate(stages)}
    jobs = plan_cases(stages)
    positions = [order[stage] for stage, _case in jobs]
    assert positions == sorted(positions)


def test_parallelism_config_requires_known_agents(tmp_path: Path) -> None:
    config = tmp_path / "parallelism.json"
    config.write_text(json.dumps({"glm": 2, "gpt": 4}), encoding="utf-8")
    assert load_parallelism(config) == {"glm": 2, "gpt": 4}

    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"unknown-agent": 2}), encoding="utf-8")
    with pytest.raises(SystemExit, match="unknown agent"):
        load_parallelism(bad)

    zero = tmp_path / "zero.json"
    zero.write_text(json.dumps({"glm": 0}), encoding="utf-8")
    with pytest.raises(SystemExit, match="must be >= 1"):
        load_parallelism(zero)


def test_parallelism_defaults_to_serial_per_agent(tmp_path: Path) -> None:
    assert load_parallelism(None) == {"glm": 1, "gpt": 1}


class _FakeCase:
    def __init__(self, case_id: str, scenario_id: str, agent: str) -> None:
        self.id = case_id
        self.scenario_id = scenario_id
        self.agent = agent
        self.effort = "max"
        self.variant = None
        self.category = "handoff"


def test_run_execution_parallelizes_and_respects_caps(monkeypatch) -> None:
    import threading
    import time

    from .. import run as run_module

    cases = [
        _FakeCase("a", "tg01-eleventy-archive-handoff", "glm"),
        _FakeCase("b", "tg02-fastapi-pagination-handoff", "glm"),
        _FakeCase("c", "tg03-flask-vue-refresh-handoff", "gpt"),
    ]
    monkeypatch.setattr(
        run_module, "_STAGE_CASES", {"task-creation": lambda: tuple(cases)}
    )

    state = {"active": 0, "peak": {"glm": 0, "gpt": 0}, "lock": threading.Lock()}
    executed: list[str] = []

    def fake_executor(harness_factory, run_label, options, case) -> None:
        with state["lock"]:
            state["active"] += 1
            agent = case.agent
            state["peak"][agent] = max(state["peak"][agent], state["active"])
        time.sleep(0.05)
        executed.append(case.id)
        with state["lock"]:
            state["active"] -= 1

    monkeypatch.setattr(
        run_module, "_STAGE_EXECUTORS", {"task-creation": fake_executor}
    )

    outcomes = run_evaluation(
        label="probe",
        stages=("task-creation",),
        scenarios=None,
        agents=None,
        fresh=False,
        samples=1,
        parallelism={"glm": 2, "gpt": 1},
    )

    assert sorted(outcome.case_id for outcome in outcomes) == ["a", "b", "c"]
    assert all(outcome.status == "ok" for outcome in outcomes)
    assert sorted(executed) == ["a", "b", "c"]


def test_run_execution_reports_skips_and_failures(monkeypatch) -> None:
    from .. import run as run_module
    from ..evaluation.execution import CaseSkipped

    cases = [
        _FakeCase("ok", "tg01-eleventy-archive-handoff", "glm"),
        _FakeCase("skip", "tg02-fastapi-pagination-handoff", "glm"),
        _FakeCase("boom", "tg03-flask-vue-refresh-handoff", "gpt"),
    ]
    monkeypatch.setattr(
        run_module, "_STAGE_CASES", {"task-creation": lambda: tuple(cases)}
    )

    def fake_executor(harness_factory, run_label, options, case) -> None:
        if case.id == "skip":
            raise CaseSkipped("no valid subject")
        if case.id == "boom":
            raise AssertionError("invalid sample")

    monkeypatch.setattr(
        run_module, "_STAGE_EXECUTORS", {"task-creation": fake_executor}
    )

    outcomes = run_evaluation(
        label="probe",
        stages=("task-creation",),
        scenarios=None,
        agents=None,
        fresh=False,
        samples=1,
        parallelism={"glm": 1, "gpt": 1},
    )
    by_id = {outcome.case_id: outcome for outcome in outcomes}
    assert by_id["ok"].status == "ok"
    assert by_id["skip"].status == "skipped"
    assert "no valid subject" in by_id["skip"].detail
    assert by_id["boom"].status == "failed"
    assert "AssertionError" in by_id["boom"].detail
