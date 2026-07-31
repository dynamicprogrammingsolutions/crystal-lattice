from dummy_action_display_app import DummyActionDisplayPlugin


def test_returns_requested_standard_display():
    plugin = DummyActionDisplayPlugin()
    result = plugin.execute_action(
        object(),
        "show_action_display",
        {"presentation": "modal", "variant": "error"},
        None,
        {},
    )
    assert result["display"]["presentation"] == "modal"
    assert result["display"]["variant"] == "error"
