from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tarfile
import gzip
import sys

from agent_evaluations.container_backend import (
    DockerRuntimeConfig,
    build_docker_image,
    build_evaluations_wheel,
    run_repoqa_task_in_container,
)
from agent_evaluations.bundled_assets import create_git_tracked_source_bundle


def test_build_docker_image_constructs_expected_command(monkeypatch, tmp_path: Path) -> None:
    seen: dict[str, object] = {}

    def _fake_run(command, check, text, capture_output):
        seen["command"] = command
        seen["check"] = check
        seen["text"] = text
        seen["capture_output"] = capture_output
        return subprocess.CompletedProcess(command, 0, stdout="built", stderr="")

    monkeypatch.setattr("subprocess.run", _fake_run)
    prepared_context = tmp_path / "context" / "build" / "agent-evaluations-docker-context"
    runtime = DockerRuntimeConfig(
        enabled=True,
        image_tag="agent-evals:test",
        dockerfile=tmp_path / "Dockerfile",
        build_context=tmp_path / "context",
        source_bundle_path=tmp_path / "bundle" / "repo-source.tar.gz",
        evaluations_wheel_dir=tmp_path / "wheels",
        config_mount_path="/config",
        task_mount_path="/workspace",
        results_mount_path="/results",
        task_workdir="/workspace",
        extra_build_args=("--pull",),
    )
    runtime.dockerfile.write_text("FROM python:3.11-slim\n", encoding="utf-8")
    runtime.build_context.mkdir(parents=True, exist_ok=True)
    runtime.source_bundle_path.parent.mkdir(parents=True, exist_ok=True)
    tar_path = runtime.source_bundle_path.with_suffix("")
    with tarfile.open(tar_path, "w") as archive:
        for name in (
            "core/python/pyproject.toml",
            "application/python/pyproject.toml",
            "plugins/openai_responses/agent_plugin.json",
            "plugins/codex-tools/agent_plugin.json",
        ):
            file_path = tmp_path / name
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text("x\n", encoding="utf-8")
            archive.add(file_path, arcname=name)
    with tar_path.open("rb") as source, gzip.open(runtime.source_bundle_path, "wb") as destination:
        destination.write(source.read())
    tar_path.unlink()

    monkeypatch.setattr(
        "agent_evaluations.container_backend.create_git_tracked_source_bundle",
        lambda output_path, *, root, revision="HEAD": runtime.source_bundle_path,
    )
    fake_wheel = runtime.evaluations_wheel_dir / "agent_evaluations-0.1.0-py3-none-any.whl"
    fake_wheel.parent.mkdir(parents=True, exist_ok=True)
    fake_wheel.write_bytes(b"wheel")
    monkeypatch.setattr(
        "agent_evaluations.container_backend.build_evaluations_wheel",
        lambda output_dir, *, source_root=None: fake_wheel,
    )

    result = build_docker_image(runtime)

    command = seen["command"]
    assert isinstance(command, list)
    assert command[:4] == ["docker", "build", "-f", str(tmp_path / "context" / "build" / "agent-evaluations-docker-context" / "Dockerfile")]
    assert "agent-evals:test" in command
    assert str(tmp_path / "context" / "build" / "agent-evaluations-docker-context") == command[-1]
    assert result["image_tag"] == "agent-evals:test"
    assert result["source_bundle_path"] == str(runtime.source_bundle_path)
    assert result["evaluations_wheel_path"] == str(fake_wheel)


def test_run_repoqa_task_in_container_constructs_expected_command(monkeypatch, tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    workspace_root = tmp_path / "workspace"
    results_root = tmp_path / "results" / "repoqa" / "run-1"
    task_input = results_root / "task-inputs" / "task.json"
    task_output = results_root / "task-results" / "task.json"
    task_input.parent.mkdir(parents=True, exist_ok=True)
    task_output.parent.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(exist_ok=True)
    workspace_root.mkdir()

    task_output.write_text(json.dumps({"state": "completed", "score": {"score": 1.0}}), encoding="utf-8")

    seen: dict[str, object] = {}

    def _fake_run(command, check, text, capture_output):
        seen["command"] = command
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    monkeypatch.setattr("subprocess.run", _fake_run)
    runtime = DockerRuntimeConfig(
        enabled=True,
        image_tag="agent-evals:test",
        dockerfile=tmp_path / "Dockerfile",
        build_context=tmp_path / "context",
        source_bundle_path=tmp_path / "bundle" / "repo-source.tar.gz",
        evaluations_wheel_dir=tmp_path / "wheels",
        config_mount_path="/config",
        task_mount_path="/workspace",
        results_mount_path="/results",
        task_workdir="/workspace",
        container_env={"BUILTIN_PLUGINS": "/opt/ai-agent-platform/plugins"},
    )

    result = run_repoqa_task_in_container(
        runtime,
        host_config_dir=config_dir,
        host_workspace_root=workspace_root,
        host_results_root=results_root,
        host_task_payload_path=task_input,
        host_output_path=task_output,
        release="2024-06-23",
        agent_id="codex-openai",
        model_override="gpt-5.4-mini",
        max_task_restarts=2,
    )

    command = seen["command"]
    assert isinstance(command, list)
    assert command[:2] == ["docker", "run"]
    assert "agent-evals:test" in command
    assert "/results/task-inputs/task.json" in command
    assert "/results/task-results/task.json" in command
    assert result["state"] == "completed"
    assert result["_docker"]["image_tag"] == "agent-evals:test"


def test_create_git_tracked_source_bundle_includes_only_tracked_files(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_dir, check=True)
    (repo_dir / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    (repo_dir / "ignored.txt").write_text("ignored\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, check=True, capture_output=True, text=True)

    bundle_path = create_git_tracked_source_bundle(tmp_path / "bundle" / "repo-source.tar.gz", root=repo_dir)

    assert bundle_path.is_file()
    with tarfile.open(bundle_path, "r:gz") as archive:
        names = sorted(archive.getnames())

    assert "tracked.txt" in names
    assert "ignored.txt" not in names


def test_build_evaluations_wheel_returns_created_artifact(monkeypatch, tmp_path: Path) -> None:
    package_root = tmp_path / "evaluations"
    package_root.mkdir()
    wheel_dir = tmp_path / "wheels"
    seen: dict[str, object] = {}

    def _fake_run(command, check, text, capture_output, env):
        seen["command"] = command
        seen["env"] = env
        wheel = wheel_dir / "agent_evaluations-0.1.0-py3-none-any.whl"
        wheel.parent.mkdir(parents=True, exist_ok=True)
        wheel.write_bytes(b"wheel")
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    monkeypatch.setattr("subprocess.run", _fake_run)

    wheel_path = build_evaluations_wheel(wheel_dir, source_root=package_root)

    assert wheel_path == wheel_dir / "agent_evaluations-0.1.0-py3-none-any.whl"
    command = seen["command"]
    assert isinstance(command, list)
    assert command[:5] == [sys.executable, "-m", "pip", "wheel", "--no-deps"]
