from __future__ import annotations

from copy import deepcopy

import pytest

from agent_app.application_future import AgentApplication
from agent_app.config import (
    build_agent_config,
    resolve_config_mixins,
    resolve_request_config,
    validate_resolved_config_variants,
)
from agent_app.config_merge import merge_config, validate_merge_directives
from agent_app.config_variants import (
    resolve_config_variants,
    validate_config_variants,
)
from agent_core import AgentCore


def test_merge_policy_selects_shallow_for_specific_sibling_key() -> None:
    base = {
        "request_options": {
            "temperature": 0.2,
            "thinking": {"type": "enabled", "budget_tokens": 1024},
        },
        "headers": {"x-base": "one", "x-shared": "base"},
    }
    overlay = {
        "$merge": {
            "default": "deep",
            "shallow": ["request_options"],
        },
        "request_options": {
            "thinking": {"type": "adaptive"},
        },
        "headers": {"x-shared": "overlay"},
    }

    merged = merge_config(base, overlay, default_mode="shallow")

    assert merged == {
        "request_options": {
            "thinking": {"type": "adaptive"},
        },
        "headers": {"x-base": "one", "x-shared": "overlay"},
    }
    assert "$merge" not in merged


def test_nested_merge_policy_overrides_deep_parent_for_direct_child() -> None:
    base = {
        "request_options": {
            "temperature": 0.2,
            "thinking": {"type": "enabled", "budget_tokens": 1024},
            "output_config": {"effort": "medium", "detail": "full"},
        }
    }
    overlay = {
        "$merge": "deep",
        "request_options": {
            "$merge": {
                "default": "deep",
                "shallow": ["thinking"],
            },
            "thinking": {"type": "adaptive", "display": "summarized"},
            "output_config": {"effort": "high"},
        },
    }

    merged = merge_config(base, overlay, default_mode="shallow")

    assert merged == {
        "request_options": {
            "temperature": 0.2,
            "thinking": {"type": "adaptive", "display": "summarized"},
            "output_config": {"effort": "high", "detail": "full"},
        }
    }


def test_merge_policy_can_select_deep_key_under_shallow_default() -> None:
    base = {
        "request_options": {"temperature": 0.2},
        "headers": {"x-base": "one", "x-shared": "base"},
    }
    overlay = {
        "$merge": {
            "default": "shallow",
            "deep": ["headers"],
        },
        "request_options": {"thinking": {"type": "adaptive"}},
        "headers": {"x-shared": "overlay"},
    }

    merged = merge_config(base, overlay, default_mode="deep")

    assert merged == {
        "request_options": {"thinking": {"type": "adaptive"}},
        "headers": {"x-base": "one", "x-shared": "overlay"},
    }


def test_merge_arrays_replace_and_are_not_interpreted() -> None:
    base = {"betas": ["old"], "items": [{"$merge": "deep", "value": 1}]}
    overlay = {
        "$merge": "deep",
        "betas": ["new"],
        "items": [{"$merge": "shallow", "value": 2}],
    }

    merged = merge_config(base, overlay, default_mode="deep")

    assert merged == {
        "betas": ["new"],
        "items": [{"$merge": "shallow", "value": 2}],
    }


def test_merge_does_not_mutate_inputs() -> None:
    base = {"nested": {"left": 1}}
    overlay = {"$merge": "deep", "nested": {"right": 2}}
    original_base = deepcopy(base)
    original_overlay = deepcopy(overlay)

    assert merge_config(base, overlay, default_mode="shallow") == {
        "nested": {"left": 1, "right": 2}
    }
    assert base == original_base
    assert overlay == original_overlay


def test_merge_validation_reports_duplicate_key_assignments() -> None:
    errors = validate_merge_directives(
        {
            "$merge": {
                "default": "deep",
                "shallow": ["request_options"],
                "deep": ["request_options"],
            }
        },
        path="agents.example",
    )

    assert any(
        error["type"] == "config_merge_invalid"
        and error["path"] == "agents.example.$merge.deep[0]"
        for error in errors
    )


def test_mixin_root_merge_directive_preserves_legacy_precedence() -> None:
    resolved, errors = resolve_config_mixins(
        {
            "mixins": {
                "base": {
                    "request_options": {
                        "temperature": 0.2,
                        "thinking": {"type": "enabled"},
                    },
                    "headers": {"x-base": "one"},
                }
            },
            "providers": {
                "dummy": {
                    "provider": "dummy_provider",
                }
            },
            "agents": {
                "default": {
                    "provider": "dummy",
                    "mixin_refs": ["base"],
                    "$merge": {
                        "default": "deep",
                        "shallow": ["request_options"],
                    },
                    "request_options": {
                        "thinking": {"type": "adaptive"},
                    },
                    "headers": {"x-agent": "two"},
                }
            },
        }
    )

    assert errors == []
    config = build_agent_config(resolved, "default")
    assert config["request_options"] == {
        "thinking": {"type": "adaptive"},
    }
    assert config["headers"] == {"x-base": "one", "x-agent": "two"}
    assert "$merge" not in config


def test_mixin_merge_directive_governs_own_merge_action_and_is_consumed() -> None:
    resolved, errors = resolve_config_mixins(
        {
            "mixins": {
                "system-base": {
                    "system_message": {
                        "template": "base",
                        "variables": {"INTRO": "x"},
                        "enabled": True,
                    },
                    "request_options": {
                        "temperature": 0.2,
                        "thinking": {"type": "enabled"},
                    },
                },
                "preset": {
                    "$merge": {"default": "shallow", "deep": ["system_message"]},
                    "bash_cwd_persistence": True,
                    "request_options": {"temperature": 0.5},
                    "system_message": {"template": "preset"},
                },
            },
            "providers": {
                "dummy": {
                    "provider": "dummy_provider",
                }
            },
            "agents": {
                "default": {
                    "provider": "dummy",
                    "mixin_refs": ["system-base", "preset"],
                }
            },
        }
    )

    assert errors == []
    agent = resolved["agents"]["default"]
    # The preset's own policy governed its merge: system_message deep-merged
    # with the base while request_options shallow-replaced it.
    assert agent["system_message"] == {
        "template": "preset",
        "variables": {"INTRO": "x"},
        "enabled": True,
    }
    assert agent["request_options"] == {"temperature": 0.5}
    assert agent["bash_cwd_persistence"] is True
    # The mixin-carried directive was consumed and does not persist into the
    # referrer's resolved configuration.
    assert "$merge" not in agent
    assert "$merge" not in agent["system_message"]


def test_mixin_nested_merge_directive_is_consumed_at_mixin_merge() -> None:
    resolved, errors = resolve_config_mixins(
        {
            "mixins": {
                "agent-options": {
                    "$merge": "deep",
                    "request_options": {
                        "$merge": {
                            "default": "deep",
                            "shallow": ["thinking"],
                        },
                        "thinking": {"type": "adaptive"},
                    },
                }
            },
            "providers": {
                "dummy": {
                    "provider": "dummy_provider",
                    "request_options": {
                        "temperature": 0.2,
                        "thinking": {
                            "type": "enabled",
                            "budget_tokens": 1024,
                        },
                    },
                }
            },
            "agents": {
                "default": {
                    "provider": "dummy",
                    "mixin_refs": ["agent-options"],
                }
            },
        }
    )

    assert errors == []
    agent = resolved["agents"]["default"]
    # The mixin's nested directive was consumed by its merge action and does
    # not survive into the resolved agent.
    assert "$merge" not in agent
    assert "$merge" not in agent["request_options"]

    # Without an agent-carried policy, the provider merge uses the default
    # shallow mode, so the agent's request_options replace the provider's.
    config = build_agent_config(resolved, "default")
    assert config["request_options"] == {
        "thinking": {"type": "adaptive"},
    }


def test_agent_nested_merge_directive_governs_provider_merge() -> None:
    resolved, errors = resolve_config_mixins(
        {
            "mixins": {
                "agent-options": {
                    "request_options": {
                        "thinking": {"type": "adaptive"},
                    },
                }
            },
            "providers": {
                "dummy": {
                    "provider": "dummy_provider",
                    "request_options": {
                        "temperature": 0.2,
                        "thinking": {
                            "type": "enabled",
                            "budget_tokens": 1024,
                        },
                    },
                }
            },
            "agents": {
                "default": {
                    "provider": "dummy",
                    "mixin_refs": ["agent-options"],
                    "$merge": {"default": "shallow", "deep": ["request_options"]},
                    "request_options": {
                        "$merge": {
                            "default": "deep",
                            "shallow": ["thinking"],
                        },
                    },
                }
            },
        }
    )

    assert errors == []
    # A nested policy declared on the agent itself governs the later
    # provider-to-agent merge.
    config = build_agent_config(resolved, "default")
    assert config["request_options"] == {
        "temperature": 0.2,
        "thinking": {"type": "adaptive"},
    }
    assert "$merge" not in config["request_options"]


def test_chained_mixin_consumes_inner_directive_and_keeps_own() -> None:
    resolved, errors = resolve_config_mixins(
        {
            "mixins": {
                "inner": {
                    "$merge": "deep",
                    "system_message": {
                        "template": "inner",
                        "variables": {"INTRO": "x"},
                    },
                },
                "outer": {
                    "$merge": {"default": "shallow", "deep": ["system_message"]},
                    "mixin_refs": ["inner"],
                    "system_message": {"template": "outer"},
                },
            },
            "providers": {
                "dummy": {
                    "provider": "dummy_provider",
                }
            },
            "agents": {
                "default": {
                    "provider": "dummy",
                    "mixin_refs": ["outer"],
                }
            },
        }
    )

    assert errors == []
    agent = resolved["agents"]["default"]
    # The inner mixin's deep directive governed its merge into the outer
    # mixin and was consumed there; the outer mixin's own policy then
    # governed its merge into the agent and was consumed as well.
    assert agent["system_message"] == {
        "template": "outer",
        "variables": {"INTRO": "x"},
    }
    assert "$merge" not in agent
    assert "$merge" not in agent["system_message"]


def test_legacy_mixin_merge_remains_supported() -> None:
    resolved, errors = resolve_config_mixins(
        {
            "mixins": {
                "base": {
                    "nested": {"left": 1},
                }
            },
            "providers": {"dummy": {"provider": "dummy_provider"}},
            "agents": {
                "default": {
                    "provider": "dummy",
                    "mixin_refs": ["base"],
                    "mixin_merge": "deep",
                    "nested": {"right": 2},
                }
            },
        }
    )

    assert errors == []
    assert build_agent_config(resolved, "default")["nested"] == {
        "left": 1,
        "right": 2,
    }


def test_conflicting_legacy_and_new_merge_modes_are_rejected() -> None:
    _resolved, errors = resolve_config_mixins(
        {
            "providers": {"dummy": {"provider": "dummy_provider"}},
            "agents": {
                "default": {
                    "provider": "dummy",
                    "mixin_merge": "shallow",
                    "$merge": "deep",
                }
            },
        }
    )

    assert any(
        error["type"] == "mixin_config_invalid"
        and error["path"] == "agents.default.$merge"
        for error in errors
    )


def test_equal_legacy_and_new_merge_modes_are_accepted() -> None:
    resolved, errors = resolve_config_mixins(
        {
            "mixins": {
                "base": {"nested": {"left": 1}},
            },
            "providers": {"dummy": {"provider": "dummy_provider"}},
            "agents": {
                "default": {
                    "provider": "dummy",
                    "mixin_refs": ["base"],
                    "mixin_merge": "deep",
                    "$merge": "deep",
                    "nested": {"right": 2},
                }
            },
        }
    )

    assert errors == []
    assert build_agent_config(resolved, "default")["nested"] == {
        "left": 1,
        "right": 2,
    }


def test_variants_support_exact_regex_order_and_deep_default() -> None:
    base = {
        "model": "claude-sonnet-5",
        "request_options": {"temperature": 0.2},
        "$variants": [
            {
                "$when": {"model": "claude-sonnet-5"},
                "request_options": {
                    "thinking": {"type": "adaptive"},
                },
            },
            {
                "$when": {"model": {"$matches": "^claude-sonnet-5(?:$|-)"}},
                "request_options": {
                    "thinking": {"display": "summarized"},
                    "output_config": {"effort": "high"},
                },
            },
        ],
    }

    resolved, errors = resolve_config_variants(base, selector=base)

    assert errors == []
    assert resolved == {
        "model": "claude-sonnet-5",
        "request_options": {
            "temperature": 0.2,
            "thinking": {
                "type": "adaptive",
                "display": "summarized",
            },
            "output_config": {"effort": "high"},
        },
    }


def test_nested_variants_use_root_selector_and_controls_are_removed() -> None:
    base = {
        "model": "claude-haiku-4-5-20251001",
        "request_options": {
            "temperature": 0.2,
            "$variants": [
                {
                    "$when": {"model": {"$matches": "^claude-haiku-4-5(?:$|-)"}},
                    "$merge": {
                        "default": "deep",
                        "shallow": ["thinking"],
                    },
                    "thinking": {
                        "type": "enabled",
                        "budget_tokens": 1024,
                    },
                }
            ],
        },
    }

    resolved, errors = resolve_config_variants(base, selector=base)

    assert errors == []
    assert resolved["request_options"] == {
        "temperature": 0.2,
        "thinking": {
            "type": "enabled",
            "budget_tokens": 1024,
        },
    }
    assert "$variants" not in resolved["request_options"]
    assert "$merge" not in resolved["request_options"]


def test_variant_conditions_do_not_observe_values_from_earlier_variants() -> None:
    base = {
        "model": "example",
        "$variants": [
            {
                "$when": {"model": "example"},
                "family": "selected",
            },
            {
                "$when": {"family": "selected"},
                "unexpected": True,
            },
        ],
    }

    resolved, errors = resolve_config_variants(base, selector=base)

    assert errors == []
    assert resolved["family"] == "selected"
    assert "unexpected" not in resolved


def test_selected_overlay_can_contain_nested_variants() -> None:
    base = {
        "model": "example",
        "$variants": [
            {
                "$when": {"model": "example"},
                "feature": {
                    "$variants": [
                        {
                            "$when": {"model": "example"},
                            "enabled": True,
                        }
                    ]
                },
            }
        ],
    }

    resolved, errors = resolve_config_variants(base, selector=base)

    assert errors == []
    assert resolved == {
        "model": "example",
        "feature": {"enabled": True},
    }


def test_request_config_reselects_variants_for_model_override_without_leaks() -> None:
    base = {
        "model": "claude-haiku-4-5-20251001",
        "$variants": [
            {
                "$when": {"model": {"$matches": "^claude-haiku-4-5(?:$|-)"}},
                "request_options": {
                    "thinking": {
                        "type": "enabled",
                        "budget_tokens": 1024,
                    }
                },
            },
            {
                "$when": {"model": {"$matches": "^claude-sonnet-5(?:$|-)"}},
                "betas": ["context-management-2025-06-27"],
                "request_options": {
                    "thinking": {
                        "type": "adaptive",
                        "display": "summarized",
                    }
                },
            },
        ],
    }

    haiku = resolve_request_config(base, None)
    sonnet = resolve_request_config(base, {"model": "claude-sonnet-5"})
    haiku_again = resolve_request_config(base, {"model": base["model"]})

    assert haiku["request_options"]["thinking"] == {
        "type": "enabled",
        "budget_tokens": 1024,
    }
    assert sonnet["request_options"]["thinking"] == {
        "type": "adaptive",
        "display": "summarized",
    }
    assert sonnet["betas"] == ["context-management-2025-06-27"]
    assert "betas" not in haiku_again
    assert haiku_again["request_options"] == haiku["request_options"]


def test_explicit_request_overrides_apply_after_variants() -> None:
    base = {
        "model": "example",
        "$variants": [
            {
                "$when": {"model": "example"},
                "request_options": {
                    "temperature": 0.2,
                    "thinking": {"type": "adaptive"},
                },
            }
        ],
    }

    resolved = resolve_request_config(
        base,
        {"request_options": {"temperature": 0.9}},
    )

    assert resolved["request_options"] == {"temperature": 0.9}


def test_variants_inside_arrays_are_opaque() -> None:
    base = {
        "model": "example",
        "items": [
            {
                "$variants": [
                    {
                        "$when": {"model": "example"},
                        "selected": True,
                    }
                ]
            }
        ],
    }

    resolved, errors = resolve_config_variants(base, selector=base)

    assert errors == []
    assert resolved["items"] == base["items"]


def test_variant_validation_rejects_invalid_regex_and_root_topology() -> None:
    errors = validate_config_variants(
        {
            "$variants": [
                {
                    "$when": {"model": {"$matches": "["}},
                    "provider": "other",
                }
            ]
        },
        path="agents.default",
    )

    assert any("Invalid regular expression" in error["detail"] for error in errors)
    assert any(
        error["type"] == "config_variant_protected_key"
        and error["path"] == "agents.default.$variants[0].provider"
        for error in errors
    )


def test_nested_provider_request_key_is_not_treated_as_topology() -> None:
    errors = validate_config_variants(
        {
            "request_options": {
                "$variants": [
                    {
                        "$when": {"model": "example"},
                        "provider": {
                            "order": ["anthropic"],
                            "allow_fallbacks": False,
                        },
                    }
                ]
            }
        },
        path="agents.default",
    )

    assert errors == []


def test_resolved_config_variant_validation_covers_mixins_providers_and_agents() -> (
    None
):
    errors = validate_resolved_config_variants(
        {
            "mixins": {
                "broken": {
                    "$variants": [
                        {
                            "$when": {"model": {"$unknown": "value"}},
                            "value": True,
                        }
                    ]
                }
            },
            "providers": {},
            "agents": {},
        }
    )

    assert any(
        error["path"] == "mixins.broken.$variants[0].$when.model" for error in errors
    )


def test_variant_validation_enforces_maximum_mapping_depth() -> None:
    config: dict[str, object] = {"value": True}
    for _index in range(4):
        config = {"nested": config}

    errors = validate_config_variants(
        config,
        path="agents.default",
        max_depth=2,
    )

    assert any(
        error["type"]
        in {
            "config_merge_depth_exceeded",
            "config_variant_depth_exceeded",
        }
        for error in errors
    )


def test_agent_application_rejects_invalid_variants(tmp_path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        __import__("json").dumps(
            {
                "plugins": ["tests.dummy_provider.DummyProvider"],
                "providers": {
                    "dummy": {"provider": "dummy_provider"},
                },
                "agents": {
                    "default": {
                        "provider": "dummy",
                        "$variants": [
                            {
                                "$when": {"model": {"$matches": "["}},
                                "temperature": 0.2,
                            }
                        ],
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="config_variant_invalid"):
        AgentApplication(
            str(config_path),
            str(tmp_path / "sessions"),
            core_factory=AgentCore,
        )
