"""Unit tests for OpenRouter verbosity extension."""

from __future__ import annotations

from openrouter_responses_plugins.openrouter_responses_verbosity_extension import OpenRouterResponsesVerbosityExtension


def test_extension_name_and_version():
    ext = OpenRouterResponsesVerbosityExtension()
    assert ext.name == "openrouter_responses_verbosity"
    assert ext.version == "0.1.0"


def test_get_tags():
    ext = OpenRouterResponsesVerbosityExtension()
    assert "ext:openrouter_responses_verbosity" in ext.get_tags({}, [])


def test_required_tags():
    ext = OpenRouterResponsesVerbosityExtension()
    assert "openrouter_responses" in ext.required_tags()


def test_init_when_unset_is_noop():
    ext = OpenRouterResponsesVerbosityExtension()
    config = {}
    state = {"config": config}
    assert ext.init(config, state) == state


def test_init_when_set_adds_state():
    ext = OpenRouterResponsesVerbosityExtension()
    config = {"verbosity": "high"}
    state = {"config": config}
    new_state = ext.init(config, state)
    assert new_state["openrouter_responses_verbosity"]["verbosity"] == "high"


def test_initialize_request_is_noop_when_missing_config():
    ext = OpenRouterResponsesVerbosityExtension()
    state = {"request": {"payload": {"model": "openai/gpt-5"}}}
    assert ext.initialize_request([], state) == state


def test_initialize_request_injects_verbosity_for_gpt5():
    ext = OpenRouterResponsesVerbosityExtension()
    config = {"verbosity": "low"}
    state = {
        "config": config,
        "request": {"payload": {"model": "openai/gpt-5"}},
    }
    state = ext.init(config, state)
    new_state = ext.initialize_request([], state)
    payload = new_state["request"]["payload"]
    assert payload["text"]["verbosity"] == "low"


def test_initialize_request_stages_verbosity_in_request_options():
    ext = OpenRouterResponsesVerbosityExtension()
    config = {"verbosity": "medium"}
    state = {
        "config": config,
        "request": {"payload": {"model": "openai/gpt-4o"}},
    }
    state = ext.init(config, state)
    new_state = ext.initialize_request([], state)
    payload = new_state["request"]["payload"]
    assert payload["text"]["verbosity"] == "medium"
