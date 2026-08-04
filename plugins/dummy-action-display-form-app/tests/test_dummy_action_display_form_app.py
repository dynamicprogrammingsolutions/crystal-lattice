from __future__ import annotations

from dummy_action_display_form_app import DummyActionDisplayFormAppPlugin


def test_show_display_form_returns_embedded_form_actions() -> None:
    plugin = DummyActionDisplayFormAppPlugin()

    result = plugin.execute_action(None, "show_display_form", {}, None, {})

    display = result["display"]
    assert display["form"]["kind"] == "form"
    assert [field["name"] for field in display["form"]["inputs"]] == [
        "callback_url",
        "note",
        "mode",
    ]
    submit = display["actions"][0]
    assert submit["kind"] == "run_action"
    assert submit["param_map"] == {
        "callback_url": "$form.callback_url",
        "note": "$form.note",
        "mode": "$form.mode",
    }
    assert display["actions"][1]["kind"] == "dismiss"


def test_submit_display_form_records_and_echoes_values() -> None:
    plugin = DummyActionDisplayFormAppPlugin()
    state = plugin.init({})

    result = plugin.execute_action(
        None,
        "submit_display_form",
        {
            "callback_url": "https://example.test/callback?code=abc&state=xyz",
            "note": "manual test",
            "mode": "manual",
            "source": "display_form",
        },
        None,
        state,
    )

    assert state["submitted_values"] == [
        {
            "callback_url": "https://example.test/callback?code=abc&state=xyz",
            "note": "manual test",
            "mode": "manual",
            "source": "display_form",
        }
    ]
    assert result["display"]["variant"] == "success"
    assert "manual test" in result["display"]["body"]