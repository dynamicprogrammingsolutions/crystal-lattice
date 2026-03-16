# 020 - Edit and Write Tools

Short description: Plan the vendor-specific edit/write tool packages for `gemini-tools`, `qwen-tools`, and `grok-tools`, reusing the shared internal package while preserving each vendor's public tool names and schema conventions.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On: `tasks/20260315-gemini-qwen-grok-tool-packages/010-reader-tools.md`

## Goal

Add vendor-accurate write/edit tools to the three public plugin packages, while reusing the shared internal package for file writes, text replacement logic, diff helpers, and common filesystem rules.

## Public package outcome

1. `plugins/gemini-tools/`
- `write_file`
- `replace`
2. `plugins/qwen-tools/`
- `write_file`
- `edit`
3. `plugins/grok-tools/`
- `create_file`
- `str_replace_editor`

## Key source references

### Gemini

- Write tool:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/write-file.ts`
- Edit tool:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/edit.ts`
- Schema text:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/definitions/model-family-sets/default-legacy.ts:61`
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/definitions/model-family-sets/default-legacy.ts:290`
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/definitions/model-family-sets/gemini-3.ts:64`
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/definitions/model-family-sets/gemini-3.ts:291`

### Qwen

- Write tool:
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/write-file.ts`
- Edit tool:
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/edit.ts`
- Tool names and migration note:
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/tool-names.ts:8`

### Grok

- Schemas:
  - `/Users/ferenci84/Dev/Mine/grok-cli/src/grok/tools.ts:32`
  - `/Users/ferenci84/Dev/Mine/grok-cli/src/grok/tools.ts:53`
- Usage guidance:
  - `/Users/ferenci84/Dev/Mine/grok-cli/src/agent/grok-agent.ts:106`

## Compatibility findings

### Separate public classes are required

1. Gemini edit tool name is `replace`.
2. Qwen edit tool name is `edit`.
3. Grok edit tool name is `str_replace_editor`.
4. Gemini/Qwen write tool is `write_file`.
5. Grok write/create tool is `create_file`.

### Shared internals are still useful

A shared internal package should own most of:

1. safe path resolution
2. file existence checks
3. write helpers
4. encoding/BOM preservation if we choose to support it
5. literal replacement helpers
6. match counting and duplicate-match handling
7. common diff snippet generation for tests or display metadata

### Important parity limit

Exact Gemini/Qwen/Grok confirmation UX should not be promised here.

Reason:

1. Their edit/write flows depend on host-side confirmation systems.
2. Some rely on IDE diff handoff or approval modes outside a pure `ToolPlugin`.
3. Our target for this subtask is tool behavior parity, schema parity, and LLM-visible result parity, not full CLI interaction parity.

This limitation should be documented in the implementation README and tests.

## Proposed public tools

### `gemini-tools`

1. Gemini-like `write_file`
2. Gemini-like `replace`

### `qwen-tools`

1. Qwen-like `write_file`
2. Qwen-like `edit`

### `grok-tools`

1. Grok-like `create_file`
2. Grok-like `str_replace_editor`

## Behavior notes by vendor

### Gemini-like

1. Match Gemini schema names and parameter docs.
2. `replace` should mirror Gemini semantics including `allow_multiple` naming.
3. Replacement strategy should be as close as practical to Gemini's behavior.
4. Placeholder/omission-detection guidance should be preserved where practical in schema docs or validation.

### Qwen-like

1. Match Qwen schema names and parameter docs.
2. `edit` should use `replace_all`, not Gemini's `allow_multiple`.
3. Behavior should mirror Qwen's simpler direct replacement model where it differs from Gemini.
4. Preserve the Qwen migration distinction in docs, but do not expose Gemini aliases by default unless an explicit compatibility reason appears during implementation.

### Grok-like

1. `create_file` should mean creation-oriented file writing.
2. `str_replace_editor` should preserve Grok naming and argument names:
- `path`
- `old_str`
- `new_str`
- `replace_all`
3. Grok guidance strongly assumes `view_file` before editing and `create_file` only for new files. The tool package can match the tool contracts, but the higher-level prompting behavior belongs in agent instructions rather than the tool plugin itself.

## Test expectations

1. Schema tests per public tool.
2. Replacement behavior tests:
- zero matches
- one match
- multiple matches with and without the relevant multi-replace flag
3. File-creation and overwrite tests.
4. Important error wording snapshot tests for each vendor package.
5. Integration tests ensuring each package exposes only its intended public tool names.

## Deliverables

1. Vendor-specific edit/write public tool classes.
2. Shared internal write/replacement helpers.
3. Tests for schema parity and core replacement semantics.
4. Clear docs about the scope of parity and known host-UX differences.

## Documentation Follow-up Added After Completion

Added on 2026-03-16 after the implementation portion of this subtask was already completed.

User-facing documentation follow-up for this subtask should include:

1. Expand the package READMEs in:
- `plugins/gemini-tools/README.md`
- `plugins/qwen-tools/README.md`
- `plugins/grok-tools/README.md`
2. Add an exposed-tool section listing the current write/edit public surface for each package.
3. Add a write/edit examples section with representative tool-call shapes and outcomes.
4. Add a cross-package comparison note so users can quickly understand:
- Gemini `replace`
- Qwen `edit`
- Grok `str_replace_editor`
5. Add a compatibility-and-limitations section making the host-UX boundary explicit:
- schema/tool behavior parity is in scope
- CLI confirmation UX, IDE diff handoff, and approval flows are not
6. Add any package-level configuration notes relevant to write/edit behavior, safety constraints, workspace restrictions, or replacement settings.
7. Where helpful, include one or two representative validation/error examples such as zero-match, multiple-match, or creation-vs-overwrite behavior.

## Execution Plan Added During Completion

Added on 2026-03-16 during subtask completion.

1. Extend the shared internal package in `plugins/tool-compat-shared/src/tool_compat_shared/` with write/edit helpers for safe path resolution reuse, create/write operations, literal replacement matching, and neutral result payload helpers.
2. Add vendor-specific public tools exposing OpenAI chat-completions-style function schemas only:
- `plugins/gemini-tools/` with `GeminiWriteFileTool` and `GeminiReplaceTool`
- `plugins/qwen-tools/` with `QwenWriteFileTool` and `QwenEditTool`
- `plugins/grok-tools/` with `GrokCreateFileTool` and `GrokStrReplaceEditorTool`
3. Update package exports, plugin manifests, and READMEs so each package exposes only its intended public tools and documents parity scope plus host-UX limitations.
4. Add shared-engine unit tests, per-package schema/behavior tests, and OpenRouter integration tests that exercise the intended vendor model family and verify resulting file contents.
5. Run the relevant test slices, report results, and append completion notes to this file.

## Completion Notes Added During Completion

Added on 2026-03-16 after implementation and verification.

### What changed

Implemented the shared edit/write layer and the vendor-specific public tools using OpenAI chat-completions-style function schemas:

1. Shared helper package:
- Added `plugins/tool-compat-shared/src/tool_compat_shared/editor_engine.py`
- Exported `write_text_file` and `replace_literal_text` from `plugins/tool-compat-shared/src/tool_compat_shared/__init__.py`
- Added shared engine tests in `plugins/tool-compat-shared/tests/test_editor_engine.py`

2. `plugins/gemini-tools/`:
- Added `GeminiWriteFileTool` in `plugins/gemini-tools/src/gemini_tools/gemini_write_file_tool.py`
- Added `GeminiReplaceTool` in `plugins/gemini-tools/src/gemini_tools/gemini_replace_tool.py`
- Updated exports, plugin manifest, README, and package-manager expectations
- Added unit/integration tests for Gemini edit/write flows

3. `plugins/qwen-tools/`:
- Added `QwenWriteFileTool` in `plugins/qwen-tools/src/qwen_tools/qwen_write_file_tool.py`
- Added `QwenEditTool` in `plugins/qwen-tools/src/qwen_tools/qwen_edit_tool.py`
- Updated exports, plugin manifest, README, and package-manager expectations
- Added unit/integration tests for Qwen edit/write flows

4. `plugins/grok-tools/`:
- Added `GrokCreateFileTool` in `plugins/grok-tools/src/grok_tools/grok_create_file_tool.py`
- Added `GrokStrReplaceEditorTool` in `plugins/grok-tools/src/grok_tools/grok_str_replace_editor_tool.py`
- Updated exports, plugin manifest, README, and package-manager expectations
- Added unit/integration tests for Grok edit/write flows

5. Documentation/task tracking:
- Updated the package READMEs to note the new tool surfaces and the explicit host-UX parity limitation
- Appended plan and completion notes to this subtask file

### Files touched

1. Shared helpers:
- `plugins/tool-compat-shared/src/tool_compat_shared/editor_engine.py`
- `plugins/tool-compat-shared/src/tool_compat_shared/__init__.py`
- `plugins/tool-compat-shared/tests/test_editor_engine.py`
- `plugins/tool-compat-shared/README.md`

2. Gemini package:
- `plugins/gemini-tools/src/gemini_tools/gemini_write_file_tool.py`
- `plugins/gemini-tools/src/gemini_tools/gemini_replace_tool.py`
- `plugins/gemini-tools/src/gemini_tools/__init__.py`
- `plugins/gemini-tools/agent_plugin.json`
- `plugins/gemini-tools/tests/test_gemini_edit_write_tools.py`
- `plugins/gemini-tools/tests/test_gemini_edit_write_tools_openrouter_integration.py`
- `plugins/gemini-tools/tests/test_gemini_read_file_tool.py`
- `plugins/gemini-tools/README.md`

3. Qwen package:
- `plugins/qwen-tools/src/qwen_tools/qwen_write_file_tool.py`
- `plugins/qwen-tools/src/qwen_tools/qwen_edit_tool.py`
- `plugins/qwen-tools/src/qwen_tools/__init__.py`
- `plugins/qwen-tools/agent_plugin.json`
- `plugins/qwen-tools/tests/test_qwen_edit_write_tools.py`
- `plugins/qwen-tools/tests/test_qwen_edit_write_tools_openrouter_integration.py`
- `plugins/qwen-tools/tests/test_qwen_read_file_tool.py`
- `plugins/qwen-tools/README.md`

4. Grok package:
- `plugins/grok-tools/src/grok_tools/grok_create_file_tool.py`
- `plugins/grok-tools/src/grok_tools/grok_str_replace_editor_tool.py`
- `plugins/grok-tools/src/grok_tools/__init__.py`
- `plugins/grok-tools/agent_plugin.json`
- `plugins/grok-tools/tests/test_grok_edit_write_tools.py`
- `plugins/grok-tools/tests/test_grok_edit_write_tools_openrouter_integration.py`
- `plugins/grok-tools/tests/test_grok_view_file_tool.py`
- `plugins/grok-tools/README.md`

### Tests run

1. Focused non-integration suites:
- `pytest plugins/tool-compat-shared/tests/test_editor_engine.py plugins/gemini-tools/tests/test_gemini_read_file_tool.py plugins/gemini-tools/tests/test_gemini_edit_write_tools.py plugins/qwen-tools/tests/test_qwen_read_file_tool.py plugins/qwen-tools/tests/test_qwen_edit_write_tools.py plugins/grok-tools/tests/test_grok_view_file_tool.py plugins/grok-tools/tests/test_grok_edit_write_tools.py -q`
- Result: `36 passed`

2. New OpenRouter integration tests for this subtask:
- `pytest plugins/gemini-tools/tests/test_gemini_edit_write_tools_openrouter_integration.py plugins/qwen-tools/tests/test_qwen_edit_write_tools_openrouter_integration.py plugins/grok-tools/tests/test_grok_edit_write_tools_openrouter_integration.py -q -m 'integration and openrouter'`
- Result: `3 passed`

3. Full shared/vendor package sweep after implementation:
- `pytest plugins/tool-compat-shared/tests plugins/gemini-tools/tests plugins/qwen-tools/tests plugins/grok-tools/tests -q`
- Result: `46 passed`

### Outcomes and notes

1. All targeted tools now expose vendor-specific public names and parameter names through OpenAI-style function schemas.
2. The shared package now owns reusable write/create and literal-replacement logic, including creation-only mode and common replacement outcome handling.
3. Package manifests now expose the reader plus edit/write tools for each vendor package.
4. One Gemini integration run initially showed newline-preservation variance after model-selected replacement arguments; the test was adjusted to assert the intended semantic content change rather than a brittle trailing-newline detail.
5. The full package sweep still emits `PytestUnknownMarkWarning` for existing `integration`/`openrouter` marks in these plugin test directories; this warning pre-existed the subtask pattern and did not block passing results.

### Open issues

1. The pure tool-plugin implementation still does not attempt to reproduce vendor CLI confirmation UX, IDE diff handoff, or approval-mode behavior.
2. Replacement behavior is intentionally literal and compatibility-oriented; upstream Gemini's more advanced edit-recovery strategies and Grok's hinted fuzzy multi-line behavior are not replicated in this subtask.
