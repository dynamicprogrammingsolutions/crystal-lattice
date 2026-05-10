from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile
from typing import Any, Dict, List, Mapping, Sequence

from .bundled_assets import create_git_tracked_source_bundle, repo_root
from .config_dir import EvaluationEnvironment, benchmark_settings, merge_dicts


def _resolve_path(raw_value: Any, *, base: Path, default: Path) -> Path:
    if not isinstance(raw_value, str) or not raw_value.strip():
        return default
    path = Path(raw_value.strip()).expanduser()
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def _string_list(raw_value: Any) -> List[str]:
    if not isinstance(raw_value, list):
        return []
    return [str(item) for item in raw_value if isinstance(item, str) and item]


def _string_mapping(raw_value: Any) -> Dict[str, str]:
    if not isinstance(raw_value, Mapping):
        return {}
    output: Dict[str, str] = {}
    for key, value in raw_value.items():
        if not isinstance(key, str) or not key:
            continue
        if not isinstance(value, str):
            continue
        output[key] = value
    return output


def _validate_source_bundle(source_bundle_path: Path) -> None:
    required_entries = {
        "core/python/pyproject.toml",
        "application/python/pyproject.toml",
        "plugins/openai_responses/agent_plugin.json",
        "plugins/codex-tools/agent_plugin.json",
    }
    with tarfile.open(source_bundle_path, "r:gz") as archive:
        names = set(archive.getnames())
    missing = sorted(entry for entry in required_entries if entry not in names)
    if missing:
        raise RuntimeError(
            "Tracked-files source bundle is missing required committed paths: "
            + ", ".join(missing)
        )


def build_evaluations_wheel(
    output_dir: Path,
    *,
    source_root: Path | None = None,
) -> Path:
    package_root = (source_root or (repo_root() / "evaluations")).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    command = [
        sys.executable,
        "-m",
        "pip",
        "wheel",
        "--no-deps",
        "--wheel-dir",
        str(output_dir),
        str(package_root),
    ]
    try:
        subprocess.run(
            command,
            check=True,
            text=True,
            capture_output=True,
            env=env,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "Failed to build agent_evaluations wheel.\n"
            f"Command: {' '.join(command)}\n"
            f"stdout:\n{exc.stdout}\n"
            f"stderr:\n{exc.stderr}"
        ) from exc
    candidates = sorted(
        output_dir.glob("agent_evaluations-*.whl"),
        key=lambda path: path.stat().st_mtime,
    )
    if not candidates:
        raise RuntimeError(
            f"Expected wheel build to produce an artifact under {output_dir}"
        )
    return candidates[-1]


@dataclass(frozen=True)
class DockerRuntimeConfig:
    enabled: bool
    image_tag: str
    dockerfile: Path
    build_context: Path
    source_bundle_path: Path
    evaluations_wheel_dir: Path
    config_mount_path: str
    task_mount_path: str
    results_mount_path: str
    task_workdir: str
    extra_build_args: tuple[str, ...] = ()
    extra_run_args: tuple[str, ...] = ()
    container_env: Dict[str, str] = field(default_factory=dict)


def resolve_docker_runtime_config(
    env: EvaluationEnvironment,
    *,
    profile_payload: Dict[str, Any],
) -> DockerRuntimeConfig:
    settings = benchmark_settings(env)
    base_cfg = settings.get("docker") if isinstance(settings.get("docker"), dict) else {}
    profile_cfg = profile_payload.get("docker") if isinstance(profile_payload.get("docker"), dict) else {}
    merged = merge_dicts(base_cfg, profile_cfg)

    root = repo_root()
    default_dockerfile = root / "evaluations" / "docker" / "RepoqaRunner.Dockerfile"
    default_context = root
    default_source_bundle_path = (
        root / "build" / "agent-evaluations" / "source-bundles" / "repo-source.tar.gz"
    )
    default_evaluations_wheel_dir = root / "build" / "agent-evaluations" / "wheels"

    enabled = bool(merged.get("enabled", False))
    image_tag = str(merged.get("image_tag") or "agent-evaluations:repoqa")
    dockerfile = _resolve_path(
        merged.get("dockerfile"),
        base=env.paths.config_dir,
        default=default_dockerfile,
    )
    build_context = _resolve_path(
        merged.get("build_context"),
        base=env.paths.config_dir,
        default=default_context,
    )
    source_bundle_path = _resolve_path(
        merged.get("source_bundle_path"),
        base=env.paths.config_dir,
        default=default_source_bundle_path,
    )
    evaluations_wheel_dir = _resolve_path(
        merged.get("evaluations_wheel_dir"),
        base=env.paths.config_dir,
        default=default_evaluations_wheel_dir,
    )
    config_mount_path = str(merged.get("config_mount_path") or "/config")
    task_mount_path = str(merged.get("task_mount_path") or "/workspace")
    results_mount_path = str(merged.get("results_mount_path") or "/results")
    task_workdir = str(merged.get("task_workdir") or task_mount_path)

    return DockerRuntimeConfig(
        enabled=enabled,
        image_tag=image_tag,
        dockerfile=dockerfile,
        build_context=build_context,
        source_bundle_path=source_bundle_path,
        evaluations_wheel_dir=evaluations_wheel_dir,
        config_mount_path=config_mount_path,
        task_mount_path=task_mount_path,
        results_mount_path=results_mount_path,
        task_workdir=task_workdir,
        extra_build_args=tuple(_string_list(merged.get("extra_build_args"))),
        extra_run_args=tuple(_string_list(merged.get("extra_run_args"))),
        container_env=_string_mapping(merged.get("container_env")),
    )


def container_path_for_host_path(
    host_path: Path,
    *,
    host_mount_root: Path,
    container_mount_root: str,
) -> str:
    relative = host_path.resolve().relative_to(host_mount_root.resolve())
    return str(PurePosixPath(container_mount_root) / PurePosixPath(relative.as_posix()))


def build_docker_image(runtime: DockerRuntimeConfig) -> Dict[str, Any]:
    source_bundle_path = create_git_tracked_source_bundle(
        runtime.source_bundle_path,
        root=runtime.build_context,
    )
    _validate_source_bundle(source_bundle_path)
    evaluations_wheel_path = build_evaluations_wheel(runtime.evaluations_wheel_dir)
    prepared_context = runtime.build_context / "build" / "agent-evaluations-docker-context"
    if prepared_context.exists():
        shutil.rmtree(prepared_context)
    prepared_context.mkdir(parents=True, exist_ok=True)

    dockerfile = prepared_context / "Dockerfile"
    dockerfile.write_text(
        runtime.dockerfile.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    source_bundle_copy = prepared_context / "repo-source.tar.gz"
    source_bundle_copy.write_bytes(source_bundle_path.read_bytes())
    wheel_copy = prepared_context / evaluations_wheel_path.name
    wheel_copy.write_bytes(evaluations_wheel_path.read_bytes())
    command = [
        "docker",
        "build",
        "-f",
        str(dockerfile),
        "-t",
        runtime.image_tag,
        *runtime.extra_build_args,
        str(prepared_context),
    ]
    try:
        completed = subprocess.run(
            command,
            check=True,
            text=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "Failed to build RepoQA Docker image.\n"
            f"Command: {' '.join(command)}\n"
            f"stdout:\n{exc.stdout}\n"
            f"stderr:\n{exc.stderr}"
        ) from exc
    return {
        "command": command,
        "image_tag": runtime.image_tag,
        "dockerfile": str(dockerfile),
        "build_context": str(prepared_context),
        "source_bundle_path": str(source_bundle_path),
        "evaluations_wheel_path": str(evaluations_wheel_path),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def run_repoqa_task_in_container(
    runtime: DockerRuntimeConfig,
    *,
    host_config_dir: Path,
    host_workspace_root: Path,
    host_results_root: Path,
    host_task_payload_path: Path,
    host_output_path: Path,
    release: str,
    agent_id: str,
    model_override: str | None,
    max_task_restarts: int,
) -> Dict[str, Any]:
    task_payload_path = container_path_for_host_path(
        host_task_payload_path,
        host_mount_root=host_results_root,
        container_mount_root=runtime.results_mount_path,
    )
    output_path = container_path_for_host_path(
        host_output_path,
        host_mount_root=host_results_root,
        container_mount_root=runtime.results_mount_path,
    )

    command = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{host_config_dir.resolve()}:{runtime.config_mount_path}",
        "-v",
        f"{host_workspace_root.resolve()}:{runtime.task_mount_path}",
        "-v",
        f"{host_results_root.resolve()}:{runtime.results_mount_path}",
        "-w",
        runtime.task_workdir,
    ]
    for key, value in runtime.container_env.items():
        command.extend(["-e", f"{key}={value}"])
    command.extend(runtime.extra_run_args)
    command.extend(
        [
            runtime.image_tag,
            "python",
            "-m",
            "agent_evaluations",
            "internal",
            "run-single",
            "repoqa",
            "--config-dir",
            runtime.config_mount_path,
            "--task-payload-path",
            task_payload_path,
            "--release",
            release,
            "--agent-id",
            agent_id,
            "--workspace-root",
            runtime.task_workdir,
            "--output-path",
            output_path,
            "--max-task-restarts",
            str(max_task_restarts),
        ]
    )
    if isinstance(model_override, str) and model_override.strip():
        command.extend(["--model", model_override.strip()])

    completed = subprocess.run(
        command,
        check=True,
        text=True,
        capture_output=True,
    )
    if not host_output_path.is_file():
        raise RuntimeError(
            "Docker task container completed without writing a result artifact"
        )
    payload = json.loads(host_output_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Docker task result artifact must be a JSON object")
    payload.setdefault("_docker", {})
    payload["_docker"].update(
        {
            "command": command,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "image_tag": runtime.image_tag,
        }
    )
    return payload