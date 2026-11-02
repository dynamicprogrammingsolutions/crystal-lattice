# Compatibility Source Drift

Observed: `2026-10-24`
Accepted source: `add5f5e71de3bb1676851bb840dfd77620f63ddb`
Current product source: `b61b38cc33132128b74ea6acb812959af5fde951`

## Outcome

Focused source drift exists and is represented in the version-two projection.

## Refreshed public claims

- **Anthropic provider:** Native automatic compaction moved from planned to conditional current support; native context editing was added as a conditional capability.
- **Codex-oriented harness:** exec_command and write_stdin moved from planned to included current tools; legacy shell modes remain optional.
- **Claude-compatible harness:** The existing compaction capability now includes a background application plugin with notifications, cancellation, retry, and pre-commit snapshots.
- **Plugin catalogue:** Added embedded-workspace-settings, interleaved-thinking, and shell-tool-settings with distribution/optional lifecycle boundaries.

## Configured agents

- Current display metadata is available for 20 agents.
- No provider/model/plugin/shell-mode drift was detected in the accepted configured-agent rows.

## Plugin project drift

- Added: `embedded-workspace-settings`, `interleaved-thinking`, `shell-tool-settings`
- Removed: none

### Descriptor changes

- `anthropic-compatible` added `anthropic_plugins.context_editing_extension.AnthropicContextEditingExtension`, `anthropic_plugins.compaction_extension.AnthropicCompactionExtension`.
- `claude-tools` added `claude_tools.claude_compaction_app.ClaudeCompactionAppPlugin`.
- `codex-tools` added `codex_tools.unified_exec_tool.ExecCommandTool`, `codex_tools.unified_exec_tool.WriteStdinTool`.

## Focused verification

- **Anthropic native context management:** `20 passed`
  - `pytest plugins/anthropic-compatible/tests/test_context_management_unit.py plugins/anthropic-compatible/tests/test_stack_integration.py -q`
- **Claude-compatible compaction:** `43 passed`
  - `pytest plugins/claude-tools/tests/test_claude_compaction_feature.py plugins/claude-tools/tests/test_claude_compaction_feature_action.py plugins/claude-tools/tests/test_claude_compaction_app.py -q`
- **Codex unified exec and shell selection:** `98 passed`
  - `pytest plugins/codex-tools/tests/test_unified_exec_tool.py plugins/codex-tools/tests/test_shell_tool_selection.py -q`
- **Embedded workspace settings:** `2 passed`
  - `PYTHONPATH=plugins/embedded-workspace-settings/src pytest plugins/embedded-workspace-settings/tests -q`
- **Interleaved thinking:** `9 passed`
  - `PYTHONPATH=plugins/interleaved-thinking/src pytest plugins/interleaved-thinking/tests -q`
- **Shell-tool settings:** `13 passed`
  - `PYTHONPATH=plugins/shell-tool-settings/src pytest plugins/shell-tool-settings/tests -q`

## Remaining limits

- No hosted provider request was run for this focused refresh.
- Anthropic compaction and context editing remain capability-gated.
- The accepted catalogue was not broadly regenerated or re-audited.
- Unchanged accepted rows retain their original verification state and limitations.
- The complete compatibility route and responsive presentation are not implemented.
