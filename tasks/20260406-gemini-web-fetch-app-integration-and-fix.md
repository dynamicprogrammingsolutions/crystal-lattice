# Gemini Web Fetch App Integration And Fix

Add a real application-layer integration test for the Gemini `web_fetch` tool using the path-loaded plugin bundle and then correct the fallback implementation so the test passes.

## Requirements checklist

- [x] Add a real API application-level integration test that loads `gemini-tools` via `path:` and exercises `web_fetch` through `AgentApplication`
- [x] Make the test use config patterned after the default Gemini app config and load API keys from the repo root `.env`
- [x] Reproduce the current fallback failure involving `AgentCore.stream_request`
- [x] Fix the fallback summarization path to use supported `AgentCore` request APIs
- [x] Update assertions so the integration test passes after the fix

## Current understanding

The default terminal/application config already uses the Gemini tool bundle through a path-loaded provider plugin configuration:

- `application/python/agent_terminal_app/default_config/config.json:171-220`
  - Provider id: `openrouter_gemini_tools`
  - Plugin loading: `path:${env:BUILTIN_PLUGINS}/gemini-tools`

The current bug is in the Gemini tool implementation, not in the app layer:

- `plugins/gemini-tools/src/gemini_tools/gemini_web_fetch_tool.py:749-818`
  - In fallback summarization, the tool tries:
    - `fallback_core.stream_request(temp_session, fallback_config)`
    - `core.stream_request(temp_session, config)`
  - `AgentCore` does not have `stream_request`

The supported `AgentCore` request methods are:

- `core/python/agent_core/core.py:1843-1978`
  - `send_request(session, config, ...) -> (Session, final_messages)`
- `core/python/agent_core/core.py:1992-2080`
  - `send_request_stream(session, config, ...) -> Iterator[event]`

This is why the observed tool error is:

- `Fallback fetch error: 'AgentCore' object has no attribute 'stream_request'`

## Test shape

Use a real OpenRouter-backed application-level test, not a synthetic pre-seeded tool-call test.

Recommended setup:

- Put the test in the Gemini plugin test suite, near the existing OpenRouter Gemini tool integrations.
- Load `.env` from the repo root to get `OPENROUTER_API_KEY` and any optional overrides.
- Build a config that mirrors the default Gemini app provider:
  - OpenRouter provider
  - Gemini model or override env var
  - `working_directory`, `allowed_paths`
  - `plugins: ["path:.../plugins/openrouter", "path:.../plugins/gemini-tools"]`
  - `plugin_policy.install_deps: true`
- Use `AgentApplication`, not raw `AgentCore`
- Drive the tool through the normal app request/tool loop with `app.send_request(...)`

For deterministic fallback coverage:

- Start a tiny local HTTP server inside the test
- Prompt the model to use `web_fetch` against a localhost URL
- Private/local URLs should force the fallback path in `gemini_web_fetch_tool.py`
- Capture `tool_results` events and assert the current failing message before the fix

## Fix direction

Replace the unsupported `stream_request(...)` usage with one supported path:

Option A:

- Use `send_request_stream(...)`
- Aggregate `partial` and `final` events into a single fallback answer string

Option B:

- Use `send_request(...)`
- Extract the final assistant content from returned messages

Implementation guidance:

- Prefer one small helper inside `gemini_web_fetch_tool.py` for "run a one-off summarization turn and collect final text"
- Reuse it in both:
  - the fallback-agent branch
  - the current-agent/core branch
- Preserve current behavior around `fallback_settings_overrides`

## Validation plan

1. Add the real integration test and confirm it reproduces the current error.
2. Implement the fallback request helper.
3. Update the test to assert successful fallback summarization instead of the old error text.
4. Run the targeted Gemini plugin integration test file.

## Notes

- The previous synthetic app-layer regression test added in `plugins/gemini-tools/tests/test_gemini_tools_application_integration.py` is not the desired final coverage because it bypasses the real model decision path.
- Keep the final test application-level and real-API-backed.

## Completion Notes

Added a real OpenRouter-backed `AgentApplication` integration test in `plugins/gemini-tools/tests/test_gemini_tools_application_integration.py` that loads `gemini-tools` via `path:` and uses a local HTTP server plus Gemini `web_fetch` to exercise the fallback path through the application tool loop.

Fixed `plugins/gemini-tools/src/gemini_tools/gemini_web_fetch_tool.py` by replacing the unsupported `stream_request(...)` calls with a helper that runs a one-off fallback summarization through `AgentCore.send_request(...)`, forces `tool_choice: none` for that internal summarization turn, and falls back to raw fetched content if the summarizer returns no assistant text.