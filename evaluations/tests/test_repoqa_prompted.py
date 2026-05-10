from __future__ import annotations

from datetime import datetime, timedelta, timezone
import gzip
import json
from pathlib import Path

from agent_app.config import resolve_request_config
from agent_evaluations.config_dir import load_evaluation_environment
from agent_evaluations.container_backend import resolve_docker_runtime_config
from agent_evaluations.repoqa import DEFAULT_REPOQA_RELEASE, repoqa_cache_path
from agent_evaluations.repoqa_prompted import (
    RepoQATask,
    build_repoqa_prompted_manifest,
    build_repoqa_prompted_prompt,
    materialize_repoqa_prompted_workspace,
    parse_repoqa_prompted_answer,
    run_repoqa_prompted_benchmark,
    run_repoqa_prompted_single_task_from_payload,
    run_repoqa_prompted_task_with_restarts,
)
from agent_evaluations.utils import write_json


def _write_fixture_config(
    config_dir: Path,
    *,
    response_text: str,
    prompted_settings: dict | None = None,
    include_tool_gating: bool = True,
    include_math_tools: bool = True,
) -> None:
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "AGENTS.md").write_text("Use tools carefully.\n", encoding="utf-8")
    plugins = [
        "plugins.controllable_openai_test_provider.ControllableOpenAITestProvider",
    ]
    if include_tool_gating:
        plugins.append("plugins.tool_gating_feature.ToolGatingFeature")
    if include_math_tools:
        plugins.append("plugins.math_tools.MathTools")
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
            "plugins": plugins,
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
                "repoqa_prompted": prompted_settings or {},
            },
        },
    )


def _write_repoqa_fixture_release(env, *, task_count: int = 1) -> None:
    tasks = []
    for index in range(task_count):
        helper_code = "def helper(value):\n    return value - 1\n"
        target_code = (
            f"def target_{index}(value):\n"
            f'    """Fixture docstring."""\n'
            f"    return helper(value) + {index}\n"
        )
        tasks.append(
            {
                "repo": f"example-repo-{index}",
                "commit_sha": f"commit-{index}",
                "entrypoint_path": "src/example",
                "topic": "fixture",
                "content": {
                    "src/example/helpers.py": helper_code,
                    "src/example/module.py": target_code,
                },
                "dependency": {
                    "src/example/helpers.py": [],
                    "src/example/module.py": ["src/example/helpers.py"],
                },
                "functions": {
                    "src/example/module.py": [
                        {
                            "name": f"target_{index}",
                            "start_line": 1,
                            "end_line": 3,
                            "global_start_line": 1,
                            "global_end_line": 3,
                            "start_byte": 0,
                            "end_byte": len(target_code.encode("utf-8")),
                            "global_start_byte": 0,
                            "global_end_byte": len(target_code.encode("utf-8")),
                            "code_ratio": 1.0,
                        }
                    ]
                },
                "needles": [
                    {
                        "name": f"target_{index}",
                        "start_line": 1,
                        "end_line": 3,
                        "start_byte": 0,
                        "end_byte": len(target_code.encode("utf-8")),
                        "global_start_line": 1,
                        "global_end_line": 3,
                        "global_start_byte": 0,
                        "global_end_byte": len(target_code.encode("utf-8")),
                        "code_ratio": 1.0,
                        "path": "src/example/module.py",
                        "description": f"Find target_{index}. It uses helper(value) and then adds {index}.",
                    }
                ],
            }
        )

    payload = {"python": tasks}
    cache_path = repoqa_cache_path(env, DEFAULT_REPOQA_RELEASE)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(gzip.compress(json.dumps(payload).encode("utf-8")))


def test_repoqa_prompted_prompt_is_deterministic_and_uses_context_budget(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    _write_fixture_config(
        config_dir,
        response_text="def target_0(value):\n    return helper(value) + 0\n",
        prompted_settings={"context_budget_chars": 90},
    )
    env = load_evaluation_environment(config_dir)
    _write_repoqa_fixture_release(env)
    manifest = build_repoqa_prompted_manifest(
        env,
        release=DEFAULT_REPOQA_RELEASE,
        language="python",
        limit=1,
        seed=1,
    )
    task = RepoQATask(**manifest["tasks"][0])

    prompt1, meta1 = build_repoqa_prompted_prompt(env, task=task, release=DEFAULT_REPOQA_RELEASE)
    prompt2, meta2 = build_repoqa_prompted_prompt(env, task=task, release=DEFAULT_REPOQA_RELEASE)

    assert prompt1 == prompt2
    assert meta1 == meta2
    assert meta1["truncated"] is True
    assert meta1["included_file_count"] >= 1
    assert "Return only the function source code" in prompt1


def test_repoqa_prompted_parser_accepts_plain_and_fenced_code() -> None:
    task = RepoQATask(
        task_id="task",
        language="python",
        repo_index=0,
        needle_index=0,
        repo_name="repo",
        commit_sha="sha",
        path="src/example/module.py",
        symbol="target_0",
        description="Find target_0.",
        start_line=1,
        end_line=2,
        ground_truth_code="def target_0(value):\n    return value\n",
    )

    plain_answer, plain_error = parse_repoqa_prompted_answer(
        task,
        "def target_0(value):\n    return value\n",
    )
    fenced_answer, fenced_error = parse_repoqa_prompted_answer(
        task,
        "Here is the function:\n```python\ndef target_0(value):\n    return value\n```\n",
    )

    assert plain_error is None
    assert fenced_error is None
    assert plain_answer is not None
    assert fenced_answer is not None
    assert plain_answer["path"] == task.path
    assert plain_answer["symbol"] == "target_0"
    assert "def target_0" in fenced_answer["code"]


def test_repoqa_prompted_fixture_run_scores_completed_plain_code_answer(tmp_path: Path) -> None:
    response_text = "def target_0(value):\n    return helper(value) + 0\n"
    config_dir = tmp_path / "config"
    _write_fixture_config(config_dir, response_text=response_text)
    env = load_evaluation_environment(config_dir)
    _write_repoqa_fixture_release(env, task_count=1)

    manifest = build_repoqa_prompted_manifest(
        env,
        release=DEFAULT_REPOQA_RELEASE,
        language="python",
        limit=1,
        seed=1,
    )
    run_manifest_path = run_repoqa_prompted_benchmark(
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
    result = json.loads((run_manifest_path.parent / "results.jsonl").read_text(encoding="utf-8").strip())

    assert summary["completed_task_count"] == 1
    assert summary["accuracy"] == 1.0
    assert result["score"]["matched"] is True
    assert result["tool_call_count"] == 0
    assert result["effective_tool_schema_count"] == 0


def test_repoqa_prompted_internal_single_task_runner_uses_existing_workspace(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    _write_fixture_config(config_dir, response_text="def target_0(value):\n    return helper(value) + 0\n")
    env = load_evaluation_environment(config_dir)
    _write_repoqa_fixture_release(env, task_count=1)
    manifest = build_repoqa_prompted_manifest(
        env,
        release=DEFAULT_REPOQA_RELEASE,
        language="python",
        limit=1,
        seed=1,
    )
    task_payload = manifest["tasks"][0]
    task = RepoQATask(**task_payload)
    workspace_root, _meta = materialize_repoqa_prompted_workspace(
        env,
        run_id="run-1",
        task=task,
        release=DEFAULT_REPOQA_RELEASE,
    )

    result = run_repoqa_prompted_single_task_from_payload(
        env,
        task_payload=task_payload,
        run_id="run-1",
        release=DEFAULT_REPOQA_RELEASE,
        workspace_root=workspace_root,
        agent_id="fixture-agent",
        model_override=None,
        max_task_restarts=1,
    )

    assert result["state"] == "completed"
    assert result["score"]["matched"] is True
    assert result["effective_tool_schema_count"] == 0


def test_repoqa_prompted_disable_all_tools_is_honored_by_application_stack(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    _write_fixture_config(config_dir, response_text="def target_0(value):\n    return helper(value) + 0\n")
    env = load_evaluation_environment(config_dir)

    app = env.build_application()
    core, base_config, _session = app.create_session_ephemeral("fixture-agent")
    effective_config = resolve_request_config(base_config, {"disable_all_tools": True})

    assert [schema["function"]["name"] for schema in core.get_tool_schemas(base_config)] == [
        "add",
        "multiply",
        "square",
    ]
    assert core.get_tool_schemas(effective_config) == []


def test_repoqa_prompted_fails_clearly_when_tool_gating_feature_is_missing(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    _write_fixture_config(
        config_dir,
        response_text="def target_0(value):\n    return helper(value) + 0\n",
        include_tool_gating=False,
        include_math_tools=True,
    )
    env = load_evaluation_environment(config_dir)
    _write_repoqa_fixture_release(env, task_count=1)
    manifest = build_repoqa_prompted_manifest(
        env,
        release=DEFAULT_REPOQA_RELEASE,
        language="python",
        limit=1,
        seed=1,
    )

    result = run_repoqa_prompted_task_with_restarts(
        env,
        run_id="missing-gating",
        release=DEFAULT_REPOQA_RELEASE,
        task_payload=manifest["tasks"][0],
        agent_id="fixture-agent",
        model_override=None,
        max_task_restarts=0,
    )

    assert result["state"] == "failed_before_turn_completed"
    assert "ToolGatingFeature" in str(result["error"])


def test_repoqa_prompted_runner_uses_docker_backend_when_selected(monkeypatch, tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    _write_fixture_config(config_dir, response_text="def target_0(value):\n    return helper(value) + 0\n")
    env = load_evaluation_environment(config_dir)
    _write_repoqa_fixture_release(env, task_count=1)
    manifest = build_repoqa_prompted_manifest(
        env,
        release=DEFAULT_REPOQA_RELEASE,
        language="python",
        limit=1,
        seed=1,
    )
    docker_runtime = resolve_docker_runtime_config(
        env,
        profile_payload={
            "docker": {
                "enabled": True,
                "image_tag": "agent-evaluations:test",
            }
        },
    )

    seen: dict[str, object] = {}

    def _fake_run_in_container(*args, **kwargs):
        seen["args"] = args
        seen["kwargs"] = kwargs
        return {
            "task": manifest["tasks"][0],
            "workspace_root": str(tmp_path / "workspace"),
            "attempts": [{"attempt_index": 0, "state": "completed"}],
            "state": "completed",
            "error": None,
            "score": {"matched": True, "score": 1.0},
            "parsed_answer": {"path": "src/example/module.py", "symbol": "target_0", "code": "def x():\n    pass\n"},
            "final_assistant_text": "def target_0(value):\n    return helper(value) + 0\n",
            "tool_call_count": 0,
            "effective_tool_schema_count": 0,
            "provider_call_count": None,
        }

    monkeypatch.setattr("agent_evaluations.repoqa_prompted.run_benchmark_task_in_container", _fake_run_in_container)

    run_manifest_path = run_repoqa_prompted_benchmark(
        env,
        benchmark_manifest=manifest,
        agent_id="fixture-agent",
        profile_name=None,
        profile_payload={},
        schedule_overrides={"tasks_per_window": 10, "window_minutes": 60, "max_parallel_tasks": 1},
        model_override=None,
        max_task_restarts=1,
        runtime_backend="docker",
        docker_runtime=docker_runtime,
        resume_run_manifest_path=None,
    )

    assert run_manifest_path.is_file()
    assert seen["kwargs"]["benchmark_id"] == "repoqa-prompted"