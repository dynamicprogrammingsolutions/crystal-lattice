# Provider plugins

This page documents how to build **provider plugins** for the platform.

Provider plugins integrate LLM APIs and convert between:

- **Core messages** (AgentCore’s stable, provider-agnostic format)
- **Provider-native messages** (the wire-format you send to / receive from a provider)

This guide is written to be **runtime-accurate**. When something is ambiguous, treat the runtime code as the source of truth:

- Protocols/docstrings: `core/python/agent_core/types.py`
- Defaulting + normalization: `core/python/agent_core/plugin/adapters.py`
- Provider wrapper orchestration: `core/python/agent_core/plugin/provider.py`
- Core request flow: `core/python/agent_core/core.py`

## Contents

- [Audience & prerequisites](#audience--prerequisites)
- [Concepts & vocabulary](#concepts--vocabulary)
- [Quickstart A: non-streaming provider (package + tests)](#quickstart-a-non-streaming-provider-package--tests)
- [Quickstart B: streaming provider (package + tests)](#quickstart-b-streaming-provider-package--tests)
- [Complete guide: build a full provider](#complete-guide-build-a-full-provider)
- [How requests flow (runtime order)](#how-requests-flow-runtime-order)
- [ProviderPlugin API reference (method-by-method)](#providerplugin-api-reference-method-by-method)
- Deep dives:
  - [State design patterns](#deep-dive-state-design-patterns)
  - [Native history retention](#deep-dive-native-history-retention)
  - [Streaming patterns & recipes](#deep-dive-streaming-patterns--recipes)
  - [Interop: extensions, features, tools](#deep-dive-interop-extensions-features-tools)
  - [Testing provider plugins](#deep-dive-testing-provider-plugins)
  - [Packaging & loading](#deep-dive-packaging--loading)
- [Troubleshooting / FAQ](#troubleshooting--faq)
- [Reference implementations (copy patterns from these)](#reference-implementations-copy-patterns-from-these)

---

## Audience & prerequisites

This doc is for plugin authors implementing:

- a **provider** (`ProviderPlugin`)
- optionally a **provider extension** (`ProviderExtensionPlugin`) to handle hot-path enrichments (tool calls, reasoning extraction, citations, caching metadata)
- optionally a **feature** (`FeaturePlugin`) that affects provider behavior on the cold path (request shaping, system prompt strategies, finalize transformations)

Prereqs:

- You can run Python 3.10+.
- You can run `pytest`.
- You’ve skimmed the AgentCore basics (sessions/messages and `send_request` / `send_request_stream`).

---

## Concepts & vocabulary

### Core messages

Core messages are plain dicts with (at minimum):

```python
{"role": "user"|"assistant"|"system"|"tool", "content": "...", "metadata": {...}}
```

They are stored in `Session.messages` as immutable `Message` objects.

### Provider-native messages

Provider-native messages are plain dicts in the shape your provider expects.

Commonly they are OpenAI-like:

```python
{"role": "user", "content": "Hello"}
```

But they can include provider-specific fields:

```python
{"role": "assistant", "content": "...", "tool_calls": [...], "reasoning": "..."}
```

### Partials vs finals

- **Partial** messages: incremental updates during streaming (shown to the UI as the model “types”).
- **Final** messages: the completed assistant message(s) for the turn.

### Shared provider state (`state: dict`)

Providers, provider extensions, and features share a single per-request state dict (owned by the provider wrapper).

Recommended conventions:

- `state["config"]`: resolved config for this request (flat dict)
- `state["request"]`: provider request info (url/payload/headers/timeout)
- `state["partial"]`: streaming accumulator

### Native history retention (`session.metadata["native_messages"]`)

AgentCore can retain provider-native history across turns and even across `AgentCore` instances.

This is crucial when the core → native conversion is lossy (e.g., provider-specific fields that should persist).

See [Native history retention deep dive](#deep-dive-native-history-retention).

### Preserving metadata: `_metadata`

Core message metadata is not automatically preserved when rebuilding core messages from native history.
If you want metadata to survive rebuild-from-native, write it into provider-native messages under `_metadata` and reconstruct it in `from_native_messages`.

See [Native history retention deep dive](#deep-dive-native-history-retention).

---

## Quickstart A: non-streaming provider (package + tests)

This quickstart creates a provider that works with `AgentCore.send_request`.

It intentionally starts with **packaging + tests first**, because provider plugins are typically loaded as installable repos.

### Step 0 — Create a plugin package (recommended)

Start from the provider template repo:

- Template directory: `plugins/template-python-provider`

Copy it (or fork it) and rename:

- project name in `pyproject.toml`
- Python package under `src/`
- class names and their `name`/`version`
- entries in `agent_plugin.json`

The template includes:

- a deterministic provider
- a provider extension
- a feature
- a small pytest suite inside the package

Packaging details (descriptor-driven plugin repos, `agent_plugin.json`) are covered in:

- [Packaging & loading deep dive](#deep-dive-packaging--loading)

### Step 1 — Implement the provider (minimal)

In your provider class, implement:

- `init(config) -> state`
- **non-streaming** `call_api(native_messages, state)`
- `finalize(native_messages, state)`

Best practice for non-streaming providers in this framework:

- Keep `call_api` focused on I/O and store any “final message to emit” in state
- Emit the final assistant message from `finalize`

This ensures provider extensions get a chance to modify the final assistant message in their own `finalize` hook.

See:

- [call_api](#call_api)
- [finalize](#finalize)
- [Streaming patterns & recipes](#deep-dive-streaming-patterns--recipes) (the accumulator approach generalizes cleanly)

### Step 2 — Wire into AgentCore

Minimal usage:

```python
from agent_core import AgentCore
from my_provider_pkg.provider import MyProvider

core = AgentCore()
core.register_provider(MyProvider)

session = core.create_session()
session = core.add_message(session, "user", "Hello")
session, finals = core.send_request(session, {"model": "..."})
```

### Step 3 — Run tests (in your package)

From repo root:

```bash
python -m pip install -e core/python
python -m pip install -e "plugins/<your-provider-repo>[dev]"
pytest plugins/<your-provider-repo>/tests -q
```

For what to test beyond the minimal suite, see:

- [Testing provider plugins deep dive](#deep-dive-testing-provider-plugins)

---

## Quickstart B: streaming provider (package + tests)

This quickstart implements streaming so you can use `AgentCore.send_request_stream`.

### Step 0 — Create a plugin package (recommended)

Use `plugins/template-python-provider` as the starting point (it already includes streaming skeletons and streaming tests).

### Step 1 — Implement streaming (accumulator pattern)

In your provider implement:

- `stream_api(native_messages, state) -> Iterator[chunk]`
- `process_chunk(native_chunk, native_messages, state) -> (partials, finals, full_history, state)`
- `finalize(native_messages, state) -> (finals, full_history, state)`

Recommended pattern:

- `stream_api` yields raw provider-native chunks
- `process_chunk` extracts a delta and updates `state["partial"]`
- `finalize` emits a single final assistant message (and appends it to native history)

See:

- [Streaming patterns & recipes deep dive](#deep-dive-streaming-patterns--recipes)

### Step 2 — Run a streaming request

```python
for event in core.send_request_stream(session, config):
    if event["type"] == "partial":
        print(event["message"]["content"], end="", flush=True)
    elif event["type"] == "final":
        session = event["session"]
        print("\nDone")
```

### Step 3 — Run tests (in your package)

Your package test suite should include:

- partial events are produced
- final message is produced and matches the accumulated content
- native history is coherent (no per-chunk artifacts persisted)

See:

- [Testing deep dive](#deep-dive-testing-provider-plugins)
- [Native history retention deep dive](#deep-dive-native-history-retention)

---

## Complete guide: build a full provider

This section is a step-by-step guide for building a production-quality provider.
Each step links to deep dives for details.

### Step 0 — Create a provider plugin repo (template)

Start from `plugins/template-python-provider`.

The template includes skeletons for:

- provider (`ProviderPlugin`)
- provider extension (`ProviderExtensionPlugin`)
- feature (`FeaturePlugin`)
- tests (pytest) inside the plugin package

See: [Packaging & loading deep dive](#deep-dive-packaging--loading).

### Step 1 — Identity + configuration schema

Set:

- `name`: stable identifier used in config, UI, and plugin selection
- `version`: semantic version string
- `get_config_schema()`: JSON-schema-like dict used for config UI and validation in apps
- `get_ui_elements()`: optional UI hints for applications

See: [Identity/config UI methods](#identity-config--ui).

### Step 2 — Design state

Recommended state conventions:

- `state["config"]`: the request config dict
- `state["request"]`: url/payload/headers/timeout
- `state["partial"]`: streaming accumulator

See: [State design patterns deep dive](#deep-dive-state-design-patterns).

### Step 3 — Implement conversions (core ↔ native)

Implement (or rely on defaults when appropriate):

- `to_native_messages(messages, state)`
- `from_native_messages(native_messages, state)`

If you want metadata to survive rebuild-from-native, use `_metadata` on native messages.

See:

- [to_native_messages](#to_native_messages)
- [from_native_messages](#from_native_messages)
- [Native history retention deep dive](#deep-dive-native-history-retention)

### Step 4 — Implement `initialize_request`

Use `initialize_request` to build:

- request URL
- headers (be careful with secrets)
- base payload (model, params)
- reset per-turn accumulators

See: [initialize_request](#initialize_request).

### Step 5 — Implement I/O

Choose:

- non-streaming only: `call_api` + `finalize`
- streaming: `stream_api` + `process_chunk` + `finalize`

Even if you support non-streaming, consider emitting the final from `finalize` so extensions can reliably modify finals.

See:

- [call_api](#call_api)
- [stream_api](#stream_api)
- [process_chunk](#process_chunk)
- [finalize](#finalize)

### Step 6 — Make native history retention correct

At the end of a turn, native history is persisted into the session.

Provider rules of thumb:

- Treat `native_messages` as full history (not a delta)
- Append final assistant messages to the returned native history
- Do **not** append raw per-chunk objects into native history

See: [Native history retention deep dive](#deep-dive-native-history-retention).

### Step 7 — Models, tags, and dependency enablement

Implement:

- `get_models(config)` (optional)
- `get_tags(config, models)`

These tags are used to decide which extensions/features/tools are enabled via their `required_tags()`.

See: [Deep dive: interop and dependency gating](#deep-dive-interop-extensions-features-tools).

### Step 8 — Tools, reasoning, multipart (decide responsibilities)

Best practice:

- provider: transport + base message conversion + chunk parsing
- extension: tool-call accumulation, reasoning extraction, citations, caching metadata
- feature: cold-path request shaping and finalize transforms

See: [Interop deep dive](#deep-dive-interop-extensions-features-tools).

### Step 9 — Build the test suite (inside the package)

Minimum recommended tests:

- non-streaming: `send_request` produces expected final core message
- streaming: `send_request_stream` yields partials and a final
- native retention: second turn sees a marker that only exists in native history
- extension/feature hooks: verify at least one observable transformation

See: [Testing deep dive](#deep-dive-testing-provider-plugins).

---

## How requests flow (runtime order)

This section is a short “call order” reference.

### Non-streaming: `AgentCore.send_request`

High-level order:

1. Provider+features+tools init chain (tools first; tool schemas injected into provider config)
2. Core → native conversion
3. `initialize_request` chain (provider, then extensions, then features)
4. `provider.call_api(...)`
5. `provider.finalize(...)` (provider then extensions)
6. Feature `finalize(...)`
7. Native → core conversion (provider then extensions then features)

See runtime code:

- `core/python/agent_core/core.py` (`send_request`, `_pre_request`)

### Streaming: `AgentCore.send_request_stream`

High-level order:

1–3. Same setup as non-streaming
4. `provider.stream_api(...)` yields chunks
5. Per chunk: provider `process_chunk` then extension `process_chunk`
6. After stream: `provider.finalize(...)` (provider then extensions)
7. Feature `finalize(...)`
8. Native → core conversion once finalization completes

See runtime code:

- `core/python/agent_core/core.py` (`send_request_stream`)
- `core/python/agent_core/plugin/provider.py` (`ProviderWrapper.stream_messages`, `process_chunk`, `finalize`)

---

## ProviderPlugin API reference (method-by-method)

Protocol and docstrings live in: `core/python/agent_core/types.py` (`ProviderPlugin`).

### Identity, config & UI

#### `name` / `version`

Class attributes identifying your plugin.

#### `get_config_schema() -> dict`

Return a JSON-schema-like dict mapping config keys to schema objects.

Used by applications to build UI and validate config.

#### `get_ui_elements() -> list[dict]`

Optional UI elements. The core treats these dicts as opaque.

### Lifecycle & state

#### `init(config: dict) -> state: dict`

Initialize provider state from config. Called once per request.

Best practice: store `config` under `state["config"]`.

#### `initialize_request(native_messages, state) -> (native_messages, state)`

Prepare for a new turn.

Use this to:

- build `state["request"]` (url/payload/headers/timeout)
- reset per-turn accumulators (e.g. `state["partial"]`)

### Conversion

#### `to_native_messages(messages, state) -> list[dict]`

Convert core messages into provider-native messages.

Important: core may call this with a **single message** (e.g. when appending to native history efficiently), so handle both full-history lists and single-element lists.

#### `from_native_messages(native_messages, state) -> list[dict]`

Convert provider-native messages into core message dicts.

Best practice: use this conversion to build stable core messages and put provider-specific extras into `metadata` (or allow extensions to do so).

#### `to_display_format(message, state) -> dict` (optional)

Used by some applications to render messages. Most providers can return the message unchanged.

### Capabilities

#### `get_models(config) -> list[ModelDescriptor]` (optional)

Return available models. If not implemented, some adapters default to `[{'id': config['model']}]` when present.

#### `get_tags(config, models) -> list[str]`

Return capability/environment tags.

These tags are used to enable/disable extensions/features/tools via their `required_tags()`.

### I/O

#### `call_api(native_messages, state)`

Make a non-streaming API call.

Best practice in this codebase: for non-streaming, consider returning no finals from `call_api` and emitting finals from `finalize` (so provider extensions can reliably modify the final message in their own `finalize` hook).

See reference patterns:

- `core/python/plugins/deterministic_stream_provider.py` (non-streaming computed in `call_api`, emitted in `finalize`)

#### `stream_api(native_messages, state) -> Iterator[chunk]`

Make a streaming API call and yield provider-native chunk objects.

#### `process_chunk(native_chunk, native_messages, state)`

Process one chunk on the hot path.

Recommended pattern:

- extract a delta from `native_chunk`
- reduce into a partial fragment and `state["partial"]` accumulator
- emit partial fragments (for UI) but do not append raw chunk objects to native history

#### `finalize(native_messages, state)`

Called once after streaming completes (and also used in non-streaming flows).

Provider finalize runs first, then provider extension finalize hooks run, then feature finalize hooks run.

Finalize should:

- emit final assistant message(s)
- append those finals to the returned provider-native history

---

## Deep dive: state design patterns

Recommended state keys:

- `config`: the merged request config dict
- `request`: request info (`url`, `payload`, `headers`, `timeout`)
- `partial`: streaming accumulator dict (shared with extensions)

Guidelines:

- Treat state as immutable-by-convention: return new dicts rather than mutating in place.
  (Some providers mutate for convenience; keep it minimal and predictable.)
- Never log secrets (API keys, auth headers).

---

## Deep dive: native history retention

AgentCore may persist provider-native history to:

- keep exact provider semantics across turns
- preserve fields that are lossy across core ↔ native conversion

Key ideas:

- After a request completes, the core stores provider-native history under `session.metadata["native_messages"]`.
- The core verifies integrity between core messages and retained native history using `native_messages_integrity`.
- When native history is present and valid, subsequent requests reuse it instead of reconverting full history.

Provider/plugin author requirements:

1. Return coherent native history from `call_api` / `process_chunk` / `finalize`.
2. Append final assistant message(s) into native history.
3. Do not append raw per-chunk objects to native history.
4. If you need metadata to survive rebuild-from-native, persist it into native messages under `_metadata`.

Reference tests showing why this matters:

- `core/python/tests/test_native_retention_across_core_instances.py`

---

## Deep dive: streaming patterns & recipes

### Accumulator-based pattern

This is the recommended streaming pattern:

- `stream_api` yields raw chunks
- `process_chunk` extracts a delta and merges into `state["partial"]`
- `finalize` emits `state["partial"]` as the final assistant message

Reference implementation:

- `core/python/plugins/openai_provider.py` (OpenAI-compatible)

### Keep native history clean

Provider-native history should represent chat turns (system/user/assistant/tool messages), not raw stream chunks.

If you want to keep raw chunks for debugging, store them in state under a non-persisted key (do not append to native history).

---

## Deep dive: interop (extensions, features, tools)

### Provider extensions

Provider extensions run:

- on the hot path (`process_chunk`) after the provider processes each chunk
- on the cold path (`finalize`) after the provider’s finalize

Best practice: put provider-specific enrichments here:

- reasoning extraction
- tool-call delta accumulation
- citations
- caching metadata

Reference extensions:

- `core/python/plugins/openai_tools_extension.py`
- `core/python/plugins/ollama_thinking_extension.py`

### Tools

Tools run before provider init; their schemas are injected into provider config under `config["tools"]`.

Providers that support tool calling should add these tool schemas to their request payload (often via an extension).

### Features

Features run on the cold path. They can:

- adjust provider-native messages before I/O (`to_native_messages` / `initialize_request`)
- transform provider-native finals in `finalize`

---

## Deep dive: testing provider plugins

Recommended: keep tests **inside your plugin package**, and ensure they are offline/deterministic.

Minimum suite:

- non-streaming request: `send_request`
- streaming request: `send_request_stream`
- native retention across turns (preferably across two AgentCore instances)
- extension/feature hooks produce observable transformations

Use the template as a reference:

- `plugins/template-python-provider/tests/*`

---

## Deep dive: packaging & loading

Provider plugins are typically loaded as pip-installable repos.

Recommended structure:

- `pyproject.toml` (installable)
- `agent_plugin.json` installed as a top-level data file
- `src/<your_package>/...`
- `tests/`

The application layer supports loading:

- dotted class paths (no install)
- local path repos (`path:...`) using `agent_plugin.json`
- git repos (`git+...`) using `agent_plugin.json`

See runtime code:

- `core/python/agent_app/plugin_sources/*`

---

## Troubleshooting / FAQ

### “My metadata disappears after a turn”

Persist it into native history under `_metadata` and reconstruct it in `from_native_messages`.

### “My extension doesn’t enable”

Check `get_tags` (provider) and `required_tags` (extension/feature/tool).

### “Native integrity error”

Your provider/native history may not match the core messages. Ensure you return full coherent native history and append finals correctly.

---

## Reference implementations (copy patterns from these)

Providers:

- `core/python/plugins/openai_provider.py` (OpenAI-compatible; streaming accumulator)
- `plugins/openrouter/src/openrouter_plugins/openrouter_provider.py` (OpenRouter; OpenAI-like)
- `core/python/plugins/deterministic_stream_provider.py` (deterministic provider used in integration tests)
- `core/python/tests/dummy_provider.py` (dummy provider with clear comments)

Provider extensions:

- `core/python/plugins/openai_tools_extension.py` (tool-call accumulation)
- `core/python/plugins/ollama_thinking_extension.py` (reasoning/thinking enrichment)
