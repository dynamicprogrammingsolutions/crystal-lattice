# Tool Schema + Tool Call Adapters (One Direction) and Accessors

Short description: Define a minimal interop layer that allows providers to translate tool schemas and tool calls between formats (e.g. OpenAI Chat vs OpenAI Responses) without changing existing tool plugins. Adapters convert in a single direction; accessors provide relaxed, stable read-only access to required fields.

Parent Task: `tasks/20260309-openrouter-responses-provider/000-main.md`

## Goals

1. Keep existing tool plugins working with minimal/no changes.
2. Allow a provider to speak a different wire format (e.g. Responses) by using declared adapters.
3. Reduce hard-coded structural assumptions about schemas/calls by centralizing “field access” behind accessors.
4. Leave room for future non-function tool types (`type: bash`, `type: web_search`, etc.) without requiring strict schemas.

## Non-goals (for this subtask)

- Do not redesign the entire tool loop or replace `metadata.tool_calls` yet.
- Do not introduce a new universal schema that all tools must output.

## Proposed approach

### Canonical internal format (initial)

To minimize churn, the canonical internal representation remains the current OpenAI-ish format:

- Tool schemas: OpenAI chat-style tools array items:
  - `{"type": "function", "function": {"name": ..., "description": ..., "parameters": ...}}`
- Tool calls: OpenAI-style tool calls stored in `assistant.metadata.tool_calls`:
  - `{"id": "call_...", "type": "function", "function": {"name": "...", "arguments": "{...}"}}`

This does not prohibit non-function tool types; it only means the initial core/tool-loop execution path remains “locally executable functions”.

### One-direction adapters

Adapters convert a single object (or payload) from one format into another. Bidirectional support is achieved by registering two different adapters.

Examples:

- `OpenAIChatToolSchemaToOpenAIResponsesToolSchema`
- `OpenAIResponsesToolCallToOpenAIChatToolCall`

Adapters are selected by explicit declaration on the provider/tool side; `can_handle(...)` is used as a guardrail and for optional detection.

### Accessors

Accessors are read-only helpers used by core/provider code to retrieve required fields from a schema/call without hardcoding the shape.

In this task we keep access strict per supported format (no legacy fallbacks). New formats are supported by adding new accessors/adapters.

## Proposed interface (Python)

The concrete location/module name is TBD; the intent is to keep it shared (reusable across providers).

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Sequence


@dataclass(frozen=True)
class ToolInteropTarget:
    """Identifies the target wire format a provider needs."""

    name: str
    # Examples:
    # - "openai.chat_completions"
    # - "openai.responses"


class ToolSchemaAdapter(Protocol):
    """Convert tool schema objects in one direction."""

    source_format: str
    target_format: str

    def can_handle(self, schema: Any) -> bool:
        ...

    def convert(self, schema: Dict[str, Any], *, target: ToolInteropTarget) -> Dict[str, Any]:
        ...


class ToolCallAdapter(Protocol):
    """Convert tool call objects (and/or call-like deltas) in one direction."""

    source_format: str
    target_format: str

    def can_handle(self, call: Any) -> bool:
        ...

    def convert(self, call: Dict[str, Any], *, target: ToolInteropTarget) -> Dict[str, Any]:
        ...


class ToolSchemaAccessor(Protocol):
    """Read-only extraction helpers for a specific schema format."""

    format: str

    def can_handle(self, schema: Any) -> bool:
        ...

    def get_tool_name(self, schema: Dict[str, Any]) -> Optional[str]:
        ...

    def get_tool_type(self, schema: Dict[str, Any]) -> Optional[str]:
        ...


class ToolCallAccessor(Protocol):
    """Read-only extraction helpers for a specific tool call format."""

    format: str

    def can_handle(self, call: Any) -> bool:
        ...

    def get_call_id(self, call: Dict[str, Any]) -> Optional[str]:
        ...

    def get_tool_name(self, call: Dict[str, Any]) -> Optional[str]:
        ...

    def get_arguments(self, call: Dict[str, Any]) -> Any:
        """Return dict or JSON string; caller decides parsing policy."""
        ...


@dataclass(frozen=True)
class ToolInteropPolicy:
    """Controls how strict conversion/lookup should be."""

    strict: bool = False


class ToolInteropRegistry:
    """Holds known adapters/accessors and provides resolution helpers."""

    def __init__(
        self,
        *,
        schema_adapters: Sequence[type[ToolSchemaAdapter]] = (),
        call_adapters: Sequence[type[ToolCallAdapter]] = (),
        schema_accessors: Sequence[type[ToolSchemaAccessor]] = (),
        call_accessors: Sequence[type[ToolCallAccessor]] = (),
    ) -> None:
        ...

    def convert_schemas(
        self,
        schemas: List[Dict[str, Any]],
        *,
        adapters: Sequence[type[ToolSchemaAdapter]],
        target: ToolInteropTarget,
        policy: ToolInteropPolicy = ToolInteropPolicy(),
    ) -> List[Dict[str, Any]]:
        ...

    def convert_tool_calls(
        self,
        calls: List[Dict[str, Any]],
        *,
        adapters: Sequence[type[ToolCallAdapter]],
        target: ToolInteropTarget,
        policy: ToolInteropPolicy = ToolInteropPolicy(),
    ) -> List[Dict[str, Any]]:
        ...

    def get_schema_accessor(self, schema: Dict[str, Any]) -> ToolSchemaAccessor:
        ...

    def get_call_accessor(self, call: Dict[str, Any]) -> ToolCallAccessor:
        ...
```

Notes:

- The provider or tool plugin supplies the adapters list it wants to use for a boundary. The registry’s auto-resolution via `can_handle` is a fallback.
- This interface intentionally keeps inputs/outputs as `dict[str, Any]` to remain compatible with existing plugin return types.

## Concrete adapters to implement for OpenRouter Responses

1. `OpenAIChatToolSchemaToOpenAIResponsesToolSchema`
   - Input: `{type:"function", function:{name, description?, parameters?}}`
   - Output: `{type:"function", name, description?, parameters?}`

2. `OpenAIResponsesToolCallToOpenAIChatToolCall`
   - Input: Responses-native function call representation (from Responses streaming events or final output)
   - Output: OpenAI tool call object: `{id, type:"function", function:{name, arguments}}`

3. (Likely) tool output mapping for tool results back into Responses inputs
   - A dedicated adapter for tool *outputs* may be needed depending on how the provider constructs “tool result” inputs for `/responses`.

## Success criteria

- A provider can request tool schemas in OpenAI chat format from tools (existing behavior) and convert them to a Responses wire format via adapters.
- A provider can parse Responses tool-call outputs/events and produce canonical `metadata.tool_calls` objects for the existing tool loop.
- Core/provider call sites that need `name`/`id`/`args` use accessors rather than hardcoded key paths.

## Plan (added during completion)

This subtask is implemented **strict-only**: we only support the canonical in-repo shapes (no backwards-compat fallbacks like top-level `schema["name"]` or `call["tool_call_id"]`).

1. Add `agent_core` tool interop module (protocols + registry + strict accessors + OpenAI Chat ↔ Responses adapters).
2. Refactor core + app tool-loop call sites to use accessors (remove hard-coded key paths + remove fallback shapes).
3. Update repo tests/fixtures to use canonical tool-call shapes.
4. Add unit tests for accessors/adapters.
5. Run `pytest core/python/tests -q`.

## Checklist

- [x] Add `core/python/agent_core/tool_interop.py` (strict accessors + adapters + registry)
- [x] Refactor core tool execution paths to use accessors
- [x] Refactor application tool-loop preview/lookup paths to use accessors
- [x] Update tests to use canonical tool-call shapes
- [x] Add unit tests for tool interop
- [x] Run `pytest core/python/tests -q`
