from __future__ import annotations

from openai_responses_plugins.openai_responses_verbosity_extension import (
    OpenAIResponsesVerbosityExtension,
)


def test_extension_name_and_version() -> None:
    ext = OpenAIResponsesVerbosityExtension()

    assert ext.name == "openai_responses_verbosity"
    assert ext.version == "0.1.0"


def test_get_tags_and_required_tags() -> None:
    ext = OpenAIResponsesVerbosityExtension()

    assert ext.get_tags({}, []) == ["ext:openai_responses_verbosity"]
    assert ext.required_tags() == ["openai_responses", "supports_verbosity"]


def test_get_ui_elements_hidden_without_extension_tag() -> None:
    ext = OpenAIResponsesVerbosityExtension()

    assert ext.get_ui_elements(config={}, tags=["openai_responses"], models=[]) == []


def test_get_ui_elements_hidden_when_config_disables_ui() -> None:
    ext = OpenAIResponsesVerbosityExtension()

    assert (
        ext.get_ui_elements(
            config={"show_verbosity_ui": False},
            tags=["ext:openai_responses_verbosity"],
            models=[],
        )
        == []
    )


def test_get_ui_elements_shows_select_for_supported_models() -> None:
    ext = OpenAIResponsesVerbosityExtension()

    elements = ext.get_ui_elements(
        config={},
        tags=["openai_responses", "supports_verbosity", "ext:openai_responses_verbosity"],
        models=[{"id": "gpt-5-mini"}],
    )

    assert len(elements) == 1
    assert elements[0]["key"] == "verbosity"
    assert [option["value"] for option in elements[0]["options"]] == [
        "low",
        "medium",
        "high",
    ]


def test_init_when_unset_is_noop() -> None:
    ext = OpenAIResponsesVerbosityExtension()
    state = {"config": {}}

    assert ext.init({}, state) == state


def test_init_when_invalid_is_noop() -> None:
    ext = OpenAIResponsesVerbosityExtension()
    state = {"config": {"verbosity": "maximum"}}

    assert ext.init({"verbosity": "maximum"}, state) == state


def test_init_when_valid_adds_state() -> None:
    ext = OpenAIResponsesVerbosityExtension()
    state = {"config": {"verbosity": "high"}}

    new_state = ext.init({"verbosity": "high"}, state)

    assert new_state["openai_responses_verbosity"] == {"verbosity": "high"}


def test_initialize_request_is_noop_without_valid_extension_state() -> None:
    ext = OpenAIResponsesVerbosityExtension()
    state = {"request": {"payload": {"model": "gpt-5-mini"}}}

    native_messages, new_state = ext.initialize_request([], state)

    assert native_messages == []
    assert new_state == state


def test_initialize_request_injects_verbosity_and_preserves_existing_text_format() -> None:
    ext = OpenAIResponsesVerbosityExtension()
    state = {
        "request": {
            "payload": {
                "model": "gpt-5-mini",
                "text": {"format": {"type": "json_schema", "name": "answer"}},
            }
        }
    }
    state = ext.init({"verbosity": "low"}, state)

    native_messages, new_state = ext.initialize_request([], state)

    assert native_messages == []
    payload = new_state["request"]["payload"]
    assert payload["text"] == {
        "format": {"type": "json_schema", "name": "answer"},
        "verbosity": "low",
    }


def test_initialize_request_creates_default_text_format_when_missing() -> None:
    ext = OpenAIResponsesVerbosityExtension()
    state = {"request": {"payload": {"model": "gpt-5-mini"}}}
    state = ext.init({"verbosity": "medium"}, state)

    _native_messages, new_state = ext.initialize_request([], state)

    assert new_state["request"]["payload"]["text"] == {
        "format": {"type": "text"},
        "verbosity": "medium",
    }