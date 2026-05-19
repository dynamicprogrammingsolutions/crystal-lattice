from __future__ import annotations

import json
from pathlib import Path

from agent_evaluations.config_dir import load_evaluation_environment


def test_load_evaluation_environment_reads_config_dir_and_dotenv(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / ".env").write_text("OPENAI_API_KEY=dotenv-key\n", encoding="utf-8")
    (config_dir / "AGENTS.md").write_text("project instructions\n", encoding="utf-8")
    (config_dir / "config.json").write_text(
        json.dumps(
            {
                "plugin_cache_dir": "${env:CONFIG_DIR}/.plugin_cache",
                "agentic_evaluations": {
                    "cache_root": "${env:CONFIG_DIR}/cache-root",
                    "results_root": "${env:CONFIG_DIR}/results-root",
                    "manifests_root": "${env:CONFIG_DIR}/manifests-root",
                    "workspace_root": "${env:CONFIG_DIR}/workspace-root",
                    "profiles_root": "${env:CONFIG_DIR}/profiles-root",
                },
            }
        ),
        encoding="utf-8",
    )

    env = load_evaluation_environment(config_dir)

    assert env.paths.config_dir == config_dir.resolve()
    assert env.paths.cache_root == (config_dir / "cache-root")
    assert env.paths.results_root == (config_dir / "results-root")
    assert env.paths.manifests_root == (config_dir / "manifests-root")
    assert env.paths.workspace_root == (config_dir / "workspace-root")
    assert env.paths.profiles_root == (config_dir / "profiles-root")
    assert env.env_overrides["CONFIG_DIR"] == str(config_dir.resolve())
    assert env.env_overrides["OPENAI_API_KEY"] == "dotenv-key"
