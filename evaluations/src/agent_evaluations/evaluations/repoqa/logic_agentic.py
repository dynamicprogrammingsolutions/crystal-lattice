from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
from typing import Any, Dict, Iterable, List, Optional, Tuple

from agent_core import Session
from agent_core.tool_interop import DEFAULT_TOOL_INTEROP_REGISTRY

from agent_evaluations.container_backend import (
    DockerRuntimeConfig,
    resolve_docker_runtime_config,
    run_benchmark_task_in_container,
    warm_container_plugin_cache,
)
from agent_evaluations.config_dir import EvaluationEnvironment, benchmark_settings, merge_dicts
from agent_evaluations.evaluations.repoqa.common import (
    DEFAULT_REPOQA_RELEASE,
    RepoQATask,
    count_tool_calls,
    download_repoqa_release,
    extract_final_assistant_text,
    iter_repoqa_tasks,
    load_repoqa_dataset,
    repoqa_cache_path,
    score_repoqa_answer,
)
from agent_evaluations.profiles import load_run_profile
from agent_evaluations.repeated_runs import (
    aggregate_results_by_task_id,
    expand_task_payloads_with_repeats,
    normalize_repeat_count,
    task_instance_id,
)
from agent_evaluations.scheduler import TaskStartPolicy, plan_task_starts, policy_from_config, sleep_until
from agent_evaluations.utils import append_jsonl, isoformat_utc, utc_now, write_json, write_json_atomic


REPOQA_BENCHMARK_ID = "repoqa"

def build_repoqa_manifest(
    env: EvaluationEnvironment,
    *,
    release: str,
    language: str,
    limit: int | None,
    seed: int,
) -> Dict[str, Any]:
    dataset = load_repoqa_dataset(env, release=release)
    tasks = list(iter_repoqa_tasks(dataset, language=language))
    if seed:
        import random

        rng = random.Random(seed)
        rng.shuffle(tasks)
    if isinstance(limit, int) and limit > 0:
        tasks = tasks[:limit]

    manifest = {
        "benchmark": REPOQA_BENCHMARK_ID,
        "release": release,
        "language": language,
        "seed": seed,
        "limit": limit,
        "created_at": isoformat_utc(),
        "task_count": len(tasks),
        "tasks": [task.to_manifest_dict() for task in tasks],
    }
    return manifest


def default_repoqa_manifest_path(
    env: EvaluationEnvironment,
    *,
    release: str,
    language: str,
    seed: int,
    limit: int | None,
) -> Path:
    limit_part = "all" if limit is None else str(limit)
    return env.paths.manifests_root / "repoqa" / f"{language}-{release}-seed{seed}-limit{limit_part}.json"


def _workspace_root_for_run(env: EvaluationEnvironment, run_id: str, runtime_task_id: str) -> Path:
    return env.paths.workspace_root / "repoqa" / run_id / runtime_task_id


def _repoqa_workspace_prompt(task: RepoQATask) -> str:
    return (
        "# RepoQA Task\n\n"
        "Use the workspace tools to inspect `repo/` and identify the requested function.\n\n"
        f"- Repository: `{task.repo_name}`\n"
        f"- Commit SHA: `{task.commit_sha}`\n"
        f"- Target file path: `{task.path}`\n"
        f"- Target symbol: `{task.symbol}`\n"
        f"- Description:\n{task.description}\n\n"
        "Return exactly one JSON object and no surrounding markdown. The JSON object must contain:\n"
        '- `"path"`: the file path\n'
        '- `"symbol"`: the function or method name\n'
        '- `"code"`: the full function source code\n'
    )


def materialize_repoqa_workspace(
    env: EvaluationEnvironment,
    *,
    run_id: str,
    task: RepoQATask,
    release: str,
    runtime_task_id: str | None = None,
) -> Tuple[Path, Dict[str, Any]]:
    dataset = load_repoqa_dataset(env, release=release)
    repo_entry = dataset[task.language][task.repo_index]
    resolved_runtime_task_id = runtime_task_id or task.task_id
    workspace_root = _workspace_root_for_run(env, run_id, resolved_runtime_task_id)
    if workspace_root.exists():
        shutil.rmtree(workspace_root)
    repo_root = workspace_root / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)

    content_map = repo_entry.get("content")
    if not isinstance(content_map, dict):
        raise ValueError("RepoQA repo entry missing content map")
    for relative_path, content in sorted(content_map.items()):
        if not isinstance(relative_path, str) or not isinstance(content, str):
            continue
        destination = repo_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")

    task_md = workspace_root / "TASK.md"
    task_md.write_text(_repoqa_workspace_prompt(task), encoding="utf-8")

    if env.paths.agents_path.is_file():
        shutil.copy2(env.paths.agents_path, workspace_root / "AGENTS.md")

    submission_dir = workspace_root / "submission"
    submission_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "benchmark": REPOQA_BENCHMARK_ID,
        "release": release,
        "task": task.to_manifest_dict(),
        "workspace_root": str(workspace_root),
        "repo_root": str(repo_root),
        "runtime_task_id": resolved_runtime_task_id,
        "created_at": isoformat_utc(),
    }
    write_json(workspace_root / "meta.json", metadata)
    return workspace_root, metadata


def parse_repoqa_answer(raw_text: str) -> Tuple[Optional[Dict[str, str]], Optional[str]]:
    text = raw_text.strip()
    if not text:
        return None, "empty_response"

    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            text = "\n".join(lines[1:-1]).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end >= start:
        candidate = text[start : end + 1]
    else:
        candidate = text

    try:
        payload = json.loads(candidate)
    except Exception as exc:
        return None, f"json_parse_failed: {exc}"

    if not isinstance(payload, dict):
        return None, "answer_not_object"
    path = payload.get("path")
    symbol = payload.get("symbol")
    code = payload.get("code")
    if not isinstance(path, str) or not isinstance(symbol, str) or not isinstance(code, str):
        return None, "answer_missing_required_fields"
    return {
        "path": path.strip(),
        "symbol": symbol.strip(),
        "code": code,
    }, None

def _run_repoqa_attempt(
    env: EvaluationEnvironment,
    *,
    session_root: Path,
    workspace_root: Path,
    user_prompt: str,
    agent_id: str,
    model_override: str | None,
) -> Dict[str, Any]:
    app = env.build_application(session_root=session_root)
    core, base_config, session = app.create_session_ephemeral(agent_id)
    session = core.add_message(session, "user", user_prompt, metadata=None, config=base_config)

    overrides: Dict[str, Any] = {
        "working_directory": str(workspace_root),
        "allowed_paths": [str(workspace_root)],
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
        raise RuntimeError("RepoQA run did not produce a final session checkpoint")

    request_completed = any(event.get("type") == "request_completed" for event in events)
    if not request_completed:
        raise RuntimeError("RepoQA run did not complete the request turn")

    return {
        "events": events,
        "final_session": final_session,
        "final_assistant_text": extract_final_assistant_text(events),
        "tool_call_count": count_tool_calls(final_session),
        "provider_call_count": None,
    }


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


def run_repoqa_task_with_restarts_in_workspace(
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
    user_prompt = (
        "Solve the RepoQA task in this workspace. Read `TASK.md`, inspect `repo/`, "
        "and respond with exactly one JSON object."
    )
    session_root = env.paths.results_root / "repoqa" / run_id / "sessions"
    last_error: Optional[str] = None
    attempts: List[Dict[str, Any]] = []

    for attempt_index in range(max_task_restarts + 1):
        started_at = isoformat_utc()
        try:
            attempt_result = _run_repoqa_attempt(
                env,
                session_root=session_root,
                workspace_root=workspace_root,
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
                    "eligible_for_accuracy": True,
                    "failure_category": "request_failure",
                    "error": last_error,
                    "score": {
                        "matched": False,
                        "path_match": False,
                        "symbol_match": False,
                        "code_match": False,
                        "score": 0.0,
                    },
                    "parsed_answer": None,
                    "final_assistant_text": "",
                    "tool_call_count": 0,
                    "provider_call_count": None,
                }
            continue

        parsed_answer, parse_error = parse_repoqa_answer(attempt_result["final_assistant_text"])
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
            "provider_call_count": attempt_result["provider_call_count"],
            "meta": metadata,
        }

    raise RuntimeError("Unreachable RepoQA retry loop exit")


def run_repoqa_task_with_restarts(
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

    workspace_root, metadata = materialize_repoqa_workspace(
        env,
        run_id=run_id,
        task=task,
        release=release,
        runtime_task_id=runtime_task_id,
    )
    return run_repoqa_task_with_restarts_in_workspace(
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
    merged = merge_dicts(settings.get("schedule", {}) if isinstance(settings.get("schedule"), dict) else {}, profile.get("schedule", {}) if isinstance(profile.get("schedule"), dict) else {})
    return merge_dicts(merged, explicit)


def create_repoqa_run_manifest(
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
    run_defaults = settings.get("run") if isinstance(settings.get("run"), dict) else {}
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
        "benchmark": REPOQA_BENCHMARK_ID,
        "release": benchmark_manifest["release"],
        "language": benchmark_manifest["language"],
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


def run_repoqa_benchmark(
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
        run_manifest = create_repoqa_run_manifest(
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
        run_root = env.paths.results_root / "repoqa" / run_manifest["run_id"]
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
    completed: List[Dict[str, Any]] = []

    from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

    tasks = run_manifest.get("tasks") or []
    if not isinstance(tasks, list):
        raise ValueError("run manifest tasks must be a list")

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
                    workspace_root, _metadata = materialize_repoqa_workspace(
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
                        benchmark_id=REPOQA_BENCHMARK_ID,
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
                        run_repoqa_task_with_restarts,
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

    task_aggregates = aggregate_results_by_task_id(completed)
    for aggregate in task_aggregates:
        append_jsonl(task_aggregate_jsonl, aggregate)
    success_rates = [
        float(item["success_rate"])
        for item in task_aggregates
        if isinstance(item.get("success_rate"), (int, float))
    ]
    summary = {
        "run_id": run_manifest["run_id"],
        "benchmark": REPOQA_BENCHMARK_ID,
        "release": run_manifest["release"],
        "language": run_manifest["language"],
        "agent_id": run_manifest["agent_id"],
        "repeat_count": int(run_manifest.get("repeat_count") or 1),
        "manifest_task_count": len({str(item.get("task_id")) for item in tasks if isinstance(item, dict)}),
        "task_instance_count": len(tasks),
        "logical_task_count": len(task_aggregates),
        "completed_task_count": len(completed),
        "matched_task_count": sum(1 for item in completed if ((item.get("score") or {}).get("matched") is True)),
        "logical_tasks_with_all_successes": sum(
            1
            for item in task_aggregates
            if item.get("eligible_instance_count")
            and item.get("matched_instance_count") == item.get("eligible_instance_count")
        ),
        "logical_tasks_with_any_success": sum(
            1 for item in task_aggregates if int(item.get("matched_instance_count") or 0) > 0
        ),
        "logical_task_average_success_rate": (
            sum(success_rates) / len(success_rates) if success_rates else 0.0
        ),
        "accuracy": (
            sum(float((item.get("score") or {}).get("score") or 0.0) for item in completed) / len(completed)
            if completed
            else 0.0
        ),
        "results_jsonl": str(results_jsonl),
        "task_aggregate_jsonl": str(task_aggregate_jsonl),
        "run_manifest_path": str(run_manifest_path),
        "completed_at": isoformat_utc(),
        "benchmark_mode": "repoqa-agentic-custom",
    }
    write_json_atomic(summary_json, summary)
    return run_manifest_path


def run_repoqa_single_task_from_payload(
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
        metadata = {
            "benchmark": REPOQA_BENCHMARK_ID,
            "release": release,
            "task": task.to_manifest_dict(),
            "workspace_root": str(workspace_root),
            "repo_root": str(workspace_root / "repo"),
            "runtime_task_id": runtime_task_id,
            "created_at": isoformat_utc(),
        }
    return run_repoqa_task_with_restarts_in_workspace(
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
