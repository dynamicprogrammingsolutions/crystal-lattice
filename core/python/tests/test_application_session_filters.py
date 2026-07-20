from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from agent_app.application_future import AgentApplication
from agent_app.session_filters import (
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
