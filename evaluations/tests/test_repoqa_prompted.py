from __future__ import annotations

from datetime import datetime, timedelta, timezone
import gzip
import json
from pathlib import Path
import sys

from agent_app.config import resolve_request_config
from agent_evaluations.benchmark_registry import load_benchmarks
from agent_evaluations.config_dir import load_evaluation_environment
from agent_evaluations.container_backend import resolve_docker_runtime_config
from agent_evaluations.evaluations.repoqa.benchmark_prompted import (
    RepoQATask,
    build_repoqa_prompted_manifest,
    build_repoqa_prompted_prompt,
    materialize_repoqa_prompted_workspace,
    parse_repoqa_prompted_answer,
    run_repoqa_prompted_benchmark,
    run_repoqa_prompted_single_task_from_payload,
    run_repoqa_prompted_task_with_restarts,
)
from agent_evaluations.evaluations.repoqa.common import DEFAULT_REPOQA_RELEASE, repoqa_cache_path
from agent_evaluations.evaluations.repoqa import logic_prompted as _logic_prompted
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


def _write_repoqa_multilanguage_fixture_release(env) -> None:
    payload = {
        "python": [
            {
                "repo": "py-repo",
                "commit_sha": "py-commit",
                "entrypoint_path": "src/py",
                "topic": "fixture",
                "content": {"src/py/mod.py": "def py_target(value):\n    return value + 1\n"},
                "dependency": {"src/py/mod.py": []},
                "functions": {
                    "src/py/mod.py": [
                        {
                            "name": "py_target",
                            "start_line": 1,
                            "end_line": 2,
                            "global_start_line": 1,
                            "global_end_line": 2,
                            "start_byte": 0,
                            "end_byte": 40,
                            "global_start_byte": 0,
                            "global_end_byte": 40,
                            "code_ratio": 1.0,
                        }
                    ]
                },
                "needles": [
                    {
                        "name": "py_target",
                        "start_line": 1,
                        "end_line": 2,
                        "start_byte": 0,
                        "end_byte": 40,
                        "global_start_line": 1,
                        "global_end_line": 2,
                        "global_start_byte": 0,
                        "global_end_byte": 40,
                        "code_ratio": 1.0,
                        "path": "src/py/mod.py",
                        "description": "Find py_target.",
                    }
                ],
            }
        ],
        "java": [
            {
                "repo": "java-repo",
                "commit_sha": "java-commit",
                "entrypoint_path": "src/java",
                "topic": "fixture",
                "content": {"src/java/Thing.java": "int javaTarget(int value) {\n  return value + 2;\n}\n"},
                "dependency": {"src/java/Thing.java": []},
                "functions": {
                    "src/java/Thing.java": [
                        {
                            "name": "javaTarget",
                            "start_line": 1,
                            "end_line": 3,
                            "global_start_line": 1,
                            "global_end_line": 3,
                            "start_byte": 0,
                            "end_byte": 52,
                            "global_start_byte": 0,
                            "global_end_byte": 52,
                            "code_ratio": 1.0,
                        }
                    ]
                },
                "needles": [
                    {
                        "name": "javaTarget",
                        "start_line": 1,
                        "end_line": 3,
                        "start_byte": 0,
                        "end_byte": 52,
                        "global_start_line": 1,
                        "global_end_line": 3,
                        "global_start_byte": 0,
                        "global_end_byte": 52,
                        "code_ratio": 1.0,
                        "path": "src/java/Thing.java",
                        "description": "Find javaTarget.",
                    }
                ],
            }
        ],
    }
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


def test_repoqa_prompted_all_language_manifest_is_deterministic_and_balanced(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    _write_fixture_config(config_dir, response_text="def py_target(value):\n    return value + 1\n")
    env = load_evaluation_environment(config_dir)
    _write_repoqa_multilanguage_fixture_release(env)

    manifest1 = build_repoqa_prompted_manifest(
        env,
        release=DEFAULT_REPOQA_RELEASE,
        language="all",
        limit=2,
        seed=7,
    )
    manifest2 = build_repoqa_prompted_manifest(
        env,
        release=DEFAULT_REPOQA_RELEASE,
        language="all",
        limit=2,
        seed=7,
    )

    stable1 = {key: value for key, value in manifest1.items() if key != "created_at"}
    stable2 = {key: value for key, value in manifest2.items() if key != "created_at"}
    assert stable1 == stable2
    assert manifest1["languages"] == ["python", "java"]
    assert [task["language"] for task in manifest1["tasks"]] == ["python", "java"]


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
    assert summary["eligible_task_count"] == 1
    assert summary["excluded_missing_target_context_count"] == 0
    assert summary["accuracy"] == 1.0
    assert result["score"]["matched"] is True
    assert result["tool_call_count"] == 0
    assert result["effective_tool_schema_count"] == 0


def test_repoqa_prompted_omitted_target_skips_request_and_is_excluded(tmp_path: Path, monkeypatch) -> None:
    config_dir = tmp_path / "config"
    _write_fixture_config(
        config_dir,
        response_text="def target_0(value):\n    return helper(value) + 0\n",
        prompted_settings={"context_budget_chars": 70},
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
    task_payload = manifest["tasks"][0]

    def _unexpected_attempt(*_args, **_kwargs):
        raise AssertionError("request should not be sent when target is omitted from context")

    monkeypatch.setattr(_logic_prompted, "_run_repoqa_prompted_attempt", _unexpected_attempt)

    result = run_repoqa_prompted_task_with_restarts(
        env,
        run_id="omitted-target",
        release=DEFAULT_REPOQA_RELEASE,
        task_payload=task_payload,
        agent_id="fixture-agent",
        model_override=None,
        max_task_restarts=0,
    )

    assert result["state"] == "skipped_missing_target_context"
    assert result["outcome"] == "skipped_missing_target_context"
    assert result["eligible_for_accuracy"] is False
    assert result["target_in_context"] is False
    assert result["provider_call_count"] == 0


def test_repoqa_prompted_summary_excludes_missing_target_context_from_accuracy(monkeypatch, tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    _write_fixture_config(config_dir, response_text="def target_0(value):\n    return helper(value) + 0\n")
    env = load_evaluation_environment(config_dir)
    _write_repoqa_fixture_release(env, task_count=2)
    manifest = build_repoqa_prompted_manifest(
        env,
        release=DEFAULT_REPOQA_RELEASE,
        language="python",
        limit=2,
        seed=1,
    )

    responses = iter(
        [
            {
                "task": manifest["tasks"][0],
                "workspace_root": str(tmp_path / "workspace-1"),
                "attempts": [],
                "state": "skipped_missing_target_context",
                "outcome": "skipped_missing_target_context",
                "eligible_for_accuracy": False,
                "failure_category": "context_budget_excluded_target",
                "error": None,
                "score": {"matched": False, "score": 0.0},
                "parsed_answer": None,
                "parse_error": None,
                "final_assistant_text": "",
                "tool_call_count": 0,
                "effective_tool_schema_count": 0,
                "usage": None,
                "cost": None,
                "cost_formatted": None,
                "provider_call_count": 0,
                "meta": {},
            },
            {
                "task": manifest["tasks"][1],
                "workspace_root": str(tmp_path / "workspace-2"),
                "attempts": [{"attempt_index": 0, "state": "completed"}],
                "state": "completed",
                "outcome": "matched",
                "eligible_for_accuracy": True,
                "failure_category": None,
                "error": None,
                "score": {"matched": True, "score": 1.0},
                "parsed_answer": {
                    "path": manifest["tasks"][1]["path"],
                    "symbol": manifest["tasks"][1]["symbol"],
                    "code": manifest["tasks"][1]["ground_truth_code"],
                },
                "parse_error": None,
                "final_assistant_text": manifest["tasks"][1]["ground_truth_code"],
                "tool_call_count": 0,
                "effective_tool_schema_count": 0,
                "usage": None,
                "cost": None,
                "cost_formatted": None,
                "provider_call_count": None,
                "meta": {},
            },
        ]
    )

    monkeypatch.setattr(_logic_prompted, "run_repoqa_prompted_task_with_restarts", lambda *args, **kwargs: next(responses))

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
    assert summary["manifest_task_count"] == 2
    assert summary["eligible_task_count"] == 1
    assert summary["excluded_missing_target_context_count"] == 1
    assert summary["model_request_task_count"] == 1
    assert summary["matched_task_count"] == 1
    assert summary["accuracy"] == 1.0
    assert summary["raw_accuracy_over_manifest"] == 0.5


def test_repoqa_prompted_summary_excludes_failed_requests_and_uses_none_for_zero_denominator(
    monkeypatch,
    tmp_path: Path,
) -> None:
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

    responses = iter(
        [
            {
                "task": manifest["tasks"][0],
                "workspace_root": str(tmp_path / "workspace-1"),
                "attempts": [{"attempt_index": 0, "state": "retryable_failure"}],
                "state": "failed_before_turn_completed",
                "outcome": "failed_before_turn_completed",
                "eligible_for_accuracy": False,
                "failure_category": "request_failure",
                "error": "RuntimeError: quota",
                "score": {"matched": False, "score": 0.0},
                "parsed_answer": None,
                "parse_error": None,
                "final_assistant_text": "",
                "tool_call_count": 0,
                "effective_tool_schema_count": 0,
                "usage": None,
                "cost": None,
                "cost_formatted": None,
                "provider_call_count": None,
                "meta": {},
            }
        ]
    )

    monkeypatch.setattr(_logic_prompted, "run_repoqa_prompted_task_with_restarts", lambda *args, **kwargs: next(responses))

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
    assert summary["eligible_task_count"] == 0
    assert summary["successful_request_instance_count"] == 0
    assert summary["error_request_instance_count"] == 1
    assert summary["has_error_request_instances"] is True
    assert summary["accuracy"] is None
    assert summary["logical_task_average_success_rate"] is None


def test_repoqa_prompted_docker_repeat_instances_use_unique_paths(monkeypatch, tmp_path: Path) -> None:
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

    seen_inputs: list[str] = []
    seen_workspaces: list[str] = []

    def _fake_run_in_container(*args, **kwargs):
        seen_inputs.append(str(kwargs["host_task_payload_path"].name))
        seen_workspaces.append(str(kwargs["host_workspace_root"]))
        task_payload = json.loads(kwargs["host_task_payload_path"].read_text(encoding="utf-8"))
        return {
            "task": task_payload,
            "task_instance_id": task_payload["task_instance_id"],
            "repeat_index": task_payload["repeat_index"],
            "repeat_count": task_payload["repeat_count"],
            "workspace_root": str(kwargs["host_workspace_root"]),
            "attempts": [{"attempt_index": 0, "state": "completed"}],
            "state": "completed",
            "outcome": "matched",
            "eligible_for_accuracy": True,
            "failure_category": None,
            "error": None,
            "score": {"matched": True, "score": 1.0},
            "parsed_answer": {"path": "src/example/module.py", "symbol": "target_0", "code": "def x():\n    pass\n"},
            "final_assistant_text": "def target_0(value):\n    return helper(value) + 0\n",
            "tool_call_count": 0,
            "effective_tool_schema_count": 0,
            "provider_call_count": None,
            "meta": {},
        }

    monkeypatch.setattr(
        _logic_prompted,
        "warm_container_plugin_cache",
        lambda runtime, *, host_config_dir, agent_id=None: {"state": "warmed"},
    )
    monkeypatch.setattr(_logic_prompted, "run_benchmark_task_in_container", _fake_run_in_container)

    run_repoqa_prompted_benchmark(
        env,
        benchmark_manifest=manifest,
        agent_id="fixture-agent",
        profile_name=None,
        profile_payload={},
        schedule_overrides={"tasks_per_window": 100, "window_minutes": 1, "max_parallel_tasks": 1},
        model_override=None,
        repeat_count=2,
        max_task_restarts=1,
        runtime_backend="docker",
        docker_runtime=docker_runtime,
        resume_run_manifest_path=None,
    )

    assert seen_inputs == [f'{manifest["tasks"][0]["task_id"]}#r1.json', f'{manifest["tasks"][0]["task_id"]}#r2.json']
    assert seen_workspaces[0] != seen_workspaces[1]


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
    assert result["eligible_for_accuracy"] is False
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

    monkeypatch.setattr(
        _logic_prompted,
        "warm_container_plugin_cache",
        lambda runtime, *, host_config_dir, agent_id=None: {"state": "warmed"},
    )
    monkeypatch.setattr(_logic_prompted, "run_benchmark_task_in_container", _fake_run_in_container)

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


def test_repoqa_prompted_summary_aggregates_costs(monkeypatch, tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    _write_fixture_config(config_dir, response_text="def target_0(value):\n    return helper(value) + 0\n")
    env = load_evaluation_environment(config_dir)
    _write_repoqa_fixture_release(env, task_count=2)
    manifest = build_repoqa_prompted_manifest(
        env,
        release=DEFAULT_REPOQA_RELEASE,
        language="python",
        limit=2,
        seed=1,
    )

    costs = iter([0.0015, 0.0025])

    def _fake_task_runner(*_args, **kwargs):
        cost = next(costs)
        task_payload = kwargs["task_payload"]
        return {
            "task": task_payload,
            "workspace_root": str(tmp_path / "workspace"),
            "attempts": [{"attempt_index": 0, "state": "completed"}],
            "state": "completed",
            "error": None,
            "score": {"matched": True, "score": 1.0},
            "parsed_answer": {"path": task_payload["path"], "symbol": task_payload["symbol"], "code": task_payload["ground_truth_code"]},
            "parse_error": None,
            "final_assistant_text": task_payload["ground_truth_code"],
            "tool_call_count": 0,
            "effective_tool_schema_count": 0,
            "usage": {"usage_total_cost": cost, "usage_total_cost_formatted": f"${cost:.6f}"},
            "cost": cost,
            "cost_formatted": f"${cost:.6f}",
            "provider_call_count": None,
            "meta": {},
        }

    monkeypatch.setattr(_logic_prompted, "run_repoqa_prompted_task_with_restarts", _fake_task_runner)

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
    assert summary["costed_task_count"] == 2
    assert summary["total_cost"] == 0.004
    assert summary["total_cost_formatted"] == "$0.004000"