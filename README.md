# AI Agent Platform

A functional, plugin‑based agent framework for building conversational applications on top of arbitrary LLM providers (OpenRouter, OpenAI‑compatible, Ollama, echo, etc.) with tools, streaming, and a terminal + HTTP app.

- **Functional core SDK (`agent_core`)** – immutable sessions/messages, stateless pipeline, provider/tool orchestration.
- **Application layer (`agent_app`)** – config loading, sessions, events, tool loop, cancellation.
- **Terminal + HTTP app (`agent_terminal_app`)** – FastAPI JSON API and prompt_toolkit terminal client.
- **Plugin system (`core/python/plugins`)** – providers, reasoning/thinking extensions, features, and tools.

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

### 1. Install from source

From the repository root:

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

The terminal app ships with an echo‑based config file:

- `application/python/agent_terminal_app/config_echo_app.json`

From the repo root:

```bash
cd application/python
mkdir -p .crystal
cp agent_terminal_app/config_echo_app.json .crystal/config.json
python -m agent_terminal_app --console
```

You now have an interactive terminal client:

- Type messages and press Enter to send
- Use `/help` for commands
- Use `/new` to start a new session
- Use `/exit` or `Ctrl-Q` to quit

This mode uses the echo provider only – no API keys or external services.

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

```python
from agent_core import AgentCore
from plugins.openrouter_provider import OpenRouterProvider

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
python -m agent_terminal_app --console \
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
     - Supports cooperative cancellation via `AgentApplication.cancel_request()`.

3. **Terminal & HTTP app – `application/python/agent_terminal_app`**
   - `server.py` – FastAPI app with routes:
     - `POST /sessions` – create a session (optionally with `system_message`).
     - `POST /sessions/{session_id}/messages` – append a message.
     - `POST /sessions/{session_id}/send` – run request + tool loop and publish events.
     - `GET /events` – poll events by `session_id` / `request_id`.
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

4. **Plugins – `core/python/plugins`**
   - Providers:
     - `openai_provider.OpenAICompatibleProvider` – OpenAI / OpenAI‑compatible / Ollama endpoints.
     - `openrouter_provider.OpenRouterProvider` – OpenRouter API.
     - `echo_openai_like_provider.EchoOpenAILikeProvider` – local echo provider for tests and examples.
   - Provider extensions:
     - `openrouter_reasoning_extension.OpenRouterReasoningExtension` – reasoning support on OpenRouter.
     - `openrouter_tools_extension.OpenRouterToolsExtension` – OpenRouter tool‑calling support.
     - `ollama_thinking_extension.OllamaThinkingExtension` – Ollama thinking blocks.
     - Additional extensions for caching, failure simulation, etc.
   - Features:
     - `system_message_feature.SystemMessageFeature` – templated system message insertion without mutating core history.
     - `request_options_feature.RequestOptionsFeature` – merge arbitrary `request_options` into provider payload.
   - Tools:
     - `file_reader_tool.FileReaderTool` – safe file reading with allowlist + size limit.
     - `shell_tool.ShellTool` – sandboxed shell execution with streaming output.
     - `math_tools.MathTools` – basic calculator tools (add, multiply, square).
     - `apply_patch_tool.ApplyPatchTool` – Codex‑style `*** Begin Patch` / `*** End Patch` file editing.

For a deeper architectural description and diagrams, see `ARCHITECTURE.md`.

---

## Repository Layout

Common entry points and directories:

- `core/python/agent_core` – core SDK (`core.py`, `types.py`, `plugin/`, `utils.py`).
- `core/python/agent_app` – application layer (`application_future.py`, `tool_loop.py`, `sessions.py`, `events.py`, `config.py`).
- `core/python/plugins` – built‑in providers, extensions, features, tools.
- `core/python/examples` – runnable examples; also used to generate `EXAMPLES.md`.
- `core/python/tests` – tests for core, app layer, and plugins.
- `application/python/agent_terminal_app` – terminal + HTTP app.
- `application/python/tests` – tests for server + terminal behavior.
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
```

Markers (core tests):

- `-m openrouter` – OpenRouter integration tests (require `OPENROUTER_API_KEY`)
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
- Terminal app: **`agent-terminal-app` 0.1.0**
- License: **MIT**

See `core/python/pyproject.toml`, `application/python/pyproject.toml`, and the source files for the most up‑to‑date behavior.