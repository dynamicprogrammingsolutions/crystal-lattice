# Investigate And Implement Claude Compaction

Determine Claude Code's compaction behavior and add Claude-compatible compaction support.

## Requirements checklist

- [x] Investigate Claude Code compaction prompts/output format through behavior, if possible.
- [x] Decide Claude implementation direction without coupling it to the Gemini compaction packages.
- [x] Implement Claude-compatible compaction action support.
- [x] Add unit and application integration tests for Claude compaction behavior.
- [x] Wire Claude compaction into the existing Claude plugin/default-config path without adding Gemini-style compaction config keys.

Parent Task: tasks/20260504-claude-tools-parity/000-main.md

Depends On: tasks/20260504-claude-tools-parity/010-investigate-claude-code-behavior.md
Depends On: tasks/20260504-claude-tools-parity/030-implement-claude-system-message-and-config.md

## Existing State

Current compaction support is Gemini-shaped:

- `plugins/gemini-compaction-app`
- `plugins/gemini-compaction-feature`

The app plugin prompt asks for a structured XML `<state_snapshot>` with sections such as:

- `<overall_goal>`
- `<active_constraints>`
- `<key_knowledge>`
- `<artifact_trail>`
- `<file_system_state>`
- `<recent_actions>`
- `<task_state>`

The app plugin is configured per agent under:

```yaml
compaction:
  enabled: false
  type: "gemini"
  agent_id: null
  prompt: null
  settings_overrides: {}
  verification_pass: true
```

The feature plugin mirrors this with feature-level actions.

## Investigation Notes

Claude Code likely has its own compaction behavior, but this was not yet captured. Investigate via real Claude Code behavior because Claude Code is not open source.

Potential approaches:

- Trigger `/compact` in an interactive or scripted Claude Code session and proxy-log the internal request.
- Create a long context in print/stream-json mode and observe whether automatic compaction occurs.
- Search Claude Code local cache/debug logs for compaction-related request markers, but do not rely on code internals.

Capture:

- compaction prompt/system instructions
- output format expected from summarizer
- any acknowledgement message inserted into conversation history
- whether verification/self-critique pass exists
- whether tool outputs receive special handling

## Implementation Direction

Implement Claude compaction as a Claude-specific feature plugin inside `plugins/claude-tools`.

- Keep Gemini compaction separate for now.
- Use the Gemini compaction packages only as references for how a similar feature is wired in this repo.
- Avoid introducing shared Gemini/Claude compaction abstractions during this task.

## Execution plan

Added during completion after user approval.

Stage 1: Investigation only. Do not make production compaction behavior changes yet.

- [x] Reuse the existing Claude proxy harness and artifact conventions from `tasks/20260504-claude-tools-parity/010-investigate-claude-code-behavior.md` and `plugins/claude-tools/investigation/`.
- [x] Add a focused Claude compaction investigation script under `plugins/claude-tools/investigation/scripts/` that can run Claude Code through the proxy, trigger compaction scenarios, and capture normalized artifacts.
- [x] Run a compact investigation matrix covering:
  - explicit/manual compaction trigger if available
  - automatic compaction trigger if it can be reproduced reliably
  - a case with tool history in the compacted range
  - a case with a prior snapshot/summary already present
- [x] Capture and document the observed compaction behavior:
  - summarizer prompt/system instructions
  - output format
  - history injection shape
  - acknowledgment message behavior
  - verification/self-critique pass behavior
  - treatment of tool outputs and file-state details
- [x] Compare observed Claude behavior with the current Gemini compaction plugins and record a Claude-specific implementation direction without introducing shared Gemini/Claude compaction abstractions.
- [x] Pause after investigation and present findings plus a separate Stage 2 implementation plan for approval before any production implementation work.

Stage 2: Implementation, added during completion after the user approved moving past investigation.

- [x] Implement a Claude-specific compaction feature plugin inside `plugins/claude-tools/src/claude_tools/`.
- [x] Register the feature in `plugins/claude-tools/agent_plugin.json` so the session action appears whenever the `claude-tools` package is enabled.
- [x] Keep the implementation self-contained and separate from Gemini compaction logic.
- [x] Use the normalized compaction fixtures and investigation notes as the behavioral contract for:
  - prompt construction
  - summary validation
  - compacted-history injection shape
  - repeated compaction behavior
- [x] Add fixture-driven unit tests in `plugins/claude-tools/tests/`.
- [x] Add an application-style action test covering the feature action path.
- [x] Run focused verification and update this task file plus `tasks/20260504-claude-tools-parity/000-main.md` with the actual final status.

## Investigation Notes

Added during Stage 1 investigation.

- Manual compaction is available via the `/compact` slash command, and it works in `claude -p --output-format stream-json` mode when the session is resumed with `-c`.
- Normalized fixtures were added under `plugins/claude-tools/investigation/fixtures/compaction/` for:
  - `error-no-messages`
  - `error-not-enough-messages`
  - `success-basic`
  - `success-tool-history`
  - `success-prior-summary`
- Investigation harness and notes were added:
  - `plugins/claude-tools/investigation/scripts/investigate_compaction.py`
  - `plugins/claude-tools/investigation/notes/compaction.md`
  - The investigation script now also normalizes machine-specific memory-directory paths into stable placeholders such as `<MEMORY_DIR>`.
- Key observed behavior:
  - On success, Claude injects a synthetic user summary message rather than Gemini-style XML.
  - The summary includes numbered prose sections, transcript-path fallback guidance, and a resume-without-acknowledgement directive.
  - A local command trail is also recorded around compaction (`<local-command-caveat>`, `/compact`, `Compacted`).
  - Tool-derived state can be preserved in the summary and transcript attachments.
  - A dedicated verification/self-critique pass was not observed.
  - The exact outgoing compaction request body was captured through `../openai-proxy`: Claude sends the normal session system prompt and prior conversation, then appends a compaction-specific summarization instruction block as the final user-message content rather than switching to a Gemini-like snapshot prompt format.
- Recommendation from investigation:
  - Implement Claude compaction separately inside `plugins/claude-tools` as a Claude-specific feature plugin, without generalizing the Gemini compaction packages.

## Completion Notes

Added during completion after implementation and verification.

- Script-driven normalization is complete:
  - `plugins/claude-tools/investigation/scripts/investigate_compaction.py` now regenerates normalized fixtures with `<WORKSPACE>`, `<PROJECT_TRANSCRIPT>`, `<SESSION_ID>`, and `<MEMORY_DIR>` placeholders.
  - The committed compaction fixtures also include normalized outgoing request artifacts such as `compact_request`, `compact_request_prompt_text`, and `compact_request_prompt_sections`.
- Production Claude compaction support was implemented as a Claude-specific feature plugin:
  - `plugins/claude-tools/src/claude_tools/claude_compaction_feature.py`
  - `plugins/claude-tools/agent_plugin.json`
  - `plugins/claude-tools/src/claude_tools/__init__.py`
- The implementation is intentionally separate from Gemini compaction logic.
- The feature exposes a session action whenever the `claude-tools` package is enabled and does not use Gemini-style `compaction.enabled` or `compaction.type` parameters.
- Tests added against normalized fixtures:
  - `plugins/claude-tools/tests/test_claude_compaction_feature.py`
  - `application/python/tests/test_claude_compaction_feature_action.py`
- Additional integration coverage was added at both requested levels:
  - `plugins/claude-tools/tests/test_claude_compaction_feature_ollama_integration.py`
  - `application/python/tests/test_claude_default_config_compaction_integration.py`
- Current Claude compaction config surface is:
  - `compaction_model`
  - `claude_compaction_prompt`
  - `claude_compaction_settings_overrides`
  - `compaction_model` is the primary dedicated-model knob; advanced request-only tuning remains available through `claude_compaction_settings_overrides`.
- The compaction rewrite path now follows the `summarize-range-app` pattern more closely:
  - the feature builds a compacted `Session` via `AgentCore.rebuild_native_history`, `slice_session`, and `add_message`
  - provider-native history is then read back from the rebuilt session metadata
  - hardcoded provider-native message assembly is no longer used for the final action result
- Claude compaction now supports:
  - config/UI exposure for `compaction_model`
  - session-action range selection (`start`, `end`, `end_inclusive`)
  - a message-level `Compact messages up to here` UI action
  - preservation of a leading system message in the visible transcript for every compaction mode, while still including that system message in subrange compaction requests as context
- Focused verification completed:
  - `pytest plugins/claude-tools/tests/test_claude_compaction_feature.py -q`
  - `pytest application/python/tests/test_claude_compaction_feature_action.py -q`
  - `pytest plugins/claude-tools/tests/test_claude_compaction_feature_ollama_integration.py -q`
  - `pytest -m 'integration and api and openrouter' application/python/tests/test_claude_default_config_compaction_integration.py -q`
  - `ruff check plugins/claude-tools/src/claude_tools/claude_compaction_feature.py plugins/claude-tools/tests/test_claude_compaction_feature.py application/python/tests/test_claude_compaction_feature_action.py`
  - `black --check plugins/claude-tools/src/claude_tools/claude_compaction_feature.py plugins/claude-tools/tests/test_claude_compaction_feature.py application/python/tests/test_claude_compaction_feature_action.py`
- No new default-config keys were added. The existing default Claude agent already points at the `claude-tools` package, so adding the feature to that package made the session action available without introducing extra config wiring.
