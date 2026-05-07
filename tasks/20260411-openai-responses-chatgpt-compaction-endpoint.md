# OpenAI Responses ChatGPT Compaction Endpoint

Make native compaction follow the same effective ChatGPT/API endpoint choice as normal OpenAI Responses requests, with a dedicated compaction toggle and clear failure behavior.

## Requirements checklist

- [x] Native compaction uses the effective ChatGPT/API runtime config instead of a separately resolved raw API client.
- [x] Add a dedicated config flag to control whether ChatGPT auth/endpoint can be used for compaction, defaulting to enabled.
- [x] Force API-mode compaction when that flag is disabled, with a clear error if no API credential is available.
- [x] Fail clearly when ChatGPT-backed native compaction is attempted on an endpoint that does not support it.
- [x] Add focused unit coverage for ChatGPT mode, forced API mode, and the disabled-without-API-key failure path.

## Completion Notes

Added a shared runtime helper at `plugins/openai_responses/src/openai_responses_plugins/openai_responses_runtime.py` so provider and compaction client creation use the same auth-mode, base URL, and ChatGPT header resolution.

Updated `plugins/openai_responses/src/openai_responses_plugins/openai_responses_native_compaction_extension.py` to:
- build a fresh client from the feature-initialized runtime config
- honor `use_chatgpt_auth_for_compaction` (default `true`)
- force API-mode compaction when disabled
- raise a clearer error when ChatGPT-backed compaction fails on the ChatGPT endpoint
- remove the misleading action-level `instructions` field and rely on the configured system-message feature path instead
- explicitly opt into request-time provider/feature initialization via `AgentCore.initialize_action_request(...)`
- use `request_context` and `request_runtime` injected into session-action context instead of relying on automatic action initialization
- preserve the same top-level `instructions` and migrated-session stripping behavior as normal requests

Follow-up implementation and verification added after the initial endpoint work:
- verified the real ChatGPT-backed native compaction path using saved manual-login credentials
- added a manual integration test under `plugins/openai_responses/tests/test_openai_responses_chatgpt_native_compaction_manual_integration.py`
- fixed compatibility with ChatGPT backend responses that emit `type: "compaction_summary"` instead of only `type: "compaction"`
- confirmed the explicit action-initialization refactor preserved the live ChatGPT compaction flow

Verified with:
- `python -m pytest plugins/openai_responses/tests/test_openai_responses_native_compaction_extension_unit.py -q`
- `python -m pytest plugins/openai_responses/tests/test_openai_responses_provider_unit.py -q`
- `python -m pytest plugins/openai_responses/tests/test_agent_application_openai_responses_config_loads.py -q`
- `python -m pytest plugins/openai_responses/tests/test_openai_responses_chatgpt_native_compaction_manual_integration.py -m manual_integration -q`