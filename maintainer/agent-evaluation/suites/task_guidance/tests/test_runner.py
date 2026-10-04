from __future__ import annotations

import json
from pathlib import Path

import pytest

from ..configuration import AGENTS, SUITE_ROOT, selected_bundle, thinking_variants
from ..fixtures import TaskGuidanceWorkspaceFactory
from ..runner import (
    CREATION_VARIANTS,
    FROM_PLAN_PROMPTS,
    PLANNING_SESSION_SUFFIX,
    PLANNING_VARIANTS,
    RUNNER_VERSION,
    TaskGuidanceHarness,
    _runtime_config_root,
    request_overrides,
    tool_metrics,
)
from ..scenarios import scenario_by_id
from ..stages import STAGES


def test_pinned_runtime_configs_pin_the_standard_tool_families() -> None:
    glm = json.loads((SUITE_ROOT / AGENTS["glm"]["config"]).read_text(encoding="utf-8"))
    assert any("/claude-tools" in item for item in glm["plugins"])
    assert not any("/codex-tools" in item for item in glm["plugins"])
    assert glm["agents"][AGENTS["glm"]["agent_id"]]["model"] == AGENTS["glm"]["model"]

    gpt = json.loads((SUITE_ROOT / AGENTS["gpt"]["config"]).read_text(encoding="utf-8"))
    assert any("/codex-tools" in item for item in gpt["plugins"])
    assert not any("/claude-tools" in item for item in gpt["plugins"])
    assert gpt["agents"][AGENTS["gpt"]["agent_id"]]["model"] == AGENTS["gpt"]["model"]
    # The authentication method is pinned by the fixture, not by code.
    assert gpt["agents"][AGENTS["gpt"]["agent_id"]]["auth_mode"] == "chatgpt"


def test_request_overrides_enable_canonical_task_guidance(tmp_path: Path) -> None:
    overrides = request_overrides(
        "gpt",
        tmp_path,
        reasoning_effort="xhigh",
    )

    assert overrides["include_tasks"] is True
    assert overrides["working_directory"] == str(tmp_path)
    assert overrides["reasoning_effort"] == "xhigh"
    assert "auth_mode" not in overrides
    assert "chatgpt_credentials_path" not in overrides

    glm = request_overrides("glm", tmp_path, reasoning_effort="max")
    assert glm["request_options"] == {"reasoning_effort": "max"}

    assessment = request_overrides(
        "gpt",
        tmp_path,
        reasoning_effort="high",
        include_tasks=False,
    )
    assert assessment["include_tasks"] is False


def test_two_stage_pipeline_declares_its_variants_and_asks() -> None:
    # The planning arm is exactly the guidance on/off pair; the delivery
    # evidence of an unguided planning turn records include_tasks False.
    assert PLANNING_VARIANTS == ("guided", "unguided")
    assert PLANNING_SESSION_SUFFIX.lstrip().startswith("Investigate")

    # Every creation variant has its own distinct continuation ask.
    assert sorted(CREATION_VARIANTS) == sorted(FROM_PLAN_PROMPTS)
    assert len(set(FROM_PLAN_PROMPTS.values())) == len(FROM_PLAN_PROMPTS)
    assert "execution-plan" in FROM_PLAN_PROMPTS["omit-plan"]
    assert "execution-plan" not in FROM_PLAN_PROMPTS["standard"]


def test_thinking_variants_declare_the_reasoning_state_dimension() -> None:
    # GLM cells run both ways; GPT keeps provider-default thinking (the
    # documented plugin limitation).
    assert thinking_variants("glm") == ("preserve", "strip")
    assert thinking_variants("gpt") == ()


def test_strip_thinking_config_variant_loads_the_plugin_for_ollama(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ..configuration import agent_config_file

    plugin = "path:${env:BUILTIN_PLUGINS}/interleaved-thinking"
    monkeypatch.setenv("TASK_GUIDANCE_GLM_PROVIDER", "ollama")
    path = agent_config_file(
        "glm",
        artifact_root=tmp_path,
        version=RUNNER_VERSION,
        thinking="strip",
    )
    config = json.loads(path.read_text(encoding="utf-8"))
    assert plugin in config["plugins"]
    assert path.name == f"glm-{RUNNER_VERSION}-strip.json"

    # zai manages reasoning server-side: strip is its default behavior,
    # so no plugin joins the config and the file keeps its own identity.
    monkeypatch.setenv("TASK_GUIDANCE_GLM_PROVIDER", "zai")
    zai = agent_config_file(
        "glm",
        artifact_root=tmp_path,
        version=RUNNER_VERSION,
        thinking="strip",
    )
    zai_config = json.loads(zai.read_text(encoding="utf-8"))
    assert plugin not in zai_config["plugins"]


def test_request_overrides_map_thinking_onto_provider_mechanisms(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("TASK_GUIDANCE_GLM_PROVIDER", raising=False)
    preserve = request_overrides(
        "glm",
        tmp_path,
        reasoning_effort="max",
        thinking="preserve",
    )
    assert preserve["request_options"]["thinking"] == {
        "type": "enabled",
        "clear_thinking": False,
    }
    strip = request_overrides(
        "glm",
        tmp_path,
        reasoning_effort="max",
        thinking="strip",
    )
    assert "thinking" not in strip["request_options"]

    # ollama preserves inline thinking by default: preserve is not a
    # request option there (strip is the config-variant plugin).
    monkeypatch.setenv("TASK_GUIDANCE_GLM_PROVIDER", "ollama")
    ollama = request_overrides(
        "glm",
        tmp_path,
        reasoning_effort="max",
        thinking="preserve",
    )
    assert "thinking" not in ollama["request_options"]


def test_harness_rejects_unknown_thinking_variants(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AGENT_EVAL_ARTIFACT_ROOT", str(tmp_path))
    with pytest.raises(ValueError, match="unknown thinking variant"):
        TaskGuidanceHarness("glm", thinking="nonsense")


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


# The two-stage pipeline executors (subtask 125) landed with their stage
# catalog entries; every catalog executor is expected on the harness again.


def test_every_stage_executor_exists_on_the_harness() -> None:
    for spec in STAGES.values():
        assert hasattr(TaskGuidanceHarness, spec.executor), spec.executor


def test_runtime_config_root_compiles_the_tasks_file(tmp_path: Path) -> None:
    runtime = _runtime_config_root(
        bundle=selected_bundle(),
        artifact_root=tmp_path,
    )
    assert "Task Files and Subtasks" in runtime.joinpath("TASKS_v7.md").read_text(
        encoding="utf-8"
    )


def test_harness_builds_from_the_pinned_fixture(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("AGENT_EVAL_ARTIFACT_ROOT", str(tmp_path))
    harness = TaskGuidanceHarness("glm")
    try:
        assert harness.agent_name == "glm"
        assert harness.agent["agent_id"] == "glm-ollama"
        # The pinned fixture's agent entry, with the auth method it declares.
        assert harness.runtime_agent["model"] == AGENTS["glm"]["model"]
        assert "auth_mode" not in harness.runtime_agent
        resolved = tmp_path / "agent-config" / f"glm-{RUNNER_VERSION}.json"
        assert resolved.is_file()
        assert json.loads(resolved.read_text(encoding="utf-8"))["plugin_cache_dir"] == (
            str(tmp_path / "plugin-cache" / "glm" / RUNNER_VERSION)
        )
    finally:
        harness.close()


def test_agent_config_file_applies_the_artifact_plugin_cache(
    tmp_path: Path,
) -> None:
    from ..configuration import agent_config_file

    path = agent_config_file("glm", artifact_root=tmp_path, version=RUNNER_VERSION)
    config = json.loads(path.read_text(encoding="utf-8"))
    assert config["plugin_cache_dir"] == str(
        tmp_path / "plugin-cache" / "glm" / RUNNER_VERSION
    )
    fixture = json.loads(
        (SUITE_ROOT / AGENTS["glm"]["config"]).read_text(encoding="utf-8")
    )
    assert config["agents"] == fixture["agents"]
    assert config["plugins"] == fixture["plugins"]


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
