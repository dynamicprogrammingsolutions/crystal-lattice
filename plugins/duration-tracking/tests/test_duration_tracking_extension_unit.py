"""Unit tests for the duration tracking feature plugin.

The tests feed realistic ``DurationExtension``-style stamps (fixture
messages, no clock) and assert the plugin records from them, stamps the
store-backed session totals, and projects them to public metadata.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from duration_tracking_plugins import duration_store
from duration_tracking_plugins.duration_tracking_extension import (
    DurationTrackingExtension,
)


def _assistant_final(duration_ms: int = 1200, **md_overrides: Any) -> Dict[str, Any]:
    md: Dict[str, Any] = {
        "duration_started_at": "2026-01-01T00:00:00+00:00",
        "duration_finished_at": "2026-01-01T00:00:01.200000+00:00",
        "duration_ms": duration_ms,
        "duration_formatted": "1.2s",
        "turn_duration_ms": duration_ms,
        "turn_duration_formatted": "1.2s",
    }
    md.update(md_overrides)
    return {"role": "assistant", "content": "hello", "_metadata": md}


def _native_history(finals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build a native history whose tail mirrors the finals."""

    prior: List[Dict[str, Any]] = [
        {"role": "user", "content": "hi"},
    ]
    return prior + [dict(item) for item in finals]


def _state(
    db_path: Path,
    *,
    session_id: str = "s1",
    request_id: str = "req-1",
    working_directory: str = "/tmp/ws",
    config_overrides: Optional[Dict[str, Any]] = None,
    with_request_context: bool = True,
) -> Dict[str, Any]:
    config: Dict[str, Any] = {
        "working_directory": working_directory,
        "model": "test-model",
        "duration_tracking_db_path": str(db_path),
    }
    if config_overrides:
        config.update(config_overrides)
    state: Dict[str, Any] = {"config": config}
    if with_request_context:
        state["_request_context"] = {
            "session_id": session_id,
            "request_id": request_id,
        }
    return state


def _finalize(
    feature: DurationTrackingExtension,
    finals: List[Dict[str, Any]],
    native: List[Dict[str, Any]],
    state: Dict[str, Any],
):
    return feature.finalize(finals, native, state)


def _request_rows(db_path: Path) -> List[Dict[str, Any]]:
    # The store creates its schema lazily on first use; touch it through
    # the public path so "nothing recorded" cases can query the table.
    duration_store.session_totals(db_path, working_directory="/tmp/ws", session_id="s1")
    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute("SELECT * FROM duration_requests")]
    finally:
        conn.close()


def _internal(message: Dict[str, Any]) -> Dict[str, Any]:
    internal = message.get("_metadata")
    assert isinstance(internal, dict)
    return internal


def test_finalize_records_row_and_stamps_totals(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    feature = DurationTrackingExtension()
    finals = [_assistant_final()]
    native = _native_history(finals)

    new_finals, new_native, _ = _finalize(feature, finals, native, _state(db_path))

    # The store row landed with the stamp values.
    rows = _request_rows(db_path)
    assert len(rows) == 1
    assert rows[0]["session_id"] == "s1"
    assert rows[0]["working_directory"] == "/tmp/ws"
    assert rows[0]["model"] == "test-model"
    assert rows[0]["request_id"] == "req-1"
    assert rows[0]["duration_ms"] == 1200
    assert rows[0]["duration_started_at"] == "2026-01-01T00:00:00+00:00"
    assert rows[0]["duration_finished_at"] == "2026-01-01T00:00:01.200000+00:00"
    # Row time is the actual request end from the finished stamp.
    assert rows[0]["time"] == "2026-01-01T00:00:01.200000+00:00"

    # Totals are stamped raw + formatted on the finals...
    internal = _internal(new_finals[0])
    assert internal["duration_session_total"] == 1200
    assert internal["duration_session_total_formatted"] == "1.2s"
    assert internal["duration_session_requests"] == 1
    assert internal["duration_session_requests_formatted"] == "1"
    assert internal["duration_session_average"] == pytest.approx(1200.0)
    assert internal["duration_session_average_formatted"] == "1.2s"
    # The original stamps stay intact.
    assert internal["duration_ms"] == 1200

    # ...and on the matching native tail entry, not the earlier history.
    tail_internal = _internal(new_native[-1])
    assert tail_internal["duration_session_total"] == 1200
    assert "duration_session_total" not in (new_native[0].get("_metadata") or {})

    totals = duration_store.session_totals(
        db_path, working_directory="/tmp/ws", session_id="s1"
    )
    assert totals == {"request_count": 1, "total_ms": 1200}


def test_finalize_accumulates_totals_across_requests(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    feature = DurationTrackingExtension()

    finals_one = [_assistant_final(1200)]
    _finalize(feature, finals_one, _native_history(finals_one), _state(db_path))

    finals_two = [_assistant_final(300)]
    new_finals, _, _ = _finalize(
        feature,
        finals_two,
        _native_history(finals_two),
        _state(db_path, request_id="req-2"),
    )

    internal = _internal(new_finals[0])
    assert internal["duration_session_total"] == 1500
    assert internal["duration_session_total_formatted"] == "1.5s"
    assert internal["duration_session_requests"] == 2
    assert internal["duration_session_requests_formatted"] == "2"
    assert internal["duration_session_average"] == pytest.approx(750.0)
    assert internal["duration_session_average_formatted"] == "750ms"


def test_finalize_guard_skips_already_processed_finals(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    feature = DurationTrackingExtension()
    finals = [_assistant_final()]
    state = _state(db_path)

    stamped_finals, _, _ = _finalize(feature, finals, _native_history(finals), state)
    again_finals, _, _ = _finalize(
        feature, stamped_finals, _native_history(stamped_finals), state
    )

    # No duplicate row and no double stamping.
    assert len(_request_rows(db_path)) == 1
    assert _internal(again_finals[0]) == _internal(stamped_finals[0])


def test_finalize_dedupes_by_request_id_via_unique_index(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    feature = DurationTrackingExtension()
    state = _state(db_path)

    # Fresh unstamped finals bypass the already-processed guard; only the
    # unique request id stops the duplicate row.
    finals_one = [_assistant_final(1200)]
    _finalize(feature, finals_one, _native_history(finals_one), state)
    finals_two = [_assistant_final(999)]
    new_finals, _, _ = _finalize(
        feature, finals_two, _native_history(finals_two), state
    )

    rows = _request_rows(db_path)
    assert len(rows) == 1
    assert rows[0]["duration_ms"] == 1200
    # Totals still stamp from the store (factual history).
    assert _internal(new_finals[0])["duration_session_total"] == 1200


def test_finalize_appends_summary_csv_row(tmp_path: Path) -> None:
    import csv

    db_path = tmp_path / "durations.sqlite3"
    feature = DurationTrackingExtension()
    finals = [_assistant_final(1200)]
    _finalize(feature, finals, _native_history(finals), _state(db_path))
    finals_two = [_assistant_final(300)]
    _finalize(
        feature,
        finals_two,
        _native_history(finals_two),
        _state(db_path, request_id="req-2"),
    )

    csv_path = db_path.with_name("duration-tracking-summary.csv")
    with open(csv_path, encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    assert float(rows[0]["duration"]) == pytest.approx(1200)
    assert float(rows[0]["session_total_duration"]) == pytest.approx(1200)
    assert float(rows[1]["duration"]) == pytest.approx(300)
    assert float(rows[1]["session_total_duration"]) == pytest.approx(1500)


def test_finalize_summary_csv_disabled_by_config(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    feature = DurationTrackingExtension()
    finals = [_assistant_final()]

    _finalize(
        feature,
        finals,
        _native_history(finals),
        _state(
            db_path,
            config_overrides={"track_duration_tracking_summary_csv": False},
        ),
    )

    assert not db_path.with_name("duration-tracking-summary.csv").exists()
    # The row still recorded; only the CSV is gated.
    assert len(_request_rows(db_path)) == 1


def test_finalize_without_stamps_records_nothing(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    feature = DurationTrackingExtension()
    finals = [{"role": "assistant", "content": "hello", "_metadata": {"usage": {}}}]

    new_finals, new_native, _ = _finalize(
        feature, finals, _native_history(finals), _state(db_path)
    )

    assert _request_rows(db_path) == []
    assert "duration_session_total" not in _internal(new_finals[0])
    assert "duration_session_total" not in _internal(new_native[-1])


def test_finalize_with_track_durations_disabled_records_nothing(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "durations.sqlite3"
    feature = DurationTrackingExtension()
    finals = [_assistant_final()]

    new_finals, _, _ = _finalize(
        feature,
        finals,
        _native_history(finals),
        _state(db_path, config_overrides={"track_durations": False}),
    )

    assert _request_rows(db_path) == []
    assert "duration_session_total" not in _internal(new_finals[0])


def test_finalize_with_malformed_stamps_records_nothing(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    feature = DurationTrackingExtension()

    cases = [
        {"duration_ms": "not-a-number"},
        {"duration_ms": -5},
        {"duration_started_at": None},
        {"duration_finished_at": ""},
    ]
    for index, overrides in enumerate(cases):
        finals = [_assistant_final(**overrides)]
        new_finals, _, _ = _finalize(
            feature,
            finals,
            _native_history(finals),
            _state(db_path, request_id=f"req-{index}"),
        )
        assert _request_rows(db_path) == []
        assert "duration_session_total" not in _internal(new_finals[0])


def test_finalize_without_finals_unchanged(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    feature = DurationTrackingExtension()
    native = [{"role": "user", "content": "hi"}]

    new_finals, new_native, new_state = _finalize(feature, [], native, _state(db_path))

    assert new_finals == []
    assert new_native == native
    assert _request_rows(db_path) == []


def test_finalize_store_failure_is_swallowed(tmp_path: Path) -> None:
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")
    db_path = blocker / "durations.sqlite3"
    feature = DurationTrackingExtension()
    finals = [_assistant_final()]

    # The store path is unwritable; finalize must not raise and must not
    # stamp totals it could not verify.
    new_finals, _, _ = _finalize(
        feature, finals, _native_history(finals), _state(db_path)
    )

    assert "duration_session_total" not in _internal(new_finals[0])


def test_finalize_without_session_context_records_row_but_skips_totals(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "durations.sqlite3"
    feature = DurationTrackingExtension()
    finals = [_assistant_final()]

    new_finals, _, _ = _finalize(
        feature,
        finals,
        _native_history(finals),
        _state(db_path, with_request_context=False),
    )

    rows = _request_rows(db_path)
    assert len(rows) == 1
    assert rows[0]["session_id"] is None
    assert rows[0]["request_id"] is None
    assert "duration_session_total" not in _internal(new_finals[0])


def _tool_message(duration_ms: int = 250, **md_overrides: Any) -> Dict[str, Any]:
    md: Dict[str, Any] = {
        "tool_call_id": "call_1",
        "tool_name": "read_file",
        "duration_ms": duration_ms,
        "duration_formatted": "250ms",
        "duration_started_at": "2026-01-01T00:00:00+00:00",
        "duration_finished_at": "2026-01-01T00:00:00.250000+00:00",
    }
    md.update(md_overrides)
    return {"role": "tool", "content": "file contents", "metadata": md}


def _tool_context(
    db_path: Path,
    *,
    session_id: str = "s1",
    request_id: str = "req-1",
    tool_call_id: Optional[str] = "call_1",
    tool_error: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    context: Dict[str, Any] = {
        "session_id": session_id,
        "request_id": request_id,
        "tool_call_id": tool_call_id,
        "tool_name": "read_file",
        "tool_plugin": "file_reader_tool",
        "config": (
            config
            if config is not None
            else {
                "working_directory": "/tmp/ws",
                "model": "test-model",
                "duration_tracking_db_path": str(db_path),
            }
        ),
    }
    if tool_error is not None:
        context["tool_error"] = tool_error
    return context


def _tool_rows(db_path: Path) -> List[Dict[str, Any]]:
    duration_store.tool_session_totals(
        db_path, working_directory="/tmp/ws", session_id="s1"
    )
    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute("SELECT * FROM tool_durations")]
    finally:
        conn.close()


def test_finalize_tool_call_records_row_from_stamps(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    feature = DurationTrackingExtension()
    message = _tool_message()
    state: Dict[str, Any] = {}

    out_message, out_state = feature.finalize_tool_call(
        message, state, context=_tool_context(db_path)
    )

    rows = _tool_rows(db_path)
    assert len(rows) == 1
    assert rows[0]["session_id"] == "s1"
    assert rows[0]["working_directory"] == "/tmp/ws"
    assert rows[0]["model"] == "test-model"
    assert rows[0]["request_id"] == "req-1"
    assert rows[0]["tool_call_id"] == "call_1"
    assert rows[0]["tool_name"] == "read_file"
    assert rows[0]["tool_plugin"] == "file_reader_tool"
    assert rows[0]["duration_ms"] == 250
    assert rows[0]["duration_started_at"] == "2026-01-01T00:00:00+00:00"
    assert rows[0]["duration_finished_at"] == "2026-01-01T00:00:00.250000+00:00"
    assert rows[0]["tool_error"] is None
    assert rows[0]["time"] == "2026-01-01T00:00:00.250000+00:00"

    # The hook records only; the message and state pass through unchanged.
    assert out_message == message
    assert out_state == state


def test_finalize_tool_call_unstamped_message_records_nothing(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    feature = DurationTrackingExtension()
    message = {
        "role": "tool",
        "content": "result",
        "metadata": {"tool_call_id": "call_1", "tool_name": "read_file"},
    }

    out_message, _ = feature.finalize_tool_call(
        message, {}, context=_tool_context(db_path)
    )

    assert _tool_rows(db_path) == []
    assert out_message == message


def test_finalize_tool_call_with_tracking_disabled_records_nothing(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "durations.sqlite3"
    feature = DurationTrackingExtension()

    out_message, _ = feature.finalize_tool_call(
        _tool_message(),
        {},
        context=_tool_context(
            db_path,
            config={
                "working_directory": "/tmp/ws",
                "duration_tracking_db_path": str(db_path),
                "track_durations": False,
            },
        ),
    )

    assert _tool_rows(db_path) == []
    assert out_message == _tool_message()


def test_finalize_tool_call_records_error_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    feature = DurationTrackingExtension()

    feature.finalize_tool_call(
        _tool_message(),
        {},
        context=_tool_context(db_path, tool_error="inspect_call_failed"),
    )

    rows = _tool_rows(db_path)
    assert len(rows) == 1
    assert rows[0]["tool_error"] == "inspect_call_failed"


def test_finalize_tool_call_without_call_id_records_without_dedup(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "durations.sqlite3"
    feature = DurationTrackingExtension()

    # Failed inspection yields no call id; each occurrence is a distinct
    # event and the composite key cannot dedup NULL components.
    feature.finalize_tool_call(
        _tool_message(),
        {},
        context=_tool_context(db_path, tool_call_id=None),
    )
    feature.finalize_tool_call(
        _tool_message(),
        {},
        context=_tool_context(db_path, tool_call_id=None),
    )

    assert len(_tool_rows(db_path)) == 2


def test_finalize_tool_call_dedupes_on_composite_key(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    feature = DurationTrackingExtension()
    context = _tool_context(db_path)

    feature.finalize_tool_call(_tool_message(), {}, context=context)
    feature.finalize_tool_call(_tool_message(duration_ms=999), {}, context=context)

    rows = _tool_rows(db_path)
    assert len(rows) == 1
    assert rows[0]["duration_ms"] == 250


def test_finalize_tool_call_store_failure_is_swallowed(tmp_path: Path) -> None:
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")
    db_path = blocker / "durations.sqlite3"
    feature = DurationTrackingExtension()
    message = _tool_message()

    out_message, out_state = feature.finalize_tool_call(
        message, {"marker": True}, context=_tool_context(db_path)
    )

    assert out_message == message
    assert out_state == {"marker": True}


def test_finalize_tool_call_falls_back_to_state_config(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    feature = DurationTrackingExtension()
    # No layer-1 config in the context; the provider state carries it.
    state: Dict[str, Any] = {
        "config": {
            "working_directory": "/tmp/ws",
            "model": "test-model",
            "duration_tracking_db_path": str(db_path),
        }
    }
    context = _tool_context(db_path)
    context["config"] = None

    feature.finalize_tool_call(_tool_message(), state, context=context)

    rows = _tool_rows(db_path)
    assert len(rows) == 1
    assert rows[0]["working_directory"] == "/tmp/ws"


def test_finalize_stamps_tool_totals_alongside_llm_totals(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    feature = DurationTrackingExtension()

    # A tool call recorded earlier in the session (its own request).
    feature.finalize_tool_call(
        _tool_message(duration_ms=250),
        {},
        context=_tool_context(db_path, request_id="req-0", tool_call_id="call_0"),
    )

    finals = [_assistant_final(1200)]
    new_finals, new_native, _ = _finalize(
        feature, finals, _native_history(finals), _state(db_path)
    )

    internal = _internal(new_finals[0])
    assert internal["duration_session_total"] == 1200
    assert internal["duration_session_requests"] == 1
    # Tool totals stamp alongside the LLM totals, raw + formatted.
    assert internal["tool_duration_session_total"] == 250
    assert internal["tool_duration_session_total_formatted"] == "250ms"
    assert internal["tool_duration_session_calls"] == 1
    assert internal["tool_duration_session_calls_formatted"] == "1"
    assert internal["tool_duration_session_average"] == pytest.approx(250.0)
    assert internal["tool_duration_session_average_formatted"] == "250ms"

    # The native tail carries the same dual totals.
    tail_internal = _internal(new_native[-1])
    assert tail_internal["tool_duration_session_total"] == 250
    assert tail_internal["duration_session_total"] == 1200


def test_finalize_stamps_zero_tool_totals_for_tool_less_sessions(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "durations.sqlite3"
    feature = DurationTrackingExtension()
    finals = [_assistant_final(1200)]

    new_finals, _, _ = _finalize(
        feature, finals, _native_history(finals), _state(db_path)
    )

    internal = _internal(new_finals[0])
    # Tool totals are always stamped (zeros included), mirroring the LLM
    # totals; the average and formatted count only appear with calls.
    assert internal["tool_duration_session_total"] == 0
    assert internal["tool_duration_session_total_formatted"] == "0ms"
    assert internal["tool_duration_session_calls"] == 0
    assert "tool_duration_session_calls_formatted" not in internal
    assert "tool_duration_session_average" not in internal


def test_from_native_messages_projects_session_totals(tmp_path: Path) -> None:
    native = [
        {"role": "user", "content": "hi"},
        {
            "role": "assistant",
            "content": "hello",
            "_metadata": {
                "duration_ms": 1200,
                "duration_session_total": 1200,
                "duration_session_total_formatted": "1.2s",
                "duration_session_requests": 1,
                "duration_session_requests_formatted": "1",
            },
        },
    ]
    messages = [
        {"role": "user", "content": "hi"},
        {
            "role": "assistant",
            "content": "hello",
            "metadata": {"native_indices": [1]},
        },
    ]

    projected = DurationTrackingExtension().from_native_messages(native, messages)

    metadata = projected[1]["metadata"]
    assert metadata["duration_session_total"] == 1200
    assert metadata["duration_session_total_formatted"] == "1.2s"
    assert metadata["duration_session_requests"] == 1
    assert metadata["duration_session_requests_formatted"] == "1"
    # Existing keys are preserved; only missing session keys are added.
    assert metadata["native_indices"] == [1]


def test_from_native_messages_promotes_only_session_keys(tmp_path: Path) -> None:
    native = [
        {
            "role": "assistant",
            "content": "hello",
            "_metadata": {
                "duration_ms": 1200,
                "duration_formatted": "1.2s",
                "duration_started_at": "2026-01-01T00:00:00+00:00",
                "duration_finished_at": "2026-01-01T00:00:01.200000+00:00",
                "turn_duration_ms": 1200,
                "duration_session_total": 1200,
                "tool_duration_session_total": 250,
                "tool_duration_session_calls": 1,
            },
        },
    ]
    messages = [
        {
            "role": "assistant",
            "content": "hello",
            "metadata": {"native_indices": [0]},
        }
    ]

    projected = DurationTrackingExtension().from_native_messages(native, messages)

    metadata = projected[0]["metadata"]
    assert metadata["duration_session_total"] == 1200
    assert metadata["tool_duration_session_total"] == 250
    assert metadata["tool_duration_session_calls"] == 1
    # Per-message duration stamps are owned by the duration feature; the
    # tracker promotes only its session-total keys.
    assert "duration_ms" not in metadata
    assert "turn_duration_ms" not in metadata
    assert "duration_started_at" not in metadata


def test_from_native_messages_passes_through_other_messages(
    tmp_path: Path,
) -> None:
    native = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello", "_metadata": {}},
    ]
    messages = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello", "metadata": {}},
        {"role": "assistant", "content": "no indices", "metadata": None},
    ]

    projected = DurationTrackingExtension().from_native_messages(native, messages)

    assert projected[0] == messages[0]
    assert projected[1] == messages[1]
    assert projected[2] == messages[2]
