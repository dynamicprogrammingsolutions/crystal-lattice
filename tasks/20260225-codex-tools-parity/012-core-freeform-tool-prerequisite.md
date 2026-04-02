# 012 — Core prerequisite: freeform/custom tool support

Add the core interop and execution support needed for tool plugins to originate non-chat, non-function tool schemas and raw-input tool calls end-to-end.

## Requirements checklist

- [ ] Make the generic core tool path stop assuming OpenAI chat-completions function schemas are the only source format.
- [ ] Support a raw-input or freeform/custom tool-call shape needed by upstream Codex `apply_patch`.
- [ ] Preserve existing chat-completions and Responses function-tool behavior while adding the new path.

Parent Task: `tasks/20260225-codex-tools-parity/000-main.md`

## Why this task exists

The repo now has schema/call adapters in `agent_core.tool_interop`, but they are not yet enough to let a tool plugin emit a non-chat schema and still participate fully in:

- tool discovery
- tool preview generation
- tool execution
- provider request injection

That gap is the main blocker for true Codex GPT-5 `apply_patch` parity.

## Findings to preserve

### 1) The interop registry is real, but currently narrow

Current registry and default adapters:

- `core/python/agent_core/tool_interop.py:81-139`
- `core/python/agent_core/tool_interop.py:147-343`

Important current limitations:

- the only built-in schema adapter is chat-completions function -> Responses function
- the default schema accessor list only includes `OpenAIChatToolSchemaAccessor`
- there is no built-in freeform/custom schema accessor or freeform/custom call accessor

### 2) Provider-side Responses injection already uses adapters

Examples:

- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_tools_extension.py:277-304`
- `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_tools_extension.py:65-80`
- `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py:220-228`

This proves the adapter mechanism is useful, but those call sites still assume chat-style schemas as input.

### 3) Generic core tool resolution still hard-codes chat-style accessors

Current call sites:

- `core/python/agent_core/core.py:2748-2809`
- `core/python/agent_core/core.py:2932-2997`
- `core/python/agent_app/tool_loop.py:96-129`
- `core/python/agent_app/tool_loop.py:140-169`

These paths use `OpenAIChatToolSchemaAccessor` and `OpenAIChatToolCallAccessor` directly, which means a plugin-originated non-chat schema or raw-input call will not resolve end-to-end.

### 4) The current `ToolPlugin` protocol assumes structured dict arguments

Relevant protocol methods today:

- `core/python/agent_core/types.py:1157-1242`

The protocol currently expects:

- `execute_tool(..., arguments: Dict[str, Any], ...)`
- `format_tool_call_preview(..., arguments: Dict[str, Any], ...)`
- `stream_tool(..., arguments: Dict[str, Any], ...)`

Upstream Codex freeform `apply_patch` instead behaves like a raw text input tool:

- `../codex/codex-rs/core/src/tools/handlers/apply_patch.rs:288-299`
- `../codex/codex-rs/core/src/tools/handlers/apply_patch.rs:302-389`

## Desired outcome

After this task:

- a tool plugin can expose a non-chat source schema when supported by adapters/accessors
- the generic core tool loop can resolve tool names and arguments without assuming chat-completions function envelopes
- the preview and execution path can pass through raw-input payloads when the selected tool format requires it
- existing chat-style and Responses function-call behavior still works unchanged

## Likely implementation areas

At minimum, evaluate changes in:

- `core/python/agent_core/tool_interop.py`
- `core/python/agent_core/core.py`
- `core/python/agent_app/tool_loop.py`
- `core/python/agent_core/types.py`
- any plugin wrapper/adapters that currently lock `arguments` to `Dict[str, Any]`

The cleanest shape may be one of these:

1. Introduce a normalized internal tool-invocation payload that can represent either structured arguments or raw freeform input.
2. Extend the tool protocol and wrapper layer so previews/execution can receive either dict arguments or raw input in a typed way.

Do not choose an approach that only fixes request payload injection while leaving previews and execution on the old chat-only path.

## Non-goals

This task is the prerequisite only.

Do not do here:

- final `apply_patch` model-specific exposure logic
- the `patch_text` / `input` schema decision in isolation
- shell selection work

Those belong in:

- `tasks/20260225-codex-tools-parity/011-shell-selection-parity.md`
- `tasks/20260225-codex-tools-parity/013-apply-patch-true-parity.md`

## Test expectations

- Add `agent_core` tests covering schema/call accessor selection for at least one non-chat source format.
- Add tests proving a non-chat/raw-input tool can be discovered, previewed, and executed through the generic core tool loop.
- Keep existing function-tool tests passing for both chat and Responses provider paths.

## Execution plan

Added during completion planning on 2026-04-02.

This task is an interop architecture refactor, not a narrow freeform-only feature. The goal is to make tool interop genuinely format-extensible so that tool schemas and tool calls are not forced through a single canonical external format inside core.

### Architectural decisions

The following decisions are part of the plan and should be treated as settled unless new implementation constraints are discovered:

1. There will be no canonical external tool schema/call format in core.
   - Core must stop privileging OpenAI chat-completions function schemas and calls as the universal internal convention.
   - Accessors and adapters exist specifically so source and target can vary.

2. Core still needs a semantic contract.
   - Even without a canonical wire format, core must be able to learn a few facts from schemas/calls via accessors.
   - Minimum required semantics are:
     - tool name, if available
     - tool call id, if available
     - payload value
     - payload kind
     - optional payload format / metadata
   - These semantics come from accessors, not from direct dict-shape assumptions.

3. Accessors inspect; adapters translate.
   - Accessors answer: what is this object, and what can core extract from it?
   - Adapters answer: how can this object be converted into another format?
   - Keep these concerns separate.

4. Explicit interop contributions are additive.
   - If a provider/tool/request contributes explicit accessors or adapters, try them first.
   - If they do not handle a case, contributed and core-default accessors/adapters must still be tried.
   - Explicit inputs must not replace or disable the core defaults.

5. Provider capabilities must be explicit.
   - Providers should declare which schema formats they can accept and which tool-call formats they emit.
   - Adapter selection should target declared provider capabilities, not hardcoded assumptions like "convert to chat-function first".

6. Multihop adapter composition is allowed.
   - Resolver logic may return a direct adapter when available.
   - If no direct adapter supports a source/target pair, the resolver may return a composed adapter built from multiple compatible adapters.
   - Design the API around this possibility from the start.

7. Tool execution should be payload-first.
   - The final payload should remain the second parameter passed to the tool.
   - Additional information such as payload kind/format/metadata should travel via optional keyword arguments.
   - Avoid wrapping payload in a required view object unless later implementation needs it internally.

8. Tool routing should move toward `can_handle(...)`.
   - Add optional tool-side `can_handle_tool_call(...)` support now.
   - Name-based routing remains as a compatibility fallback for older tools.
   - Over time, tool-name dependence should become optional rather than central.

9. Existing OpenAI-chat-style tools should keep working unchanged.
   - This refactor is allowed to break provider-side and core assumptions.
   - It should not require rewriting existing tool plugins that already emit chat-completions function schemas and consume dict payloads.
   - Wrapper/adaptor compatibility should preserve them.

### Target model after refactor

The desired model is:

- tools may emit any schema format
- providers/extensions/tools may contribute additional accessors/adapters
- core builds an effective interop registry for the active request/config
- core asks the registry for the first accessor that can interpret a schema/call
- providers ask the registry for the first compatible adapter path that can turn source schemas into provider-accepted target schemas
- explicit contributions are tried first, then contributed ones, then defaults
- if no adapter path exists, fail clearly rather than silently dropping support

### Effective interop registry

Introduce a composition model for tool interop contributions.

Likely new type:

```python
@dataclass(frozen=True)
class ToolInteropContribution:
    schema_accessors: tuple[ToolSchemaAccessor, ...] = ()
    call_accessors: tuple[ToolCallAccessor, ...] = ()
    schema_adapters: tuple[ToolSchemaAdapter, ...] = ()
    call_adapters: tuple[ToolCallAdapter, ...] = ()
```

Build an effective registry per config/request from three tiers:

1. explicit contributions
2. provider/tool contributed contributions
3. core defaults

Within each tier, support `priority` ordering on accessors/adapters. Explicit tier still outranks contributed tier, and contributed tier still outranks defaults.

The effective registry should be what core/app/provider code uses, instead of directly instantiating `OpenAIChatToolSchemaAccessor` or `OpenAIChatToolCallAccessor`.

### Accessor refactor

Current accessor APIs are too OpenAI-function-centric because they expose `get_arguments(...)` rather than a general payload model.

Refactor accessors to expose payload semantically. The exact final signatures may vary, but they should support the following information.

For tool-call accessors:

```python
class ToolCallAccessor(Protocol):
    priority: int
    format_id: str | None

    def can_handle(self, call: Any) -> bool:
        ...

    def get_call_id(self, call: dict[str, Any]) -> str | None:
        ...

    def get_tool_name(self, call: dict[str, Any]) -> str | None:
        ...

    def get_payload(self, call: dict[str, Any]) -> Any:
        ...

    def get_payload_kind(self, call: dict[str, Any]) -> str:
        ...

    def get_payload_format(self, call: dict[str, Any]) -> str | None:
        ...

    def get_payload_metadata(self, call: dict[str, Any]) -> dict[str, Any] | None:
        ...
```

For schema accessors:

```python
class ToolSchemaAccessor(Protocol):
    priority: int
    format_id: str | None

    def can_handle(self, schema: Any) -> bool:
        ...

    def get_tool_name(self, schema: dict[str, Any]) -> str | None:
        ...

    def get_tool_kind(self, schema: dict[str, Any]) -> str | None:
        ...

    def get_schema_format(self, schema: dict[str, Any]) -> str | None:
        ...
```

Important details:

- `tool_name` becomes optional
- payload is the final payload object, not always a dict
- payload kind can distinguish object/text/etc.
- format ids should exist from the start for diagnostics and adapter routing

Examples:

- OpenAI chat function call accessor:
  - payload = parsed dict arguments
  - payload kind = `"object"`
- future custom/freeform accessor:
  - payload = raw string input
  - payload kind = `"text"`

### Adapter refactor

Adapters should continue to declare source and target formats, but adapter selection must become additive and capability-driven.

Requirements for the new selection logic:

- explicit adapters are prepended, not exclusive
- contributed adapters are considered after explicit ones
- core defaults remain available as fallback
- already-compatible schemas should pass through unchanged
- if no direct adapter exists, resolver may return a composed multihop adapter

Do not keep call sites that pass a narrow adapter list and thereby bypass the broader registry.

Conversion flow should become conceptually closer to:

```python
converted = registry.convert_schemas(
    schemas,
    target_formats=provider.accepted_tool_schema_formats(...),
    explicit_adapters=provider_specific_adapters,
)
```

Resolver behavior:

- detect source format via accessors or adapter `can_handle`
- if provider already accepts the source format, pass through unchanged
- else choose direct adapter if available
- else choose composed adapter chain if available
- else raise a clear `ToolInteropError`

### Provider capability declaration

Providers need to declare what formats they accept/emit so adapter selection has a real target.

Add provider-side hooks such as:

```python
def accepted_tool_schema_formats(self, config, state=None) -> list[str]:
    ...

def emitted_tool_call_formats(self, config, state=None) -> list[str]:
    ...
```

Or an equivalent bundled interop contribution API if that proves cleaner.

Expected behavior examples:

- OpenAI chat-compatible providers likely accept only chat-function tool schemas.
- OpenAI/OpenRouter Responses providers may accept both Responses function schemas and Responses custom/freeform schemas.
- Providers that emit multiple call shapes should declare them all.

### Provider/tool contribution hooks

Add optional interop contribution hooks so providers, provider extensions, and tools can register their own accessors/adapters.

Likely shape:

```python
def get_tool_interop_contribution(
    self,
    config: dict[str, Any],
    state: dict[str, Any] | None = None,
) -> ToolInteropContribution:
    return ToolInteropContribution()
```

This allows:

- providers to contribute target-specific schema/call adapters
- tools to contribute accessors for their own schema/call formats
- Responses-specific custom/freeform support without hardcoding it into core

### Core execution refactor

Remove hardcoded OpenAI chat accessors from generic core execution and app tool loop paths.

This applies at least to:

- `core/python/agent_core/core.py`
- `core/python/agent_app/tool_loop.py`

Replace logic that directly creates `OpenAIChatToolSchemaAccessor` / `OpenAIChatToolCallAccessor` with logic that:

1. builds an effective registry for the active config/request
2. asks the registry for the first schema/call accessor that can handle each object
3. extracts tool name, payload, payload kind, payload format, and metadata through that accessor

The generic tool loop should no longer parse raw dict shapes directly.

### Tool execution API evolution

Move tool-facing execution toward a payload-first API while preserving legacy tools.

Target direction for tool methods:

```python
def execute_tool(
    self,
    tool_name: str | None,
    payload: Any,
    state: dict[str, Any],
    *,
    payload_kind: str | None = None,
    payload_format: str | None = None,
    payload_metadata: dict[str, Any] | None = None,
    tool_call: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ...
```

Apply the same idea to:

- `format_tool_call_preview(...)`
- `stream_tool(...)`

Important compatibility behavior:

- if a plugin implements the new payload-first signature, use it
- if a plugin only implements the legacy dict-arguments form and payload is a dict/object, adapt to the old call
- if a plugin only implements the legacy form but receives unsupported payload kind such as text, fail clearly

The wrapper/adaptor layer should provide this compatibility so existing tools do not need rewriting.

### Tool-side routing via `can_handle_tool_call(...)`

Add optional tool-side routing support now so the system can evolve away from strict name matching.

Likely shape:

```python
def can_handle_tool_call(
    self,
    tool_name: str | None,
    payload: Any,
    state: dict[str, Any],
    *,
    payload_kind: str | None = None,
    payload_format: str | None = None,
    payload_metadata: dict[str, Any] | None = None,
    tool_call: dict[str, Any] | None = None,
    tool_schema: dict[str, Any] | None = None,
) -> bool | None:
    return None
```

Routing order should be:

1. ask available tools `can_handle_tool_call(...)`
2. first `True` wins
3. `False` means explicit rejection
4. `None` means no opinion / allow fallback
5. fallback routing remains name-based for older implementations

This makes tool name optional for newer paths while retaining compatibility.

### Metadata readers

Any internal code that reads raw `metadata["tool_calls"]` dicts directly should be migrated to registry/accessor-based helpers.

Stored tool-call metadata may continue to use provider-native or tool-native shapes, but readers in core/app should not assume a particular dict structure.

At minimum, review and update:

- core execution paths
- app preview generation
- provider extensions that read tool-call objects directly
- tests/docs that encode chat-function-only assumptions

### Migration / backward compatibility strategy

This task is allowed to refactor provider/core assumptions heavily, but should preserve existing tool plugins where practical.

Compatibility target:

- existing tool plugins that emit OpenAI chat-completions function schemas and consume dict payloads should continue to work unchanged
- provider-side and core-side assumptions may change substantially
- wrapper/adaptor compatibility should absorb the legacy execution signatures

Do not require a repo-wide tool-plugin rewrite just to land the interop architecture.

### Implementation phases

#### Phase 1: Interop composition and contracts

- Add `ToolInteropContribution`
- Add effective registry composition with precedence tiers
- Add `priority` support on accessors/adapters
- Add provider/tool contribution hooks
- Add provider capability hooks for accepted/emitted formats

#### Phase 2: Accessor and adapter generalization

- Expand accessor interfaces to expose payload/payload-kind/payload-format/payload-metadata
- Add stable `format_id` support from the start
- Refactor conversion helpers so explicit adapters are additive
- Add adapter resolution API that can return direct or composed adapters

#### Phase 3: Core execution refactor

- Replace direct `OpenAIChatToolSchemaAccessor` / `OpenAIChatToolCallAccessor` usage in core/app
- Build and use effective registries per config/request
- Route all schema/call inspection through accessors
- Keep name-based matching only as fallback behavior

#### Phase 4: Tool API evolution

- Add payload-first execution/preview/stream support
- Add optional `can_handle_tool_call(...)`
- Update wrapper/adaptor layer to preserve legacy dict-argument tools

#### Phase 5: Provider adoption

- Update Responses providers/extensions first
- Make schema injection format-neutral
- Make emitted tool-call parsing format-neutral
- Preserve clear failure behavior when no compatible adapter path exists
- Keep chat providers function-only unless they explicitly support broader formats

#### Phase 6: Tests, docs, and migration cleanup

- Add unit tests for registry composition, priority, additive fallback, direct conversion, and multihop composition
- Add integration tests for payload-first execution and `can_handle_tool_call(...)` routing
- Add regression tests proving legacy chat-style tools still work unchanged
- Update docs to describe the final interop model clearly and remove chat-function-only assumptions where no longer valid

### Minimum test matrix

The finished work for this task should include tests for:

- registry composition order: explicit > contributed > default
- accessor priority ordering
- additive fallback when explicit adapters do not handle a format
- direct schema/call conversion
- multihop adapter composition
- provider accepted-format negotiation
- legacy OpenAI-chat-style tool plugins continuing to work unchanged
- payload-first tool receiving string/text payload correctly
- `can_handle_tool_call(...)` routing winning over legacy name matching
- fallback name-based routing continuing to work
- clear failure when no compatible adapter path exists

### Important non-goals for this task

Do not turn this task into final `apply_patch` parity work.

This task should deliver the architecture prerequisite only:

- format-extensible tool interop
- payload-first execution semantics
- provider capability negotiation
- additive accessors/adapters with fallback and composition

The actual `apply_patch` parity implementation remains in:

- `tasks/20260225-codex-tools-parity/013-apply-patch-true-parity.md`

### References to keep in mind while implementing

Current hardcoded assumptions to remove:

- `core/python/agent_core/core.py:2748-2809`
- `core/python/agent_app/tool_loop.py:96-169`
- `core/python/agent_core/types.py:1157-1242`
- `core/python/agent_core/plugin/tool.py`
- `core/python/agent_core/plugin/adapters.py`

Current interop layer starting point:

- `core/python/agent_core/tool_interop.py:81-343`
- `core/python/tests/test_tool_interop.py`

Current provider-side conversion assumptions to refactor:

- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_tools_extension.py:277-304`
- `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_tools_extension.py:65-80`
- `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py:220-228`

Upstream behavior motivating this task:

- `../codex/codex-rs/core/src/tools/handlers/apply_patch.rs:65-103`
- `../codex/codex-rs/core/src/tools/handlers/apply_patch.rs:288-389`

The upstream Rust design is not a one-to-one implementation target, but it is a useful proof point that a tool handler can support both structured function payloads and raw/custom payloads without forcing everything through one schema/call convention.