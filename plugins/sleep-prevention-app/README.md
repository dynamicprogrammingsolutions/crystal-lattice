# Sleep Prevention App Plugin

Application plugin that exposes a live server setting for keeping the local
server process awake.

## Configuration

Add the plugin to the application config:

```json
{
  "plugins": [
    "path:${env:BUILTIN_PLUGINS}/sleep-prevention-app"
  ]
}
```

The plugin exposes one server-scoped setting:

- `sleep_prevention_enabled`: checkbox, default `false`

When the setting is enabled, the plugin starts sleep prevention for the current
server process. When it is disabled or the application closes, the plugin
releases the hold.

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

## Other Platforms

On non-macOS platforms, the plugin uses `wakepy` and activates
`wakepy.keep.running()` for the lifetime of the enabled setting.