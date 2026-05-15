from __future__ import annotations

import json
from pathlib import Path

from agent_evaluations.config_dir import apply_artifact_root, apply_profile_path_overrides, load_evaluation_environment


def test_apply_profile_path_overrides_uses_config_dir_relative_paths(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "config.json").write_text(
        json.dumps(
            {
                "plugins": [],
                "providers": {},
                "agents": {},
                "agentic_evaluations": {
                    "cache_root": str(config_dir / "cache"),
                    "results_root": str(config_dir / "results"),
                    "manifests_root": str(config_dir / "manifests"),
                    "workspace_root": str(config_dir / "workspaces"),
                    "profiles_root": str(config_dir / "profiles"),
                },
            }
        ),
        encoding="utf-8",
    )
    env = load_evaluation_environment(config_dir)

    updated = apply_profile_path_overrides(
        env,
        {
            "paths": {
                "results_root": "results/nano-sample",
                "workspace_root": "workspaces/nano-sample",
            }
        },
    )

    assert updated.paths.results_root == (config_dir / "results" / "nano-sample").resolve()
    assert updated.paths.workspace_root == (config_dir / "workspaces" / "nano-sample").resolve()
    assert updated.paths.cache_root == env.paths.cache_root
    assert updated.paths.manifests_root == env.paths.manifests_root
    assert updated.paths.profiles_root == env.paths.profiles_root


def test_apply_artifact_root_wraps_results_and_workspaces_only(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "config.json").write_text(
        json.dumps(
            {
                "plugins": [],
                "providers": {},
                "agents": {},
                "agentic_evaluations": {
                    "cache_root": str(config_dir / "cache"),
                    "results_root": str(config_dir / "results"),
                    "manifests_root": str(config_dir / "manifests"),
                    "workspace_root": str(config_dir / "workspaces"),
                    "profiles_root": str(config_dir / "profiles"),
                },
            }
        ),
        encoding="utf-8",
    )
    env = load_evaluation_environment(config_dir)
    env = apply_profile_path_overrides(
        env,
        {
            "paths": {
                "results_root": "results/mini-full",
                "workspace_root": "workspaces/mini-full",
            }
        },
    )

    updated = apply_artifact_root(env, str(tmp_path / "artifacts" / "run1"))

    assert updated.paths.results_root == (tmp_path / "artifacts" / "run1" / "results" / "mini-full").resolve()
    assert updated.paths.workspace_root == (tmp_path / "artifacts" / "run1" / "workspaces" / "mini-full").resolve()
    assert updated.paths.cache_root == env.paths.cache_root
    assert updated.paths.manifests_root == env.paths.manifests_root
    assert updated.paths.profiles_root == env.paths.profiles_root