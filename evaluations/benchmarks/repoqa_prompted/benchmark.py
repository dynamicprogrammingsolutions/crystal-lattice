from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import sys
from typing import Any, Dict

from agent_evaluations.benchmark_registry import BenchmarkDefinition
from agent_evaluations.cli_helpers import (
    add_common_internal_run_single_arguments,
    add_common_run_arguments,
    json_file,
    load_run_environment,
    print_json,
    resolve_run_value,
    resolve_runtime_backend,
    schedule_overrides_from_args,
)
from agent_evaluations.config_dir import apply_profile_path_overrides, load_evaluation_environment
from agent_evaluations.container_backend import resolve_docker_runtime_config
from agent_evaluations.profiles import load_run_profile
from agent_evaluations.utils import write_json_atomic


def _load_logic_module() -> Any:
    module_name = "agent_evaluations_external_benchmark_repoqa_prompted_logic"
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


_logic = _load_logic_module()
RepoQATask = _logic.RepoQATask
DEFAULT_REPOQA_RELEASE = _logic.DEFAULT_REPOQA_RELEASE
build_repoqa_prompted_manifest = _logic.build_repoqa_prompted_manifest
build_repoqa_prompted_prompt = _logic.build_repoqa_prompted_prompt
default_repoqa_prompted_manifest_path = _logic.default_repoqa_prompted_manifest_path
materialize_repoqa_prompted_workspace = _logic.materialize_repoqa_prompted_workspace
parse_repoqa_prompted_answer = _logic.parse_repoqa_prompted_answer
repoqa_cache_path = _logic.repoqa_cache_path
download_repoqa_release = _logic.download_repoqa_release
run_repoqa_prompted_benchmark = _logic.run_repoqa_prompted_benchmark
run_repoqa_prompted_single_task_from_payload = _logic.run_repoqa_prompted_single_task_from_payload
run_repoqa_prompted_task_with_restarts = _logic.run_repoqa_prompted_task_with_restarts
run_benchmark_task_in_container = _logic.run_benchmark_task_in_container
warm_container_plugin_cache = _logic.warm_container_plugin_cache


def _manifest_profile(profile_payload: Dict[str, Any]) -> Dict[str, Any]:
    raw = profile_payload.get("manifest")
    if isinstance(raw, dict):
        return dict(raw)
    return {}


def _resolve_manifest_value(
    cli_value: Any,
    profile_payload: Dict[str, Any],
    key: str,
    *,
    default: Any = None,
) -> Any:
    if cli_value is not None:
        return cli_value
    manifest = _manifest_profile(profile_payload)
    if key in manifest:
        return manifest[key]
    if key in profile_payload:
        return profile_payload[key]
    return default


def _resolve_manifest_path(cli_value: Any, profile_payload: Dict[str, Any]) -> str | None:
    if isinstance(cli_value, str) and cli_value:
        return cli_value
    manifest = _manifest_profile(profile_payload)
    raw = manifest.get("manifest_path")
    return raw if isinstance(raw, str) and raw else None


def _load_manifest_for_run(
    env: Any,
    args: argparse.Namespace,
    profile_payload: Dict[str, Any],
) -> Dict[str, Any]:
    manifest_path = _resolve_manifest_path(args.manifest_path, profile_payload)
    if isinstance(manifest_path, str) and manifest_path:
        return json_file(manifest_path)
    release = str(_resolve_manifest_value(args.release, profile_payload, "release", default=DEFAULT_REPOQA_RELEASE))
    language = str(_resolve_manifest_value(args.language, profile_payload, "language", default="python"))
    limit = _resolve_manifest_value(args.limit, profile_payload, "limit")
    seed = int(_resolve_manifest_value(args.seed, profile_payload, "seed", default=1))
    download_repoqa_release(env, release=release, force=False)
    return build_repoqa_prompted_manifest(
        env,
        release=release,
        language=language,
        limit=limit,
        seed=seed,
    )


def _download_repoqa_prompted(args: argparse.Namespace) -> int:
    env = load_evaluation_environment(args.config_dir)
    profile_payload = load_run_profile(env.paths.profiles_root, args.profile)
    env = apply_profile_path_overrides(env, profile_payload)
    release = str(_resolve_manifest_value(args.release, profile_payload, "release", default=DEFAULT_REPOQA_RELEASE))
    path = download_repoqa_release(env, release=release, force=bool(args.force))
    print_json(
        {
            "benchmark": "repoqa-prompted",
            "release": release,
            "download_path": str(path),
        }
    )
    return 0


def _manifest_repoqa_prompted(args: argparse.Namespace) -> int:
    env = load_evaluation_environment(args.config_dir)
    profile_payload = load_run_profile(env.paths.profiles_root, args.profile)
    env = apply_profile_path_overrides(env, profile_payload)
    release = str(_resolve_manifest_value(args.release, profile_payload, "release", default=DEFAULT_REPOQA_RELEASE))
    language = str(_resolve_manifest_value(args.language, profile_payload, "language", default="python"))
    limit = _resolve_manifest_value(args.limit, profile_payload, "limit")
    seed = int(_resolve_manifest_value(args.seed, profile_payload, "seed", default=1))
    download_repoqa_release(env, release=release, force=False)
    manifest = build_repoqa_prompted_manifest(
        env,
        release=release,
        language=language,
        limit=limit,
        seed=seed,
    )
    profile_output_path = _resolve_manifest_value(None, profile_payload, "output_path")
    output_path = (
        Path(args.output_path).expanduser()
        if isinstance(args.output_path, str) and args.output_path
        else (
            Path(profile_output_path).expanduser()
            if isinstance(profile_output_path, str) and profile_output_path
            else default_repoqa_prompted_manifest_path(
                env,
                release=release,
                language=language,
                seed=seed,
                limit=limit,
            )
        )
    )
    write_json_atomic(output_path, manifest)
    print_json({"manifest_path": str(output_path), "task_count": manifest["task_count"]})
    return 0


def _run_repoqa_prompted(args: argparse.Namespace) -> int:
    env, profile_payload = load_run_environment(
        args.config_dir,
        args.profile,
        artifact_root=args.artifact_root,
    )
    agent_id = resolve_run_value(args.agent_id, profile_payload, "agent_id")
    if not isinstance(agent_id, str) or not agent_id:
        raise ValueError("agent_id must be provided via --agent-id or the run profile")
    runtime_backend = resolve_runtime_backend(args.runtime_backend, profile_payload)
    docker_runtime = (
        resolve_docker_runtime_config(env, profile_payload=profile_payload)
        if runtime_backend == "docker"
        else None
    )
    manifest = _load_manifest_for_run(env, args, profile_payload)
    resume_path = (
        Path(args.run_manifest).expanduser()
        if isinstance(args.run_manifest, str) and args.run_manifest
        else None
    )
    run_manifest_path = run_repoqa_prompted_benchmark(
        env,
        benchmark_manifest=manifest,
        agent_id=agent_id,
        profile_name=args.profile,
        profile_payload=profile_payload,
        schedule_overrides=schedule_overrides_from_args(args),
        model_override=resolve_run_value(args.model, profile_payload, "model"),
        repeat_count=int(resolve_run_value(args.repeat_count, profile_payload, "repeat_count", default=1)),
        max_task_restarts=int(
            resolve_run_value(args.max_task_restarts, profile_payload, "max_task_restarts", default=2)
        ),
        runtime_backend=runtime_backend,
        docker_runtime=docker_runtime,
        resume_run_manifest_path=resume_path,
    )
    print_json({"run_manifest_path": str(run_manifest_path)})
    return 0


def _internal_run_single_repoqa_prompted(args: argparse.Namespace) -> int:
    env = load_evaluation_environment(args.config_dir)
    task_payload = json_file(args.task_payload_path)
    workspace_root = Path(args.workspace_root).expanduser()
    output_path = Path(args.output_path).expanduser()
    run_id = output_path.parent.parent.name if output_path.parent.parent.name else "internal"
    result = run_repoqa_prompted_single_task_from_payload(
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
    parser = subparsers.add_parser("repoqa-prompted", help="Download RepoQA release for prompted runs")
    parser.add_argument("--config-dir", required=True)
    parser.add_argument("--profile")
    parser.add_argument("--release")
    parser.add_argument("--force", action="store_true")
    parser.set_defaults(func=_download_repoqa_prompted)


def register_manifest(subparsers: Any) -> None:
    parser = subparsers.add_parser("repoqa-prompted", help="Generate RepoQA prompted manifest")
    parser.add_argument("--config-dir", required=True)
    parser.add_argument("--profile")
    parser.add_argument("--release")
    parser.add_argument("--language")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--output-path")
    parser.set_defaults(func=_manifest_repoqa_prompted)


def register_run(subparsers: Any) -> None:
    parser = subparsers.add_parser("repoqa-prompted", help="Run RepoQA prompted benchmark")
    add_common_run_arguments(parser)
    parser.add_argument("--release")
    parser.add_argument("--language")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--seed", type=int)
    parser.set_defaults(func=_run_repoqa_prompted)


def register_internal_run_single(subparsers: Any) -> None:
    parser = subparsers.add_parser("repoqa-prompted", help=argparse.SUPPRESS)
    add_common_internal_run_single_arguments(parser)
    parser.add_argument("--release", default=DEFAULT_REPOQA_RELEASE)
    parser.set_defaults(func=_internal_run_single_repoqa_prompted)


BENCHMARK = BenchmarkDefinition(
    benchmark_id="repoqa-prompted",
    register_download=register_download,
    register_manifest=register_manifest,
    register_run=register_run,
    register_internal_run_single=register_internal_run_single,
)