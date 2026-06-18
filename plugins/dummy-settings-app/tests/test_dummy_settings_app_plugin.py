from __future__ import annotations

from dummy_settings_app_plugin import DummySettingsAppPlugin


def test_dummy_settings_app_plugin_exposes_server_scoped_controls() -> None:
    plugin = DummySettingsAppPlugin()
    state = plugin.init({})

    elements = plugin.get_ui_elements(state)

    server_keys = {
        element["key"]
        for element in elements
        if element.get("ui_type") == "config" and element.get("scope") == "server"
    }
    assert server_keys == {
        "dummy_server_mode",
        "dummy_server_enabled",
        "dummy_server_name",
        "dummy_show_more_parameters",
    }
    assert any(element.get("scope") == "session" for element in elements)
    assert not any(
        str(element.get("key", "")).startswith("dummy_extra_text_")
        for element in elements
    )


def test_dummy_settings_app_plugin_adds_extra_controls_from_server_settings_context() -> None:
    plugin = DummySettingsAppPlugin()
    state = plugin.init({})

    elements = plugin.get_ui_elements(
        state,
        {},
        {"server_settings": {"dummy_show_more_parameters": True}},
    )

    extra_keys = [
        element["key"]
        for element in elements
        if str(element.get("key", "")).startswith("dummy_extra_text_")
    ]
    assert len(extra_keys) == 16
    assert extra_keys[0] == "dummy_extra_text_01"
    assert extra_keys[-1] == "dummy_extra_text_16"


def test_dummy_settings_app_plugin_records_lifecycle_context() -> None:
    plugin = DummySettingsAppPlugin()
    state = plugin.init({})

    result = plugin.execute_action(
        None,
        "record_server_settings_changed",
        {},
        {
            "lifecycle": "server_settings_changed",
            "scope": "server",
            "changed_keys": ["dummy_server_mode"],
        },
        state,
    )

    assert result["recorded"] is True
    assert plugin.executed[-1]["context"]["scope"] == "server"
    assert state["settings_lifecycle_calls"][-1]["context"]["changed_keys"] == [
        "dummy_server_mode"
    ]