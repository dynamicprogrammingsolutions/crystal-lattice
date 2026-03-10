"""OpenRouter model-specific capability constants.

Maps model identifiers (or suffixes) to supported values and defaults for
features like reasoning effort. Used by extensions to build accurate UI
options and defaults per model.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

REASONING_EFFORT_SUPPORTED_VALUES_MAP: Dict[str, List[str]] = {
    "o1": ["low", "medium", "high"],
    "o3": ["low", "medium", "high"],
    "gpt-5": ["minimal", "low", "medium", "high"],
    "gpt-5.1": ["none", "low", "medium", "high"],
    "gpt-5.2": ["none", "low", "medium", "high", "xhigh"],
    "gpt-5-pro": ["high"],
    "gpt-5.2-pro": ["medium", "high", "xhigh"],
    "grok-3-mini": ["low", "high"],
}

# All possible reasoning effort values (union of all models) for config schema enum.
REASONING_EFFORT_ALL_VALUES: List[str] = sorted(
    {v for values in REASONING_EFFORT_SUPPORTED_VALUES_MAP.values() for v in values}
)

# Default reasoning effort per model when supported.
REASONING_EFFORT_DEFAULT_VALUES_MAP: Dict[str, str] = {
    "o1": "medium",
    "o3": "medium",
    "gpt-5": "medium",
    "gpt-5.1": "none",
    "gpt-5.2": "none",
    "gpt-5-pro": "high",
    "gpt-5.2-pro": "medium",
    "grok-3-mini": "low",
}


def resolve_reasoning_effort_model_key(model_id: Optional[str]) -> Optional[str]:
    """Resolve a full model id (e.g. openai/gpt-5) to a key in the capability maps.

    Tries exact match on the suffix after the last '/', then the longest
    map key that appears in the model_id string (so gpt-5.2-pro matches
    openai/gpt-5.2-pro).
    """
    if not isinstance(model_id, str) or not model_id.strip():
        return None
    raw = model_id.strip().lower()
    suffix = raw.split("/")[-1] if "/" in raw else raw
    if suffix in REASONING_EFFORT_SUPPORTED_VALUES_MAP:
        return suffix
    best: Optional[str] = None
    for key in REASONING_EFFORT_SUPPORTED_VALUES_MAP:
        if key in raw and (best is None or len(key) > len(best)):
            best = key
    return best


def get_reasoning_effort_options_and_default(
    model_id: Optional[str],
) -> tuple[List[Dict[str, Any]], Optional[str]]:
    """Return (options list for UI, default value) for reasoning effort for the given model."""
    key = resolve_reasoning_effort_model_key(model_id)
    if key is None:
        return [], None
    supported = REASONING_EFFORT_SUPPORTED_VALUES_MAP.get(key)
    if not supported:
        return [], None
    default = REASONING_EFFORT_DEFAULT_VALUES_MAP.get(key)
    options = [{"value": v, "label": v} for v in supported]
    return options, default
