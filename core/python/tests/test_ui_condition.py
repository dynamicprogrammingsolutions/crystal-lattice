"""Tests for UI condition evaluation (agent_app.utils.ui_condition)."""

import pytest

from agent_app.utils.ui_condition import evaluate_condition


def test_evaluate_condition_missing_or_falsy_returns_true():
    """Missing or falsy condition is treated as true (show element)."""
    ctx = {"role": "assistant"}
    assert evaluate_condition(None, ctx) is True
    assert evaluate_condition({}, ctx) is True


def test_evaluate_condition_eq():
    """Leaf eq: value at path must equal given value."""
    ctx = {"role": "assistant", "metadata": {"x": 1}}
    assert evaluate_condition({"path": "role", "eq": "assistant"}, ctx) is True
    assert evaluate_condition({"path": "role", "eq": "user"}, ctx) is False
    assert evaluate_condition({"path": "metadata.x", "eq": 1}, ctx) is True
    assert evaluate_condition({"path": "missing", "eq": "x"}, ctx) is False


def test_evaluate_condition_exists():
    """Leaf exists: path must exist (true) or be missing (false)."""
    ctx = {"role": "assistant", "empty": ""}
    assert evaluate_condition({"path": "role", "exists": True}, ctx) is True
    assert evaluate_condition({"path": "role", "exists": False}, ctx) is False
    assert evaluate_condition({"path": "missing", "exists": True}, ctx) is False
    assert evaluate_condition({"path": "missing", "exists": False}, ctx) is True
    assert evaluate_condition({"path": "empty", "exists": True}, ctx) is True


def test_evaluate_condition_empty():
    """Leaf empty: value at path must be empty (true) or non-empty (false)."""
    ctx = {"a": None, "b": "", "c": [], "d": {}, "e": "x", "f": [1]}
    assert evaluate_condition({"path": "a", "empty": True}, ctx) is True
    assert evaluate_condition({"path": "b", "empty": True}, ctx) is True
    assert evaluate_condition({"path": "c", "empty": True}, ctx) is True
    assert evaluate_condition({"path": "d", "empty": True}, ctx) is True
    assert evaluate_condition({"path": "e", "empty": True}, ctx) is False
    assert evaluate_condition({"path": "f", "empty": True}, ctx) is False
    assert evaluate_condition({"path": "e", "empty": False}, ctx) is True
    assert evaluate_condition({"path": "missing", "empty": True}, ctx) is True


def test_evaluate_condition_all():
    """Composition all: every sub-condition must be true."""
    ctx = {"role": "assistant", "metadata": {"tool_calls": None}}
    cond = {
        "all": [
            {"path": "role", "eq": "assistant"},
            {"path": "metadata.tool_calls", "empty": True},
        ],
    }
    assert evaluate_condition(cond, ctx) is True
    ctx["metadata"]["tool_calls"] = [{"id": "1"}]
    assert evaluate_condition(cond, ctx) is False
    ctx["role"] = "user"
    assert evaluate_condition(cond, ctx) is False


def test_evaluate_condition_any():
    """Composition any: at least one sub-condition must be true."""
    ctx = {"role": "user"}
    cond = {"any": [{"path": "role", "eq": "assistant"}, {"path": "role", "eq": "user"}]}
    assert evaluate_condition(cond, ctx) is True
    ctx["role"] = "assistant"
    assert evaluate_condition(cond, ctx) is True
    ctx["role"] = "tool"
    assert evaluate_condition(cond, ctx) is False


def test_evaluate_condition_not():
    """Composition not: sub-condition must be false."""
    ctx = {"role": "assistant"}
    assert evaluate_condition({"not": {"path": "role", "eq": "user"}}, ctx) is True
    assert evaluate_condition({"not": {"path": "role", "eq": "assistant"}}, ctx) is False
