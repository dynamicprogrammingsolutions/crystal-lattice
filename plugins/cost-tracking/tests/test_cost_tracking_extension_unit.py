"""Unit tests for the generic cost tracking extension."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pytest

from cost_tracking_plugins.cost_tracking_extension import CostTrackingExtension


def _final(
    *,
    response_id: str = "resp_1",
    usage: Dict[str, Any] | None = None,
    bucket: str = "openai-responses-chatgpt",
    estimated_cost: float = 0.5,
    with_cost_stamp: bool = False,
) -> Dict[str, Any]:
    internal: Dict[str, Any] = {
        "response_id": response_id,
        "usage_bucket": bucket,
        "usage_total_cost": estimated_cost,
        "usage": usage
        or {
            "input_tokens": 100,
            "input_tokens_details": {"cached_tokens": 10},
            "output_tokens": 20,
            "output_tokens_details": {"reasoning_tokens": 5},
        },
    }
    if with_cost_stamp:
        internal["cost_session_total"] = 0.5
        internal["cost_session_total_formatted"] = "$0.500000"
        internal["cost_session_requests"] = 1
    return {"role": "assistant", "_metadata": internal}


def _make_state(
    tmp_path: Path, *, session_id: str = "s1", **config_extra
) -> Dict[str, Any]:
    config = {
        "model": "gpt-5-mini",
        "working_directory": "workspace/repo",
        "cost_tracking_db_path": str(tmp_path / "costs.sqlite3"),
    }
    config.update(config_extra)
    return {"config": config, "_request_context": {"session_id": session_id}}


def _db_path(tmp_path: Path) -> Path:
    return tmp_path / "costs.sqlite3"


def _summary_csv_path(tmp_path: Path) -> Path:
    return _db_path(tmp_path).with_name("cost-tracking-summary.csv")


def _summary_csv_rows(tmp_path: Path) -> List[Dict[str, Any]]:
    import csv

    with open(_summary_csv_path(tmp_path), encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_extension_requires_cost_tracking_tag() -> None:
    ext = CostTrackingExtension()
    assert ext.required_tags() == ["cost_tracking"]
    assert ext.get_tags({}, []) == ["ext:cost_tracking"]


def test_config_schema_defaults() -> None:
    schema = CostTrackingExtension().get_config_schema()
    assert schema["track_costs"]["default"] is True
    assert schema["show_cost_status_total"]["default"] is True
    assert schema["track_cost_tracking_summary_csv"]["default"] is True
    assert schema["total_usage_breakdown"]["default"] == "none"
    assert schema["total_usage_breakdown"]["options"] == [
        "none",
        "totals",
        "averages",
    ]
    assert schema["total_usage_breakdown"]["label"] == "Total usage breakdown"
    assert "cost_tracking_db_path" in schema
    assert "cost_tracking_summary_csv_path" in schema


def _total_element() -> Dict[str, Any]:
    return {
        "ui_type": "status_bar",
        "data": "metadata.cost_session_total_formatted",
        "template": "Total: {{data}}",
        "condition": {
            "path": "metadata.cost_session_total_formatted",
            "exists": True,
        },
    }


def _breakdown_element(data_path: str, template: str) -> Dict[str, Any]:
    return {
        "ui_type": "status_bar",
        "data": data_path,
        "template": template,
        "condition": {"path": data_path, "exists": True},
    }


def _config_element(default: str = "none") -> Dict[str, Any]:
    return {
        "ui_type": "config",
        "type": "select",
        "key": "total_usage_breakdown",
        "label": "Total usage breakdown",
        "description": (
            "Show the session cost breakdown as separate status bar fields."
        ),
        "options": [
            {"value": "none", "label": "None"},
            {"value": "totals", "label": "Totals"},
            {"value": "averages", "label": "Averages"},
        ],
        "default": default,
    }


def test_status_bar_element_and_gate() -> None:
    ext = CostTrackingExtension()

    # The config element is always contributed; default (none) keeps the
    # total footer unchanged.
    assert ext.get_ui_elements(config={}) == [_config_element(), _total_element()]
    assert ext.get_ui_elements(config={"total_usage_breakdown": "none"}) == [
        _config_element(),
        _total_element(),
    ]
    # Gating the status bar keeps the config setting editable in the UI.
    assert ext.get_ui_elements(config={"show_cost_status_total": False}) == [
        _config_element()
    ]
    # The config element's default reflects the current choice.
    assert ext.get_ui_elements(config={"total_usage_breakdown": "averages"})[0] == (
        _config_element(default="averages")
    )


def test_status_bar_elements_totals_choice() -> None:
    ext = CostTrackingExtension()

    elements = ext.get_ui_elements(config={"total_usage_breakdown": "totals"})
    assert elements == [
        _config_element(default="totals"),
        _total_element(),
        _breakdown_element(
            "metadata.cost_session_input_cost_formatted", "input: {{data}}"
        ),
        _breakdown_element(
            "metadata.cost_session_cached_cost_formatted", "cached input: {{data}}"
        ),
        _breakdown_element(
            "metadata.cost_session_cache_write_cost_formatted",
            "cache write: {{data}}",
        ),
        _breakdown_element(
            "metadata.cost_session_output_cost_formatted", "output: {{data}}"
        ),
        _breakdown_element(
            "metadata.cost_session_requests_formatted", "requests: {{data}}"
        ),
    ]


def test_status_bar_elements_averages_choice() -> None:
    ext = CostTrackingExtension()

    elements = ext.get_ui_elements(config={"total_usage_breakdown": "averages"})
    assert elements == [
        _config_element(default="averages"),
        _total_element(),
        _breakdown_element(
            "metadata.cost_session_requests_formatted", "requests: {{data}}"
        ),
        _breakdown_element(
            "metadata.cost_session_average_cost_formatted", "average: {{data}}"
        ),
        _breakdown_element(
            "metadata.cost_session_input_cost_avg_formatted", "input: {{data}}"
        ),
        _breakdown_element(
            "metadata.cost_session_cached_cost_avg_formatted",
            "cached input: {{data}}",
        ),
        _breakdown_element(
            "metadata.cost_session_cache_write_cost_avg_formatted",
            "cache write: {{data}}",
        ),
        _breakdown_element(
            "metadata.cost_session_output_cost_avg_formatted", "output: {{data}}"
        ),
    ]


def test_process_chunk_records_and_stamps_session_total(tmp_path: Path) -> None:
    ext = CostTrackingExtension()
    final = _final()
    state = _make_state(tmp_path)

    _partials, finals, new_native, _state = ext.process_chunk(
        native_chunk=None,
        partial_messages=[],
        final_messages=[final],
        native_messages=[final],
        state=state,
    )

    md = finals[0]["_metadata"]
    assert md["cost_session_total"] == pytest.approx(0.5)
    assert md["cost_session_total_formatted"] == "$0.500000"
    assert md["cost_session_requests"] == 1
    assert new_native[0]["_metadata"]["cost_session_total"] == pytest.approx(0.5)

    totals = cost_store_session_totals(tmp_path)
    assert totals["request_count"] == 1
    assert totals["total_cost"] == pytest.approx(0.5)


def cost_store_session_totals(tmp_path: Path) -> Dict[str, Any]:
    from cost_tracking_plugins import cost_store

    return cost_store.session_totals(
        _db_path(tmp_path),
        working_directory=str(Path.cwd() / "workspace" / "repo"),
        session_id="s1",
    )


def test_process_chunk_resolves_absolute_working_directory(tmp_path: Path) -> None:
    ext = CostTrackingExtension()
    state = _make_state(tmp_path)

    ext.process_chunk(
        native_chunk=None,
        partial_messages=[],
        final_messages=[_final()],
        native_messages=[_final()],
        state=state,
    )

    from cost_tracking_plugins import cost_store

    rows = cost_store.bucket_report(_db_path(tmp_path))
    assert rows["request_count"] == 1
    # The relative working directory was resolved against the server cwd.
    import sqlite3

    conn = sqlite3.connect(str(_db_path(tmp_path)))
    try:
        wd = conn.execute("SELECT working_directory FROM cost_requests").fetchone()[0]
    finally:
        conn.close()
    assert wd == str(Path.cwd() / "workspace" / "repo")


def test_finalize_non_stream_records_from_native_tail(tmp_path: Path) -> None:
    ext = CostTrackingExtension()
    native = [_final()]

    finals, new_native, _state = ext.finalize([], native, _make_state(tmp_path))

    assert finals == []
    assert new_native[0]["_metadata"]["cost_session_total"] == pytest.approx(0.5)
    assert cost_store_session_totals(tmp_path)["request_count"] == 1


def test_finalize_skips_already_stamped_streaming_items(tmp_path: Path) -> None:
    ext = CostTrackingExtension()
    stamped = _final(with_cost_stamp=True)

    _finals, new_native, _state = ext.finalize([], [stamped], _make_state(tmp_path))

    assert new_native[0]["_metadata"]["cost_session_requests"] == 1
    assert cost_store_session_totals(tmp_path)["request_count"] == 0


def test_finalize_records_when_finals_carry_unprocessed_usage(tmp_path: Path) -> None:
    ext = CostTrackingExtension()
    final = _final()

    finals, _new_native, _state = ext.finalize([final], [final], _make_state(tmp_path))

    assert finals[0]["_metadata"]["cost_session_total"] == pytest.approx(0.5)
    assert cost_store_session_totals(tmp_path)["request_count"] == 1


def test_finalize_skips_finals_already_stamped(tmp_path: Path) -> None:
    ext = CostTrackingExtension()
    final = _final(with_cost_stamp=True)

    finals, _new_native, _state = ext.finalize([final], [final], _make_state(tmp_path))

    assert cost_store_session_totals(tmp_path)["request_count"] == 0


def test_response_id_dedupes_across_refinalize(tmp_path: Path) -> None:
    ext = CostTrackingExtension()
    state = _make_state(tmp_path)

    ext.process_chunk(
        native_chunk=None,
        partial_messages=[],
        final_messages=[_final()],
        native_messages=[_final()],
        state=state,
    )
    # A rebuild re-presents the same response; the store dedupes it.
    ext.finalize([], [_final()], state)

    assert cost_store_session_totals(tmp_path)["request_count"] == 1
    # The summary CSV also stays deduplicated: only freshly inserted rows
    # append a CSV row.
    summary_rows = _summary_csv_rows(tmp_path)
    assert len(summary_rows) == 1


def test_track_costs_gate_disables_recording(tmp_path: Path) -> None:
    ext = CostTrackingExtension()

    _partials, finals, _new_native, _state = ext.process_chunk(
        native_chunk=None,
        partial_messages=[],
        final_messages=[_final()],
        native_messages=[_final()],
        state=_make_state(tmp_path, track_costs=False),
    )

    assert "cost_session_total" not in finals[0]["_metadata"]
    assert cost_store_session_totals(tmp_path)["request_count"] == 0
    assert not _summary_csv_path(tmp_path).exists()


def test_missing_bucket_or_usage_skips_recording(tmp_path: Path) -> None:
    ext = CostTrackingExtension()
    no_bucket = {"role": "assistant", "_metadata": {"usage": {"input_tokens": 1}}}
    no_usage = {"role": "assistant", "_metadata": {"usage_bucket": "b1"}}

    _partials, finals, _new_native, _state = ext.process_chunk(
        native_chunk=None,
        partial_messages=[],
        final_messages=[no_bucket, no_usage],
        native_messages=[no_bucket, no_usage],
        state=_make_state(tmp_path),
    )

    assert "cost_session_total" not in finals[0]["_metadata"]
    assert cost_store_session_totals(tmp_path)["request_count"] == 0


def test_actual_cost_recorded_and_estimated_skipped(tmp_path: Path) -> None:
    ext = CostTrackingExtension()
    usage = {
        "prompt_tokens": 50,
        "completion_tokens": 10,
        "cost": 0.0125,
    }
    final = _final(
        usage=usage,
        bucket="openai-compatible-api-fireworks-ai",
        estimated_cost=999.0,
    )

    ext.process_chunk(
        native_chunk=None,
        partial_messages=[],
        final_messages=[final],
        native_messages=[final],
        state=_make_state(tmp_path),
    )

    import sqlite3

    conn = sqlite3.connect(str(_db_path(tmp_path)))
    try:
        row = conn.execute(
            "SELECT estimated_cost, actual_cost, input_tokens, output_tokens "
            "FROM cost_requests"
        ).fetchone()
    finally:
        conn.close()
    assert row[0] is None
    assert row[1] == pytest.approx(0.0125)
    assert row[2] == 50
    assert row[3] == 10


def test_from_native_messages_promotes_cost_metadata() -> None:
    ext = CostTrackingExtension()
    native = [
        {"role": "user"},
        {
            "role": "assistant",
            "_metadata": {
                "cost_session_total": 1.25,
                "cost_session_total_formatted": "$1.250000",
                "cost_session_requests": 3,
                "usage": {"input_tokens": 1},
            },
        },
    ]
    core = [
        {"role": "user", "metadata": {}},
        {
            "role": "assistant",
            "metadata": {
                "native_indices": [1],
                "usage_effective_auth_mode": "api",
            },
        },
    ]

    out = ext.from_native_messages(native, core)

    assert out[0] == core[0]
    assert out[1]["metadata"]["cost_session_total_formatted"] == "$1.250000"
    assert out[1]["metadata"]["cost_session_requests"] == 3
    assert out[1]["metadata"]["usage_effective_auth_mode"] == "api"


def test_from_native_messages_without_native_indices_is_unchanged() -> None:
    ext = CostTrackingExtension()
    native = [
        {
            "role": "assistant",
            "_metadata": {"cost_session_total_formatted": "$2.000000"},
        }
    ]
    core = [{"role": "assistant", "metadata": {}}]

    out = ext.from_native_messages(native, core)

    assert out == core


def test_session_totals_require_workspace_and_session(tmp_path: Path) -> None:
    ext = CostTrackingExtension()
    config = {
        "model": "m",
        "cost_tracking_db_path": str(_db_path(tmp_path)),
        # No working_directory configured.
    }
    state = {"config": config, "_request_context": {"session_id": "s1"}}

    _partials, finals, _new_native, _state = ext.process_chunk(
        native_chunk=None,
        partial_messages=[],
        final_messages=[_final()],
        native_messages=[_final()],
        state=state,
    )

    # The row is recorded, but no session total can be stamped without a
    # workspace.
    assert "cost_session_total" not in finals[0]["_metadata"]
    from cost_tracking_plugins import cost_store

    report = cost_store.bucket_report(_db_path(tmp_path))
    assert report["request_count"] == 1


def test_recording_failure_never_breaks_pipeline(tmp_path: Path) -> None:
    ext = CostTrackingExtension()
    # A directory in place of the database file makes sqlite fail.
    broken_db = tmp_path / "costs.sqlite3"
    broken_db.mkdir()

    _partials, finals, _new_native, _state = ext.process_chunk(
        native_chunk=None,
        partial_messages=[],
        final_messages=[_final()],
        native_messages=[_final()],
        state=_make_state(tmp_path),
    )

    assert "cost_session_total" not in finals[0]["_metadata"]


def test_session_totals_stamp_accumulates_across_requests(tmp_path: Path) -> None:
    ext = CostTrackingExtension()
    state = _make_state(tmp_path)

    for response_id, cost in (("resp_1", 0.25), ("resp_2", 0.75)):
        ext.process_chunk(
            native_chunk=None,
            partial_messages=[],
            final_messages=[_final(response_id=response_id, estimated_cost=cost)],
            native_messages=[_final(response_id=response_id, estimated_cost=cost)],
            state=state,
        )

    totals = cost_store_session_totals(tmp_path)
    assert totals["request_count"] == 2
    assert totals["total_cost"] == pytest.approx(1.0)


def test_list_type_hints_accept_core_shapes() -> None:
    ext = CostTrackingExtension()
    messages: List[Dict[str, Any]] = [{"role": "assistant", "metadata": {}}]
    out = ext.from_native_messages([], messages)
    assert out == messages


def test_recording_appends_summary_csv_row(tmp_path: Path) -> None:
    ext = CostTrackingExtension()
    state = _make_state(tmp_path)

    _partials, finals, _new_native, _state = ext.process_chunk(
        native_chunk=None,
        partial_messages=[],
        final_messages=[_final(usage={"prompt_tokens": 100, "cost": 0.75})],
        native_messages=[_final(usage={"prompt_tokens": 100, "cost": 0.75})],
        state=state,
    )

    assert finals[0]["_metadata"]["cost_session_total_formatted"]
    rows = _summary_csv_rows(tmp_path)
    assert len(rows) == 1
    assert rows[0]["bucket"] == "openai-responses-chatgpt"
    assert rows[0]["session_id"] == "s1"
    assert rows[0]["working_directory"]
    assert float(rows[0]["cost"]) == pytest.approx(0.75)
    assert float(rows[0]["session_total_cost"]) == pytest.approx(0.75)
    assert float(rows[0]["bucket_total_cost"]) == pytest.approx(0.75)


def test_summary_csv_disabled_by_config(tmp_path: Path) -> None:
    ext = CostTrackingExtension()
    state = _make_state(tmp_path, track_cost_tracking_summary_csv=False)

    ext.process_chunk(
        native_chunk=None,
        partial_messages=[],
        final_messages=[_final()],
        native_messages=[_final()],
        state=state,
    )

    assert cost_store_session_totals(tmp_path)["request_count"] == 1
    assert not _summary_csv_path(tmp_path).exists()


def _final_with_breakdown(
    *,
    response_id: str = "resp_bd_1",
    items: Dict[str, Any] | None = None,
    total: float = 0.5,
) -> Dict[str, Any]:
    internal: Dict[str, Any] = {
        "response_id": response_id,
        "usage_bucket": "openai-responses-chatgpt",
        "usage_total_cost": total,
        "usage_cost_breakdown": items
        or {"input": 0.2, "cached": 0.1, "cache_write": 0.05, "output": 0.15},
        "usage": {
            "input_tokens": 100,
            "input_tokens_details": {"cached_tokens": 10},
            "output_tokens": 20,
        },
    }
    return {"role": "assistant", "_metadata": internal}


def test_breakdown_stamps_totals_and_averages_fields(tmp_path: Path) -> None:
    ext = CostTrackingExtension()
    # Stamping is mode-independent: the config choice only selects UI
    # elements, so even "none" stores the complete field set.
    state = _make_state(tmp_path, total_usage_breakdown="none")

    _partials, finals, _native, _state = ext.process_chunk(
        native_chunk=None,
        partial_messages=[],
        final_messages=[_final_with_breakdown()],
        native_messages=[_final_with_breakdown()],
        state=state,
    )

    md = finals[0]["_metadata"]
    # Raw + formatted totals for every item.
    assert md["cost_session_input_cost"] == pytest.approx(0.2)
    assert md["cost_session_input_cost_formatted"] == "$0.200000"
    assert md["cost_session_cached_cost"] == pytest.approx(0.1)
    assert md["cost_session_cached_cost_formatted"] == "$0.100000"
    assert md["cost_session_cache_write_cost"] == pytest.approx(0.05)
    assert md["cost_session_cache_write_cost_formatted"] == "$0.050000"
    assert md["cost_session_output_cost"] == pytest.approx(0.15)
    assert md["cost_session_output_cost_formatted"] == "$0.150000"
    # Raw + formatted averages for every item, plus session-level fields.
    assert md["cost_session_input_cost_avg"] == pytest.approx(0.2)
    assert md["cost_session_input_cost_avg_formatted"] == "$0.200000"
    assert md["cost_session_cached_cost_avg"] == pytest.approx(0.1)
    assert md["cost_session_cached_cost_avg_formatted"] == "$0.100000"
    assert md["cost_session_cache_write_cost_avg"] == pytest.approx(0.05)
    assert md["cost_session_cache_write_cost_avg_formatted"] == "$0.050000"
    assert md["cost_session_output_cost_avg"] == pytest.approx(0.15)
    assert md["cost_session_output_cost_avg_formatted"] == "$0.150000"
    assert md["cost_session_average_cost"] == pytest.approx(0.5)
    assert md["cost_session_average_cost_formatted"] == "$0.500000"
    assert md["cost_session_requests_formatted"] == "1"
    # The combined string from the first implementation is gone.
    assert "cost_session_breakdown_formatted" not in md


def test_breakdown_skips_unavailable_items(tmp_path: Path) -> None:
    ext = CostTrackingExtension()
    state = _make_state(tmp_path)

    _partials, finals, _native, _state = ext.process_chunk(
        native_chunk=None,
        partial_messages=[],
        # No usage_cost_breakdown at all: item fields are skipped, but the
        # session-level fields still exist.
        final_messages=[_final()],
        native_messages=[_final()],
        state=state,
    )

    md = finals[0]["_metadata"]
    assert "cost_session_input_cost" not in md
    assert "cost_session_input_cost_formatted" not in md
    assert "cost_session_input_cost_avg" not in md
    assert md["cost_session_requests_formatted"] == "1"
    assert md["cost_session_average_cost"] == pytest.approx(0.5)
    assert md["cost_session_average_cost_formatted"] == "$0.500000"


def test_breakdown_averages_divide_by_request_count(tmp_path: Path) -> None:
    ext = CostTrackingExtension()
    state = _make_state(tmp_path)

    first = _final_with_breakdown(response_id="resp_bd_a")
    ext.process_chunk(
        native_chunk=None,
        partial_messages=[],
        final_messages=[first],
        native_messages=[first],
        state=state,
    )
    second = _final_with_breakdown(
        response_id="resp_bd_b",
        items={"input": 0.1, "output": 0.05},
        total=0.15,
    )
    _partials, finals, _native, _state = ext.process_chunk(
        native_chunk=None,
        partial_messages=[],
        final_messages=[second],
        native_messages=[second],
        state=state,
    )

    md = finals[0]["_metadata"]
    assert md["cost_session_requests"] == 2
    assert md["cost_session_requests_formatted"] == "2"
    # Session item sums: input 0.2 + 0.1, output 0.15 + 0.05; cached and
    # cache write only have data from the first request.
    assert md["cost_session_input_cost"] == pytest.approx(0.3)
    assert md["cost_session_input_cost_formatted"] == "$0.300000"
    assert md["cost_session_input_cost_avg"] == pytest.approx(0.15)
    assert md["cost_session_input_cost_avg_formatted"] == "$0.150000"
    assert md["cost_session_output_cost"] == pytest.approx(0.2)
    assert md["cost_session_output_cost_avg"] == pytest.approx(0.1)
    assert md["cost_session_cached_cost"] == pytest.approx(0.1)
    assert md["cost_session_cached_cost_avg"] == pytest.approx(0.05)
    # Session total 0.5 + 0.15 across 2 requests.
    assert md["cost_session_average_cost"] == pytest.approx(0.325)
    assert md["cost_session_average_cost_formatted"] == "$0.325000"
