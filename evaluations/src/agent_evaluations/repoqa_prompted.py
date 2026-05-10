from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from agent_app.config import resolve_request_config
from agent_core import Session

from .config_dir import EvaluationEnvironment, benchmark_settings, merge_dicts
from .container_backend import (
    DockerRuntimeConfig,
    run_benchmark_task_in_container,
)
from .repoqa import (
    DEFAULT_REPOQA_RELEASE,
    REPOQA_RELEASE_URL_TEMPLATE,
    RepoQATask,
    _count_tool_calls,
    _extract_final_assistant_text,
    download_repoqa_release,
    iter_repoqa_tasks,
    load_repoqa_dataset,
    score_repoqa_answer,
)
from .scheduler import plan_task_starts, policy_from_config, sleep_until
from .utils import append_jsonl, isoformat_utc, utc_now, write_json, write_json_atomic


REPOQA_PROMPTED_BENCHMARK_ID = "repoqa-prompted"


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
    tasks = list(iter_repoqa_tasks(dataset, language=language))
    if seed:
        import random

        rng = random.Random(seed)
        rng.shuffle(tasks)
    if isinstance(limit, int) and limit > 0:
        tasks = tasks[:limit]

    return {
        "benchmark": REPOQA_PROMPTED_BENCHMARK_ID,
        "release": release,
        "language": language,
        "seed": seed,
        "limit": limit,
        "created_at": isoformat_utc(),
        "task_count": len(tasks),
        "tasks": [task.to_manifest_dict() for task in tasks],
    }


def _workspace_root_for_run(env: EvaluationEnvironment, run_id: str, task_id: str) -> Path:
    return env.paths.workspace_root / REPOQA_PROMPTED_BENCHMARK_ID / run_id / task_id


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
    context_budget_chars = int(settings.get("context_budget_chars") or 120000)
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
) -> Tuple[Path, Dict[str, Any]]:
    workspace_root = _workspace_root_for_run(env, run_id, task.task_id)
    if workspace_root.exists():
        import shutil

        shutil.rmtree(workspace_root)
    workspace_root.mkdir(parents=True, exist_ok=True)
    prompt, prompt_meta = build_repoqa_prompted_prompt(env, task=task, release=release)
    (workspace_root / "PROMPT.txt").write_text(prompt, encoding="utf-8")
    metadata = {
        **prompt_meta,
        "workspace_root": str(workspace_root),
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

    if task.symbol in candidate:
        symbol_index = candidate.find(task.symbol)
        line_start = candidate.rfind("\n", 0, symbol_index)
        candidate = candidate[line_start + 1 :].strip() if line_start >= 0 else candidate.strip()

    symbol = task.symbol
    python_match = re.search(r"^\s*(?:async\s+def|def)\s+([A-Za-z_][A-Za-z0-9_]*)", candidate, flags=re.MULTILINE)
    if python_match:
        symbol = python_match.group(1)
    else:
        generic_match = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", candidate)
        if generic_match:
            symbol = generic_match.group(1)

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
    return {
        "events": events,
        "final_session": final_session,
        "final_assistant_text": _extract_final_assistant_text(events),
        "tool_call_count": _count_tool_calls(final_session),
        "effective_tool_schema_count": len(effective_tool_schemas),
        "provider_call_count": None,
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
) -> Dict[str, Any]:
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
                    "workspace_root": str(workspace_root),
                    "attempts": attempts,
                    "state": "failed_before_turn_completed",
                    "error": last_error,
                    "score": {
                        "matched": False,
                        "path_match": False,
                        "symbol_match": False,
                        "code_match": False,
                        "score": 0.0,
                    },
                    "parsed_answer": None,
                    "parse_error": None,
                    "final_assistant_text": "",
                    "tool_call_count": 0,
                    "effective_tool_schema_count": None,
                    "provider_call_count": None,
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
            "workspace_root": str(workspace_root),
            "attempts": attempts,
            "state": "completed",
            "error": None,
            "score": score,
            "parsed_answer": parsed_answer,
            "parse_error": parse_error,
            "final_assistant_text": attempt_result["final_assistant_text"],
            "tool_call_count": attempt_result["tool_call_count"],
            "effective_tool_schema_count": attempt_result["effective_tool_schema_count"],
            "provider_call_count": attempt_result["provider_call_count"],
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
    workspace_root, metadata = materialize_repoqa_prompted_workspace(
        env,
        run_id=run_id,
        task=task,
        release=release,
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
    runtime_backend: str,
    docker_runtime: DockerRuntimeConfig | None,
) -> Dict[str, Any]:
    settings = benchmark_settings(env)
    schedule_config = _normalize_run_schedule(settings, profile_payload, schedule_overrides)
    policy = policy_from_config(schedule_config, default_seed=int(benchmark_manifest.get("seed") or 0))
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    planned_starts = plan_task_starts(
        task_count=len(benchmark_manifest.get("tasks") or []),
        anchor=utc_now(),
        policy=policy,
    )
    return {
        "run_id": run_id,
        "created_at": isoformat_utc(),
        "benchmark": REPOQA_PROMPTED_BENCHMARK_ID,
        "release": benchmark_manifest["release"],
        "language": benchmark_manifest["language"],
        "agent_id": agent_id,
        "profile_name": profile_name,
        "profile": profile_payload,
        "model_override": model_override,
        "max_task_restarts": max_task_restarts,
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
            for task, start in zip(benchmark_manifest.get("tasks") or [], planned_starts)
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
            runtime_backend=runtime_backend,
            docker_runtime=docker_runtime,
        )
        run_root = env.paths.results_root / REPOQA_PROMPTED_BENCHMARK_ID / run_manifest["run_id"]
        run_root.mkdir(parents=True, exist_ok=True)
        run_manifest_path = run_root / "run-manifest.json"
        write_json_atomic(run_manifest_path, run_manifest)

    run_root = run_manifest_path.parent
    results_jsonl = run_root / "results.jsonl"
    summary_json = run_root / "summary.json"
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
                    workspace_root, _metadata = materialize_repoqa_prompted_workspace(
                        env,
                        run_id=str(run_manifest["run_id"]),
                        task=task,
                        release=str(run_manifest["release"]),
                    )
                    task_input_dir = run_root / "task-inputs"
                    task_result_dir = run_root / "task-results"
                    task_input_dir.mkdir(parents=True, exist_ok=True)
                    task_result_dir.mkdir(parents=True, exist_ok=True)
                    task_input_path = task_input_dir / f"{task.task_id}.json"
                    task_output_path = task_result_dir / f"{task.task_id}.json"
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

    summary = {
        "run_id": run_manifest["run_id"],
        "benchmark": REPOQA_PROMPTED_BENCHMARK_ID,
        "release": run_manifest["release"],
        "language": run_manifest["language"],
        "agent_id": run_manifest["agent_id"],
        "completed_task_count": len(completed),
        "matched_task_count": sum(1 for item in completed if ((item.get("score") or {}).get("matched") is True)),
        "accuracy": (
            sum(float((item.get("score") or {}).get("score") or 0.0) for item in completed) / len(completed)
            if completed
            else 0.0
        ),
        "results_jsonl": str(results_jsonl),
        "run_manifest_path": str(run_manifest_path),
        "completed_at": isoformat_utc(),
        "benchmark_mode": "repoqa-prompted-custom",
    }
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
    )