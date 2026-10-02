from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from agent_app.application_future import AgentApplication
from agent_app.session_filters import (
    coerce_session_list_filter_input,
    evaluate_session_list_filters,
    normalize_session_list_filter_schema,
)
from agent_core import AgentCore, Message, Session

from .dummy_provider import DummyProvider  # noqa: F401
from .fixtures.session_filters_app_plugin import (  # noqa: F401
    ConflictingSessionSearchFixturePlugin,
    SessionFiltersFixturePlugin,
)


_FILTER_CASES_PATH = (
    Path(__file__).resolve().parents[3]
    / "test"
    / "fixture"
    / "session-list"
    / "v1"
    / "filter-cases.json"
)
_OPEN_APPLICATIONS: List[AgentApplication] = []


@pytest.fixture(autouse=True)
def _close_test_applications() -> Any:
    yield
    while _OPEN_APPLICATIONS:
        _OPEN_APPLICATIONS.pop().close()


def _make_config(tmp_path: Path, *, conflict: bool = False) -> Path:
    plugins = [
        "tests.dummy_provider.DummyProvider",
        "tests.fixtures.session_filters_app_plugin.SessionFiltersFixturePlugin",
    ]
    if conflict:
        plugins.append(
            "tests.fixtures.session_filters_app_plugin."
            "ConflictingSessionSearchFixturePlugin"
        )
    config = {
        "providers": {
            "dummy": {
                "provider": "dummy_provider",
                "model": "test-model",
            }
        },
        "plugins": plugins,
        "agents": {"default": {"provider": "dummy"}},
    }
    path = tmp_path / "filters-config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def _new_application(tmp_path: Path, *, conflict: bool = False) -> AgentApplication:
    app = AgentApplication(
        _make_config(tmp_path, conflict=conflict),
        tmp_path / "sessions",
        core_factory=AgentCore,
    )
    _OPEN_APPLICATIONS.append(app)
    return app


def _save_session(
    app: AgentApplication,
    *,
    session_id: str,
    preview: str,
    metadata: Dict[str, Any],
) -> None:
    app.save_session(
        Session(
            session_id=session_id,
            messages=(
                Message(role="system", content="system"),
                Message(role="user", content=preview),
            ),
            metadata={"agent_id": "default", **metadata},
        )
    )


# Requirements:
# - SLIST-007: Verifies normalization, schema conflicts, typed matching, and defaults.
def test_python_uses_shared_filter_contract_cases() -> None:
    fixtures = json.loads(_FILTER_CASES_PATH.read_text(encoding="utf-8"))

    for case in fixtures["normalization_cases"]:
        schema = normalize_session_list_filter_schema([case["raw"]])
        is_valid = len(schema.filters) == 1
        assert is_valid is case["expected"]["valid"], case["name"]
        if is_valid:
            declaration = schema.filters[0]
            assert declaration.filter_type == case["expected"]["type"], case["name"]
            assert declaration.main_search is case["expected"]["main_search"], case[
                "name"
            ]
        else:
            assert case["expected"]["diagnostic_code"] in {
                diagnostic.code for diagnostic in schema.diagnostics
            }, case["name"]

    for case in fixtures["schema_cases"]:
        schema = normalize_session_list_filter_schema(case["elements"])
        assert [declaration.element_id for declaration in schema.filters] == case[
            "expected"
        ]["filter_ids"], case["name"]
        assert schema.main_search_id == case["expected"]["main_search_id"], case["name"]
        assert (
            schema.main_search_conflict is case["expected"]["main_search_conflict"]
        ), case["name"]
        diagnostic_code = case["expected"].get("diagnostic_code")
        if diagnostic_code:
            assert diagnostic_code in {
                diagnostic.code for diagnostic in schema.diagnostics
            }, case["name"]

    for case in fixtures["evaluation_cases"]:
        schema = normalize_session_list_filter_schema(case["elements"])
        result = evaluate_session_list_filters(
            case["sessions"],
            schema=schema,
            filter_values=case["values"],
            apply_filter_defaults=case["apply_defaults"],
        )
        assert [summary["session_id"] for summary in result.summaries] == case[
            "expected_ids"
        ], case["name"]


# Requirements:
# - SLIST-007: Confirms normalized select options preserve supported tone metadata.
def test_filter_contract_accepts_highlight_option_tone() -> None:
    schema = normalize_session_list_filter_schema(
        [
            {
                "ui_type": "session_list_filter",
                "id": "pinned_state",
                "label": "Pinned",
                "data": "metadata.pinned",
                "type": "boolean",
                "match": "equals",
                "options": [
                    {"value": False, "label": "Not pinned", "tone": "muted"},
                    {"value": True, "label": "Pinned", "tone": "highlight"},
                ],
            }
        ]
    )

    assert schema.diagnostics == ()
    assert schema.filters[0].options[1].tone == "highlight"


def test_datetime_filter_terminal_input_requires_timezone_or_any() -> None:
    schema = normalize_session_list_filter_schema(
        [
            {
                "ui_type": "session_list_filter",
                "id": "modified_after",
                "label": "Modified after",
                "data": "modified",
                "type": "datetime",
                "match": "on_or_after",
            }
        ]
    )
    declaration = schema.filters[0]

    assert (
        coerce_session_list_filter_input(
            declaration,
            "2026-09-01T02:00:00+02:00",
        )
        == "2026-09-01T02:00:00+02:00"
    )
    assert coerce_session_list_filter_input(declaration, "any") is None
    with pytest.raises(ValueError, match="timezone-aware"):
        coerce_session_list_filter_input(
            declaration,
            "2026-09-01T00:00:00",
        )


# Requirements:
# - SLIST-007: Confirms defaults and search preserve ordering and precede the limit.
def test_application_applies_defaults_search_and_limit_after_ordering(
    tmp_path: Path,
) -> None:
    app = _new_application(tmp_path)
    _save_session(
        app,
        session_id="older-visible",
        preview="ordinary alpha",
        metadata={"title": "Alpha title"},
    )
    _save_session(
        app,
        session_id="newer-archived",
        preview="archived alpha",
        metadata={"archived": True, "title": "Archived title"},
    )

    unfiltered = app.list_session_summaries()
    assert {summary["session_id"] for summary in unfiltered} == {
        "older-visible",
        "newer-archived",
    }

    default_filtered = app.list_session_summaries(
        apply_filter_defaults=True,
    )
    assert [summary["session_id"] for summary in default_filtered] == ["older-visible"]

    searched = app.list_session_summaries(
        filter_values={"session_search": "ALPHA"},
        apply_filter_defaults=True,
        limit=1,
    )
    assert [summary["session_id"] for summary in searched] == ["older-visible"]
    assert app.get_session_summary("newer-archived")["session_id"] == ("newer-archived")


# Requirements:
# - SLIST-001: Exercises normalized filter schema access through AgentApplication.
# - SLIST-007: Confirms conflicting main searches do not remove unrelated filters.
# - SLIST-008: Confirms schema conflicts are nonfatal and produce diagnostics.
def test_application_reports_main_search_conflict_without_losing_other_filters(
    tmp_path: Path,
) -> None:
    app = _new_application(tmp_path, conflict=True)
    schema = app.get_session_list_filter_schema()

    assert schema["main_search_id"] is None
    assert schema["main_search_conflict"] is True
    assert [declaration["id"] for declaration in schema["filters"]] == ["archived"]
    assert "ambiguous_session_list_main_search" in {
        diagnostic["code"] for diagnostic in schema["diagnostics"]
    }
