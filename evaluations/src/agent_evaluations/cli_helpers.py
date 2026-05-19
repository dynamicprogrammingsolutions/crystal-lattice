from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Tuple

from .config_dir import apply_artifact_root, apply_profile_path_overrides, load_evaluation_environment
from .profiles import load_run_profile


def print_json(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def resolve_run_value(
    cli_value: Any,
    profile_payload: Dict[str, Any],
    key: str,
    *,
    default: Any = None,
) -> Any:
    if cli_value is not None:
        return cli_value
    if key in profile_payload:
        return profile_payload[key]
    return default


def schedule_overrides_from_args(args: argparse.Namespace) -> Dict[str, Any]:
    schedule: Dict[str, Any] = {}
    if args.window_minutes is not None:
        schedule["window_minutes"] = args.window_minutes
    if args.tasks_per_window is not None:
        schedule["tasks_per_window"] = args.tasks_per_window
    if args.max_parallel_tasks is not None:
        schedule["max_parallel_tasks"] = args.max_parallel_tasks
    if args.randomize_task_starts:
        schedule["randomize_task_starts"] = True
    if args.random_seed is not None:
        schedule["random_seed"] = args.random_seed
    return schedule


def resolve_runtime_backend(
    cli_value: Any,
    profile_payload: Dict[str, Any],
) -> str:
    raw = cli_value if cli_value is not None else profile_payload.get("runtime_backend")
    if not isinstance(raw, str) or not raw.strip():
        return "host"
    normalized = raw.strip().lower()
    if normalized not in {"host", "docker"}:
        raise ValueError("runtime backend must be 'host' or 'docker'")
    return normalized


def json_file(path: str | Path) -> Dict[str, Any]:
    loaded = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("JSON file must contain an object")
    return loaded


def load_run_environment(
    config_dir: str | Path,
    profile: str | None,
    *,
    artifact_root: str | Path | None = None,
) -> Tuple[Any, Dict[str, Any]]:
    env = load_evaluation_environment(config_dir)
    profile_payload = load_run_profile(env.paths.profiles_root, profile)
    env = apply_profile_path_overrides(env, profile_payload)
    env = apply_artifact_root(env, artifact_root)
    return env, profile_payload


def add_common_run_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config-dir", required=True)
    parser.add_argument("--agent-id")
    parser.add_argument("--profile")
    parser.add_argument("--run-manifest")
    parser.add_argument("--manifest-path")
    parser.add_argument("--artifact-root")
    parser.add_argument("--model")
    parser.add_argument("--repeat-count", type=int)
    parser.add_argument("--max-task-restarts", type=int)
    parser.add_argument("--window-minutes", type=int)
    parser.add_argument("--tasks-per-window", type=int)
    parser.add_argument("--max-parallel-tasks", type=int)
    parser.add_argument("--randomize-task-starts", action="store_true")
    parser.add_argument("--random-seed", type=int)
    parser.add_argument("--runtime-backend", choices=["host", "docker"])


def add_common_internal_run_single_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config-dir", required=True)
    parser.add_argument("--task-payload-path", required=True)
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--model")
    parser.add_argument("--max-task-restarts", type=int, default=2)