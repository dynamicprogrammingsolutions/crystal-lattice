# System Message Rendering And Developer Role Follow-Up

Short description: Add red-green regression coverage around `feature-system-message` with `openai_responses`, preserve the already-correct placeholder rendering behavior, and fix the missing conversion from outbound `system` messages to `developer` messages for reasoning/developer-only OpenAI models.

Parent Task: `tasks/20260310-openai-responses-provider/000-main.md`

Depends On:
- `tasks/20260310-openai-responses-provider/040-provider-streaming-event-normalization-and-finalization.md`

## Why this follow-up exists

Reviewing session `/Users/ferenci84/Dev/Mine/ai-agent-platform/.crystal/sessions/f45bc937-f1c1-4db0-80f1-fa9b6bf7a70e.json` showed the first stored native item as:

```json
{
  "type": "message",
  "role": "system",
  "content": [
    {
      "type": "input_text",
      "text": "{{CODEX_SYSTEM}}\n\n{{TASKS}}\n\n{{AGENTS}}"
    }
  ]
}
```

That stored shape is not itself the bug.

Current code does two different things intentionally:

1. `SystemMessageFeature.initialize_request(...)` keeps provider-native history templated, but writes a rendered request override into `state["request"]["messages"]` after resolving variables and replacing placeholders.
2. `OpenAIResponsesProvider.call_api(...)` and `stream_api(...)` prefer `request["messages"]` over the retained native history when sending `input` to the SDK.

So placeholder substitution appears to be correct before send, but we do not have explicit regression coverage for the `openai_responses` stack.

The actual gap is role handling:

1. `OpenAIResponsesProvider.to_native_messages(...)` currently preserves `role` exactly as `system`, `user`, `assistant`, or `developer`.
2. No later request-preparation step rewrites outbound `system` to `developer`.
3. For OpenAI reasoning/developer-message-first models, this means we are still sending a `system` message on the wire.

## Evidence collected

### Placeholder rendering is already happening at request time

- `plugins/feature-system-message/src/feature_system_message/system_message_feature.py:377`
- `plugins/feature-system-message/src/feature_system_message/system_message_feature.py:392`
- `plugins/feature-system-message/src/feature_system_message/system_message_feature.py:500`

Relevant behavior:

1. The feature inserts a template-level system message into `working_native` when needed.
2. It resolves variables via `_resolve_variables(...)` and renders text via `_render_template(...)`.
3. It writes the rendered message list to `state["request"]["messages"]`, while returning `working_native` with the unrendered template preserved.

### The provider does use the rendered override for actual SDK calls

- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:680`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:829`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:884`

Relevant behavior:

1. `call_api(...)` reads `override = request.get("messages")` and uses that as `base_history` when present.
2. `stream_api(...)` does the same.
3. The sanitized `base_history` becomes the SDK `input` payload.

### The provider never converts outbound `system` to `developer`

- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:426`

The provider currently builds Responses items with `"role": role`, so a `system` message remains `system` all the way to the OpenAI SDK call.

### Official OpenAI guidance to align with

OpenAI’s reasoning best-practices guide says that starting with `o1-2024-12-17`, reasoning models support developer messages rather than system messages. The general text-generation guide also frames `developer` messages as the application-level instruction layer for Responses requests. See:

- https://developers.openai.com/api/docs/guides/reasoning-best-practices
- https://developers.openai.com/api/docs/guides/text

## Required outcome

1. Preserve the current good behavior where placeholders are substituted before the request is sent.
2. Keep retained provider-native history templated unless there is a compelling reason not to.
3. Convert outbound instruction messages from `system` to `developer` for the OpenAI model families that require or expect developer-message semantics.
4. Apply the same role normalization for both non-streaming and streaming request paths.
5. Keep the fix scoped to outbound request shaping. Do not rewrite stored session/core message roles unless truly necessary.

## Red -> green test plan

Add the tests first so the current behavior fails where it should and passes where it already works.

### Test group A: prove the currently-correct placeholder behavior

Add a regression test that uses:

1. `AgentCore`
2. `SystemMessageFeature`
3. a scripted `OpenAIResponsesProvider` subclass with a fake SDK client that captures `responses.create(...)`

Assertions:

1. The stored native history keeps the template text such as `{{CODEX_SYSTEM}}` / `{{TASKS}}` / `{{AGENTS}}`.
2. The actual SDK `input` contains the rendered text, not the placeholders.
3. This test should pass before the role-conversion fix and remain green afterwards.

### Test group B: reproduce the current bug first

Add at least one failing test that captures outbound input for a developer-message-first model, for example `gpt-5.4`.

Assertions for the failing version:

1. When the core/session has a `system` message, the outbound SDK `input` should use `role == "developer"`.
2. The same expectation should hold when the system message comes from `feature-system-message` rather than an explicit core message.
3. Cover both `call_api(...)` and `stream_api(...)`, or implement a shared helper and test both paths through that helper.

### Test group C: verify the fix

After implementation, assert:

1. `gpt-5.4` outbound requests send `developer` rather than `system`.
2. Non-targeted models that still accept ordinary `system` semantics keep their current outbound role unless you intentionally broaden the mapping.
3. Placeholder substitution still works in the same request after role normalization.

## Implementation notes

1. Prefer a shared outbound-input normalization helper in `OpenAIResponsesProvider` so non-streaming and streaming cannot drift.
2. Keep the conversion late enough that retained native history remains stable and request-time rendering from `feature-system-message` is preserved.
3. If model-family detection needs a small helper, keep it explicit and documented. Avoid ad hoc string checks scattered across request paths.
4. If the best scope turns out to be broader than `gpt-5.4`, document the chosen model family boundaries in tests.

## Suggested files to touch

1. `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
2. `plugins/openai_responses/tests/test_openai_responses_provider_unit.py`
3. If the clearest regression lives at the stack level: add a focused integration-style test under `plugins/openai_responses/tests/`

## Definition of done

1. New tests land in a red-green order and describe the bug clearly.
2. Placeholder rendering is explicitly covered for `openai_responses`.
3. Outbound role conversion is fixed for the targeted developer-message-first models.
4. Both non-streaming and streaming request paths are covered.

## Execution plan (added during completion)

Execution approach: staged, tests-first. Add regression coverage first, then make a small provider-only request-shaping change, then run focused verification.

1. Expand `plugins/openai_responses/tests/test_openai_responses_provider_unit.py` with request-capture tests that assert the exact `responses.create(..., input=...)` payload for both `call_api(...)` and `stream_api(...)`.
2. Add placeholder-rendering regression coverage using the real `SystemMessageFeature` flow so the tests prove both of these together:
   - retained native history keeps the templated `system` message content
   - outbound SDK `input` contains rendered text with placeholders resolved
3. Add red-first outbound role-normalization tests for developer-message-first models covering both:
   - an explicit core `system` message
   - a `system` message injected/rendered by `feature-system-message`
4. Use `gpt-5-mini` as the GPT-5 family regression target and also cover at least one `o`-family model so the broadened scope is explicit in tests.
5. Add at least one non-target model regression assertion, for example `gpt-4.1-mini`, to prove ordinary `system` behavior stays unchanged outside the targeted families.
6. Implement a shared outbound-input preparation helper in `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py` so `call_api(...)` and `stream_api(...)` cannot drift.
7. Keep role normalization late in request shaping, after `request["messages"]` override selection, so stored provider-native history remains templated and stable while only outbound request items are rewritten.
8. Define an explicit helper for the model-family boundary and scope it to developer-message-first OpenAI families currently targeted by this task:
   - `gpt-5*`
   - `o1*`
   - `o3*`
   - `o4*`
9. Run focused verification with `pytest plugins/openai_responses/tests/test_openai_responses_provider_unit.py -q` and any additional targeted OpenAI Responses test file if the new regressions are clearer at the stack level.
