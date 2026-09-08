from dummy_rich_config_ui import DummyRichConfigUiFeature


def test_dummy_rich_config_ui_is_explicitly_enabled() -> None:
    assert DummyRichConfigUiFeature.default_enabled is False


def test_dummy_rich_config_ui_exposes_manual_test_controls() -> None:
    feature = DummyRichConfigUiFeature()
    elements = feature.get_ui_elements({})
    by_key = {element["key"]: element for element in elements}

    appearance = by_key["dummy_rich_ui_appearance"]
    assert appearance["icon"] == "sliders"
    assert appearance["rich_ui"]["kind"] == "dropdown"
    assert "icon" not in appearance["rich_ui"]
    assert appearance["rich_ui"]["placements"] == ["composer", "session_header"]
    assert {option["tone"] for option in appearance["options"]} == {
        "primary",
        "highlight",
        "warning",
        "success",
        "danger",
        "muted",
    }
    assert all("icon" in option for option in appearance["options"])

    toggle = by_key["dummy_rich_ui_toggle"]
    assert toggle["icon"] == "toggle-left"
    assert toggle["rich_ui"]["kind"] == "toggle"
    assert [option["value"] for option in toggle["rich_ui"]["options"]] == [
        False,
        True,
    ]

    disabled = by_key["dummy_rich_ui_disabled_toggle"]
    assert disabled["icon"] == "slash"
    assert disabled["disabled"] is True
    assert disabled["rich_ui"]["default_pinned"] is False
