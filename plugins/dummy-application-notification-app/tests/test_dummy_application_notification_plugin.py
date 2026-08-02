from dummy_application_notification_app import DummyApplicationNotificationPlugin
import pytest


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

    def expire_application_notification(self, notification_id, reason):
        self.items = [
            {
                **self.items[0],
                "status": "expired",
                "expiration": {"reason": reason},
            }
        ]
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
    assert app.items[0]["retention"] == {"policy": "until_resolved"}
    plugin.execute_action(app, "resolve_application_notification", {}, None, {})
    assert app.items[0]["status"] == "resolved"

    plugin.execute_action(
        app,
        "emit_application_notification",
        {"presentation": "banner", "variant": "warning"},
        None,
        {},
    )
    plugin.execute_action(app, "expire_application_notification", {}, None, {})
    assert app.items[0]["status"] == "expired"


def test_emits_ttl_application_notification_and_validates_duration():
    plugin = DummyApplicationNotificationPlugin()
    app = _App()
    plugin.execute_action(
        app,
        "emit_application_notification",
        {
            "presentation": "banner",
            "variant": "info",
            "retention": "ttl",
            "ttl_seconds": 5,
        },
        None,
        {},
    )
    assert app.items[0]["retention"]["policy"] == "ttl"
    assert app.items[0]["retention"]["expires_at"].endswith("Z")

    with pytest.raises(ValueError, match="positive integer"):
        plugin.execute_action(
            app,
            "emit_application_notification",
            {
                "presentation": "banner",
                "variant": "info",
                "retention": "ttl",
                "ttl_seconds": 0,
            },
            None,
            {},
        )
