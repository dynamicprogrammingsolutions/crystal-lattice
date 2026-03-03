# Subtask: Provider extension docs (reasoning + tool calling)

Parent Task: tasks/20260303-provider-plugin-docs/000-main.md

Depends On:

- tasks/20260303-provider-plugin-docs/020-provider-plugins-doc.md
- tasks/20260303-provider-plugin-docs/040-template-provider-tests.md

## Description

Expand `plugins/docs/` to fully document **provider extensions** (`ProviderExtensionPlugin`) so that a provider author can implement complete support for:

- Tool calling (including streaming `tool_calls` accumulation and tool message mapping)
- Reasoning/thinking (including streaming reasoning accumulation, and optional `reasoning_details` preservation)

The current provider guide (`plugins/docs/provider-plugins.md`) mentions extensions but does not provide enough detail for authors to implement real tools/reasoning support end-to-end.

This subtask adds the missing “how-to” documentation and clarifies the runtime contracts (metadata keys, state/accumulator rules, and hot-path invariants) that make extensions interoperable with the tool loop and UIs.

## Goals

1) Provide a clear, copyable recipe for implementing a **tools extension** and a **reasoning extension**.
2) Document the **core metadata contract** expected by the tool loop and terminal rendering.
3) Document the **streaming accumulator interop requirement**: provider and extensions must not stomp each other’s fields when using `state["partial"]`.
4) Provide a testing strategy: unit tests for extension logic + integration scaffolds.
5) Keep `plugins/docs/provider-plugins.md` readable by moving deep extension details into a dedicated page, while still summarizing the extension story in the provider guide.

## Proposed docs structure

Create a new doc page:

- `plugins/docs/provider-extensions.md`

And update:

- `plugins/docs/index.md` (link the new page)
- `plugins/docs/provider-plugins.md` (add a short “Provider extensions: tools + reasoning” section and link to the new page; keep only high-level guidance in the provider guide)

Rationale:

- Provider authors need extensions guidance *when building providers*, so `provider-plugins.md` should link prominently.
- The tools/reasoning extension patterns are long and cross-provider; a separate page avoids bloating the provider doc.

## Content that is missing today (must be added)

### A) ProviderExtensionPlugin lifecycle reference (practical)

Document what each hook is responsible for, and what it is allowed to change:

- `init(config, state)`: store derived config in shared state
- `initialize_request(native_messages, state)`: modify request payload/state at per-turn boundary
- `process_chunk(native_chunk, partial_messages, final_messages, native_messages, state)`: hot path; recommend only enriching partials and updating `state["partial"]`
- `finalize(final_messages, native_messages, state)`: cold path; final adjustments after provider finalize
- `to_native_messages` / `from_native_messages`: stateless mapping between core metadata and provider-native fields

Include guidance about `to_native_messages`/`from_native_messages` being called with single-message lists (from `AgentCore.add_message`) and full-history lists (from request conversion).

### B) Canonical metadata keys (UI + tool loop interop)

Document the keys that should exist on **core messages** for apps/tool loops to work:

- Assistant messages:
  - `metadata["tool_calls"]`: list of OpenAI-style tool calls
  - `metadata["reasoning"]`: reasoning/thinking text (optional)
  - `metadata["reasoning_details"]`: provider-native detail blocks (optional)
- Tool messages:
  - `metadata["tool_call_id"]`: id linking tool result to a tool call
  - `metadata["tool_name"]`: tool name (produced by core tools)
  - `metadata["display"]`: optional display helper for UIs

Clarify where these come from:

- `tool_calls` originate from provider-native fields and should be mapped by a tools extension.
- `tool_call_id` should be preserved across native-history rebuilds (often via provider-native `_metadata`).

### C) Tools extension recipe (non-streaming + streaming)

Provide a concrete, provider-agnostic recipe:

1) In `init`: capture `config["tools"]` schemas into state.
2) In `initialize_request`: inject tools/tool_choice into request payload.
3) In `process_chunk`: accumulate `tool_calls` streaming deltas (merge by `index`, concatenate `function.arguments` fragments).
4) In `to_native_messages`: map outbound core messages into provider-native `tool_calls` and `tool_call_id`.
5) In `from_native_messages`: surface provider-native tool_calls and `_metadata` into core `metadata`.

### D) Reasoning extension recipe

Provide a similar recipe:

1) Config + UI schema for enabling reasoning, and request payload injection.
2) Streaming accumulation for `reasoning` fragments.
3) Optional accumulation/preservation for `reasoning_details` (multi-provider formats).
4) Mapping provider-native reasoning fields into core `metadata["reasoning"]`.

### E) Accumulator interop requirement (critical pitfall)

Call out explicitly:

- If extensions store data in `state["partial"]` (the shared accumulator), the provider’s accumulation logic must preserve unknown keys when merging new deltas.
- Providers should merge deltas with a pattern like `{**current, ...}` rather than constructing a fresh dict with only `role/content`.

This is required for extensions like tools/reasoning/usage to work reliably.

### F) Testing strategy

Document recommended testing layers:

- Offline unit tests for extension mapping and delta accumulation.
- Integration scaffolds (`pytest -m integration`) which are `xfail` until the provider author removes the mark.

Point authors at `plugins/template-python-provider/tests/` as scaffolding and at the OpenRouter tests as comprehensive examples.

## References for further research (source of truth)

Completing agent should study these files before writing docs:

**Protocols & wrappers**

- `core/python/agent_core/types.py` (`ProviderExtensionPlugin` docstrings + method contracts)
- `core/python/agent_core/plugin/provider.py` (`ProviderWrapper.process_chunk`, partial conversion pipeline)
- `core/python/agent_core/plugin/adapters.py` (`ProviderExtensionDefaultsAdapter` semantics, especially `initialize_request` return handling)

**Tool loop & UI expectations**

- `core/python/agent_app/tool_loop.py` (tool-loop semantics + event shapes)
- `core/python/agent_app/application_future.py` (tool call extraction relies on `assistant.metadata.tool_calls`)
- `application/python/agent_terminal_app/event_rendering.py` (renders `metadata.reasoning` and summarizes `metadata.tool_calls`)
- `docs/api/events.md` (tool calling events)
- `docs/api/core-sdk.md` (`execute_tool_calls` accepted tool call shapes)

**Reference extensions (recommended patterns)**

- `core/python/plugins/openai_tools_extension.py` (canonical tools extension: payload injection + streaming accumulation + message mapping)
- `core/python/plugins/ollama_thinking_extension.py` (canonical reasoning extension: payload injection + streaming accumulation + metadata)

**Provider examples that preserve accumulator keys**

- `core/python/plugins/openai_provider.py` (`_merge_delta_content` uses `{**current, ...}`)
- `plugins/openrouter/src/openrouter_plugins/openrouter_provider.py` (similar accumulator merge)

**Comprehensive provider-specific extensions/tests**

- `plugins/openrouter/src/openrouter_plugins/openrouter_tools_extension.py`
- `plugins/openrouter/src/openrouter_plugins/openrouter_reasoning_extension.py` (reasoning_details accumulation)
- `plugins/openrouter/tests/test_openrouter_tools_comprehensive.py`
- `plugins/openrouter/tests/test_openrouter_tools_reasoning_integration.py`
- `plugins/openrouter/tests/test_openrouter_reasoning_integration.py`

## Detailed plan

1) Review current provider docs and identify gaps
- Read `plugins/docs/provider-plugins.md` and note where it only gestures at extensions.
- Confirm which metadata keys are rendered/consumed by apps and tool loops.

2) Study reference implementations
- Tools extension: `core/python/plugins/openai_tools_extension.py`.
- Reasoning extension: `core/python/plugins/ollama_thinking_extension.py` and `plugins/openrouter/src/openrouter_plugins/openrouter_reasoning_extension.py`.
- Verify wrapper behavior on the hot path: `core/python/agent_core/plugin/provider.py`.

3) Decide doc split and outline
- Keep a short summary + link in `plugins/docs/provider-plugins.md`.
- Put detailed recipes, code skeletons, and pitfalls in `plugins/docs/provider-extensions.md`.

4) Write `plugins/docs/provider-extensions.md`
- Lifecycle/method reference with invariants.
- “Tools extension” section with:
  - config/tools injection
  - mapping (`tool_calls`, `tool_call_id`, `_metadata`)
  - streaming accumulation algorithm for tool_calls
- “Reasoning extension” section with:
  - request knobs and payload injection
  - streaming accumulation
  - optional reasoning_details handling
- “Shared accumulator interop” section that explains why providers must preserve keys.
- “Testing” section pointing to template scaffolds and OpenRouter tests.

5) Wire the new doc into the docs index and provider guide
- Update `plugins/docs/index.md` to link `provider-extensions.md`.
- Update `plugins/docs/provider-plugins.md` with a short “Provider extensions: tools + reasoning” section and links.

6) Validate documentation quality
- `rg` for dead/broken file references.
- Ensure code blocks are minimal and copyable.
- Ensure terminology matches runtime (`tool_calls`, `tool_call_id`, `_metadata`, `state["partial"]`).

---

## Completion plan + finalized TOC (added 2026-03-03)

### Finalized documentation structure (`plugins/docs/provider-extensions.md`)

1) Overview (what extensions are for; tools + reasoning)
2) Runtime contracts (interop)
   - Canonical core metadata keys (`tool_calls`, `tool_call_id`, `reasoning`, `reasoning_details`, `tool_name`, `display`)
   - Tool-call shapes accepted by `AgentCore.execute_tool_calls` / tool loop
3) Lifecycle & hook reference (what each hook is for)
4) Shared streaming accumulator contract (`state["partial"]`)
   - Provider requirement: preserve unknown accumulator keys when merging
   - Extension requirement: merge into `state["partial"]` without stomping
5) Generic accumulator pattern for extensions (provider-style)
6) Recipe: Tools extension (OpenAI-compatible deltas)
   - request injection (`config["tools"]` → `state["request"]["payload"]["tools"]`)
   - streaming accumulation (`delta.tool_calls` merge-by-index + arguments concatenation)
   - mapping (`tool_calls` + `tool_call_id`) to/from core metadata
7) Recipe: Reasoning extension (OpenAI-compatible deltas)
   - request knobs (example: `reasoning_effort`)
   - streaming accumulation (`delta.reasoning` fragments)
   - optional `reasoning_details` preservation/accumulation
8) Testing strategy (unit tests for reducers/mappers; integration scaffolds)
9) Reference implementations + runtime file pointers

### Documentation files to change

- Add: `plugins/docs/provider-extensions.md`
- Update: `plugins/docs/index.md` (link)
- Update: `plugins/docs/provider-plugins.md` (short section + link)

### Code examples to include (clean, short, reusable)

#### A) Generic accumulator helper (provider-style)

```python
from __future__ import annotations

from typing import Any, Iterable


def _merge_delta_content(
    current: dict[str, Any],
    delta: dict[str, Any],
    *,
    override: Iterable[str] = (),
    accumulate: Iterable[str] = (),
) -> dict[str, Any]:
    return {
        **current,
        **{k: delta.get(k, current.get(k, "")) for k in override},
        **{k: (current.get(k) or "") + (delta.get(k) or "") for k in accumulate},
    }
```

#### B) Generic extension streaming path (like the provider accumulator pattern)

```python
from __future__ import annotations

from typing import Any


class AccumulatorExtensionMixin:
    def extract_delta(self, native_chunk: dict[str, Any]) -> dict[str, Any]:  # pragma: no cover
        raise NotImplementedError

    def process_delta(
        self,
        delta: dict[str, Any],
        accumulated: dict[str, Any] | None,
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:  # pragma: no cover
        raise NotImplementedError

    def process_chunk(
        self,
        native_chunk: dict[str, Any] | None,
        partial_messages: list[dict[str, Any]],
        final_messages: list[dict[str, Any]],
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
    ):
        delta = self.extract_delta(native_chunk or {})
        acc = state.get("partial") if isinstance(state.get("partial"), dict) else {}
        patch, acc = self.process_delta(delta, acc)

        new_partials = partial_messages
        if isinstance(patch, dict) and patch and partial_messages:
            new_partials = [*partial_messages[:-1], {**partial_messages[-1], **patch}]

        return new_partials, final_messages, list(native_messages), {**state, "partial": acc}
```

#### C) Tool-call accumulation helper using `_merge_delta_content` for nested function merge

```python
from __future__ import annotations

from typing import Any


def _merge_shallow(
    current: dict[str, Any],
    delta: dict[str, Any],
    *,
    exclude: tuple[str, ...] = (),
) -> dict[str, Any]:
    return {**current, **{k: v for k, v in delta.items() if k not in exclude}}


def _merge_tool_call(current: dict[str, Any], delta: dict[str, Any]) -> dict[str, Any]:
    out = _merge_shallow(current, delta, exclude=("index", "function"))
    func_delta = delta.get("function")
    if isinstance(func_delta, dict):
        func_current = out.get("function")
        func_current = func_current if isinstance(func_current, dict) else {}
        out["function"] = _merge_delta_content(
            func_current,
            func_delta,
            override=("name",),
            accumulate=("arguments",),
        )
    return out


def _merge_tool_calls(existing: list[dict[str, Any]], deltas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged = [dict(tc) for tc in existing]
    for d in deltas:
        if not isinstance(d, dict):
            continue
        i = d.get("index")
        i = i if isinstance(i, int) and i >= 0 else len(merged)
        while len(merged) <= i:
            merged.append({})
        merged[i] = _merge_tool_call(merged[i], d)
    return merged
```

#### D) Minimal OpenAI-compatible tools extension skeleton (recipe)

```python
from __future__ import annotations

from typing import Any

from agent_core.types import ProviderExtensionPlugin


class OpenAICompatibleToolsExtension(AccumulatorExtensionMixin, ProviderExtensionPlugin):
    name = "my_tools"
    version = "0.1.0"

    def required_tags(self) -> list[str]:
        return ["provider:openai_compatible", "supports_tools"]

    def init(self, config: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        tools = config.get("tools")
        return {**state, "_tools": tools if isinstance(tools, list) else []}

    def initialize_request(self, native_messages: list[dict[str, Any]], state: dict[str, Any]):
        tools = state.get("_tools") or []
        if not tools:
            return native_messages, state
        req = state.get("request") or {}
        payload = dict(req.get("payload") or {})
        payload |= {"tools": tools, "tool_choice": payload.get("tool_choice", "auto")}
        return native_messages, {**state, "request": {**req, "payload": payload}}

    def extract_delta(self, native_chunk: dict[str, Any]) -> dict[str, Any]:
        choice = (native_chunk.get("choices") or [{}])[0]
        return choice if isinstance(choice, dict) else {}

    def process_delta(self, delta: dict[str, Any], accumulated: dict[str, Any] | None):
        base = accumulated or {}
        d = delta.get("delta") or delta.get("message") or {}
        tool_deltas = d.get("tool_calls") if isinstance(d, dict) else None
        if not isinstance(tool_deltas, list) or not tool_deltas:
            return None, base

        existing = base.get("tool_calls") if isinstance(base.get("tool_calls"), list) else []
        merged = _merge_tool_calls(
            existing=[tc for tc in existing if isinstance(tc, dict)],
            deltas=[tc for tc in tool_deltas if isinstance(tc, dict)],
        )
        new_acc = {**base, "tool_calls": merged}
        return {"tool_calls": merged}, new_acc
```

#### E) Minimal OpenAI-compatible reasoning extension skeleton (recipe)

```python
from __future__ import annotations

from typing import Any

from agent_core.types import ProviderExtensionPlugin


class OpenAICompatibleReasoningExtension(AccumulatorExtensionMixin, ProviderExtensionPlugin):
    name = "my_reasoning"
    version = "0.1.0"

    def required_tags(self) -> list[str]:
        return ["provider:openai_compatible", "supports_thinking"]

    def extract_delta(self, native_chunk: dict[str, Any]) -> dict[str, Any]:
        choice = (native_chunk.get("choices") or [{}])[0]
        return choice if isinstance(choice, dict) else {}

    def process_delta(self, delta: dict[str, Any], accumulated: dict[str, Any] | None):
        base = accumulated or {}
        d = delta.get("delta") or delta.get("message") or {}
        frag = d.get("reasoning") if isinstance(d, dict) else None
        if not isinstance(frag, str) or not frag:
            return None, base

        new_acc = _merge_delta_content(base, {"reasoning": frag}, accumulate=("reasoning",))
        return {"reasoning": frag}, new_acc
```

---

## Completion notes (added 2026-03-03)

- Added the dedicated provider extensions doc page: `plugins/docs/provider-extensions.md`.
- Wired it into the docs index: `plugins/docs/index.md`.
- Kept `plugins/docs/provider-plugins.md` high-level by adding a short link and pointer to the new page.
- Code examples use a provider-style accumulator pattern (generic `process_chunk` calling provider-specific `extract_delta`/`process_delta`) and OpenAI-compatible streaming delta fields (`choices[0].delta.tool_calls`, `choices[0].delta.reasoning`).

