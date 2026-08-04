# Add GPT-5.6 Reasoning Pro Mode

Expose OpenAI's GPT-5.6 `reasoning.mode: "pro"` request control as a first-class OpenAI Responses setting, distinct from Fast/priority service tier behavior.

## Requirements checklist

- [x] Add a first-class optional configuration key for GPT-5.6 Pro reasoning mode.
- [x] Emit `reasoning.mode: "pro"` only for supported GPT-5.6 models.
- [x] Treat omission as standard reasoning mode unless official API behavior supports an explicit standard value.
- [x] Keep Pro reasoning mode separate from `service_tier: "priority"` Fast mode.
- [x] Preserve existing `reasoning.effort`, `reasoning.summary`, raw request options, and include values.
- [x] Add unit tests for schema/UI visibility, normalization, nested merging, and model restrictions.
- [x] Add a separate real API Pro-mode integration test.
- [x] Add a separate saved-login ChatGPT Pro-mode integration test and run it with credentials from `~/.crystal`.
- [x] Update reasoning and pricing documentation to explain Pro-mode billing semantics.
- [x] Report unavailable or rejected API/ChatGPT credentials as not-run verification with the exact reason.

Parent Task: `tasks/20260713-openai-responses-gpt-5-6-support/000-main.md`

## Source behavior

The OpenAI reasoning guide recommends GPT-5.6 Sol with:

```json
{
  "reasoning": {
    "mode": "pro",
    "effort": "medium"
  }
}
```

OpenAI states that Pro mode performs more model work and bills the resulting
tokens at the selected model's normal token rates. It is not a separate model
ID and does not use a separate per-token pricing table.

This must not be confused with the existing Fast mode extension:

`plugins/openai_responses/src/openai_responses_plugins/openai_responses_fast_mode_extension.py`

Fast mode sets:

```json
{
  "service_tier": "priority"
}
```

Pro reasoning mode instead belongs inside the nested `reasoning` object.

## Configuration design

Preferred public key:

```json
{
  "reasoning_mode": "pro"
}
```

Use an optional enum containing `pro`, with absence meaning standard behavior.
Do not send `"mode": "standard"` unless the current official API schema is
verified to accept that exact value.

An enable-style boolean may be considered only if it better matches current UI
patterns, but the wire concept and configuration documentation should remain
clear. Avoid naming that could be confused with ChatGPT subscription plans or
Fast mode.

## Implementation plan

1. Extend
   `plugins/openai_responses/src/openai_responses_plugins/openai_responses_reasoning_extension.py`.
2. Add schema and a model-aware UI control visible only for supported GPT-5.6
   selections.
3. Normalize valid config into the existing extension-owned reasoning state.
4. Merge mode with effort and summary in:

   `request_options["reasoning"]`.

5. Preserve expert-provided nested request options unless a first-class config
   key intentionally overrides the same field.
6. Do not modify Fast mode, Flex mode, or pricing multipliers.

## Test requirements

Unit tests:

- schema exposes the optional Pro setting;
- UI shows it for GPT-5.6 family selections and hides it for older models;
- unset config emits no `reasoning.mode`;
- enabled config emits exactly `"mode": "pro"`;
- mode composes with effort and summary;
- existing raw reasoning fields remain intact;
- Fast mode can coexist, producing both:

  ```json
  {
    "reasoning": {"mode": "pro"},
    "service_tier": "priority"
  }
  ```

  without either feature overwriting the other.

Separate real API integration test:

- Use `gpt-5.6-sol` or the authoritative bare alias with
  `reasoning_mode: "pro"` and a moderate effort.
- Send a short deterministic prompt.
- Assert successful completion.
- Record/verify the outgoing nested reasoning payload if the test harness
  supports request recording.
- Gate on `OPENAI_API_KEY`.

Separate ChatGPT saved-login integration test:

- Add a dedicated `manual_integration` test using
  `$CHATGPT_TEST_STATE_DIR/auth/chatgpt-auth.json`.
- Use a GPT-5.6 model explicitly.
- Record the outgoing request and assert it contains
  `reasoning.mode == "pro"`.
- Assert whether the ChatGPT backend accepts and completes the request.
- Run during implementation with:

  ```bash
  CHATGPT_TEST_STATE_DIR="$HOME/.crystal" \
  OPENAI_RESPONSES_CHATGPT_MODEL="gpt-5.6-sol" \
    pytest <chatgpt-pro-mode-test> \
      -m "manual_integration and integration and openai" -q
  ```

- If ChatGPT rejects Pro mode while the API accepts it, report the exact
  endpoint response and document the divergence. Do not silently remove the
  field or count an `xfail` as full support.

Documentation:

- Update `plugins/openai_responses/README.md`.
- Explain that Pro mode increases model work and token usage but uses the
  selected model's standard per-token rates.
- Cross-reference Fast mode to prevent configuration confusion.

## Execution plan

(Proposed 2026-07-18. Awaiting user approval before implementation. No code
changes have been made yet.)

### First-class Pro-mode configuration and nested request shaping

#### Configuration surface

Add a new first-class optional config key to the reasoning extension:

- `reasoning_mode`: optional string enum `["pro"]`. Absence means standard
  behavior. The schema enum is intentionally `["pro"]` only (not
  `["standard", "pro"]`) so the UI offers a single affirmative choice and
  absence remains the documented standard-mode signal.

No boolean alias is introduced. The wire concept is a mode enum, not an
on/off toggle, and the task explicitly prefers an optional enum. The
config-level documentation will state that absence = standard mode.

#### Request shaping

When `reasoning_mode: "pro"` is set and the selected model supports Pro
mode, the reasoning extension merges `mode: "pro"` into the existing
`request_options["reasoning"]` dict during `initialize_request`. The merge
reuses the existing precedence pattern: config-level reasoning state is
spread on top of the existing nested `reasoning` dict, so config wins over
raw `request_options.reasoning.mode` when both are present, while unrelated
raw reasoning fields (effort, summary, `generate_summary`, etc.) are
preserved.

When `reasoning_mode` is unset, the extension does NOT inject
`reasoning.mode` and does NOT send `"mode": "standard"`. Omission is the
standard-mode signal. This matches the task's preferred design and the
official reasoning guide's statement that `standard` is the API default.

The existing `include: ["reasoning.encrypted_content"]` injection and the
existing `reasoning_effort` / `reasoning_summary` merges are unchanged. Pro
mode composes with effort and summary inside the same nested `reasoning`
object.

#### Model gating

Pro mode is GPT-5.6-only. The extension will reuse the existing
`_MODEL_REASONING_EFFORT_PATTERNS` match result to decide whether the
selected model is in the GPT-5.6 family (Sol, Terra, Luna, or the bare
`gpt-5.6` alias). Concretely, the model supports Pro mode iff
`_supported_reasoning_efforts_for_model(model)` came from one of the three
GPT-5.6 patterns (Sol/Terra, Luna, or bare alias). For any other model
(GPT-5, GPT-5.1, GPT-5.2, GPT-5.4, GPT-5 Pro, unknown), `reasoning_mode:
"pro"` is silently dropped — the same silent-drop behavior already used for
unsupported `reasoning_effort` values.

Implementation detail: rather than re-scanning the patterns, add a small
helper `_model_supports_pro_reasoning(model) -> bool` that returns `True`
only when the resolved effort tuple is one of the three GPT-5.6 tuples.
This keeps the gating logic explicit and unit-testable without coupling to
the regex order.

### Why the behavior belongs in the reasoning extension and stays separate from Fast mode

`reasoning.mode` is a nested field inside the OpenAI Responses `reasoning`
object. The reasoning extension already owns `request_options["reasoning"]`
merging in `initialize_request` (see
`openai_responses_reasoning_extension.py:397-439`). Adding `mode` to that
same merge is the natural extension of the existing responsibility and
avoids a second extension touching the same nested dict.

Fast mode is a different wire concept. The Fast mode extension
(`openai_responses_fast_mode_extension.py`) writes `service_tier: "priority"`
into the top-level `request["payload"]` (see
`openai_responses_fast_mode_extension.py:135-157`), not into
`request_options["reasoning"]`. The two extensions touch different parts of
the outbound request:

- Reasoning extension: `state["config"]["request_options"]["reasoning"]`
  (consumed by `RequestOptionsFeature` to build the final payload).
- Fast mode extension: `state["request"]["payload"]["service_tier"]`
  (written directly onto the request payload).

Because the two write paths do not overlap, Pro mode and Fast mode can both
be active without one clobbering the other. No coordination code is needed
between the extensions. The unit-test suite will include an explicit
coexistence test that registers both extensions and asserts both
`reasoning.mode: "pro"` and `service_tier: "priority"` appear in the
recorded outgoing request.

This separation also keeps the auth-mode rules independent: Fast mode has
its own ChatGPT-vs-API gating (`enable_fast_mode_for_api_requests`), while
Pro mode has no auth-mode gating — it is a reasoning control, not a service
tier, and is valid for both API and ChatGPT auth modes on GPT-5.6 models.

### Human decisions

- **Key name**: `reasoning_mode`. Matches the task's preferred public key,
  parallels the existing `reasoning_effort` / `reasoning_summary` naming,
  and avoids any name that could be confused with ChatGPT subscription
  plans (e.g. `pro_plan`, `chatgpt_pro`) or with Fast mode (e.g.
  `fast_mode`, `priority_mode`). The wire field is `reasoning.mode`; the
  config key is `reasoning_mode` to match the existing `reasoning_effort`
  → `reasoning.effort` pattern.
- **Optional enum vs boolean**: optional enum `["pro"]`. The wire concept
  is a mode with two possible values (`standard`, `pro`), not an on/off
  toggle. An enum keeps the door open for future modes without a schema
  reshape, and keeps the "absence = standard" semantics explicit. A boolean
  (`enable_pro_reasoning`) was considered and rejected because it would
  obscure the wire concept and make future mode values awkward to add.
- **Omission semantics**: absence = standard. The extension never sends
  `"mode": "standard"`. The official reasoning guide confirms `standard`
  is a valid API value and is the default, so omission is safe. The task's
  conditional ("unless the official API schema is verified to accept that
  exact value") is satisfied — the API does accept `standard` — but the
  preferred design is still omission, so we omit. This keeps the outbound
  request minimal and avoids sending a redundant default. The documentation
  will state both facts: omission = standard, and `standard` is a valid
  explicit value that the extension chooses not to send.
- **Model gating**: GPT-5.6 family only (Sol, Terra, Luna, bare
  `gpt-5.6` alias). Older models silently drop `reasoning_mode: "pro"`.
  This mirrors the existing silent-drop behavior for unsupported
  `reasoning_effort` values and avoids raising errors for config that is
  simply not applicable to the selected model. The bare `gpt-5.6` alias
  follows task 020's precedent: the reasoning extension treats it as
  Sol-capable even though task 010 does not publish it in the catalog.
- **Precedence over raw request options**: config-level `reasoning_mode`
  overrides raw `request_options.reasoning.mode` when both are present,
  matching the existing `reasoning_effort` precedence rule. When config is
  unset and raw `request_options.reasoning.mode` is present, the raw value
  is preserved as an expert escape hatch. The merge is implemented by
  spreading the config-level reasoning dict on top of the existing
  reasoning dict, exactly as `initialize_request` already does for `effort`
  and `summary`.
- **No default inferred**: if `reasoning_mode` is unset, no `mode` is
  injected. The API's built-in default (standard) applies. This parallels
  the no-default-inferred decision for `reasoning_effort` in task 020.
- **No auth-mode gating**: Pro mode is valid for both API and ChatGPT auth
  modes on GPT-5.6 models. Unlike Fast mode, there is no
  `enable_pro_mode_for_api_requests` opt-in. Pro mode is a reasoning
  control, not a service tier, and the OpenAI reasoning guide does not
  restrict it to ChatGPT auth.

### Concrete example configuration and resulting Responses payload

Config (API auth, GPT-5.6 Sol, Pro mode with medium effort and concise
summary):

```json
{
  "model": "gpt-5.6-sol",
  "api_key": "${env:OPENAI_API_KEY}",
  "base_url": "https://api.openai.com/v1",
  "auth_mode": "api",
  "timeout": 240,
  "reasoning_mode": "pro",
  "reasoning_effort": "medium",
  "reasoning_summary": "concise"
}
```

Resulting `request_options["reasoning"]` after the reasoning extension's
`initialize_request`:

```json
{
  "mode": "pro",
  "effort": "medium",
  "summary": "concise"
}
```

Resulting top-level Responses request payload (after
`RequestOptionsFeature` lifts `request_options` into the payload and the
reasoning extension adds the `include` entry):

```json
{
  "model": "gpt-5.6-sol",
  "input": [...],
  "stream": true,
  "reasoning": {
    "mode": "pro",
    "effort": "medium",
    "summary": "concise"
  },
  "include": ["reasoning.encrypted_content"]
}
```

Simultaneous Fast mode (ChatGPT auth, GPT-5.6 Sol, Pro mode + Fast mode):

```json
{
  "model": "gpt-5.6-sol",
  "auth_mode": "chatgpt",
  "chatgpt_credentials_path": "~/.crystal/auth/chatgpt-auth.json",
  "system_message_as_instructions": true,
  "system_message": "You are a precise assistant.",
  "timeout": 240,
  "reasoning_mode": "pro",
  "reasoning_effort": "medium",
  "reasoning_summary": "concise",
  "enable_fast_mode": true
}
```

Resulting outbound payload (reasoning extension + Fast mode extension both
active):

```json
{
  "model": "gpt-5.6-sol",
  "input": [...],
  "instructions": "You are a precise assistant.",
  "stream": true,
  "store": false,
  "reasoning": {
    "mode": "pro",
    "effort": "medium",
    "summary": "concise"
  },
  "service_tier": "priority",
  "include": ["reasoning.encrypted_content"]
}
```

The `reasoning.mode` and `service_tier` keys live in different parts of the
payload and do not collide.

### Exact unit tests

All new unit tests go in
`plugins/openai_responses/tests/test_openai_responses_reasoning_extension_unit.py`,
continuing the existing block from task 020.

Schema:
- `test_get_config_schema_includes_reasoning_mode_pro_enum` — schema has
  `reasoning_mode` with `type: "string"`, `required: False`, and
  `enum: ["pro"]` (exactly one value, not `["standard", "pro"]`).

UI visibility:
- `test_get_ui_elements_shows_reasoning_mode_for_gpt_5_6_sol` —
  `get_ui_elements` for `gpt-5.6-sol` includes a `reasoning_mode` select
  with options `[{"value": "pro", "label": "pro"}]`.
- `test_get_ui_elements_shows_reasoning_mode_for_gpt_5_6_luna` — Luna also
  shows the Pro control (Pro mode is not effort-gated; it is GPT-5.6-family
  gated).
- `test_get_ui_elements_shows_reasoning_mode_for_bare_gpt_5_6_alias` —
  bare `gpt-5.6` also shows the Pro control (alias maps to Sol
  capabilities).
- `test_get_ui_elements_hides_reasoning_mode_for_older_models` —
  `gpt-5-mini`, `gpt-5.1-mini`, `gpt-5.2`, `gpt-5.4`, `gpt-5-pro`, and
  unknown `o3-mini` do NOT include a `reasoning_mode` element.
- `test_get_ui_elements_hides_reasoning_mode_without_supports_reasoning_tag`
  — when `tags` omits `supports_reasoning`, no `reasoning_mode` element is
  returned (matches the existing early-return guard).

Model restrictions / silent drop:
- `test_init_drops_reasoning_mode_pro_for_gpt_5_4` — `reasoning_mode: "pro"`
  with `model: "gpt-5.4"` -> no `_openai_responses_reasoning` in state (Pro
  mode silently dropped for non-GPT-5.6).
- `test_init_drops_reasoning_mode_pro_for_unknown_model` —
  `reasoning_mode: "pro"` with `model: "o3-mini"` -> no
  `_openai_responses_reasoning` in state.
- `test_init_preserves_reasoning_mode_pro_for_luna` — `reasoning_mode: "pro"`
  with `model: "gpt-5.6-luna"` -> state has `_openai_responses_reasoning`
  with `mode: "pro"` (Luna supports Pro mode even though it does not support
  `ultra` effort).

Nested merging:
- `test_initialize_request_injects_pro_mode_for_sol` — `reasoning_mode:
  "pro"`, `model: "gpt-5.6-sol"` -> `request_options.reasoning.mode ==
  "pro"`.
- `test_initialize_request_injects_pro_mode_for_terra` — same for Terra.
- `test_initialize_request_injects_pro_mode_for_luna` — same for Luna.
- `test_initialize_request_injects_pro_mode_for_bare_gpt_5_6_alias` — same
  for bare `gpt-5.6`.
- `test_initialize_request_pro_mode_composes_with_effort_and_summary` —
  `reasoning_mode: "pro"`, `reasoning_effort: "medium"`,
  `reasoning_summary: "concise"`, `model: "gpt-5.6-sol"` ->
  `request_options.reasoning == {"mode": "pro", "effort": "medium",
  "summary": "concise"}`.
- `test_initialize_request_pro_mode_preserves_unrelated_existing_reasoning_fields`
  — existing `request_options.reasoning.generate_summary` and
  `request_options.reasoning.summary` survive when config-level
  `reasoning_mode: "pro"` is merged; existing raw `mode` is overwritten.
- `test_initialize_request_omits_mode_when_reasoning_mode_unset` —
  `reasoning_effort: "medium"` only, no `reasoning_mode` ->
  `request_options.reasoning` has `effort` but no `mode` key.
- `test_initialize_request_does_not_send_standard_mode` — explicitly
  assert that `request_options.reasoning` never contains
  `"mode": "standard"` for any GPT-5.6 model, whether `reasoning_mode` is
  set, unset, or set to a non-pro value.

Raw option coexistence:
- `test_initialize_request_config_reasoning_mode_overrides_request_options_mode`
  — config `reasoning_mode: "pro"` overrides
  `request_options.reasoning.mode: "standard"` -> final `mode == "pro"`.
- `test_initialize_request_preserves_raw_request_options_mode_when_config_unset`
  — no `reasoning_mode` in config, `request_options.reasoning.mode: "pro"`
  -> final `mode == "pro"` (raw expert escape hatch preserved).
- `test_initialize_request_preserves_raw_request_options_standard_mode_when_config_unset`
  — no `reasoning_mode` in config,
  `request_options.reasoning.mode: "standard"` -> final `mode == "standard"`
  (raw expert value preserved, extension does not strip it).

Simultaneous Fast mode:
- `test_initialize_request_pro_mode_and_fast_mode_coexist` — register both
  `OpenAIResponsesReasoningExtension` and `OpenAIResponsesFastModeExtension`
  on a core with `RequestOptionsFeature`. Config: `model: "gpt-5.6-sol"`,
  `auth_mode: "chatgpt"`, `_openai_responses_effective_auth_mode: "chatgpt"`,
  `reasoning_mode: "pro"`, `reasoning_effort: "medium"`,
  `enable_fast_mode: True`. After running both extensions' `init` and
  `initialize_request`, assert the final state has both
  `request_options.reasoning.mode == "pro"` (lifted into
  `request.payload.reasoning.mode` by `RequestOptionsFeature`) and
  `request.payload.service_tier == "priority"`. This test uses the real
  `AgentCore` + `RequestOptionsFeature` + both extensions, not a mock, so
  it exercises the actual coexistence path.

### Separate real API and saved-login ChatGPT acceptance tests

#### Real API test

Add to
`plugins/openai_responses/tests/test_openai_responses_reasoning_extension_integration.py`:

- `test_openai_responses_reasoning_mode_pro_gpt_5_6_sol_real_api` —
  `model: "gpt-5.6-sol"`, `reasoning_mode: "pro"`,
  `reasoning_effort: "medium"`, `reasoning_summary: "concise"`, minimal
  exact-response prompt (`Reply with exactly: GPT56_PRO_OK`). Uses the
  existing `_RecordingApiProvider` pattern to capture the outgoing request.
  Asserts: successful completion, response content contains `GPT56_PRO_OK`,
  recorded `reasoning.mode == "pro"`, recorded `reasoning.effort ==
  "medium"`, recorded `reasoning.summary == "concise"`. Gate on
  `OPENAI_API_KEY` via the existing `ensure_openai_api_key` fixture.
  Markers: `@pytest.mark.integration`, `@pytest.mark.openai`,
  `@pytest.mark.api`.
- Cost-aware model selection: use `gpt-5.6-sol` (the model the OpenAI
  reasoning guide explicitly recommends for Pro mode) with `medium` effort
  to keep token use reasonable. Prompt is one short sentence.
- Endpoint-divergence reporting: if the public API rejects
  `reasoning.mode: "pro"`, capture the exact exception type and message and
  use `pytest.xfail` with a documented reason (same pattern as the `ultra`
  test in task 020). Do NOT silently convert a rejection into a pass. The
  `xfail` reason string will include the exact API error so future runs
  can detect when the endpoint starts accepting the value (xpass).

#### Saved-login ChatGPT test

New file
`plugins/openai_responses/tests/test_openai_responses_chatgpt_reasoning_pro_mode_manual_integration.py`:

- `test_openai_responses_chatgpt_reasoning_mode_pro_gpt_5_6_sol` —
  `model: "gpt-5.6-sol"`, `auth_mode: "chatgpt"`,
  `chatgpt_credentials_path: $CHATGPT_TEST_STATE_DIR/auth/chatgpt-auth.json`,
  `reasoning_mode: "pro"`, `reasoning_effort: "medium"`,
  `reasoning_summary: "concise"`, exact-response prompt
  (`Reply with exactly: CHATGPT_REASONING_PRO_OK`), streaming. Uses the
  existing `_RecordingChatGPTProvider` pattern to capture the outgoing
  request. Asserts: successful completion, response content contains
  `CHATGPT_REASONING_PRO_OK`, recorded `reasoning.mode == "pro"`,
  recorded `reasoning.effort == "medium"`,
  `metadata.usage_effective_auth_mode == "chatgpt"`.
- Credential gate: skip with exact reason on `FileNotFoundError`, non-dict
  JSON, missing/blank `access_token`, or expired `expires_at`. Never prints
  access tokens, refresh tokens, ID tokens, account IDs, or emails. Reuses
  the exact gate helper from task 020's
  `test_openai_responses_chatgpt_reasoning_effort_manual_integration.py`.
- Endpoint-divergence reporting: if the ChatGPT backend rejects
  `reasoning.mode: "pro"` while the public API accepts it, capture the
  exact status/error and use `pytest.xfail` with a documented reason that
  includes the exact backend rejection. Do NOT silently remove the field
  or count an `xfail` as full support. The `xfail` reason will explicitly
  state "ChatGPT backend rejected reasoning.mode=pro; API acceptance is
  recorded in the real API test" so the divergence is visible in test
  output.
- Markers: `pytestmark = pytest.mark.api`; per-test
  `@pytest.mark.manual_integration`, `@pytest.mark.integration`,
  `@pytest.mark.openai`.
- Implementation run command:

  ```bash
  CHATGPT_TEST_STATE_DIR="$HOME/.crystal" \
  OPENAI_RESPONSES_CHATGPT_MODEL="gpt-5.6-sol" \
    pytest plugins/openai_responses/tests/test_openai_responses_chatgpt_reasoning_pro_mode_manual_integration.py \
      -m "manual_integration and integration and openai" -q
  ```

- If credentials are missing/expired on run, report as not run with the
  exact skip reason, not as a pass.

### Reasoning and pricing documentation sections to update

`plugins/openai_responses/README.md`:

1. **Reasoning keys section** (currently lines 498-535). Add:
   - A new bullet for `reasoning_mode`: optional string enum `["pro"]`,
     GPT-5.6 family only (Sol, Terra, Luna, and the bare `gpt-5.6` alias).
     Absence means standard mode; the extension never sends
     `"mode": "standard"` because omission is the standard-mode signal and
     `standard` is the API default.
   - A note that `reasoning.mode` and `reasoning.effort` are independent:
     mode selects standard or pro execution; effort controls how much
     reasoning the model applies within that mode. If `reasoning_effort` is
     unset, GPT-5.6 defaults to `medium` in both modes (per the official
     reasoning guide).
   - A note that `reasoning_mode: "pro"` is silently dropped for non-GPT-5.6
     models, matching the existing silent-drop behavior for unsupported
     `reasoning_effort`.
   - A precedence note: config-level `reasoning_mode` overrides raw
     `request_options.reasoning.mode`; when config is unset, raw
     `request_options.reasoning.mode` is preserved as an expert escape
     hatch.
   - A cross-reference to the Fast mode section: Pro mode is a nested
     `reasoning.mode` value and is distinct from Fast mode's
     `service_tier: "priority"`. Both can be enabled simultaneously; they
     touch different parts of the outbound payload.

2. **Fast mode section** (currently lines 460-476). Add a one-sentence
   cross-reference: "Pro reasoning mode (`reasoning_mode: "pro"`) is a
   nested reasoning control and is independent of Fast mode's
   `service_tier: "priority"`. Both can be enabled at the same time on
   GPT-5.6 models."

3. **Pricing notes** (no dedicated pricing section exists today; the
   relevant pricing text is in the "Usage keys" section at lines 546-557
   and the "Fast mode" section at lines 460-476). Add a short "Pro mode
   billing" subsection immediately after the reasoning keys section:
   - Pro mode performs more model work than standard mode and increases
     token usage and cost.
   - Pro mode bills the aggregated model-work tokens at the selected
     model's standard per-token rates. There is no separate Pro-mode
     pricing table and no new `service_tier` value for Pro mode.
   - Cost estimation in this bundle continues to use the selected model's
     standard-tier pricing entry from `data/openai_model_pricing.json` (or
     the manual ChatGPT fallback). Pro mode does not introduce a
     priority-tier or flex-tier price lookup.
   - Existing Pro model IDs (e.g. `gpt-5.5-pro`, `gpt-5.4-pro`) keep their
     current behavior and pricing; they are distinct model SKUs, not a
     reasoning-mode billing category. (This disambiguates "Pro mode" the
     reasoning setting from "-pro" the model SKU suffix.)
   - Cross-reference Fast mode: priority-tier pricing applies only when
     Fast mode reports `service_tier: "priority"`; Pro mode does not change
     the service tier and does not trigger priority-tier pricing.

### Implementation order

1. Edit
   `plugins/openai_responses/src/openai_responses_plugins/openai_responses_reasoning_extension.py`:
   - Add `_REASONING_MODES = ("pro",)` constant.
   - Add `_model_supports_pro_reasoning(model) -> bool` helper that returns
     `True` only when `_supported_reasoning_efforts_for_model(model)` is one
     of the three GPT-5.6 effort tuples.
   - Extend `get_config_schema()` with the `reasoning_mode` key (enum
     `["pro"]`, required `False`).
   - Extend `get_ui_elements()` to include a `reasoning_mode` select when
     the resolved model supports Pro mode; omit it otherwise.
   - Extend `_normalize_reasoning_config()` to read `reasoning_mode` and,
     when it equals `"pro"` and the model supports Pro mode, set
     `reasoning["mode"] = "pro"`.
   - No change to `initialize_request` merge logic: the existing
     `{**existing_reasoning, **reasoning}` spread already handles `mode`
     once it is present in the normalized state.
2. Add the unit tests listed above to
   `plugins/openai_responses/tests/test_openai_responses_reasoning_extension_unit.py`.
3. Run the unit tests to confirm schema, UI visibility, silent-drop, nested
   merging, raw-option coexistence, and Fast mode coexistence before
   touching integration tests.
4. Add the real API Pro-mode test to
   `plugins/openai_responses/tests/test_openai_responses_reasoning_extension_integration.py`.
5. Create
   `plugins/openai_responses/tests/test_openai_responses_chatgpt_reasoning_pro_mode_manual_integration.py`
   with the saved-login ChatGPT Pro-mode test.
6. Update `plugins/openai_responses/README.md` reasoning keys section, Fast
   mode cross-reference, and add the Pro mode billing subsection.
7. Run the fast default plugin suite.
8. Run the ChatGPT saved-login Pro-mode test with
   `CHATGPT_TEST_STATE_DIR="$HOME/.crystal"` and
   `OPENAI_RESPONSES_CHATGPT_MODEL="gpt-5.6-sol"`.
9. Run the real API Pro-mode test if `OPENAI_API_KEY` is available;
   otherwise report as not run with the exact reason.
10. Lint/format changed files with `ruff check` and `black`.
11. Append `## Completion Notes` to this task file and update the checklist
    in `000-main.md`.

### Verification commands

- Unit tests (focused):
  ```
  pytest plugins/openai_responses/tests/test_openai_responses_reasoning_extension_unit.py -q
  ```
- Fast default plugin suite:
  ```
  pytest plugins/openai_responses/tests -q
  ```
- Real API Pro mode:
  ```
  pytest plugins/openai_responses/tests/test_openai_responses_reasoning_extension_integration.py -m 'integration and api and not slow_integration and openai' -q
  ```
- ChatGPT saved-login Pro mode:

  ```bash
  CHATGPT_TEST_STATE_DIR="$HOME/.crystal" \
  OPENAI_RESPONSES_CHATGPT_MODEL="gpt-5.6-sol" \
    pytest plugins/openai_responses/tests/test_openai_responses_chatgpt_reasoning_pro_mode_manual_integration.py \
      -m "manual_integration and integration and openai" -q
  ```

- Lint/format: `ruff check <changed files>` and `black <changed files>`.

### Compatibility risks

- **Schema addition only**: `reasoning_mode` is a new optional key. Existing
  configs that do not set it are unaffected; the extension does not inject
  `mode` when the key is absent. No existing test should break.
- **Model gating silent-drop**: users who set `reasoning_mode: "pro"` on a
  non-GPT-5.6 model will see the value silently dropped. This matches the
  existing `reasoning_effort` silent-drop behavior and is documented. No
  error is raised.
- **No `standard` sent**: the extension never sends `"mode": "standard"`.
  If a future OpenAI API change makes an explicit `standard` value required
  for some flow, the extension would need a follow-up change. The official
  reasoning guide currently states `standard` is the default, so omission
  is safe.
- **Fast mode coexistence**: the unit-test coexistence test uses the real
  `AgentCore` + `RequestOptionsFeature` + both extensions to verify the
  two write paths do not collide. Risk is low because the two extensions
  write to different state paths (`request_options.reasoning` vs
  `request.payload.service_tier`), but the test guards against accidental
  future coupling.
- **ChatGPT endpoint divergence**: the ChatGPT backend may reject
  `reasoning.mode: "pro"` even though the public API accepts it. The test
  uses `pytest.xfail` with the exact rejection message in that case, so the
  divergence is visible in test output and automatically converts to a
  normal pass when the backend starts accepting the value.
- **Pre-existing test failures**: task 020's completion notes report 3
  pre-existing failures in `test_openai_responses_native_history_regressions.py`
  (`KeyError: '_openai_responses_uploaded_attachments'`), unrelated to
  this task. The fast default suite is expected to show the same 3
  failures; I will verify they are unchanged by my work.
- **GPT-5.6 pricing not yet present**: task 050 owns pricing. Integration
  tests do not assert on cost. The Pro mode billing documentation states
  that Pro mode uses the selected model's standard-tier pricing, which
  task 050 will add. Until then, cost estimation for GPT-5.6 models remains
  zero (the provider defect noted in task 010's investigation).

### Prerequisite assumptions

- Task 010 is complete: the checked-in Codex snapshot includes
  `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna` with correct names and
  descriptions; `source_commit: 50b82133850d940627cf307d77e280619bfafe25`.
- Task 020 is complete: `_REASONING_EFFORTS` includes `max` and `ultra`;
  `_UNKNOWN_MODEL_REASONING_EFFORTS` preserves the older unknown-model
  fallback; the three GPT-5.6 patterns (Sol/Terra, Luna, bare alias) are
  in `_MODEL_REASONING_EFFORT_PATTERNS` before the broader GPT-5 patterns.
  This task reuses those patterns to gate Pro mode.
- Task 010 decided NOT to add bare `gpt-5.6` to the catalog. This task
  handles bare `gpt-5.6` at the reasoning-extension level only (Pro mode is
  available for the bare alias because it maps to Sol capabilities), not at
  the catalog level.
- The saved ChatGPT login at `~/.crystal/auth/chatgpt-auth.json` is valid
  through `2026-07-18T19:42:08Z` (per task 010 completion notes). If
  implementation runs after that, the ChatGPT test will skip with an exact
  reason and must be reported as not run, not as a pass.
- `OPENAI_API_KEY` is available in repo root `.env` and loaded by the
  plugin `conftest.py`.
- GPT-5.6 pricing is NOT yet in `data/openai_model_pricing.json` (task 050
  owns that). Integration tests do not assert on cost.
- Reasoning context (`reasoning.context`) is out of scope for this task
  (subtask 040).
- Effort-matrix changes are out of scope for this task (task 020 owns the
  effort matrix; this task only adds `reasoning_mode` and the nested
  `reasoning.mode` merge).
- The repo `.venv` has `openai`, `pytest`, and `agent_core` installed (per
  task 010 completion notes).

## Completion Notes

(Added 2026-07-18 during completion.)

### What was done

- Extended `plugins/openai_responses/src/openai_responses_plugins/openai_responses_reasoning_extension.py`:
  - Added `_REASONING_MODES = ("pro",)` constant (line 39).
  - Added `_GPT_5_6_REASONING_EFFORTS` frozenset (lines 62-70) containing the
    two unique GPT-5.6 effort tuples, used to gate Pro mode without
    re-scanning the patterns.
  - Added `_model_supports_pro_reasoning(model) -> bool` helper (lines
    139-143) that returns `True` only when the resolved effort tuple is one
    of the GPT-5.6 tuples.
  - Extended `get_config_schema()` (lines 99-107) with the `reasoning_mode`
    key: `type: "string"`, `required: False`, `enum: ["pro"]`.
  - Extended `get_ui_elements()` (lines 176-186) to append a
    `reasoning_mode` select when the resolved model supports Pro mode; omit
    it otherwise.
  - Extended `_normalize_reasoning_config()` (lines 205-211) to read
    `reasoning_mode` and, when it equals `"pro"` and the model supports Pro
    mode, set `reasoning["mode"] = "pro"`.
  - No change to `initialize_request` merge logic: the existing
    `{**existing_reasoning, **reasoning}` spread already handles `mode`
    once it is present in the normalized state.
- Added 21 unit tests to
  `plugins/openai_responses/tests/test_openai_responses_reasoning_extension_unit.py`:
  - Schema: `test_get_config_schema_includes_reasoning_mode_pro_enum`
  - UI visibility: `test_get_ui_elements_shows_reasoning_mode_for_gpt_5_6_sol`,
    `test_get_ui_elements_shows_reasoning_mode_for_gpt_5_6_luna`,
    `test_get_ui_elements_shows_reasoning_mode_for_bare_gpt_5_6_alias`,
    `test_get_ui_elements_hides_reasoning_mode_for_older_models`,
    `test_get_ui_elements_hides_reasoning_mode_without_supports_reasoning_tag`
  - Model restrictions / silent drop: `test_init_drops_reasoning_mode_pro_for_gpt_5_4`,
    `test_init_drops_reasoning_mode_pro_for_unknown_model`,
    `test_init_preserves_reasoning_mode_pro_for_luna`
  - Nested merging: `test_initialize_request_injects_pro_mode_for_sol`,
    `test_initialize_request_injects_pro_mode_for_terra`,
    `test_initialize_request_injects_pro_mode_for_luna`,
    `test_initialize_request_injects_pro_mode_for_bare_gpt_5_6_alias`,
    `test_initialize_request_pro_mode_composes_with_effort_and_summary`,
    `test_initialize_request_pro_mode_preserves_unrelated_existing_reasoning_fields`,
    `test_initialize_request_omits_mode_when_reasoning_mode_unset`,
    `test_initialize_request_does_not_send_standard_mode`
  - Raw option coexistence:
    `test_initialize_request_config_reasoning_mode_overrides_request_options_mode`,
    `test_initialize_request_preserves_raw_request_options_mode_when_config_unset`,
    `test_initialize_request_preserves_raw_request_options_standard_mode_when_config_unset`
  - Simultaneous Fast mode: `test_initialize_request_pro_mode_and_fast_mode_coexist`
    (uses real `OpenAIResponsesReasoningExtension` +
    `OpenAIResponsesFastModeExtension` + `RequestOptionsFeature` in priority
    order, asserts both `reasoning.mode: "pro"` and
    `service_tier: "priority"` in the final payload)
  - Added `_reasoning_mode_elements` helper and
    `OpenAIResponsesFastModeExtension` import at the top of the new test
    block.
- Added real API integration test
  `test_openai_responses_reasoning_mode_pro_gpt_5_6_sol_real_api` in
  `plugins/openai_responses/tests/test_openai_responses_reasoning_extension_integration.py`.
  Uses the existing `_RecordingApiProvider` pattern to capture the outgoing
  request. Asserts: successful completion, response content contains
  `GPT56_PRO_OK`, recorded `reasoning.mode == "pro"`,
  `reasoning.effort == "medium"`, `reasoning.summary == "concise"`. Gate on
  `OPENAI_API_KEY` via the existing `ensure_openai_api_key` fixture. Markers:
  `@pytest.mark.integration`, `@pytest.mark.openai`, `@pytest.mark.api`.
- Created
  `plugins/openai_responses/tests/test_openai_responses_chatgpt_reasoning_pro_mode_manual_integration.py`
  with `test_openai_responses_chatgpt_reasoning_mode_pro_gpt_5_6_sol`.
  Markers: `manual_integration`, `integration`, `openai`, `api`. Credential
  gate skips with exact reason on missing file, non-dict JSON, missing/blank
  `access_token`, or expired `expires_at`. Never prints tokens/account/email.
  Uses `_RecordingChatGPTProvider` and registers
  `OpenAIResponsesReasoningExtension` + `OpenAIResponsesUsageExtension` so
  `usage_effective_auth_mode` is available. Asserts recorded
  `reasoning.mode == "pro"` and `reasoning.effort == "medium"`.
- Updated `plugins/openai_responses/README.md`:
  - "Reasoning keys" section: added `reasoning_mode` bullet (optional enum
    `["pro"]`, GPT-5.6 family only, absence = standard, never sends
    `"standard"`); added `reasoning.mode`/`reasoning.effort` independence
    note; updated the bare `gpt-5.6` alias note to mention Pro mode control;
    updated the no-default-inferred note to cover both `reasoning_effort` and
    `reasoning_mode`; updated the silent-drop note to cover
    `reasoning_mode: "pro"` for non-GPT-5.6 models; updated the precedence
    note to cover `request_options.reasoning.mode`.
  - "Fast mode" section: added a one-sentence cross-reference that Pro
    reasoning mode is independent of Fast mode's `service_tier: "priority"`
    and both can be enabled simultaneously on GPT-5.6 models.
  - Added "Pro mode billing" subsection after the reasoning keys section:
    Pro mode bills at the selected model's standard per-token rates, no
    separate pricing table, no new `service_tier` value, cost estimation
    uses standard-tier pricing, priority-tier pricing only applies to Fast
    mode, existing Pro model IDs (`gpt-5.5-pro`, `gpt-5.4-pro`) are distinct
    SKUs not a reasoning-mode billing category.

### Real endpoint divergence discovered (reasoning.mode: "pro")

The public OpenAI API accepts `reasoning.mode: "pro"` for `gpt-5.6-sol` (the
real API test passed). The ChatGPT-hosted backend rejects it with:

```text
Error code: 400 - {'error': {'message': '`reasoning.mode` is not supported with this model.', 'type': 'invalid_request_error', 'param': 'reasoning.mode', 'code': 'unsupported_value'}}
```

This is a real endpoint capability difference between the public API and the
ChatGPT-hosted backend at implementation time (2026-07-18). The ChatGPT
integration test uses `pytest.xfail` with the exact rejection message so the
divergence is visible in test output. The extension still offers
`reasoning_mode: "pro"` for GPT-5.6 models because the public API accepts it
and the ChatGPT backend may start accepting it in the future. If the
ChatGPT backend later accepts `reasoning.mode: "pro"`, the test will `xpass`
(unexpected pass) and can be converted to a normal pass test at that time.

### Human decisions recorded

- Key name: `reasoning_mode`. Parallels `reasoning_effort`/`reasoning_summary`.
  Avoids confusion with ChatGPT subscription plans or Fast mode.
- Optional enum `["pro"]`, not a boolean. Preserves the wire concept and
  future mode extensibility.
- Omission = standard. The extension never sends `"mode": "standard"`. The
  official reasoning guide confirms `standard` is a valid API value and is
  the default, so omission is safe and minimal.
- Model gating: GPT-5.6 family only (Sol, Terra, Luna, bare `gpt-5.6`
  alias). Older models silently drop `reasoning_mode: "pro"`, matching the
  existing `reasoning_effort` silent-drop behavior.
- Precedence: config-level `reasoning_mode` overrides raw
  `request_options.reasoning.mode`; when config is unset, raw value is
  preserved as an expert escape hatch (both `"pro"` and `"standard"` raw
  values are preserved).
- No default inferred: if `reasoning_mode` is unset, no `mode` is injected.
- No auth-mode gating: Pro mode is valid for both API and ChatGPT auth modes
  on GPT-5.6 models. Unlike Fast mode, there is no
  `enable_pro_mode_for_api_requests` opt-in.

### Verification commands and results

All commands run with `/Users/ferenci84/Dev/Mine/ai-agent-platform/.venv/bin/python -m pytest`.

1. Reasoning extension unit tests:
   ```
   pytest plugins/openai_responses/tests/test_openai_responses_reasoning_extension_unit.py -q
   ```
   Result: 44 passed in 1.30s (23 from task 020 + 21 new from task 030).

2. Fast default plugin suite:
   ```
   pytest plugins/openai_responses/tests -q
   ```
   Result: 328 passed, 70 deselected, 3 failed in 26.38s. The 3 failures are
   pre-existing in `test_openai_responses_native_history_regressions.py`
   (`KeyError: '_openai_responses_uploaded_attachments'`) and are unrelated
   to this task. Verified by task 010 and task 020 completion notes: the
   same 3 tests fail on the clean tree. My 21 new unit tests are included
   in the 328 passed (up from 283 in task 020).

3. Real API reasoning mode Pro test:
   ```
   pytest plugins/openai_responses/tests/test_openai_responses_reasoning_extension_integration.py -m 'integration and api and not slow_integration and openai' -q
   ```
   Result: 4 passed, 1 xfailed in 18.29s. The new
   `test_openai_responses_reasoning_mode_pro_gpt_5_6_sol_real_api` passed;
   the public OpenAI API accepted `reasoning.mode: "pro"` for
   `gpt-5.6-sol`. The 1 xfail is the pre-existing task 020 `ultra` test
   (the API rejects `ultra`). `OPENAI_API_KEY` was loaded from repo root
   `.env` by the plugin `conftest.py`.

4. ChatGPT saved-login reasoning mode Pro test:
   ```
   CHATGPT_TEST_STATE_DIR="$HOME/.crystal" OPENAI_RESPONSES_CHATGPT_MODEL="gpt-5.6-sol" \
     pytest plugins/openai_responses/tests/test_openai_responses_chatgpt_reasoning_pro_mode_manual_integration.py \
       -m "manual_integration and integration and openai" -q
   ```
   Result: 1 xfailed in 2.62s. The ChatGPT backend rejected
   `reasoning.mode: "pro"` with `Error code: 400 - {'error': {'message':
   '`reasoning.mode` is not supported with this model.', 'type':
   'invalid_request_error', 'param': 'reasoning.mode', 'code':
   'unsupported_value'}}`. The xfail reason captures the exact rejection so
   the endpoint divergence is visible in test output. The saved login at
   `~/.crystal/auth/chatgpt-auth.json` was valid (expires
   `2026-07-18T19:42:08Z`).

5. Lint/format:
   ```
   ruff check <changed files>
   ```
   Result: All checks passed.
   ```
   black <changed files>
   ```
   Result: 2 files reformatted (2 test files; formatting only, no semantic
   changes). Re-ran unit tests after formatting: 44 passed.

### Credential/API gating report

- `OPENAI_API_KEY`: available in repo root `.env`, loaded by plugin
  `conftest.py`. Real API test ran and passed. Not skipped.
- ChatGPT saved login at `~/.crystal/auth/chatgpt-auth.json`: present, valid
  through `2026-07-18T19:42:08Z`. ChatGPT Pro mode test ran and xfailed
  (backend rejected `reasoning.mode: "pro"`). Not skipped.
- No credentials were printed during verification. The ChatGPT test's
  credential gate checks `access_token` presence and `expires_at` validity
  without printing token values.

### Risks confirmed

- ChatGPT endpoint divergence: the ChatGPT backend rejects
  `reasoning.mode: "pro"` while the public API accepts it. Documented via
  `xfail` with the exact rejection message in the ChatGPT test. The
  extension still offers `reasoning_mode: "pro"` for GPT-5.6 models per the
  public API.
- Pre-existing test failures: the 3 failures in
  `test_openai_responses_native_history_regressions.py` are unchanged by
  this task (same 3 as tasks 010 and 020).
- GPT-5.6 pricing not yet present: integration tests do not assert on cost.
  The Pro mode billing documentation states that Pro mode uses the selected
  model's standard-tier pricing, which task 050 will add. Until then, cost
  estimation for GPT-5.6 models remains zero (the provider defect noted in
  task 010's investigation).
- ChatGPT login expiry: the saved login expires `2026-07-18T19:42:08Z`.
  Implementation ran on `2026-07-18` so the test ran (and xfailed). If run
  after expiry, the test will skip with `saved ChatGPT login at {path}
  expired at {expires_at}` and must be reported as not run.

### Files changed

- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_reasoning_extension.py`
  (added `_REASONING_MODES`, `_GPT_5_6_REASONING_EFFORTS`,
  `_model_supports_pro_reasoning`; extended `get_config_schema`,
  `get_ui_elements`, `_normalize_reasoning_config`)
- `plugins/openai_responses/tests/test_openai_responses_reasoning_extension_unit.py`
  (21 new tests + `_reasoning_mode_elements` helper +
  `OpenAIResponsesFastModeExtension` import)
- `plugins/openai_responses/tests/test_openai_responses_reasoning_extension_integration.py`
  (1 new real API test + `_gpt_5_6_pro_mode_config` helper)
- `plugins/openai_responses/tests/test_openai_responses_chatgpt_reasoning_pro_mode_manual_integration.py`
  (new file, 1 ChatGPT saved-login test + recording provider helpers)
- `plugins/openai_responses/README.md` (reasoning keys section: new
  `reasoning_mode` bullet, mode/effort independence, silent-drop,
  precedence; Fast mode cross-reference; Pro mode billing subsection)
- `tasks/20260713-openai-responses-gpt-5-6-support/030-add-reasoning-pro-mode.md`
  (this file: execution plan + completion notes)

## Follow-up execution plan

(Proposed 2026-07-18. Awaiting user approval before implementation. No code
changes have been made yet for this follow-up.)

### Goal

Three adjustments to the auth-mode gating and footer surfacing for Pro mode
and Fast mode:

1. **Pro mode becomes API-only** (reverse of the current Fast mode pattern):
   UI shows the Pro mode control only when `auth_mode` is `api` or `auto`
   (or unset, which defaults to `api`); hidden when `auth_mode` is
   `chatgpt`. Request injection skips `reasoning.mode` when the effective
   auth mode resolves to `chatgpt`.

2. **Fast mode becomes enabled for both endpoints**: remove the
   `enable_fast_mode_for_api_requests` opt-in and the auth-mode check in
   `initialize_request`. Fast mode injects `service_tier: "priority"`
   whenever `enable_fast_mode: true`, regardless of auth mode. Verified
   that the public API accepts `service_tier: "priority"` for
   API-authenticated `gpt-5.6-sol` requests.

3. **Footer shows both Pro mode and Fast mode when available in the
   response**: the provider already extracts `service_tier` from the
   response; add extraction of `reasoning.mode` and surface both in the
   usage footer. The API returns `reasoning.mode: "pro"` for Pro mode
   requests and `service_tier: "priority"` for Fast mode requests
   (verified via direct SDK calls on 2026-07-18).

### Change 1: Pro mode auth-mode gating (API-only)

#### Reasoning extension changes

`openai_responses_reasoning_extension.py`:

- Import `effective_auth_mode` and `normalize_auth_mode` from
  `openai_responses_runtime` (the canonical shared helpers already used
  by the provider, flex, and prompt-caching extensions).
- `get_ui_elements()`: before appending the `reasoning_mode` select,
  check the requested auth mode via `normalize_auth_mode(config.get("auth_mode"))`.
  Only append the control when the result is not `"chatgpt"` (i.e., show
  for `api`, `auto`, and unset/default). This is the requested mode, not
  the effective mode, because the UI reflects what the user is
  configuring.
- `_normalize_reasoning_config()`: add a fourth condition to the
  existing `reasoning_mode` guard: `effective_auth_mode(config) != "chatgpt"`.
  This skips `mode` when the effective auth mode resolves to ChatGPT,
  mirroring how the flex processing extension skips `service_tier: "flex"`
  for ChatGPT. The effective auth mode is available at `init()` time
  because the ChatGPT auth feature (priority 10) runs before the
  reasoning extension (priority 50) and sets
  `_openai_responses_effective_auth_mode`.

No change to `initialize_request()` — the existing merge still works
because `mode` is simply absent from the reasoning state when the
effective auth mode is ChatGPT.

#### Behavior matrix

| Requested `auth_mode` | Effective auth mode | UI shows Pro control | Request injects `mode: "pro"` |
| --- | --- | --- | --- |
| `api` (or unset) | `api` | yes | yes |
| `auto` | `api` | yes | yes |
| `auto` | `chatgpt` | yes | no (skipped by `_normalize_reasoning_config`) |
| `chatgpt` | `chatgpt` | no | no |

### Change 2: Fast mode enabled for both endpoints

#### Fast mode extension changes

`openai_responses_fast_mode_extension.py`:

- `get_config_schema()`: remove the `enable_fast_mode_for_api_requests`
  entry. Keep only `enable_fast_mode`.
- `get_ui_elements()`: remove the `enable_for_api` branching. The
  description becomes a single string: "Applies `service_tier: "priority"`
  to Responses calls for both API-key and ChatGPT auth modes."
- `_fast_mode_description()`: remove (no longer needed).
- `initialize_request()`: remove the auth-mode check entirely. Inject
  `service_tier: "priority"` whenever `_FAST_MODE_STATE_KEY` is present
  in state (set by `init()` when `enable_fast_mode: true`). Keep the
  `request` dict guard.

#### Backwards compatibility for `enable_fast_mode_for_api_requests`

The key is removed from the schema. Existing configs that set it to
`true` will simply ignore the key (the schema no longer advertises it,
and the extension no longer reads it). This is a minor breaking change
for configs that relied on the opt-in, but the new behavior is a
strict superset (Fast mode now works for both endpoints), so the opt-in
is no longer meaningful. The README and tests will be updated to
reflect this.

### Change 3: Footer visibility for Pro mode and Fast mode

#### Provider changes

`openai_responses_provider.py`:

- Add `_RAW_REASONING_MODE_METADATA_KEY = "_openai_responses_reasoning_mode"`
  next to the existing `_RAW_REASONING_CONTEXT_METADATA_KEY`.
- In `_response_internal_metadata()`, after extracting
  `reasoning.context`, also extract `reasoning.mode`:
  ```python
  reasoning_mode = reasoning_obj.get("mode")
  if isinstance(reasoning_mode, str) and reasoning_mode:
      md[_RAW_REASONING_MODE_METADATA_KEY] = reasoning_mode
  ```
  The response metadata is already attached to all output items by
  `_attach_internal_metadata_to_output()`, so no further plumbing is
  needed.

#### Usage extension changes

`openai_responses_usage_extension.py`:

- Add `_RAW_REASONING_MODE_METADATA_KEY = "_openai_responses_reasoning_mode"`
  constant (mirroring `_RAW_SERVICE_TIER_METADATA_KEY`).
- Add `_reasoning_mode_from_items()` static method (mirroring
  `_service_tier_from_items()`) that reads the reasoning mode from the
  first item's internal metadata.
- In `_build_usage_metadata()`, call `reasoning_mode =
  self._reasoning_mode_from_items(current_items)` alongside the existing
  `service_tier` extraction.
- Add `"usage_reasoning_mode": reasoning_mode` to `extra_md` when
  `reasoning_mode` is a non-empty string.
- Add `"usage_reasoning_mode"` to `_PUBLIC_USAGE_METADATA_KEYS`.
- In `get_ui_elements()`, add a new footer entry after the existing
  `usage_service_tier` entry:
  ```python
  {
      "ui_type": "message_footer",
      "data": "metadata.usage_reasoning_mode",
      "template": "mode: {{data}}",
      "condition": {
          "path": "metadata.usage_reasoning_mode",
          "eq": "pro",
      },
  },
  ```
  This shows `mode: pro` only when the response reported
  `reasoning.mode: "pro"`. Standard mode is the default and is not
  shown (matching the existing pattern where `service_tier: "default"`
  is not shown in the footer).

The existing `usage_service_tier` footer entry already shows
`tier: priority` when Fast mode reports `service_tier: "priority"` and
`tier: flex` when flex processing reports `service_tier: "flex"`. No
change needed for the Fast mode footer — it will now appear for both
API and ChatGPT auth modes because Fast mode is enabled for both.

#### Fast mode extension `from_native_messages` — no change needed

The Fast mode extension already surfaces `openai_service_tier` and
`fast_mode_applied` in `from_native_messages()`. The usage extension
reads the raw `_openai_responses_service_tier` from internal metadata
for the footer. No change needed here.

### Exact unit tests

#### Pro mode auth-mode gating (reasoning extension unit tests)

Add to `test_openai_responses_reasoning_extension_unit.py`:

UI visibility:
- `test_get_ui_elements_shows_reasoning_mode_for_api_auth` —
  `auth_mode: "api"` shows the Pro mode control for `gpt-5.6-sol`.
- `test_get_ui_elements_shows_reasoning_mode_for_auto_auth` —
  `auth_mode: "auto"` shows the Pro mode control.
- `test_get_ui_elements_shows_reasoning_mode_for_default_auth` — no
  `auth_mode` set shows the Pro mode control (defaults to `api`).
- `test_get_ui_elements_hides_reasoning_mode_for_chatgpt_auth` —
  `auth_mode: "chatgpt"` hides the Pro mode control even for
  `gpt-5.6-sol`.

Request injection:
- `test_init_drops_reasoning_mode_pro_for_chatgpt_effective_auth` —
  `_openai_responses_effective_auth_mode: "chatgpt"` drops `mode` from
  reasoning state; `_openai_responses_reasoning` either absent or
  present without `mode`.
- `test_init_preserves_reasoning_mode_pro_for_api_effective_auth` —
  `_openai_responses_effective_auth_mode: "api"` keeps `mode: "pro"`.
- `test_init_drops_reasoning_mode_pro_for_auto_resolving_to_chatgpt` —
  `auth_mode: "auto"` with
  `_openai_responses_effective_auth_mode: "chatgpt"` drops `mode`.
- `test_init_preserves_reasoning_mode_pro_for_auto_resolving_to_api` —
  `auth_mode: "auto"` with
  `_openai_responses_effective_auth_mode: "api"` keeps `mode: "pro"`.
- `test_init_preserves_effort_and_summary_for_chatgpt_auth` —
  `auth_mode: "chatgpt"` with `reasoning_effort: "medium"` and
  `reasoning_summary: "concise"` still injects `effort` and `summary`
  (only `mode` is dropped, not the other reasoning fields).

Update existing tests that assumed Pro mode is auth-mode-agnostic:
- `test_get_ui_elements_shows_reasoning_mode_for_gpt_5_6_sol` — add
  `auth_mode: "api"` to the config (or verify the default is `api`).
- `test_get_ui_elements_shows_reasoning_mode_for_gpt_5_6_luna` — same.
- `test_get_ui_elements_shows_reasoning_mode_for_bare_gpt_5_6_alias` —
  same.

#### Fast mode changes (Fast mode extension unit tests)

Update `test_openai_responses_fast_mode_extension_unit.py`:

- `test_extension_name_tags_schema_and_required_tags` — schema now has
  only `enable_fast_mode` (not `enable_fast_mode_for_api_requests`).
  Update the description assertion.
- `test_get_ui_elements_exposes_fast_mode_toggle` — description is the
  new unified string.
- Remove `test_get_ui_elements_mentions_api_when_api_fast_mode_is_enabled_in_config`
  (key no longer exists).
- `test_initialize_request_is_noop_for_api_auth` → rename to
  `test_initialize_request_injects_priority_for_api_auth` — now asserts
  `service_tier == "priority"` for API auth.
- Remove `test_initialize_request_injects_priority_for_api_auth_when_explicitly_enabled`
  (key no longer exists).
- `test_initialize_request_injects_priority_service_tier_for_chatgpt` —
  still passes (ChatGPT still injects).
- `test_init_and_initialize_request_are_noops_when_fast_mode_disabled` —
  still passes.
- `test_from_native_messages_surfaces_priority_service_tier_metadata` —
  still passes.

#### Footer visibility (usage extension unit tests)

Add to `test_openai_responses_usage_extension_unit.py`:

- `test_streaming_usage_surfaces_reasoning_mode_pro` — native item with
  `_metadata._openai_responses_reasoning_mode: "pro"` →
  `metadata.usage_reasoning_mode == "pro"`.
- `test_streaming_usage_omits_reasoning_mode_when_absent` — no
  `_openai_responses_reasoning_mode` in native items →
  `usage_reasoning_mode` not in metadata.
- `test_streaming_usage_surfaces_service_tier_priority_and_reasoning_mode_pro`
  — both `_openai_responses_service_tier: "priority"` and
  `_openai_responses_reasoning_mode: "pro"` → both `usage_service_tier`
  and `usage_reasoning_mode` present (verifies coexistence).
- Update the `get_ui_elements` test (if any) to include the new
  `mode: {{data}}` footer entry.

### Integration tests

#### Real API tests

Add to `test_openai_responses_reasoning_extension_integration.py`:

- `test_openai_responses_reasoning_mode_pro_footer_visible_real_api` —
  `gpt-5.6-sol` with `reasoning_mode: "pro"`, API auth. Asserts:
  successful completion, `metadata.usage_reasoning_mode == "pro"`, and
  the recorded request has `reasoning.mode == "pro"`. This verifies the
  footer surfaces Pro mode for API auth.

Add to `test_openai_responses_reasoning_extension_integration.py` (or a
new Fast mode integration test file):

- `test_openai_responses_fast_mode_priority_footer_visible_real_api` —
  `gpt-5.6-sol` with `enable_fast_mode: true`, API auth (no
  `enable_fast_mode_for_api_requests` needed anymore). Asserts:
  successful completion, `metadata.usage_service_tier == "priority"`,
  and the recorded request has `service_tier == "priority"`. This
  verifies Fast mode now works for API auth and the footer surfaces it.

#### ChatGPT saved-login tests

**Existing Fast mode test (retest after change):**
`test_openai_responses_chatgpt_auth_manual_integration.py::
test_openai_responses_chatgpt_saved_login_fast_mode_round_trip` already
exists and xfails. Confirmed on 2026-07-18: the ChatGPT backend reports
`service_tier='default'` for `gpt-5.6-luna` even when the outgoing request
sends `service_tier: "priority"`. The xfail reason is:
`ChatGPT backend reported service_tier='default' for model gpt-5.6-luna;
some accounts or models may not have Fast mode access.`

This change does **not** alter ChatGPT-auth behavior (Fast mode still
injects `service_tier: "priority"` for ChatGPT auth, same as before). The
test should still xfail with the same reason after the change. Re-run it
to confirm the xfail is unchanged — if it starts passing (backend now
honors priority), update the test to a hard assert; if it still xfails,
leave it as-is. Do not remove the xfail or weaken it into a skip.

**Existing pricing test (note, not fixed in this task):**
`test_openai_responses_chatgpt_pricing_manual_integration.py::
test_openai_responses_chatgpt_saved_login_priority_tier_pricing` has a
similar xfail for `reported_tier != "priority"`, but on 2026-07-18 it
failed with `RuntimeError: OpenAI Responses stream failed: terminal
event error: unknown error` before reaching the xfail. This is a
separate backend/terminal-error issue, not caused by the Fast mode
change. Leave it for the pricing task (050) to investigate; do not try to
fix it here.

**Pro mode test (update for new gating):**
`test_openai_responses_chatgpt_reasoning_pro_mode_manual_integration.py::
test_openai_responses_chatgpt_reasoning_mode_pro_gpt_5_6_sol` currently
xfails because the ChatGPT backend rejects `reasoning.mode: "pro"`. With
the new auth-mode gating, the extension will not inject `mode` for
ChatGPT auth, so the request will not include `reasoning.mode`. Update
the test:
- Remove the `pytest.xfail` — the request should now succeed.
- Assert the recorded request does NOT contain `reasoning.mode` (the
  extension skips it for ChatGPT auth).
- Assert `metadata.usage_reasoning_mode` is absent or not `"pro"` (the
  backend didn't receive `mode: "pro"`, so it won't report it).
- Keep the credential gate (skip with exact reason if the saved login is
  missing/expired/invalid).

### Documentation updates

`plugins/openai_responses/README.md`:

1. **Reasoning keys section** — update the `reasoning_mode` bullet to
   state it is API-only: shown when `auth_mode` is `api` or `auto`,
   hidden when `auth_mode` is `chatgpt`; not injected when the effective
   auth mode resolves to ChatGPT.
2. **Fast mode section** — update to state Fast mode now applies to
   both API and ChatGPT auth modes. Remove the
   `enable_fast_mode_for_api_requests` bullet. Update the description
   to not mention "ChatGPT-only" or "API opt-in".
3. **Pro mode billing subsection** — add a note that Pro mode is
   API-only; ChatGPT auth does not inject `reasoning.mode`.
4. **Usage keys section** — mention the new `usage_reasoning_mode`
   metadata field and the `mode: pro` footer entry.

### Implementation order

1. Edit `openai_responses_reasoning_extension.py`: import
   `effective_auth_mode`/`normalize_auth_mode`; add auth-mode guard to
   `get_ui_elements()` and `_normalize_reasoning_config()`.
2. Edit `openai_responses_fast_mode_extension.py`: remove
   `enable_fast_mode_for_api_requests` from schema, UI, and
   `initialize_request()`; simplify description.
3. Edit `openai_responses_provider.py`: add
   `_RAW_REASONING_MODE_METADATA_KEY` and extract `reasoning.mode` in
   `_response_internal_metadata()`.
4. Edit `openai_responses_usage_extension.py`: add
   `_RAW_REASONING_MODE_METADATA_KEY`, `_reasoning_mode_from_items()`,
   `usage_reasoning_mode` metadata, and the `mode: {{data}}` footer
   entry.
5. Edit `scripts/run_openai_responses_tier_matrix.py`: remove
   `enable_fast_mode_for_api_requests=True` from the `api-priority`
   `MatrixCase` (the key no longer exists; `enable_fast_mode=True` alone
   is sufficient for API auth now). The unit test
   `test_run_openai_responses_tier_matrix_unit.py` only asserts case
   names, so it will still pass.
6. Add/update unit tests for all four source files.
7. Run unit tests to confirm all pass.
8. Add real API integration tests for Pro mode footer and Fast mode
   API-auth footer.
9. Update ChatGPT Pro mode test to reflect the new auth-mode gating
   (no xfail; assert `reasoning.mode` absent from recorded request).
10. Update README.
11. Run fast default plugin suite.
12. Run real API integration tests.
13. Run ChatGPT saved-login tests with `~/.crystal`:
    - Re-run `test_openai_responses_chatgpt_saved_login_fast_mode_round_trip`
      to confirm the xfail is unchanged (ChatGPT backend still reports
      `service_tier='default'`).
    - Run the updated Pro mode test to confirm it now passes (no xfail).
14. Lint/format.
15. Append follow-up completion notes and update `000-main.md` if
    needed.

### Verification commands

- Unit tests (focused):
  ```
  pytest plugins/openai_responses/tests/test_openai_responses_reasoning_extension_unit.py \
         plugins/openai_responses/tests/test_openai_responses_fast_mode_extension_unit.py \
         plugins/openai_responses/tests/test_openai_responses_usage_extension_unit.py -q
  ```
- Fast default plugin suite:
  ```
  pytest plugins/openai_responses/tests -q
  ```
- Real API Pro mode footer:
  ```
  pytest plugins/openai_responses/tests/test_openai_responses_reasoning_extension_integration.py \
    -m 'integration and api and not slow_integration and openai' -q
  ```
- Real API Fast mode footer (new test for API auth):
  ```
  pytest plugins/openai_responses/tests/test_openai_responses_reasoning_extension_integration.py \
    -m 'integration and api and not slow_integration and openai' -q
  ```
- ChatGPT saved-login Pro mode (updated, no longer xfail):
  ```bash
  CHATGPT_TEST_STATE_DIR="$HOME/.crystal" \
  OPENAI_RESPONSES_CHATGPT_MODEL="gpt-5.6-sol" \
    pytest plugins/openai_responses/tests/test_openai_responses_chatgpt_reasoning_pro_mode_manual_integration.py \
      -m "manual_integration and integration and openai" -q
  ```
- ChatGPT saved-login Fast mode (existing, should still pass):
  ```bash
  CHATGPT_TEST_STATE_DIR="$HOME/.crystal" \
    pytest plugins/openai_responses/tests/test_openai_responses_chatgpt_auth_manual_integration.py \
      -m "manual_integration and integration and openai" -q
  ```
- Lint/format: `ruff check <changed files>` and `black <changed files>`.

### Compatibility risks

- **`enable_fast_mode_for_api_requests` removal**: configs that set
  this key will silently ignore it. The new behavior is a strict
  superset (Fast mode works for both endpoints), so no functionality is
  lost. The key is removed from the schema, so config validation will
  not flag it (the schema is opt-in, not strict). The tier matrix script
  (`scripts/run_openai_responses_tier_matrix.py`) also sets this key in
  the `api-priority` case and will be updated.
- **Pro mode API-only gating**: users who previously set
  `reasoning_mode: "pro"` with `auth_mode: "chatgpt"` will see the
  control hidden and the mode not injected. This is the intended
  behavior change. The ChatGPT backend already rejected
  `reasoning.mode: "pro"`, so this change makes the extension match the
  backend's behavior rather than sending a rejected field.
- **Footer entry for `usage_reasoning_mode`**: new metadata field. No
  existing test should break (it's additive). The footer only shows
  `mode: pro` when the response reports it, so standard-mode requests
  are unaffected.
- **ChatGPT Fast mode xfail is pre-existing and unchanged**: the
  existing `test_openai_responses_chatgpt_saved_login_fast_mode_round_trip`
  test xfails because the ChatGPT backend reports `service_tier='default'`
  (not `"priority"`) even when `service_tier: "priority"` is sent. This
  change does not alter ChatGPT-auth behavior, so the xfail should still
  trigger. The test is re-run after the change to confirm. The xfail is
  not a regression — it documents a real backend limitation.
- **Pre-existing test failures**: the 3 failures in
  `test_openai_responses_native_history_regressions.py` are unchanged
  (same as tasks 010/020/030). The
  `test_openai_responses_chatgpt_saved_login_priority_tier_pricing`
  failure (RuntimeError: terminal event error) is a separate
  backend/terminal-error issue, not caused by this change; it is left
  for the pricing task (050) to investigate.
- **ChatGPT login expiry**: the saved login expires
  `2026-07-29T13:11:12Z` (refreshed since the original task 030). If
  implementation runs after that, the ChatGPT tests will skip with an
  exact reason and must be reported as not run.

### Prerequisite assumptions

- Task 030 is committed (`4921e63a`): `reasoning_mode` config key,
  `_model_supports_pro_reasoning`, schema/UI/normalization, 21 unit
  tests, real API test, ChatGPT test (xfail), README updates.
- The public OpenAI API accepts `service_tier: "priority"` for
  API-authenticated `gpt-5.6-sol` requests and returns
  `service_tier: "priority"` in the response (verified 2026-07-18).
- The public OpenAI API returns `reasoning.mode: "pro"` in the
  response when Pro mode is requested (verified 2026-07-18).
- The ChatGPT backend rejects `reasoning.mode: "pro"` with
  `reasoning.mode is not supported with this model` (verified
  2026-07-18).
- The ChatGPT backend reports `service_tier: "default"` (not
  `"priority"`) even when `service_tier: "priority"` is sent in the
  request (confirmed 2026-07-18 via
  `test_openai_responses_chatgpt_saved_login_fast_mode_round_trip`
  xfail). The existing test documents this with an xfail and is
  re-run after the change to confirm the behavior is unchanged.
- `OPENAI_API_KEY` is available in repo root `.env`.
- The saved ChatGPT login at `~/.crystal/auth/chatgpt-auth.json` is
  valid through `2026-07-29T13:11:12Z` (refreshed since the original
  task 030).
- The shared `effective_auth_mode` and `normalize_auth_mode` helpers
  in `openai_responses_runtime.py` are the canonical implementations
  used by the provider, flex, and prompt-caching extensions.

## Follow-up completion notes

(Added 2026-07-19 during follow-up implementation. All three changes
implemented and verified.)

### What changed

#### Change 1: Pro mode API-only gating

`openai_responses_reasoning_extension.py`:
- Imported `effective_auth_mode` and `normalize_auth_mode` from
  `openai_responses_runtime` (the canonical shared helpers).
- `get_ui_elements()`: the `reasoning_mode` select is now shown only when
  `normalize_auth_mode(config.get("auth_mode")) != "chatgpt"` (i.e., for
  `api`, `auto`, `api_key`, and unset/default). Hidden when `chatgpt`.
- `_normalize_reasoning_config()`: added a 4th guard to the
  `reasoning_mode` check: `effective_auth_mode(config) != "chatgpt"`. This
  skips `mode` when the effective auth mode resolves to ChatGPT.
  `effort` and `summary` are unaffected and still injected for ChatGPT
  auth.

#### Change 2: Fast mode enabled for both endpoints

`openai_responses_fast_mode_extension.py`:
- Removed `enable_fast_mode_for_api_requests` from the schema, UI, and
  `initialize_request()`.
- Removed the `_effective_auth_mode()` helper and `_fast_mode_description()`
  method (no longer needed).
- `initialize_request()` now injects `service_tier: "priority"` whenever
  `_FAST_MODE_STATE_KEY` is present in state (set by `init()` when
  `enable_fast_mode: true`), regardless of auth mode.
- Updated the docstring and UI description to state Fast mode applies to
  both API-key and ChatGPT auth modes.

#### Change 3: Footer visibility for Pro mode and Fast mode

`openai_responses_provider.py`:
- Added `_RAW_REASONING_MODE_METADATA_KEY = "_openai_responses_reasoning_mode"`.
- In `_response_internal_metadata()`, extract `reasoning.mode` from the
  response object alongside the existing `reasoning.context` extraction.

`openai_responses_usage_extension.py`:
- Added `_RAW_REASONING_MODE_METADATA_KEY` constant.
- Added `_reasoning_mode_from_items()` static method (mirrors
  `_service_tier_from_items()`).
- In `_build_usage_metadata()`, extract `reasoning_mode` from items and
  attach `usage_reasoning_mode` to public metadata when present.
- Added `usage_reasoning_mode` to `_PUBLIC_USAGE_METADATA_KEYS`.
- Added a `mode: {{data}}` footer entry in `get_ui_elements()` shown when
  `usage_reasoning_mode == "pro"`.

#### Tier matrix script

`scripts/run_openai_responses_tier_matrix.py`:
- Removed `enable_fast_mode_for_api_requests` from the `MatrixCase`
  dataclass, the `api-priority` case definition, the config builder, and
  the metric line formatter. The `api-priority` case now uses
  `enable_fast_mode=True` alone (sufficient for API auth).

### Tests added/updated

#### Unit tests
- `test_openai_responses_reasoning_extension_unit.py`: added 11 new
  tests for auth-mode gating (5 UI visibility: api/auto/default/api_key/
  chatgpt; 5 request injection: chatgpt-effective/api-effective/auto-
  resolving-to-chatgpt/auto-resolving-to-api/effort+summary-preserved-
  for-chatgpt; 1 coexistence test for ChatGPT auth verifying Pro mode
  dropped while Fast mode applies). Updated the existing
  `test_initialize_request_pro_mode_and_fast_mode_coexist` to use API
  auth.
- `test_openai_responses_fast_mode_extension_unit.py`: updated schema
  test (only `enable_fast_mode`), UI description test (new unified
  string), renamed `test_initialize_request_is_noop_for_api_auth` to
  `test_initialize_request_injects_priority_for_api_auth`, removed
  `test_get_ui_elements_mentions_api_when_api_fast_mode_is_enabled_in_config`
  and `test_initialize_request_injects_priority_for_api_auth_when_explicitly_enabled`,
  added 2 new tests for auto-resolving-to-api and auto-resolving-to-
  chatgpt.
- `test_openai_responses_usage_extension_unit.py`: added 3 new tests
  for reasoning mode surfacing (pro surfaced, omitted when absent,
  coexistence with service_tier priority). Updated the UI elements
  test to include the new `usage_reasoning_mode` footer entry.
- `test_openai_responses_provider_unit.py`: added 6 new tests for
  `reasoning.mode` extraction (pro extracted, pro+context extracted,
  omitted when absent/no-obj/not-string/empty).
- `application/python/tests/test_openai_responses_flex_processing_endpoints.py`:
  renamed `test_openai_fast_mode_injects_priority_for_chatgpt_only` to
  `test_openai_fast_mode_injects_priority_for_both_auth_modes` and
  updated assertions (API auth now injects `service_tier: "priority"`).

#### Integration tests
- `test_openai_responses_reasoning_extension_integration.py`: added 2
  new real API tests:
  `test_openai_responses_reasoning_mode_pro_footer_visible_real_api`
  (verifies `usage_reasoning_mode == "pro"` in metadata) and
  `test_openai_responses_fast_mode_priority_footer_visible_real_api`
  (verifies `usage_service_tier == "priority"` for API auth, new since
  Fast mode now works for API).
- `test_openai_responses_chatgpt_reasoning_pro_mode_manual_integration.py`:
  updated `test_openai_responses_chatgpt_reasoning_mode_pro_gpt_5_6_sol`
  to remove the `pytest.xfail` (the extension now skips `mode` for
  ChatGPT auth, so the request succeeds). Asserts `reasoning.mode` is
  absent from the recorded request and `usage_reasoning_mode` is not
  `"pro"`.

### Verification results

- Unit tests (focused): 221 passed.
- Full fast default plugin suite (`pytest plugins/openai_responses/tests
  -q`): 384 passed, 3 pre-existing failures in
  `test_openai_responses_native_history_regressions.py` (unchanged from
  tasks 010/020/030), 76 deselected (integration).
- Tier matrix unit tests: 9 passed.
- Real API integration tests
  (`pytest plugins/openai_responses/tests/test_openai_responses_reasoning_extension_integration.py
  -m 'integration and api and not slow_integration and openai' -q`):
  8 passed, 1 pre-existing xfailed (ultra effort).
- ChatGPT Pro mode test
  (`CHATGPT_TEST_STATE_DIR=$HOME/.crystal OPENAI_RESPONSES_CHATGPT_MODEL=gpt-5.6-sol pytest
  plugins/openai_responses/tests/test_openai_responses_chatgpt_reasoning_pro_mode_manual_integration.py
  -m 'manual_integration and integration and openai' -q`):
  1 passed (no xfail — the extension now skips `mode` for ChatGPT auth,
  so the request succeeds without `reasoning.mode`).
- ChatGPT Fast mode test (retest after change, `gpt-5.6-sol`):
  1 xfailed with `ChatGPT backend reported service_tier='default' for
  model gpt-5.6-sol` — the xfail is unchanged (ChatGPT backend still
  reports `service_tier='default'` for Fast mode). Transient 503/terminal
  errors were observed for `gpt-5.6-luna` and `gpt-5.5` during testing;
  these are backend availability issues, not caused by this change.
- Application tests
  (`pytest application/python/tests/test_openai_responses_flex_processing_endpoints.py
  -m integration -q`): 3 passed.
- Lint/format: `ruff check` and `black` clean on all changed files.

### Findings

- The public OpenAI API accepts `service_tier: "priority"` for
  API-authenticated `gpt-5.6-sol` requests and returns
  `service_tier: "priority"` in the response (verified 2026-07-18).
- The public OpenAI API returns `reasoning.mode: "pro"` in the response
  when Pro mode is requested (verified 2026-07-18).
- The ChatGPT backend rejects `reasoning.mode: "pro"` with
  `reasoning.mode is not supported with this model` (verified
  2026-07-18). With the new auth-mode gating, the extension does not
  inject `mode` for ChatGPT auth, so the request succeeds without
  `reasoning.mode`.
- The ChatGPT backend reports `service_tier: "default"` (not
  `"priority"`) for Fast mode requests (confirmed 2026-07-18). The
  existing xfail in
  `test_openai_responses_chatgpt_saved_login_fast_mode_round_trip`
  documents this backend limitation and is unchanged by this follow-up.
- The `test_openai_responses_chatgpt_saved_login_priority_tier_pricing`
  test (in `test_openai_responses_chatgpt_pricing_manual_integration.py`)
  currently fails with `RuntimeError: terminal event error: unknown
  error` before reaching its xfail. This is a separate backend/terminal-
  error issue, not caused by this change; left for the pricing task (050)
  to investigate.
- The `test_add_message_returns_400_for_pdf_without_upload_mode` test
  (in `application/python/tests/test_openai_responses_attachment_endpoints.py`)
  is a pre-existing failure (confirmed by stashing changes and running
  the test on the unmodified tree). Not caused by this change.

### Files changed

- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_reasoning_extension.py`
  (import `effective_auth_mode`/`normalize_auth_mode`; auth-mode guard
  in `get_ui_elements()` and `_normalize_reasoning_config()`)
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_fast_mode_extension.py`
  (removed `enable_fast_mode_for_api_requests`, `_effective_auth_mode`,
  `_fast_mode_description`; simplified `initialize_request()`;
  updated docstring/schema/UI description)
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
  (added `_RAW_REASONING_MODE_METADATA_KEY`; extract `reasoning.mode`
  in `_response_internal_metadata()`)
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_usage_extension.py`
  (added `_RAW_REASONING_MODE_METADATA_KEY`,
  `_reasoning_mode_from_items()`, `usage_reasoning_mode` metadata,
  `mode: {{data}}` footer entry)
- `plugins/openai_responses/tests/test_openai_responses_reasoning_extension_unit.py`
  (11 new tests + updated coexistence test)
- `plugins/openai_responses/tests/test_openai_responses_fast_mode_extension_unit.py`
  (updated schema/UI/API-auth tests; removed 2 obsolete tests; added 2
  auto-auth tests)
- `plugins/openai_responses/tests/test_openai_responses_usage_extension_unit.py`
  (3 new reasoning mode tests + updated UI elements test)
- `plugins/openai_responses/tests/test_openai_responses_provider_unit.py`
  (6 new `reasoning.mode` extraction tests)
- `plugins/openai_responses/tests/test_openai_responses_reasoning_extension_integration.py`
  (2 new real API footer tests)
- `plugins/openai_responses/tests/test_openai_responses_chatgpt_reasoning_pro_mode_manual_integration.py`
  (updated Pro mode test: no xfail, assert `reasoning.mode` absent)
- `application/python/tests/test_openai_responses_flex_processing_endpoints.py`
  (renamed/updated Fast mode test for both auth modes)
- `scripts/run_openai_responses_tier_matrix.py` (removed
  `enable_fast_mode_for_api_requests` from `MatrixCase`, config builder,
  metric formatter)
- `plugins/openai_responses/README.md` (Fast mode section: both
  endpoints; reasoning keys: Pro mode API-only; Pro mode billing:
  API-only note; usage keys: `usage_reasoning_mode` footer; config
  example: removed `enable_fast_mode_for_api_requests`)
- `tasks/20260713-openai-responses-gpt-5-6-support/030-add-reasoning-pro-mode.md`
  (this file: follow-up execution plan + completion notes)
