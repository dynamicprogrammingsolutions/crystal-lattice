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
        "runtime image changes",
        "syntax and JSON checks",
        "crystal-lattice validate-cloud --workspace-dir <project>",
        "Do not print secrets",
    ):
        assert required in template

    assert (
        "Read and follow the bundled authoring guide before writing files" in template
    )
    assert "Use the bundled default profile scripts as examples" in template
    assert "provider-free" not in template


def test_cloud_script_author_agent_can_read_guide_and_default_profiles() -> None:
    config = json.loads(DEFAULT_CONFIG.read_text(encoding="utf-8"))
    agent = config["agents"]["cloud-script-author"]
    allowed_paths = agent["allowed_paths"]

    assert "${env:BUILTIN_PLUGINS}/cloud-agent-app" in allowed_paths
    assert "${env:CONFIG_DIR}/cloud-agent/profiles" in allowed_paths

    variables = config["mixins"]["cloud_script_author_codex_message"]["system_message"][
        "variables"
    ]
    assert variables["CLOUD_SCRIPT_AUTHORING_GUIDE_PATH"]["text"] == (
        "${env:BUILTIN_PLUGINS}/cloud-agent-app/docs/cloud-script-authoring.md"
    )
    assert variables["CLOUD_AGENT_DEFAULT_PROFILES_PATH"]["text"] == (
        "${env:CONFIG_DIR}/cloud-agent/profiles"
    )


def test_default_config_declares_default_runtime_profile_explicitly() -> None:
    config = json.loads(DEFAULT_CONFIG.read_text(encoding="utf-8"))
    cloud = config["application"]["cloud_agent"]

    assert cloud["default_container_profile"] == "default-runtime"
    profile = cloud["container_profiles"]["default-runtime"]
    assert profile["mode"] == "dockerfile"
    assert profile["image"] == "cloud-agent-runtime:latest"
    assert profile["dockerfile"] == "Dockerfile"

    context = profile["context"]
    assert isinstance(context, list)
    assert {
        "source": "${env:BUILTIN_PLUGINS}/cloud-agent-app/src/cloud_agent_app/bundled_runtime/python/Dockerfile",
        "target": "Dockerfile",
    } in context
    assert {
        "source": "${env:BUILTIN_PLUGINS}/cloud-agent-app/src/cloud_agent_app/bundled_runtime/python/runtime.py",
        "target": "runtime.py",
    } in context
    assert {
        "source": "${env:CLOUD_RUNTIME_BUILD_CONTEXT}/python_lib",
        "target": "python_lib",
    } in context
