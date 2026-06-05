from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = (
    ROOT
    / "application"
    / "python"
    / "agent_terminal_app"
    / "default_config"
    / "config.json"
)


def test_cloud_script_author_prompt_includes_container_profile_guidance() -> None:
    config = json.loads(DEFAULT_CONFIG.read_text(encoding="utf-8"))
    mixin = config["mixins"]["cloud_script_author_codex_message"]
    template = mixin["system_message"]["template"]

    for required in (
        "cloud-agent project hooks",
        "{{CLOUD_SCRIPT_AUTHORING_GUIDE_PATH}}",
        "{{CLOUD_AGENT_DEFAULT_PROFILES_PATH}}",
        "container profile guidance",
        "container_profiles",
        "build_assets",
        "cache_mounts",
        "mounts",
        "Node tooling",
        "Ollama",
        "prefer fast local checks first",
        "small external smoke",
        "transferred credentials or remote services",
        "Do not print secrets",
    ):
        assert required in template

    assert "baking the project workspace into Docker layers" in template
    assert "stable manifests, lockfiles, patches" in template
    assert "provider-free" not in template


def test_cloud_script_author_agent_can_read_guide_and_default_profiles() -> None:
    config = json.loads(DEFAULT_CONFIG.read_text(encoding="utf-8"))
    agent = config["agents"]["cloud-script-author"]
    allowed_paths = agent["allowed_paths"]

    assert "${env:BUILTIN_PLUGINS}/cloud-agent-app" in allowed_paths
    assert "${env:CONFIG_DIR}/cloud-agent/profiles" in allowed_paths

    variables = config["mixins"]["cloud_script_author_codex_message"][
        "system_message"
    ]["variables"]
    assert variables["CLOUD_SCRIPT_AUTHORING_GUIDE_PATH"]["text"] == (
        "${env:BUILTIN_PLUGINS}/cloud-agent-app/docs/cloud-script-authoring.md"
    )
    assert variables["CLOUD_AGENT_DEFAULT_PROFILES_PATH"]["text"] == (
        "${env:CONFIG_DIR}/cloud-agent/profiles"
    )