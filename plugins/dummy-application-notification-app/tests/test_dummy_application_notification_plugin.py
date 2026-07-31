from dummy_application_notification_app import DummyApplicationNotificationPlugin


class _App:
    def __init__(self):
        self.items = []

    def create_application_notification(self, notification):
        stored = {**notification, "id": "application-1", "status": "pending"}
        self.items = [stored]
        return stored

    def list_application_notifications(self):
        return self.items

    def resolve_application_notification(self, notification_id, resolution):
        self.items = [{**self.items[0], "status": "resolved", "resolution": resolution}]
        return self.items[0]


def test_emits_and_resolves_application_notification():
    plugin = DummyApplicationNotificationPlugin()
    app = _App()
    result = plugin.execute_action(
        app,
        "emit_application_notification",
        {"presentation": "banner", "variant": "success"},
        None,
        {},
    )
    assert result["notification_id"] == "application-1"
    assert app.items[0]["display"]["presentation"] == "banner"
    plugin.execute_action(app, "resolve_application_notification", {}, None, {})
    assert app.items[0]["status"] == "resolved"
