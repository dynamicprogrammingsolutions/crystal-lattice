# Add GPT-5.6 Programmatic Tool Calling

Add opt-in OpenAI Responses Programmatic Tool Calling support for bounded, read-only workflows while preserving caller linkage, native history, tool-loop safety, and separate API versus ChatGPT behavior.

## Requirements checklist

- [ ] Verify the supported OpenAI Python SDK version and API request/response contract before implementation.
- [ ] Verify the interceptor capability task `tasks/20260717-tool-call-interceptor-capability.md` is complete (prerequisite).
- [ ] Add opt-in Programmatic Tool Calling configuration, disabled by default.
- [ ] Require an explicit allowlist of tools eligible for programmatic invocation.
- [ ] Add `programmatic_tool_calling` and per-tool `allowed_callers` request shaping.
- [ ] Add regex-based model gating (`PROGRAMMATIC_TOOL_CALLING_MODEL_PATTERNS`) covering GPT-5.6 and future GPT-5.x/6+ models.
- [ ] Preserve `caller` from program-issued function calls through tool interop, execution, session history, and returned function outputs.
- [ ] Preserve and expose `program` and `program_output` response items without conflating them with the final assistant message.
- [ ] Enforce read-only eligibility and bounded execution limits via a provider-specific interceptor (plugs into the generic interceptor capability defined in `tasks/20260717-tool-call-interceptor-capability.md`).
- [ ] Preserve existing direct tool calling and older-model behavior.
- [ ] Add focused core, provider, application tool-loop, persistence, and regression tests.
- [ ] Add a separate real OpenAI API GPT-5.6 integration test.
- [ ] Add a separate saved-login ChatGPT integration test and run it with credentials from `~/.crystal`.
- [ ] Update OpenAI Responses documentation with supported use cases, security constraints, configuration, and limitations.
- [ ] Report unavailable or rejected API/ChatGPT credentials as not-run verification with the exact reason.

Parent Task: `tasks/20260713-openai-responses-gpt-5-6-support/000-main.md`

## Feature summary

Programmatic Tool Calling allows GPT-5.6 to generate JavaScript that OpenAI runs
inside an isolated hosted V8 environment. The program can call eligible
client-owned function tools, process several tool results in code, and return a
compact `program_output`.

The hosted runtime executes only model-generated JavaScript. Client-owned tools
remain local to this framework:

1. The model emits a `program` item.
2. The hosted program reaches a client-owned function tool.
3. OpenAI emits a normal `function_call` item with a `caller` object linking it
   to the program.
4. This framework executes the tool.
5. The framework returns a `function_call_output` with the original `call_id`
   and the identical `caller`.
6. OpenAI resumes the hosted program.
7. The program eventually emits `program_output`.
8. The model may then emit a separate final assistant message.

Representative request shape:

```json
{
  "model": "gpt-5.6-sol",
  "tools": [
    {
      "type": "programmatic_tool_calling"
    },
    {
      "type": "function",
      "name": "lookup_records",
      "description": "Return matching records.",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {"type": "string"}
        },
        "required": ["query"],
        "additionalProperties": false
      },
      "strict": true,
      "allowed_callers": ["direct", "programmatic"]
    }
  ]
}
```

Representative program-issued tool call:

```json
{
  "type": "function_call",
  "call_id": "call_123",
  "name": "lookup_records",
  "arguments": "{\"query\":\"example\"}",
  "caller": {
    "type": "program",
    "caller_id": "program_123"
  }
}
```

Required tool output:

```json
{
  "type": "function_call_output",
  "call_id": "call_123",
  "caller": {
    "type": "program",
    "caller_id": "program_123"
  },
  "output": "{\"records\":[]}"
}
```

## Appropriate scope

Good candidates:

- bounded read-only filtering, joining, sorting, ranking, and deduplication;
- batching many similar records;
- repeated deterministic validation;
- map/reduce-style retrieval;
- reducing large structured intermediate results to a compact schema.

Poor candidates:

- a single direct tool call;
- write or side-effecting tools;
- approval-gated operations;
- workflows where each result requires model judgment before the next call;
- citation-heavy or native-artifact flows;
- open-ended agent behavior;
- workflows where intermediate reasoning and results must remain visible to the
  user.

Programmatic Tool Calling must not be enabled globally merely because a model
supports it. The implementation should require a bounded use case and explicit
tool eligibility.

## Official constraints

Research sources:

- `https://developers.openai.com/api/docs/guides/tools-programmatic-tool-calling`
- `https://openai.com/index/gpt-5-6/`

Current documented constraints:

- only GPT-5.6 models support the feature;
- only the Responses API supports it;
- the hosted JavaScript runtime has no filesystem or network access;
- the runtime has a five-second execution limit;
- client-owned function tools require `allowed_callers` containing
  `programmatic`;
- hosted tools such as web search and file search cannot be called from the
  program;
- program-issued calls include `caller.type == "program"` and a program
  `caller_id`;
- the same caller must be returned on `function_call_output`;
- a program can issue multiple calls before the program completes;
- `program_output` and the final assistant message are separate outputs and
  must both be validated;
- a program may be incomplete and may expose an error.

Recheck the live official documentation during implementation because this is a
new API surface and fields may evolve.

## Current framework findings

Relevant code:

- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_tools_extension.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
- `core/python/agent_core/tool_interop.py`
- `core/python/agent_core/core.py`
- `core/python/agent_app/tool_loop.py`
- `plugins/openai_responses/tests/test_openai_responses_tools_extension_unit.py`
- `plugins/openai_responses/tests/test_openai_responses_tools_extension_integration.py`
- `plugins/openai_responses/tests/test_openai_responses_native_history_regressions.py`

Capabilities already present:

- Responses-native function schemas and function calls;
- provider-native history retention;
- streaming and non-streaming response item accumulation;
- execution of multiple function calls from one assistant response;
- repeated LLM/tool phases;
- tool-result persistence and checkpointing;
- configurable maximum outer tool-loop depth;
- conversion between OpenAI Responses calls and core-compatible tool calls.

Identified gaps:

1. The tools extension does not inject
   `{"type": "programmatic_tool_calling"}`.
2. Converted function schemas do not expose `allowed_callers`.
3. The Responses function-call accessor currently exposes only call ID, name,
   arguments, and existing internal metadata.
4. The Responses-to-chat tool-call adapter drops the top-level `caller`.
5. Core tool-result messages do not automatically carry caller metadata from
   the initiating call.
6. Provider conversion of a core tool message emits only `call_id` and
   `output`, not `caller`.
7. `program` and `program_output` items remain in native history as unknown or
   orphan items but are not exposed as structured assistant metadata.
8. There is no programmatic-tool allowlist or read-only policy.
9. The current outer loop limits LLM/tool phases but does not separately cap the
   number of program-issued calls in one phase.
10. The installed Crystal runtime used during research had `openai 2.32.0`,
    whose generated Responses types did not include Programmatic Tool Calling.

## OpenAI SDK findings

The plugin currently declares:

```toml
openai>=2.0.0
```

The provider calls:

```python
client.responses.create(**payload, ...)
```

The installed `openai 2.32.0` generated tool union did not contain
`programmatic_tool_calling`, `program`, or `program_output`.

The current upstream `openai-python` main branch inspected on July 16, 2026 was
version `2.45.0` and included:

- `ProgrammaticToolCalling`;
- function-tool `allowed_callers`;
- response `program` and `program_output` item types;
- response function-call `caller` types.

Implementation must determine the first released SDK version that contains the
required generated types.

Preferred approach:

1. Raise the plugin dependency to the first released compatible version.
2. Use the generated SDK types and normal `responses.create` path.

Fallback approach:

- use narrowly scoped `extra_body` handling only if a compatible released SDK
  cannot be used;
- do not move the entire request to untyped raw JSON merely for this feature;
- add tests proving ordinary Responses requests remain on the existing path.

## Codex findings

Latest inspected Codex upstream:

```text
03bb3b12367397e14a8facc2e018d645ff4d8e83
2026-07-16T09:00:51Z
```

Codex contains migration and prompting guidance for Programmatic Tool Calling,
including:

- request-shape examples;
- preserving `call_id` and `caller`;
- limiting usage to bounded read-only stages;
- validating both `program_output` and the final assistant message;
- comparing tokens, latency, cost, calls, turns, and retries against direct
  calling.

The inspected production Codex request and tool-loop code did not yet implement
the `programmatic_tool_calling`, `program`, `program_output`, or caller-linkage
flow. Codex is therefore a design/reference source for this task, not an
implementation to copy.

## Proposed configuration

Programmatic Tool Calling must be disabled by default.

Suggested keys:

```json
{
  "enable_programmatic_tool_calling": false,
  "programmatic_tool_names": [
    "lookup_records",
    "get_record_details"
  ],
  "programmatic_tool_caller_policy": "direct_and_programmatic",
  "programmatic_max_calls_per_phase": 20
}
```

Configuration semantics:

- `enable_programmatic_tool_calling`
  - adds the built-in Programmatic Tool Calling tool only for supported
    GPT-5.6 models;
  - default `false`.
- `programmatic_tool_names`
  - required non-empty allowlist when enabled;
  - names must resolve to active function tools;
  - custom/freeform tools are out of scope for the first implementation.
- `programmatic_tool_caller_policy`
  - `programmatic_only` emits `["programmatic"]`;
  - `direct_and_programmatic` emits `["direct", "programmatic"]`;
  - default should preserve direct-call compatibility.
- `programmatic_max_calls_per_phase`
  - application-side safety limit for calls emitted by one program response;
  - excess calls should return a clear bounded error rather than execute.

Do not infer read-only safety from a tool name. The allowlist is an explicit
operator decision. If the framework later gains general tool capability
metadata such as read-only/side-effecting, this feature may validate against it,
but adding that global protocol is not required for the first implementation.

## Implementation outline

### 1. SDK and capability validation

- Identify the minimum compatible `openai-python` release.
- Update `plugins/openai_responses/pyproject.toml`.
- Confirm GPT-5.6 model gating for explicit family IDs and any supported bare
  alias.
- Verify API and ChatGPT endpoint behavior independently.

### 2. Request schema shaping

Update `OpenAIResponsesToolsExtension.initialize_request(...)`:

- convert ordinary active tools as today;
- validate configured allowlist names;
- add `allowed_callers` only to eligible function schemas;
- keep unselected tools direct-only;
- append exactly one top-level
  `{"type": "programmatic_tool_calling"}` entry;
- avoid duplicate injection when raw request options already contain the
  built-in tool;
- reject unsupported model/tool combinations with actionable errors.

Keep this OpenAI Responses-specific. Do not add Programmatic Tool Calling to
generic core tool schemas or unrelated providers.

### 3. Caller-preserving tool interop

Extend the Responses function-call path so `caller` survives:

```text
native function_call
  -> inspected call payload metadata
  -> converted/core tool call metadata
  -> tool execution
  -> core tool-result metadata
  -> native function_call_output
```

Requirements:

- preserve the exact caller object without mutation;
- preserve direct/null caller behavior;
- do not let tools overwrite core-managed caller metadata;
- preserve caller through streaming, non-streaming, save/reload, rebuild, and
  provider switching safeguards;
- return caller only where the target provider format supports it.

The cleanest likely approach is:

1. Have `OpenAIResponsesFunctionCallAccessor.get_payload_metadata(...)` expose
   caller as provider-specific metadata.
2. Preserve that metadata in the Responses-to-core call adapter.
3. Merge initiating-call payload metadata into final core tool-message metadata
   in `AgentCore.iter_tool_messages(...)`.
4. Have the OpenAI Responses provider/tools extension copy caller to
   `function_call_output`.

Any core change must remain provider-neutral and regression-tested with direct
tool calls and other providers.

### 4. Program item preservation and observability

Preserve native items exactly:

- `program`;
- program-issued `function_call`;
- `function_call_output`;
- `program_output`;
- final assistant `message`.

Expose useful assistant metadata without replacing native history, for example:

```json
{
  "metadata": {
    "openai_responses_programmatic_tool_calling": {
      "programs": [],
      "program_outputs": []
    }
  }
}
```

Preserve at least:

- program item ID;
- code;
- status;
- error when present;
- program output text/value;
- native indices;
- response ID.

The final assistant `content` must continue to come from the assistant message,
not from `program_output`. Program output is diagnostic/intermediate structured
state.

### 5. Application tool-loop safeguards

The current `ToolLoopRunner` can execute several emitted calls and resume the
model. Extend it or a provider-owned policy hook to:

- identify calls with `caller.type == "program"`;
- reject programmatic calls to tools outside the allowlist;
- enforce `programmatic_max_calls_per_phase`;
- preserve caller on both success and synthesized error tool results;
- count each resume toward existing maximum tool-loop depth;
- cancel cleanly during a batch;
- checkpoint only valid native/core history.

Sequential execution is acceptable for the first implementation. Parallel
execution of independent program-issued calls is explicitly follow-up scope.

### 6. Error behavior

Cover:

- unknown programmatic tool;
- disabled or empty allowlist;
- selected non-function/custom tool;
- programmatic call to a direct-only tool;
- malformed or missing caller;
- caller referencing an unknown program item;
- excessive calls in one phase;
- tool execution failure;
- incomplete program;
- program error;
- missing `program_output`;
- completed program output followed by an incomplete or incorrect final message.

Return tool execution errors to the program as normal function outputs with the
original caller where possible. Provider/protocol errors that prevent safe
continuation should terminate the request with a clear application error.

## Test plan

### Unit tests

`core/python/tests/test_tool_interop.py` or focused new core tests:

- Responses function call accessor captures caller;
- conversion preserves caller metadata;
- direct calls remain unchanged;
- malformed callers are handled predictably.

`plugins/openai_responses/tests/test_openai_responses_tools_extension_unit.py`:

- feature disabled produces the existing tool payload;
- enabled GPT-5.6 request adds the built-in tool once;
- allowlisted tools receive correct `allowed_callers`;
- unselected tools remain direct-only;
- unsupported models reject or omit according to documented policy;
- raw request tool entries are not duplicated;
- `function_call_output` includes exact caller.

Provider tests:

- streaming and non-streaming fixtures with:
  - `program`;
  - multiple program-issued function calls;
  - caller-linked outputs;
  - `program_output`;
  - final assistant message;
- incomplete/error program items;
- native history and `native_indices` preservation;
- save/reload and rebuild round trip.

### Application tool-loop tests

Add a deterministic integration-style unit test using read-only fixture tools:

1. Script the provider to emit a program and several caller-linked calls.
2. Execute the calls through the real `ToolLoopRunner`.
3. Assert every output carries the original caller.
4. Resume the scripted provider.
5. Emit and preserve `program_output`.
6. Emit a separate final assistant response.
7. Verify checkpoints, event order, and final session history.

Add safety tests for allowlist violations, call limits, cancellation, and tool
errors.

### Real OpenAI API integration

- Gate on `OPENAI_API_KEY`.
- Use a GPT-5.6 model and deterministic read-only fixture tools.
- Ask for a bounded aggregation/filtering result that requires multiple tool
  calls.
- Assert at least one `program` item.
- Assert program-issued calls contain caller.
- Assert returned outputs preserve caller.
- Assert a `program_output` item exists.
- Assert the final assistant response is correct independently of program
  output.
- Compare basic call/turn/token metadata with a direct-calling baseline where
  practical.

### ChatGPT saved-login integration

- Add a separate test rather than parametrizing the API test.
- Use:

  ```bash
  CHATGPT_TEST_STATE_DIR="$HOME/.crystal" \
  OPENAI_RESPONSES_CHATGPT_MODEL="gpt-5.6-luna" \
    pytest <chatgpt-programmatic-tool-calling-test> \
      -m "manual_integration and integration and openai" -q
  ```

- Resolve credentials from
  `$CHATGPT_TEST_STATE_DIR/auth/chatgpt-auth.json`.
- Record and validate the outgoing tool schemas.
- Assert whether the ChatGPT backend accepts Programmatic Tool Calling.
- If accepted, verify the complete caller-linked loop.
- If rejected, report exact status/error and document the endpoint difference.
- Do not count missing credentials or a skipped test as successful
  verification.
- Do not print credential or account values.

## Documentation requirements

Update `plugins/openai_responses/README.md` with:

- feature overview;
- supported models/endpoints;
- disabled-by-default behavior;
- configuration keys;
- allowlist and read-only security guidance;
- caller preservation;
- program versus final assistant output;
- execution and call limits;
- API versus ChatGPT support status;
- example request/tool configuration;
- troubleshooting for malformed caller, unsupported tools, and endpoint
  rejection.

If public core/tool interop behavior changes, update the relevant tool interop
and protocol documentation as required by the repository guidelines.

## Completion verification

Suggested focused commands:

```bash
pytest core/python/tests/test_tool_interop.py -q
pytest plugins/openai_responses/tests/test_openai_responses_tools_extension_unit.py -q
pytest plugins/openai_responses/tests/test_openai_responses_tools_extension_integration.py -q
pytest plugins/openai_responses/tests/test_openai_responses_native_history_regressions.py -q
pytest application/python/tests -k "programmatic_tool_calling" -q
```

Then run the dedicated real API and ChatGPT tests with their gates explicitly
enabled. Record skipped credential-gated tests as not run.

## Execution plan

(Approved 2026-07-17. Implementation proceeds in the order below. This plan was
added during completion and is the authoritative scope for the work.)

### A. SDK compatibility approach

**Minimum compatible SDK release: `openai==2.45.0`** (released 2026-07-09).

Verification performed during planning:

- `openai==2.44.0` does NOT contain `ProgrammaticToolCalling`, `allowed_callers`,
  `Program`, or `ProgramOutput` in any namespace.
- `openai==2.45.0` is the first released version that contains all required
  generated types in the non-beta `openai.types.responses` namespace:
  - `openai.types.responses.tool_param.ProgrammaticToolCalling`
    (`TypedDict` with `type: Required[Literal["programmatic_tool_calling"]]`)
  - `openai.types.responses.function_tool_param.FunctionToolParam.allowed_callers`
    (`Optional[List[Literal["direct", "programmatic"]]]`)
  - `openai.types.responses.response_function_tool_call.ResponseFunctionToolCall.caller`
    (`Optional[Union[CallerDirect, CallerProgram, None]]` with discriminator
    `type`)
  - `openai.types.responses.response_input_item_param.FunctionCallOutput.caller`
    (`Optional[FunctionCallOutputCaller]`)
  - `openai.types.responses.response_input_item_param.Program`
    (`id`, `call_id`, `code`, `fingerprint`, `type: Literal["program"]`)
  - `openai.types.responses.response_input_item_param.ProgramOutput`
    (`id`, `call_id`, `result`, `status`, `type: Literal["program_output"]`)
  - `openai.types.responses.response_input_item.Program` (BaseModel)
  - `openai.types.responses.response_input_item.ProgramOutput` (BaseModel)
- `openai==2.46.0` (latest at planning time) also contains them; the
  `beta` namespace mirrors them but is not required.

**Decision: raise the plugin dependency, do not use `extra_body`.**

- `plugins/openai_responses/pyproject.toml`: bump `openai>=2.0.0` to
  `openai>=2.45.0`.
- The provider already calls `client.responses.create(**payload, ...)`. Because
  `payload` is a plain `dict`, the SDK's `**payload`-based call path accepts the
  new `tools` entries and the new `caller` field on `function_call_output`
  without code changes. No `extra_body` is required.
- Add a guard test that imports `ProgrammaticToolCalling` from
  `openai.types.responses.tool_param` so a future SDK regression is caught.
- Do not move the entire request to untyped raw JSON. Add a unit test that
  proves ordinary Responses requests (no programmatic tool calling) remain on
  the existing `responses.create(**payload, ...)` path with the same payload
  shape as today.

Fallback (`extra_body`) is explicitly rejected for this task because the
generated SDK types are available in a released version; the fallback exists in
the task description only in case the SDK had not yet shipped the types.

### B. Opt-in configuration

New provider config keys (added to `OpenAIResponsesProvider.get_config_schema`
and documented in the README), all disabled by default:

| Key | Type | Default | Semantics |
| --- | --- | --- | --- |
| `enable_programmatic_tool_calling` | bool | `false` | Adds `{"type": "programmatic_tool_calling"}` to `tools` and enables `allowed_callers` injection. Only takes effect for supported models (see section D). |
| `programmatic_tool_names` | list[str] | `[]` | Required non-empty allowlist when enabled. Names must resolve to active `function` tools. Custom/freeform tools are out of scope for the first implementation and are rejected. |
| `programmatic_tool_caller_policy` | string | `"direct_and_programmatic"` | `programmatic_only` emits `["programmatic"]`; `direct_and_programmatic` emits `["direct", "programmatic"]`. Default preserves direct-call compatibility. |
| `programmatic_max_calls_per_phase` | integer | `20` | Application-side safety limit on program-issued calls in one LLM phase. Excess calls return a bounded error result instead of executing. |

Semantics and validation:

- `enable_programmatic_tool_calling=true` with an empty
  `programmatic_tool_names` is a configuration error; the tools extension raises
  an actionable error at `initialize_request` time.
- Names in `programmatic_tool_names` that do not resolve to an active
  `function` tool are a configuration error.
- Custom/freeform tools in `programmatic_tool_names` are rejected with a clear
  error (first implementation is function-only).
- The allowlist is an explicit operator decision. The framework does not infer
  read-only safety from tool names. Automatic classification is out of scope.
- The keys live under the provider config (not a separate feature plugin) so
  the tools extension can read them from `state["config"]` during
  `initialize_request` without a new plugin dependency.

### C. Request schema shaping

Owned by `OpenAIResponsesToolsExtension.initialize_request` (provider-specific;
no core change). The current method already converts active tools via the
interop registry and sets `payload["tools"]` and `payload["tool_choice"]`.
Extend it:

1. Read `state["config"]` for the four keys above. If
   `enable_programmatic_tool_calling` is false or absent, behavior is unchanged.
2. Model gating (see section H.9): if the resolved model does not match any
   pattern in `PROGRAMMATIC_TOOL_CALLING_MODEL_PATTERNS`, raise an actionable
   error rather than silently omitting the tool. The patterns assume future
   GPT-5.x (x >= 6) and GPT-6+ models DO support the feature; see H.9 for the
   exact patterns.
3. Validate `programmatic_tool_names` is a non-empty list of strings and that
   each name resolves to an active `function` tool (not `custom`). Reject
   duplicates and names that resolve to custom/freeform tools.
4. After the registry converts schemas to the `openai.responses` target, walk
   the converted list and add `allowed_callers` to each allowlisted function
   tool:
   - `programmatic_only` -> `["programmatic"]`
   - `direct_and_programmatic` -> `["direct", "programmatic"]`
   - Non-allowlisted function tools are left unchanged (they remain direct-only
     by omission).
5. Append exactly one top-level
   `{"type": "programmatic_tool_calling"}` entry to `payload["tools"]`.
6. De-duplicate: if `payload["tools"]` already contains an entry with
   `type == "programmatic_tool_calling"` (e.g. a caller passed a raw request
   override), do not append a second one. This keeps raw request overrides
   authoritative.
7. Reject unsupported combinations with actionable errors:
   - enabled with empty allowlist;
   - enabled with a non-function tool in the allowlist;
   - enabled with an allowlist name that does not resolve to any active tool;
   - enabled with an unsupported model.

This shaping is OpenAI Responses-specific. Do not add `programmatic_tool_calling`
or `allowed_callers` to generic core tool schemas or unrelated providers.

### D. Caller preservation

The `caller` object must survive the full round trip:

```
native function_call
  -> inspected call payload_metadata (interop)
  -> converted/core tool call metadata (adapter)
  -> tool execution (core)
  -> core tool-result metadata (core)
  -> native function_call_output (provider)
```

Layer-by-layer ownership:

1. **Generic tool interop (`agent_core/tool_interop.py`)** — provider-neutral
   extension of existing accessors/adapters:
   - `OpenAIResponsesFunctionCallAccessor.get_payload_metadata`: in addition to
     `call.get("_metadata")`, also extract `call.get("caller")` and return it
     under a stable key `openai_responses_caller` in the returned metadata
     dict. Only include it when `caller` is a dict (or `None` for direct calls).
     Do not mutate the original call.
   - `OpenAIResponsesToolCallToOpenAIChatToolCall.convert`: after producing the
     chat-completions shape, copy `openai_responses_caller` from the inspected
     payload metadata into the converted call's `_metadata` (or a dedicated
     `caller` key on the converted dict). The chat-completions `function` shape
     has no `caller` field, so the caller rides through `_metadata`. This
     preserves the existing adapter contract (the converted call is still a
     valid chat-completions tool call) while keeping caller available for the
     reverse path.
   - `OpenAIResponsesCustomToolCallAccessor.get_payload_metadata`: unchanged
     for now (custom/freeform tools are out of scope for programmatic
     invocation in the first implementation).

   Why interop: caller is a provider-specific concept that must be carried
   alongside the call without breaking the chat-completions format contract.
   Keeping it in `payload_metadata` is the existing extension point for
   provider-specific call metadata.

2. **Core tool-result handling (`agent_core/core.py` `iter_tool_messages`)** —
   provider-neutral merge:
   - After building the `metadata` dict for a tool message, merge
     `inspected_call.payload_metadata` into it using the exact sequence:
     1. Set core-managed keys (`tool_call_id`, `tool_name`, `tool_schema`,
        `tool_plugin`, `display`).
     2. Merge `inspected_call.payload_metadata` with `if key not in metadata`
        (never overwrites core-managed keys).
     3. Merge `result_metadata` (tool-supplied, from
        `last_result["metadata"]`) with `if key not in metadata` (cannot
        overwrite core-managed keys OR `payload_metadata` keys).
   - This gives `payload_metadata` priority over `result_metadata` for
     non-core-managed keys, so `openai_responses_caller` from the initiating
     call cannot be overwritten by a tool that also returns
     `metadata["openai_responses_caller"]`.
   - This is the single place where initiating-call payload metadata reaches
     the tool-result message, so the provider's reverse conversion can read
     it back.
   - The merge is provider-neutral: only keys that do not collide with
     core-managed keys are copied. Existing direct-call behavior (no caller
     metadata) is unchanged because `payload_metadata` is empty for direct
     calls.

   Why core: `iter_tool_messages` is the only place that has both the
   initiating `inspected_call` and the final tool message in scope. Putting the
   merge here keeps the contract provider-neutral and regression-testable with
   direct calls and other providers.

3. **OpenAI Responses provider (`openai_responses_provider.py`)** — reverse
   conversion:
   - `to_native_messages` (the `role == "tool"` branch): when building the
     `function_call_output` item, read `openai_responses_caller` from the core
     tool message metadata (via `internal_md`) and, if present and a dict,
     add it as the top-level `caller` field on the
     `function_call_output` item. If absent, omit `caller` (preserves
     direct-call behavior).
   - `from_native_messages`: when reading a native `function_call_output`
     item, copy its top-level `caller` (if present) into the core tool message
     metadata under `openai_responses_caller`, so save/reload and rebuild
     preserve it. There are **two** code locations that build a tool message
     from a `function_call_output` item; both need the caller read:
     - `_flush_response_segment` (line ~1922-1972): read `caller` from the
       `function_call_output` item and add to `tool_md["openai_responses_caller"]`.
     - Main loop `item_type == "function_call_output"` branch (line
       ~2053-2101): same.
   - `_native_internal_from_core_metadata`: do not strip
     `openai_responses_caller` (it is not in the existing pop list and must
     survive the round trip).
   - **Key name lock-in**: use `openai_responses_caller` (no leading
     underscore). `_core_metadata_from_native_internal` (line 908) strips
     keys matching `_openai_responses_*` (with leading underscore); the chosen
     key does not match that pattern and survives the native→core round trip.
     Do not "fix" it to `_openai_responses_caller` — that would be stripped.

   Why provider: the `function_call_output.caller` field is Responses-specific.
   The provider is the only layer that knows whether the target wire format
   supports `caller`.

4. **Tools extension (`openai_responses_tools_extension.py`)** —
   `to_native_messages` tool branch: when re-adding `tool_plugin`,
   `tool_name`, `display` into `_metadata`, also preserve
   `openai_responses_caller` if it is present in the core tool message
   metadata. This matches the existing pattern for `display` and keeps caller
   intact across native-history rebuilds.

Requirements (from the task):

- Preserve the exact caller object without mutation (copy by reference; do not
  deep-copy).
- Preserve direct/null caller behavior (no `caller` field emitted for direct
  calls).
- Do not let tools overwrite core-managed caller metadata (the merge in
  `iter_tool_messages` is one-directional: `payload_metadata` is the
  initiating-call source of truth; tool-supplied `last_result["metadata"]`
  cannot overwrite `openai_responses_caller`).
- Preserve caller through streaming, non-streaming, save/reload, rebuild, and
  provider switching safeguards. The save/reload path is covered by
  `from_native_messages` reading `caller` from the native
  `function_call_output` item; the rebuild path is covered by the tools
  extension re-adding it to `_metadata`.
- Return caller only where the target provider format supports it. The
  provider's `to_native_messages` is the only place that emits `caller` on the
  wire, and it only does so for the Responses format.

### E. Program item handling and observability

Today, `program`/`program_output` items are already part of the assistant
segment (via `response_id` in `_metadata`, stamped by
`_attach_internal_metadata_to_output` at line ~2358-2384) and their indices
are included in `native_indices`, but they are not exposed as structured
assistant metadata. The hook point for metadata exposure is
`_build_response_segment_assistant` (line ~1626), not the orphan-handling
block at lines ~2105-2130.

1. **Native history preservation**: `program`, program-issued
   `function_call`, `function_call_output`, and `program_output` items are
   already preserved in native history because the provider stores all
   `output` items. No change to native storage is required. However,
   `_sanitize_input_item` (line ~2150) currently strips `id`, `status`,
   `namespace`, `phase` from every non-compaction item, which would corrupt
   `program` and `program_output` items (the SDK 2.45.0 source confirms
   `Program.id` and `ProgramOutput.id`/`status` are required fields). Fix
   this explicitly:
   - Add a new constant `_PASSTHROUGH_ITEM_TYPES = {"program", "program_output"}`
     near `_COMPACTION_ITEM_TYPES` (line ~109).
   - Add an early-return branch in `_sanitize_input_item` for
     `item_type in _PASSTHROUGH_ITEM_TYPES` that returns the item with only
     `_metadata` stripped (no `id`/`status`/`namespace`/`phase` removal, no
     content cleaning).
   - Verify that `code`, `fingerprint`, `caller`, `call_id`, and `result`
     survive the round trip.

2. **Assistant metadata exposure**: in `_build_response_segment_assistant`
   (and the non-segmented `from_native_messages` path), when a segment contains
   `program` or `program_output` items, attach a structured metadata block to
   the owning assistant message:
   ```json
   {
     "metadata": {
       "openai_responses_programmatic_tool_calling": {
         "programs": [
           {
             "id": "prog_123",
             "call_id": "call_prog_123",
             "code": "<js source>",
             "fingerprint": "<opaque>",
             "status": "completed",
             "error": null,
             "native_index": 4,
             "response_id": "resp_123"
           }
         ],
         "program_outputs": [
           {
             "id": "prog_out_123",
             "call_id": "call_prog_123",
             "result": "<json string>",
             "status": "completed",
             "native_index": 7,
             "response_id": "resp_123"
           }
         ]
       }
     }
   }
   ```
   Preserve at least: program item ID, code, status, error when present,
   program output text/value, native indices, response ID.

3. **Final assistant content**: the final assistant `content` must continue to
   come from the assistant `message` item, not from `program_output`.
   `program_output.result` is diagnostic/intermediate structured state. The
   existing `_assistant_candidate_from_response_item` already only builds
   candidates from `type == "message"` items, so this is preserved by
   construction. Add a regression test that a segment containing
   `program_output` without a final `message` does not surface
   `program_output.result` as the assistant content.

4. **Incomplete program**: if a `program` item has `status == "incomplete"` or
   an error, record it in the metadata block and surface a clear diagnostic.
   Do not raise from `from_native_messages`; the application tool loop is
   responsible for deciding whether to continue (see section F).

### F. Bounded tool-loop behavior

The allowlist enforcement and per-phase call limit are provider-specific
policy decisions. They are implemented as a provider-specific interceptor
that plugs into the generic interceptor capability defined in the separate
task `tasks/20260717-tool-call-interceptor-capability.md`.

**Prerequisite**: the interceptor capability task must be complete before
this task's implementation. The capability task defines:
- a generic interceptor protocol with pre-execution and post-execution hooks;
- `ToolLoopRunner`'s thin-orchestrator hook (consults interceptors before
  and after each tool call; applies decisions; copies `payload_metadata`
  into short-circuited results; maintains a per-phase state object);
- `AgentApplication`'s per-request discovery of interceptors from the
  active provider's extensions (provider-scoped).

The exact protocol shape (class names, method names, dataclass shapes) is
defined by the interceptor capability task; this task does not prescribe them.

This task only implements the provider-specific interceptor and registers it
via the discovery mechanism defined by the interceptor capability task.

#### F.1 Provider-specific interceptor

A provider-specific interceptor in the OpenAI Responses plugin implements
the generic interceptor protocol from the interceptor capability task. It
implements the pre-execution hook only; the post-execution hook is a no-op
(returns no opinion).

Pre-execution hook logic:

1. Read `enable_programmatic_tool_calling`, `programmatic_tool_names`,
   `programmatic_max_calls_per_phase` from `config`.
2. If `enable_programmatic_tool_calling` is false, return no opinion (the
   call is direct and executes normally).
3. If `inspected_call is None`, return no opinion (malformed call; let the
   loop handle it via the existing "no tool handled" synthesis).
4. Inspect `inspected_call.payload_metadata` for `openai_responses_caller`.
   If absent or `caller.type != "program"`, return no opinion (the call is
   direct; the interceptor does not apply).
5. The call is programmatic. Check `inspected_call.tool_name` against
   `programmatic_tool_names`:
   - If not in the allowlist, return a short-circuit decision with an error
     result: `"Error: tool 'X' is not in the programmatic_tool_names allowlist"`.
6. Check the per-phase counter in the per-phase state object under the
   namespaced key `openai_responses_programmatic_calls`:
   - Initialize to 0 if absent.
   - If the counter has reached `programmatic_max_calls_per_phase`, return a
     short-circuit decision with an error result:
     `"Error: programmatic_max_calls_per_phase exceeded for this LLM phase"`.
   - Otherwise increment the counter and return a proceed decision.
7. The interceptor does not touch `openai_responses_caller` directly; the
   generic `ToolLoopRunner` (per the interceptor capability task) copies
   `payload_metadata` (which contains the caller) into the short-circuited
   result's metadata, so the provider's `to_native_messages` emits `caller`
   on the `function_call_output`.

Registration: the OpenAI Responses tools extension exposes the interceptor
via the discovery mechanism defined by the interceptor capability task. The
interceptor is returned when `enable_programmatic_tool_calling` is true, else
no interceptors are returned. `AgentApplication` collects interceptors from
each active provider extension per request and passes them to `ToolLoopRunner`.

#### F.2 What stays generic vs. provider-specific

| Concern | Owner | Why |
| --- | --- | --- |
| Generic interceptor protocol | Interceptor capability task (`agent_app`) | Generic capability; any provider can implement it. |
| `ToolLoopRunner` interceptor hook | Interceptor capability task (`agent_app`) | Generic; calls interceptors, copies `payload_metadata` into short-circuited results. |
| Per-phase state object | Interceptor capability task (`agent_app`) | `ToolLoopRunner` owns it and resets it per phase; interceptors use namespaced keys. |
| Copying `payload_metadata` into short-circuited results | Interceptor capability task (`agent_app`) | Provider-neutral merge; `openai_responses_caller` rides through because it is in `payload_metadata`. |
| Provider-specific interceptor | OpenAI Responses plugin | Provider-specific; reads `programmatic_tool_names`, `programmatic_max_calls_per_phase`, checks `openai_responses_caller`. |
| Allowlist check | OpenAI Responses plugin | Reads `programmatic_tool_names`; provider-specific. |
| Per-phase call limit | OpenAI Responses plugin | Reads `programmatic_max_calls_per_phase`; provider-specific. |
| Identifying programmatic calls | OpenAI Responses plugin | Checks `openai_responses_caller` in `payload_metadata`; provider-specific. |
| `max_loops` accounting | `agent_app` (unchanged) | Existing outer-loop limit. |
| Sequential execution | `agent_app` (unchanged) | Existing loop is sequential. Parallel execution is follow-up scope. |
| Cancellation | `agent_app` (unchanged) | Existing `_is_cancelled` checks. |

### G. Ownership summary (why each layer)

| Change | Layer | Why |
| --- | --- | --- |
| Bump `openai>=2.45.0` | Plugin `pyproject.toml` | The plugin is the only consumer of the Responses SDK; the core does not import `openai`. |
| Inject `programmatic_tool_calling` tool | Plugin tools extension | The built-in tool is Responses-specific. Generic core schemas must not carry it. |
| Add `allowed_callers` to function schemas | Plugin tools extension | `allowed_callers` is a Responses-specific schema field. The core schema format is provider-neutral. |
| Model gating (regex patterns) | Plugin tools extension | Model eligibility is a Responses API constraint. The core does not know which models support which features. Patterns assume future GPT-5.x (x >= 6) and GPT-6+ models support the feature; see H.9. |
| Expose `caller` in `get_payload_metadata` | Generic tool interop | `payload_metadata` is the existing provider-neutral extension point for call-level metadata. The key name (`openai_responses_caller`) is namespaced so other providers are unaffected. |
| Preserve `caller` in the chat-completions adapter | Generic tool interop | The adapter is the boundary between Responses and chat-completions formats. Carrying caller via `_metadata` keeps the chat-completions contract intact. |
| Merge `payload_metadata` into tool-result metadata | Core `iter_tool_messages` | This is the only place with both the initiating call and the final tool message in scope. The merge is provider-neutral (only non-core-managed keys are copied). |
| Emit `caller` on `function_call_output` | Plugin provider | `caller` is a Responses wire field. The provider is the only layer that knows the target format supports it. |
| Read `caller` from native `function_call_output` | Plugin provider | Needed for save/reload and rebuild round trips. Two code locations: `_flush_response_segment` and the main loop branch. |
| Preserve `caller` in tools extension `_metadata` | Plugin tools extension | Matches the existing `display`/`tool_plugin` re-add pattern; needed for native-history rebuilds. |
| `program`/`program_output` metadata exposure | Plugin provider | The items are Responses-specific. The core has no concept of a program. |
| Final assistant content from `message`, not `program_output` | Plugin provider | Already enforced by `_assistant_candidate_from_response_item` only accepting `type == "message"`. Add a regression test. |
| Provider-specific interceptor | OpenAI Responses plugin | Provider-specific; implements the generic interceptor protocol from the interceptor capability task. Reads `programmatic_tool_names`, `programmatic_max_calls_per_phase`, checks `openai_responses_caller`. |
| Generic interceptor protocol + `ToolLoopRunner` hook | Interceptor capability task (`agent_app`) | Generic; defined in `tasks/20260717-tool-call-interceptor-capability.md`. This task depends on it. |
| Sequential execution | `agent_app` (unchanged) | The existing loop is sequential. Parallel execution is follow-up scope. |

### H. Human decisions (with recommendations)

1. **SDK upgrade vs `extra_body`**: upgrade to `openai>=2.45.0`. The generated
   types are available in a released version, so `extra_body` is not needed.
   Recommendation: accept.

2. **Configuration names/defaults**: use the four keys listed in section B with
   the listed defaults. `enable_programmatic_tool_calling` defaults to `false`.
   `programmatic_tool_names` defaults to `[]` and is required non-empty when
   enabled. `programmatic_tool_caller_policy` defaults to
   `"direct_and_programmatic"` to preserve direct-call compatibility.
   `programmatic_max_calls_per_phase` defaults to `20` (a conservative bound
   that covers typical map/reduce retrieval without allowing unbounded
   execution). Recommendation: accept.

3. **Allowlist semantics**: explicit, names-only, function-only. The framework
   does not infer read-only safety from tool names. Custom/freeform tools are
   rejected in the first implementation. Recommendation: accept.

4. **Caller policy**: preserve the exact caller object without mutation. Do not
   let tools overwrite core-managed caller metadata. Direct/null caller
   behavior is preserved (no `caller` field emitted for direct calls).
   Recommendation: accept.

5. **Call limits**: `programmatic_max_calls_per_phase` is a per-phase counter,
   reset at the start of each LLM phase. Excess calls return a bounded error
   result with the original caller (so the program can resume and exit
   cleanly). The existing `max_loops` outer-loop limit is unchanged. The limit
   is per LLM phase, not per program. A program that spans multiple phases may
   emit up to `programmatic_max_calls_per_phase` calls in each phase. The
   outer `max_loops` limit bounds the total number of phases. The theoretical
   maximum total program-issued calls is
   `max_loops × programmatic_max_calls_per_phase` (e.g., 8 × 20 = 160 with
   defaults). Operators who want a tighter total cap should lower `max_loops`
   or `programmatic_max_calls_per_phase`. The hosted runtime's 5-second
   per-invocation execution limit is the primary bound on program complexity.
   Recommendation: accept.

6. **Metadata exposure**: expose `program` and `program_output` as structured
   assistant metadata under `openai_responses_programmatic_tool_calling`. Do
   not replace native history. Do not surface `program_output.result` as
   assistant content. Recommendation: accept.

7. **Sequential execution**: program-issued calls are executed sequentially in
   the order emitted. Parallel local execution is follow-up scope.
   Recommendation: accept.

8. **Error behavior**:
   - Unknown programmatic tool: synthesize a tool-result error with the
     original caller; let the program resume.
   - Disabled or empty allowlist: configuration error at
     `initialize_request` time (raise, do not silently disable).
   - Selected non-function/custom tool: configuration error at
     `initialize_request` time.
   - Programmatic call to a direct-only tool (allowlist mismatch):
     synthesized error result with the original caller.
   - Malformed or missing caller: treat as a direct call (no caller emitted);
     log a warning. Do not raise.
   - Caller referencing an unknown program item: synthesize an error result
     with the original caller; let the program resume and exit.
   - Excessive calls in one phase: synthesized bounded-error result with the
     original caller.
   - Tool execution failure: the existing `iter_tool_messages` path already
     synthesizes an error result; extend it to carry the original caller.
   - Incomplete program: record in metadata; let the application decide
     whether to continue.
   - Program error: record in metadata; surface as a diagnostic.
   - Missing `program_output`: record in metadata; do not raise.
   - Completed program output followed by an incomplete or incorrect final
     message: record in metadata; surface as a diagnostic.

   Provider/protocol errors that prevent safe continuation (e.g. the API
   rejects the request shape) terminate the request with a clear application
   error. Recommendation: accept.

9. **Model gating**: gate on a list of regex patterns
   (`PROGRAMMATIC_TOOL_CALLING_MODEL_PATTERNS`) that match the current GPT-5.6
   family and future models that are assumed to support the feature. There is
   no model name like `gpt-5.6.1`, so multi-dot version false-positives are not
   a concern. The patterns are:
   ```python
   PROGRAMMATIC_TOOL_CALLING_MODEL_PATTERNS = [
       re.compile(r"^gpt-5\.[6-9](-.*)?$"),      # gpt-5.6 through gpt-5.9 and variants
       re.compile(r"^gpt-[6-9](\..*)?(-.*)?$"),  # gpt-6 through gpt-9 and variants
   ]
   ```
   This matches: `gpt-5.6`, `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`,
   `gpt-5.7`, `gpt-5.7-xxxx`, `gpt-5.8`, ..., `gpt-6`, `gpt-6.0`,
   `gpt-6.0-mini`, `gpt-7`, etc. It rejects: `gpt-5.5`, `gpt-5.4`,
   `gpt-5.2`, `gpt-4`, `gpt-3.5`. Task 010 decided not to publish the bare
   `gpt-5.6` alias in the UI, but users can still type it; the pattern matches
   it and the API routes it to Sol. New GPT-5.x (x >= 6) and GPT-6+ family
   members are assumed to support the feature and are included by the
   patterns; if a future model does NOT support it, add an exclusion pattern
   or tighten the list at that time. Recommendation: accept.

10. **ChatGPT endpoint support**: unknown at planning time. The ChatGPT
    backend may or may not accept `programmatic_tool_calling`. The ChatGPT
    integration test (section K) must record the exact outcome. If ChatGPT
    rejects it, document the endpoint difference in the README and mark the
    test as `xfail` only after confirming and documenting the rejection. Do
    not silently convert a rejection into a pass. Recommendation: accept.

### I. Concrete examples

#### Configuration

```json
{
  "model": "gpt-5.6-luna",
  "api_key": "...",
  "enable_programmatic_tool_calling": true,
  "programmatic_tool_names": ["lookup_records", "get_record_details"],
  "programmatic_tool_caller_policy": "direct_and_programmatic",
  "programmatic_max_calls_per_phase": 20
}
```

#### Outgoing request payload (after schema shaping)

```json
{
  "model": "gpt-5.6-luna",
  "tools": [
    {"type": "programmatic_tool_calling"},
    {
      "type": "function",
      "name": "lookup_records",
      "description": "Return matching records.",
      "parameters": {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
        "additionalProperties": false
      },
      "strict": true,
      "allowed_callers": ["direct", "programmatic"]
    },
    {
      "type": "function",
      "name": "get_record_details",
      "description": "Return details for one record.",
      "parameters": {
        "type": "object",
        "properties": {"id": {"type": "string"}},
        "required": ["id"],
        "additionalProperties": false
      },
      "strict": true,
      "allowed_callers": ["direct", "programmatic"]
    },
    {
      "type": "function",
      "name": "write_record",
      "description": "Write a record (side-effecting, not allowlisted).",
      "parameters": {
        "type": "object",
        "properties": {"id": {"type": "string"}, "value": {"type": "string"}},
        "required": ["id", "value"],
        "additionalProperties": false
      },
      "strict": true
    }
  ],
  "tool_choice": "auto"
}
```

`write_record` is omitted from `programmatic_tool_names` and therefore has no
`allowed_callers`; it remains direct-only by omission.

#### Program-issued function call (from the API)

```json
{
  "type": "function_call",
  "id": "fc_123",
  "call_id": "call_inventory_123",
  "name": "lookup_records",
  "arguments": "{\"query\":\"sku_123\"}",
  "caller": {
    "type": "program",
    "caller_id": "call_prog_123"
  }
}
```

#### Core tool call (after interop conversion)

```json
{
  "id": "call_inventory_123",
  "type": "function",
  "function": {
    "name": "lookup_records",
    "arguments": "{\"query\":\"sku_123\"}"
  },
  "_metadata": {
    "openai_responses_caller": {
      "type": "program",
      "caller_id": "call_prog_123"
    }
  }
}
```

#### Core tool-result message (after `iter_tool_messages`)

```json
{
  "role": "tool",
  "content": "{\"records\":[{\"id\":\"sku_123\",\"available_units\":42}]}",
  "metadata": {
    "tool_call_id": "call_inventory_123",
    "tool_name": "lookup_records",
    "tool_plugin": "inventory_tools",
    "openai_responses_caller": {
      "type": "program",
      "caller_id": "call_prog_123"
    }
  }
}
```

#### Native `function_call_output` (on the wire)

```json
{
  "type": "function_call_output",
  "call_id": "call_inventory_123",
  "output": "{\"records\":[{\"id\":\"sku_123\",\"available_units\":42}]}",
  "caller": {
    "type": "program",
    "caller_id": "call_prog_123"
  }
}
```

#### Program and program_output items (in native history)

```json
{
  "type": "program",
  "id": "prog_123",
  "call_id": "call_prog_123",
  "code": "const r = await fetch('lookup_records', {query:'sku_123'}); text(JSON.stringify(r));",
  "fingerprint": "opaque_replay_state"
}
```

```json
{
  "type": "program_output",
  "id": "prog_out_123",
  "call_id": "call_prog_123",
  "result": "{\"sku\":\"sku_123\",\"available_units\":42,\"requested_units\":31,\"shortage_units\":0}",
  "status": "completed"
}
```

#### Assistant metadata (structured observability)

```json
{
  "role": "assistant",
  "content": "The inventory for sku_123 shows 42 units available.",
  "metadata": {
    "response_id": "resp_123",
    "native_indices": [3, 4, 5, 6, 7, 8],
    "openai_responses_programmatic_tool_calling": {
      "programs": [
        {
          "id": "prog_123",
          "call_id": "call_prog_123",
          "code": "const r = await fetch('lookup_records', {query:'sku_123'}); text(JSON.stringify(r));",
          "fingerprint": "opaque_replay_state",
          "status": "completed",
          "error": null,
          "native_index": 3,
          "response_id": "resp_123"
        }
      ],
      "program_outputs": [
        {
          "id": "prog_out_123",
          "call_id": "call_prog_123",
          "result": "{\"sku\":\"sku_123\",\"available_units\":42,\"requested_units\":31,\"shortage_units\":0}",
          "status": "completed",
          "native_index": 7,
          "response_id": "resp_123"
        }
      ]
    }
  }
}
```

The final assistant `content` comes from the assistant `message` item, not
from `program_output.result`.

### J. Changed contracts and affected consumers

1. **Tool interop: `OpenAIResponsesFunctionCallAccessor.get_payload_metadata`**
   - Before: returns `dict(call.get("_metadata"))` or `{}`.
   - After: returns `{**dict(call.get("_metadata")), "openai_responses_caller": call.get("caller")}` when `caller` is a dict, else unchanged.
   - Affected consumers:
     - `OpenAIResponsesToolCallToOpenAIChatToolCall.convert` (reads
       `payload_metadata` via `inspect_call`).
     - `OpenAIResponsesToolsExtension._assistant_tool_calls_to_native_items`
       (uses `inspect_call`).
     - `AgentCore.iter_tool_messages` (uses `inspect_call.payload_metadata`;
       will now see `openai_responses_caller`).
     - `AgentCore.format_tool_call_preview` (uses `inspect_call`; unaffected
       functionally).
   - Regression risk: low. The added key is namespaced and does not collide
     with existing metadata keys. Existing tests that assert exact metadata
     dicts may need updating if they compare with `==` against a literal dict;
     audit during implementation.

2. **Tool interop: `OpenAIResponsesToolCallToOpenAIChatToolCall.convert`**
   - Before: returns `{"id", "type", "function"}` with no `_metadata`.
   - After: returns the same shape plus `_metadata["openai_responses_caller"]`
     when the source call has a `caller`.
   - Affected consumers:
     - `OpenAIResponsesToolsExtension._native_function_call_to_chat_tool_call`
       (consumes the converted call).
     - `OpenAIResponsesToolsExtension.from_native_messages` (rebuilds core
       assistant `tool_calls` from the converted calls).
     - `AgentCore.iter_tool_messages` (receives the converted call as
       `inspected_call.raw`).
   - Regression risk: low. The `_metadata` key is preserved by the existing
     tools-extension round-trip and does not affect the chat-completions wire
     shape.

3. **Core: `AgentCore.iter_tool_messages`**
   - Before: tool message `metadata` contains only `tool_call_id`,
     `tool_name`, `tool_schema`, `tool_plugin`, `display`, and tool-supplied
     keys.
   - After: also contains non-core-managed keys from
     `inspected_call.payload_metadata` (e.g. `openai_responses_caller`).
   - Affected consumers:
     - `ToolLoopRunner._apply_tool_calls` (reads tool message metadata; will
       now see `openai_responses_caller`).
     - `OpenAIResponsesProvider.to_native_messages` (reads
       `openai_responses_caller` from core tool message metadata to emit
       `caller` on `function_call_output`).
     - Session persistence (the metadata dict is persisted as part of the tool
       message; the new key rides through).
     - Other providers (Anthropic, OpenRouter, reference provider): they do
       not read `openai_responses_caller`, so the extra key is inert. Verify
       with the existing provider test suites.
   - Regression risk: medium. The merge is provider-neutral but touches a
     hot path. Add regression tests for direct calls (no caller metadata) and
     for other providers (no behavior change).

4. **Plugin provider: `to_native_messages` (tool branch)**
   - Before: emits `{"type": "function_call_output", "call_id", "output"}` and
     optional `_metadata`.
   - After: also emits top-level `caller` when
     `internal_md["openai_responses_caller"]` is a dict.
   - Affected consumers:
     - The OpenAI Responses API (reads `caller` to resume the program).
     - `from_native_messages` (reads `caller` back for save/reload).
     - Native history regression tests (may need updating to expect `caller`
       on program-issued `function_call_output` items).
   - Regression risk: low for direct calls (no `caller` emitted). Medium for
     programmatic calls (new field on the wire; covered by integration tests).

5. **Plugin provider: `from_native_messages`**
   - Before: `program` and `program_output` items are orphan items attached to
     the last assistant message's `native_indices`.
   - After: they are still attached (for native-history continuity) but also
     exposed as structured `openai_responses_programmatic_tool_calling`
     metadata on the owning assistant message.
   - Affected consumers:
     - Terminal event rendering (may want to surface program/program_output
       diagnostics in the future; not required for this task).
     - Session persistence (the metadata is persisted; the new key rides
       through).
     - Native history regression tests (may need updating to expect the new
       metadata block).
   - Regression risk: low. The new metadata is additive.

6. **Plugin tools extension: `to_native_messages` (tool branch)**
   - Before: re-adds `tool_plugin`, `tool_name`, `display` to `_metadata`.
   - After: also re-adds `openai_responses_caller` if present.
   - Affected consumers: native-history rebuild path.
   - Regression risk: low. Additive change.

7. **Plugin tools extension: `initialize_request`**
   - Before: converts tools, sets `tool_choice`.
   - After: also injects `programmatic_tool_calling` and `allowed_callers` when
     enabled.
   - Affected consumers: the OpenAI Responses API request shape.
   - Regression risk: low when disabled (default). Medium when enabled (new
     fields on the wire; covered by unit and integration tests).

8. **Application tool loop: `ToolLoopRunner` interceptor hook**
   - Before: `__init__` takes no interceptors; `_apply_tool_calls`
     executes all calls directly.
   - After: `__init__` takes an optional interceptors sequence;
     `_apply_tool_calls` consults each interceptor's pre-execution hook before
     execution, maintains a per-phase state object, and applies interceptor
     decisions (proceed, proceed with modified parameters, short-circuit
     with result, post-execution modification). Short-circuited results merge
     `payload_metadata` from the initiating call.
   - Affected consumers: `AgentApplication.send_request` (must collect
     registered interceptors from active provider extensions and pass them to
     `ToolLoopRunner`); `ToolLoopRunner.run`.
   - Regression risk: low for direct calls (no interceptors registered, or
     interceptors return no opinion for direct calls; behavior is identical to
     today). Medium for the new hook (covered by generic application tests in
     the interceptor capability task).
   - **Note**: this contract change is owned by the interceptor capability
     task (`tasks/20260717-tool-call-interceptor-capability.md`); this task
     depends on it and does not modify `ToolLoopRunner` directly.

9. **Application tool loop: generic interceptor protocol (new, in the
   interceptor capability task)**
   - Before: no such protocol.
   - After: the interceptor capability task defines a generic interceptor
     protocol with pre-execution and post-execution hooks, a context object,
     and a decision result. `AgentApplication` discovers implementers from
     active provider extensions and passes them to `ToolLoopRunner`.
   - Affected consumers: any provider extension that wants to enforce a
     per-call policy or modify tool calls/results. The OpenAI Responses
     plugin is the first consumer.
   - Regression risk: low. The protocol is additive; no existing code
     implements it until the OpenAI Responses plugin does.
   - **Note**: this protocol is owned by the interceptor capability task;
     this task depends on it.

10. **OpenAI Responses plugin: provider-specific interceptor (new)**
    - Before: no such interceptor.
    - After: a provider-specific interceptor in the OpenAI Responses plugin
      implements the generic interceptor protocol. It reads the four config
      keys, identifies programmatic calls via `openai_responses_caller`,
      enforces the allowlist and per-phase limit, and returns proceed or
      short-circuit decisions from the pre-execution hook. The
      post-execution hook is a no-op. Registered via the discovery mechanism
      defined by the interceptor capability task.
    - Affected consumers: `ToolLoopRunner` (calls it generically via the
      interceptor capability task's mechanism); `AgentApplication` (collects
      it from the extension).
    - Regression risk: low when `enable_programmatic_tool_calling` is false
      (the interceptor returns `None` for all calls). Medium when enabled
      (covered by plugin tests in K.6b and K.6c).

11. **Plugin `pyproject.toml`**
   - Before: `openai>=2.0.0`.
   - After: `openai>=2.45.0`.
   - Affected consumers: any environment that installs the plugin. The repo
     `.venv` currently has `openai==2.26.0` and must be upgraded before running
     the new tests.
   - Regression risk: low. The SDK is backward-compatible for existing
     Responses calls. Run the existing plugin suite after the bump to confirm.

### K. Exact tests

#### K.1 Core tool-interop tests (`core/python/tests/test_tool_interop.py`)

Add:

- `test_openai_responses_function_call_accessor_extracts_caller_as_metadata`:
  a `function_call` with `caller={"type":"program","caller_id":"call_prog_1"}`
  yields `payload_metadata["openai_responses_caller"]` equal to the caller dict.
- `test_openai_responses_function_call_accessor_direct_call_has_no_caller_metadata`:
  a `function_call` without `caller` yields `payload_metadata` with no
  `openai_responses_caller` key.
- `test_openai_responses_function_call_accessor_malformed_caller_is_ignored`:
  a `function_call` with `caller="not a dict"` yields `payload_metadata` with
  no `openai_responses_caller` key (graceful degradation).
- `test_openai_responses_tool_call_to_openai_chat_preserves_caller_in_metadata`:
  the converted chat-completions call carries
  `_metadata["openai_responses_caller"]` when the source has a caller.
- `test_openai_responses_tool_call_to_openai_chat_omits_caller_for_direct_calls`:
  the converted chat-completions call has no `_metadata["openai_responses_caller"]`
  when the source has no caller.
- `test_openai_responses_tool_call_to_openai_chat_wire_shape_unchanged`:
  the converted call's `id`, `type`, `function.name`, `function.arguments`
  are unchanged from the existing behavior (regression guard).

#### K.2 Core tool-result merge tests (new file or extend
`core/python/tests/test_tool_plugin_context.py`)

Add:

- `test_iter_tool_messages_merges_payload_metadata_into_tool_message_metadata`:
  a tool call with `payload_metadata["openai_responses_caller"]` produces a
  tool message whose `metadata` contains the same caller dict.
- `test_iter_tool_messages_does_not_overwrite_core_managed_metadata`:
  a tool call with `payload_metadata["tool_call_id"]` (attempted collision)
  does not overwrite the core-managed `tool_call_id`.
- `test_iter_tool_messages_payload_metadata_wins_over_result_metadata`:
  a call with `payload_metadata["openai_responses_caller"]` and a tool that
  returns `last_result["metadata"]["openai_responses_caller"] = "tool_supplied"`
  — assert the final metadata has the `payload_metadata` value, not the
  tool-supplied one (verifies the merge ordering: payload_metadata is merged
  before result_metadata, both with `if key not in metadata`).
- `test_iter_tool_messages_direct_call_metadata_unchanged`:
  a direct call (no `payload_metadata`) produces a tool message with the
  existing metadata shape (regression guard).

#### K.3 Plugin tools-extension unit tests
(`plugins/openai_responses/tests/test_openai_responses_tools_extension_unit.py`)

Add:

- `test_initialize_request_disabled_omits_programmatic_tool_calling`:
  with `enable_programmatic_tool_calling` false or absent, the payload's
  `tools` list does not contain `{"type": "programmatic_tool_calling"}` and no
  function tool has `allowed_callers`.
- `test_initialize_request_enabled_adds_programmatic_tool_calling_once`:
  with the feature enabled and a valid allowlist, the payload's `tools` list
  contains exactly one `{"type": "programmatic_tool_calling"}` entry.
- `test_initialize_request_allowlisted_tools_get_allowed_callers`:
  allowlisted function tools get
  `allowed_callers: ["direct", "programmatic"]` (or `["programmatic"]` for
  `programmatic_only`).
- `test_initialize_request_unselected_tools_remain_direct_only`:
  non-allowlisted function tools have no `allowed_callers`.
- `test_initialize_request_rejects_empty_allowlist`:
  enabled with `programmatic_tool_names: []` raises an actionable error.
- `test_initialize_request_rejects_unknown_tool_name`:
  enabled with a name that does not resolve to an active tool raises an
  actionable error.
- `test_initialize_request_rejects_custom_tool_in_allowlist`:
  enabled with a custom/freeform tool in the allowlist raises an actionable
  error.
- `test_initialize_request_rejects_unsupported_model`:
  enabled with a model that does not match any pattern in
  `PROGRAMMATIC_TOOL_CALLING_MODEL_PATTERNS` (e.g. `gpt-5.5`, `gpt-5.4`,
  `gpt-4`) raises an actionable error.
- `test_initialize_request_accepts_future_gpt_5_x_models`:
  enabled with `gpt-5.7` and `gpt-5.7-xxxx` does NOT raise (the regex patterns
  include future minor versions 5.6 through 5.9).
- `test_initialize_request_accepts_future_gpt_6_plus_models`:
  enabled with `gpt-6`, `gpt-6.0`, `gpt-6.0-mini`, `gpt-7` does NOT raise
  (the regex patterns include future major versions 6 through 9).
- `test_initialize_request_accepts_bare_gpt_5_6_alias`:
  enabled with `gpt-5.6` (no suffix) does NOT raise (the API routes it to
  Sol).
- `test_initialize_request_does_not_duplicate_programmatic_tool_calling`:
  when the raw request payload already contains
  `{"type": "programmatic_tool_calling"}`, the extension does not append a
  second one.
- `test_round_trip_preserves_caller_on_function_call_output`:
  a core tool message with `openai_responses_caller` in metadata produces a
  native `function_call_output` with the same top-level `caller`.
- `test_round_trip_direct_call_omits_caller`:
  a core tool message without `openai_responses_caller` produces a native
  `function_call_output` without a `caller` field.
- `test_round_trip_caller_survives_rebuild`:
  after `to_native_messages` -> `from_native_messages` -> `to_native_messages`,
  the `caller` on `function_call_output` is preserved.

#### K.4 Plugin provider tests
(extend `test_openai_responses_provider_unit.py` and
`test_openai_responses_native_history_regressions.py`)

Add to `test_openai_responses_provider_unit.py`:

- `test_sanitize_input_item_preserves_program_required_fields`:
  round-trip a `program` and a `program_output` through
  `_sanitize_input_item` and assert `id`, `call_id`, `code`, `fingerprint`,
  `result`, `status`, `type` all survive (not stripped by the
  `_PASSTHROUGH_ITEM_TYPES` early-return branch).
- `test_from_native_messages_exposes_program_metadata_on_assistant`:
  a native history containing a `program` item produces an assistant message
  with `metadata.openai_responses_programmatic_tool_calling.programs[0]`
  containing id, call_id, code, fingerprint, status, native_index, response_id.
- `test_from_native_messages_exposes_program_output_metadata_on_assistant`:
  a native history containing a `program_output` item produces an assistant
  message with `metadata.openai_responses_programmatic_tool_calling.program_outputs[0]`
  containing id, call_id, result, status, native_index, response_id.
- `test_from_native_messages_final_assistant_content_comes_from_message_not_program_output`:
  a segment with `program_output` and a final `message` produces assistant
  `content` from the `message`, not from `program_output.result`.
- `test_from_native_messages_program_output_without_message_does_not_become_content`:
  a segment with `program_output` and no final `message` produces empty
  assistant `content` and the `program_output.result` only in metadata.
- `test_to_native_messages_emits_caller_on_function_call_output`:
  a core tool message with `openai_responses_caller` produces a native
  `function_call_output` with the same top-level `caller`.
- `test_to_native_messages_omits_caller_for_direct_calls`:
  a core tool message without `openai_responses_caller` produces a native
  `function_call_output` without `caller`.
- `test_from_native_messages_preserves_caller_in_both_tool_message_paths`:
  covers both the segment-embedded `function_call_output` (via
  `_flush_response_segment`) and the standalone `function_call_output` (via
  the main loop branch) — both produce tool messages with
  `openai_responses_caller` in metadata.

Add to `test_openai_responses_native_history_regressions.py`:

- `test_programmatic_tool_calling_round_trip_preserves_program_and_program_output`:
  a scripted response containing `program`, program-issued `function_call`,
  `function_call_output` (with `caller`), `program_output`, and a final
  `message` round-trips through `to_native_messages` ->
  `from_native_messages` -> `to_native_messages` with all items and the
  `caller` preserved.
- `test_programmatic_tool_calling_save_reload_preserves_caller`:
  simulate save/reload by serializing native messages to JSON and back, then
  rebuild; the `caller` on `function_call_output` is preserved.
- `test_programmatic_tool_calling_streaming_accumulates_program_items`:
  a streaming response that emits `program`, `function_call`, and
  `program_output` via `response.output_item.done` events accumulates them in
  `state["_openai_responses_stream_output_items"]` and surfaces them in the
  final assistant metadata.

#### K.5 Plugin tools-extension integration tests
(extend `test_openai_responses_tools_extension_integration.py`)

Add a scripted end-to-end test using a `_ScriptedToolsProvider`:

- `test_programmatic_tool_calling_loop_executes_caller_linked_calls`:
  script the provider to emit a `program` item, a program-issued
  `function_call` with `caller`, and (after the tool result) a
  `program_output` and a final `message`. Use a read-only fixture tool in the
  allowlist. Assert:
  - the outgoing request payload contains
    `{"type": "programmatic_tool_calling"}` and `allowed_callers` on the
    allowlisted tool;
  - the tool result message carries `openai_responses_caller`;
  - the second request's native input contains a `function_call_output` with
    the same `caller`;
  - the final assistant message has structured
    `openai_responses_programmatic_tool_calling` metadata;
  - the final assistant `content` comes from the final `message`, not from
    `program_output.result`.

#### K.6 Application tool-loop tests

The generic interceptor hook tests (pre-execution proceed, pre-execution
with modified parameters, pre-execution short-circuit, post-execution
modification, post-execution chaining, per-phase state reset,
non-active-provider isolation, `inspected_call is None` handling, regression
safety for direct calls) are owned by the interceptor capability task
(`tasks/20260717-tool-call-interceptor-capability.md`) and are NOT
duplicated here. This task only adds the provider-specific tests below.

**K.6a Provider-specific interceptor tests**
(new file `plugins/openai_responses/tests/test_openai_responses_programmatic_tool_calling_interceptor_unit.py`)

These tests verify the OpenAI Responses plugin's interceptor in isolation,
using stub `inspected_call` objects and config dicts. They do NOT instantiate
`ToolLoopRunner`.

1. `test_interceptor_returns_no_opinion_when_feature_disabled`:
   with `enable_programmatic_tool_calling: false`, the interceptor returns no
   opinion for all calls.
2. `test_interceptor_returns_no_opinion_for_direct_calls`:
   a call without `openai_responses_caller` in `payload_metadata` returns no
   opinion.
3. `test_interceptor_returns_no_opinion_when_inspected_call_is_none`:
   when `inspected_call is None`, the interceptor returns no opinion (lets
   the loop handle the malformed call via the existing "no tool handled"
   path).
4. `test_interceptor_returns_proceed_for_allowlisted_programmatic_call`:
   a programmatic call to an allowlisted tool returns a proceed decision and
   increments the per-phase counter.
5. `test_interceptor_returns_short_circuit_for_non_allowlisted_tool`:
   a programmatic call to a tool not in `programmatic_tool_names` returns a
   short-circuit decision with a clear error message.
6. `test_interceptor_returns_short_circuit_when_per_phase_limit_reached`:
   with `programmatic_max_calls_per_phase: 2` and the counter already at 2,
   the interceptor returns a short-circuit decision.
7. `test_interceptor_uses_namespaced_phase_state_key`:
   the counter is stored under `openai_responses_programmatic_calls` in the
   per-phase state object, not under a generic key.
8. `test_interceptor_post_execution_hook_is_noop`:
   the post-execution hook returns no opinion for all results (executed,
   short-circuited, and "no tool handled" errors).

**K.6b End-to-end tool-loop integration with the interceptor**
(new file `application/python/tests/test_tool_loop_programmatic_tool_calling.py`)

A deterministic integration-style test that wires the real provider-specific
interceptor into `ToolLoopRunner` via the generic hook (provided by the
interceptor capability task), using a scripted OpenAI Responses provider and
read-only fixture tools.

1. `test_programmatic_tool_calling_allowlist_rejects_unknown_tool`:
   script a program-issued call to a tool not in the allowlist; assert a
   synthesized error result with the original caller; assert the program
   resumes.
2. `test_programmatic_tool_calling_per_phase_limit_returns_bounded_error`:
   set `programmatic_max_calls_per_phase: 2`; script three program-issued
   calls in one phase; assert the third produces a bounded-error result with
   the original caller.
3. `test_programmatic_tool_calling_preserves_caller_on_tool_execution_error`:
   script a program-issued call to a tool that raises; assert the synthesized
   error result carries the original caller.
4. `test_programmatic_tool_calling_resumes_program_and_emits_program_output`:
   script the full loop: program -> caller-linked call -> tool result ->
   program_output -> final message. Assert event order, checkpoints, and
   final session history.
5. `test_programmatic_tool_calling_direct_call_unaffected`:
   with the feature enabled, a direct call (no caller) still executes through
   the existing path (regression guard).

#### K.7 Real OpenAI API integration test
(new file
`plugins/openai_responses/tests/test_openai_responses_programmatic_tool_calling_real_api.py`)

- Markers: `pytest.mark.api`, `@pytest.mark.integration`, `@pytest.mark.openai`.
- Gate on `OPENAI_API_KEY` via the existing `ensure_openai_api_key` fixture
  pattern.
- Use `gpt-5.6-luna` (the cheapest GPT-5.6 family member).
- Use deterministic read-only fixture tools (e.g. a `lookup_records` tool
  that returns a fixed list).
- Ask for a bounded aggregation/filtering result that requires multiple tool
  calls.
- Assert:
  - at least one `program` item in the response;
  - program-issued calls contain `caller.type == "program"` and a
    `caller_id`;
  - returned `function_call_output` items preserve the caller;
  - a `program_output` item exists;
  - the final assistant response is correct independently of
    `program_output`;
  - compare basic call/turn/token metadata with a direct-calling baseline
    where practical (record both, do not assert a strict ordering).
- Do not parametrize with ChatGPT auth; keep that in a separate test.

#### K.8 Saved-login ChatGPT integration test
(new file
`plugins/openai_responses/tests/test_openai_responses_chatgpt_programmatic_tool_calling_manual_integration.py`)

- Markers: `pytest.mark.api`, `@pytest.mark.manual_integration`,
  `@pytest.mark.integration`, `@pytest.mark.openai`.
- Credential path: `$CHATGPT_TEST_STATE_DIR/auth/chatgpt-auth.json` (fall back
  to `plugins/chatgpt-auth-app/tests/.manual-state`).
- Credential gate: skip with exact reason on `FileNotFoundError`, non-dict
  JSON, missing/blank `access_token`, or expired `expires_at`. Never print
  tokens/account/email.
- Use `OPENAI_RESPONSES_CHATGPT_MODEL="gpt-5.6-luna"` (or a configurable
  GPT-5.6 model).
- Record the outgoing tool schemas (via a recording provider subclass) and
  assert they include `{"type": "programmatic_tool_calling"}` and
  `allowed_callers` on the allowlisted tool.
- Assert whether the ChatGPT backend accepts Programmatic Tool Calling:
  - If accepted, verify the complete caller-linked loop (program, caller,
    function_call_output with caller, program_output, final message).
  - If rejected, report the exact status/error and document the endpoint
    difference. Mark `xfail` only after confirming and documenting the
    rejection; do not silently convert a rejection into a pass.
- Do not count missing credentials or a skipped test as successful
  verification.
- Run with:
  ```bash
  CHATGPT_TEST_STATE_DIR="$HOME/.crystal" \
  OPENAI_RESPONSES_CHATGPT_MODEL="gpt-5.6-luna" \
    pytest plugins/openai_responses/tests/test_openai_responses_chatgpt_programmatic_tool_calling_manual_integration.py \
      -m "manual_integration and integration and openai" -q
  ```

#### K.9 Regression tests

- `test_openai_responses_provider_unit.py`: add
  `test_get_tags_does_not_advertise_programmatic_tool_calling_by_default`
  (the provider tag list is unchanged when the feature is disabled).
- `test_openai_responses_tools_extension_unit.py`: add
  `test_initialize_request_ordinary_responses_payload_shape_unchanged`
  (with the feature disabled, the payload shape is identical to today).
- `test_openai_responses_native_history_regressions.py`: ensure the existing
  regression tests still pass after the `from_native_messages` changes (or
  are updated to assert the new metadata block where appropriate).
- Run the OpenRouter, OpenAI Responses, and reference provider suites to
  confirm the core `iter_tool_messages` merge does not break other
  providers.

### L. Documentation sections

Update `plugins/openai_responses/README.md` with a new
`### Programmatic Tool Calling` section under `## Features`, and add config
keys to `## Configuration reference`. Cover:

1. **Feature overview**: what Programmatic Tool Calling is, that GPT-5.6
   generates JavaScript that OpenAI runs in an isolated hosted V8, and that
   client-owned function tools remain local to this framework.
2. **Supported models/endpoints**: GPT-5.6 family (`gpt-5.6-sol`,
   `gpt-5.6-terra`, `gpt-5.6-luna`) and the bare `gpt-5.6` alias (routed to
   Sol by the API). Future GPT-5.x (x >= 6) and GPT-6+ models are assumed to
   support the feature and are matched by the regex patterns in
   `PROGRAMMATIC_TOOL_CALLING_MODEL_PATTERNS`; if a future model does NOT
   support it, add an exclusion pattern or tighten the list. Only the
   Responses API supports it. ChatGPT endpoint support is unknown; see the
   troubleshooting section.
3. **Disabled-by-default behavior**: the feature is off by default and
   requires an explicit allowlist.
4. **Configuration keys**: the four keys in section B, with types, defaults,
   and semantics.
5. **Safe use cases**: bounded read-only filtering, joining, sorting,
   ranking, deduplication; batching many similar records; repeated
   deterministic validation; map/reduce-style retrieval; reducing large
   structured intermediate results to a compact schema.
6. **Security boundaries**:
   - the allowlist is an explicit operator decision; the framework does not
     infer read-only safety from tool names;
   - only function tools are supported in the first implementation;
   - side-effecting, approval-gated, and custom/freeform tools must not be
     allowlisted;
   - the hosted runtime has no filesystem or network access;
   - the framework executes client-owned function tools locally; it does not
     execute the generated JavaScript.
7. **Caller preservation**: the framework preserves `caller` from
   program-issued calls through tool interop, execution, session history, and
   returned function outputs.
8. **Program vs. final assistant output**: `program_output` is
   diagnostic/intermediate structured state; the final assistant `content`
   comes from the assistant `message`, not from `program_output`.
9. **Execution and call limits**: the hosted runtime has a five-second
   execution limit; `programmatic_max_calls_per_phase` is an
   application-side safety limit. The limit is per LLM phase, not per program.
   A program that spans multiple phases may emit up to
   `programmatic_max_calls_per_phase` calls in each phase. The outer
   `max_loops` limit bounds the total number of phases. The theoretical
   maximum total program-issued calls is
   `max_loops × programmatic_max_calls_per_phase` (e.g., 8 × 20 = 160 with
   defaults). Operators who want a tighter total cap should lower `max_loops`
   or `programmatic_max_calls_per_phase`.
10. **API vs. ChatGPT support status**: API supports it; ChatGPT endpoint
    support is unknown and must be verified per session.
11. **Example request/tool configuration**: the example in section I.
12. **Troubleshooting**:
    - "Malformed caller" / "missing caller": the framework treats such calls
      as direct; check the model output and the SDK version.
    - "Unsupported tool in allowlist": ensure the allowlisted tool is a
      function tool registered with the application.
    - "Endpoint rejection" (ChatGPT): the ChatGPT backend may reject
      `programmatic_tool_calling`; check the response status and fall back to
      API auth mode.
    - "Empty allowlist": set `programmatic_tool_names` to a non-empty list of
      function tool names.
    - "Model not supported": use a model that matches
      `PROGRAMMATIC_TOOL_CALLING_MODEL_PATTERNS` (GPT-5.6 family or future
      GPT-5.x/6+ models). If a future model does not support the feature,
      add an exclusion pattern or tighten the list.

If public core/tool interop behavior changes, update
`TYPES_AND_PROTOCOLS.md` and `docs/api/core-sdk.md` with the new
`payload_metadata` merge contract in `iter_tool_messages`.

The generic interceptor capability (protocol, `ToolLoopRunner` hook,
`AgentApplication` discovery) is defined and documented by the interceptor
capability task (`tasks/20260717-tool-call-interceptor-capability.md`); this
task does not duplicate that documentation. The OpenAI Responses plugin's
provider-specific interceptor is the first implementation and is documented
in `plugins/openai_responses/README.md` as a provider-specific interceptor
that plugs into the generic capability.

### M. Implementation order

0. **Prerequisite check**: verify the interceptor capability task
   `tasks/20260717-tool-call-interceptor-capability.md` is complete. If not,
   complete it first — this task depends on the generic interceptor protocol,
   the `ToolLoopRunner` hook, and `AgentApplication` discovery.
0a. **Login refresh**: before starting implementation, check
   `~/.crystal/auth/chatgpt-auth.json` expiry. If expired or will expire
   within the expected implementation window, refresh the login first using
   the existing refresh flow. The saved login was valid through
   `2026-07-18T19:42:08Z` at task-010 completion time.
1. Bump `openai>=2.45.0` in `plugins/openai_responses/pyproject.toml` and
   upgrade the repo `.venv` (`python -m pip install -e
   "plugins/openai_responses[dev]"`). After bumping, run
   `pytest plugins/openai_responses/tests -q` (default, non-integration) and
   triage ALL failures before proceeding. Record before/after pass counts in
   `## Completion Notes`. If the bump breaks unrelated tests, fix those first
   as a separate commit so the feature diff stays clean. Note: other plugins
   (OpenRouter, reference provider) do not depend on `openai` and won't be
   affected.
2. Add the SDK guard test that imports `ProgrammaticToolCalling` from
   `openai.types.responses.tool_param`.
3. Add the tool-interop changes (accessor + adapter) and the K.1 unit tests.
4. Add the core `iter_tool_messages` merge (section D.2 ordering) and the
   K.2 unit tests.
5. Add the provider `to_native_messages` / `from_native_messages` caller
   handling (both locations, section D.3) and the K.4 unit tests. Use the
   key `openai_responses_caller` (no leading underscore).
6. Add the provider `program`/`program_output` metadata exposure and the
   `_PASSTHROUGH_ITEM_TYPES` fix in `_sanitize_input_item` (section E.1);
   add the K.4 unit tests.
7. Add the tools-extension `initialize_request` schema shaping (including
   `PROGRAMMATIC_TOOL_CALLING_MODEL_PATTERNS` regex gating, section H.9) and
   the K.3 unit tests.
8. Add the tools-extension `to_native_messages` caller re-add and the K.3
   round-trip tests.
9. Add the K.5 scripted end-to-end integration test.
10. Add the OpenAI Responses provider-specific interceptor
    (section F.1) and the K.6a interceptor unit tests.
11. Add the K.6b end-to-end tool-loop integration test that wires the
    interceptor into `ToolLoopRunner` via the generic hook (provided by the
    interceptor capability task).
12. Add the K.7 real API integration test.
13. Add the K.8 ChatGPT saved-login integration test (moved earlier to
    maximize the chance of running before login expiry).
14. Update `plugins/openai_responses/README.md` (section L).
15. Update `TYPES_AND_PROTOCOLS.md` and `docs/api/core-sdk.md` if the core
    contract change requires it.
16. Run the fast default plugin suite, the core suite, and the application
    suite.
17. Run the real API test with `OPENAI_API_KEY` from repo root `.env`.
18. Run the ChatGPT saved-login test with `CHATGPT_TEST_STATE_DIR="$HOME/.crystal"`.
19. Lint/format/typecheck: `ruff check`, `black`, `pyright` on changed files.
20. Append `## Completion Notes` to this task file and update `000-main.md`
    checklist.

### N. Dependency/version changes

- `plugins/openai_responses/pyproject.toml`: `openai>=2.0.0` ->
  `openai>=2.45.0`.
- No other plugin or core dependency changes.
- The repo `.venv` must be upgraded before running the new tests:
  ```bash
  python -m pip install -e "plugins/openai_responses[dev]"
  ```

### O. Verification commands

```bash
# Fast default suites
pytest core/python/tests/test_tool_interop.py -q
pytest core/python/tests/test_tool_plugin_context.py -q
pytest plugins/openai_responses/tests -q
pytest application/python/tests/test_tool_loop_programmatic_tool_calling.py -q

# Targeted programmatic tool calling tests
pytest plugins/openai_responses/tests/test_openai_responses_tools_extension_unit.py -q
pytest plugins/openai_responses/tests/test_openai_responses_tools_extension_integration.py -q
pytest plugins/openai_responses/tests/test_openai_responses_native_history_regressions.py -q
pytest plugins/openai_responses/tests/test_openai_responses_provider_unit.py -q
pytest plugins/openai_responses/tests/test_openai_responses_programmatic_tool_calling_interceptor_unit.py -q

# Generic interceptor capability tests (owned by the interceptor task)
pytest application/python/tests/test_tool_call_interceptor.py -q

# Real API (gated on OPENAI_API_KEY in repo root .env)
pytest plugins/openai_responses/tests/test_openai_responses_programmatic_tool_calling_real_api.py \
  -m "integration and api and not slow_integration and openai" -q

# ChatGPT saved-login (gated on CHATGPT_TEST_STATE_DIR)
CHATGPT_TEST_STATE_DIR="$HOME/.crystal" \
OPENAI_RESPONSES_CHATGPT_MODEL="gpt-5.6-luna" \
  pytest plugins/openai_responses/tests/test_openai_responses_chatgpt_programmatic_tool_calling_manual_integration.py \
    -m "manual_integration and integration and openai" -q

# Lint/format/typecheck
ruff check core/python/agent_core plugins/openai_responses/src plugins/openai_responses/tests application/python/agent_app
black core/python/agent_core plugins/openai_responses/src plugins/openai_responses/tests application/python/agent_app
pyright
```

Record skipped credential-gated tests as not run, not as passes.

### P. Risks

1. **SDK bump may surface unrelated test failures**: the repo `.venv` has
   `openai==2.26.0`; upgrading to `2.45.0+` skips 18 intermediate versions and
   may change behavior in unrelated Responses tests. Mitigation: after
   bumping, run `pytest plugins/openai_responses/tests -q` (default,
   non-integration) and triage ALL failures before starting feature work.
   Record before/after pass counts in `## Completion Notes`. If the bump
   breaks unrelated tests, fix those first as a separate commit. Other
   plugins (OpenRouter, reference provider) do not depend on `openai` and
   won't be affected.
2. **ChatGPT endpoint rejection**: the ChatGPT backend may reject
   `programmatic_tool_calling`. The K.8 test must record the exact outcome. If
   rejected, document and `xfail` only after confirmation.
3. **Saved ChatGPT login expiry**: the saved login at `~/.crystal/auth/chatgpt-auth.json`
   was valid through `2026-07-18T19:42:08Z` at task-010 completion time. If
   implementation runs after that, the ChatGPT test will skip with an exact
   reason and must be reported as not run. Mitigation: refresh the login
   before starting implementation (step 0a in section M); if the login
   expires before the test runs, document the exact expiry in
   `## Completion Notes`, mark the test as "not run" (not a skip-as-pass),
   and record the `xfail` reason as "saved login expired on
   2026-07-18T19:42:08Z; rerun with a refreshed login."
4. **`OPENAI_API_KEY` availability**: the key is in repo root `.env` but not
   exported in the shell. The plugin `conftest.py` loads it. If it is missing
   on run day, the real API test skips and must be reported as not run.
5. **Core `iter_tool_messages` merge risk**: the merge touches a hot path.
   Mitigation: the merge is provider-neutral (only non-core-managed keys are
   copied, with the ordering in section D.2) and regression-tested with
   direct calls and other providers.
6. **Native history regression risk**: the `from_native_messages` changes for
   `program`/`program_output` metadata exposure are additive but may require
   updating existing regression tests that assert exact metadata dicts.
7. **Caller metadata key name collision**: the key `openai_responses_caller`
   is namespaced; verify no existing tool or provider uses the same key. Use
   the key without a leading underscore (see section D.3 lock-in).
8. **`programmatic_max_calls_per_phase` default**: `20` is a conservative
   default. Real workloads may need more; users can override. Document the
   default, the per-phase semantics, and the combined `max_loops ×
   programmatic_max_calls_per_phase` bound in the README.
9. **Model gating over-matching**: the regex patterns in
   `PROGRAMMATIC_TOOL_CALLING_MODEL_PATTERNS` assume future GPT-5.x (x >= 6)
   and GPT-6+ models support the feature. There is no model name like
   `gpt-5.6.1`, so multi-dot version false-positives are not a concern. If a
   future model does NOT support the feature, add an exclusion pattern or
   tighten the list at that time. The K.3 tests verify acceptance of
   `gpt-5.7`, `gpt-5.7-xxxx`, `gpt-6`, `gpt-6.0-mini`, and rejection of
   `gpt-5.5`, `gpt-5.4`, `gpt-4`.
10. **Interceptor capability task dependency**: this task depends on
    `tasks/20260717-tool-call-interceptor-capability.md` being complete. If
    that task is not complete, this task cannot proceed past step 9 (the
    end-to-end integration test requires the generic interceptor hook in
    `ToolLoopRunner`).
11. **Lint/typecheck**: `ruff check` and `black` on changed files; `pyright`
    may surface new type errors from the SDK bump. Triage before committing.

### Q. Prerequisite assumptions

- Task 010's model and alias decisions are accepted: the GPT-5.6 family is
  `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`; the bare `gpt-5.6` alias is
  not published in the UI but users can type it manually and the API routes
  it to Sol.
- Tasks 020-060 (reasoning, pricing, Codex system instructions) are
  independent and do not block this task.
- The interceptor capability task
  (`tasks/20260717-tool-call-interceptor-capability.md`) is complete: the
  generic interceptor protocol, the `ToolLoopRunner` hook, and
  `AgentApplication` discovery are in place. This task implements only the
  provider-specific interceptor.
- The repo `.venv` can be upgraded to `openai>=2.45.0` without breaking other
  plugins. (OpenRouter and the reference provider do not depend on `openai`;
  verify during implementation.)
- The saved ChatGPT login at `~/.crystal/auth/chatgpt-auth.json` is usable
  through `2026-07-18T19:42:08Z`. If implementation runs after that, the
  ChatGPT test is reported as not run. Step 0a in section M refreshes the
  login before starting.
- `OPENAI_API_KEY` is available in repo root `.env` for the real API test.
- The OpenAI Responses API and the ChatGPT backend may differ in
  Programmatic Tool Calling support; the K.7 and K.8 tests record the exact
  outcomes independently.
- Future GPT-5.x (x >= 6) and GPT-6+ models are assumed to support
  Programmatic Tool Calling; the regex patterns in
  `PROGRAMMATIC_TOOL_CALLING_MODEL_PATTERNS` include them. There is no model
  name like `gpt-5.6.1`.
- Out of scope (from the task): local JavaScript execution, side-effecting
  tools, automatic read-only classification, and generalized cross-provider
  program runtimes are not implemented in this task.

## Out of scope

- implementing or embedding a local JavaScript runtime;
- executing hosted OpenAI tools from the program;
- programmatic custom/freeform tool calls in the first version;
- automatic classification of tools as read-only;
- enabling side-effecting or approval-gated tools;
- parallel local execution of program-issued calls;
- a generalized cross-provider program-runtime protocol;
- automatic migration of existing direct tool configurations;
- frontend program-code visualization beyond metadata needed for diagnostics.
