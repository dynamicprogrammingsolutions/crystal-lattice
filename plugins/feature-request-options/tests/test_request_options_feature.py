"""Tests for RequestOptionsFeature plugin."""

from __future__ import annotations

from typing import Dict, Any

from feature_request_options.request_options_feature import RequestOptionsFeature


def test_request_options_ui_array_becomes_select() -> None:
    """Array values in request_options_ui become select dropdowns with flat keys."""
    config = {
        "request_options": {"temperature": 0.7},
        "request_options_ui": {
            "temperature": ["0.0", "0.5", "0.7", "1.0"],
        },
    }

    feature = RequestOptionsFeature()
    elements = feature.get_ui_elements(config=config, tags=[], models=[{"id": "test"}])

    assert len(elements) == 1
    assert elements[0]["type"] == "select"
    assert elements[0]["key"] == "request_options__temperature"
    assert elements[0]["label"] == "Temperature"
    assert elements[0]["options"] == [
        {"value": "0.0", "label": "0.0"},
        {"value": "0.5", "label": "0.5"},
        {"value": "0.7", "label": "0.7"},
        {"value": "1.0", "label": "1.0"},
    ]


def test_request_options_ui_string_becomes_text() -> None:
    """'string' value in request_options_ui becomes text input with flat key."""
    config = {
        "request_options": {"user_id": ""},
        "request_options_ui": {
            "user_id": "string",
        },
    }

    feature = RequestOptionsFeature()
    elements = feature.get_ui_elements(config=config, tags=[], models=[{"id": "test"}])

    assert len(elements) == 1
    assert elements[0]["type"] == "text"
    assert elements[0]["key"] == "request_options__user_id"
    assert elements[0]["label"] == "User Id"


def test_request_options_ui_number_becomes_number() -> None:
    """'number' value in request_options_ui becomes number input with flat key."""
    config = {
        "request_options": {"max_tokens": 2048},
        "request_options_ui": {
            "max_tokens": "number",
        },
    }

    feature = RequestOptionsFeature()
    elements = feature.get_ui_elements(config=config, tags=[], models=[{"id": "test"}])

    assert len(elements) == 1
    assert elements[0]["type"] == "number"
    assert elements[0]["key"] == "request_options__max_tokens"
    assert elements[0]["label"] == "Max Tokens"


def test_request_options_ui_label_formatting() -> None:
    """Keys are converted from snake_case to Title Case labels."""
    config = {
        "request_options": {},
        "request_options_ui": {
            "my_custom_setting": "string",
            "another_one_here": ["a", "b"],
            "simple": "number",
        },
    }

    feature = RequestOptionsFeature()
    elements = feature.get_ui_elements(config=config, tags=[], models=[{"id": "test"}])

    assert len(elements) == 3
    keys_to_labels = {el["key"]: el["label"] for el in elements}
    assert keys_to_labels["request_options__my_custom_setting"] == "My Custom Setting"
    assert keys_to_labels["request_options__another_one_here"] == "Another One Here"
    assert keys_to_labels["request_options__simple"] == "Simple"


def test_request_options_ui_ignores_unknown_types() -> None:
    """Unknown value types in request_options_ui are silently skipped."""
    config = {
        "request_options": {},
        "request_options_ui": {
            "valid": ["a", "b"],
            "invalid_bool": True,
            "invalid_dict": {"nested": "value"},
            "invalid_int": 42,
        },
    }

    feature = RequestOptionsFeature()
    elements = feature.get_ui_elements(config=config, tags=[], models=[{"id": "test"}])

    # Only the valid array option should be present
    assert len(elements) == 1
    assert elements[0]["key"] == "request_options__valid"


def test_request_options_ui_empty_list_skipped() -> None:
    """Empty array values in request_options_ui are skipped."""
    config = {
        "request_options": {},
        "request_options_ui": {
            "empty": [],
            "valid": ["a"],
        },
    }

    feature = RequestOptionsFeature()
    elements = feature.get_ui_elements(config=config, tags=[], models=[{"id": "test"}])

    assert len(elements) == 1
    assert elements[0]["key"] == "request_options__valid"


def test_request_options_ui_in_config_schema() -> None:
    """Config schema includes request_options_ui for discovery."""
    feature = RequestOptionsFeature()
    schema = feature.get_config_schema()

    assert "request_options_ui" in schema
    rou_schema = schema["request_options_ui"]
    assert rou_schema.get("type") == "object"
    assert "additionalProperties" in rou_schema


def test_get_ui_elements_returns_empty_without_config() -> None:
    """No request_options_ui config produces no elements."""
    config = {"request_options": {"temperature": 0.7}}

    feature = RequestOptionsFeature()
    elements = feature.get_ui_elements(config=config, tags=[], models=[{"id": "test"}])

    assert elements == []


def test_get_ui_elements_empty_dict() -> None:
    """Empty request_options_ui dict produces no elements."""
    config = {
        "request_options": {},
        "request_options_ui": {},
    }

    feature = RequestOptionsFeature()
    elements = feature.get_ui_elements(config=config, tags=[], models=[{"id": "test"}])

    assert elements == []


def test_get_ui_elements_non_dict_handled_gracefully() -> None:
    """Non-dict request_options_ui is handled gracefully."""
    config = {
        "request_options": {},
        "request_options_ui": "invalid",
    }

    feature = RequestOptionsFeature()
    elements = feature.get_ui_elements(config=config, tags=[], models=[{"id": "test"}])

    assert elements == []


def test_generate_ui_elements_from_options_static() -> None:
    """Direct test of _generate_ui_elements_from_options helper."""
    options = {
        "select_field": ["one", "two", "three"],
        "text_field": "string",
        "number_field": "number",
        "ignored": True,  # Should be skipped
    }

    elements = RequestOptionsFeature._generate_ui_elements_from_options(
        options, key_prefix="request_options__"
    )

    # Should have 3 elements (ignored bool is skipped)
    assert len(elements) == 3

    by_key = {el["key"]: el for el in elements}

    # Check select
    assert by_key["request_options__select_field"]["type"] == "select"
    assert len(by_key["request_options__select_field"]["options"]) == 3

    # Check text
    assert by_key["request_options__text_field"]["type"] == "text"

    # Check number
    assert by_key["request_options__number_field"]["type"] == "number"

    # Check labels
    assert by_key["request_options__select_field"]["label"] == "Select Field"
    assert by_key["request_options__text_field"]["label"] == "Text Field"
    assert by_key["request_options__number_field"]["label"] == "Number Field"


def test_request_options_ui_non_string_array_items_filtered() -> None:
    """Non-string items in array values are filtered out."""
    options = {
        "mixed": ["valid", 123, None, "also_valid", True],
    }

    elements = RequestOptionsFeature._generate_ui_elements_from_options(
        options, key_prefix="request_options__"
    )

    assert len(elements) == 1
    # Only string items should become options
    option_values = [opt["value"] for opt in elements[0]["options"]]
    assert option_values == ["valid", "also_valid"]


def test_init_merges_flat_keys_into_request_options() -> None:
    """init() extracts flat keys and merges them into request_options."""
    feature = RequestOptionsFeature()

    config = {
        "request_options": {"temperature": 0.5, "max_tokens": 512},
        "request_options__temperature": 0.9,  # Flat key override
        "request_options__top_p": 0.95,  # Flat key addition
    }
    state: Dict[str, Any] = {}
    new_state = feature.init(config, state)

    # request_options should have merged values
    options = new_state["config"]["request_options"]
    assert options["temperature"] == 0.9  # Flat key wins
    assert options["max_tokens"] == 512  # Preserved
    assert options["top_p"] == 0.95  # Added


def test_init_removes_flat_keys_from_config() -> None:
    """init() removes flat keys from the resulting config."""
    feature = RequestOptionsFeature()

    config = {
        "request_options": {"temperature": 0.5},
        "request_options__temperature": 0.9,
        "other_key": "preserved",
    }
    state: Dict[str, Any] = {}
    new_state = feature.init(config, state)

    # Flat keys should be removed
    cfg = new_state["config"]
    assert "request_options__temperature" not in cfg
    assert "other_key" in cfg  # Non-flat keys preserved
    assert "request_options" in cfg  # Nested structure preserved


def test_init_with_no_flat_keys() -> None:
    """init() works normally when no flat keys are present."""
    feature = RequestOptionsFeature()

    config = {
        "request_options": {"temperature": 0.7},
        "other_setting": "value",
    }
    state: Dict[str, Any] = {}
    new_state = feature.init(config, state)

    # Everything should be preserved as-is
    assert new_state["config"]["request_options"] == {"temperature": 0.7}
    assert new_state["config"]["other_setting"] == "value"


def test_init_empty_flat_key_name_ignored() -> None:
    """init() ignores flat keys with empty option names."""
    feature = RequestOptionsFeature()

    config = {
        "request_options": {"temperature": 0.5},
        "request_options__": "invalid",  # Empty option name
    }
    state: Dict[str, Any] = {}
    new_state = feature.init(config, state)

    # Empty key should be ignored
    options = new_state["config"]["request_options"]
    assert "temperature" in options
    assert "" not in options  # Empty key not added


def test_initialize_request_merges_options() -> None:
    """initialize_request merges request_options into payload."""
    feature = RequestOptionsFeature()

    config = {
        "request_options": {"temperature": 0.7, "max_tokens": 512},
    }
    state: Dict[str, Any] = {}
    state = feature.init(config, state)

    # Simulate provider having set up a request
    state["request"] = {
        "url": "https://api.example.com/v1/chat/completions",
        "payload": {"model": "gpt-4", "temperature": 0.5},
        "headers": {},
    }

    native_messages: list[dict] = []
    new_native, new_state = feature.initialize_request(native_messages, state)

    # Payload should have merged options (temperature overridden)
    payload = new_state["request"]["payload"]
    assert payload["model"] == "gpt-4"
    assert payload["temperature"] == 0.7  # Overridden
    assert payload["max_tokens"] == 512  # Added


def test_initialize_request_no_options_unchanged() -> None:
    """initialize_request returns unchanged when no request_options."""
    feature = RequestOptionsFeature()

    config = {}  # No request_options
    state: Dict[str, Any] = {}
    state = feature.init(config, state)
    state["request"] = {"payload": {"model": "gpt-4"}}

    native_messages: list[dict] = []
    new_native, new_state = feature.initialize_request(native_messages, state)

    # Should be unchanged
    assert new_state == state


def test_initialize_request_empty_options_unchanged() -> None:
    """initialize_request returns unchanged when request_options is empty."""
    feature = RequestOptionsFeature()

    config = {"request_options": {}}
    state: Dict[str, Any] = {}
    state = feature.init(config, state)
    state["request"] = {"payload": {"model": "gpt-4"}}

    native_messages: list[dict] = []
    new_native, new_state = feature.initialize_request(native_messages, state)

    # Should be unchanged
    assert new_state == state


def test_full_flow_flat_keys_to_payload() -> None:
    """End-to-end: flat keys → init → initialize_request → payload."""
    feature = RequestOptionsFeature()

    # Config with flat UI keys and request_options_ui definition
    config = {
        "model": "gpt-4",
        "request_options": {"temperature": 0.5, "max_tokens": 1024},
        "request_options_ui": {
            "temperature": ["0.0", "0.5", "0.9"],
            "top_p": "number",
        },
        # Simulate UI interaction setting a flat key
        "request_options__temperature": "0.9",
        "request_options__top_p": 0.95,
    }

    # Step 1: init merges flat keys
    state: Dict[str, Any] = {}
    state = feature.init(config, state)

    # Verify flat keys merged and removed
    cfg = state["config"]
    assert "request_options__temperature" not in cfg
    assert "request_options__top_p" not in cfg
    assert cfg["request_options"]["temperature"] == "0.9"
    assert cfg["request_options"]["top_p"] == 0.95

    # Step 2: initialize_request merges into payload
    state["request"] = {
        "url": "https://api.openai.com/v1/chat/completions",
        "payload": {"model": "gpt-4"},
        "headers": {"Authorization": "Bearer token"},
    }

    native_messages: list[dict] = []
    _, new_state = feature.initialize_request(native_messages, state)

    # Verify final payload
    payload = new_state["request"]["payload"]
    assert payload["model"] == "gpt-4"
    assert payload["temperature"] == "0.9"  # From flat key
    assert payload["max_tokens"] == 1024  # Preserved
    assert payload["top_p"] == 0.95  # From flat key
