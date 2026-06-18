# Sleep Prevention App Plugin

Application plugin that exposes a live server setting for keeping the local
server process awake.

This plugin is intentionally narrow: it applies process-lifetime sleep
prevention for the currently running server. Bridge desired-state sync,
offline UI, and scheduled wake/poll behavior are handled by later server/bridge
layers rather than by this plugin.

## Configuration

Add the plugin to the application config:

```json
{
  "plugins": [
    "path:${env:BUILTIN_PLUGINS}/sleep-prevention-app"
  ]
}
```

With macOS flag customization:

```json
{
  "plugins": [
    "path:${env:BUILTIN_PLUGINS}/sleep-prevention-app"
  ],
  "application": {
    "sleep_prevention_caffeinate_flags": "-is"
  }
}
```

The plugin exposes one server-scoped setting:

- `sleep_prevention_enabled`: checkbox, default `false`

When the setting is enabled, the plugin starts sleep prevention for the current
server process. When it is disabled or the application closes, the plugin
releases the hold.

## UI Usage

With the live server settings UI available:

1. Connect the mobile or desktop client to the running server.
2. Open **Server settings**.
3. Toggle **Prevent server sleep**.

The setting is persisted by `AgentApplication` server settings. If it is still
enabled when the server restarts, startup replay runs the same
`server_settings_changed` lifecycle and the plugin reapplies sleep prevention.

## Lifecycle

The plugin contributes one lifecycle-triggered action:

- `apply_sleep_prevention`, triggered by `server_settings_changed`

The action is idempotent:

- enabled and already active: no new process/context is created
- enabled and inactive: acquire sleep-prevention hold
- disabled and active: release the hold
- disabled and already inactive: no-op

`AgentApplication.close()` calls the plugin cleanup hook, which releases any
active hold. In the FastAPI server, shutdown closes the global
`AgentApplication`, so a running `caffeinate` process or wakepy context is
released during normal shutdown.

## macOS

On macOS, the plugin uses `caffeinate`. The default flags are `-is`.

You can override the flags in the top-level `application` config:

```json
{
  "application": {
    "sleep_prevention_caffeinate_flags": "-is"
  }
}
```

The value may be a shell-style string such as `"-is"` or `"-i -s"`, or a list
such as `["-i", "-s"]`.

Nested configuration is also accepted:

```json
{
  "application": {
    "sleep_prevention": {
      "caffeinate_flags": "-is"
    }
  }
}
```

The default `-is` means:

- `-i`: prevent idle system sleep
- `-s`: prevent system sleep while on AC power

To check whether the plugin is active during manual testing, you can inspect
running processes:

```bash
pgrep -fl caffeinate
```

## Other Platforms

On non-macOS platforms, the plugin uses `wakepy` and activates
`wakepy.keep.running()` for the lifetime of the enabled setting. The wakepy
dependency is declared only for non-macOS platforms and is imported lazily, so
macOS development and tests do not require wakepy to be installed.

## Testing

From the repository root, install and run the plugin tests:

```bash
python -m pip install -e "plugins/sleep-prevention-app[dev]"
pytest plugins/sleep-prevention-app/tests -q
```

The tests mock OS/process ownership. They do not start a real `caffeinate`
process or acquire a real wakepy hold.

## Troubleshooting

If toggling the setting appears to do nothing on macOS:

- confirm the server config includes this plugin
- confirm `sleep_prevention_enabled` is saved in `/server/settings`
- confirm `caffeinate` is available with `command -v caffeinate`
- check for a running process with `pgrep -fl caffeinate`

If toggling fails on non-macOS platforms:

- confirm `wakepy` is installed in the server runtime environment
- check server logs for import or activation errors

If the process remains after shutdown, stop it manually and report the shutdown
path used. Normal `AgentApplication.close()` and FastAPI shutdown should release
the hold.
