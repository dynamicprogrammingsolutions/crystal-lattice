from __future__ import annotations

from datetime import datetime, timedelta, timezone
import gzip
import json
from pathlib import Path
import threading
import time

from agent_evaluations.config_dir import load_evaluation_environment
from agent_evaluations.container_backend import resolve_docker_runtime_config
from agent_evaluations.repoqa import (
    DEFAULT_REPOQA_RELEASE,
    RepoQATask,
    build_repoqa_manifest,
    materialize_repoqa_workspace,
    repoqa_cache_path,
    run_repoqa_benchmark,
    run_repoqa_single_task_from_payload,
    score_repoqa_answer,
)
from agent_evaluations.utils import write_json


def _write_fixture_config(config_dir: Path, *, response_text: str) -> None:
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "AGENTS.md").write_text("Use tools carefully.\n", encoding="utf-8")
    write_json(
        config_dir / "config.json",
        {
            "plugin_cache_dir": str(config_dir / ".plugin_cache"),
            "providers": {
                "fixture": {
                    "provider": "plugins.controllable_openai_test_provider.ControllableOpenAITestProvider",
                    "model": "fixture-model",
                    "response_mode": "static",
                    "response_text": response_text,
                }
            },
            "plugins": [
                "plugins.controllable_openai_test_provider.ControllableOpenAITestProvider"
            ],
            "agents": {
                "fixture-agent": {
                    "provider": "fixture"
                }
            },
            "agentic_evaluations": {
                "cache_root": str(config_dir / "cache"),
                "results_root": str(config_dir / "results"),
                "manifests_root": str(config_dir / "manifests"),
                "workspace_root": str(config_dir / "workspaces"),
                "schedule": {
                    "window_minutes": 60,
                    "tasks_per_window": 10,
                    "max_parallel_tasks": 2,
                },
            },
        },
    )


def _write_repoqa_fixture_release(env, *, task_count: int = 1) -> None:
    tasks = []
    for index in range(task_count):
        code = (
            f"def target_{index}(value):\n"
            f"    return value + {index}\n"
        )
        tasks.append(
            {
                "repo": f"example-repo-{index}",
                "commit_sha": f"commit-{index}",
                "entrypoint_path": "src/example",
                "topic": "fixture",
                "content": {
                    "src/example/module.py": code,
                },
                "dependency": {
                    "src/example/module.py": [],
                },
                "functions": {
                    "src/example/module.py": [
                        {
                            "name": f"target_{index}",
                            "start_line": 1,
                            "end_line": 2,
                            "global_start_line": 1,
                            "global_end_line": 2,
                            "start_byte": 0,
                            "end_byte": len(code.encode("utf-8")),
                            "global_start_byte": 0,
                            "global_end_byte": len(code.encode("utf-8")),
                            "code_ratio": 1.0,
                        }
                    ]
                },
                "needles": [
                    {
                        "name": f"target_{index}",
                        "start_line": 1,
                        "end_line": 2,
                        "start_byte": 0,
                        "end_byte": len(code.encode("utf-8")),
                        "global_start_line": 1,
                        "global_end_line": 2,
                        "global_start_byte": 0,
                        "global_end_byte": len(code.encode("utf-8")),
                        "code_ratio": 1.0,
                        "path": "src/example/module.py",
                        "description": f"Find target_{index}.",
                    }
                ],
            }
        )

    payload = {"python": tasks}
    cache_path = repoqa_cache_path(env, DEFAULT_REPOQA_RELEASE)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(gzip.compress(json.dumps(payload).encode("utf-8")))


def test_repoqa_fixture_run_scores_a_completed_answer(tmp_path: Path) -> None:
    response_text = json.dumps(
        {
            "path": "src/example/module.py",
            "symbol": "target_0",
            "code": "def target_0(value):\n    return value + 0\n",
        }
    )
    config_dir = tmp_path / "config"
    _write_fixture_config(config_dir, response_text=response_text)
    env = load_evaluation_environment(config_dir)
    _write_repoqa_fixture_release(env, task_count=1)

    manifest = build_repoqa_manifest(
        env,
        release=DEFAULT_REPOQA_RELEASE,
        language="python",
        limit=1,
        seed=1,
    )
    run_manifest_path = run_repoqa_benchmark(
        env,
        benchmark_manifest=manifest,
        agent_id="fixture-agent",
        profile_name=None,
        profile_payload={},
        schedule_overrides={"tasks_per_window": 10, "window_minutes": 60, "max_parallel_tasks": 1},
        model_override=None,
        max_task_restarts=1,
        resume_run_manifest_path=None,
    )

    summary = json.loads((run_manifest_path.parent / "summary.json").read_text(encoding="utf-8"))
    results_lines = (run_manifest_path.parent / "results.jsonl").read_text(encoding="utf-8").strip().splitlines()
    result = json.loads(results_lines[0])

    assert summary["completed_task_count"] == 1
    assert summary["accuracy"] == 1.0
    assert result["score"]["matched"] is True
    assert result["task"]["symbol"] == "target_0"


def test_repoqa_runner_respects_max_parallel_tasks(monkeypatch, tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    _write_fixture_config(config_dir, response_text="{}")
    env = load_evaluation_environment(config_dir)
    _write_repoqa_fixture_release(env, task_count=4)
    manifest = build_repoqa_manifest(
        env,
        release=DEFAULT_REPOQA_RELEASE,
        language="python",
        limit=4,
        seed=0,
    )

    current = 0
    observed_max = 0
    lock = threading.Lock()

    def _fake_task_runner(*_args, **kwargs):
        nonlocal current, observed_max
        with lock:
            current += 1
            observed_max = max(observed_max, current)
        time.sleep(0.05)
        with lock:
            current -= 1
        return {
            "task": kwargs["task_payload"],
            "workspace_root": str(tmp_path / "workspace"),
            "attempts": [{"attempt_index": 0, "state": "completed"}],
            "state": "completed",
            "error": None,
            "score": {"matched": True, "score": 1.0},
            "parsed_answer": {"path": "x", "symbol": "y", "code": "z"},
            "final_assistant_text": "{}",
            "tool_call_count": 0,
            "provider_call_count": None,
        }

    monkeypatch.setattr("agent_evaluations.repoqa.run_repoqa_task_with_restarts", _fake_task_runner)

    run_repoqa_benchmark(
        env,
        benchmark_manifest=manifest,
        agent_id="fixture-agent",
        profile_name=None,
        profile_payload={},
        schedule_overrides={"tasks_per_window": 10, "window_minutes": 60, "max_parallel_tasks": 2},
        model_override=None,
        max_task_restarts=1,
        resume_run_manifest_path=None,
    )

    assert observed_max <= 2


def test_repoqa_task_retries_on_pre_completion_failure(monkeypatch, tmp_path: Path) -> None:
    response_text = json.dumps(
        {
            "path": "src/example/module.py",
            "symbol": "target_0",
            "code": "def target_0(value):\n    return value + 0\n",
        }
    )
    config_dir = tmp_path / "config"
    _write_fixture_config(config_dir, response_text=response_text)
    env = load_evaluation_environment(config_dir)
    _write_repoqa_fixture_release(env, task_count=1)
    manifest = build_repoqa_manifest(
        env,
        release=DEFAULT_REPOQA_RELEASE,
        language="python",
        limit=1,
        seed=1,
    )
    task_payload = manifest["tasks"][0]
    calls = {"count": 0}

    def _flaky_attempt(*_args, **_kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("temporary failure")
        return {
            "events": [{"type": "request_completed"}],
            "final_session": object(),
            "final_assistant_text": response_text,
            "tool_call_count": 0,
            "provider_call_count": None,
        }

    monkeypatch.setattr("agent_evaluations.repoqa._run_repoqa_attempt", _flaky_attempt)

    from agent_evaluations.repoqa import run_repoqa_task_with_restarts

    result = run_repoqa_task_with_restarts(
        env,
        run_id="retry-run",
        release=DEFAULT_REPOQA_RELEASE,
        task_payload=task_payload,
        agent_id="fixture-agent",
        model_override=None,
        max_task_restarts=2,
    )

    assert calls["count"] == 2
    assert result["state"] == "completed"
    assert len(result["attempts"]) == 2


def test_repoqa_python_scoring_ignores_docstring_whitespace_only_differences() -> None:
    task = RepoQATask(
        task_id="task-1",
        language="python",
        repo_index=0,
        needle_index=0,
        repo_name="repo",
        commit_sha="commit",
        path="module.py",
        symbol="target",
        description="desc",
        start_line=1,
        end_line=4,
        ground_truth_code=(
            "def target():\n"
            "    \"\"\"Example.\n\n"
            "    x = y\n"
            "    \"\"\"\n"
            "    return 1\n"
        ),
    )

    answer = {
        "path": "module.py",
        "symbol": "target",
        "code": (
            "def target():\n"
            "    \"\"\"Example.\n\n"
            "    x=y\n"
            "    \"\"\"\n"
            "    return 1\n"
        ),
    }

    score = score_repoqa_answer(task, answer)

    assert score["path_match"] is True
    assert score["symbol_match"] is True
    assert score["code_match"] is True
    assert score["matched"] is True


def test_repoqa_python_scoring_detects_real_behavior_changes() -> None:
    task = RepoQATask(
        task_id="task-2",
        language="python",
        repo_index=0,
        needle_index=0,
        repo_name="repo",
        commit_sha="commit",
        path="module.py",
        symbol="target",
        description="desc",
        start_line=1,
        end_line=2,
        ground_truth_code=(
            "def target(value):\n"
            "    return value + 1\n"
        ),
    )

    answer = {
        "path": "module.py",
        "symbol": "target",
        "code": (
            "def target(value):\n"
            "    return value - 1\n"
        ),
    }

    score = score_repoqa_answer(task, answer)

    assert score["path_match"] is True
    assert score["symbol_match"] is True
    assert score["code_match"] is False
    assert score["matched"] is False


def test_repoqa_scoring_accepts_repo_prefixed_workspace_paths() -> None:
    task = RepoQATask(
        task_id="task-3",
        language="python",
        repo_index=0,
        needle_index=0,
        repo_name="repo",
        commit_sha="commit",
        path="pkg/module.py",
        symbol="target",
        description="desc",
        start_line=1,
        end_line=2,
        ground_truth_code=(
            "def target(value):\n"
            "    return value + 1\n"
        ),
    )

    answer = {
        "path": "repo/pkg/module.py",
        "symbol": "target",
        "code": (
            "def target(value):\n"
            "    return value + 1\n"
        ),
    }

    score = score_repoqa_answer(task, answer)

    assert score["path_match"] is True
    assert score["symbol_match"] is True
    assert score["code_match"] is True
    assert score["matched"] is True


def test_repoqa_internal_single_task_runner_uses_existing_workspace(tmp_path: Path) -> None:
    response_text = json.dumps(
        {
            "path": "repo/src/example/module.py",
            "symbol": "target_0",
            "code": "def target_0(value):\n    return value + 0\n",
        }
    )
    config_dir = tmp_path / "config"
    _write_fixture_config(config_dir, response_text=response_text)
    env = load_evaluation_environment(config_dir)
    _write_repoqa_fixture_release(env, task_count=1)
    manifest = build_repoqa_manifest(
        env,
        release=DEFAULT_REPOQA_RELEASE,
        language="python",
        limit=1,
        seed=1,
    )
    task_payload = manifest["tasks"][0]
    task = RepoQATask(**task_payload)
    workspace_root, _meta = materialize_repoqa_workspace(
        env,
        run_id="single-task-run",
        task=task,
        release=DEFAULT_REPOQA_RELEASE,
    )

    result = run_repoqa_single_task_from_payload(
        env,
        task_payload=task_payload,
        run_id="single-task-run",
        release=DEFAULT_REPOQA_RELEASE,
        workspace_root=workspace_root,
        agent_id="fixture-agent",
        model_override=None,
        max_task_restarts=1,
    )

    assert result["state"] == "completed"
    assert result["score"]["matched"] is True


def test_repoqa_runner_uses_docker_backend_when_selected(monkeypatch, tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    _write_fixture_config(config_dir, response_text="{}")
    config = json.loads((config_dir / "config.json").read_text(encoding="utf-8"))
    config["agentic_evaluations"]["docker"] = {
        "enabled": True,
        "image_tag": "agent-evals:test",
        "dockerfile": str(tmp_path / "Dockerfile"),
        "build_context": str(tmp_path),
        "source_bundle_path": str(tmp_path / "repo-source.tar.gz"),
    }
    (config_dir / "config.json").write_text(json.dumps(config), encoding="utf-8")

    env = load_evaluation_environment(config_dir)
    _write_repoqa_fixture_release(env, task_count=1)
    manifest = build_repoqa_manifest(
        env,
        release=DEFAULT_REPOQA_RELEASE,
        language="python",
        limit=1,
        seed=1,
    )

    calls: list[dict[str, object]] = []

    def _fake_run_in_container(runtime, **kwargs):
        calls.append({"runtime": runtime, **kwargs})
        return {
            "task": kwargs["host_task_payload_path"].read_text(encoding="utf-8"),
            "workspace_root": str(kwargs["host_workspace_root"]),
            "attempts": [{"attempt_index": 0, "state": "completed"}],
            "state": "completed",
            "error": None,
            "score": {"matched": True, "score": 1.0},
            "parsed_answer": {"path": "repo/x.py", "symbol": "f", "code": "def f():\n    pass\n"},
            "final_assistant_text": "{}",
            "tool_call_count": 0,
            "provider_call_count": None,
        }

    monkeypatch.setattr("agent_evaluations.repoqa.run_repoqa_task_in_container", _fake_run_in_container)

    run_manifest_path = run_repoqa_benchmark(
        env,
        benchmark_manifest=manifest,
        agent_id="fixture-agent",
        profile_name=None,
        profile_payload={"runtime_backend": "docker"},
        schedule_overrides={"tasks_per_window": 10, "window_minutes": 60, "max_parallel_tasks": 1},
        model_override=None,
        max_task_restarts=1,
        runtime_backend="docker",
        docker_runtime=resolve_docker_runtime_config(
            env,
            profile_payload={"docker": config["agentic_evaluations"]["docker"]},
        ),
        resume_run_manifest_path=None,
    )

    assert run_manifest_path.is_file()
    assert len(calls) == 1
    assert calls[0]["host_workspace_root"].is_dir()
    assert calls[0]["host_results_root"] == run_manifest_path.parent