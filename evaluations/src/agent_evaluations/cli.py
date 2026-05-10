from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from .container_backend import build_docker_image, resolve_docker_runtime_config
from .config_dir import load_evaluation_environment
from .profiles import load_run_profile
from .repoqa import (
    DEFAULT_REPOQA_RELEASE,
    build_repoqa_manifest,
    default_repoqa_manifest_path,
    download_repoqa_release,
    run_repoqa_benchmark,
    run_repoqa_single_task_from_payload,
)
from .utils import write_json_atomic


def _print_json(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _status_for_agent(app: Any, agent_id: str) -> Dict[str, Any]:
    _core, _base_config, session = app.create_session(agent_id)
    try:
        return app.execute_application_action(
            "chatgpt_auth",
            "show_account_status",
            {"session_id": session.session_id},
        )
    finally:
        app.delete_session(session.session_id)


def _resolve_run_value(
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


def _auth_login(args: argparse.Namespace) -> int:
    env = load_evaluation_environment(args.config_dir)
    app = env.build_application()
    result = app.execute_application_action("chatgpt_auth", "login_start", {})
    display = result.get("display") if isinstance(result, dict) else None
    if isinstance(display, dict):
        body = display.get("body")
        if isinstance(body, str) and body.strip():
            print(body)
    auth_status = result.get("auth_status") if isinstance(result, dict) else None
    _print_json({"auth_status": auth_status})
    return 0


def _auth_status(args: argparse.Namespace) -> int:
    env = load_evaluation_environment(args.config_dir)
    app = env.build_application()
    if isinstance(args.agent_id, str) and args.agent_id:
        result = _status_for_agent(app, args.agent_id)
    else:
        result = app.execute_application_action("chatgpt_auth", "check_status", {})
    _print_json(result if isinstance(result, dict) else {"result": result})
    return 0


def _auth_logout(args: argparse.Namespace) -> int:
    env = load_evaluation_environment(args.config_dir)
    app = env.build_application()
    result = app.execute_application_action("chatgpt_auth", "logout", {})
    _print_json(result if isinstance(result, dict) else {"result": result})
    return 0


def _download_repoqa(args: argparse.Namespace) -> int:
    env = load_evaluation_environment(args.config_dir)
    path = download_repoqa_release(env, release=args.release, force=bool(args.force))
    _print_json(
        {
            "benchmark": "repoqa",
            "release": args.release,
            "download_path": str(path),
        }
    )
    return 0


def _manifest_repoqa(args: argparse.Namespace) -> int:
    env = load_evaluation_environment(args.config_dir)
    download_repoqa_release(env, release=args.release, force=False)
    manifest = build_repoqa_manifest(
        env,
        release=args.release,
        language=args.language,
        limit=args.limit,
        seed=args.seed,
    )
    output_path = (
        Path(args.output_path).expanduser()
        if isinstance(args.output_path, str) and args.output_path
        else default_repoqa_manifest_path(
            env,
            release=args.release,
            language=args.language,
            seed=args.seed,
            limit=args.limit,
        )
    )
    write_json_atomic(output_path, manifest)
    _print_json({"manifest_path": str(output_path), "task_count": manifest["task_count"]})
    return 0


def _schedule_overrides_from_args(args: argparse.Namespace) -> Dict[str, Any]:
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


def _load_manifest_for_run(env: Any, args: argparse.Namespace) -> Dict[str, Any]:
    if isinstance(args.manifest_path, str) and args.manifest_path:
        return json.loads(Path(args.manifest_path).expanduser().read_text(encoding="utf-8"))
    download_repoqa_release(env, release=args.release, force=False)
    return build_repoqa_manifest(
        env,
        release=args.release,
        language=args.language,
        limit=args.limit,
        seed=args.seed,
    )


def _resolve_runtime_backend(
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


def _run_repoqa(args: argparse.Namespace) -> int:
    env = load_evaluation_environment(args.config_dir)
    profile_payload = load_run_profile(env.paths.profiles_root, args.profile)
    agent_id = _resolve_run_value(args.agent_id, profile_payload, "agent_id")
    if not isinstance(agent_id, str) or not agent_id:
        raise ValueError("agent_id must be provided via --agent-id or the run profile")
    runtime_backend = _resolve_runtime_backend(args.runtime_backend, profile_payload)
    docker_runtime = (
        resolve_docker_runtime_config(env, profile_payload=profile_payload)
        if runtime_backend == "docker"
        else None
    )
    manifest = _load_manifest_for_run(env, args)
    resume_path = (
        Path(args.run_manifest).expanduser()
        if isinstance(args.run_manifest, str) and args.run_manifest
        else None
    )
    run_manifest_path = run_repoqa_benchmark(
        env,
        benchmark_manifest=manifest,
        agent_id=agent_id,
        profile_name=args.profile,
        profile_payload=profile_payload,
        schedule_overrides=_schedule_overrides_from_args(args),
        model_override=_resolve_run_value(args.model, profile_payload, "model"),
        max_task_restarts=int(
            _resolve_run_value(args.max_task_restarts, profile_payload, "max_task_restarts", default=2)
        ),
        runtime_backend=runtime_backend,
        docker_runtime=docker_runtime,
        resume_run_manifest_path=resume_path,
    )
    _print_json({"run_manifest_path": str(run_manifest_path)})
    return 0


def _container_build(args: argparse.Namespace) -> int:
    env = load_evaluation_environment(args.config_dir)
    profile_payload = load_run_profile(env.paths.profiles_root, args.profile)
    runtime = resolve_docker_runtime_config(env, profile_payload=profile_payload)
    result = build_docker_image(runtime)
    _print_json(
        {
            "image_tag": result["image_tag"],
            "dockerfile": result["dockerfile"],
            "build_context": result["build_context"],
            "source_bundle_path": result["source_bundle_path"],
            "evaluations_wheel_path": result["evaluations_wheel_path"],
            "command": result["command"],
        }
    )
    return 0


def _internal_run_single_repoqa(args: argparse.Namespace) -> int:
    env = load_evaluation_environment(args.config_dir)
    task_payload = json.loads(Path(args.task_payload_path).expanduser().read_text(encoding="utf-8"))
    if not isinstance(task_payload, dict):
        raise ValueError("task payload must be a JSON object")
    workspace_root = Path(args.workspace_root).expanduser()
    output_path = Path(args.output_path).expanduser()
    run_id = output_path.parent.parent.name if output_path.parent.parent.name else "internal"
    result = run_repoqa_single_task_from_payload(
        env,
        task_payload=task_payload,
        run_id=run_id,
        release=args.release,
        workspace_root=workspace_root,
        agent_id=args.agent_id,
        model_override=args.model,
        max_task_restarts=args.max_task_restarts,
    )
    write_json_atomic(output_path, result)
    _print_json({"output_path": str(output_path), "state": result.get("state")})
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Agentic evaluation CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    auth = subparsers.add_parser("auth", help="ChatGPT auth commands")
    auth_sub = auth.add_subparsers(dest="auth_command", required=True)

    login = auth_sub.add_parser("login-chatgpt", help="Start ChatGPT login")
    login.add_argument("--config-dir", required=True)
    login.set_defaults(func=_auth_login)

    status = auth_sub.add_parser("status", help="Show ChatGPT auth status")
    status.add_argument("--config-dir", required=True)
    status.add_argument("--agent-id")
    status.set_defaults(func=_auth_status)

    logout = auth_sub.add_parser("logout", help="Log out of ChatGPT")
    logout.add_argument("--config-dir", required=True)
    logout.set_defaults(func=_auth_logout)

    download = subparsers.add_parser("download", help="Download benchmark assets")
    download_sub = download.add_subparsers(dest="download_command", required=True)
    download_repoqa = download_sub.add_parser("repoqa", help="Download RepoQA release")
    download_repoqa.add_argument("--config-dir", required=True)
    download_repoqa.add_argument("--release", default=DEFAULT_REPOQA_RELEASE)
    download_repoqa.add_argument("--force", action="store_true")
    download_repoqa.set_defaults(func=_download_repoqa)

    manifest = subparsers.add_parser("manifest", help="Generate benchmark manifests")
    manifest_sub = manifest.add_subparsers(dest="manifest_command", required=True)
    manifest_repoqa = manifest_sub.add_parser("repoqa", help="Generate RepoQA manifest")
    manifest_repoqa.add_argument("--config-dir", required=True)
    manifest_repoqa.add_argument("--release", default=DEFAULT_REPOQA_RELEASE)
    manifest_repoqa.add_argument("--language", default="python")
    manifest_repoqa.add_argument("--limit", type=int)
    manifest_repoqa.add_argument("--seed", type=int, default=1)
    manifest_repoqa.add_argument("--output-path")
    manifest_repoqa.set_defaults(func=_manifest_repoqa)

    container = subparsers.add_parser("container", help="Container image commands")
    container_sub = container.add_subparsers(dest="container_command", required=True)
    container_build = container_sub.add_parser("build", help="Build the benchmark runner image")
    container_build.add_argument("--config-dir", required=True)
    container_build.add_argument("--profile")
    container_build.set_defaults(func=_container_build)

    run = subparsers.add_parser("run", help="Run benchmark tasks")
    run_sub = run.add_subparsers(dest="run_command", required=True)
    run_repoqa = run_sub.add_parser("repoqa", help="Run RepoQA benchmark")
    run_repoqa.add_argument("--config-dir", required=True)
    run_repoqa.add_argument("--agent-id")
    run_repoqa.add_argument("--profile")
    run_repoqa.add_argument("--run-manifest")
    run_repoqa.add_argument("--manifest-path")
    run_repoqa.add_argument("--release", default=DEFAULT_REPOQA_RELEASE)
    run_repoqa.add_argument("--language", default="python")
    run_repoqa.add_argument("--limit", type=int)
    run_repoqa.add_argument("--seed", type=int, default=1)
    run_repoqa.add_argument("--model")
    run_repoqa.add_argument("--max-task-restarts", type=int)
    run_repoqa.add_argument("--window-minutes", type=int)
    run_repoqa.add_argument("--tasks-per-window", type=int)
    run_repoqa.add_argument("--max-parallel-tasks", type=int)
    run_repoqa.add_argument("--randomize-task-starts", action="store_true")
    run_repoqa.add_argument("--random-seed", type=int)
    run_repoqa.add_argument("--runtime-backend", choices=["host", "docker"])
    run_repoqa.set_defaults(func=_run_repoqa)

    internal = subparsers.add_parser("internal", help=argparse.SUPPRESS)
    internal_sub = internal.add_subparsers(dest="internal_command", required=True)
    internal_run_single = internal_sub.add_parser("run-single", help=argparse.SUPPRESS)
    internal_run_single_sub = internal_run_single.add_subparsers(dest="internal_benchmark", required=True)
    internal_repoqa = internal_run_single_sub.add_parser("repoqa", help=argparse.SUPPRESS)
    internal_repoqa.add_argument("--config-dir", required=True)
    internal_repoqa.add_argument("--task-payload-path", required=True)
    internal_repoqa.add_argument("--release", default=DEFAULT_REPOQA_RELEASE)
    internal_repoqa.add_argument("--agent-id", required=True)
    internal_repoqa.add_argument("--workspace-root", required=True)
    internal_repoqa.add_argument("--output-path", required=True)
    internal_repoqa.add_argument("--model")
    internal_repoqa.add_argument("--max-task-restarts", type=int, default=2)
    internal_repoqa.set_defaults(func=_internal_run_single_repoqa)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))