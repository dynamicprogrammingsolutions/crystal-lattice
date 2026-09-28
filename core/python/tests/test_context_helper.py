from __future__ import annotations

import re
from typing import Any

import pytest

from agent_core.core_context import CoreContext
from agent_core.plugin.context_helper import merge_context_layers


def _strip_ansi(value: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", value)


def test_equal_external_value_is_quiet_and_owned_value_wins(
    capsys: pytest.CaptureFixture[str],
) -> None:
    owned_config = {"model": "test-model"}

    result = merge_context_layers(
        builder="test",
        call_path="equal",
        generic_layer={},
        specific_layer={"config": owned_config},
        extra={"config": {"model": "test-model"}, "custom": "kept"},
    )

    assert result["config"] is owned_config
    assert result["custom"] == "kept"
    assert "context_reserved_key_clash_external" not in capsys.readouterr().out


def test_different_external_value_warns_and_owned_value_wins(
    capsys: pytest.CaptureFixture[str],
) -> None:
    owned_config = {"model": "owned-model"}

    result = merge_context_layers(
        builder="test",
        call_path="different",
        generic_layer={},
        specific_layer={"config": owned_config},
        extra={"config": {"model": "caller-model"}},
    )

    assert result["config"] is owned_config
    captured = _strip_ansi(capsys.readouterr().out)
    assert "context_reserved_key_clash_external" in captured
    assert "builder=test" in captured
    assert "call_path=different" in captured
    assert "key=config" in captured
    assert "winning_layer=specific" in captured


def test_unusual_equality_cannot_interrupt_context_merge(
    capsys: pytest.CaptureFixture[str],
) -> None:
    class _RaisesOnEquality:
        def __eq__(self, other: Any) -> bool:
            raise RuntimeError("comparison is unavailable")

    owned = _RaisesOnEquality()

    result = merge_context_layers(
        builder="test",
        call_path="unusual_equality",
        generic_layer={},
        specific_layer={"value": owned},
        extra={"value": _RaisesOnEquality()},
    )

    assert result["value"] is owned
    assert "context_reserved_key_clash_external" in capsys.readouterr().out


def test_specific_layer_still_overrides_generic_layer(
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = merge_context_layers(
        builder="test",
        call_path="internal_precedence",
        generic_layer={"value": "generic"},
        specific_layer={"value": "specific"},
        extra=None,
    )

    assert result["value"] == "specific"
    assert "context_reserved_key_clash_internal" in capsys.readouterr().out


def test_rebuild_accepts_request_id_without_same_config_warning(
    capsys: pytest.CaptureFixture[str],
) -> None:
    core_context = CoreContext(core=object())
    config = {"model": "test-model"}

    result = core_context.build_rebuild_context(
        config=config,
        plugin_context={
            "core": object(),
            "config": config,
            "request_id": None,
            "plugin_value": "kept",
        },
        extra={
            "config": {"model": "test-model"},
            "request_id": "request-123",
            "custom": "kept",
        },
    )

    assert result["config"] == config
    assert result["request_id"] == "request-123"
    assert result["plugin_value"] == "kept"
    assert result["custom"] == "kept"
    assert "context_reserved_key_clash_external" not in capsys.readouterr().out

    context_without_request = core_context.build_rebuild_context(
        config=config,
        plugin_context={"request_id": None},
    )
    assert context_without_request["request_id"] is None
