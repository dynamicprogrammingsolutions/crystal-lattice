from __future__ import annotations

import argparse
from pathlib import Path
import tempfile
from typing import Any, Dict

from .benchmark_registry import load_benchmarks
from .cli_helpers import print_json, resolve_run_value
from .container_backend import (
    build_docker_image,
    resolve_docker_runtime_config,
    warm_container_plugin_cache,
)
from .config_dir import load_evaluation_environment
from .profiles import load_run_profile


def _status_for_agent(app: Any, agent_id: str) -> Dict[str, Any]:
    _core, _base_config, session = app.create_session(agent_id)
    try:
        return app.execute_application_action("chatgpt_auth", "show_account_status", {"session_id": session.session_id})
    finally:
        app.delete_session(session.session_id)


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
    print_json({"auth_status": auth_status})
    return 0


def _auth_status(args: argparse.Namespace) -> int:
    env = load_evaluation_environment(args.config_dir)
    app = env.build_application()
    if isinstance(args.agent_id, str) and args.agent_id:
        result = _status_for_agent(app, args.agent_id)
    else:
        result = app.execute_application_action("chatgpt_auth", "check_status", {})
    print_json(result if isinstance(result, dict) else {"result": result})
    return 0


def _auth_logout(args: argparse.Namespace) -> int:
    env = load_evaluation_environment(args.config_dir)
    app = env.build_application()
    result = app.execute_application_action("chatgpt_auth", "logout", {})
    print_json(result if isinstance(result, dict) else {"result": result})
    return 0


def _container_build(args: argparse.Namespace) -> int:
    env = load_evaluation_environment(args.config_dir)
    profile_payload = load_run_profile(env.paths.profiles_root, args.profile)
    runtime = resolve_docker_runtime_config(env, profile_payload=profile_payload)
    result = build_docker_image(runtime)
    print_json(
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


def _container_warm_cache(args: argparse.Namespace) -> int:
    env = load_evaluation_environment(args.config_dir)
    profile_payload = load_run_profile(env.paths.profiles_root, args.profile)
    runtime = resolve_docker_runtime_config(env, profile_payload=profile_payload)
    agent_id = resolve_run_value(args.agent_id, profile_payload, "agent_id")
    result = warm_container_plugin_cache(
        runtime,
        host_config_dir=env.paths.config_dir,
        agent_id=agent_id if isinstance(agent_id, str) and agent_id else None,
    )
    print_json(result)
    return 0


def _internal_warm_cache(args: argparse.Namespace) -> int:
    env = load_evaluation_environment(args.config_dir)
    with tempfile.TemporaryDirectory(prefix="agent-evaluations-warm-cache-") as temp_root:
        app = env.build_application(session_root=Path(temp_root) / "sessions")
        if isinstance(args.agent_id, str) and args.agent_id:
            _core, _base_config, session = app.create_session_ephemeral(args.agent_id)
            _ = session
    print_json(
        {
            "state": "warmed",
            "config_dir": str(env.paths.config_dir),
            "agent_id": args.agent_id,
        }
    )
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

    manifest = subparsers.add_parser("manifest", help="Generate benchmark manifests")
    manifest_sub = manifest.add_subparsers(dest="manifest_command", required=True)

    container = subparsers.add_parser("container", help="Container image commands")
    container_sub = container.add_subparsers(dest="container_command", required=True)
    container_build = container_sub.add_parser("build", help="Build the benchmark runner image")
    container_build.add_argument("--config-dir", required=True)
    container_build.add_argument("--profile")
    container_build.set_defaults(func=_container_build)
    container_warm_cache = container_sub.add_parser(
        "warm-cache",
        help="Warm plugin cache in the benchmark runner container",
    )
    container_warm_cache.add_argument("--config-dir", required=True)
    container_warm_cache.add_argument("--profile")
    container_warm_cache.add_argument("--agent-id")
    container_warm_cache.set_defaults(func=_container_warm_cache)

    run = subparsers.add_parser("run", help="Run benchmark tasks")
    run_sub = run.add_subparsers(dest="run_command", required=True)

    internal = subparsers.add_parser("internal", help=argparse.SUPPRESS)
    internal_sub = internal.add_subparsers(dest="internal_command", required=True)
    internal_warm_cache = internal_sub.add_parser("warm-cache", help=argparse.SUPPRESS)
    internal_warm_cache.add_argument("--config-dir", required=True)
    internal_warm_cache.add_argument("--agent-id")
    internal_warm_cache.set_defaults(func=_internal_warm_cache)
    internal_run_single = internal_sub.add_parser("run-single", help=argparse.SUPPRESS)
    internal_run_single_sub = internal_run_single.add_subparsers(dest="internal_benchmark", required=True)

    for benchmark in load_benchmarks().values():
        benchmark.register_download(download_sub)
        benchmark.register_manifest(manifest_sub)
        benchmark.register_run(run_sub)
        benchmark.register_internal_run_single(internal_run_single_sub)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))