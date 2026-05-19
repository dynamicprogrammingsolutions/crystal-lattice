from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from agent_evaluations import cli
from agent_evaluations.benchmark_registry import BenchmarkDefinition, load_benchmarks


class _FakeEnv:
    pass


def test_load_benchmarks_discovers_repoqa_agentic() -> None:
    benchmarks = load_benchmarks()

    assert "repoqa" in benchmarks
    assert "repoqa-prompted" in benchmarks
    assert isinstance(benchmarks["repoqa"], BenchmarkDefinition)


def test_build_parser_registers_repoqa_subcommands() -> None:
    parser = cli.build_parser()

    download_args = parser.parse_args(["download", "repoqa", "--config-dir", "/tmp/config"])
    manifest_args = parser.parse_args(["manifest", "repoqa", "--config-dir", "/tmp/config"])
    run_args = parser.parse_args(["run", "repoqa", "--config-dir", "/tmp/config", "--agent-id", "fixture"])
    internal_args = parser.parse_args(
        [
            "internal",
            "run-single",
            "repoqa",
            "--config-dir",
            "/tmp/config",
            "--task-payload-path",
            "/tmp/task.json",
            "--agent-id",
            "fixture",
            "--workspace-root",
            "/tmp/workspace",
            "--output-path",
            "/tmp/out.json",
        ]
    )

    assert download_args.download_command == "repoqa"
    assert manifest_args.manifest_command == "repoqa"
    assert run_args.run_command == "repoqa"
    assert internal_args.internal_benchmark == "repoqa"


def test_internal_run_single_repoqa_dispatches_via_registered_benchmark(
    monkeypatch,
    tmp_path: Path,
) -> None:
    task_payload_path = tmp_path / "task.json"
    output_path = tmp_path / "task-results" / "result.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    task_payload_path.write_text(json.dumps({"task_id": "task-1"}), encoding="utf-8")
    seen: dict[str, object] = {}

    load_benchmarks()

    monkeypatch.setattr(
        "agent_evaluations_external_benchmark_repoqa_agentic.load_evaluation_environment",
        lambda _config_dir: _FakeEnv(),
    )

    def _fake_run_single(
        env,
        *,
        task_payload,
        run_id,
        release,
        workspace_root,
        agent_id,
        model_override,
        max_task_restarts,
    ):
        seen["env"] = env
        seen["task_payload"] = task_payload
        seen["run_id"] = run_id
        seen["release"] = release
        seen["workspace_root"] = workspace_root
        seen["agent_id"] = agent_id
        seen["model_override"] = model_override
        seen["max_task_restarts"] = max_task_restarts
        return {"state": "completed", "score": {"score": 1.0}}

    monkeypatch.setattr(
        "agent_evaluations_external_benchmark_repoqa_agentic.run_repoqa_single_task_from_payload",
        _fake_run_single,
    )

    exit_code = cli.main(
        [
            "internal",
            "run-single",
            "repoqa",
            "--config-dir",
            str(tmp_path / "config"),
            "--task-payload-path",
            str(task_payload_path),
            "--agent-id",
            "fixture-agent",
            "--workspace-root",
            str(tmp_path / "workspace"),
            "--output-path",
            str(output_path),
            "--max-task-restarts",
            "3",
        ]
    )

    assert exit_code == 0
    assert seen["task_payload"] == {"task_id": "task-1"}
    assert seen["agent_id"] == "fixture-agent"
    assert seen["max_task_restarts"] == 3
    assert json.loads(output_path.read_text(encoding="utf-8"))["state"] == "completed"


def test_load_benchmarks_rejects_duplicate_ids(monkeypatch) -> None:
    benchmark = load_benchmarks()["repoqa"]
    duplicate_modules = [
        SimpleNamespace(BENCHMARK=benchmark),
        SimpleNamespace(BENCHMARK=benchmark),
    ]
    monkeypatch.setattr(
        "agent_evaluations.benchmark_registry._benchmark_modules",
        lambda: duplicate_modules,
    )

    with pytest.raises(ValueError, match="Duplicate benchmark id registered"):
        load_benchmarks()


def test_manifest_repoqa_prompted_uses_profile_manifest_settings(
    monkeypatch,
    tmp_path: Path,
) -> None:
    config_dir = tmp_path / "config"
    profiles_dir = config_dir / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "config.json").write_text("{}\n", encoding="utf-8")
    (profiles_dir / "slice.json").write_text(
        json.dumps(
            {
                "manifest": {
                    "release": "2024-06-23",
                    "language": "all",
                    "limit": 10,
                    "seed": 7,
                }
            }
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "manifest.json"
    seen: dict[str, object] = {}

    load_benchmarks()

    def _fake_download(env, *, release, force):
        seen["download_release"] = release
        seen["download_force"] = force
        return tmp_path / "cache.json.gz"

    def _fake_build(env, *, release, language, limit, seed):
        seen["release"] = release
        seen["language"] = language
        seen["limit"] = limit
        seen["seed"] = seed
        return {"task_count": 0, "tasks": []}

    monkeypatch.setattr(
        "agent_evaluations_external_benchmark_repoqa_prompted.download_repoqa_release",
        _fake_download,
    )
    monkeypatch.setattr(
        "agent_evaluations_external_benchmark_repoqa_prompted.build_repoqa_prompted_manifest",
        _fake_build,
    )

    exit_code = cli.main(
        [
            "manifest",
            "repoqa-prompted",
            "--config-dir",
            str(config_dir),
            "--profile",
            "slice",
            "--output-path",
            str(output_path),
        ]
    )

    assert exit_code == 0
    assert seen["download_release"] == "2024-06-23"
    assert seen["release"] == "2024-06-23"
    assert seen["language"] == "all"
    assert seen["limit"] == 10
    assert seen["seed"] == 7


def test_download_repoqa_prompted_uses_profile_release(
    monkeypatch,
    tmp_path: Path,
) -> None:
    config_dir = tmp_path / "config"
    profiles_dir = config_dir / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "config.json").write_text("{}\n", encoding="utf-8")
    (profiles_dir / "slice.json").write_text(
        json.dumps({"manifest": {"release": "2024-06-23"}}),
        encoding="utf-8",
    )
    seen: dict[str, object] = {}

    load_benchmarks()

    def _fake_download(env, *, release, force):
        seen["release"] = release
        seen["force"] = force
        return tmp_path / "cache.json.gz"

    monkeypatch.setattr(
        "agent_evaluations_external_benchmark_repoqa_prompted.download_repoqa_release",
        _fake_download,
    )

    exit_code = cli.main(
        [
            "download",
            "repoqa-prompted",
            "--config-dir",
            str(config_dir),
            "--profile",
            "slice",
        ]
    )

    assert exit_code == 0
    assert seen["release"] == "2024-06-23"
    assert seen["force"] is False