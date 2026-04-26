# AI Agent Platform

A functional, plugin‑based agent framework for building conversational applications on top of arbitrary LLM providers (OpenRouter, OpenAI‑compatible, Ollama, echo, etc.) with tools, streaming, and a terminal + HTTP app.

- **Functional core SDK (`agent_core`)** – immutable sessions/messages, stateless pipeline, provider/tool orchestration.
- **Application layer (`agent_app`)** – config loading, sessions, events, tool loop, cancellation.
- **Terminal + HTTP + mobile integration app (`agent_terminal_app`)** – FastAPI JSON API, prompt_toolkit terminal client, and glue so mobile apps can connect via direct HTTP, Bonjour/mDNS discovery, or a bridge service.
- **Mobile app (`mobile/crystal-lattice-control-rn`)** – React Native client (Crystal Lattice Control) that connects to the terminal/HTTP app directly or via the bridge and provides a sessions/messages UI on phones and simulators.
- **Plugin system** – built-in plugins in `core/python/plugins` plus optional plugin repos under `plugins/` (providers, extensions, features, tools).
- **Bridge service (`bridge-elixir`)** – Elixir/Phoenix WebSocket bridge that lets mobile/desktop apps talk to local HTTP servers across networks using pairing + proxied HTTP requests.

This README is for first‑time users and contributors who want to either *try the platform quickly* or *start extending it*.

---

## Quick Start

### Prerequisites

- Python **3.10+**
- Recommended: a virtualenv

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows
```

### 1. Install the CLI

For a published Python install, use:

```bash
pipx install crystal-lattice-cli
crystal-lattice --help
```

From a local checkout, install the editable packages from the repository root:

```bash
# Core SDK + plugins
cd core/python
pip install -e ".[dev]"

# Terminal app
cd ../../application/python
pip install -e .
```

---

## First Run: Echo Provider (No API Keys)

The simplest way to try the platform is with the built‑in echo provider – no network calls or keys required.

### Core SDK + Echo provider

Create a file `echo_demo.py`:

```python
from agent_core import AgentCore
from plugins.echo_openai_like_provider import EchoOpenAILikeProvider

core = AgentCore()
core.register_provider(EchoOpenAILikeProvider)

session = core.create_session()
session = core.add_message(session, "user", "Hello from the echo provider!")

config = {
    "provider": "echo_openai_like",
    "model": "echo-test-1",
    "timeout": 60,
}

session, replies = core.send_request(session, config)
print(replies[-1]["content"])
```

Run it (from anywhere inside the virtualenv):

```bash
python echo_demo.py
```

You should see an echo of your last user message.

### Terminal app with Echo config

The terminal app ships with an echo-based config file:

- `application/python/agent_terminal_app/config_echo_app.json`

From the repo root:

```bash
cd application/python
mkdir -p .crystal
cp agent_terminal_app/config_echo_app.json .crystal/config.json
crystal-lattice --console
```

You now have an interactive terminal client:

- Type messages and press Enter to send
- Use `/help` for commands
- Use `/new` to start a new session
- Use `/exit` or `Ctrl-Q` to quit

This mode uses the echo provider only - no API keys or external services.

The terminal also respects several *application-level* settings under the
top-level "application" key in the config file. For example, you can
control how tool outputs are printed in the UI by editing
`application/python/agent_terminal_app/config_echo_app.json`:

```json
{
  "application": {
    "tool_output_line_limit": 100,
    "tool_output_char_limit": 8000,
    "tool_output_short_char_limit": 200,
    "tool_output_short_one_line": true,
    "tool_output_short_line_limit": 20
  },
  ...
}
```

- `tool_output_line_limit` / `tool_output_char_limit` limit how many lines
  and characters of tool output are shown in the terminal (agents still get
  the full content).
- `tool_output_short_*` control the compact "short" view used by
  `/list short ...`.

---

## Using Real Models (OpenRouter / OpenAI‑Compatible)

Once you’re comfortable with the echo flow, you can point the platform at real providers.

### OpenAI‑compatible provider (e.g. OpenAI, Ollama)

```python
from agent_core import AgentCore
from plugins.openai_provider import OpenAICompatibleProvider

core = AgentCore()
core.register_provider(OpenAICompatibleProvider)

config = {
    "provider": "openai_compatible",
    "model": "gpt-4o",                       # or an Ollama model like "llama3.2:1b"
    "base_url": "https://api.openai.com/v1",  # or your Ollama endpoint
    "api_key": "sk-...",                     # omit for local Ollama
}

session = core.create_session()
session = core.add_message(session, "system", "You are a helpful assistant.")
session = core.add_message(session, "user", "What is 2+2?")

session, finals = core.send_request(session, config)
print(finals[-1]["content"])
```

### OpenRouter provider

Install the OpenRouter plugin bundle (from the repo root):

```bash
python -m pip install -e plugins/openrouter
```

```python
from agent_core import AgentCore
from openrouter_plugins.openrouter_provider import OpenRouterProvider

core = AgentCore()
core.register_provider(OpenRouterProvider)

config = {
    "provider": "openrouter",
    "model": "openai/gpt-5-mini",  # or another supported model id
    "api_key": "...OPENROUTER_API_KEY...",
}

session = core.create_session()
session = core.add_message(session, "user", "Explain functional programming in one sentence.")

session, finals = core.send_request(session, config)
print(finals[-1]["content"])
```

### Terminal app with OpenRouter config

The terminal app includes an OpenRouter‑based configuration:

- `application/python/agent_terminal_app/config_openrouter_app_layer.json`

From the repo root:

```bash
cd application/python
export OPENROUTER_API_KEY=...  # or set in a .env file
crystal-lattice --console \
  --config agent_terminal_app/config_openrouter_app_layer.json
```

Key features in the terminal:

- `/send` – send a request with current history (also `Ctrl-X S`)
- `/append` – add a message without sending
- `/delete`, `/modify`, `/list` – manage message history (indices and ranges)
- `/agent` – switch between configured agents
- `/plugins` – list/enable/disable providers, extensions, features, tools per session
- `/set` – adjust config overrides (e.g. reasoning settings) via UI schema

---

## Architecture Overview

The platform is organized into three layers plus plugins:

1. **Core SDK – `core/python/agent_core`**
   - `core.py` – `AgentCore`, a stateless processing pipeline that manages:
     - Immutable `Session` and `Message` flows
     - Provider/extension/feature/tool registration
     - Requests: `send_request`, `send_request_stream`, `send_request_stream_async`
     - Session editing: `slice_session`, `fork_session`, `modify_message`
     - Provider‑native history retention (`native_messages`) and integrity checking
     - Tools: `get_tool_schemas`, `iter_tool_messages`, `execute_tool_calls`, `stream_tool_call`
   - `types.py` – dataclasses and plugin protocols (`ProviderPlugin`, `ProviderExtensionPlugin`, `FeaturePlugin`, `ToolPlugin`).
   - `plugin/` – wrappers and default adapters for providers, extensions, features, tools.
   - `utils.py` – functional pipeline helper and structured logging (`structlog`).

2. **Application layer – `core/python/agent_app`**
   - `application_future.py` (`AgentApplication`):
     - Loads and resolves JSON config with `${env:...}` and `${file:...}` placeholders.
     - Discovers plugin classes from string paths in config.
     - Builds per‑agent plugin sets (providers, extensions, features, tools).
     - Manages sessions via `FilesystemSessionStore` (JSON on disk).
     - Manages events via `InMemoryEventStore` (used by server + terminal).
     - Exposes a *core‑first* request API: `send_request(core, session, base_config, overrides, stream)` yielding events.
   - `tool_loop.py` (`ToolLoopRunner`):
     - Drives the LLM + tools loop on top of `AgentCore.send_request*` and `iter_tool_messages`.
     - Emits `request_started`, `partial`, `final`, `tool_calls`, `tool_partial`, `tool_results`, `request_completed`, `error` events.
     - Additionally yields internal `session_checkpoint` events with live `Session` objects so applications can persist progress incrementally without embedding full sessions in external events.
     - Supports cooperative cancellation via `AgentApplication.cancel_request()`.

3. **Terminal & HTTP app – `application/python/agent_terminal_app`**
   - `server.py` – FastAPI app with routes:
     - `POST /sessions` – create a session (optionally with `system_message`).
     - `POST /sessions/{session_id}/messages` – append a message.
     - `POST /sessions/{session_id}/send` – run request + tool loop and publish events.
     - `GET /events` – poll events by `session_id` / `request_id`.
      - `GET/PUT /api/data`, `GET /api/hello` – simple demo endpoints used by the React Native mobile example.
   - `terminal_app.py` (`TerminalApplication`):
     - Owns an `AgentApplication` and an active `Session`.
     - Session lifecycle: create, switch, list, delete.
     - Message ops: append, delete (by indices or ranges), modify, list.
     - Agents: `current_agent_id`, `available_agents`, `switch_agent`.
     - Plugins: per‑session plugin enable/disable, reset to agent defaults.
     - Overrides: `update_override(key, value)` stored in `session.metadata["overrides"]`.
     - Requests: `send_request(stream=True/False)` and event polling APIs.
   - `terminal.py`:
     - prompt_toolkit UI with:
       - Slash commands: `/help`, `/agent`, `/session`, `/send`, `/append`, `/delete`, `/modify`, `/list`, `/set`, `/plugins`, `/cancel`, `/new`, `/exit`.
       - Shortcuts: `Ctrl-N` (new session), `Ctrl-Q` (exit), `Ctrl-X S` (send), `Ctrl-X A` (append), `Ctrl-X C` (cancel active request).
       - Autocomplete for agents, sessions, plugins, and `/set` keys.
   - `event_rendering.py`:
     - Separate renderers for reasoning (`metadata.reasoning`), assistant content, streaming tool output, and request headers/footers.

   Together, the HTTP server and terminal app form the main user-facing application. They also provide the attachment points for **mobile connectivity**:

   - **Direct HTTP** – mobile apps can call `/api/data` and `/sessions/...` directly by host + port.
   - **Bonjour/mDNS** – `bonjour.py` advertises the HTTP server on the local network so compatible clients can discover it automatically.
   - **Bridge service** – `bridge_client.py` connects to the Elixir bridge (`bridge-elixir`) so mobile apps can pair with and talk to this server across networks via `http_request` messages.

4. **Plugins**
   - Built-in plugins (installed with `agent-core`):
     - `core/python/plugins` (Python package `plugins.*`)
   - Optional plugin bundles (installed separately or loaded via `path:` in app config):
     - `plugins/openrouter` (Python package `openrouter_plugins.*`) – OpenRouter provider + extensions (tools, reasoning, web search, usage, verbosity).

For a deeper architectural description and diagrams, see `ARCHITECTURE.md`.

For directory-specific guidelines on the terminal/server/mobile integration layer, see:

- `application/python/agent_terminal_app/AGENTS.md`
- `application/python/agent_terminal_app/README.md`

---

## Mobile & Bridge Integration

The platform includes a reference mobile integration that connects a React Native
app to a locally running Python server, both on the same LAN and across
networks.

High-level flow:

- **Direct HTTP** – mobile app talks directly to the FastAPI server
  (`agent_terminal_app.server`) via host + port.
- **Bonjour/mDNS** – the server advertises an `_http._tcp` service via
  `bonjour.py`, and the mobile app discovers it automatically on the local
  network.
- **Bridge service** – the Python server connects as a "server" client to the
  Elixir bridge (`bridge-elixir`) using `bridge_client.py`. The mobile app
  connects as an "app" client, pairs using a 6‑digit code, and sends
  `http_request` messages that the bridge proxies to the local FastAPI server.

Rough topology with bridge + TLS in front:

```text
React Native app
     │
     ▼
  Nginx / LB (TLS termination, e.g. wss://bridge.example.com)
     │
     ▼
  bridge-elixir (Phoenix + libcluster, /ws/websocket)
     │
     ▼
Python HTTP server (agent_terminal_app.server, http://host:port)
```

Key directories and docs:

- `application/python/agent_terminal_app` – FastAPI server, terminal client,
  Bonjour + bridge integration.
- `mobile/crystal-lattice-control-rn` – React Native app (Crystal Lattice Control) that talks to the terminal/HTTP app via direct HTTP, Bonjour discovery, or the bridge; see its `README.md` and `AGENTS.md`.
- `bridge-elixir` – Elixir/Phoenix bridge service and Docker/HAProxy configs.
- `bridge-elixir/PRODUCTION_DEPLOYMENT.md` – single-node and clustered bridge
  deployment guides (with optional TLS in Nginx/HAProxy).
- `bridge-elixir/README.md` / `bridge-elixir/AGENTS.md` – bridge architecture
  and contributor notes.

### React Native example app (Crystal Lattice Control)

The repository includes a React Native app that exercises the mobile
connectivity paths in a real UI.

From the repo root:

```bash
cd mobile/crystal-lattice-control-rn
npm install           # or: npm ci

# Start Metro bundler
npm run start

# In a separate terminal: run on iOS simulator
npm run ios

# Or on Android emulator / device
npm run android
```

The app expects the Python terminal/HTTP server to be running and reachable
from the device or simulator. You can connect in three ways from the app:

- **Manual** – enter host and port of the FastAPI server.
- **Discovery** – use Bonjour/mDNS to find the advertised `_http._tcp` service.
- **Bridge** – enter the WebSocket URL for the Elixir bridge (e.g.
  `ws://bridge-host:4000/ws/websocket`), select a server, and pair using the
  6‑digit code shown in the server logs.

Once connected, the app shows:

- A **Connection** tab – server name, `/api/hello` health check, disconnect.
- A **Sessions** tab – list/create sessions backed by `/sessions`.
- A **Messages** tab – per-session chat view using `/sessions/{id}/messages`
  and `/sessions/{id}/send`, with role-specific message styling and
  collapsible tool results and reasoning.

---

## Repository Layout

Common entry points and directories:

- `core/python/agent_core` – core SDK (`core.py`, `types.py`, `plugin/`, `utils.py`).
- `core/python/agent_app` – application layer (`application_future.py`, `tool_loop.py`, `sessions.py`, `events.py`, `config.py`).
- `core/python/plugins` – built‑in providers, extensions, features, tools.
- `core/python/examples` – runnable examples; also used to generate `EXAMPLES.md`.
- `core/python/tests` – tests for core, app layer, and plugins.
- `application/python/agent_terminal_app` – terminal + HTTP + mobile integration app; see its `README.md` and `AGENTS.md` for details.
- `application/python/tests` – tests for server + terminal behavior.
- `mobile/crystal-lattice-control-rn` – React Native app (Crystal Lattice Control); see its `README.md` and `AGENTS.md`.
- `bridge-elixir` – Elixir/Phoenix bridge service used for cross‑network mobile connectivity; see `bridge-elixir/README.md`, `bridge-elixir/PRODUCTION_DEPLOYMENT.md`, and `bridge-elixir/AGENTS.md`.
- `docs/` – MkDocs configuration and reference docs.
- Root docs: `ARCHITECTURE.md`, `DEVELOPMENT.md`, `EXAMPLES.md`, `TYPES_AND_PROTOCOLS.md`, `PROJECT_PLAN.md`.

---

## Using the Core SDK in Your Own Project

### Basic synchronous chat

```python
from agent_core import AgentCore
from plugins.openai_provider import OpenAICompatibleProvider

core = AgentCore()
core.register_provider(OpenAICompatibleProvider)

config = {
    "provider": "openai_compatible",
    "model": "gpt-4o",
    "base_url": "https://api.openai.com/v1",
    "api_key": "sk-...",
}

session = core.create_session()
session = core.add_message(session, "system", "You are a helpful assistant.")
session = core.add_message(session, "user", "What is 2+2?")

session, finals = core.send_request(session, config)
print(finals[-1]["content"])
```

### Streaming

```python
for chunk in core.send_request_stream(session, config):
    if chunk["type"] == "partial":
        print(chunk["message"]["content"], end="", flush=True)
    elif chunk["type"] == "final":
        session = chunk["session"]
        print("\n[Done]")
```

### Tools (FileReaderTool example)

```python
from plugins.file_reader_tool import FileReaderTool

core.register_tool(FileReaderTool)

config = {
    "provider": "openai_compatible",
    "model": "gpt-4o",
    "base_url": "https://api.openai.com/v1",
    "api_key": "sk-...",
    "allowed_paths": ["."],
    "max_file_size": 1024 * 1024,
    "working_directory": ".",
}

# After an assistant response with tool_calls:
last = finals[-1]
tool_calls = last.get("metadata", {}).get("tool_calls", [])

if tool_calls:
    tool_messages = core.execute_tool_calls(tool_calls, config)
    for tm in tool_messages:
        session = core.add_message(
            session,
            tm.get("role", "tool"),
            tm.get("content", ""),
            tm.get("metadata"),
            config=config,
        )
```

---

## Examples & Recipes

Examples live under `core/python/examples` and are documented in `EXAMPLES.md`. Highlights:

- **Echo provider** – `example1_echo_provider.py`
- **Prefix extension** – `example2_prefix_extension.py`
- **Web search feature** – `example3_web_search_feature.py`
- **FileReaderTool** – `example4_file_reader_tool.py`
- **Project plan series (Examples 5–9)** – low‑level and streaming APIs, tool loops, history manipulation, config updates.
- **Minimal FastAPI/JSON app** – `example10_project_plan_app.py`
- **OpenAI tools on Ollama** – `example11_openai_tools_file_reader.py`
- **Core‑first app layer** – `example13_openrouter_tools_app_layer.py`

Run example tests to ensure they’re working:

```bash
pytest core/python/examples/tests -qs
```

---

## Development Setup (For Contributors)

### Environment

- Python **3.10+**
- Virtualenv highly recommended

### Install for development

```bash
# From repo root
cd core/python
pip install -e ".[dev]"

cd ../../application/python
pip install -e .
```

### Run tests

```bash
# Core SDK + plugins
pytest core/python/tests -q

# Examples (treated as executable docs)
pytest core/python/examples/tests -qs

# Terminal app
pytest application/python/tests -q

# Optional: OpenRouter plugin bundle tests
python -m pip install -e "plugins/openrouter[dev]"
pytest plugins/openrouter/tests -q
```

Markers:

- `-m openrouter` – tests that require OpenRouter (require `OPENROUTER_API_KEY`)
- `-m integration` – all integration tests
- `-m ollama` – tests that hit a local Ollama instance

### Lint, format, typecheck (from repo root)

```bash
ruff check core/python/agent_core core/python/tests core/python/examples core/python/plugins
black core/python/agent_core core/python/tests core/python/examples core/python/plugins
pyright
```

For contributor guidance, see `AGENTS.md` and `DEVELOPMENT.md`.

---

## Extending the Platform (Plugins)

Plugins are plain Python classes implementing the protocols in `agent_core.types`.

- **Providers** (`ProviderPlugin`) – integrate LLM APIs.
- **Provider extensions** (`ProviderExtensionPlugin`) – hot‑path streaming observers/enrichers (reasoning, tools, caching).
- **Features** (`FeaturePlugin`) – cold‑path per‑turn behavior (system prompts, request options, etc.).
- **Tools** (`ToolPlugin`) – callables such as file operations, shell, math, apply‑patch, with optional streaming (`stream_tool`) and display payloads.

Useful entry points:

- `docs/plugins/development.md` – plugin development guide.
- `plugins/docs/provider-plugins.md` – canonical provider plugin authoring guide.
- `docs/reference/agent_core/types.md` – plugin protocol reference.
- Example plugins under `core/python/examples`.

---

## Documentation

### MkDocs site

To browse the API and reference docs locally:

```bash
pip install -r docs/requirements.txt
mkdocs serve
```

Key docs:

- `docs/api/core-sdk.md` – core SDK user‑facing guide
- `docs/reference/agent_core/*` – generated API reference
- `EXAMPLES.md` – example catalogue

When changing examples, run:

```bash
pytest core/python/examples/tests -qs
python scripts/generate_examples_md.py
```

---

## Status, Version, License

- Core package: **`agent-core` 0.3.0**
- Terminal CLI package: **`crystal-lattice-cli` 0.1.0** (`crystal-lattice` command)
- License: **MIT**

See `core/python/pyproject.toml`, `application/python/pyproject.toml`, and the source files for the most up‑to‑date behavior.
