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

## Credentials and startup

The CLI can create and start the default config without provider API keys.
Missing credentials do not prevent the server, terminal, local configuration,
or agent listing from starting.

Put keys for API-backed providers and tools in a `.env` file rather than
exporting them before every launch. For a project-local config:

```bash
# .crystal/.env
OPENAI_API_KEY=...
OPENROUTER_API_KEY=...
ANTHROPIC_API_KEY=...
```

The CLI reads these values for config resolution without adding them to the
process environment. A request to a credentialed API still requires the real
key for that provider or tool. See
[configuration placeholders](configuration-placeholders.md#env-files) for
the complete lookup order and precedence.

## Bridge runtime settings

Bridge registration is explicitly enabled with `--enable-bridge` or
`--bridge-url`. `application.bridge_url` supplies a reusable URL but does not
enable registration by itself. URL precedence is:

1. `--bridge-url`;
2. `.crystal/profile.json`;
3. `~/.crystal/projects.json`;
4. `application.bridge_url`.

Advanced bridge-client transport settings live under `application.bridge`:

```json
{
  "application": {
    "bridge_url": "wss://bridge.example/ws/websocket",
    "bridge": {
      "ws_max_size_bytes": 16777216,
      "http_timeout_seconds": 120.0,
      "http_chunk_size_bytes": 921600,
      "http_chunk_threshold_bytes": 262144,
      "http_max_body_bytes": 10485760,
      "debug": false
    }
  }
}
```

| Key | Type | Default | Meaning |
| --- | --- | --- | --- |
| `ws_max_size_bytes` | positive integer or `null` | `16777216` (16 MiB) | Maximum WebSocket message accepted by the Python bridge client. `null` disables the WebSocket library's message-size limit. |
| `http_timeout_seconds` | positive finite number | `120.0` | Timeout used by bridge HTTP download/upload operations. |
| `http_chunk_size_bytes` | positive integer | `921600` (900 KiB) | Payload target for legacy chunked bridge responses, with protocol-envelope headroom applied by the adapter. |
| `http_chunk_threshold_bytes` | positive integer | `262144` (256 KiB) | Response size above which the legacy adapter uses chunked response events. |
| `http_max_body_bytes` | positive integer | `10485760` (10 MiB) | Maximum request body buffered by the Python legacy bridge adapter. |
| `debug` | boolean | `false` | Enables bridge-client debug output. |

Wrong JSON types, zero or negative sizes/timeouts, and non-finite timeouts stop
server startup with a field-specific error. These settings are read when the
process starts. Application reload does not reconnect the bridge or restart
Bonjour, so changing them requires restarting Crystal Lattice.

Bridge and Bonjour do not implicitly read specially named environment
variables. Use the documented CLI/profile/application settings. Embedders that
run `agent_terminal_app.server:app` directly configure
`ServerIntegrationRuntimeConfig` before FastAPI startup.

The ordinary [placeholder system](configuration-placeholders.md) remains
available when a configuration author deliberately places a placeholder in
one of these fields; that is explicit configuration, not an automatic bridge
environment contract.

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
application startup. An unresolved environment placeholder is reported
separately as an `env_missing` warning, and that warning is not itself fatal.
The empty resolved value can still cause an independent fatal validation error
when it is used in a structural setting such as a plugin path. Optional
credential placeholders in the generated default config do not prevent
startup; the selected API-backed functionality still needs its configured
credentials.

## See also

- [Plugin system overview](../../../plugins/docs/overview.md)
- [Packaging and loading plugins](../../../plugins/docs/plugin-packaging-and-loading.md)
- [Package quickstart](quickstart.md)
