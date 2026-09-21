from __future__ import annotations

import json
from pathlib import Path

from .fixtures import TaskGuidanceWorkspaceFactory, selected_bundle
from .runner import (
    PROFILES,
    ModelProfile,
    _project_config_for_profile,
    _runtime_config_root,
    tool_metrics,
)
from .scenarios import scenario_by_id


def test_profiles_use_standard_model_family_tools() -> None:
    assert PROFILES["glm"].model == "glm-5.3-flash:cloud"
    assert PROFILES["glm"].tool_fragment == "/claude-tools"
    assert PROFILES["gpt"].model == "gpt-5.6-luna"
    assert PROFILES["gpt"].tool_fragment == "/codex-tools"


def test_request_overrides_enable_canonical_task_guidance(tmp_path: Path) -> None:
    profile = PROFILES["gpt"]
    overrides = profile.request_overrides(
        tmp_path,
        reasoning_effort="xhigh",
    )

    assert overrides["include_tasks"] is True
    assert overrides["working_directory"] == str(tmp_path)
    assert overrides["reasoning_effort"] == "xhigh"

    assessment = profile.request_overrides(
        tmp_path,
        reasoning_effort="high",
        include_tasks=False,
    )
    assert assessment["include_tasks"] is False


def test_tool_metrics_separate_investigation_and_mutation_calls() -> None:
    metrics = tool_metrics(
        (
            {"tool_name": "Read", "is_mutation": False},
            {"tool_name": "rg", "is_mutation": False},
            {"tool_name": "shell", "is_mutation": False},
            {"tool_name": "apply_patch", "is_mutation": True},
        )
    )

    assert metrics == {
        "total": 4,
        "mutation": 1,
        "read": 1,
        "search": 1,
        "list": 0,
        "shell": 1,
        "other": 1,
    }


def test_model_profile_is_immutable() -> None:
    profile = ModelProfile(
        name="demo",
        agent_id="demo",
        model="demo",
        auth_mode=None,
        tool_fragment="/tool",
        provider_fragments=(),
    )

    assert profile.model == "demo"


def test_runtime_config_and_profile_projection_use_selected_tool_families(
    tmp_path: Path,
) -> None:
    runtime = _runtime_config_root(
        bundle=selected_bundle(),
        artifact_root=tmp_path,
    )
    assert "Task Files and Subtasks" in runtime.joinpath(
        "TASKS_v7.md"
    ).read_text(encoding="utf-8")

    glm_path = _project_config_for_profile(
        runtime / "config.json",
        artifact_root=tmp_path,
        profile=PROFILES["glm"],
    )
    glm = json.loads(glm_path.read_text(encoding="utf-8"))
    assert any("/claude-tools" in item for item in glm["plugins"])
    assert not any("/codex-tools" in item for item in glm["plugins"])

    gpt_path = _project_config_for_profile(
        runtime / "config.json",
        artifact_root=tmp_path,
        profile=PROFILES["gpt"],
    )
    gpt = json.loads(gpt_path.read_text(encoding="utf-8"))
    assert any("/codex-tools" in item for item in gpt["plugins"])
    assert not any("/claude-tools" in item for item in gpt["plugins"])


def test_workspace_factory_compiles_project_guidance(tmp_path: Path) -> None:
    scenario = scenario_by_id("tg04-flask-vue-discovery-decomposition")
    factory = TaskGuidanceWorkspaceFactory(
        scenario=scenario,
        bundle=selected_bundle(),
    )
    workspace = factory(tmp_path / "workspace")
    try:
        agents = workspace.joinpath("AGENTS.md").read_text(encoding="utf-8")
        assert "Vue Books application" in agents
        assert "## Testing" in agents
        assert workspace.joinpath(".guidance-lock.json").is_file()
        assert workspace.joinpath("client/src/components/Books.vue").is_file()
    finally:
        factory.cleanup(workspace)