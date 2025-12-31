# agent-terminal-app

Minimal example application that combines the core SDK's
`AgentApplication` API with:

- a FastAPI-based JSON API for sessions and requests
- a `prompt_toolkit`-based terminal client with multiline input,
  slash commands, and keyboard shortcuts

The API and terminal share an in-memory event store so that multiple
frontends can observe the same session's events (including streaming
assistant messages) when they run in the same process.

## Installation

From the repository root:

```bash
# 1. Install the core SDK (provides agent_core, agent_app, plugins)
cd core/python
pip install -e ".[dev]"

# 2. Install the terminal application package
cd ../../application/python
pip install -e .
```

Python 3.10+ is required.

## Running the API server

From `application/python`:

```bash
python -m agent_terminal_app
```

This starts a FastAPI app (via uvicorn) on `http://127.0.0.1:8000` by
default. The main routes are:

- `POST /sessions` – create a new session
- `POST /sessions/{session_id}/messages` – append a message
- `POST /sessions/{session_id}/send` – start the model/tool loop in the background
- `GET /events` – list events from the shared in-memory event store

You can change host and port:

```bash
python -m agent_terminal_app --host 0.0.0.0 --port 9000
```

## Enabling Bonjour (mDNS) and the bridge service

The API server can optionally:

- advertise itself on the local network via **Bonjour/mDNS** so that
  compatible clients (like the React Native demo app) can discover it
  automatically, and
- connect to the **Elixir bridge service** so that mobile/desktop
  clients can reach the server via a WebSocket bridge with a pairing
  flow.

These integrations are configured via command‑line flags when starting
the app with ``python -m agent_terminal_app``. Under the hood the
flags are converted to environment variables (``ENABLE_BONJOUR``,
``BRIDGE_URL``, etc.) that the FastAPI app reads on startup.

### Simplest Bonjour command

From ``application/python``:

```bash
python -m agent_terminal_app \
  --host 0.0.0.0 \
  --port 9000 \
  --enable-bonjour
``

This will:

- start the HTTP API on ``http://0.0.0.0:9000``, and
- advertise a ``_http._tcp`` Bonjour service named
  ``"Agent Terminal App"`` on port ``9000``.

You normally do **not** need to override the Bonjour options. For
completeness, the most useful flags are:

- ``--enable-bonjour`` – turn Bonjour advertising on.
- ``--bonjour-port`` – explicit port to advertise; by default the
  server port (``--port``) is used.
- ``--bonjour-service-name`` – human‑readable instance name shown in
  Bonjour browsers (default: ``"Agent Terminal App"``).

Internally these map to:

- ``ENABLE_BONJOUR=1``
- ``BONJOUR_PORT=<value>`` (if provided)
- ``BONJOUR_SERVICE_NAME=<value>`` (if provided)

### Verify

```bash
dns-sd -B _http._tcp .
```

### Simplest bridge command

To enable the bridge client, you need a running Elixir bridge
instance (for example, from the ``bridge-elixir`` directory in the
repository) exposing a WebSocket endpoint such as
``ws://localhost:4000/ws/websocket``.

The minimal command is:

```bash
python -m agent_terminal_app \
  --host 0.0.0.0 \
  --port 9000 \
  --bridge-url ws://localhost:4000/ws/websocket
``

This will:

- start the HTTP API on ``http://0.0.0.0:9000``, and
- connect to the bridge as a "server" client, registering this
  process so that mobile/desktop clients can discover and pair with it.

When the bridge is enabled, the server prints human‑facing messages to
stdout, including a banner with the 6‑digit pairing code and, once
paired, the bridge session id. This makes it easy to complete the
pairing flow from the React Native demo app.

The most useful bridge options are:

- ``--bridge-url`` – **required** to enable the bridge; WebSocket URL
  of the Elixir bridge, for example
  ``ws://localhost:4000/ws/websocket``.
- ``--bridge-display-name`` – optional human‑friendly name shown in
  bridge clients (defaults to ``"Agent Terminal App"``).
- ``--bridge-location`` – optional free‑text location string (for
  example, ``"Office"``); purely informational.
- ``--bridge-local-http-base`` – optional explicit base URL for the
  local HTTP server as seen from the bridge (default:
  ``http://<SERVER_HOST>:<SERVER_PORT>`` derived from the ``--host``
  and ``--port`` flags).

Under the hood these map to the following environment variables:

- ``BRIDGE_URL``
- ``BRIDGE_DISPLAY_NAME`` (if provided)
- ``BRIDGE_LOCATION`` (if provided)
- ``BRIDGE_LOCAL_HTTP_BASE`` (if provided)
- ``BRIDGE_SERVER_ID`` (if you supply ``--bridge-server-id``)

### Bonjour + bridge together

You can enable both integrations at the same time:

```bash
python -m agent_terminal_app \
  --host 0.0.0.0 \
  --port 9000 \
  --enable-bonjour \
  --bridge-url ws://localhost:4000/ws/websocket \
  --bridge-display-name "My Agent Server" \
  --bridge-location "Office"
``

In this mode:

- LAN clients can discover the server via Bonjour and talk to it
  directly over HTTP.
- Remote clients can connect to the same server via the Elixir bridge
  using the pairing flow.

## Running the terminal client

To run only the terminal client (no HTTP server in this process):

```bash
python -m agent_terminal_app --console
```

Features:

- multiline input (press Enter to add lines, Ctrl-D / Ctrl-C to exit)
- slash commands:
  - `/help` – list commands and shortcuts
  - `/new` – start a new session
  - `/exit` or `/quit` – exit the client
- keyboard shortcuts:
  - `Ctrl-N` – start a new session
  - `Ctrl-Q` – exit the client

Messages and events are printed to stdout; the terminal's own
scrollback acts as the message history.

## Running server and terminal together

You can run both the API server and the terminal client in a single
process. The server runs in a background thread while the console runs
in the foreground, sharing the same `AgentApplication` instance and
in-memory event store:

```bash
python -m agent_terminal_app --server --console
```

In this mode, any requests sent through the HTTP API (for the same
session) will produce events that also appear in the terminal, and vice
versa.

## Logging

By default, all output goes to stdout and the log level for the
terminal application starts at `WARNING`.

You can mirror logs to a separate file using `--log-file`:

```bash
# Server only, with logs mirrored to app.log
python -m agent_terminal_app --log-file app.log

# Console only, with logs mirrored to console.log
python -m agent_terminal_app --console --log-file console.log

# Server + console, with all logs mirrored to combined.log
python -m agent_terminal_app --server --console --log-file combined.log
```

The `--log-file` option adds a file handler to Python's root logger, so
uvicorn and the terminal client logs are written both to stdout and to
the given file.

You can also control the log level for both the terminal application
and the core SDK using `--log-level` (overriding any `LOG_LEVEL`
environment variable):

```bash
python -m agent_terminal_app --log-level DEBUG
python -m agent_terminal_app --console --log-level INFO
```

## Command-line options

You can inspect all available flags with:

```bash
python -m agent_terminal_app --help
```

Common options:

- `--server` – run the HTTP API server (default when no flags given)
- `--console` – run the interactive terminal client
- `--host` / `--port` – bind address and port for the server
- `--config` – path to a JSON config file
- `--config-local` – force use of `./.crystal/config.json`, creating a
  default if missing
- `--sessions-dir` – directory for session files (default:
  `./.crystal/sessions`)
- `--app-name` – name to set as the terminal window title
- `--log-file` – mirror logs to a file while keeping stdout output
- `--log-level` – set log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`)

## Plugins

The terminal client exposes per-session plugin control via `/plugins`.

- `/plugins` – list all known plugins for the active session, including
  whether they are enabled, their kind (provider/extension/feature/tool),
  and a stable plugin id.
- `/plugins on <id-or-index>` – enable a plugin for this session using
  either its id (e.g. `delay_extension`) or the 1-based index from the
  last `/plugins` listing.
- `/plugins off <id-or-index>` – disable a plugin for this session.
- `/plugins reset` – clear any session-specific overrides and revert to
  the agent's default plugin configuration (or "all enabled" if no
  defaults are configured).

Changes are stored on the session (in `session.metadata["plugins"]`), so
subsequent requests and reloads use the updated plugin set.

Many plugins also expose configuration and display metadata via
`get_ui_elements()`:

- Elements with `ui_type == "config"` (or with no `ui_type`, which
  defaults to `"config"`) describe editable settings. The `/set`
  command and its completions are driven by these entries.
- Elements with `ui_type == "message_footer"` describe per-message
  footer fields (for example, timestamps or cached-token counters).
  The terminal renders them under each message when present.
- Elements with `ui_type == "status_bar"` describe status bar fields
  derived from the last assistant message (for example, cumulative
  usage cost). These are shown in the bottom status bar next to the
  agent and session id.

Built-in examples include:

- `TimestampExtension` (feature): adds a `metadata.timestamp` field and
  a `message_footer` UI element so timestamps appear in message footers.
- `OpenRouterUsageExtension` (provider extension): adds
  `message_footer` elements for per-message token/cost info and a
  `status_bar` element for cumulative cost.

## Listing messages

The `/list` slash command shows recent messages with a compact view of
content, thinking, and tool usage for each entry:

- `[index] role` – zero-based message index and role.
- `content:` (or `result:` for `tool` messages) – the message text.
- `thinking:` – reasoning attached by reasoning-capable providers or
  extensions (from `metadata["reasoning"]` or `metadata["thinking_blocks"]`).
- `tools:` – a summary of tool calls attached to assistant messages,
  counting calls and listing function names from `metadata["tool_calls"]`.
- `tool_call_id:` – the id of the tool call for `tool` messages when
  `metadata["tool_call_id"]` is present.

This is the same formatting exercised by
`test_list_slash_command_shows_thinking_and_tools` in
`application/python/tests/test_terminal_application.py`.
