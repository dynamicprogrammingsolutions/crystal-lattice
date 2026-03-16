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
