# Add GPT-5.6 Programmatic Tool Calling

Add opt-in OpenAI Responses Programmatic Tool Calling support for bounded, read-only workflows while preserving caller linkage, native history, tool-loop safety, and separate API versus ChatGPT behavior.

## Requirements checklist

- [ ] Verify the supported OpenAI Python SDK version and API request/response contract before implementation.
- [ ] Add opt-in Programmatic Tool Calling configuration, disabled by default.
- [ ] Require an explicit allowlist of tools eligible for programmatic invocation.
- [ ] Add `programmatic_tool_calling` and per-tool `allowed_callers` request shaping.
- [ ] Preserve `caller` from program-issued function calls through tool interop, execution, session history, and returned function outputs.
- [ ] Preserve and expose `program` and `program_output` response items without conflating them with the final assistant message.
- [ ] Enforce read-only eligibility and bounded execution limits.
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
