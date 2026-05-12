from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "benchmarks"
    / "repoqa_prompted"
    / "chained_workflow.py"
)
SPEC = importlib.util.spec_from_file_location("repoqa_prompted_chained_workflow", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load module from {MODULE_PATH}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

build_hierarchical_report = MODULE.build_hierarchical_report
command_report = MODULE.command_report
command_status = MODULE.command_status
latest_stage_run_dir = MODULE.latest_stage_run_dir
load_workflow = MODULE.load_workflow


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _write_config(config_dir: Path) -> None:
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


def _profile(results_root: str) -> dict:
    return {
        "benchmark": "repoqa-prompted",
        "agent_id": "fixture-agent",
        "model": "fixture-model",
        "runtime_backend": "docker",
        "repeat_count": 3,
        "paths": {
            "results_root": results_root,
            "workspace_root": results_root.replace("results", "workspaces"),
        },
    }


def test_latest_stage_run_dir_uses_profile_results_root(tmp_path: Path) -> None:
    workflow_dir = tmp_path / "workflow"
    config_dir = workflow_dir / "config"
    profiles_dir = config_dir / "profiles"
    _write_config(config_dir)
    _write_json(profiles_dir / "nano.json", _profile("results/nano-sample"))
    _write_json(
        workflow_dir / "workflow.json",
        {
            "benchmark": "repoqa-prompted",
            "config_dir": "config",
            "base_manifest": "base.json",
            "stages": {
                "nano": {
                    "profile": "nano",
                    "model": "gpt-5.4-nano",
                    "input_manifest": "base.json",
                }
            },
        },
    )
    first = config_dir / "results" / "nano-sample" / "repoqa-prompted" / "20260101T000000Z"
    second = config_dir / "results" / "nano-sample" / "repoqa-prompted" / "20260102T000000Z"
    _write_json(first / "summary.json", {"run_id": "one"})
    _write_json(second / "summary.json", {"run_id": "two"})

    workflow = load_workflow(workflow_dir / "workflow.json")

    assert latest_stage_run_dir(workflow, "nano") == second


def test_latest_stage_run_dir_respects_artifact_root(tmp_path: Path) -> None:
    workflow_dir = tmp_path / "workflow"
    config_dir = workflow_dir / "config"
    profiles_dir = config_dir / "profiles"
    artifact_root = tmp_path / "artifacts" / "run1"
    _write_config(config_dir)
    _write_json(profiles_dir / "nano.json", _profile("results/nano-sample"))
    _write_json(
        workflow_dir / "workflow.json",
        {
            "benchmark": "repoqa-prompted",
            "config_dir": "config",
            "base_manifest": "base.json",
            "stages": {
                "nano": {
                    "profile": "nano",
                    "model": "gpt-5.4-nano",
                    "input_manifest": "base.json",
                }
            },
        },
    )
    run_dir = artifact_root / "results" / "nano-sample" / "repoqa-prompted" / "20260102T000000Z"
    _write_json(run_dir / "summary.json", {"run_id": "two"})

    workflow = load_workflow(workflow_dir / "workflow.json")

    assert latest_stage_run_dir(workflow, "nano", str(artifact_root)) == run_dir


def test_build_hierarchical_report_assigns_tiers_with_inheritance(tmp_path: Path) -> None:
    workflow_dir = tmp_path / "workflow"
    config_dir = workflow_dir / "config"
    profiles_dir = config_dir / "profiles"
    _write_config(config_dir)
    _write_json(profiles_dir / "nano.json", _profile("results/nano-sample"))
    _write_json(profiles_dir / "mini.json", _profile("results/mini-sample"))
    _write_json(profiles_dir / "full.json", _profile("results/full-sample"))
    _write_json(
        workflow_dir / "base.json",
        {
            "benchmark": "repoqa-prompted",
            "task_count": 4,
            "tasks": [
                {"task_id": "a", "language": "python", "repo_name": "repo-a", "symbol": "sym_a", "path": "a.py"},
                {"task_id": "b", "language": "python", "repo_name": "repo-b", "symbol": "sym_b", "path": "b.py"},
                {"task_id": "c", "language": "python", "repo_name": "repo-c", "symbol": "sym_c", "path": "c.py"},
                {"task_id": "d", "language": "python", "repo_name": "repo-d", "symbol": "sym_d", "path": "d.py"},
            ],
        },
    )
    _write_json(
        workflow_dir / "workflow.json",
        {
            "benchmark": "repoqa-prompted",
            "config_dir": "config",
            "base_manifest": "base.json",
            "stages": {
                "nano": {"profile": "nano", "model": "gpt-5.4-nano", "input_manifest": "base.json"},
                "mini": {"profile": "mini", "model": "gpt-5.4-mini", "input_manifest": "mini.json"},
                "full": {"profile": "full", "model": "gpt-5.4", "input_manifest": "full.json"},
            },
        },
    )
    nano_run = config_dir / "results" / "nano-sample" / "repoqa-prompted" / "20260101T000000Z"
    mini_run = config_dir / "results" / "mini-sample" / "repoqa-prompted" / "20260102T000000Z"
    full_run = config_dir / "results" / "full-sample" / "repoqa-prompted" / "20260103T000000Z"
    _write_json(
        nano_run / "summary.json",
        {
            "logical_task_count": 4,
            "accuracy": 0.25,
            "successful_request_instance_count": 3,
            "error_request_instance_count": 1,
            "has_error_request_instances": True,
            "token_measured_request_instance_count": 3,
            "duration_measured_request_instance_count": 3,
            "tps_measured_request_instance_count": 3,
            "average_input_tokens": 100.0,
            "average_output_tokens": 20.0,
            "average_reasoning_tokens": 0.0,
            "average_duration_seconds": 5.0,
            "average_output_tokens_per_second": 4.0,
        },
    )
    _write_json(
        mini_run / "summary.json",
        {
            "logical_task_count": 3,
            "accuracy": 0.5,
            "successful_request_instance_count": 2,
            "error_request_instance_count": 0,
            "has_error_request_instances": False,
            "token_measured_request_instance_count": 2,
            "duration_measured_request_instance_count": 2,
            "tps_measured_request_instance_count": 2,
            "average_input_tokens": 80.0,
            "average_output_tokens": 25.0,
            "average_reasoning_tokens": 0.0,
            "average_duration_seconds": 4.0,
            "average_output_tokens_per_second": 6.25,
        },
    )
    _write_json(
        full_run / "summary.json",
        {
            "logical_task_count": 2,
            "accuracy": 0.5,
            "successful_request_instance_count": 2,
            "error_request_instance_count": 0,
            "has_error_request_instances": False,
            "token_measured_request_instance_count": 2,
            "duration_measured_request_instance_count": 2,
            "tps_measured_request_instance_count": 2,
            "average_input_tokens": 70.0,
            "average_output_tokens": 30.0,
            "average_reasoning_tokens": 1.0,
            "average_duration_seconds": 3.0,
            "average_output_tokens_per_second": 10.0,
        },
    )
    _write_jsonl(
        nano_run / "task-aggregate.jsonl",
        [
            {"task_id": "a", "repeat_count": 3, "eligible_instance_count": 3, "matched_instance_count": 3, "excluded_missing_target_context_count": 0},
            {"task_id": "b", "repeat_count": 3, "eligible_instance_count": 3, "matched_instance_count": 1, "excluded_missing_target_context_count": 0},
            {"task_id": "c", "repeat_count": 3, "eligible_instance_count": 0, "matched_instance_count": 0, "excluded_missing_target_context_count": 3},
            {"task_id": "d", "repeat_count": 3, "eligible_instance_count": 3, "matched_instance_count": 0, "excluded_missing_target_context_count": 0},
        ],
    )
    _write_jsonl(
        mini_run / "task-aggregate.jsonl",
        [
            {"task_id": "b", "repeat_count": 3, "eligible_instance_count": 3, "matched_instance_count": 3, "excluded_missing_target_context_count": 0},
            {"task_id": "c", "repeat_count": 3, "eligible_instance_count": 3, "matched_instance_count": 2, "excluded_missing_target_context_count": 0},
            {"task_id": "d", "repeat_count": 3, "eligible_instance_count": 3, "matched_instance_count": 0, "excluded_missing_target_context_count": 0},
        ],
    )
    _write_jsonl(
        full_run / "task-aggregate.jsonl",
        [
            {"task_id": "c", "repeat_count": 3, "eligible_instance_count": 3, "matched_instance_count": 3, "excluded_missing_target_context_count": 0},
            {"task_id": "d", "repeat_count": 3, "eligible_instance_count": 3, "matched_instance_count": 1, "excluded_missing_target_context_count": 0},
        ],
    )

    workflow = load_workflow(workflow_dir / "workflow.json")
    report = build_hierarchical_report(workflow)
    rows = {item["task_id"]: item for item in report["tasks"]}
    stage_rows = {item["stage"]: item for item in report["stage_summaries"]}

    assert report["tier_counts"] == {"tier_1": 1, "tier_2": 1, "tier_3": 1, "unsolved": 1}
    assert rows["a"]["tier"] == "tier_1"
    assert rows["b"]["tier"] == "tier_2"
    assert rows["c"]["tier"] == "tier_3"
    assert rows["d"]["tier"] == "unsolved"
    assert rows["a"]["mini_score"] == 1.0
    assert rows["a"]["mini_actually_ran"] is False
    assert rows["a"]["mini_assumed_success"] is True
    assert rows["c"]["full_score"] == 1.0
    assert rows["c"]["full_actually_ran"] is True
    assert rows["c"]["full_assumed_success"] is False
    assert rows["d"]["full_score"] == 1 / 3
    assert report["task_count"] == 4
    assert stage_rows["nano"]["run_task_count"] == 4
    assert stage_rows["nano"]["inherited_task_count"] == 0
    assert stage_rows["nano"]["skipped_due_to_context_task_count"] == 1
    assert abs(stage_rows["nano"]["average_run_task_score"] - (1 / 3)) < 1e-9
    assert stage_rows["nano"]["partially_successful_run_task_count"] == 1
    assert abs(stage_rows["nano"]["average_partially_successful_run_task_score"] - (1 / 3)) < 1e-9
    assert abs(stage_rows["nano"]["effective_accuracy"] - (1 / 3)) < 1e-9
    assert stage_rows["nano"]["successful_request_instance_count"] == 3
    assert stage_rows["nano"]["error_request_instance_count"] == 1
    assert stage_rows["nano"]["has_error_request_instances"] is True
    assert stage_rows["nano"]["average_input_tokens"] == 100.0
    assert stage_rows["nano"]["average_output_tokens"] == 20.0
    assert stage_rows["nano"]["average_reasoning_tokens"] == 0.0
    assert stage_rows["nano"]["average_duration_seconds"] == 5.0
    assert stage_rows["nano"]["average_output_tokens_per_second"] == 4.0
    assert stage_rows["nano"]["fully_solved_task_count"] == 1
    assert stage_rows["nano"]["fully_successful_run_task_count"] == 1
    assert stage_rows["mini"]["inherited_task_count"] == 1
    assert stage_rows["mini"]["run_task_count"] == 3
    assert stage_rows["mini"]["skipped_due_to_context_task_count"] == 0
    assert abs(stage_rows["mini"]["average_run_task_score"] - (5 / 9)) < 1e-9
    assert stage_rows["mini"]["partially_successful_run_task_count"] == 1
    assert abs(stage_rows["mini"]["average_partially_successful_run_task_score"] - (2 / 3)) < 1e-9
    assert abs(stage_rows["mini"]["effective_accuracy"] - (2 / 3)) < 1e-9
    assert stage_rows["mini"]["successful_request_instance_count"] == 2
    assert stage_rows["mini"]["error_request_instance_count"] == 0
    assert stage_rows["mini"]["has_error_request_instances"] is False
    assert stage_rows["mini"]["average_input_tokens"] == 80.0
    assert stage_rows["mini"]["average_output_tokens"] == 25.0
    assert stage_rows["mini"]["average_reasoning_tokens"] == 0.0
    assert stage_rows["mini"]["average_duration_seconds"] == 4.0
    assert stage_rows["mini"]["average_output_tokens_per_second"] == 6.25
    assert stage_rows["mini"]["fully_solved_task_count"] == 2
    assert stage_rows["mini"]["fully_successful_run_task_count"] == 1
    assert abs(stage_rows["full"]["average_run_task_score"] - (2 / 3)) < 1e-9
    assert stage_rows["full"]["partially_successful_run_task_count"] == 1
    assert abs(stage_rows["full"]["average_partially_successful_run_task_score"] - (1 / 3)) < 1e-9
    assert abs(stage_rows["full"]["effective_accuracy"] - (5 / 6)) < 1e-9
    assert stage_rows["full"]["successful_request_instance_count"] == 2
    assert stage_rows["full"]["error_request_instance_count"] == 0
    assert stage_rows["full"]["has_error_request_instances"] is False
    assert stage_rows["full"]["average_input_tokens"] == 70.0
    assert stage_rows["full"]["average_output_tokens"] == 30.0
    assert stage_rows["full"]["average_reasoning_tokens"] == 1.0
    assert stage_rows["full"]["average_duration_seconds"] == 3.0
    assert stage_rows["full"]["average_output_tokens_per_second"] == 10.0
    assert stage_rows["full"]["fully_solved_task_count"] == 3
    assert stage_rows["full"]["fully_successful_run_task_count"] == 1


def test_command_status_reports_manifest_and_latest_run_presence(tmp_path: Path) -> None:
    workflow_dir = tmp_path / "workflow"
    config_dir = workflow_dir / "config"
    profiles_dir = config_dir / "profiles"
    _write_config(config_dir)
    _write_json(profiles_dir / "nano.json", _profile("results/nano-sample"))
    _write_json(workflow_dir / "base.json", {"benchmark": "repoqa-prompted", "task_count": 0, "tasks": []})
    _write_json(
        workflow_dir / "workflow.json",
        {
            "benchmark": "repoqa-prompted",
            "config_dir": "config",
            "base_manifest": "base.json",
            "stages": {
                "nano": {
                    "profile": "nano",
                    "model": "gpt-5.4-nano",
                    "input_manifest": "base.json",
                    "next_manifest": "next.json",
                }
            },
        },
    )
    run_dir = config_dir / "results" / "nano-sample" / "repoqa-prompted" / "20260101T000000Z"
    _write_json(run_dir / "summary.json", {"run_id": "one"})

    workflow = load_workflow(workflow_dir / "workflow.json")
    status = command_status(workflow)

    assert status["base_manifest_exists"] is True
    assert status["stages"][0]["input_manifest_exists"] is True
    assert status["stages"][0]["next_manifest_exists"] is False
    assert status["stages"][0]["latest_run_dir"] == str(run_dir)


def test_command_report_writes_outputs_under_artifact_root(tmp_path: Path) -> None:
    workflow_dir = tmp_path / "workflow"
    config_dir = workflow_dir / "config"
    profiles_dir = config_dir / "profiles"
    artifact_root = tmp_path / "artifacts" / "run1"
    _write_config(config_dir)
    _write_json(profiles_dir / "nano.json", _profile("results/nano-sample"))
    _write_json(
        workflow_dir / "base.json",
        {
            "benchmark": "repoqa-prompted",
            "task_count": 1,
            "tasks": [
                {"task_id": "a", "language": "python", "repo_name": "repo-a", "symbol": "sym_a", "path": "a.py"},
            ],
        },
    )
    _write_json(
        workflow_dir / "workflow.json",
        {
            "benchmark": "repoqa-prompted",
            "config_dir": "config",
            "base_manifest": "base.json",
            "report": {"output_json": "config/reports/chained-summary.json"},
            "stages": {
                "nano": {"profile": "nano", "model": "gpt-5.4-nano", "input_manifest": "base.json"},
            },
        },
    )
    nano_run = artifact_root / "results" / "nano-sample" / "repoqa-prompted" / "20260101T000000Z"
    _write_json(nano_run / "summary.json", {"repeat_count": 3, "model_request_task_count": 1})
    _write_jsonl(
        nano_run / "task-aggregate.jsonl",
        [
            {"task_id": "a", "repeat_count": 3, "eligible_instance_count": 3, "matched_instance_count": 3, "excluded_missing_target_context_count": 0},
        ],
    )

    workflow = load_workflow(workflow_dir / "workflow.json")
    report = command_report(workflow, str(artifact_root))

    output_json = artifact_root / "reports" / "chained-summary.json"
    assert report["output_json"] == str(output_json)
    assert Path(report["output_tasks_csv"]) == artifact_root / "reports" / "chained-summary-tasks.csv"
    assert Path(report["output_stages_csv"]) == artifact_root / "reports" / "chained-summary-stages.csv"
    assert output_json.is_file()