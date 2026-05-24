# Follow-on Test Cleanup Backlog

Record the larger cleanup areas that should not block the first marker/env/command pass, but are worth preserving now so a later agent can split them into implementation tasks without re-scoping from scratch.

## Requirements checklist

- [ ] Capture the deferred cleanup areas requested by the user.
- [ ] Preserve the current evidence for why each deferred area matters.
- [ ] Keep these items explicitly out of the first implementation pass unless directly needed by the accepted scope.

Parent Task: `tasks/20260524-test-and-agents-cleanup/000-main.md`

## Deferred area 1: SDK and example e2e cleanup

Why this matters:

- Provider-backed examples currently blur the line between example smoke tests and integration tests.
- Eight example tests in `core/python/examples/tests` currently use provider or Ollama markers without `integration`:
  - `core/python/examples/tests/test_example5_project_plan_basic.py`
  - `core/python/examples/tests/test_example6_project_plan_streaming.py`
  - `core/python/examples/tests/test_example7_project_plan_tool_calls.py`
  - `core/python/examples/tests/test_example8_project_plan_messages.py`
  - `core/python/examples/tests/test_example9_project_plan_config_updates.py`
  - `core/python/examples/tests/test_example11_openai_tools_file_reader.py`
  - `core/python/examples/tests/test_example12_openrouter_tools_app.py`
  - `core/python/examples/tests/test_example13_openrouter_tools_app_layer.py`

Possible follow-up work:

- decide whether example/provider smoke tests should always also carry `integration`
- separate pure example correctness from provider-backed example verification
- clarify whether SDK e2e coverage belongs in `core/python/examples/tests` or in a more clearly named e2e location

## Deferred area 2: terminal/server test organization

Why this matters:

- `application/python/tests/test_agent_terminal_app_server.py` is large and mixes local HTTP behavior, app flow behavior, and at least one Ollama-backed integration path.
- `application/python/tests/test_terminal_application.py` is also large and covers many concerns in one place.

Useful references:

- `application/python/tests/test_agent_terminal_app_server.py:1`
- `application/python/tests/test_agent_terminal_app_server.py:3238-3239`
- `application/python/tests/test_terminal_application.py:1545`

Possible follow-up work:

- split local HTTP endpoint behavior from real-provider integration behavior
- separate terminal UI/business-logic tests from broader application flow tests
- reduce the amount of broad-file scanning needed when contributors change terminal/server behavior

## Deferred area 3: default-config-heavy test cleanup

Why this matters:

- `application/python/tests` contains many tests that depend on `agent_terminal_app/default_config/config.json` and repeated env setup.
- There is duplicated setup logic across OpenRouter, OpenAI, Gemini, Kimi, image-generation, MCP, and Codex/default-config tests.

Representative references:

- `application/python/tests/test_terminal_application_default_config_openrouter_integration.py`
- `application/python/tests/test_default_config_openrouter_image_generation_integration.py`
- `application/python/tests/test_terminal_default_config_codex_gpt5_apply_patch_real_api.py`
- `application/python/tests/test_terminal_default_config_codex_mcp_real_api.py`
- `application/python/tests/test_terminal_default_config_codex_view_image_real_api.py`
- `application/python/tests/test_gemini_web_search_integration.py`
- `application/python/tests/test_kimi_web_search_integration.py`

Possible follow-up work:

- centralize default-config env fixture setup
- split local default-config assertions from hosted real-provider assertions
- reduce repeated API-key helper logic after the shared env-loader is introduced

## Guidance for future splitting

If these deferred areas become their own tasks later, a good next split would likely be:

1. SDK/example e2e and provider-backed example classification
2. terminal/server suite decomposition
3. default-config fixture and test-organization cleanup

## Important scope guard

These items should be documented during the current cleanup, but they should not derail the first implementation pass focused on:

- marker standardization
- env-loading standardization
- standard run commands
- root `AGENTS.md` cleanup