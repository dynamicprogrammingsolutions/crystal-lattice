# Gemini Replace App Integration And Empty Instruction Fix

Add a real application-layer integration test for the Gemini `replace` tool using the path-loaded plugin bundle and then align the implementation with Gemini CLI behavior so empty or missing `instruction` values do not fail execution.

## Requirements checklist

- [x] Add a real API application-level integration test that loads `gemini-tools` via `path:` and exercises `replace` through `AgentApplication`
- [x] Make the test use config patterned after the default Gemini app config and load API keys from the repo root `.env`
- [x] Reproduce the current failure where `replace` rejects an empty `instruction`
- [x] Change runtime behavior so empty or missing `instruction` does not fail execution
- [x] Keep Gemini-compatible model-facing schema behavior unless there is a strong reason to change it
- [x] Update assertions so the integration test passes after the fix

## Current understanding

The default application config for Gemini tools is already path-based:

- `application/python/agent_terminal_app/default_config/config.json:171-220`
  - Provider id: `openrouter_gemini_tools`
  - Plugin loading: `path:${env:BUILTIN_PLUGINS}/gemini-tools`

The current port rejects empty `instruction` values during execution:

- `plugins/gemini-tools/src/gemini_tools/gemini_replace_tool.py:65-78`
  - Runtime check:
    - `if not isinstance(instruction, str) or not instruction.strip():`
    - returns `"The 'instruction' parameter must be non-empty."`

However, the current Python implementation does not otherwise use `instruction`.

## Gemini CLI parity research

The original Gemini CLI keeps `instruction` in the schema but does not use it as a hard runtime gate:

- Schema still requires it:
  - `../gemini-cli/packages/core/src/tools/definitions/model-family-sets/default-legacy.ts:304-345`
- Runtime params type makes it optional:
  - `../gemini-cli/packages/core/src/tools/edit.ts:398-403`
- Runtime validation does not reject missing or empty `instruction`:
  - `../gemini-cli/packages/core/src/tools/edit.ts:967-999`

In Gemini CLI, `instruction` is mainly used for LLM-based edit recovery after a failed match:

- `../gemini-cli/packages/core/src/tools/edit.ts:445-520`
  - Calls `FixLLMEditWithInstruction(...)`
- `../gemini-cli/packages/core/src/tools/edit.ts:470-478`
  - Uses fallback text:
    - `params.instruction ?? 'Apply the requested edit.'`
- `../gemini-cli/packages/core/src/utils/llm-edit-fixer.ts:18-68`
  - The utility model receives:
    - high-level instruction
    - failed search string
    - replacement string
    - error text
    - full file contents

So the original Gemini CLI behavior is:

- Schema-required for the model
- Runtime-tolerant
- Used as auxiliary context for self-correction, not as a base execution precondition

## Test shape

Use a real OpenRouter-backed application-level test, not a pre-seeded tool-call-only test as the final coverage.

Recommended setup:

- Put the test in the Gemini plugin test suite
- Load `.env` from repo root
- Build config similar to the default Gemini app provider:
  - OpenRouter provider
  - `plugins: ["path:.../plugins/openrouter", "path:.../plugins/gemini-tools"]`
  - `plugin_policy.install_deps: true`
  - workspace settings for file edits
- Use `AgentApplication`
- Seed a real file in `tmp_path`
- Prompt the model to perform a simple replace edit that is known to trigger the Gemini `replace` tool

The reproduction goal is to capture:

- the emitted tool call arguments
- the `tool_results` error showing empty `instruction`

If there is user-provided prompt text or logs from the original failing run, use them verbatim in the test prompt to reduce model variance.

## Fix direction

Align runtime behavior with Gemini CLI compatibility:

- Keep `instruction` in the tool schema
- Stop rejecting empty or missing `instruction` at runtime

Conservative implementation options:

Option A:

- Remove the runtime non-empty validation entirely

Option B:

- Normalize blank values to a fallback string such as:
  - `"Apply the requested edit."`

Option B is slightly closer to the Gemini CLI recovery path if we later add self-correction logic.

## Validation plan

1. Add the real integration test and confirm the current failure is reproducible.
2. Change runtime handling so `instruction` is tolerated.
3. Verify the edit succeeds and the file content changes as requested.
4. Run the targeted Gemini plugin integration test file.

## Notes

- The previous synthetic regression test in `plugins/gemini-tools/tests/test_gemini_tools_application_integration.py` is useful for local diagnosis but is not the final coverage requested here.
- The intended end state is a real application-layer, real-API integration test plus Gemini-CLI-compatible runtime behavior.

## Completion Notes

Updated `plugins/gemini-tools/src/gemini_tools/gemini_replace_tool.py` so `instruction` is no longer a runtime gate. The schema still advertises it as required for Gemini compatibility, but execution now tolerates empty or missing values, matching the original Gemini CLI behavior more closely.

Added a real OpenRouter-backed `AgentApplication` integration test in `plugins/gemini-tools/tests/test_gemini_tools_application_integration.py` that prompts Gemini to emit a `replace` tool call with an empty `instruction`, then verifies the file edit succeeds. Added a local unit regression in `plugins/gemini-tools/tests/test_gemini_edit_write_tools.py` covering empty and missing `instruction` values directly.