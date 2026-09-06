# dummy-rich-config-ui

Opt-in feature plugin for manually and automatically testing portable rich
configuration controls on mobile and desktop.

The plugin is deliberately disabled by default and is not part of production
default configuration. Load the package and enable it for an agent:

```json
{
  "plugins": [
    "path:${env:BUILTIN_PLUGINS}/dummy-rich-config-ui"
  ],
  "agents": {
    "rich-ui-test": {
      "provider": "your-provider",
      "enabled_plugins": ["dummy_rich_config_ui"]
    }
  }
}
```

Open a session for that agent on a simulator or physical device. The plugin
contributes:

- a rich dropdown shown at the composer and session header, with one option
  for every supported semantic tone and a distinct icon for each option;
- a rich Boolean composer toggle;
- a disabled session-header toggle for muted-state inspection.

All controls are ordinary session configuration settings. Selecting a value
creates the same session override used by Session Settings, and reset removes
that override. The plugin does not change provider requests or model behavior.