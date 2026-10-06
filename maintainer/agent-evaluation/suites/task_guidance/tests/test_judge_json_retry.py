"""Judge-JSON retry behavior for file-quality assessments."""

from __future__ import annotations

import json

from suites.task_guidance.evaluation.execution import (
    JUDGE_JSON_RETRIES,
    _parse_judge_response,
)


class _Value:
    def __init__(self, response: str) -> None:
        self.response = response
        self.completed = True
        self.errors = ()


class _Run:
    def __init__(self, response: str) -> None:
        self.value = _Value(response)
        self.error = None


def test_malformed_json_retries_up_to_the_limit_and_succeeds() -> None:
    reruns = []

    def rerun():
        reruns.append(True)
        return [_Run('{"grades": {}}')]

    parsed, run = _parse_judge_response(
        _Run("{oops"), lambda text: json.loads(text), rerun
    )
    assert parsed == {"grades": {}}
    assert run.value.response == '{"grades": {}}'
    assert len(reruns) == 1


def test_malformed_json_fails_after_exhausting_retries() -> None:
    reruns = []

    def rerun():
        reruns.append(True)
        return [_Run("still not json")]

    import pytest

    with pytest.raises(json.JSONDecodeError):
        _parse_judge_response(_Run("{oops"), lambda text: json.loads(text), rerun)
    assert len(reruns) == JUDGE_JSON_RETRIES


def test_valid_json_does_not_retry() -> None:
    def rerun():  # pragma: no cover - must not run
        raise AssertionError("rerun must not be called")

    parsed, run = _parse_judge_response(
        _Run('{"ok": true}'), lambda text: json.loads(text), rerun
    )
    assert parsed == {"ok": True}
    assert isinstance(run, _Run)
