# dummy-settings-app

Demo application plugin for manually testing server-scoped settings.

It contributes generic server settings controls and records settings lifecycle
calls in plugin state. It is intended for local/manual validation of the
server-settings UI path, not for production behavior.

Example config entry:

```json
{
  "plugins": [
    "path:${env:BUILTIN_PLUGINS}/dummy-settings-app"
  ]
}
```

Equivalent explicit entry form:

```json
{
  "plugins": [
    {
      "path": "${env:BUILTIN_PLUGINS}/dummy-settings-app",
      "entry": "dummy_settings_app_plugin.DummySettingsAppPlugin"
    }
  ]
}
```

The plugin exposes:

- `dummy_server_mode`: select, values `fast` / `careful`
- `dummy_server_enabled`: checkbox
- `dummy_server_name`: text

It also exposes one session-scoped setting, `dummy_session_mode`, so clients can
verify that server settings UIs filter it out.