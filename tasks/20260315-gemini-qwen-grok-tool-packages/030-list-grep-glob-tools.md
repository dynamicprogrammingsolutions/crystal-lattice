# 030 - List, Grep, and Glob Tools

Short description: Plan the vendor-style directory listing, grep, and glob tools for `gemini-tools` and `qwen-tools`, while documenting Grok's divergence toward a unified `search` tool and limiting this subtask accordingly.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On: `tasks/20260315-gemini-qwen-grok-tool-packages/010-reader-tools.md`

## Goal

Add compatibility-oriented list/search tools to the vendor packages, with a narrower level of detail than the reader subtask.

This subtask should focus on:

1. Gemini-like `list_directory`, `grep_search`, `glob`
2. Qwen-like `list_directory`, `grep_search`, `glob`
3. Documenting why Grok's unified `search` tool is not part of this subtask

## Key source references

### Gemini

- List tool:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/ls.ts`
- Glob tool:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/glob.ts`
- Grep tool:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/grep.ts`
- Schema text:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/definitions/model-family-sets/default-legacy.ts:83`
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/definitions/model-family-sets/default-legacy.ts:210`
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/definitions/model-family-sets/default-legacy.ts:247`
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/definitions/model-family-sets/gemini-3.ts:84`
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/definitions/model-family-sets/gemini-3.ts:211`
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/definitions/model-family-sets/gemini-3.ts:248`

### Qwen

- List tool:
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/ls.ts`
- Glob tool:
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/glob.ts`
- Grep tool:
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/grep.ts`
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/ripGrep.ts`

### Grok

- Unified search schema:
  - `/Users/ferenci84/Dev/Mine/grok-cli/src/grok/tools.ts:102`

## Findings to preserve

### Gemini and Qwen overlap enough for shared internals

Shared internal helpers should cover:

1. directory listing and sorting
2. ignore filtering hooks
3. glob expansion and sorting-by-recency helpers
4. grep result parsing and formatting helpers
5. optional ripgrep execution when available

### But the public schemas still differ

Examples:

1. Gemini list tool uses `dir_path`; Qwen list tool uses `path`.
2. Gemini glob supports more explicit ignore-related knobs in its schema.
3. Qwen glob truncates output based on config limits.
4. Gemini grep supports parameters like `include_pattern`, `exclude_pattern`, `names_only`, `max_matches_per_file`, and `total_max_matches`.
5. Qwen grep uses a simpler `path`, `glob`, `limit` shape in its main grep tool.

### Grok is intentionally out of scope here

Grok's `search` is not just a wrapper over list/glob/grep. It is a combined search surface with:

1. `query`
2. `search_type`
3. include/exclude patterns
4. regex/whole-word/case-sensitive flags
5. max-results and file-type filtering

That deserves its own later subtask rather than being forced into the list/grep/glob work.

## Proposed public package outcome

### `gemini-tools`

1. `list_directory`
2. `grep_search`
3. `glob`

### `qwen-tools`

1. `list_directory`
2. `grep_search`
3. `glob`

### `grok-tools`

No new public tools from this subtask.

Instead, add a note in `grok-tools` docs that Grok-compatible `search` should be handled in a dedicated later task.

## Implementation direction

1. Prefer Python implementations.
2. For grep, prefer `rg` subprocess execution when available for parity and performance.
3. Provide Python fallback behavior when `rg` is unavailable.
4. Keep exact model-facing schema docs vendor-specific.
5. Use the shared internal package for reusable mechanics but not public tool names.

## Test expectations

1. Schema tests per Gemini and Qwen public tool.
2. Listing tests for path validation, empty directories, sorting, and ignored-file reporting.
3. Glob tests for pattern matching, path scoping, sorting, and truncation behavior.
4. Grep tests for match formatting, names-only or limit behavior, and `rg` vs fallback paths where feasible.
5. Tests that `grok-tools` does not accidentally expose Gemini/Qwen list/grep/glob names.

## Deliverables

1. Gemini-compatible list/grep/glob tools.
2. Qwen-compatible list/grep/glob tools.
3. Shared internal search/list helpers.
4. Documentation note deferring Grok unified `search` to a later task.
5. README updates for `plugins/gemini-tools/README.md` and `plugins/qwen-tools/README.md` covering:
- exposed list/grep/glob tool surface
- quickstart usage examples
- vendor-specific behavior notes for listing, globbing, and grep result formatting
6. README update for `plugins/grok-tools/README.md` noting that Grok-compatible unified `search` is intentionally deferred to a later dedicated task.

## Approved Documentation Plan Added After Planning

Added on 2026-03-16 after review of existing plugin README patterns.

User-facing docs produced by this subtask should follow the stronger README conventions already used in plugin bundles such as `plugins/reference-openai-compatible-provider/README.md` and `plugins/openai_responses/README.md`, not just the minimal template shape.

At minimum, the README updates for this subtask should include:

1. A short purpose/scope statement.
2. Quickstart config examples.
3. An exposed-tool list.
4. Brief vendor-specific behavior notes users actually need when choosing between Gemini-like and Qwen-like tools.
5. A short limitations section where behavior is only approximate.
6. Development/test commands matching the repo's normal plugin README style.

## Execution Plan Added During Completion

Added on 2026-03-16 during subtask completion.

1. Add a shared search/list helper module under `plugins/tool-compat-shared/src/tool_compat_shared/` for path validation reuse, directory listing, glob expansion, grep execution/parsing, optional `rg` subprocess support, and Python fallback behavior.
2. Add Gemini public tools in `plugins/gemini-tools/src/gemini_tools/` for `list_directory`, `grep_search`, and `glob`, using OpenAI chat-completions function schemas only.
3. Add Qwen public tools in `plugins/qwen-tools/src/qwen_tools/` for `list_directory`, `grep_search`, and `glob`, again using OpenAI chat-completions function schemas and Qwen-specific parameter names/limits.
4. Update package exports, manifests, and READMEs in `plugins/gemini-tools/README.md`, `plugins/qwen-tools/README.md`, and `plugins/grok-tools/README.md`, with Grok explicitly documented as deferring unified `search` instead of exposing these three tools.
5. Add tests in the same change:
- shared-engine unit tests in `plugins/tool-compat-shared/tests/`
- Gemini unit/schema/behavior tests in `plugins/gemini-tools/tests/`
- Qwen unit/schema/behavior tests in `plugins/qwen-tools/tests/`
- a Grok regression test confirming no accidental `list_directory` / `grep_search` / `glob` exposure
- OpenRouter integration tests for Gemini and Qwen with cheap default models, following the existing reader/edit integration style
6. Run the relevant pytest slices, then append completion notes to this file.

## Completion Notes Added During Completion

Added on 2026-03-16 after implementation and verification.

### What changed

Implemented the shared list/glob/grep layer and exposed the vendor-specific Gemini and Qwen public tools using OpenAI chat-completions-style function schemas only.

1. Shared helper package:
- Added `plugins/tool-compat-shared/src/tool_compat_shared/search_engine.py`
- Exported the new list/glob/grep helpers and formatter helpers from `plugins/tool-compat-shared/src/tool_compat_shared/__init__.py`
- Added shared helper tests in `plugins/tool-compat-shared/tests/test_search_engine.py`

2. `plugins/gemini-tools/`:
- Added `GeminiListDirectoryTool` in `plugins/gemini-tools/src/gemini_tools/gemini_list_directory_tool.py`
- Added `GeminiGrepSearchTool` in `plugins/gemini-tools/src/gemini_tools/gemini_grep_search_tool.py`
- Added `GeminiGlobTool` in `plugins/gemini-tools/src/gemini_tools/gemini_glob_tool.py`
- Updated exports and `agent_plugin.json` so the package now exposes the Gemini reader, search, glob, write, and replace surfaces together
- Added unit and OpenRouter integration tests for the Gemini search tools
- Updated README coverage for the new search surface and behavior notes

3. `plugins/qwen-tools/`:
- Added `QwenListDirectoryTool` in `plugins/qwen-tools/src/qwen_tools/qwen_list_directory_tool.py`
- Added `QwenGrepSearchTool` in `plugins/qwen-tools/src/qwen_tools/qwen_grep_search_tool.py`
- Added `QwenGlobTool` in `plugins/qwen-tools/src/qwen_tools/qwen_glob_tool.py`
- Updated exports and `agent_plugin.json` so the package now exposes the Qwen reader, search, glob, write, and edit surfaces together
- Added unit and OpenRouter integration tests for the Qwen search tools
- Updated README coverage for the new search surface and behavior notes

4. `plugins/grok-tools/`:
- Added a regression test confirming the Grok package still exposes only `view_file`, `create_file`, and `str_replace_editor`
- Updated README text to explicitly defer Grok-compatible unified `search` to a later dedicated task and to note that this package does not expose Gemini/Qwen-style `list_directory`, `grep_search`, or `glob`

5. Regression/test follow-up in existing suites:
- Updated the existing Gemini and Qwen plugin-manager expectations in the reader tests to reflect the expanded package manifests
- Made two OpenRouter integration assertions more resilient to provider output shape differences where `OK` may appear in repeated content or reasoning metadata rather than a single plain-text token

### Files touched

1. Shared helpers:
- `plugins/tool-compat-shared/src/tool_compat_shared/search_engine.py`
- `plugins/tool-compat-shared/src/tool_compat_shared/__init__.py`
- `plugins/tool-compat-shared/tests/test_search_engine.py`

2. Gemini package:
- `plugins/gemini-tools/src/gemini_tools/gemini_list_directory_tool.py`
- `plugins/gemini-tools/src/gemini_tools/gemini_grep_search_tool.py`
- `plugins/gemini-tools/src/gemini_tools/gemini_glob_tool.py`
- `plugins/gemini-tools/src/gemini_tools/__init__.py`
- `plugins/gemini-tools/agent_plugin.json`
- `plugins/gemini-tools/tests/test_gemini_search_tools.py`
- `plugins/gemini-tools/tests/test_gemini_search_tools_openrouter_integration.py`
- `plugins/gemini-tools/tests/test_gemini_read_file_tool.py`
- `plugins/gemini-tools/README.md`

3. Qwen package:
- `plugins/qwen-tools/src/qwen_tools/qwen_list_directory_tool.py`
- `plugins/qwen-tools/src/qwen_tools/qwen_grep_search_tool.py`
- `plugins/qwen-tools/src/qwen_tools/qwen_glob_tool.py`
- `plugins/qwen-tools/src/qwen_tools/__init__.py`
- `plugins/qwen-tools/agent_plugin.json`
- `plugins/qwen-tools/tests/test_qwen_search_tools.py`
- `plugins/qwen-tools/tests/test_qwen_search_tools_openrouter_integration.py`
- `plugins/qwen-tools/tests/test_qwen_read_file_tool.py`
- `plugins/qwen-tools/tests/test_qwen_edit_write_tools_openrouter_integration.py`
- `plugins/qwen-tools/README.md`

4. Grok package:
- `plugins/grok-tools/tests/test_grok_search_surface.py`
- `plugins/grok-tools/README.md`

5. Task tracking:
- `tasks/20260315-gemini-qwen-grok-tool-packages/030-list-grep-glob-tools.md`

### Tests run

1. Focused new-test slices:
- `pytest plugins/tool-compat-shared/tests/test_search_engine.py -q`
- `pytest plugins/gemini-tools/tests/test_gemini_search_tools.py -q`
- `pytest plugins/qwen-tools/tests/test_qwen_search_tools.py -q`
- `pytest plugins/grok-tools/tests/test_grok_search_surface.py -q`
- `pytest plugins/gemini-tools/tests/test_gemini_search_tools_openrouter_integration.py -q -m 'integration and openrouter'`
- `pytest plugins/qwen-tools/tests/test_qwen_search_tools_openrouter_integration.py -q -m 'integration and openrouter'`

2. Broader affected-package regression slices:
- `pytest plugins/tool-compat-shared/tests -q`
- `pytest plugins/gemini-tools/tests -q`
- `pytest plugins/qwen-tools/tests -q`
- `pytest plugins/grok-tools/tests -q`
- `pytest plugins/tool-compat-shared/tests -q plugins/gemini-tools/tests -q plugins/qwen-tools/tests -q plugins/grok-tools/tests -q`

### Outcomes

1. The new shared helper tests passed.
2. The new Gemini, Qwen, and Grok surface tests passed.
3. The Gemini and Qwen OpenRouter integration tests for the new search tools passed with the expected model families.
4. The full affected plugin test directories passed after updating stale manifest expectations and making two integration assertions tolerant of provider output-shape variation.

### Open issues / notes

1. Running the combined multi-plugin pytest command from the repo root produced `PytestUnknownMarkWarning` warnings for `integration` and `openrouter` markers because the mixed root invocation does not inherit each plugin package's local marker registration. The tests still passed, and the package-local pytest invocations remain clean for normal plugin development flows.
