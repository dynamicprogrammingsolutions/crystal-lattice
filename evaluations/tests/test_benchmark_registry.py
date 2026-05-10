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

    monkeypatch.setattr(
        "agent_evaluations.benchmarks.repoqa_agentic.load_evaluation_environment",
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
        "agent_evaluations.benchmarks.repoqa_agentic.run_repoqa_single_task_from_payload",
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