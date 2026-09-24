from __future__ import annotations

from .configuration import selected_bundle
from .handoffs import CanonicalHandoffWorkspaceFactory
from .scenarios import SCENARIOS


def test_bounded_scenarios_have_retain_and_omit_handoffs() -> None:
    bounded = [scenario for scenario in SCENARIOS if scenario.category == "handoff"]
    assert len(bounded) == 3
    for scenario in bounded:
        for variant in ("retain", "omit"):
            factory = CanonicalHandoffWorkspaceFactory(
                scenario=scenario,
                variant=variant,
                bundle=selected_bundle(),
            )
            text = factory.source_path.read_text(encoding="utf-8")
            assert "## Requirements checklist" in text
            if variant == "retain":
                assert "## Execution plan" in text
                assert "Status: Draft" in text
            else:
                assert "## Execution plan" not in text


def test_incomplete_handoff_is_an_explicit_negative_control() -> None:
    scenario = next(
        scenario
        for scenario in SCENARIOS
        if scenario.scenario_id == "tg02-fastapi-pagination-handoff"
    )
    factory = CanonicalHandoffWorkspaceFactory(
        scenario=scenario,
        variant="incomplete",
        bundle=selected_bundle(),
    )
    text = factory.source_path.read_text(encoding="utf-8")

    assert "## Requirements checklist" in text
    assert "src/app/api/notes.py" not in text
    assert "requirement question" not in text.lower()
    assert "production" not in text.lower()
