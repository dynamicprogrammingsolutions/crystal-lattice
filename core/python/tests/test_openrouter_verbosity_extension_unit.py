"""Unit tests for OpenRouter verbosity extension."""

from __future__ import annotations

from plugins.openrouter_verbosity_extension import OpenRouterVerbosityExtension


def test_extension_name_and_version():
    ext = OpenRouterVerbosityExtension()
    assert ext.name == "openrouter_verbosity"
    assert ext.version == "0.1.0"


def test_get_tags():
    ext = OpenRouterVerbosityExtension()
    assert "ext:openrouter_verbosity" in ext.get_tags({}, [])


def test_required_tags():
    ext = OpenRouterVerbosityExtension()
    assert "openrouter" in ext.required_tags()


def test_init_when_unset_is_noop():
    ext = OpenRouterVerbosityExtension()
    config = {}
    state = {"config": config}
    assert ext.init(config, state) == state


def test_init_when_set_adds_state():
    ext = OpenRouterVerbosityExtension()
    config = {"verbosity": "high"}
    state = {"config": config}
    new_state = ext.init(config, state)
    assert new_state["openrouter_verbosity"]["verbosity"] == "high"


def test_initialize_request_is_noop_when_missing_config():
    ext = OpenRouterVerbosityExtension()
    state = {"request": {"payload": {"model": "openai/gpt-5"}}}
    assert ext.initialize_request([], state) == state


def test_initialize_request_injects_verbosity_for_gpt5():
    ext = OpenRouterVerbosityExtension()
    config = {"verbosity": "low"}
    state = {
        "config": config,
        "request": {"payload": {"model": "openai/gpt-5"}},
    }
    state = ext.init(config, state)
    new_state = ext.initialize_request([], state)
    assert new_state["request"]["payload"]["verbosity"] == "low"


def test_initialize_request_does_not_inject_for_non_gpt5_models():
    ext = OpenRouterVerbosityExtension()
    config = {"verbosity": "medium"}
    state = {
        "config": config,
        "request": {"payload": {"model": "openai/gpt-4o"}},
    }
    state = ext.init(config, state)
    new_state = ext.initialize_request([], state)
    assert "verbosity" not in new_state["request"]["payload"]
