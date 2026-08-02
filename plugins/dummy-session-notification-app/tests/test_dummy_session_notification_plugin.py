from dummy_session_notification_app import DummySessionNotificationPlugin
import pytest


class _App:
    def __init__(self):
        self.items = []

    def create_session_notification(self, session_id, notification):
        stored = {**notification, "id": "session-1", "status": "pending"}
        self.items = [stored]
        return stored

    def list_session_notifications(self, session_id):
        return self.items

    def resolve_session_notification(self, session_id, notification_id, resolution):
        self.items = [{**self.items[0], "status": "resolved", "resolution": resolution}]
        return self.items[0]

    def expire_session_notification(
        self,
        session_id,
        notification_id,
        reason,
    ):
        self.items = [
            {
                **self.items[0],
                "status": "expired",
                "expiration": {"reason": reason},
            }
        ]
        return self.items[0]


def test_emits_and_resolves_session_notification():
    plugin = DummySessionNotificationPlugin()
    app = _App()
    context = {"session_id": "session"}
    result = plugin.execute_action(
        app,
        "emit_session_notification",
        {"presentation": "inline", "variant": "warning"},
        context,
        {},
    )
    assert result["notification_id"] == "session-1"
    assert app.items[0]["display"]["presentation"] == "inline"
    assert app.items[0]["retention"] == {"policy": "until_resolved"}
    plugin.execute_action(app, "resolve_session_notification", {}, context, {})
    assert app.items[0]["status"] == "resolved"

    plugin.execute_action(
        app,
        "emit_session_notification",
        {"presentation": "inline", "variant": "warning"},
        context,
        {},
    )
    plugin.execute_action(app, "expire_session_notification", {}, context, {})
    assert app.items[0]["status"] == "expired"


def test_emits_ttl_session_notification_and_validates_duration():
    plugin = DummySessionNotificationPlugin()
    app = _App()
    context = {"session_id": "session"}
    plugin.execute_action(
        app,
        "emit_session_notification",
        {
            "presentation": "inline",
            "variant": "info",
            "retention": "ttl",
            "ttl_seconds": 5,
        },
        context,
        {},
    )
    assert app.items[0]["retention"]["policy"] == "ttl"
    assert app.items[0]["retention"]["expires_at"].endswith("Z")

    with pytest.raises(ValueError, match="positive integer"):
        plugin.execute_action(
            app,
            "emit_session_notification",
            {
                "presentation": "inline",
                "variant": "info",
                "retention": "ttl",
                "ttl_seconds": 0,
            },
            context,
            {},
        )


def test_configures_session_followups_and_preserves_display_format():
    plugin = DummySessionNotificationPlugin()
    app = _App()
    context = {"session_id": "session"}
    plugin.execute_action(
        app,
        "emit_session_notification",
        {
            "presentation": "banner",
            "variant": "error",
            "followup_buttons": "multiple",
        },
        context,
        {},
    )
    actions = app.items[0]["display"]["actions"]
    assert len(actions) == 3
    result = plugin.execute_action(
        app,
        "notification_followup",
        actions[2]["fixed_params"],
        context,
        {},
    )
    assert result["display"]["presentation"] == "banner"
    assert result["display"]["variant"] == "error"

    plugin.execute_action(
        app,
        "emit_session_notification",
        {
            "presentation": "inline",
            "variant": "info",
            "followup_buttons": "one",
        },
        context,
        {},
    )
    assert len(app.items[0]["display"]["actions"]) == 1
