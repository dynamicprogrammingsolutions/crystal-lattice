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
