# Configurable ChatGPT originator header

Add a small, config-driven identity header for OpenAI Responses requests that use ChatGPT authentication, with the Crystal Lattice identity owned by the application default config rather than hard-coded in the provider plugin.

## Requirements checklist

- [x] The OpenAI Responses ChatGPT-auth configuration accepts an optional `chatgpt_originator` string.
- [x] A non-blank configured value is sent as the `Originator` header on ChatGPT-authenticated Responses requests, including normal streaming requests and provider paths that reuse the shared ChatGPT client/header construction.
- [x] API-key mode does not send the ChatGPT `Originator` header.
- [x] Missing or blank `chatgpt_originator` preserves compatibility by omitting the header.
- [x] The terminal application's maintained default OpenAI provider config declares `chatgpt_originator` as `crystal_lattice_control`.
- [x] The public OpenAI Responses configuration reference describes the setting and omission behavior.

## Scope

In scope:

- OpenAI Responses ChatGPT-auth config schema and shared header construction.
- The maintained terminal default config.
- Focused automated coverage for configuration propagation and outbound headers.
- The existing OpenAI Responses package configuration reference.

Out of scope:

- `User-Agent`, `OpenAI-Beta`, session/request correlation headers, Codex-specific headers, device attestation, or broader error-reporting changes.
- Impersonating the Codex client or using a Codex originator value.

## Requirement questions

None. The approved default-config identity is `crystal_lattice_control`; custom configurations may choose another non-blank value or omit the setting.

## Supporting details

- The shared ChatGPT header builder currently adds only `ChatGPT-Account-Id` and is used by the normal SDK client, async client, requests transport, request state, and native-compaction client paths.
- pi identifies itself honestly with `originator: pi`; live comparison requests established that the ChatGPT Codex Responses endpoint accepts a third-party originator.
- Keeping the provider-level setting optional avoids changing behavior for package users who do not consume the terminal application's default config.
- Header names are case-insensitive; use the conventional `Originator` spelling in generated header maps and assertions.

## Execution plan

Status: Approved

Add `chatgpt_originator` to the ChatGPT-auth feature's provider configuration schema without assigning a product-specific plugin default. Extend the shared ChatGPT default-header builder to trim the configured value and add `Originator` only when the effective auth mode is ChatGPT and the value is non-blank. Because all supported clients and request paths already consume this shared header builder, keep the implementation centralized instead of adding transport-specific header logic.

Declare `"chatgpt_originator": "crystal_lattice_control"` on the maintained `openai` provider in the terminal default config. This makes the shipped application identify itself while leaving standalone plugin consumers unchanged unless they opt in.

Use focused tests at two boundaries:

1. Provider/config tests prove configured, missing, blank, and API-mode behavior and ensure the setting survives ChatGPT-auth feature initialization.
2. A request-path test captures an outbound ChatGPT-authenticated request through the existing production provider transport and verifies both `Originator` and `ChatGPT-Account-Id`, so the requirement is not proven only by testing the helper in isolation.

Keep the change backward-compatible: do not invent fallback identity values, reject missing values, or alter unrelated ChatGPT headers.

### Implementation decisions and open questions

- Decision: The config key is `chatgpt_originator`.
- Decision: The provider plugin has no product-specific fallback; missing, non-string, or whitespace-only values omit the header.
- Decision: The maintained default config owns the value `crystal_lattice_control`.
- Decision: Only effective ChatGPT auth sends the header. API-key mode ignores the setting.
- Open questions: None.

### Documentation

- Add `chatgpt_originator` to the provider-key reference in `plugins/openai_responses/README.md`.
- Explain that it applies only to effective ChatGPT auth and that missing or blank values omit the header.
- No project-wide documentation page or documentation restructuring is needed.

### Task checklist

- [x] Add `chatgpt_originator` to the ChatGPT-auth feature configuration schema.
- [x] Extend shared ChatGPT header construction with the optional `Originator` value.
- [x] Add `chatgpt_originator: crystal_lattice_control` to the terminal default OpenAI provider config.
- [x] Add focused configuration and outbound-request regression tests.
- [x] Update the OpenAI Responses configuration reference.
- [x] Run the focused plugin and default-config tests.
- [x] Run the complete fast OpenAI Responses package test suite if focused verification passes.

### Requirement verification

- Requirements 1–4: Run a focused provider request-path test that sends a ChatGPT-authenticated streaming request to a local HTTP fixture through the production transport. Assert that a configured non-blank value arrives as `Originator`, `ChatGPT-Account-Id` remains present, and corresponding focused cases prove omission for missing/blank configuration and API mode.
- Requirement 5: Load the maintained terminal default config through the existing default-config test path and assert that the effective OpenAI provider config contains `chatgpt_originator == "crystal_lattice_control"`.
- Requirement 6: Inspect the updated package configuration reference and run any maintained documentation/config-reference validation that covers the file.

### Additional implementation verification

- Run `pytest plugins/openai_responses/tests -q`.
- Run the focused default-config test in `application/python/tests/test_default_config_effective_agent_configs.py`.
- Confirm no credentials are added to the repository diff.

## Implementation Notes

- The outbound regression test uses the production provider and requests transport with an injected recording HTTP session. This keeps the test deterministic while exercising the complete header propagation path from provider config to the transport request.

## Completion Notes

- Added the optional `chatgpt_originator` schema field and centralized `Originator` header construction in the shared ChatGPT header helper. Values are trimmed; missing, blank, non-string, and API-mode values are omitted.
- Added `chatgpt_originator: crystal_lattice_control` to the maintained terminal default OpenAI provider config and documented the option in the OpenAI Responses package reference.
- Added focused tests for schema exposure, feature-state propagation, trimming, omission behavior, API-mode isolation, default-config resolution, and the final headers passed by a streaming provider request to the requests transport.
- Requirement evidence:
  - `pytest plugins/openai_responses/tests/test_openai_responses_chatgpt_auth_feature_unit.py plugins/openai_responses/tests/test_requests_transport.py -q` — 18 passed.
  - `pytest application/python/tests/test_default_config_effective_agent_configs.py::test_default_config_openai_context_maintenance_variants_and_ui -m integration -q` — 1 passed.
  - `pytest plugins/openai_responses/tests -q` — 525 passed, 95 deselected.
  - JSON parsing, default-value assertions, Black formatting, and `git diff --check` passed.
- Plan deviation: the outbound-header check injects a recording HTTP session at the production requests-transport boundary instead of opening a local listening socket. It still executes provider initialization, request construction, streaming dispatch, and the final header merge while avoiding a slower network fixture.
- Non-blocking existing finding: unfiltered Ruff reports the pre-existing unused `has_valid_chatgpt` local in `OpenAIResponsesChatGPTAuthFeature.get_ui_elements`; Ruff passes for the touched files when that existing `F841` is excluded. No unrelated cleanup was included.
- No unresolved or deferred task scope remains.
