from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from agent_core.utils import get_logger


def _context_logger():
    return get_logger("context_helper")


def _context_values_equal(owned: Any, candidate: Any) -> bool:
    """Return whether two context values match without risking merge failure."""

    if owned is candidate:
        return True
    try:
        return bool(owned == candidate)
    except Exception:
        return False


def merge_context_layers(
    *,
    builder: str,
    call_path: str,
    generic_layer: Mapping[str, Any],
    specific_layer: Mapping[str, Any],
    extra: Optional[Mapping[str, Any]],
) -> Dict[str, Any]:
    """Merge generic, specific, and caller-provided context with warnings.

    Precedence rules:
    - specific-layer keys override generic-layer keys
    - caller-provided extra keys are additive only
    - equal caller repetitions of owned keys are ignored without a warning
    - differing caller clashes with owned keys are ignored with a warning
    """

    result: Dict[str, Any] = {}
    reserved_keys: Dict[str, str] = {}

    for key, value in generic_layer.items():
        if not isinstance(key, str):
            continue
        result[key] = value
        reserved_keys[key] = "generic"

    for key, value in specific_layer.items():
        if not isinstance(key, str):
            continue
        if key in reserved_keys:
            _context_logger().warning(
                "context_reserved_key_clash_internal",
                builder=builder,
                call_path=call_path,
                key=key,
                winning_layer="specific",
                replaced_layer=reserved_keys[key],
            )
        result[key] = value
        reserved_keys[key] = "specific"

    if isinstance(extra, Mapping):
        for key, value in extra.items():
            if not isinstance(key, str):
                continue
            if key in reserved_keys:
                if _context_values_equal(result[key], value):
                    continue
                _context_logger().warning(
                    "context_reserved_key_clash_external",
                    builder=builder,
                    call_path=call_path,
                    key=key,
                    winning_layer=reserved_keys[key],
                )
                continue
            result[key] = value

    return result
