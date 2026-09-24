"""Configuration well-formedness and consumer-derivation tests.

``configuration.json`` is the single declaration of what the evaluation
is: the agents with their pinned runtime-config fixtures, the scenario
categories with their producer matrices and stage lists, and the default
directories. These tests verify the suite *through* the manifest: the
manifest is checked against the scenario data and the stage catalog, the
pinned fixtures are checked against the manifest, consumer expectations
are checked against configuration-derived values, and no test duplicates
literal agent or matrix values.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from .. import (
    fixtures,
    freeze,
    handoff_semantic,
    result_package,
    results,
    runner,
    semantic,
)
from ..configuration import (
    AGENTS,
    CATEGORIES,
    DEFAULT_ARTIFACT_ROOT,
    DEFAULT_BUNDLE,
    GUIDANCE_TARGET,
    PACKAGES_ROOT,
    REPOSITORY_ROOT,
    SCENARIOS_ROOT,
    SUITE_ROOT,
    all_producer_cells,
    assessment_cell,
    negative_control,
    negative_control_designations,
    plan_variants,
    producer_cells,
    selected_artifact_root,
    selected_bundle,
    stage_config,
)
from ..handoff_semantic import load_handoff_records
from ..results import consolidate_results
from ..scenarios import SCENARIOS, scenario_by_id
from ..stages import STAGES


def scenario_by_category() -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for scenario in SCENARIOS:
        grouped.setdefault(scenario.category, []).append(scenario.scenario_id)
    return grouped


def fixture_config(agent_name: str) -> dict:
    path = SUITE_ROOT / AGENTS[agent_name]["config"]
    return json.loads(path.read_text(encoding="utf-8"))


# --- Well-formedness of the manifest -------------------------------------


def test_every_declared_scenario_exists_and_belongs_to_its_category() -> None:
    declared = {
        category: list(spec["scenarios"]) for category, spec in CATEGORIES.items()
    }
    actual = scenario_by_category()
    assert declared == actual


def test_every_scenario_category_is_declared() -> None:
    assert set(CATEGORIES) == {scenario.category for scenario in SCENARIOS}


def test_every_producer_cell_references_a_declared_agent() -> None:
    for spec in CATEGORIES.values():
        for cell in spec["producer_cells"]:
            assert cell["agent"] in AGENTS


def test_every_producer_cell_effort_is_declared_for_its_agent() -> None:
    for spec in CATEGORIES.values():
        for cell in spec["producer_cells"]:
            assert cell["effort"] in AGENTS[cell["agent"]]["efforts"]


def test_producer_cells_are_unique_per_category() -> None:
    for category in CATEGORIES:
        cells = producer_cells(category)
        assert len(cells) == len(set(cells)), category


def test_every_declared_effort_is_exercised_somewhere() -> None:
    exercised = {
        (cell["agent"], cell["effort"])
        for spec in CATEGORIES.values()
        for cell in spec["producer_cells"]
    }
    for name, agent in AGENTS.items():
        for effort in agent["efforts"]:
            assert (name, effort) in exercised, (name, effort)


def test_agents_declare_unique_runtime_identities() -> None:
    agent_ids = [agent["agent_id"] for agent in AGENTS.values()]
    assert len(agent_ids) == len(set(agent_ids))
    for agent in AGENTS.values():
        assert agent["model"]
        assert agent["efforts"]


def test_stage_names_come_from_the_catalog() -> None:
    for spec in CATEGORIES.values():
        for name in spec["stages"]:
            assert name in STAGES, name


def test_stage_configs_match_their_catalog_schema() -> None:
    for category, spec in CATEGORIES.items():
        for name, config in spec["stages"].items():
            expected = set(STAGES[name].config)
            assert set(config) == expected, (category, name)


def test_assessment_stages_declare_a_valid_judging_cell() -> None:
    for category, spec in CATEGORIES.items():
        for name, config in spec["stages"].items():
            if set(STAGES[name].config) != {"agent", "effort"}:
                continue
            agent, effort = assessment_cell(category, name)
            assert agent in AGENTS
            assert effort in AGENTS[agent]["efforts"]


def test_all_assessment_stages_share_one_judging_cell() -> None:
    cells = {
        assessment_cell(category, name)
        for category, spec in CATEGORIES.items()
        for name in spec["stages"]
        if set(STAGES[name].config) == {"agent", "effort"}
    }
    assert len(cells) == 1


def test_negative_control_designation_is_well_formed() -> None:
    for category in CATEGORIES:
        control = negative_control(category)
        if control is None:
            continue
        assert control["scenario"] in CATEGORIES[category]["scenarios"]
        assert (control["agent"], control["effort"]) in set(producer_cells(category))
        assert control["agent"] in AGENTS
        assert control["effort"] in AGENTS[control["agent"]]["efforts"]
        assert control["variant"] not in plan_variants(category)


def test_negative_controls_run_only_with_handoff_planning() -> None:
    for category, spec in CATEGORIES.items():
        if negative_control(category) is None:
            continue
        assert "handoff-plan" in spec["stages"], category
        assert plan_variants(category), category


def test_default_directories_are_distinct_repository_paths() -> None:
    directories = (
        DEFAULT_ARTIFACT_ROOT,
        DEFAULT_BUNDLE,
        GUIDANCE_TARGET,
        PACKAGES_ROOT,
        SCENARIOS_ROOT,
    )
    assert len(directories) == len(set(directories))
    for directory in directories:
        assert directory.is_relative_to(REPOSITORY_ROOT)


def test_default_directories_exist_in_the_repository() -> None:
    assert DEFAULT_BUNDLE.is_dir()
    assert GUIDANCE_TARGET.is_dir()
    assert PACKAGES_ROOT.is_dir()
    assert SCENARIOS_ROOT.is_dir()


def test_selected_directories_honor_environment_overrides(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = tmp_path / "bundle"
    artifact_root = tmp_path / "artifacts"
    monkeypatch.setenv("AGENT_EVAL_GUIDANCE_BUNDLE", str(bundle))
    monkeypatch.setenv("AGENT_EVAL_ARTIFACT_ROOT", str(artifact_root))

    assert selected_bundle() == bundle
    assert selected_artifact_root() == artifact_root


def test_selected_directories_default_without_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AGENT_EVAL_GUIDANCE_BUNDLE", raising=False)
    monkeypatch.delenv("AGENT_EVAL_ARTIFACT_ROOT", raising=False)

    assert selected_bundle() == DEFAULT_BUNDLE
    assert selected_artifact_root() == DEFAULT_ARTIFACT_ROOT


# --- Pinned runtime-config fixtures ---------------------------------------


def test_every_agent_fixture_pins_exactly_its_declared_agent() -> None:
    for name, agent in AGENTS.items():
        config = fixture_config(name)
        assert set(config["agents"]) == {agent["agent_id"]}
        entry = config["agents"][agent["agent_id"]]
        assert entry["model"] == agent["model"]
        assert isinstance(config["plugins"], list) and config["plugins"]
        assert "plugin_cache_dir" not in config


def test_the_authentication_method_lives_only_in_the_fixture() -> None:
    glm_entry = fixture_config("glm")["agents"][AGENTS["glm"]["agent_id"]]
    gpt_entry = fixture_config("gpt")["agents"][AGENTS["gpt"]["agent_id"]]
    assert "auth_mode" not in glm_entry
    assert gpt_entry["auth_mode"] == "chatgpt"
    assert gpt_entry["chatgpt_credentials_path"] == (
        "${env:CHATGPT_TEST_STATE_DIR}/auth/chatgpt-auth.json"
    )


def test_fixture_tool_families_pin_the_declared_agents() -> None:
    glm_plugins = fixture_config("glm")["plugins"]
    gpt_plugins = fixture_config("gpt")["plugins"]
    assert any("/claude-tools" in item for item in glm_plugins)
    assert not any("/codex-tools" in item for item in glm_plugins)
    assert any("/codex-tools" in item for item in gpt_plugins)
    assert not any("/claude-tools" in item for item in gpt_plugins)


# --- Consumer derivation --------------------------------------------------


def test_semantic_expectations_derive_from_the_configuration() -> None:
    for scenario in SCENARIOS:
        assert semantic.expected_producer_cells(scenario) == producer_cells(
            scenario.category
        )


def _write_record(
    root: Path,
    agent: str,
    name: str,
    run_id: str,
    value: dict[str, object],
) -> None:
    path = root / agent / "runs" / run_id / "records" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _producer_record(
    scenario_id: str,
    agent: str,
    effort: str,
    *,
    variant: str | None = None,
    attempt: str = "r1",
) -> dict[str, object]:
    record: dict[str, object] = {
        "scenario_id": scenario_id,
        "producer": {"profile": agent, "reasoning_effort": effort},
        "run_attempt": attempt,
        "valid": True,
        "invalid_reasons": [],
        "task_files": {},
    }
    if variant is not None:
        record["variant"] = variant
    return record


def test_results_expected_sets_match_the_configuration(tmp_path: Path) -> None:
    for scenario in SCENARIOS:
        category = scenario.category
        cells = producer_cells(category)
        for agent, effort in cells:
            _write_record(
                tmp_path,
                agent,
                STAGES["task-creation"].record,
                f"{scenario.scenario_id}-{effort}",
                _producer_record(scenario.scenario_id, agent, effort),
            )
        if "handoff-plan" not in CATEGORIES[category]["stages"]:
            continue
        for variant in plan_variants(category):
            for agent, effort in cells:
                _write_record(
                    tmp_path,
                    agent,
                    STAGES["handoff-plan"].record,
                    f"{scenario.scenario_id}-{variant}-{effort}",
                    _producer_record(
                        scenario.scenario_id,
                        agent,
                        effort,
                        variant=variant,
                    ),
                )
        for agent, effort in cells:
            _write_record(
                tmp_path,
                agent,
                STAGES["continuation"].record,
                f"{scenario.scenario_id}-same-{effort}",
                _producer_record(scenario.scenario_id, agent, effort),
            )
    for control in negative_control_designations():
        _write_record(
            tmp_path,
            control["agent"],
            STAGES["negative-control"].record,
            "negative-control",
            _producer_record(
                control["scenario"],
                control["agent"],
                control["effort"],
                variant=control["variant"],
            ),
        )

    value = consolidate_results(tmp_path)
    status = value["status"]

    expected_producers = sum(
        len(producer_cells(scenario.category)) for scenario in SCENARIOS
    )
    assert status["producers"]["expected"] == expected_producers
    assert status["producers"]["missing"] == []

    planning_scenarios = [
        scenario
        for scenario in SCENARIOS
        if "handoff-plan" in CATEGORIES[scenario.category]["stages"]
    ]
    expected_handoffs = sum(
        len(plan_variants(scenario.category)) * len(producer_cells(scenario.category))
        for scenario in planning_scenarios
    )
    assert status["handoffs"]["expected"] == expected_handoffs
    assert status["handoffs"]["missing"] == []

    expected_continuations = sum(
        len(producer_cells(scenario.category)) for scenario in planning_scenarios
    )
    assert status["same_agent"]["expected"] == expected_continuations
    assert status["same_agent"]["missing"] == []

    assert status["negative_controls"]["expected"] == len(
        negative_control_designations()
    )
    assert status["negative_controls"]["missing"] == []


def test_handoff_semantic_expected_records_match_the_configuration(
    tmp_path: Path,
) -> None:
    control_scenario_id = negative_control_designations()[0]["scenario"]
    control = scenario_by_id(control_scenario_id)
    other = next(
        scenario
        for scenario in SCENARIOS
        if scenario.category == control.category
        and scenario.scenario_id != control_scenario_id
    )
    for scenario in (control, other):
        category = scenario.category
        cells = producer_cells(category)
        for variant in plan_variants(category):
            for agent, effort in cells:
                _write_record(
                    tmp_path,
                    agent,
                    STAGES["handoff-plan"].record,
                    f"{scenario.scenario_id}-{variant}-{effort}",
                    _producer_record(
                        scenario.scenario_id,
                        agent,
                        effort,
                        variant=variant,
                        attempt="h1",
                    ),
                )
        for agent, effort in cells:
            _write_record(
                tmp_path,
                agent,
                STAGES["continuation"].record,
                f"{scenario.scenario_id}-same-{effort}",
                _producer_record(
                    scenario.scenario_id,
                    agent,
                    effort,
                    attempt="p1",
                ),
            )
    designation = negative_control(control.category)
    assert designation is not None
    _write_record(
        tmp_path,
        designation["agent"],
        STAGES["negative-control"].record,
        "negative-control",
        _producer_record(
            designation["scenario"],
            designation["agent"],
            designation["effort"],
            variant=designation["variant"],
            attempt="h1",
        ),
    )

    for scenario, expected_negative in ((control, 1), (other, 0)):
        fresh, same = load_handoff_records(
            tmp_path,
            scenario=scenario,
            labels=None,
            allow_partial=False,
        )
        cells = producer_cells(scenario.category)
        assert (
            len(fresh)
            == len(plan_variants(scenario.category)) * len(cells) + expected_negative
        )
        assert len(same) == len(cells)


# --- Single-source ownership ----------------------------------------------


CONSUMER_MODULES = (
    fixtures,
    freeze,
    handoff_semantic,
    result_package,
    results,
    runner,
    semantic,
)

MATRIX_LITERALS = (
    '"glm", "max"',
    '"gpt", "high"',
    '"gpt", "xhigh"',
    '"gpt", "max"',
    '["retain", "omit"]',
    '"tg02-fastapi-pagination-handoff"',
    "PROFILES",
    "ASSESSOR_CELL",
    "HANDOFF_VARIANTS",
)

DIRECTORY_DEFINITIONS = (
    "DEFAULT_ARTIFACT_ROOT =",
    "DEFAULT_BUNDLE =",
    "DEFAULT_PACKAGES_ROOT =",
    "DEFAULT_SCENARIOS_ROOT =",
    "CRYSTAL_LATTICE_TARGET =",
)


def test_no_duplicated_matrix_literals_remain_in_consumers() -> None:
    for module in CONSUMER_MODULES:
        source = Path(module.__file__).read_text(encoding="utf-8")
        for literal in MATRIX_LITERALS:
            assert literal not in source, (module.__name__, literal)


def test_default_directories_are_declared_only_in_the_configuration() -> None:
    for module in CONSUMER_MODULES:
        source = Path(module.__file__).read_text(encoding="utf-8")
        for definition in DIRECTORY_DEFINITIONS:
            assert definition not in source, (module.__name__, definition)


def test_record_names_are_declared_only_in_the_stage_catalog() -> None:
    for module in CONSUMER_MODULES:
        source = Path(module.__file__).read_text(encoding="utf-8")
        for spec in STAGES.values():
            assert spec.record not in source, (module.__name__, spec.record)


def test_all_producer_cells_are_distinct_and_ordered() -> None:
    cells = all_producer_cells()
    assert len(cells) == len(set(cells))
    expected: list[tuple[str, str]] = []
    for category in CATEGORIES:
        for pair in producer_cells(category):
            if pair not in expected:
                expected.append(pair)
    assert cells == tuple(expected)


def test_stage_config_requires_a_declared_stage() -> None:
    with pytest.raises(KeyError):
        stage_config("handoff", "no-such-stage")
