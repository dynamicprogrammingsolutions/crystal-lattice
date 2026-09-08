# Application configuration

Crystal Lattice configuration combines providers, agents, plugin packages,
reusable mixins, model-selected variants, placeholders, and application
settings in one JSON file.

## Configuration layers

The main layers are:

- top-level settings and plugin package specs;
- reusable `mixins`;
- named `providers`;
- named `agents`;
- session/request overrides stored with a session.

Provider settings are merged into the selected agent. Mixins are expanded
before that provider-to-agent merge. Model-selected variants are evaluated
after the effective model override is known, and explicit session/request
overrides apply last.

## Guides

- [Plugin configuration](configuration-plugins.md): package specs, loading
  layers, enablement, installation policy, Node tools, and Bash tools.
- [Placeholders](configuration-placeholders.md): environment variables, file
  loading, derived paths, and literal values.
- [Configuration mixins](configuration-mixins.md): reusable fragments,
  precedence, recursion, and shallow/deep merge behavior.
- [Configuration variants](configuration-variants.md): model-selected
  settings, exact and regex conditions, nested variants, and merge policies.
- [System-message templates](configuration-system-messages.md): file-backed
  templates, runtime helpers, dynamic sections, and UI contributions.
- [Terminal configuration](terminal.md#terminal-configuration): terminal
  presentation and application-owned UI settings.

## Minimal example

```json
{
  "plugins": [
    "path:${env:BUILTIN_PLUGINS}/openrouter"
  ],
  "providers": {
    "openrouter": {
      "provider": "openrouter",
      "api_key": "${env:OPENROUTER_API_KEY}",
      "base_url": "https://openrouter.ai/api/v1"
    }
  },
  "agents": {
    "default": {
      "provider": "openrouter",
      "model": "openai/gpt-5-mini"
    }
  }
}
```

The command searches for configuration in:

1. `./.crystal/config.json`
2. `~/.crystal/config.json`

Use `--config` for an explicit file or `--config-local` to create and use
`./.crystal/config.json`.

## Session-list loading

The current local session-list implementation persists complete derived
summaries so a new runtime does not reopen every unchanged session file.
Session files are still authoritative; deleting the derived cache only causes
summaries to be rebuilt.

The service enumerates session filenames and attributes first. It then resolves
new or changed sessions from newest to oldest. Full resolution waits for up to
10 seconds by default. If files remain unresolved, the response still contains
every discovered session: complete summaries appear first and unresolved
sessions use empty preview and metadata values with the standard fallback
title. Resolution continues inside the server for later list requests.

This behavior can be tuned through the current implementation's own
application section:

```json
{
  "application": {
    "cached_background_session_list": {
      "foreground_timeout_seconds": 10.0,
      "worker_count": 1,
      "persistent_cache_enabled": true,
      "local_cache_directory": "~/.crystal/cache/session-list"
    }
  }
}
```

- `foreground_timeout_seconds` is a non-negative finite number. `0` returns
  cached and metadata-only summaries without waiting for content resolution.
- `worker_count` is an integer from 1 through 8.
- `persistent_cache_enabled` disables cross-runtime reuse when set to `false`;
  background resolution remains active.
- `local_cache_directory` overrides the directory for private derived summary
  databases.

These settings belong to the current local implementation. Other
session-list-service implementations may ignore them or use different
settings.

By default, the cache is under `~/.crystal/cache/session-list`. When session
files are inside an on-demand cloud folder, keep
`local_cache_directory` outside that folder so the derived summaries remain
locally available.

## Diagnostics

Configuration errors are available programmatically:

```python
from agent_app import AgentApplication

app = AgentApplication("config.json", "./sessions")
for error in app.get_config_errors():
    print(error.get("type"), error.get("path"), error.get("detail"))
```

Invalid plugin package, mixin, merge-policy, and variant configuration prevents
application startup. Missing placeholder values are reported separately.

## See also

- [Plugin system overview](../../../plugins/docs/overview.md)
- [Packaging and loading plugins](../../../plugins/docs/plugin-packaging-and-loading.md)
- [Package quickstart](quickstart.md)