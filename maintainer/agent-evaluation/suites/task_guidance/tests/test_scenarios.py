from __future__ import annotations

from ..scenarios import SCENARIOS, scenario_by_id


def test_scenario_contracts_are_complete_and_unique() -> None:
    assert len(SCENARIOS) == 10
    assert len({scenario.scenario_id for scenario in SCENARIOS}) == 10
    assert [scenario.category for scenario in SCENARIOS].count("handoff") == 3
    assert [scenario.category for scenario in SCENARIOS].count("decomposition") == 3
    assert [scenario.category for scenario in SCENARIOS].count("kind") == 4

    for scenario in SCENARIOS:
        assert scenario.markdown_path.is_file()
        assert scenario.target_path.is_file()
        assert scenario.prompt
        target = scenario.target
        assert target["project"]["fixture_id"] == scenario.fixture_id
        assert scenario_by_id(scenario.scenario_id) is scenario


def test_complex_targets_have_coherent_partitions_and_fragmentation_pressure() -> None:
    for scenario in SCENARIOS:
        target = scenario.target
        if scenario.category != "decomposition":
            assert target["acceptable_partition_sizes"] == [1]
            continue
        assert 4 in target["acceptable_partition_sizes"]
        assert len(target["coherent_deliverables"]) == 4
        assert len(target["fragmentation_examples"]) >= 4
        assert target["important_crossings"]
