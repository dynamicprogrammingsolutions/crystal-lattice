# Dummy session notification plugin

Non-production demonstration plugin for persistent session notifications and
follow-up actions. It is enabled only by examples and integration tests.

Actions:

- `emit_session_notification`
- `resolve_session_notification`
- `expire_session_notification`
- `notification_followup`

Run:

```bash
pytest plugins/dummy-session-notification-app/tests -q
```