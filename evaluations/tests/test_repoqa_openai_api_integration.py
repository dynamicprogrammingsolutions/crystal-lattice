from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sys

from agent_evaluations.benchmark_registry import load_benchmarks
from agent_evaluations.config_dir import load_evaluation_environment
load_benchmarks()
_shared = sys.modules["agent_evaluations_external_benchmark_repoqa_shared_common"]
_agentic = sys.modules["agent_evaluations_external_benchmark_repoqa_agentic"]
DEFAULT_REPOQA_RELEASE = _shared.DEFAULT_REPOQA_RELEASE
build_repoqa_manifest = _agentic.build_repoqa_manifest
download_repoqa_release = _agentic.download_repoqa_release
run_repoqa_benchmark = _agentic.run_repoqa_benchmark

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_DIR = (
    ROOT / "application" / "python" / "agent_terminal_app" / "default_config"
)


def _require_openai_api_key() -> str:
    value = os.getenv("OPENAI_API_KEY")
    if not value:
        import pytest

        pytest.skip("OPENAI_API_KEY not set; skipping RepoQA OpenAI API integration test")
    return value


def _prepare_config_dir(tmp_path: Path) -> Path:
    config_dir = tmp_path / "config"
    shutil.copytree(DEFAULT_CONFIG_DIR, config_dir)
    (config_dir / "AGENTS.md").write_text(
        "This workspace is an evaluation harness. Use tools to inspect the repo and return only the requested JSON answer.\n",
        encoding="utf-8",
    )

    config_path = config_dir / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["agentic_evaluations"] = {
        "cache_root": str(config_dir / "cache"),
        "results_root": str(config_dir / "results"),
        "manifests_root": str(config_dir / "manifests"),
        "workspace_root": str(config_dir / "workspaces"),
        "schedule": {
            "window_minutes": 60,
            "tasks_per_window": 10,
            "max_parallel_tasks": 1,
        },
    }
    config_path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return config_dir


def test_repoqa_openai_api_smoke_run_gpt54mini(tmp_path: Path) -> None:
    _require_openai_api_key()
    config_dir = _prepare_config_dir(tmp_path)
    env = load_evaluation_environment(config_dir)

    download_repoqa_release(env, release=DEFAULT_REPOQA_RELEASE, force=False)
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
        agent_id="codex-openai-api",
        profile_name=None,
        profile_payload={},
        schedule_overrides={
            "window_minutes": 60,
            "tasks_per_window": 10,
            "max_parallel_tasks": 1,
        },
        model_override="gpt-5.4-mini",
        max_task_restarts=1,
        resume_run_manifest_path=None,
    )

    summary_path = run_manifest_path.parent / "summary.json"
    results_path = run_manifest_path.parent / "results.jsonl"
    assert summary_path.is_file()
    assert results_path.is_file()

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["completed_task_count"] == 1
    assert summary["agent_id"] == "codex-openai-api"