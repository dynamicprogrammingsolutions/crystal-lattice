from __future__ import annotations

import json
import importlib.util
import re
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple
import random

from agent_app.config import resolve_request_config
from agent_core import Session

from agent_evaluations.config_dir import EvaluationEnvironment, benchmark_settings, merge_dicts
from agent_evaluations.container_backend import (
    DockerRuntimeConfig,
    run_benchmark_task_in_container,
    warm_container_plugin_cache,
)
from agent_evaluations.repeated_runs import (
    aggregate_results_by_task_id,
    expand_task_payloads_with_repeats,
    load_existing_results_for_manifest,
    normalize_repeat_count,
    task_instance_id,
)
from agent_evaluations.scheduler import plan_task_starts, policy_from_config, sleep_until
from agent_evaluations.utils import (
    append_jsonl,
    isoformat_utc,
    utc_now,
    write_json,
    write_json_atomic,
    write_jsonl_atomic,
)


def _load_repoqa_shared_module() -> Any:
    module_name = "agent_evaluations_external_benchmark_repoqa_shared_common"
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached
    module_path = Path(__file__).resolve().parents[1] / "repoqa_shared" / "common.py"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load RepoQA shared helpers from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_shared = _load_repoqa_shared_module()
DEFAULT_REPOQA_RELEASE = _shared.DEFAULT_REPOQA_RELEASE
RepoQATask = _shared.RepoQATask
count_tool_calls = _shared.count_tool_calls
download_repoqa_release = _shared.download_repoqa_release
extract_final_assistant_text = _shared.extract_final_assistant_text
iter_repoqa_tasks = _shared.iter_repoqa_tasks
load_repoqa_dataset = _shared.load_repoqa_dataset
repoqa_cache_path = _shared.repoqa_cache_path
score_repoqa_answer = _shared.score_repoqa_answer


REPOQA_PROMPTED_BENCHMARK_ID = "repoqa-prompted"
REPOQA_LANGUAGE_ORDER = ["python", "cpp", "java", "typescript", "rust", "go"]


def default_repoqa_prompted_manifest_path(
    env: EvaluationEnvironment,
    *,
    release: str,
    language: str,
    seed: int,
    limit: int | None,
) -> Path:
    limit_part = "all" if limit is None else str(limit)
    return (
        env.paths.manifests_root
        / REPOQA_PROMPTED_BENCHMARK_ID
        / f"{language}-{release}-seed{seed}-limit{limit_part}.json"
    )


def build_repoqa_prompted_manifest(
    env: EvaluationEnvironment,
    *,
    release: str,
    language: str,
    limit: int | None,
    seed: int,
) -> Dict[str, Any]:
    dataset = load_repoqa_dataset(env, release=release)
    languages = _resolve_languages(dataset, language)
    tasks = _select_repoqa_tasks(dataset, languages=languages, seed=seed, limit=limit)

    return {
        "benchmark": REPOQA_PROMPTED_BENCHMARK_ID,
        "release": release,
        "language": language,
        "languages": languages,
        "seed": seed,
        "limit": limit,
        "created_at": isoformat_utc(),
        "task_count": len(tasks),
        "tasks": [task.to_manifest_dict() for task in tasks],
    }


def _resolve_languages(dataset: Dict[str, Any], language: str) -> List[str]:
    if language == "all":
        available = [item for item in REPOQA_LANGUAGE_ORDER if isinstance(dataset.get(item), list)]
        if available:
            return available
        discovered = sorted(key for key, value in dataset.items() if isinstance(value, list))
        if discovered:
            return discovered
        raise KeyError("RepoQA dataset does not contain any language task lists")
    if not isinstance(dataset.get(language), list):
        raise KeyError(f"RepoQA dataset does not contain language {language!r}")
    return [language]


def _select_repoqa_tasks(
    dataset: Dict[str, Any],
    *,
    languages: Sequence[str],
    seed: int,
    limit: int | None,
) -> List[RepoQATask]:
    per_language: List[List[RepoQATask]] = []
    for language in languages:
        tasks = list(iter_repoqa_tasks(dataset, language=language))
        rng = random.Random(f"{seed}:{language}")
        rng.shuffle(tasks)
        per_language.append(tasks)

    merged: List[RepoQATask] = []
    max_length = max((len(tasks) for tasks in per_language), default=0)
    for index in range(max_length):
        for tasks in per_language:
            if index < len(tasks):
                merged.append(tasks[index])
                if isinstance(limit, int) and limit > 0 and len(merged) >= limit:
                    return merged
    return merged[:limit] if isinstance(limit, int) and limit > 0 else merged


def _workspace_root_for_run(env: EvaluationEnvironment, run_id: str, runtime_task_id: str) -> Path:
    return env.paths.workspace_root / REPOQA_PROMPTED_BENCHMARK_ID / run_id / runtime_task_id


def _task_from_payload(task_payload: Dict[str, Any]) -> RepoQATask:
    return RepoQATask(
        task_id=str(task_payload["task_id"]),
        language=str(task_payload["language"]),
        repo_index=int(task_payload["repo_index"]),
        needle_index=int(task_payload["needle_index"]),
        repo_name=str(task_payload["repo_name"]),
        commit_sha=str(task_payload["commit_sha"]),
        path=str(task_payload["path"]),
        symbol=str(task_payload["symbol"]),
        description=str(task_payload["description"]),
        start_line=int(task_payload["start_line"]),
        end_line=int(task_payload["end_line"]),
        ground_truth_code=str(task_payload["ground_truth_code"]),
    )


def _repoqa_prompted_settings(env: EvaluationEnvironment) -> Dict[str, Any]:
    settings = benchmark_settings(env)
    subtree = settings.get("repoqa_prompted")
    if isinstance(subtree, dict):
        return dict(subtree)
    return {}


def _dependency_sorted_paths(repo_entry: Dict[str, Any]) -> List[str]:
    content_map = repo_entry.get("content")
    dependency_map = repo_entry.get("dependency")
    if not isinstance(content_map, dict):
        raise ValueError("RepoQA repo entry missing content map")
    paths = sorted(path for path, content in content_map.items() if isinstance(path, str) and isinstance(content, str))
    if not isinstance(dependency_map, dict):
        return paths

    ordered: List[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(path: str) -> None:
        if path in visited:
            return
        if path in visiting:
            return
        visiting.add(path)
        raw_deps = dependency_map.get(path)
        deps = sorted(dep for dep in raw_deps if isinstance(dep, str)) if isinstance(raw_deps, list) else []
        for dep in deps:
            if dep in content_map:
                visit(dep)
        visiting.remove(path)
        visited.add(path)
        ordered.append(path)

    entrypoint_path = repo_entry.get("entrypoint_path")
    prioritized = [path for path in paths if isinstance(entrypoint_path, str) and path.startswith(entrypoint_path)]
    for path in prioritized + paths:
        visit(path)
    return ordered


def build_repoqa_prompted_prompt(
    env: EvaluationEnvironment,
    *,
    task: RepoQATask,
    release: str,
) -> Tuple[str, Dict[str, Any]]:
    dataset = load_repoqa_dataset(env, release=release)
    repo_entry = dataset[task.language][task.repo_index]
    content_map = repo_entry.get("content")
    if not isinstance(content_map, dict):
        raise ValueError("RepoQA repo entry missing content map")

    settings = _repoqa_prompted_settings(env)
    context_budget_chars = int(settings.get("context_budget_chars") or 1000000)
    max_files_raw = settings.get("max_files")
    max_files = int(max_files_raw) if isinstance(max_files_raw, int) and max_files_raw > 0 else None

    file_sections: List[str] = []
    included_paths: List[str] = []
    used_chars = 0
    truncated = False

    for path in _dependency_sorted_paths(repo_entry):
        content = content_map.get(path)
        if not isinstance(content, str):
            continue
        section = f"\nFile: {path}\n```{task.language}\n{content.rstrip()}\n```\n"
        if max_files is not None and len(included_paths) >= max_files:
            truncated = True
            break
        if file_sections and used_chars + len(section) > context_budget_chars:
            truncated = True
            break
        if not file_sections and len(section) > context_budget_chars:
            section = section[:context_budget_chars]
            truncated = True
        file_sections.append(section)
        included_paths.append(path)
        used_chars += len(section)

    prompt = (
        "You are given repository code context and a description of one target function.\n"
        "Return only the function source code that best matches the description.\n"
        "Do not explain your answer. Do not return JSON.\n\n"
        f"Repository: {task.repo_name}\n"
        f"Commit SHA: {task.commit_sha}\n"
        f"Language: {task.language}\n\n"
        "Repository code context:\n"
        + "".join(file_sections)
        + "\nFunction description:\n"
        + task.description.strip()
        + "\n\nReturn only the function source code."
    )
    metadata = {
        "benchmark": REPOQA_PROMPTED_BENCHMARK_ID,
        "release": release,
        "task": task.to_manifest_dict(),
        "included_paths": included_paths,
        "included_file_count": len(included_paths),
        "target_path": task.path,
        "target_in_context": task.path in included_paths,
        "context_budget_chars": context_budget_chars,
        "context_chars_used": used_chars,
        "truncated": truncated,
    }
    return prompt, metadata


def materialize_repoqa_prompted_workspace(
    env: EvaluationEnvironment,
    *,
    run_id: str,
    task: RepoQATask,
    release: str,
    runtime_task_id: str | None = None,
) -> Tuple[Path, Dict[str, Any]]:
    resolved_runtime_task_id = runtime_task_id or task.task_id
    workspace_root = _workspace_root_for_run(env, run_id, resolved_runtime_task_id)
    if workspace_root.exists():
        import shutil

        shutil.rmtree(workspace_root)
    workspace_root.mkdir(parents=True, exist_ok=True)
    prompt, prompt_meta = build_repoqa_prompted_prompt(env, task=task, release=release)
    (workspace_root / "PROMPT.txt").write_text(prompt, encoding="utf-8")
    metadata = {
        **prompt_meta,
        "workspace_root": str(workspace_root),
        "runtime_task_id": resolved_runtime_task_id,
        "created_at": isoformat_utc(),
    }
    write_json(workspace_root / "meta.json", metadata)
    return workspace_root, metadata


def parse_repoqa_prompted_answer(task: RepoQATask, raw_text: str) -> Tuple[Optional[Dict[str, str]], Optional[str]]:
    text = raw_text.strip()
    if not text:
        return None, "empty_response"

    fenced_blocks = re.findall(r"```[^\n`]*\n(.*?)```", text, flags=re.DOTALL)
    candidate = max(fenced_blocks, key=len).strip() if fenced_blocks else text

    symbol = task.symbol
    python_match = re.search(r"^\s*(?:async\s+def|def)\s+([A-Za-z_][A-Za-z0-9_]*)", candidate, flags=re.MULTILINE)
    if python_match:
        symbol = python_match.group(1)
    else:
        language_patterns = [
            r"^\s*(?:export\s+default\s+)?function\s+([A-Za-z_][A-Za-z0-9_]*)",
            r"^\s*(?:pub\s+)?fn\s+([A-Za-z_][A-Za-z0-9_]*)",
            r"^\s*(?:template\s*<[^>]+>\s*)?(?:inline\s+)?(?:auto|[A-Za-z_][A-Za-z0-9_:<>\[\]\s*&]+)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
            r"^\s*(?:public|private|protected|static|final|synchronized|abstract|\s)+[A-Za-z0-9_<>,\[\]\s?@]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
            r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(",
        ]
        for pattern in language_patterns:
            generic_match = re.search(pattern, candidate, flags=re.MULTILINE)
            if generic_match:
                symbol = generic_match.group(1)
                break

    if not candidate.strip():
        return None, "empty_normalized_code"

    return {
        "path": task.path,
        "symbol": symbol,
        "code": candidate.strip() + ("\n" if not candidate.endswith("\n") else ""),
    }, None


def _run_repoqa_prompted_attempt(
    env: EvaluationEnvironment,
    *,
    session_root: Path,
    user_prompt: str,
    agent_id: str,
    model_override: str | None,
) -> Dict[str, Any]:
    app = env.build_application(session_root=session_root)
    core, base_config, session = app.create_session_ephemeral(agent_id)
    session = core.add_message(session, "user", user_prompt, metadata=None, config=base_config)

    overrides: Dict[str, Any] = {
        "disable_all_tools": True,
    }
    if isinstance(model_override, str) and model_override.strip():
        overrides["model"] = model_override.strip()

    effective_auth_mode = base_config.get("auth_mode")
    provider_name = base_config.get("provider")
    if provider_name == "openai_responses" and effective_auth_mode in {"api", "auto"}:
        overrides["enable_flex_processing"] = True

    stream = False
    if provider_name == "openai_responses" and base_config.get("auth_mode") in {"auto", "chatgpt"}:
        stream = True

    effective_config = resolve_request_config(base_config, overrides)
    effective_tool_schemas = core.get_tool_schemas(effective_config)
    if effective_tool_schemas:
        raise RuntimeError(
            "RepoQA prompted runs require tool gating to fully disable tools for the request. "
            "Enable plugins.tool_gating_feature.ToolGatingFeature for the selected agent/config."
        )

    events = list(
        app.send_request(
            core,
            session,
            base_config,
            overrides=overrides,
            stream=stream,
        )
    )
    checkpoints = [event for event in events if event.get("type") == "session_checkpoint"]
    final_session = checkpoints[-1]["session"] if checkpoints else session
    if not isinstance(final_session, Session):
        raise RuntimeError("RepoQA prompted run did not produce a final session checkpoint")
    request_completed = any(event.get("type") == "request_completed" for event in events)
    if not request_completed:
        raise RuntimeError("RepoQA prompted run did not complete the request turn")
    final_assistant_text = extract_final_assistant_text(events)
    if any(event.get("type") == "error" for event in events) and not final_assistant_text.strip():
        raise RuntimeError("RepoQA prompted run completed with request error and no assistant response")
    return {
        "events": events,
        "final_session": final_session,
        "final_assistant_text": final_assistant_text,
        "tool_call_count": count_tool_calls(final_session),
        "effective_tool_schema_count": len(effective_tool_schemas),
        "usage_metadata": _extract_final_assistant_usage_metadata(final_session),
        "provider_call_count": None,
    }


def _extract_final_assistant_usage_metadata(final_session: Session) -> Optional[Dict[str, Any]]:
    for message in reversed(final_session.messages):
        if getattr(message, "role", None) != "assistant":
            continue
        metadata = message.metadata if isinstance(message.metadata, dict) else {}
        usage_fields = {
            key: value
            for key, value in metadata.items()
            if key == "usage" or key.startswith("usage_")
        }
        if usage_fields:
            return usage_fields
    return None


def _task_cost_from_usage(usage_metadata: Optional[Dict[str, Any]]) -> Optional[float]:
    if not isinstance(usage_metadata, dict):
        return None
    for key in ("usage_turn_cost_cumulative", "usage_total_cost"):
        value = usage_metadata.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    return None


def _parse_iso8601_utc(raw: Any) -> Optional[datetime]:
    if not isinstance(raw, str) or not raw.strip():
        return None
    return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc)


def _duration_seconds(result_row: Dict[str, Any]) -> Optional[float]:
    started_at = _parse_iso8601_utc(result_row.get("actual_start_at"))
    finished_at = _parse_iso8601_utc(result_row.get("finished_at"))
    if started_at is None or finished_at is None:
        return None
    duration = (finished_at - started_at).total_seconds()
    return duration if duration > 0 else None


def _usage_payload(result_row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    usage_metadata = result_row.get("usage")
    if not isinstance(usage_metadata, dict):
        return None
    usage = usage_metadata.get("usage")
    return usage if isinstance(usage, dict) else None


def _usage_input_tokens(result_row: Dict[str, Any]) -> Optional[int]:
    usage = _usage_payload(result_row)
    value = usage.get("input_tokens") if isinstance(usage, dict) else None
    return int(value) if isinstance(value, (int, float)) else None


def _usage_output_tokens(result_row: Dict[str, Any]) -> Optional[int]:
    usage = _usage_payload(result_row)
    value = usage.get("output_tokens") if isinstance(usage, dict) else None
    return int(value) if isinstance(value, (int, float)) else None


def _usage_reasoning_tokens(result_row: Dict[str, Any]) -> Optional[int]:
    usage = _usage_payload(result_row)
    if not isinstance(usage, dict):
        return None
    details = usage.get("output_tokens_details") or usage.get("completion_tokens_details")
    if not isinstance(details, dict):
        return 0
    value = details.get("reasoning_tokens")
    return int(value) if isinstance(value, (int, float)) else 0


def _average(values: Sequence[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / len(values)


def _build_repoqa_prompted_summary(
    *,
    run_manifest: Dict[str, Any],
    run_manifest_path: Path,
    results_jsonl: Path,
    task_aggregate_jsonl: Path,
    completed: Sequence[Dict[str, Any]],
    tasks: Sequence[Dict[str, Any]],
    preexisting_result_count: int,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    eligible_results = [
        item
        for item in completed
        if item.get("eligible_for_accuracy", True)
        and item.get("state") == "completed"
        and item.get("outcome") != "skipped_missing_target_context"
    ]
    matched_eligible_count = sum(
        1 for item in eligible_results if ((item.get("score") or {}).get("matched") is True)
    )
    task_aggregates = aggregate_results_by_task_id(completed)
    success_rates = [
        float(item["success_rate"])
        for item in task_aggregates
        if isinstance(item.get("success_rate"), (int, float))
    ]

    executed_results = [item for item in completed if item.get("imported_result") is not True]
    executed_request_results = [
        item for item in executed_results if item.get("outcome") != "skipped_missing_target_context"
    ]
    successful_request_results = [
        item for item in executed_request_results if item.get("state") == "completed"
    ]
    error_request_results = [
        item for item in executed_request_results if item.get("state") != "completed"
    ]

    token_rows = [
        item
        for item in successful_request_results
        if _usage_input_tokens(item) is not None
        and _usage_output_tokens(item) is not None
        and _usage_reasoning_tokens(item) is not None
    ]
    duration_rows = [item for item in successful_request_results if _duration_seconds(item) is not None]
    tps_values = [
        float(_usage_output_tokens(item) or 0) / float(_duration_seconds(item) or 1.0)
        for item in successful_request_results
        if _usage_output_tokens(item) is not None
        and _duration_seconds(item) is not None
        and float(_duration_seconds(item) or 0.0) > 0.0
    ]

    summary = {
        "run_id": run_manifest["run_id"],
        "benchmark": REPOQA_PROMPTED_BENCHMARK_ID,
        "release": run_manifest["release"],
        "language": run_manifest["language"],
        "languages": run_manifest.get("languages"),
        "agent_id": run_manifest["agent_id"],
        "repeat_count": int(run_manifest.get("repeat_count") or 1),
        "manifest_task_count": len({str(item.get("task_id")) for item in tasks if isinstance(item, dict)}),
        "task_instance_count": len(tasks),
        "logical_task_count": len(task_aggregates),
        "completed_task_count": len(completed),
        "preexisting_result_count": preexisting_result_count,
        "new_result_count": len(completed) - preexisting_result_count,
        "imported_result_count": sum(1 for item in completed if item.get("imported_result") is True),
        "executed_result_count": sum(1 for item in completed if item.get("imported_result") is not True),
        "model_request_task_count": sum(
            1 for item in completed if item.get("outcome") != "skipped_missing_target_context"
        ),
        "eligible_task_count": len(eligible_results),
        "excluded_missing_target_context_count": sum(
            1 for item in completed if item.get("outcome") == "skipped_missing_target_context"
        ),
        "matched_task_count": matched_eligible_count,
        "logical_tasks_with_all_successes": sum(
            1
            for item in task_aggregates
            if item.get("eligible_instance_count")
            and item.get("matched_instance_count") == item.get("eligible_instance_count")
            and item.get("excluded_missing_target_context_count") == 0
        ),
        "logical_tasks_with_any_success": sum(
            1 for item in task_aggregates if int(item.get("matched_instance_count") or 0) > 0
        ),
        "logical_task_average_success_rate": (
            sum(success_rates) / len(success_rates) if success_rates else None
        ),
        "accuracy": (
            sum(float((item.get("score") or {}).get("score") or 0.0) for item in eligible_results) / len(eligible_results)
            if eligible_results
            else None
        ),
        "raw_accuracy_over_manifest": (
            sum(float((item.get("score") or {}).get("score") or 0.0) for item in completed) / len(tasks)
            if tasks
            else 0.0
        ),
        "successful_request_instance_count": len(successful_request_results),
        "error_request_instance_count": len(error_request_results),
        "has_error_request_instances": len(error_request_results) > 0,
        "token_measured_request_instance_count": len(token_rows),
        "duration_measured_request_instance_count": len(duration_rows),
        "tps_measured_request_instance_count": len(tps_values),
        "average_input_tokens": _average([float(_usage_input_tokens(item) or 0) for item in token_rows]),
        "average_output_tokens": _average([float(_usage_output_tokens(item) or 0) for item in token_rows]),
        "average_reasoning_tokens": _average([float(_usage_reasoning_tokens(item) or 0) for item in token_rows]),
        "average_duration_seconds": _average([float(_duration_seconds(item) or 0.0) for item in duration_rows]),
        "average_output_tokens_per_second": _average(tps_values),
        "results_jsonl": str(results_jsonl),
        "task_aggregate_jsonl": str(task_aggregate_jsonl),
        "run_manifest_path": str(run_manifest_path),
        "completed_at": isoformat_utc(),
        "benchmark_mode": "repoqa-prompted-custom",
    }
    costs = [float(item["cost"]) for item in completed if isinstance(item.get("cost"), (int, float))]
    if costs:
        total_cost = sum(costs)
        summary["costed_task_count"] = len(costs)
        summary["total_cost"] = total_cost
        summary["total_cost_formatted"] = f"${total_cost:.6f}"
        summary["average_cost_per_costed_task"] = total_cost / len(costs)
        summary["average_cost_per_costed_task_formatted"] = f"${(total_cost / len(costs)):.6f}"
    return task_aggregates, summary


def rebuild_repoqa_prompted_artifacts(run_manifest_path: Path) -> Dict[str, Any]:
    run_manifest = json.loads(run_manifest_path.read_text(encoding="utf-8"))
    run_root = run_manifest_path.parent
    results_jsonl = run_root / "results.jsonl"
    task_aggregate_jsonl = run_root / "task-aggregate.jsonl"
    summary_json = run_root / "summary.json"
    tasks = run_manifest.get("tasks") or []
    if not isinstance(tasks, list):
        raise ValueError("run manifest tasks must be a list")
    completed, _completed_instance_ids = load_existing_results_for_manifest(results_jsonl, tasks)
    prior_summary: Dict[str, Any] = {}
    if summary_json.is_file():
        loaded = json.loads(summary_json.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            prior_summary = loaded
    preexisting_result_count_raw = prior_summary.get("preexisting_result_count")
    if isinstance(preexisting_result_count_raw, int):
        preexisting_result_count = preexisting_result_count_raw
    else:
        preexisting_result_count = sum(1 for item in completed if item.get("imported_result") is True)
    task_aggregates, summary = _build_repoqa_prompted_summary(
        run_manifest=run_manifest,
        run_manifest_path=run_manifest_path,
        results_jsonl=results_jsonl,
        task_aggregate_jsonl=task_aggregate_jsonl,
        completed=completed,
        tasks=tasks,
        preexisting_result_count=preexisting_result_count,
    )
    write_jsonl_atomic(task_aggregate_jsonl, task_aggregates)
    write_json_atomic(summary_json, summary)
    return summary


def _target_in_prompt_context(task: RepoQATask, metadata: Dict[str, Any]) -> bool:
    included_paths = metadata.get("included_paths")
    if isinstance(included_paths, list):
        return task.path in [item for item in included_paths if isinstance(item, str)]
    return bool(metadata.get("target_in_context"))


def _excluded_missing_target_context_result(
    task: RepoQATask,
    *,
    workspace_root: Path,
    metadata: Dict[str, Any],
    runtime_task_id: str,
    repeat_index: int,
    repeat_count: int,
) -> Dict[str, Any]:
    return {
        "task": task.to_manifest_dict(),
        "task_instance_id": runtime_task_id,
        "repeat_index": repeat_index,
        "repeat_count": repeat_count,
        "workspace_root": str(workspace_root),
        "attempts": [],
        "state": "skipped_missing_target_context",
        "outcome": "skipped_missing_target_context",
        "eligible_for_accuracy": False,
        "failure_category": "context_budget_excluded_target",
        "error": None,
        "score": {
            "matched": False,
            "path_match": False,
            "symbol_match": False,
            "code_match": False,
            "comparison_method": None,
            "code_comparison": None,
            "score": 0.0,
        },
        "parsed_answer": None,
        "parse_error": None,
        "final_assistant_text": "",
        "tool_call_count": 0,
        "effective_tool_schema_count": 0,
        "usage": None,
        "cost": None,
        "cost_formatted": None,
        "provider_call_count": 0,
        "target_in_context": False,
        "context_truncated": bool(metadata.get("truncated")),
        "meta": metadata,
    }


def run_repoqa_prompted_task_with_restarts_in_workspace(
    env: EvaluationEnvironment,
    *,
    task: RepoQATask,
    workspace_root: Path,
    metadata: Dict[str, Any],
    run_id: str,
    release: str,
    agent_id: str,
    model_override: str | None,
    max_task_restarts: int,
    runtime_task_id: str | None = None,
    repeat_index: int = 0,
    repeat_count: int = 1,
) -> Dict[str, Any]:
    resolved_runtime_task_id = runtime_task_id or task.task_id
    if not _target_in_prompt_context(task, metadata):
        return _excluded_missing_target_context_result(
            task,
            workspace_root=workspace_root,
            metadata=metadata,
            runtime_task_id=resolved_runtime_task_id,
            repeat_index=repeat_index,
            repeat_count=repeat_count,
        )

    user_prompt = (workspace_root / "PROMPT.txt").read_text(encoding="utf-8")
    session_root = env.paths.results_root / REPOQA_PROMPTED_BENCHMARK_ID / run_id / "sessions"
    attempts: List[Dict[str, Any]] = []
    last_error: Optional[str] = None

    for attempt_index in range(max_task_restarts + 1):
        started_at = isoformat_utc()
        try:
            attempt_result = _run_repoqa_prompted_attempt(
                env,
                session_root=session_root,
                user_prompt=user_prompt,
                agent_id=agent_id,
                model_override=model_override,
            )
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            attempts.append(
                {
                    "attempt_index": attempt_index,
                    "started_at": started_at,
                    "finished_at": isoformat_utc(),
                    "state": "retryable_failure",
                    "error": last_error,
                }
            )
            if attempt_index >= max_task_restarts:
                return {
                    "task": task.to_manifest_dict(),
                    "task_instance_id": resolved_runtime_task_id,
                    "repeat_index": repeat_index,
                    "repeat_count": repeat_count,
                    "workspace_root": str(workspace_root),
                    "attempts": attempts,
                    "state": "failed_before_turn_completed",
                    "outcome": "failed_before_turn_completed",
                    "eligible_for_accuracy": False,
                    "failure_category": "request_failure",
                    "error": last_error,
                    "score": {
                        "matched": False,
                        "path_match": False,
                        "symbol_match": False,
                        "code_match": False,
                        "comparison_method": None,
                        "code_comparison": None,
                        "score": 0.0,
                    },
                    "parsed_answer": None,
                    "parse_error": None,
                    "final_assistant_text": "",
                    "tool_call_count": 0,
                    "effective_tool_schema_count": None,
                    "usage": None,
                    "cost": None,
                    "cost_formatted": None,
                    "provider_call_count": None,
                    "target_in_context": _target_in_prompt_context(task, metadata),
                    "context_truncated": bool(metadata.get("truncated")),
                    "meta": metadata,
                }
            continue

        parsed_answer, parse_error = parse_repoqa_prompted_answer(task, attempt_result["final_assistant_text"])
        score = score_repoqa_answer(task, parsed_answer)
        attempts.append(
            {
                "attempt_index": attempt_index,
                "started_at": started_at,
                "finished_at": isoformat_utc(),
                "state": "completed",
                "error": None,
                "parse_error": parse_error,
                "tool_call_count": attempt_result["tool_call_count"],
            }
        )
        return {
            "task": task.to_manifest_dict(),
            "task_instance_id": resolved_runtime_task_id,
            "repeat_index": repeat_index,
            "repeat_count": repeat_count,
            "workspace_root": str(workspace_root),
            "attempts": attempts,
            "state": "completed",
            "outcome": "matched" if score.get("matched") is True else "mismatched",
            "eligible_for_accuracy": True,
            "failure_category": None,
            "error": None,
            "score": score,
            "parsed_answer": parsed_answer,
            "parse_error": parse_error,
            "final_assistant_text": attempt_result["final_assistant_text"],
            "tool_call_count": attempt_result["tool_call_count"],
            "effective_tool_schema_count": attempt_result["effective_tool_schema_count"],
            "usage": attempt_result["usage_metadata"],
            "cost": _task_cost_from_usage(attempt_result["usage_metadata"]),
            "cost_formatted": (
                attempt_result["usage_metadata"].get("usage_turn_cost_cumulative_formatted")
                if isinstance(attempt_result["usage_metadata"], dict)
                and isinstance(attempt_result["usage_metadata"].get("usage_turn_cost_cumulative_formatted"), str)
                else (
                    attempt_result["usage_metadata"].get("usage_total_cost_formatted")
                    if isinstance(attempt_result["usage_metadata"], dict)
                    and isinstance(attempt_result["usage_metadata"].get("usage_total_cost_formatted"), str)
                    else None
                )
            ),
            "provider_call_count": attempt_result["provider_call_count"],
            "target_in_context": _target_in_prompt_context(task, metadata),
            "context_truncated": bool(metadata.get("truncated")),
            "meta": metadata,
        }

    raise RuntimeError("Unreachable RepoQA prompted retry loop exit")


def run_repoqa_prompted_task_with_restarts(
    env: EvaluationEnvironment,
    *,
    run_id: str,
    release: str,
    task_payload: Dict[str, Any],
    agent_id: str,
    model_override: str | None,
    max_task_restarts: int,
) -> Dict[str, Any]:
    task = _task_from_payload(task_payload)
    runtime_task_id = task_instance_id(task_payload)
    repeat_index = int(task_payload.get("repeat_index") or 0)
    repeat_count = normalize_repeat_count(task_payload.get("repeat_count") or 1)
    workspace_root, metadata = materialize_repoqa_prompted_workspace(
        env,
        run_id=run_id,
        task=task,
        release=release,
        runtime_task_id=runtime_task_id,
    )
    return run_repoqa_prompted_task_with_restarts_in_workspace(
        env,
        task=task,
        workspace_root=workspace_root,
        metadata=metadata,
        run_id=run_id,
        release=release,
        agent_id=agent_id,
        model_override=model_override,
        max_task_restarts=max_task_restarts,
        runtime_task_id=runtime_task_id,
        repeat_index=repeat_index,
        repeat_count=repeat_count,
    )


def _normalize_run_schedule(settings: Dict[str, Any], profile: Dict[str, Any], explicit: Dict[str, Any]) -> Dict[str, Any]:
    merged = merge_dicts(
        settings.get("schedule", {}) if isinstance(settings.get("schedule"), dict) else {},
        profile.get("schedule", {}) if isinstance(profile.get("schedule"), dict) else {},
    )
    return merge_dicts(merged, explicit)


def create_repoqa_prompted_run_manifest(
    env: EvaluationEnvironment,
    *,
    benchmark_manifest: Dict[str, Any],
    agent_id: str,
    profile_name: str | None,
    profile_payload: Dict[str, Any],
    schedule_overrides: Dict[str, Any],
    model_override: str | None,
    max_task_restarts: int,
    repeat_count: int,
    runtime_backend: str,
    docker_runtime: DockerRuntimeConfig | None,
) -> Dict[str, Any]:
    settings = benchmark_settings(env)
    schedule_config = _normalize_run_schedule(settings, profile_payload, schedule_overrides)
    policy = policy_from_config(schedule_config, default_seed=int(benchmark_manifest.get("seed") or 0))
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    expanded_tasks = expand_task_payloads_with_repeats(
        benchmark_manifest.get("tasks") or [],
        repeat_count=repeat_count,
    )
    planned_starts = plan_task_starts(
        task_count=len(expanded_tasks),
        anchor=utc_now(),
        policy=policy,
    )
    return {
        "run_id": run_id,
        "created_at": isoformat_utc(),
        "benchmark": REPOQA_PROMPTED_BENCHMARK_ID,
        "release": benchmark_manifest["release"],
        "language": benchmark_manifest["language"],
        "languages": list(benchmark_manifest.get("languages") or [benchmark_manifest["language"]]),
        "agent_id": agent_id,
        "profile_name": profile_name,
        "profile": profile_payload,
        "model_override": model_override,
        "max_task_restarts": max_task_restarts,
        "repeat_count": repeat_count,
        "runtime_backend": runtime_backend,
        "docker_runtime": (
            {
                "enabled": docker_runtime.enabled,
                "image_tag": docker_runtime.image_tag,
                "dockerfile": str(docker_runtime.dockerfile),
                "build_context": str(docker_runtime.build_context),
                "config_mount_path": docker_runtime.config_mount_path,
                "task_mount_path": docker_runtime.task_mount_path,
                "results_mount_path": docker_runtime.results_mount_path,
                "task_workdir": docker_runtime.task_workdir,
                "source_bundle_path": str(docker_runtime.source_bundle_path),
                "evaluations_wheel_dir": str(docker_runtime.evaluations_wheel_dir),
                "extra_build_args": list(docker_runtime.extra_build_args),
                "extra_run_args": list(docker_runtime.extra_run_args),
                "container_env": dict(docker_runtime.container_env),
            }
            if docker_runtime is not None
            else None
        ),
        "schedule_policy": {
            "timezone": policy.timezone_name,
            "window_minutes": policy.window_minutes,
            "tasks_per_window": policy.tasks_per_window,
            "max_parallel_tasks": policy.max_parallel_tasks,
            "randomize_task_starts": policy.randomize_task_starts,
            "random_seed": policy.random_seed,
            "allowed_weekdays": sorted(policy.allowed_weekdays) if policy.allowed_weekdays is not None else None,
            "working_hours": [
                {
                    "start_minute": item.start_minute,
                    "end_minute": item.end_minute,
                }
                for item in policy.working_hours
            ],
            "max_tasks_per_day": policy.max_tasks_per_day,
        },
        "tasks": [
            {
                **task,
                "planned_start_at": isoformat_utc(start),
            }
            for task, start in zip(expanded_tasks, planned_starts)
        ],
    }


def run_repoqa_prompted_benchmark(
    env: EvaluationEnvironment,
    *,
    benchmark_manifest: Dict[str, Any],
    agent_id: str,
    profile_name: str | None,
    profile_payload: Dict[str, Any],
    schedule_overrides: Dict[str, Any],
    model_override: str | None,
    max_task_restarts: int,
    repeat_count: int = 1,
    runtime_backend: str = "host",
    docker_runtime: DockerRuntimeConfig | None = None,
    resume_run_manifest_path: Path | None = None,
) -> Path:
    if resume_run_manifest_path is not None:
        run_manifest = json.loads(resume_run_manifest_path.read_text(encoding="utf-8"))
        run_manifest_path = resume_run_manifest_path
    else:
        run_manifest = create_repoqa_prompted_run_manifest(
            env,
            benchmark_manifest=benchmark_manifest,
            agent_id=agent_id,
            profile_name=profile_name,
            profile_payload=profile_payload,
            schedule_overrides=schedule_overrides,
            model_override=model_override,
            max_task_restarts=max_task_restarts,
            repeat_count=repeat_count,
            runtime_backend=runtime_backend,
            docker_runtime=docker_runtime,
        )
        run_root = env.paths.results_root / REPOQA_PROMPTED_BENCHMARK_ID / run_manifest["run_id"]
        run_root.mkdir(parents=True, exist_ok=True)
        run_manifest_path = run_root / "run-manifest.json"
        write_json_atomic(run_manifest_path, run_manifest)

    run_root = run_manifest_path.parent
    results_jsonl = run_root / "results.jsonl"
    task_aggregate_jsonl = run_root / "task-aggregate.jsonl"
    summary_json = run_root / "summary.json"

    if runtime_backend == "docker":
        if docker_runtime is None:
            raise ValueError("docker_runtime must be provided when runtime_backend='docker'")
        warm_container_plugin_cache(
            docker_runtime,
            host_config_dir=env.paths.config_dir,
            agent_id=agent_id,
        )

    active_tasks: Dict[Any, Dict[str, Any]] = {}

    from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

    tasks = run_manifest.get("tasks") or []
    if not isinstance(tasks, list):
        raise ValueError("run manifest tasks must be a list")
    completed, completed_instance_ids = load_existing_results_for_manifest(results_jsonl, tasks)
    preexisting_result_count = len(completed)

    schedule_policy = run_manifest.get("schedule_policy") or {}
    policy = policy_from_config(
        {
            "timezone": schedule_policy.get("timezone"),
            "window_minutes": schedule_policy.get("window_minutes"),
            "tasks_per_window": schedule_policy.get("tasks_per_window"),
            "max_parallel_tasks": schedule_policy.get("max_parallel_tasks"),
            "randomize_task_starts": schedule_policy.get("randomize_task_starts"),
            "random_seed": schedule_policy.get("random_seed"),
        },
        default_seed=0,
    )

    next_index = 0
    with ThreadPoolExecutor(max_workers=policy.max_parallel_tasks) as executor:
        while next_index < len(tasks) or active_tasks:
            while next_index < len(tasks) and len(active_tasks) < policy.max_parallel_tasks:
                task_payload = tasks[next_index]
                if not isinstance(task_payload, dict):
                    next_index += 1
                    continue
                if task_instance_id(task_payload) in completed_instance_ids:
                    next_index += 1
                    continue
                planned_start_at = task_payload.get("planned_start_at")
                if not isinstance(planned_start_at, str):
                    raise ValueError("run manifest task missing planned_start_at")
                planned_dt = datetime.fromisoformat(planned_start_at.replace("Z", "+00:00"))
                now = utc_now()
                if planned_dt > now:
                    break
                if run_manifest.get("runtime_backend") == "docker":
                    docker_cfg_payload = run_manifest.get("docker_runtime")
                    if not isinstance(docker_cfg_payload, dict):
                        raise ValueError("docker runtime backend selected without docker_runtime config")
                    runtime = DockerRuntimeConfig(
                        enabled=bool(docker_cfg_payload.get("enabled", True)),
                        image_tag=str(docker_cfg_payload["image_tag"]),
                        dockerfile=Path(str(docker_cfg_payload["dockerfile"])),
                        build_context=Path(str(docker_cfg_payload["build_context"])),
                        source_bundle_path=Path(str(docker_cfg_payload["source_bundle_path"])),
                        evaluations_wheel_dir=Path(str(docker_cfg_payload["evaluations_wheel_dir"])),
                        config_mount_path=str(docker_cfg_payload["config_mount_path"]),
                        task_mount_path=str(docker_cfg_payload["task_mount_path"]),
                        results_mount_path=str(docker_cfg_payload["results_mount_path"]),
                        task_workdir=str(docker_cfg_payload["task_workdir"]),
                        extra_build_args=tuple(docker_cfg_payload.get("extra_build_args") or []),
                        extra_run_args=tuple(docker_cfg_payload.get("extra_run_args") or []),
                        container_env=dict(docker_cfg_payload.get("container_env") or {}),
                    )
                    task = _task_from_payload(task_payload)
                    workspace_root, _metadata = materialize_repoqa_prompted_workspace(
                        env,
                        run_id=str(run_manifest["run_id"]),
                        task=task,
                        release=str(run_manifest["release"]),
                        runtime_task_id=task_instance_id(task_payload),
                    )
                    task_input_dir = run_root / "task-inputs"
                    task_result_dir = run_root / "task-results"
                    task_input_dir.mkdir(parents=True, exist_ok=True)
                    task_result_dir.mkdir(parents=True, exist_ok=True)
                    runtime_task_id = task_instance_id(task_payload)
                    task_input_path = task_input_dir / f"{runtime_task_id}.json"
                    task_output_path = task_result_dir / f"{runtime_task_id}.json"
                    write_json_atomic(task_input_path, task_payload)
                    future = executor.submit(
                        run_benchmark_task_in_container,
                        runtime,
                        benchmark_id=REPOQA_PROMPTED_BENCHMARK_ID,
                        host_config_dir=env.paths.config_dir,
                        host_workspace_root=workspace_root,
                        host_results_root=run_root,
                        host_task_payload_path=task_input_path,
                        host_output_path=task_output_path,
                        release=str(run_manifest["release"]),
                        agent_id=str(run_manifest["agent_id"]),
                        model_override=(
                            str(run_manifest.get("model_override"))
                            if isinstance(run_manifest.get("model_override"), str)
                            else None
                        ),
                        max_task_restarts=int(run_manifest.get("max_task_restarts") or 0),
                    )
                else:
                    future = executor.submit(
                        run_repoqa_prompted_task_with_restarts,
                        env,
                        run_id=str(run_manifest["run_id"]),
                        release=str(run_manifest["release"]),
                        task_payload=task_payload,
                        agent_id=str(run_manifest["agent_id"]),
                        model_override=(
                            str(run_manifest.get("model_override"))
                            if isinstance(run_manifest.get("model_override"), str)
                            else None
                        ),
                        max_task_restarts=int(run_manifest.get("max_task_restarts") or 0),
                    )
                active_tasks[future] = {
                    "task_id": task_payload.get("task_id"),
                    "task_instance_id": task_payload.get("task_instance_id"),
                    "repeat_index": task_payload.get("repeat_index"),
                    "repeat_count": task_payload.get("repeat_count"),
                    "planned_start_at": planned_start_at,
                    "actual_start_at": isoformat_utc(),
                }
                next_index += 1

            if not active_tasks:
                if next_index >= len(tasks):
                    break
                next_task = tasks[next_index]
                planned_start_at = next_task.get("planned_start_at")
                if not isinstance(planned_start_at, str):
                    raise ValueError("run manifest task missing planned_start_at")
                planned_dt = datetime.fromisoformat(planned_start_at.replace("Z", "+00:00"))
                sleep_until(planned_dt)
                continue

            timeout = None
            if next_index < len(tasks):
                next_task = tasks[next_index]
                planned_start_at = next_task.get("planned_start_at")
                if isinstance(planned_start_at, str):
                    planned_dt = datetime.fromisoformat(planned_start_at.replace("Z", "+00:00"))
                    timeout = max(0.0, (planned_dt - utc_now()).total_seconds())

            done, _pending = wait(list(active_tasks.keys()), timeout=timeout, return_when=FIRST_COMPLETED)
            if not done:
                continue
            for future in done:
                task_info = active_tasks.pop(future)
                result = future.result()
                payload = {
                    **task_info,
                    "finished_at": isoformat_utc(),
                    **result,
                }
                append_jsonl(results_jsonl, payload)
                completed.append(payload)
                completed_instance_ids.add(str(payload["task_instance_id"]))

    task_aggregates, summary = _build_repoqa_prompted_summary(
        run_manifest=run_manifest,
        run_manifest_path=run_manifest_path,
        results_jsonl=results_jsonl,
        task_aggregate_jsonl=task_aggregate_jsonl,
        completed=completed,
        tasks=tasks,
        preexisting_result_count=preexisting_result_count,
    )
    write_jsonl_atomic(task_aggregate_jsonl, task_aggregates)
    write_json_atomic(summary_json, summary)
    return run_manifest_path


def run_repoqa_prompted_single_task_from_payload(
    env: EvaluationEnvironment,
    *,
    task_payload: Dict[str, Any],
    run_id: str,
    release: str,
    workspace_root: Path,
    agent_id: str,
    model_override: str | None,
    max_task_restarts: int,
) -> Dict[str, Any]:
    task = _task_from_payload(task_payload)
    runtime_task_id = task_instance_id(task_payload)
    repeat_index = int(task_payload.get("repeat_index") or 0)
    repeat_count = normalize_repeat_count(task_payload.get("repeat_count") or 1)
    meta_path = workspace_root / "meta.json"
    metadata: Dict[str, Any]
    if meta_path.is_file():
        loaded = json.loads(meta_path.read_text(encoding="utf-8"))
        metadata = loaded if isinstance(loaded, dict) else {}
    else:
        _prompt, prompt_meta = build_repoqa_prompted_prompt(env, task=task, release=release)
        metadata = {
            **prompt_meta,
            "workspace_root": str(workspace_root),
            "runtime_task_id": runtime_task_id,
            "created_at": isoformat_utc(),
        }
        write_json(workspace_root / "meta.json", metadata)
        (workspace_root / "PROMPT.txt").write_text(_prompt, encoding="utf-8")
    return run_repoqa_prompted_task_with_restarts_in_workspace(
        env,
        task=task,
        workspace_root=workspace_root,
        metadata=metadata,
        run_id=run_id,
        release=release,
        agent_id=agent_id,
        model_override=model_override,
        max_task_restarts=max_task_restarts,
        runtime_task_id=runtime_task_id,
        repeat_index=repeat_index,
        repeat_count=repeat_count,
    )