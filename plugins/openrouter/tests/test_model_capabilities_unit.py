"""Unit tests for the regex-based reasoning_effort override system in model_capabilities."""

from __future__ import annotations

from openrouter_plugins.model_capabilities import (
    REASONING_EFFORT_ALL_VALUES,
    REASONING_EFFORT_MODEL_OVERRIDES,
    get_reasoning_effort_options_and_default,
    resolve_reasoning_effort_override,
)


def _option_values(options):
    return [opt["value"] for opt in options]


# --- Override map coverage --------------------------------------------------


def test_all_values_enum_order():
    """REASONING_EFFORT_ALL_VALUES is in display order with all 7 values."""
    assert REASONING_EFFORT_ALL_VALUES == [
        "none",
        "minimal",
        "low",
        "medium",
        "high",
        "xhigh",
        "max",
    ]


def test_override_patterns_are_regex_compiled():
    """All patterns in REASONING_EFFORT_MODEL_OVERRIDES are compiled regex."""
    import re

    for pattern, _values, _default in REASONING_EFFORT_MODEL_OVERRIDES:
        assert isinstance(
            pattern, re.Pattern
        ), f"pattern {pattern!r} is not a compiled regex"


def test_override_order_most_specific_first():
    """gpt-5.2-pro appears before gpt-5.2 so it matches first."""
    patterns = [pattern.pattern for pattern, _v, _d in REASONING_EFFORT_MODEL_OVERRIDES]
    gpt52pro_idx = patterns.index(r"gpt-5\.2-pro")
    gpt52_idx = patterns.index(r"gpt-5\.2")
    assert gpt52pro_idx < gpt52_idx, "gpt-5.2-pro must come before gpt-5.2"
    gpt5pro_idx = patterns.index(r"gpt-5-pro")
    gpt5_idx = patterns.index(r"gpt-5")
    assert gpt5pro_idx < gpt5_idx, "gpt-5-pro must come before gpt-5"


# --- GPT models (override matches) ------------------------------------------


def test_gpt_5_2_options_and_default():
    options, default = get_reasoning_effort_options_and_default("openai/gpt-5.2")
    assert _option_values(options) == ["none", "low", "medium", "high", "xhigh"]
    assert default == "none"


def test_gpt_5_2_mini_options_and_default():
    options, default = get_reasoning_effort_options_and_default("openai/gpt-5.2-mini")
    assert _option_values(options) == ["none", "low", "medium", "high", "xhigh"]
    assert default == "none"


def test_gpt_5_2_pro_options_and_default():
    options, default = get_reasoning_effort_options_and_default("openai/gpt-5.2-pro")
    assert _option_values(options) == ["medium", "high", "xhigh"]
    assert default == "medium"


def test_gpt_5_1_options_and_default():
    options, default = get_reasoning_effort_options_and_default("openai/gpt-5.1")
    assert _option_values(options) == ["none", "low", "medium", "high"]
    assert default == "none"


def test_gpt_5_options_and_default():
    options, default = get_reasoning_effort_options_and_default("openai/gpt-5")
    assert _option_values(options) == ["minimal", "low", "medium", "high"]
    assert default == "medium"


def test_gpt_5_mini_options_and_default():
    options, default = get_reasoning_effort_options_and_default("openai/gpt-5-mini")
    assert _option_values(options) == ["minimal", "low", "medium", "high"]
    assert default == "medium"


def test_gpt_5_pro_options_and_default():
    options, default = get_reasoning_effort_options_and_default("openai/gpt-5-pro")
    assert _option_values(options) == ["high"]
    assert default == "high"


def test_o1_options_and_default():
    options, default = get_reasoning_effort_options_and_default("openai/o1")
    assert _option_values(options) == ["low", "medium", "high"]
    assert default == "medium"


def test_o1_mini_options_and_default():
    options, default = get_reasoning_effort_options_and_default("openai/o1-mini")
    assert _option_values(options) == ["low", "medium", "high"]
    assert default == "medium"


def test_o3_options_and_default():
    options, default = get_reasoning_effort_options_and_default("openai/o3")
    assert _option_values(options) == ["low", "medium", "high"]
    assert default == "medium"


def test_grok_3_mini_options_and_default():
    options, default = get_reasoning_effort_options_and_default("x-ai/grok-3-mini")
    assert _option_values(options) == ["low", "high"]
    assert default == "low"


# --- Non-GPT models (no override → all values) ------------------------------


def test_glm_5_2_returns_all_values_no_default():
    """z-ai/glm-5.2 is not in the override map → all values, no default."""
    options, default = get_reasoning_effort_options_and_default("z-ai/glm-5.2")
    assert _option_values(options) == REASONING_EFFORT_ALL_VALUES
    assert default is None


def test_deepseek_v4_pro_returns_all_values_no_default():
    options, default = get_reasoning_effort_options_and_default(
        "deepseek/deepseek-v4-pro"
    )
    assert _option_values(options) == REASONING_EFFORT_ALL_VALUES
    assert default is None


def test_kimi_k2_7_returns_all_values_no_default():
    options, default = get_reasoning_effort_options_and_default(
        "moonshotai/kimi-k2.7-code"
    )
    assert _option_values(options) == REASONING_EFFORT_ALL_VALUES
    assert default is None


def test_minimax_m3_returns_all_values_no_default():
    options, default = get_reasoning_effort_options_and_default("minimax/minimax-m3")
    assert _option_values(options) == REASONING_EFFORT_ALL_VALUES
    assert default is None


def test_unknown_model_returns_all_values_no_default():
    options, default = get_reasoning_effort_options_and_default("some-unknown-model")
    assert _option_values(options) == REASONING_EFFORT_ALL_VALUES
    assert default is None


# --- Edge cases -------------------------------------------------------------


def test_none_model_id_returns_empty():
    options, default = get_reasoning_effort_options_and_default(None)
    assert options == []
    assert default is None


def test_empty_model_id_returns_empty():
    options, default = get_reasoning_effort_options_and_default("")
    assert options == []
    assert default is None


def test_whitespace_model_id_returns_empty():
    options, default = get_reasoning_effort_options_and_default("   ")
    assert options == []
    assert default is None


def test_model_id_case_insensitive():
    """Override matching is case-insensitive (model_id is lowercased)."""
    options, default = get_reasoning_effort_options_and_default("OpenAI/GPT-5.2")
    assert _option_values(options) == ["none", "low", "medium", "high", "xhigh"]
    assert default == "none"


# --- Empty-list disable behavior --------------------------------------------


def test_empty_list_override_disables_ui():
    """An override with an empty values list disables the reasoning_effort UI.

    This is a synthetic test using a temporary override entry to verify the
    disable behavior without polluting the production override map.
    """
    import re

    from openrouter_plugins import model_capabilities as mod

    # Save original and inject a temporary disable entry for a test model.
    original = mod.REASONING_EFFORT_MODEL_OVERRIDES
    try:
        mod.REASONING_EFFORT_MODEL_OVERRIDES = [
            (re.compile(r"non-reasoning-test-model"), [], None),
            *original,
        ]
        options, default = get_reasoning_effort_options_and_default(
            "foo/non-reasoning-test-model"
        )
        assert options == [], "empty override should disable UI (empty options)"
        assert default is None
    finally:
        mod.REASONING_EFFORT_MODEL_OVERRIDES = original


# --- resolve_reasoning_effort_override --------------------------------------


def test_resolve_override_returns_values_and_default():
    values, default = resolve_reasoning_effort_override("openai/gpt-5.2")
    assert values == ["none", "low", "medium", "high", "xhigh"]
    assert default == "none"


def test_resolve_override_returns_none_for_unknown_model():
    assert resolve_reasoning_effort_override("z-ai/glm-5.2") is None


def test_resolve_override_returns_none_for_none():
    assert resolve_reasoning_effort_override(None) is None


def test_resolve_override_first_match_wins():
    """gpt-5.2-pro matches before gpt-5.2 (first-match-wins ordering)."""
    values, _default = resolve_reasoning_effort_override("openai/gpt-5.2-pro")
    assert values == [
        "medium",
        "high",
        "xhigh",
    ], "should match gpt-5.2-pro, not gpt-5.2"
