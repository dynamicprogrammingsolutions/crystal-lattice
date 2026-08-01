# Dummy application notification plugin

Non-production demonstration plugin for creating, updating, and resolving
owner-memory application notifications. It is intentionally absent from the
default runtime configuration.

Actions:

- `emit_application_notification`
- `resolve_application_notification`
- `expire_application_notification`

Run:

```bash
pytest plugins/dummy-application-notification-app/tests -q
```