# Provider plugins

Provider plugins integrate LLM APIs and convert between:

- **Core messages**: AgentCore’s stable, provider-agnostic message format
- **Provider-native messages**: the wire-format your provider uses

This guide is **provider-specific** and intended to be more complete than the general plugin overview in `docs/plugins/development.md`.

Runtime code references (source of truth):

- Protocols/docstrings: `core/python/agent_core/types.py`
- Provider wrapper orchestration: `core/python/agent_core/plugin/provider.py`
- Defaulting/normalization: `core/python/agent_core/plugin/adapters.py`
- Core request flow: `core/python/agent_core/core.py`

## Contents

- [Concepts & vocabulary](#concepts--vocabulary)
- [Quickstart / development workflow](#quickstart--development-workflow)
- [Complete guide: build a full provider](#complete-guide-build-a-full-provider-step-by-step)
- Deep dives:
  - [Provider state shape](#deep-dive-provider-state-shape)
  - [Native history retention](#deep-dive-native-history-retention)
  - [Streaming patterns & recipes](#deep-dive-streaming-patterns--recipes)
  - [Debugging streaming chunks](#deep-dive-debugging-streaming-chunks)
  - [Interop (extensions/features/tools)](#deep-dive-interop-extensionsfeatures-tools)
  - [Testing provider plugins](#deep-dive-testing-provider-plugins)
- [Reference implementations](#reference-implementations)

See also:

- [Provider extensions (tools + reasoning)](provider-extensions.md)
- [Packaging & loading plugins](plugin-packaging-and-loading.md)
- [Execution order (providers, extensions, features, tools)](plugin-execution-order.md)
- [UI elements (`get_ui_elements`)](ui-elements.md)
- [Testing & validation](testing-and-validation.md)

---

## Concepts & vocabulary

### Core message shape

Core messages are dicts like:

```python
{
  "role": "user" | "assistant" | "system" | "tool",
  "content": "...",
  "metadata": {"any": "json"},
  # optionally:
  "multipartContent": [
    {"type": "image", "content": {"url": "..."}, "metadata": {}}
  ]
}
```

### Provider-native message shape

Provider-native messages are whatever your provider needs. Common OpenAI-like shape:

```python
{"role": "user", "content": "Hello"}
```

Provider-native messages may include provider-specific keys (tool calls, reasoning, cache metadata, etc.):

```python
{
  "role": "assistant",
  "content": "...",
  "tool_calls": [{"id": "...", "type": "function", "function": {"name": "x", "arguments": "{}"}}],
  "reasoning": "...",
  "_metadata": {"cached_tokens": 123}
}
```

### Partials vs finals

- **partials**: incremental updates during streaming
- **finals**: completed assistant messages for the turn

Partial example (during streaming):

```python
{"role": "assistant", "content": "Hel"}
```

Final example (after finalize):

```python
{"role": "assistant", "content": "Hello world"}
```

### Shared provider state (`state: dict`)

Providers, provider extensions, and features share a single state dict (owned by the provider wrapper).

Recommended state shape:

```python
state = {
  "config": config,
  "request": {"url": "...", "payload": {...}, "headers": {...}, "timeout": 60},
  "partial": None,
}
```

---

## Quickstart / development workflow

This workflow matches how provider integrations are typically built in practice:

1) package scaffold → 2) non-streaming first (learn shapes) → 3) streaming → 4) try in a real app

### Step 0 — Create a provider plugin package (recommended)

Start from the template:

- `plugins/template-python-provider`

Copy it (or fork it) and rename:

```text
template-python-provider/  ->  my-provider/
src/template_python_provider/ -> src/my_provider/
```

Update the descriptor `agent_plugin.json` entries to your package/module/class names.

Example `agent_plugin.json`:

```json
{
  "entries": [
    "my_provider.provider.MyProvider",
    "my_provider.extension.MyProviderExtension",
    "my_provider.feature.MyFeature"
  ],
  "subdirectory": "."
}
```

More details: [Packaging & loading plugins](plugin-packaging-and-loading.md).

### Step 1 — Implement non-streaming first (`call_api`) + write the first tests

Non-streaming is the fastest way to learn provider request/response shapes without chunk parsing.

Minimum provider methods to start:

- `init(config) -> state`
- `call_api(native_messages, state)`
- (optionally) `to_native_messages` / `from_native_messages` if you need custom conversion

Example `call_api` skeleton (HTTP omitted):

```python
def call_api(self, native_messages, state):
    request = state.get("request") or {}
    # TODO: send HTTP request
    # raw = requests.post(...).json()
    raw = {"choices": [{"message": {"role": "assistant", "content": "hi"}}]}

    # TODO: extract provider-native assistant message
    msg = raw["choices"][0]["message"]
    # Return (partial_messages, final_messages, native_messages, new_state)
    return [], [msg], [*native_messages, msg], state
```

First smoke test (pytest) should call `send_request`:

```python
def test_call_api_smoke():
    core = AgentCore()
    core.register_provider(MyProvider)
    session = core.create_session()
    session = core.add_message(session, "user", "Hello")
    _new_session, finals = core.send_request(session, {"model": "m"})
    assert finals and finals[-1]["role"] == "assistant"
```

### Step 2 — Add debug logging for shape discovery (trial-and-error)

When you don’t know the response shape yet, add *temporary* debug logging.

Recommended pattern: log truncated payloads and never log secrets.

```python
from agent_core.utils import get_logger
log = get_logger("my_provider")

log.info("provider_response", response=str(raw)[:2000])
```

Recommended test to drive this:

```python
def test_debug_dump_response_shape(caplog):
    # Run one request; inspect caplog output while developing.
    with caplog.at_level("INFO"):
        _session2, finals = core.send_request(session, {"model": "m"})
    assert finals
    # Inspect caplog.text while iterating.
```

### Step 3 — Implement streaming (choose a path)

There are **two supported paths**.

#### Path A (recommended): accumulator pattern

You keep shared `process_chunk`/`finalize` and implement:

- `stream_api`
- `extract_delta`
- `process_delta`

Example delta extractor (OpenAI-like):

```python
def extract_delta(self, chunk: dict) -> dict:
    return (chunk.get("choices") or [{}])[0]
```

Example delta reducer:

```python
def process_delta(self, delta: dict, accumulated: dict | None):
    base = accumulated or {}
    d = delta.get("delta") or {}
    frag = {"role": d.get("role", "assistant"), "content": d.get("content", "")}
    new_acc = {
        "role": base.get("role", frag["role"]),
        "content": base.get("content", "") + (frag.get("content") or ""),
    }
    return frag, new_acc
```

In the template, the shared implementation lives in `AccumulatorStreamingMixin`.

Note: if you use a mixin/base-class that provides `process_chunk`/`finalize`, put it **before** `ProviderPlugin` in your class bases so Python’s method resolution order uses the mixin implementation.

#### Path B: custom streaming

Implement `process_chunk` and `finalize` yourself.

```python
def process_chunk(self, native_chunk, native_messages, state):
    # TODO: parse chunk
    partial = {"role": "assistant", "content": native_chunk.get("content", "")}
    # IMPORTANT: do not append raw chunk to native history
    return [partial], [], list(native_messages), state

def finalize(self, native_messages, state):
    final = {"role": "assistant", "content": state.get("acc", "")}
    return [final], [*native_messages, final], state
```

### Step 4 — Streaming tests (recommended)

First streaming test should:

- assert partial events exist
- assert final exists
- assert final content == concatenation of partials (for simple text providers)

```python
def test_streaming_smoke():
    partial = ""
    final = None
    for e in core.send_request_stream(session, cfg):
        if e["type"] == "partial":
            partial += e["message"].get("content", "")
        if e["type"] == "final":
            final = e
    assert final is not None
    assert final["messages"][-1]["content"]
```

### Step 5 — Try it in a real app config (terminal/desktop/mobile)

Automated tests provide the fastest feedback loop, but you’ll eventually want to try the provider in a real app.

Example terminal app config pattern (adapt from `application/python/agent_terminal_app/config_echo_app.json`):

```json
{
  "plugin_cache_dir": "~/.crystal/cache/plugins",
  "plugins": [
    "path:/abs/or/rel/to/my-provider-repo"
  ],
  "providers": {
    "my_provider_default": {
      "provider": "my_provider_id",
      "model": "my-model",
      "api_key": "${env:MY_API_KEY}",
      "base_url": "https://example.com/v1"
    }
  },
  "agents": {
    "default": {"provider": "my_provider_default"}
  }
}
```

Then run the terminal app with that config (see `application/python/agent_terminal_app`):

```bash
cd application/python
python -m agent_terminal_app --console --config /path/to/your_config.json
```

For more config formats, see:

- [Packaging & loading plugins](plugin-packaging-and-loading.md)
- `docs/plugins/application-config.md`

---

## Complete guide: build a full provider (step-by-step)

This section expands each step with best practices and links to deep dives.

### 1) Define identity, config schema, and UI

```python
class MyProvider(AccumulatorStreamingMixin, ProviderPlugin):
    name = "my_provider_id"
    version = "0.1.0"

    def get_config_schema(self):
        return {
            "model": {"type": "string", "required": True},
            "api_key": {"type": "string", "required": False},
        }

    def get_ui_elements(self):
        return [{"type": "text", "key": "model", "label": "Model"}]
```

UI deep dive: [UI elements](ui-elements.md).

### 2) Implement `init` and `initialize_request`

```python
def init(self, config):
    return {"config": config, "request": {}, "partial": None}

def initialize_request(self, native_messages, state):
    cfg = state.get("config") or {}
    request = {
        "url": (cfg.get("base_url") or "https://api.example.com/v1").rstrip("/") + "/chat/completions",
        "payload": {"model": cfg.get("model")},
        "headers": {"Authorization": f"Bearer {cfg.get('api_key','')}"},
        "timeout": float(cfg.get("timeout", 60)),
    }
    return list(native_messages), {**state, "request": request, "partial": None}
```

### 3) Implement conversion hooks (only when needed)

If you need to preserve metadata across rebuild-from-native, use `_metadata`.

```python
def to_native_messages(self, messages, state):
    out = []
    for m in messages:
        md = dict(m.get("metadata") or {})
        md.pop("native_indices", None)
        nm = {"role": m.get("role"), "content": m.get("content", "")}
        if md:
            nm["_metadata"] = md
        out.append(nm)
    return out

def from_native_messages(self, native_messages, state):
    out = []
    for nm in native_messages:
        md = dict(nm.get("_metadata") or {}) if isinstance(nm.get("_metadata"), dict) else {}
        md.pop("native_indices", None)
        out.append({"role": nm.get("role"), "content": nm.get("content", ""), "metadata": md})
    return out
```

### 4) Non-streaming I/O (`call_api`) first

```python
def call_api(self, native_messages, state):
    request = state["request"]
    # TODO: send HTTP request and parse JSON
    raw = {"choices": [{"message": {"role": "assistant", "content": "hi"}}]}
    msg = raw["choices"][0]["message"]
    # Return (partial_messages, final_messages, native_messages, new_state)
    return [], [msg], [*native_messages, msg], state
```

### 5) Streaming I/O

Accumulator path (recommended): implement `stream_api`, `extract_delta`, `process_delta`.

Custom path: implement `process_chunk` and `finalize` yourself.

### 6) Native history retention (don’t break it)

Provider rules of thumb:

- append *final* assistant messages to native history
- do **not** append raw stream chunks to native history

Example finalize (custom):

```python
def finalize(self, native_messages, state):
    final = state.get("partial")
    if final:
        return [final], [*native_messages, final], state
    return [], list(native_messages), state
```

### 7) Add extension and feature hooks (optional)

Provider extensions are recommended for reasoning/tool-call accumulation.

Example extension stub:

```python
class MyToolsExtension(ProviderExtensionPlugin):
    name = "my_tools"
    version = "0.1.0"
    def required_tags(self):
        return ["supports_tools"]
```

## Deep dive: provider state shape

The provider wrapper owns a shared state dict for one request. Providers, provider extensions, and features can read/write it.

Recommended keys:

```python
state = {
  "config": config,               # resolved request config
  "request": {
    "url": "...",
    "payload": {...},
    "headers": {...},
    "timeout": 60,
  },
  "partial": None,               # streaming accumulator (dict)
  "debug_stream": False,         # optional
}
```

Guidelines:

- Keep `state` JSON-serializable when you can (debugging is easier).
- Avoid storing raw chunks in native history; if you need them for debugging, store them under a state key that is not persisted.

Runtime reference:

- `core/python/agent_core/plugin/provider.py` (wrapper stores/discards state)

---

## Deep dive: native history retention

AgentCore can retain provider-native history in `session.metadata["native_messages"]`.

Why it matters:

- Core↔native conversion can be lossy.
- Some provider-native fields (tool call IDs, cache metadata, special roles) must survive across turns.

Provider rules of thumb:

1. Always return a coherent **full** native history list.
2. Append final assistant messages to native history.
3. Do not append raw stream chunks to native history.
4. Use `_metadata` on native messages if you need metadata to survive rebuild-from-native.

Example: preserving metadata through rebuild-from-native:

```python
# in to_native_messages
nm = {"role": role, "content": content, "_metadata": {"cached_tokens": 123}}

# in from_native_messages
md = dict(native.get("_metadata") or {})
core_msg = {"role": native.get("role"), "content": native.get("content"), "metadata": md}
```

Recommended retention test pattern (native-only marker):

```python
class MarkerExt(ProviderExtensionPlugin):
    def finalize(self, finals, native, state):
        return finals, [{**m, "_native_only": True} for m in native], state

class MyProvider(...):
    def call_api(self, native_messages, state):
        preserved = any(m.get("_native_only") for m in native_messages)
        ...
```

See also:

- `core/python/tests/test_native_retention_across_core_instances.py`

---

## Deep dive: streaming patterns & recipes

### Recipe 1: OpenAI-style SSE JSON chunks

Many providers stream line-delimited JSON where each line contains something like:

```python
{"choices": [{"delta": {"role": "assistant", "content": "H"}}]}
```

Typical accumulator-based implementation:

```python
def extract_delta(self, chunk: dict) -> dict:
    return (chunk.get("choices") or [{}])[0]

def process_delta(self, delta: dict, accumulated: dict | None):
    base = accumulated or {}
    d = delta.get("delta") or {}
    frag = {"role": d.get("role", "assistant"), "content": d.get("content", "")}
    new_acc = {"role": base.get("role", frag["role"]), "content": base.get("content", "") + frag["content"]}
    return frag, new_acc
```

### Recipe 2: Custom `process_chunk` / `finalize` (when the accumulator pattern isn’t a fit)

The accumulator pattern works well when your provider emits clean text/tool/reasoning deltas that can be reduced into a single “final assistant message”.

Implementing `process_chunk`/`finalize` directly is appropriate when:

- The stream has multiple event types that don’t map cleanly to a single accumulator (e.g. separate “content blocks”, “thinking blocks”, “tool blocks”).
- You need special-case handling of deltas (restarts, rewinds, out-of-order indices, partial JSON, etc.).
- You want to emit more than one final message for a turn (for example, a primary answer plus an additional assistant note/message).
- Using `extract_delta`/`process_delta` would be more complicated than handling the protocol explicitly.

In these cases, treat `native_chunk` as an opaque provider event and write an explicit reducer.

Example (illustrative event-type switch):

```python
def process_chunk(self, native_chunk, native_messages, state):
    event_type = native_chunk.get("type")

    # Example: text delta
    if event_type == "content_delta":
        text = (native_chunk.get("delta") or {}).get("text", "")
        acc = (state.get("acc") or "") + (text or "")
        partials = [{"role": "assistant", "content": text}] if text else []
        # IMPORTANT: keep native history unchanged while streaming.
        return partials, [], list(native_messages), {**state, "acc": acc}

    # Example: tool-call delta or other structured data
    if event_type == "tool_delta":
        tool_state = {**(state.get("tool") or {}), **(native_chunk.get("delta") or {})}
        return [], [], list(native_messages), {**state, "tool": tool_state}

    # Ignore unknown/non-message events
    return [], [], list(native_messages), state


def finalize(self, native_messages, state):
    # Build one or more final provider-native assistant messages.
    finals = []
    if state.get("acc"):
        finals.append({"role": "assistant", "content": state["acc"]})
    if state.get("tool"):
        # Example: attach tool summary as a second assistant message
        finals.append({"role": "assistant", "content": f"Tool summary: {state['tool']}"})

    full_history = [*native_messages, *finals]
    return finals, full_history, state
```

Even with fully custom streaming, keep these invariants:

- Do not append raw stream chunks/events into native history.
- Append only final provider-native chat messages (assistant/tool/etc.) to native history.
- Return `native_messages` as a coherent full-history list.

### Tool calls and reasoning

Best practice in this repo:

- Provider: transport + base accumulation
- Extension: tool_call and reasoning delta accumulation (shared `state["partial"]`)

Reference extensions:

- `core/python/plugins/openai_tools_extension.py`
- `core/python/plugins/ollama_thinking_extension.py`

See also: [Provider extensions (tools + reasoning)](provider-extensions.md) for step-by-step recipes, accumulator interop rules, and copyable code skeletons.

---

## Deep dive: debugging streaming chunks

When you don’t know the chunk shape, log the first N chunks/deltas.

Example (with truncation):

```python
from agent_core.utils import get_logger
log = get_logger("my_provider")

if state.get("debug_stream"):
    log.info("chunk", chunk=str(native_chunk)[:2000])
```

Recommended test during development:

```python
def test_capture_first_chunks(caplog):
    # Enable debug_stream in config and run one streaming request.
    with caplog.at_level("INFO"):
        for _ in core.send_request_stream(session, {"debug_stream": True, "model": "m"}):
            pass
    # Inspect caplog.text while iterating.
    assert "chunk" in caplog.text
```

---

## Deep dive: interop (extensions/features/tools)

### Provider extensions

Provider extensions are the preferred place to implement streaming accumulation and metadata mapping for tools and reasoning.

For a dedicated guide with recipes and reusable code patterns, see:

- [Provider extensions (tools + reasoning)](provider-extensions.md)

Extensions can:

- read and update `state["partial"]` during streaming
- attach provider-native fields to the final message during finalize
- surface provider-native fields into core `metadata` via `from_native_messages`

Example required-tags gating:

```python
class MyToolsExtension(ProviderExtensionPlugin):
    def required_tags(self):
        return ["supports_tools"]
```

### Tools (schema injection)

Tools run before the provider initializes; tool schemas are injected into provider config under `config["tools"]`.

Provider-side payload merge example:

```python
tools = state.get("config", {}).get("tools")
if tools:
    payload = {**payload, "tools": tools, "tool_choice": "auto"}
```

See ordering details: [Execution order](plugin-execution-order.md).

---

## Deep dive: testing provider plugins

A good development loop is:

- implement one method
- run a focused test
- iterate

Minimum recommended provider test suite:

1) non-streaming `send_request` smoke test
2) streaming `send_request_stream` smoke test
3) native retention across two turns (preferably across two AgentCore instances)
4) extension/feature hook produces observable change

Example streaming smoke skeleton:

```python
def test_streaming_smoke():
    partial = ""
    final = None
    for e in core.send_request_stream(session, cfg):
        if e["type"] == "partial":
            partial += e["message"].get("content", "")
        elif e["type"] == "final":
            final = e
    assert final is not None
```

Tests to copy patterns from:

- Offline unit tests (always run):
  - `plugins/template-python-provider/tests/test_provider_skeleton_unit.py`
  - `plugins/template-python-provider/tests/test_extension_patterns_unit.py`
- Integration scaffolds (run with `pytest -m integration`; `xfail` by default until implemented):
  - `plugins/template-python-provider/tests/test_provider_integration_basic.py`
  - `plugins/template-python-provider/tests/test_provider_integration_reasoning.py`
  - `plugins/template-python-provider/tests/test_provider_integration_tools.py`
  - `plugins/template-python-provider/tests/test_provider_integration_tools_reasoning.py`
  - `plugins/template-python-provider/tests/test_provider_integration_usage.py`
  - `plugins/template-python-provider/tests/test_agent_application_integration_tools_e2e.py`
- Native retention regression coverage:
  - `core/python/tests/test_native_retention_across_core_instances.py`

---

## Reference implementations

Providers:

- `core/python/plugins/openai_provider.py`
- `plugins/openrouter/src/openrouter_plugins/openrouter_provider.py`

Provider extensions:

- `core/python/plugins/openai_tools_extension.py`
- `core/python/plugins/ollama_thinking_extension.py`

Native retention tests:

- `core/python/tests/test_native_retention_across_core_instances.py`
