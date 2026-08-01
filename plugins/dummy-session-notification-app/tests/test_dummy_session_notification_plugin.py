from dummy_session_notification_app import DummySessionNotificationPlugin


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
