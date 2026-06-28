"""OpenRouter model-specific capability helpers."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


# Full enum of all possible reasoning_effort values, in display order.
# Used when no model-specific override matches.
REASONING_EFFORT_ALL_VALUES: List[str] = [
    "none",
    "minimal",
    "low",
    "medium",
    "high",
    "xhigh",
    "max",
]

# Regex-based model overrides for the reasoning_effort UI dropdown.
#
# Each entry is (pattern, values, default):
# - pattern: regex matched against the full model_id (lowercased).
# - values: empty list = disable the reasoning_effort UI for this model;
#           non-empty = restrict the UI dropdown to these values.
# - default: informational only — shown in the UI as the model's default effort.
#   NOT injected into the request; the model uses its own default when
#   ``reasoning_effort`` is not explicitly set in config.
#
# First match wins, so order most-specific patterns first.
# If no pattern matches, all REASONING_EFFORT_ALL_VALUES are shown in the UI.
REASONING_EFFORT_MODEL_OVERRIDES: List[
    Tuple[re.Pattern[str], List[str], Optional[str]]
] = [
    # GPT-5.2-pro: medium/high/xhigh
    (re.compile(r"gpt-5\.2-pro"), ["medium", "high", "xhigh"], "medium"),
    # GPT-5-pro: only high
    (re.compile(r"gpt-5-pro"), ["high"], "high"),
    # GPT-5.2: none/low/medium/high/xhigh
    (re.compile(r"gpt-5\.2"), ["none", "low", "medium", "high", "xhigh"], "none"),
    # GPT-5.1: none/low/medium/high
    (re.compile(r"gpt-5\.1"), ["none", "low", "medium", "high"], "none"),
    # GPT-5 (base): minimal/low/medium/high
    (re.compile(r"gpt-5"), ["minimal", "low", "medium", "high"], "medium"),
    # o1/o3: low/medium/high
    (re.compile(r"\bo1\b"), ["low", "medium", "high"], "medium"),
    (re.compile(r"\bo3\b"), ["low", "medium", "high"], "medium"),
    # grok-3-mini: low/high only
    (re.compile(r"grok-3-mini"), ["low", "high"], "low"),
]


def resolve_reasoning_effort_override(
    model_id: Optional[str],
) -> Optional[Tuple[List[str], Optional[str]]]:
    """Return the first matching (values, default) override for model_id, or None."""
    if not isinstance(model_id, str) or not model_id.strip():
        return None
    normalized = model_id.strip().lower()
    for pattern, values, default in REASONING_EFFORT_MODEL_OVERRIDES:
        if pattern.search(normalized):
            return (values, default)
    return None


def get_reasoning_effort_options_and_default(
    model_id: Optional[str],
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Return UI options and default reasoning effort for a model.

    Behavior:
    - No model_id → no UI (empty options, no default).
    - No override matches → all REASONING_EFFORT_ALL_VALUES shown, no default.
    - Override matches with empty values → UI disabled (empty options, no default).
    - Override matches with non-empty values → those values shown, override default used.

    The ``default`` is informational only — it is shown in the UI element's
    ``default`` field so users know what the model applies when ``reasoning_effort``
    is not explicitly set. It is NOT injected into the request; the model uses
    its own default behavior when ``reasoning_effort`` is absent from config.
    """
    if not isinstance(model_id, str) or not model_id.strip():
        return [], None

    override = resolve_reasoning_effort_override(model_id)
    if override is None:
        # No override → all values, no explicit default
        options = [{"value": v, "label": v} for v in REASONING_EFFORT_ALL_VALUES]
        return options, None

    values, default = override
    if not values:
        # Explicitly disabled
        return [], None

    options = [{"value": v, "label": v} for v in values]
    return options, default
