from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from agent_evaluations.benchmark_registry import BenchmarkDefinition
from agent_evaluations.cli_helpers import (
    add_common_internal_run_single_arguments,
    add_common_run_arguments,
    json_file,
    print_json,
    resolve_run_value,
    resolve_runtime_backend,
    schedule_overrides_from_args,
)
from agent_evaluations.config_dir import load_evaluation_environment
from agent_evaluations.container_backend import (
    resolve_docker_runtime_config,
)
from agent_evaluations.profiles import load_run_profile
from agent_evaluations.repoqa import (
    DEFAULT_REPOQA_RELEASE,
    build_repoqa_manifest,
    default_repoqa_manifest_path,
    download_repoqa_release,
    run_repoqa_benchmark,
    run_repoqa_single_task_from_payload,
)
from agent_evaluations.utils import write_json_atomic


def _load_manifest_for_run(env: Any, args: argparse.Namespace) -> Dict[str, Any]:
    if isinstance(args.manifest_path, str) and args.manifest_path:
        return json_file(args.manifest_path)
    download_repoqa_release(env, release=args.release, force=False)
    return build_repoqa_manifest(
        env,
        release=args.release,
        language=args.language,
        limit=args.limit,
        seed=args.seed,
    )


def _download_repoqa(args: argparse.Namespace) -> int:
    env = load_evaluation_environment(args.config_dir)
    path = download_repoqa_release(env, release=args.release, force=bool(args.force))
    print_json(
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
    print_json({"manifest_path": str(output_path), "task_count": manifest["task_count"]})
    return 0


def _run_repoqa(args: argparse.Namespace) -> int:
    env = load_evaluation_environment(args.config_dir)
    profile_payload = load_run_profile(env.paths.profiles_root, args.profile)
    agent_id = resolve_run_value(args.agent_id, profile_payload, "agent_id")
    if not isinstance(agent_id, str) or not agent_id:
        raise ValueError("agent_id must be provided via --agent-id or the run profile")
    runtime_backend = resolve_runtime_backend(args.runtime_backend, profile_payload)
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
        schedule_overrides=schedule_overrides_from_args(args),
        model_override=resolve_run_value(args.model, profile_payload, "model"),
        max_task_restarts=int(
            resolve_run_value(args.max_task_restarts, profile_payload, "max_task_restarts", default=2)
        ),
        runtime_backend=runtime_backend,
        docker_runtime=docker_runtime,
        resume_run_manifest_path=resume_path,
    )
    print_json({"run_manifest_path": str(run_manifest_path)})
    return 0


def _internal_run_single_repoqa(args: argparse.Namespace) -> int:
    env = load_evaluation_environment(args.config_dir)
    task_payload = json_file(args.task_payload_path)
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
    print_json({"output_path": str(output_path), "state": result.get("state")})
    return 0


def register_download(subparsers: Any) -> None:
    parser = subparsers.add_parser("repoqa", help="Download RepoQA release")
    parser.add_argument("--config-dir", required=True)
    parser.add_argument("--release", default=DEFAULT_REPOQA_RELEASE)
    parser.add_argument("--force", action="store_true")
    parser.set_defaults(func=_download_repoqa)


def register_manifest(subparsers: Any) -> None:
    parser = subparsers.add_parser("repoqa", help="Generate RepoQA manifest")
    parser.add_argument("--config-dir", required=True)
    parser.add_argument("--release", default=DEFAULT_REPOQA_RELEASE)
    parser.add_argument("--language", default="python")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--output-path")
    parser.set_defaults(func=_manifest_repoqa)


def register_run(subparsers: Any) -> None:
    parser = subparsers.add_parser("repoqa", help="Run RepoQA benchmark")
    add_common_run_arguments(parser)
    parser.add_argument("--release", default=DEFAULT_REPOQA_RELEASE)
    parser.add_argument("--language", default="python")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--seed", type=int, default=1)
    parser.set_defaults(func=_run_repoqa)


def register_internal_run_single(subparsers: Any) -> None:
    parser = subparsers.add_parser("repoqa", help=argparse.SUPPRESS)
    add_common_internal_run_single_arguments(parser)
    parser.add_argument("--release", default=DEFAULT_REPOQA_RELEASE)
    parser.set_defaults(func=_internal_run_single_repoqa)


BENCHMARK = BenchmarkDefinition(
    benchmark_id="repoqa",
    register_download=register_download,
    register_manifest=register_manifest,
    register_run=register_run,
    register_internal_run_single=register_internal_run_single,
)