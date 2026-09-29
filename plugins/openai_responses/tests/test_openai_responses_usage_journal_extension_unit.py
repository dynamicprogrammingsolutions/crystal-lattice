from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from openai_responses_plugins.openai_responses_usage_extension import (
    OpenAIResponsesUsageExtension,
)


def _chatgpt_state(
    tmp_path: Path, *, config_extras: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    config: Dict[str, Any] = {
        "model": "gpt-5-mini",
        "_openai_responses_effective_auth_mode": "chatgpt",
        "chatgpt_credentials_path": str(tmp_path / "auth" / "chatgpt-auth.json"),
    }
    if config_extras:
        config.update(config_extras)
    return {"config": config}


def _api_state(tmp_path: Path) -> Dict[str, Any]:
    return {
        "config": {
            "model": "gpt-5-mini",
            "_openai_responses_effective_auth_mode": "api",
            "chatgpt_credentials_path": str(tmp_path / "auth" / "chatgpt-auth.json"),
        }
    }


def _user_item(text: str = "hello") -> Dict[str, Any]:
    return {
        "type": "message",
        "role": "user",
        "content": [{"type": "input_text", "text": text}],
    }


def _assistant_item(text: str = "ok") -> Dict[str, Any]:
    return {
        "type": "message",
        "role": "assistant",
        "content": [{"type": "output_text", "text": text}],
    }


def _completed_chunk(
    usage: Dict[str, Any], response_id: str = "resp_1"
) -> Dict[str, Any]:
    return {
        "type": "response.completed",
        "response": {"id": response_id, "usage": usage},
    }


def _journal_records(tmp_path: Path) -> List[Dict[str, Any]]:
    journal_path = tmp_path / "auth" / "chatgpt-usage-journal.ndjson"
    if not journal_path.exists():
        return []
    return [
        json.loads(line)
        for line in journal_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_chatgpt_request_appends_request_usage_record(tmp_path: Path) -> None:
    ext = OpenAIResponsesUsageExtension()
    state = _chatgpt_state(tmp_path)
    state["_openai_responses_chatgpt_rate_limit_snapshots"] = {
        "captured_at": "2026-01-01T00:00:00Z",
        "source": "x-codex-headers",
        "plan_type": "plus",
        "snapshots": [
            {
                "limit_id": "codex",
                "primary": {
                    "used_percent": 42.0,
                    "window_minutes": 300,
                    "resets_at": 1704069000,
                },
                "secondary": None,
                "credits": None,
            }
        ],
    }
    usage = {
        "input_tokens": 1000,
        "input_tokens_details": {"cached_tokens": 0},
        "output_tokens": 50,
        "output_tokens_details": {"reasoning_tokens": 5},
    }
    final_messages = [_assistant_item()]

    ext.process_chunk(
        native_chunk=_completed_chunk(usage),
        partial_messages=[],
        final_messages=final_messages,
        native_messages=[_user_item(), *final_messages],
        state=state,
    )

    records = _journal_records(tmp_path)
    assert len(records) == 1
    record = records[0]
    assert record["type"] == "request_usage"
    assert record["response_id"] == "resp_1"
    assert record["model"] == "gpt-5-mini"
    assert record["input_tokens"] == 1000
    assert record["output_tokens"] == 50
    assert record["reasoning_tokens"] == 5
    assert record["estimated_cost"] > 0.0
    # The snapshot stashed in shared state is paired with the request record.
    assert record["rate_limits"]["plan_type"] == "plus"
    assert record["rate_limits"]["snapshots"][0]["primary"]["used_percent"] == 42.0
    # Raw usage is retained for reconstruction.
    assert record["usage"]["input_tokens"] == 1000


def test_api_mode_does_not_journal(tmp_path: Path) -> None:
    ext = OpenAIResponsesUsageExtension()
    usage = {"input_tokens": 100, "output_tokens": 10}
    final_messages = [_assistant_item()]

    ext.process_chunk(
        native_chunk=_completed_chunk(usage),
        partial_messages=[],
        final_messages=final_messages,
        native_messages=[_user_item(), *final_messages],
        state=_api_state(tmp_path),
    )

    assert _journal_records(tmp_path) == []


def test_journal_config_gate_disables_tracking(tmp_path: Path) -> None:
    ext = OpenAIResponsesUsageExtension()
    usage = {"input_tokens": 100, "output_tokens": 10}
    final_messages = [_assistant_item()]

    ext.process_chunk(
        native_chunk=_completed_chunk(usage),
        partial_messages=[],
        final_messages=final_messages,
        native_messages=[_user_item(), *final_messages],
        state=_chatgpt_state(
            tmp_path, config_extras={"track_chatgpt_usage_journal": False}
        ),
    )

    assert _journal_records(tmp_path) == []


def test_journal_falls_back_to_rate_limits_file(tmp_path: Path) -> None:
    rate_limits_path = tmp_path / "auth" / "chatgpt-rate-limits.json"
    rate_limits_path.parent.mkdir(parents=True, exist_ok=True)
    rate_limits_path.write_text(
        json.dumps(
            {
                "captured_at": "2026-01-01T00:00:00Z",
                "source": "x-codex-headers",
                "plan_type": "plus",
                "snapshots": [
                    {
                        "limit_id": "codex",
                        "primary": {
                            "used_percent": 55.0,
                            "window_minutes": 300,
                            "resets_at": 1704069000,
                        },
                        "secondary": None,
                        "credits": None,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    ext = OpenAIResponsesUsageExtension()
    usage = {"input_tokens": 100, "output_tokens": 10}
    final_messages = [_assistant_item()]

    ext.process_chunk(
        native_chunk=_completed_chunk(usage),
        partial_messages=[],
        final_messages=final_messages,
        native_messages=[_user_item(), *final_messages],
        state=_chatgpt_state(
            tmp_path,
            config_extras={"chatgpt_rate_limits_path": str(rate_limits_path)},
        ),
    )

    records = _journal_records(tmp_path)
    assert len(records) == 1
    assert records[0]["rate_limits"]["snapshots"][0]["primary"]["used_percent"] == 55.0


def test_journal_failure_does_not_break_usage_metadata(tmp_path: Path) -> None:
    ext = OpenAIResponsesUsageExtension()
    # A file blocking the journal directory makes appends fail; the extension
    # must still attach usage metadata normally.
    blocker = tmp_path / "auth"
    blocker.write_text("not a directory", encoding="utf-8")
    usage = {"input_tokens": 100, "output_tokens": 10}
    final_messages = [_assistant_item()]

    _partials, finals, _native, _state = ext.process_chunk(
        native_chunk=_completed_chunk(usage),
        partial_messages=[],
        final_messages=final_messages,
        native_messages=[_user_item(), *final_messages],
        state=_chatgpt_state(tmp_path),
    )

    md = finals[0].get("_metadata") or {}
    assert md.get("usage_effective_auth_mode") == "chatgpt"
    assert md.get("usage") == usage


def test_finalize_path_appends_request_usage_record(tmp_path: Path) -> None:
    ext = OpenAIResponsesUsageExtension()
    usage = {"input_tokens": 100, "output_tokens": 10}
    native_messages: List[Dict[str, Any]] = [
        _user_item(),
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "ok"}],
            "_metadata": {
                "response_id": "resp_9",
                "_openai_responses_usage_raw": usage,
            },
        },
    ]

    ext.finalize(
        final_messages=[],
        native_messages=native_messages,
        state=_chatgpt_state(tmp_path),
    )

    records = _journal_records(tmp_path)
    assert len(records) == 1
    assert records[0]["type"] == "request_usage"
    assert records[0]["response_id"] == "resp_9"
    assert records[0]["input_tokens"] == 100


def test_usage_config_schema_exposes_journal_controls() -> None:
    schema = OpenAIResponsesUsageExtension().get_config_schema()
    assert schema["track_chatgpt_usage_journal"]["default"] is True
    assert "chatgpt_usage_journal_path" in schema
    assert schema["track_chatgpt_usage_summary_csv"]["default"] is True
    assert "chatgpt_usage_summary_csv_path" in schema


def _summary_csv_path(tmp_path: Path) -> Path:
    return tmp_path / "auth" / "chatgpt-usage-summary.csv"


def _summary_rows(tmp_path: Path) -> List[Dict[str, Any]]:
    path = _summary_csv_path(tmp_path)
    if not path.exists():
        return []
    import csv

    with open(path, encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_journal_record_carries_session_fields(tmp_path: Path) -> None:
    ext = OpenAIResponsesUsageExtension()
    state = _chatgpt_state(
        tmp_path, config_extras={"working_directory": "workspace/repo"}
    )
    state["_request_context"] = {"session_id": "session-journal"}
    usage = {"input_tokens": 100, "output_tokens": 10}
    final_messages = [_assistant_item()]

    ext.process_chunk(
        native_chunk=_completed_chunk(usage),
        partial_messages=[],
        final_messages=final_messages,
        native_messages=[_user_item(), *final_messages],
        state=state,
    )

    records = _journal_records(tmp_path)
    assert len(records) == 1
    assert records[0]["session_id"] == "session-journal"
    # Relative working directories are resolved to absolute paths.
    import os

    assert records[0]["working_directory"] == os.path.abspath("workspace/repo")


def test_summary_csv_written_alongside_journal(tmp_path: Path) -> None:
    ext = OpenAIResponsesUsageExtension()
    state = _chatgpt_state(tmp_path)
    state["_request_context"] = {"session_id": "session-csv"}
    state["_openai_responses_chatgpt_rate_limit_snapshots"] = {
        "captured_at": "2026-01-01T00:00:00Z",
        "source": "x-codex-headers",
        "snapshots": [
            {
                "limit_id": "codex",
                "primary": {"used_percent": 61.0},
                "secondary": None,
                "credits": None,
            }
        ],
    }
    usage = {"input_tokens": 100, "output_tokens": 10}
    final_messages = [_assistant_item()]

    ext.process_chunk(
        native_chunk=_completed_chunk(usage),
        partial_messages=[],
        final_messages=final_messages,
        native_messages=[_user_item(), *final_messages],
        state=state,
    )

    rows = _summary_rows(tmp_path)
    assert len(rows) == 1
    assert rows[0]["session_id"] == "session-csv"
    assert float(rows[0]["estimated_cost"]) > 0.0
    assert float(rows[0]["total_cost"]) == float(rows[0]["estimated_cost"])
    assert float(rows[0]["used_percent"]) == 61.0


def test_summary_csv_disabled_by_config(tmp_path: Path) -> None:
    ext = OpenAIResponsesUsageExtension()
    state = _chatgpt_state(
        tmp_path, config_extras={"track_chatgpt_usage_summary_csv": False}
    )
    usage = {"input_tokens": 100, "output_tokens": 10}
    final_messages = [_assistant_item()]

    ext.process_chunk(
        native_chunk=_completed_chunk(usage),
        partial_messages=[],
        final_messages=final_messages,
        native_messages=[_user_item(), *final_messages],
        state=state,
    )

    assert _journal_records(tmp_path), "journal must still be written"
    assert _summary_rows(tmp_path) == []


def test_refinalized_response_is_journaled_once(tmp_path: Path) -> None:
    ext = OpenAIResponsesUsageExtension()
    usage = {"input_tokens": 100, "output_tokens": 10}

    # First pass: streaming journaling for resp_dup.
    final_messages = [_assistant_item()]
    ext.process_chunk(
        native_chunk=_completed_chunk(usage, response_id="resp_dup"),
        partial_messages=[],
        final_messages=final_messages,
        native_messages=[_user_item(), *final_messages],
        state=_chatgpt_state(tmp_path),
    )

    # Re-finalize path: the same response presented again (e.g. a session
    # rebuild) must not append a duplicate record.
    native_messages: List[Dict[str, Any]] = [
        _user_item(),
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "ok"}],
            "_metadata": {
                "response_id": "resp_dup",
                "_openai_responses_usage_raw": usage,
            },
        },
    ]
    ext.finalize(
        final_messages=[],
        native_messages=native_messages,
        state=_chatgpt_state(tmp_path),
    )

    records = _journal_records(tmp_path)
    assert len(records) == 1
    assert records[0]["response_id"] == "resp_dup"

    # A different response id is still journaled.
    ext.process_chunk(
        native_chunk=_completed_chunk(usage, response_id="resp_other"),
        partial_messages=[],
        final_messages=[_assistant_item()],
        native_messages=[_user_item(), _assistant_item()],
        state=_chatgpt_state(tmp_path),
    )
    assert len(_journal_records(tmp_path)) == 2
