from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from agent_evaluations.repeated_runs import (
    aggregate_results_by_task_id,
    expand_task_payloads_with_repeats,
    load_existing_results_for_manifest,
    select_result_rows_for_manifest,
)


REPOQA_LOGIC_MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "benchmarks"
    / "repoqa_prompted"
    / "logic.py"
)
REPOQA_WORKFLOW_MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "benchmarks"
    / "repoqa_prompted"
    / "chained_workflow.py"
)


def _load_module(module_path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LOGIC = _load_module(REPOQA_LOGIC_MODULE_PATH, "repoqa_prompted_logic_for_resume_tests")
WORKFLOW = _load_module(REPOQA_WORKFLOW_MODULE_PATH, "repoqa_prompted_workflow_for_resume_tests")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _logical_task(task_id: str) -> dict:
    return {
        "task_id": task_id,
        "language": "python",
        "repo_name": f"repo-{task_id}",
        "path": f"{task_id}.py",
        "symbol": f"sym_{task_id}",
    }


def _result_row(task_payload: dict, *, matched: bool, imported: bool = False) -> dict:
    score_value = 1.0 if matched else 0.0
    return {
        "task": {
            key: value
            for key, value in task_payload.items()
            if key not in {"planned_start_at", "repeat_count", "repeat_index", "task_instance_id"}
        },
        "task_instance_id": task_payload["task_instance_id"],
        "repeat_index": task_payload["repeat_index"],
        "repeat_count": task_payload["repeat_count"],
        "state": "completed",
        "outcome": "matched" if matched else "mismatched",
        "eligible_for_accuracy": True,
        "failure_category": None,
        "error": None,
        "score": {
            "matched": matched,
            "path_match": matched,
            "symbol_match": matched,
            "code_match": matched,
            "comparison_method": None,
            "code_comparison": None,
            "score": score_value,
        },
        "parsed_answer": None,
        "parse_error": None,
        "final_assistant_text": "",
        "tool_call_count": 0,
        "effective_tool_schema_count": 0,
        "usage": None,
        "cost": 0.25,
        "cost_formatted": "$0.250000",
        "provider_call_count": 1,
        "target_in_context": True,
        "context_truncated": False,
        "meta": {},
        "actual_start_at": "2025-12-31T23:59:55Z",
        "finished_at": "2026-01-01T00:00:00Z",
        "imported_result": imported,
    }


def _minimal_env(tmp_path: Path):
    return SimpleNamespace(
        paths=SimpleNamespace(
            results_root=tmp_path / "results",
            config_dir=tmp_path / "config",
        )
    )


def _workflow_profile(results_root: str) -> dict:
    return {
        "benchmark": "repoqa-prompted",
        "agent_id": "fixture-agent",
        "model": "fixture-model",
        "runtime_backend": "host",
        "repeat_count": 3,
        "max_task_restarts": 0,
        "paths": {
            "results_root": results_root,
            "workspace_root": results_root.replace("results", "workspaces"),
        },
    }


def _workflow_config(config_dir: Path, manifest_name: str) -> dict:
    return {
        "benchmark": "repoqa-prompted",
        "config_dir": str(config_dir),
        "base_manifest": str(config_dir.parent / manifest_name),
        "stages": {
            "nano": {
                "profile": "nano",
                "model": "gpt-5.4-nano",
                "input_manifest": str(config_dir.parent / manifest_name),
            }
        },
    }


def test_select_result_rows_for_manifest_reuses_overlapping_repeats_only() -> None:
    logical_tasks = [_logical_task("task-a")]
    source_tasks = expand_task_payloads_with_repeats(logical_tasks, repeat_count=3)
    destination_tasks = expand_task_payloads_with_repeats(logical_tasks, repeat_count=5)
    source_rows = [_result_row(task, matched=True) for task in source_tasks]

    selected = select_result_rows_for_manifest(
        source_rows,
        destination_tasks,
        require_all_known=False,
    )

    assert [row["task_instance_id"] for row in selected] == ["task-a#r1", "task-a#r2", "task-a#r3"]


def test_load_existing_results_rejects_task_payload_mismatch(tmp_path: Path) -> None:
    tasks = expand_task_payloads_with_repeats([_logical_task("task-a")], repeat_count=1)
    bad_row = _result_row(tasks[0], matched=True)
    bad_row["task"]["path"] = "other.py"
    results_path = tmp_path / "results.jsonl"
    _write_jsonl(results_path, [bad_row])

    with pytest.raises(ValueError, match="task payload mismatch"):
        load_existing_results_for_manifest(results_path, tasks)


def test_aggregate_results_excludes_failed_requests_from_success_rate() -> None:
    tasks = expand_task_payloads_with_repeats([_logical_task("task-a")], repeat_count=2)
    successful = _result_row(tasks[0], matched=True)
    failed = _result_row(tasks[1], matched=False)
    failed["state"] = "failed_before_turn_completed"
    failed["outcome"] = "failed_before_turn_completed"
    failed["eligible_for_accuracy"] = False
    failed["failure_category"] = "request_failure"
    failed["error"] = "RuntimeError: quota"

    aggregate = aggregate_results_by_task_id([successful, failed])[0]

    assert aggregate["completed_instance_count"] == 2
    assert aggregate["eligible_instance_count"] == 1
    assert aggregate["matched_instance_count"] == 1
    assert aggregate["success_rate"] == 1.0


def test_run_repoqa_prompted_benchmark_skips_preexisting_instances(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run_root = tmp_path / "results" / "repoqa-prompted" / "20260101T000000Z"
    run_manifest_path = run_root / "run-manifest.json"
    tasks = expand_task_payloads_with_repeats(
        [_logical_task("task-a"), _logical_task("task-b"), _logical_task("task-c")],
        repeat_count=1,
    )
    for task in tasks:
        task["planned_start_at"] = "2026-01-01T00:00:00Z"
    run_manifest = {
        "run_id": "20260101T000000Z",
        "benchmark": "repoqa-prompted",
        "release": "fixture-release",
        "language": "python",
        "languages": ["python"],
        "agent_id": "fixture-agent",
        "repeat_count": 1,
        "runtime_backend": "host",
        "max_task_restarts": 0,
        "schedule_policy": {
            "timezone": "UTC",
            "window_minutes": 1,
            "tasks_per_window": 10,
            "max_parallel_tasks": 1,
            "randomize_task_starts": False,
            "random_seed": 0,
        },
        "tasks": tasks,
    }
    _write_json(run_manifest_path, run_manifest)
    _write_jsonl(
        run_root / "results.jsonl",
        [
            _result_row(tasks[0], matched=True),
            _result_row(tasks[1], matched=False),
        ],
    )

    called_instance_ids: list[str] = []

    def fake_run_task(*args, **kwargs):
        task_payload = kwargs["task_payload"]
        called_instance_ids.append(task_payload["task_instance_id"])
        return _result_row(task_payload, matched=True)

    monkeypatch.setattr(LOGIC, "run_repoqa_prompted_task_with_restarts", fake_run_task)

    returned_path = LOGIC.run_repoqa_prompted_benchmark(
        _minimal_env(tmp_path),
        benchmark_manifest={"tasks": []},
        agent_id="fixture-agent",
        profile_name="fixture-profile",
        profile_payload={},
        schedule_overrides={},
        model_override=None,
        max_task_restarts=0,
        repeat_count=1,
        runtime_backend="host",
        docker_runtime=None,
        resume_run_manifest_path=run_manifest_path,
    )

    assert returned_path == run_manifest_path
    assert called_instance_ids == ["task-c"]

    result_rows = [
        json.loads(line)
        for line in (run_root / "results.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(result_rows) == 3
    summary = json.loads((run_root / "summary.json").read_text(encoding="utf-8"))
    assert summary["completed_task_count"] == 3
    assert summary["preexisting_result_count"] == 2
    assert summary["new_result_count"] == 1


def test_run_repoqa_prompted_summary_includes_error_duration_and_token_metrics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_root = tmp_path / "results" / "repoqa-prompted" / "20260102T000000Z"
    run_manifest_path = run_root / "run-manifest.json"
    tasks = expand_task_payloads_with_repeats(
        [_logical_task("task-a"), _logical_task("task-b"), _logical_task("task-c")],
        repeat_count=1,
    )
    for task in tasks:
        task["planned_start_at"] = "2026-01-01T00:00:00Z"
    run_manifest = {
        "run_id": "20260102T000000Z",
        "benchmark": "repoqa-prompted",
        "release": "fixture-release",
        "language": "python",
        "languages": ["python"],
        "agent_id": "fixture-agent",
        "repeat_count": 1,
        "runtime_backend": "host",
        "max_task_restarts": 0,
        "schedule_policy": {
            "timezone": "UTC",
            "window_minutes": 1,
            "tasks_per_window": 10,
            "max_parallel_tasks": 1,
            "randomize_task_starts": False,
            "random_seed": 0,
        },
        "tasks": tasks,
    }
    _write_json(run_manifest_path, run_manifest)
    success_row = _result_row(tasks[0], matched=True)
    success_row["usage"] = {
        "usage": {
            "input_tokens": 10,
            "output_tokens": 20,
            "output_tokens_details": {"reasoning_tokens": 2},
        }
    }
    success_row["actual_start_at"] = "2026-01-01T00:00:00Z"
    success_row["finished_at"] = "2026-01-01T00:00:05Z"

    error_row = {
        **_result_row(tasks[1], matched=False),
        "state": "failed_before_turn_completed",
        "outcome": "failed_before_turn_completed",
        "usage": None,
        "cost": None,
        "actual_start_at": "2026-01-01T00:00:10Z",
        "finished_at": "2026-01-01T00:00:12Z",
    }
    _write_jsonl(run_root / "results.jsonl", [success_row, error_row])

    def fake_run_task(*args, **kwargs):
        task_payload = kwargs["task_payload"]
        row = _result_row(task_payload, matched=False)
        row["usage"] = {
            "usage": {
                "input_tokens": 30,
                "output_tokens": 10,
                "output_tokens_details": {"reasoning_tokens": 0},
            }
        }
        row["actual_start_at"] = "2026-01-01T00:00:20Z"
        row["finished_at"] = "2026-01-01T00:00:22Z"
        return row

    monkeypatch.setattr(LOGIC, "run_repoqa_prompted_task_with_restarts", fake_run_task)

    LOGIC.run_repoqa_prompted_benchmark(
        _minimal_env(tmp_path),
        benchmark_manifest={"tasks": []},
        agent_id="fixture-agent",
        profile_name="fixture-profile",
        profile_payload={},
        schedule_overrides={},
        model_override=None,
        max_task_restarts=0,
        repeat_count=1,
        runtime_backend="host",
        docker_runtime=None,
        resume_run_manifest_path=run_manifest_path,
    )

    summary = json.loads((run_root / "summary.json").read_text(encoding="utf-8"))
    assert summary["successful_request_instance_count"] == 2
    assert summary["error_request_instance_count"] == 1
    assert summary["has_error_request_instances"] is True
    assert summary["token_measured_request_instance_count"] == 2
    assert summary["duration_measured_request_instance_count"] == 2
    assert summary["tps_measured_request_instance_count"] == 2
    assert summary["average_input_tokens"] == 20.0
    assert summary["average_output_tokens"] == 15.0
    assert summary["average_reasoning_tokens"] == 1.0
    assert summary["average_duration_seconds"] == 3.5
    assert summary["average_output_tokens_per_second"] == 4.5


def test_command_seed_run_copies_overlapping_results_into_new_run(tmp_path: Path) -> None:
    workflow_dir = tmp_path / "workflow"
    config_dir = workflow_dir / "config"
    profiles_dir = config_dir / "profiles"
    config_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        config_dir / "config.json",
        {
            "plugins": [],
            "providers": {},
            "agents": {"fixture-agent": {"provider": "fixture"}},
            "agentic_evaluations": {
                "cache_root": str(config_dir / "cache"),
                "results_root": str(config_dir / "results"),
                "manifests_root": str(config_dir / "manifests"),
                "workspace_root": str(config_dir / "workspaces"),
                "profiles_root": str(config_dir / "profiles"),
            },
        },
    )
    _write_json(profiles_dir / "nano.json", _workflow_profile("results/nano-sample"))
    manifest_path = workflow_dir / "manifest.json"
    logical_tasks = [_logical_task("task-a"), _logical_task("task-b"), _logical_task("task-c")]
    _write_json(
        manifest_path,
        {
            "benchmark": "repoqa-prompted",
            "release": "fixture-release",
            "language": "python",
            "languages": ["python"],
            "seed": 1,
            "limit": 3,
            "task_count": 3,
            "tasks": logical_tasks,
        },
    )
    _write_json(workflow_dir / "workflow.json", _workflow_config(config_dir, "manifest.json"))

    source_run_dir = workflow_dir / "source-run"
    source_tasks = expand_task_payloads_with_repeats(logical_tasks[:2], repeat_count=3)
    _write_jsonl(
        source_run_dir / "results.jsonl",
        [_result_row(task, matched=True) for task in source_tasks],
    )

    workflow = WORKFLOW.load_workflow(workflow_dir / "workflow.json")
    seeded = WORKFLOW.command_seed_run(
        workflow,
        "nano",
        source_run_dir=source_run_dir,
        manifest_path=str(manifest_path),
    )

    seeded_results = [
        json.loads(line)
        for line in Path(seeded["results_jsonl"]).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert seeded["imported_instance_count"] == 6
    assert seeded["imported_task_count"] == 2
    assert len(seeded_results) == 6
    assert all(row["imported_result"] is True for row in seeded_results)
    assert all(row["import_mode"] == "actual_results" for row in seeded_results)
    assert all(row["source_run_dir"] == str(source_run_dir) for row in seeded_results)