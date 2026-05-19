from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import subprocess
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from agent_evaluations.cli_helpers import load_run_environment, resolve_run_value, resolve_runtime_backend
from agent_evaluations.container_backend import resolve_docker_runtime_config
from agent_evaluations.profiles import load_run_profile
from agent_evaluations.repeated_runs import select_result_rows_for_manifest
from agent_evaluations.utils import isoformat_utc, write_json_atomic, write_jsonl_atomic


DEFAULT_WORKFLOW_CONFIG = Path(__file__).with_name("chained_sample20_workflow.json")


def _load_json_object(path: Path) -> Dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return loaded


def _load_jsonl_objects(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped:
            continue
        loaded = json.loads(stripped)
        if not isinstance(loaded, dict):
            raise ValueError(f"Expected JSON object in {path} line {line_number}")
        rows.append(loaded)
    return rows


def _resolve_path(base_dir: Path, raw_path: str) -> Path:
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute():
        return candidate
    return (base_dir / candidate).resolve()


def load_workflow(path: Path) -> Dict[str, Any]:
    payload = _load_json_object(path)
    workflow_dir = path.parent.resolve()
    payload["_workflow_path"] = str(path.resolve())
    payload["_workflow_dir"] = str(workflow_dir)
    payload["config_dir"] = str(_resolve_path(workflow_dir, str(payload["config_dir"])))
    payload["base_manifest"] = str(_resolve_path(workflow_dir, str(payload["base_manifest"])))
    generation = payload.get("base_manifest_generation")
    if isinstance(generation, dict) and isinstance(generation.get("output_manifest"), str):
        generation["output_manifest"] = str(_resolve_path(workflow_dir, generation["output_manifest"]))
    stages = payload.get("stages")
    if not isinstance(stages, dict):
        raise ValueError("Workflow config must contain a stages object")
    for stage in stages.values():
        if not isinstance(stage, dict):
            raise ValueError("Workflow stages must be objects")
        if isinstance(stage.get("input_manifest"), str):
            stage["input_manifest"] = str(_resolve_path(workflow_dir, stage["input_manifest"]))
        if isinstance(stage.get("next_manifest"), str):
            stage["next_manifest"] = str(_resolve_path(workflow_dir, stage["next_manifest"]))
    report = payload.get("report")
    if isinstance(report, dict) and isinstance(report.get("output_json"), str):
        report["output_json"] = str(_resolve_path(workflow_dir, report["output_json"]))
    return payload


def _stage_names(workflow: Mapping[str, Any]) -> List[str]:
    stages = workflow.get("stages")
    if not isinstance(stages, Mapping):
        raise ValueError("Workflow config missing stages")
    preferred = ["nano", "mini", "full"]
    ordered = [name for name in preferred if name in stages]
    ordered.extend(name for name in stages.keys() if name not in ordered)
    return ordered


def _stage_payload(workflow: Mapping[str, Any], stage_name: str) -> Dict[str, Any]:
    stages = workflow.get("stages")
    if not isinstance(stages, Mapping):
        raise ValueError("Workflow config missing stages")
    raw = stages.get(stage_name)
    if not isinstance(raw, dict):
        raise KeyError(f"Unknown stage {stage_name!r}")
    return raw


def _load_repoqa_logic_module() -> Any:
    import importlib.util
    import sys

    module_name = "agent_evaluations_external_benchmark_repoqa_prompted_logic_workflow"
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached
    module_path = Path(__file__).with_name("logic.py")
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load RepoQA prompted logic from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _config_dir(workflow: Mapping[str, Any]) -> Path:
    raw = workflow.get("config_dir")
    if not isinstance(raw, str):
        raise ValueError("Workflow config missing config_dir")
    return Path(raw)


def _resolve_artifact_root(artifact_root: str | None) -> Optional[Path]:
    if not isinstance(artifact_root, str) or not artifact_root.strip():
        return None
    return Path(artifact_root).expanduser().resolve()


def _latest_run_dir(results_root: Path, benchmark: str) -> Optional[Path]:
    benchmark_root = results_root / benchmark
    if not benchmark_root.is_dir():
        return None
    candidates = [
        child for child in benchmark_root.iterdir()
        if child.is_dir() and (child / "summary.json").is_file()
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda path: path.name)[-1]


def _load_stage_environment_and_profile(
    workflow: Mapping[str, Any],
    stage_name: str,
    artifact_root: str | None = None,
) -> Tuple[Any, Dict[str, Any]]:
    config_dir = _config_dir(workflow)
    stage = _stage_payload(workflow, stage_name)
    profile_name = stage.get("profile")
    if not isinstance(profile_name, str) or not profile_name:
        raise ValueError(f"Stage {stage_name!r} missing profile")
    return load_run_environment(
        config_dir,
        profile_name,
        artifact_root=artifact_root,
    )


def latest_stage_run_dir(
    workflow: Mapping[str, Any],
    stage_name: str,
    artifact_root: str | None = None,
) -> Optional[Path]:
    benchmark = workflow.get("benchmark")
    if not isinstance(benchmark, str) or not benchmark:
        raise ValueError("Workflow config missing benchmark")
    env, _profile_payload = _load_stage_environment_and_profile(workflow, stage_name, artifact_root)
    return _latest_run_dir(env.paths.results_root, benchmark)


def _report_output_path(workflow: Mapping[str, Any], artifact_root: str | None) -> Optional[Path]:
    report_cfg = workflow.get("report")
    if not isinstance(report_cfg, Mapping) or not isinstance(report_cfg.get("output_json"), str):
        return None
    output_path = Path(str(report_cfg["output_json"]))
    resolved_artifact_root = _resolve_artifact_root(artifact_root)
    if resolved_artifact_root is None:
        return output_path
    parts = list(output_path.parts)
    if "reports" in parts:
        suffix = Path(*parts[parts.index("reports") + 1 :])
    else:
        suffix = Path(output_path.name)
    return resolved_artifact_root / "reports" / suffix


def build_filtered_manifest_from_aggregate(
    input_manifest_path: Path,
    aggregate_path: Path,
    output_manifest_path: Path,
) -> Dict[str, Any]:
    from agent_evaluations_external_benchmark_repoqa_prompted_filter import (  # type: ignore
        build_filtered_manifest,
        collect_fully_solved_task_ids,
    )

    input_manifest = _load_json_object(input_manifest_path)
    aggregates = _load_jsonl_objects(aggregate_path)
    excluded_task_ids = collect_fully_solved_task_ids(aggregates)
    filtered_manifest = build_filtered_manifest(
        input_manifest,
        excluded_task_ids=excluded_task_ids,
    )
    output_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    output_manifest_path.write_text(
        json.dumps(filtered_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "input_manifest": str(input_manifest_path),
        "task_aggregate_jsonl": str(aggregate_path),
        "output_manifest": str(output_manifest_path),
        "input_task_count": len(input_manifest.get("tasks") or []),
        "excluded_fully_solved_task_count": len(excluded_task_ids),
        "output_task_count": len(filtered_manifest.get("tasks") or []),
    }


def _is_fully_solved(aggregate: Mapping[str, Any]) -> bool:
    return (
        int(aggregate.get("repeat_count") or 1) == int(aggregate.get("eligible_instance_count") or 0)
        and int(aggregate.get("repeat_count") or 1) == int(aggregate.get("matched_instance_count") or 0)
        and int(aggregate.get("excluded_missing_target_context_count") or 0) == 0
    )


def _task_rows_from_manifest(manifest_path: Path) -> List[Dict[str, Any]]:
    manifest = _load_json_object(manifest_path)
    tasks = manifest.get("tasks")
    if not isinstance(tasks, list):
        raise ValueError(f"Manifest {manifest_path} must contain tasks")
    return [task for task in tasks if isinstance(task, dict)]


def _aggregate_map(aggregate_path: Optional[Path]) -> Dict[str, Dict[str, Any]]:
    if aggregate_path is None or not aggregate_path.is_file():
        return {}
    rows = _load_jsonl_objects(aggregate_path)
    return {
        str(item["task_id"]): item
        for item in rows
        if isinstance(item, dict) and isinstance(item.get("task_id"), str)
    }


def _stage_report_entry(
    stage_name: str,
    stage_payload: Mapping[str, Any],
    aggregate: Optional[Mapping[str, Any]],
    run_dir: Optional[Path],
) -> Dict[str, Any]:
    if aggregate is None:
        return {
            "stage": stage_name,
            "model": stage_payload.get("model"),
            "run_dir": str(run_dir) if run_dir is not None else None,
            "state": "missing",
        }
    return {
        "stage": stage_name,
        "model": stage_payload.get("model"),
        "run_dir": str(run_dir) if run_dir is not None else None,
        "state": "complete",
        "repeat_count": aggregate.get("repeat_count"),
        "actual_run_instance_count": aggregate.get("model_request_task_count"),
        "cost_per_run_instance": aggregate.get("average_cost_per_costed_task"),
        "total_cost": aggregate.get("total_cost"),
        "successful_request_instance_count": aggregate.get("successful_request_instance_count"),
        "error_request_instance_count": aggregate.get("error_request_instance_count"),
        "has_error_request_instances": aggregate.get("has_error_request_instances"),
        "token_measured_request_instance_count": aggregate.get("token_measured_request_instance_count"),
        "duration_measured_request_instance_count": aggregate.get("duration_measured_request_instance_count"),
        "tps_measured_request_instance_count": aggregate.get("tps_measured_request_instance_count"),
        "average_input_tokens": aggregate.get("average_input_tokens"),
        "average_output_tokens": aggregate.get("average_output_tokens"),
        "average_reasoning_tokens": aggregate.get("average_reasoning_tokens"),
        "average_duration_seconds": aggregate.get("average_duration_seconds"),
        "average_output_tokens_per_second": aggregate.get("average_output_tokens_per_second"),
    }


def _stage_actual_score(aggregate: Optional[Mapping[str, Any]]) -> Optional[float]:
    if not isinstance(aggregate, Mapping):
        return None
    eligible = int(aggregate.get("eligible_instance_count") or 0)
    matched = int(aggregate.get("matched_instance_count") or 0)
    if eligible <= 0:
        return None
    return matched / eligible


def _write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fieldnames})


def build_hierarchical_report(
    workflow: Mapping[str, Any],
    artifact_root: str | None = None,
) -> Dict[str, Any]:
    stage_names = _stage_names(workflow)
    base_manifest_path = Path(str(workflow["base_manifest"]))
    base_tasks = _task_rows_from_manifest(base_manifest_path)
    base_task_count = len(base_tasks)
    run_dirs = {stage: latest_stage_run_dir(workflow, stage, artifact_root) for stage in stage_names}
    summary_payloads = {}
    aggregate_maps = {}
    for stage_name in stage_names:
        run_dir = run_dirs[stage_name]
        summary_payloads[stage_name] = (
            _load_json_object(run_dir / "summary.json") if run_dir is not None and (run_dir / "summary.json").is_file() else None
        )
        aggregate_maps[stage_name] = _aggregate_map(run_dir / "task-aggregate.jsonl" if run_dir is not None else None)

    task_rows: List[Dict[str, Any]] = []
    tier_counts = {
        "tier_1": 0,
        "tier_2": 0,
        "tier_3": 0,
        "unsolved": 0,
    }
    for task in base_tasks:
        task_id = str(task["task_id"])
        nano_item = aggregate_maps.get("nano", {}).get(task_id)
        mini_item = aggregate_maps.get("mini", {}).get(task_id)
        full_item = aggregate_maps.get("full", {}).get(task_id)

        nano_solved = _is_fully_solved(nano_item) if isinstance(nano_item, Mapping) else False
        mini_solved = nano_solved or (_is_fully_solved(mini_item) if isinstance(mini_item, Mapping) else False)
        full_solved = mini_solved or (_is_fully_solved(full_item) if isinstance(full_item, Mapping) else False)

        nano_actually_ran = isinstance(nano_item, Mapping)
        mini_actually_ran = isinstance(mini_item, Mapping)
        full_actually_ran = isinstance(full_item, Mapping)
        mini_assumed_success = (not mini_actually_ran) and nano_solved
        full_assumed_success = (not full_actually_ran) and mini_solved

        if nano_solved:
            tier = "tier_1"
        elif mini_solved:
            tier = "tier_2"
        elif full_solved:
            tier = "tier_3"
        else:
            tier = "unsolved"
        tier_counts[tier] += 1

        nano_actual_score = _stage_actual_score(nano_item)
        mini_actual_score = _stage_actual_score(mini_item)
        full_actual_score = _stage_actual_score(full_item)
        nano_score = nano_actual_score
        mini_score = 1.0 if mini_assumed_success else mini_actual_score
        full_score = 1.0 if full_assumed_success else full_actual_score
        nano_skipped_due_to_context = bool(
            isinstance(nano_item, Mapping)
            and int(nano_item.get("excluded_missing_target_context_count") or 0) > 0
        )
        mini_skipped_due_to_context = bool(
            isinstance(mini_item, Mapping)
            and int(mini_item.get("excluded_missing_target_context_count") or 0) > 0
        )
        full_skipped_due_to_context = bool(
            isinstance(full_item, Mapping)
            and int(full_item.get("excluded_missing_target_context_count") or 0) > 0
        )

        task_rows.append(
            {
                "task_id": task_id,
                "language": task.get("language"),
                "repo": task.get("repo_name"),
                "symbol": task.get("symbol"),
                "path": task.get("path"),
                "nano_score": nano_score,
                "nano_actually_ran": nano_actually_ran,
                "nano_skipped_due_to_context": nano_skipped_due_to_context,
                "mini_score": mini_score,
                "mini_actually_ran": mini_actually_ran,
                "mini_skipped_due_to_context": mini_skipped_due_to_context,
                "mini_assumed_success": mini_assumed_success,
                "full_score": full_score,
                "full_actually_ran": full_actually_ran,
                "full_skipped_due_to_context": full_skipped_due_to_context,
                "full_assumed_success": full_assumed_success,
                "tier": tier,
            }
        )

    stage_summaries = [
        _stage_report_entry(
            stage_name,
            _stage_payload(workflow, stage_name),
            summary_payloads.get(stage_name),
            run_dirs.get(stage_name),
        )
        for stage_name in stage_names
    ]
    cumulative_solved_task_ids: set[str] = set()
    for stage_summary in stage_summaries:
        stage_name = str(stage_summary["stage"])
        stage_rows = [row for row in task_rows if row.get(f"{stage_name}_actually_ran")]
        actually_ran_task_count = len(stage_rows)
        assumed_success_task_count = sum(
            1 for row in task_rows if row.get(f"{stage_name}_assumed_success") is True
        )
        actual_fully_solved_task_count = sum(
            1
            for row in stage_rows
            if row.get(f"{stage_name}_actually_ran") and (
                row["tier"] == "tier_1" if stage_name == "nano"
                else row["tier"] == "tier_2" if stage_name == "mini"
                else row["tier"] == "tier_3"
            )
        )
        actual_average_task_score_values = [
            float(row[f"{stage_name}_score"])
            for row in stage_rows
            if isinstance(row.get(f"{stage_name}_score"), (int, float))
        ]
        actual_average_task_score = (
            sum(actual_average_task_score_values) / len(actual_average_task_score_values)
            if actual_average_task_score_values
            else None
        )
        partially_successful_task_scores = [
            float(row[f"{stage_name}_score"])
            for row in stage_rows
            if isinstance(row.get(f"{stage_name}_score"), (int, float))
            and 0.0 < float(row[f"{stage_name}_score"]) < 1.0
        ]
        effective_task_score_values = [
            float(row[f"{stage_name}_score"])
            for row in task_rows
            if isinstance(row.get(f"{stage_name}_score"), (int, float))
        ]
        effective_average_task_score = (
            sum(effective_task_score_values) / base_task_count if base_task_count else None
        )
        skipped_due_to_context_task_count = sum(
            1 for row in stage_rows if row.get(f"{stage_name}_skipped_due_to_context") is True
        )
        stage_fully_solved_rows = [
            row for row in task_rows
            if (
                stage_name == "nano" and row["tier"] == "tier_1"
            ) or (
                stage_name == "mini" and row["tier"] in {"tier_1", "tier_2"}
            ) or (
                stage_name == "full" and row["tier"] in {"tier_1", "tier_2", "tier_3"}
            )
        ]
        cumulative_solved_task_ids.update({str(row["task_id"]) for row in stage_fully_solved_rows})
        stage_summary["inherited_task_count"] = assumed_success_task_count
        stage_summary["run_task_count"] = actually_ran_task_count
        stage_summary["skipped_due_to_context_task_count"] = skipped_due_to_context_task_count
        stage_summary["average_run_task_score"] = actual_average_task_score
        stage_summary["partially_successful_run_task_count"] = len(partially_successful_task_scores)
        stage_summary["average_partially_successful_run_task_score"] = (
            sum(partially_successful_task_scores) / len(partially_successful_task_scores)
            if partially_successful_task_scores
            else None
        )
        stage_summary["effective_accuracy"] = effective_average_task_score
        stage_summary["fully_solved_task_count"] = len(cumulative_solved_task_ids)
        stage_summary["fully_successful_run_task_count"] = actual_fully_solved_task_count

    return {
        "workflow_config": workflow.get("_workflow_path"),
        "artifact_root": str(_resolve_artifact_root(artifact_root)) if _resolve_artifact_root(artifact_root) is not None else None,
        "base_manifest": str(base_manifest_path),
        "task_count": base_task_count,
        "stage_summaries": stage_summaries,
        "tier_counts": tier_counts,
        "tasks": task_rows,
    }


def _import_filter_module() -> None:
    import importlib.util
    import sys

    module_name = "agent_evaluations_external_benchmark_repoqa_prompted_filter"
    if module_name in sys.modules:
        return
    module_path = Path(__file__).with_name("filter_manifest_by_success.py")
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load filter module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)


def command_prepare_base_manifest(workflow: Mapping[str, Any]) -> Dict[str, Any]:
    generation = workflow.get("base_manifest_generation")
    if not isinstance(generation, Mapping):
        raise ValueError("Workflow config missing base_manifest_generation")
    output_manifest = Path(str(generation["output_manifest"]))
    command = [
        "agent-evaluations",
        "manifest",
        str(workflow["benchmark"]),
        "--config-dir",
        str(workflow["config_dir"]),
        "--language",
        str(generation["language"]),
        "--limit",
        str(generation["limit"]),
        "--seed",
        str(generation["seed"]),
        "--output-path",
        str(output_manifest),
    ]
    completed = subprocess.run(command, check=True, text=True, capture_output=True)
    return {
        "command": command,
        "stdout": completed.stdout.strip(),
    }


def command_run_stage(workflow: Mapping[str, Any], stage_name: str) -> Dict[str, Any]:
    return command_run_stage_with_overrides(
        workflow,
        stage_name,
        manifest_path=None,
        run_manifest_path=None,
        artifact_root=None,
    )


def command_run_stage_with_overrides(
    workflow: Mapping[str, Any],
    stage_name: str,
    *,
    manifest_path: Optional[str],
    run_manifest_path: Optional[str],
    artifact_root: str | None,
) -> Dict[str, Any]:
    stage = _stage_payload(workflow, stage_name)
    resolved_manifest_path = manifest_path or str(stage["input_manifest"])
    command = [
        "agent-evaluations",
        "run",
        str(workflow["benchmark"]),
        "--config-dir",
        str(workflow["config_dir"]),
        "--profile",
        str(stage["profile"]),
        "--manifest-path",
        resolved_manifest_path,
    ]
    resolved_artifact_root = _resolve_artifact_root(artifact_root)
    if resolved_artifact_root is not None:
        command.extend(["--artifact-root", str(resolved_artifact_root)])
    if isinstance(run_manifest_path, str) and run_manifest_path:
        command.extend(["--run-manifest", run_manifest_path])
    completed = subprocess.run(command, check=True, text=True, capture_output=True)
    return {
        "stage": stage_name,
        "command": command,
        "stdout": completed.stdout.strip(),
    }


def command_refilter_next(
    workflow: Mapping[str, Any],
    stage_name: str,
    artifact_root: str | None = None,
) -> Dict[str, Any]:
    _import_filter_module()
    stage = _stage_payload(workflow, stage_name)
    next_manifest = stage.get("next_manifest")
    if not isinstance(next_manifest, str) or not next_manifest:
        raise ValueError(f"Stage {stage_name!r} does not define next_manifest")
    run_dir = latest_stage_run_dir(workflow, stage_name, artifact_root)
    if run_dir is None:
        raise FileNotFoundError(f"No completed run found for stage {stage_name!r}")
    aggregate_path = run_dir / "task-aggregate.jsonl"
    if not aggregate_path.is_file():
        raise FileNotFoundError(f"Missing aggregate file for stage {stage_name!r}: {aggregate_path}")
    return build_filtered_manifest_from_aggregate(
        Path(str(stage["input_manifest"])),
        aggregate_path,
        Path(next_manifest),
    )


def command_status(workflow: Mapping[str, Any], artifact_root: str | None = None) -> Dict[str, Any]:
    statuses = []
    for stage_name in _stage_names(workflow):
        stage = _stage_payload(workflow, stage_name)
        latest_run = latest_stage_run_dir(workflow, stage_name, artifact_root)
        statuses.append(
            {
                "stage": stage_name,
                "profile": stage.get("profile"),
                "model": stage.get("model"),
                "input_manifest": stage.get("input_manifest"),
                "input_manifest_exists": Path(str(stage["input_manifest"])).is_file(),
                "next_manifest": stage.get("next_manifest"),
                "next_manifest_exists": (
                    Path(str(stage["next_manifest"])).is_file()
                    if isinstance(stage.get("next_manifest"), str)
                    else None
                ),
                "latest_run_dir": str(latest_run) if latest_run is not None else None,
            }
        )
    return {
        "workflow_config": workflow.get("_workflow_path"),
        "artifact_root": str(_resolve_artifact_root(artifact_root)) if _resolve_artifact_root(artifact_root) is not None else None,
        "config_dir": workflow.get("config_dir"),
        "base_manifest": workflow.get("base_manifest"),
        "base_manifest_exists": Path(str(workflow["base_manifest"])).is_file(),
        "stages": statuses,
    }


def command_seed_run(
    workflow: Mapping[str, Any],
    stage_name: str,
    *,
    source_run_dir: Path,
    manifest_path: Optional[str],
    artifact_root: str | None = None,
) -> Dict[str, Any]:
    logic = _load_repoqa_logic_module()
    env, profile_payload = _load_stage_environment_and_profile(workflow, stage_name, artifact_root)
    stage = _stage_payload(workflow, stage_name)
    resolved_manifest_path = Path(manifest_path) if isinstance(manifest_path, str) and manifest_path else Path(
        str(stage["input_manifest"])
    )
    benchmark_manifest = _load_json_object(resolved_manifest_path)
    runtime_backend = resolve_runtime_backend(None, profile_payload)
    docker_runtime = (
        resolve_docker_runtime_config(env, profile_payload=profile_payload)
        if runtime_backend == "docker"
        else None
    )
    profile_name = stage.get("profile")
    run_manifest = logic.create_repoqa_prompted_run_manifest(
        env,
        benchmark_manifest=benchmark_manifest,
        agent_id=str(resolve_run_value(None, profile_payload, "agent_id")),
        profile_name=str(profile_name) if isinstance(profile_name, str) else None,
        profile_payload=profile_payload,
        schedule_overrides={},
        model_override=resolve_run_value(None, profile_payload, "model"),
        max_task_restarts=int(resolve_run_value(None, profile_payload, "max_task_restarts", default=2)),
        repeat_count=int(resolve_run_value(None, profile_payload, "repeat_count", default=1)),
        runtime_backend=runtime_backend,
        docker_runtime=docker_runtime,
    )
    run_root = env.paths.results_root / str(workflow["benchmark"]) / str(run_manifest["run_id"])
    run_root.mkdir(parents=True, exist_ok=True)
    run_manifest_path = run_root / "run-manifest.json"
    write_json_atomic(run_manifest_path, run_manifest)

    source_results_path = source_run_dir / "results.jsonl"
    if not source_results_path.is_file():
        raise FileNotFoundError(f"Missing source results file: {source_results_path}")
    source_rows = _load_jsonl_objects(source_results_path)
    overlapping_rows = select_result_rows_for_manifest(
        source_rows,
        [task for task in run_manifest.get("tasks") or [] if isinstance(task, dict)],
        require_all_known=False,
    )
    imported_rows = []
    for row in overlapping_rows:
        copied = dict(row)
        copied["imported_result"] = True
        copied["import_mode"] = "actual_results"
        copied["source_run_dir"] = str(source_run_dir)
        copied["imported_at"] = isoformat_utc()
        imported_rows.append(copied)
    results_jsonl_path = run_root / "results.jsonl"
    write_jsonl_atomic(results_jsonl_path, imported_rows)
    return {
        "stage": stage_name,
        "artifact_root": str(_resolve_artifact_root(artifact_root)) if _resolve_artifact_root(artifact_root) is not None else None,
        "source_run_dir": str(source_run_dir),
        "manifest_path": str(resolved_manifest_path),
        "run_manifest_path": str(run_manifest_path),
        "results_jsonl": str(results_jsonl_path),
        "imported_instance_count": len(imported_rows),
        "imported_task_count": len({str(row["task"]["task_id"]) for row in imported_rows}),
    }


def command_report(workflow: Mapping[str, Any], artifact_root: str | None = None) -> Dict[str, Any]:
    report = build_hierarchical_report(workflow, artifact_root)
    output_path = _report_output_path(workflow, artifact_root)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        report["output_json"] = str(output_path)
        tasks_csv_path = output_path.with_name(output_path.stem + "-tasks.csv")
        stages_csv_path = output_path.with_name(output_path.stem + "-stages.csv")
        _write_csv(
            tasks_csv_path,
            report["tasks"],
            [
                "task_id",
                "language",
                "repo",
                "symbol",
                "path",
                "tier",
                "nano_score",
                "nano_actually_ran",
                "nano_skipped_due_to_context",
                "mini_score",
                "mini_actually_ran",
                "mini_skipped_due_to_context",
                "mini_assumed_success",
                "full_score",
                "full_actually_ran",
                "full_skipped_due_to_context",
                "full_assumed_success",
            ],
        )
        _write_csv(
            stages_csv_path,
            report["stage_summaries"],
            [
                "stage",
                "model",
                "state",
                "run_dir",
                "inherited_task_count",
                "run_task_count",
                "skipped_due_to_context_task_count",
                "average_run_task_score",
                "partially_successful_run_task_count",
                "average_partially_successful_run_task_score",
                "effective_accuracy",
                "fully_solved_task_count",
                "fully_successful_run_task_count",
                "repeat_count",
                "actual_run_instance_count",
                "successful_request_instance_count",
                "error_request_instance_count",
                "has_error_request_instances",
                "token_measured_request_instance_count",
                "duration_measured_request_instance_count",
                "tps_measured_request_instance_count",
                "average_input_tokens",
                "average_output_tokens",
                "average_reasoning_tokens",
                "average_duration_seconds",
                "average_output_tokens_per_second",
                "cost_per_run_instance",
                "total_cost",
            ],
        )
        report["output_tasks_csv"] = str(tasks_csv_path)
        report["output_stages_csv"] = str(stages_csv_path)
    return report


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run and report staged RepoQA prompted workflows.")
    parser.add_argument("--workflow-config", default=str(DEFAULT_WORKFLOW_CONFIG))
    parser.add_argument("--artifact-root")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("prepare-base-manifest")
    run_stage = subparsers.add_parser("run-stage")
    run_stage.add_argument("stage", choices=["nano", "mini", "full"])
    run_stage.add_argument("--manifest-path")
    run_stage.add_argument("--run-manifest")
    refilter = subparsers.add_parser("refilter-next")
    refilter.add_argument("stage", choices=["nano", "mini"])
    seed_run = subparsers.add_parser("seed-run")
    seed_run.add_argument("stage", choices=["nano", "mini", "full"])
    seed_run.add_argument("--source-run-dir", required=True)
    seed_run.add_argument("--manifest-path")
    subparsers.add_parser("status")
    subparsers.add_parser("report")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    workflow = load_workflow(Path(args.workflow_config).expanduser().resolve())
    if args.command == "prepare-base-manifest":
        payload = command_prepare_base_manifest(workflow)
    elif args.command == "run-stage":
        payload = command_run_stage_with_overrides(
            workflow,
            args.stage,
            manifest_path=args.manifest_path,
            run_manifest_path=args.run_manifest,
            artifact_root=args.artifact_root,
        )
    elif args.command == "refilter-next":
        payload = command_refilter_next(workflow, args.stage, args.artifact_root)
    elif args.command == "seed-run":
        payload = command_seed_run(
            workflow,
            args.stage,
            source_run_dir=Path(args.source_run_dir).expanduser().resolve(),
            manifest_path=args.manifest_path,
            artifact_root=args.artifact_root,
        )
    elif args.command == "status":
        payload = command_status(workflow, args.artifact_root)
    elif args.command == "report":
        payload = command_report(workflow, args.artifact_root)
    else:
        raise ValueError(f"Unknown command {args.command!r}")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())