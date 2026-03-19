# 090 - Kimi Core File Tools

Short description: Create the `kimi-tools` plugin package and implement Kimi CLI-compatible reader, writer, editor, glob, and grep tools, reusing the shared internal package from `tool-compat-shared` while matching Kimi's PascalCase tool names, unique multi-edit semantics, line-numbered output, and vendor-specific response formatting.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On:
- `tasks/20260315-gemini-qwen-grok-tool-packages/010-reader-tools.md`
- `tasks/20260315-gemini-qwen-grok-tool-packages/020-edit-and-write-tools.md`
- `tasks/20260315-gemini-qwen-grok-tool-packages/030-list-grep-glob-tools.md`

## Goal

Introduce a fourth vendor plugin package `plugins/kimi-tools/` and deliver Kimi CLI-compatible file tools (reader, writer, editor, glob, grep) with schema-faithful parameter names, validation wording, content limits, and response formatting.

This subtask also extends `tool-compat-shared` with Kimi-specific shared helpers (multi-edit support, append mode, line-numbered output, `**`-prefix blocking, multi-mode grep) that are not needed by the earlier vendor packages but will be available for reuse.

## Why Kimi warrants its own subtask

Kimi CLI (`MoonshotAI/kimi-cli`) differs structurally from Gemini/Qwen/Grok in ways that make this more than a copy of an existing package:

1. **Python-native source** — tools are already Python with Pydantic models, making them the most directly portable of all four vendors. Schema docs live in `.md` files with Jinja2 template variables.
2. **PascalCase tool names** — `ReadFile`, `WriteFile`, `StrReplaceFile`, `Glob`, `Grep` (not snake_case like the other vendors).
3. **Line-numbered output** — `ReadFile` returns content with `cat -n`-style line numbers (`"    42\tline content"`). No other vendor does this.
4. **Append mode** — `WriteFile` supports `mode: "overwrite" | "append"`. Gemini/Qwen/Grok have overwrite only.
5. **Multi-edit support** — `StrReplaceFile` accepts `edit: Edit | list[Edit]` where `Edit = {old, new, replace_all}`, allowing multiple replacements in one call.
6. **`**`-pattern blocking** — `Glob` actively rejects patterns starting with `**` with a safety error message.
7. **Multi-mode grep** — `Grep` has three output modes (`content`, `files_with_matches`, `count_matches`) plus ripgrep-style flags (`-B`, `-A`, `-C`, `-n`, `-i`, `type`, `multiline`).
8. **Different content limits** — 1000 lines, 2000 chars/line, 100KB total output (vs Gemini's 2000 lines, 2000 chars/line, 20MB file cap).

## Public package outcome

1. `plugins/kimi-tools/`
- `KimiReadFileTool` (tool name: `ReadFile`)
- `KimiWriteFileTool` (tool name: `WriteFile`)
- `KimiStrReplaceFileTool` (tool name: `StrReplaceFile`)
- `KimiGlobTool` (tool name: `Glob`)
- `KimiGrepTool` (tool name: `Grep`)

## Key source references

All paths are relative to the locally cloned Kimi CLI repo at `../kimi-cli`, commit `7ba9695`.

### Tool registration

- Default agent spec (tool list):
  - `src/kimi_cli/agents/default/agent.yaml`
- Tool protocol and execution:
  - `src/kimi_cli/soul/toolset.py` (`CallableTool2`, `KimiToolset`)
- Tool base class and key-argument extraction:
  - `src/kimi_cli/tools/__init__.py`

### Individual tools

- ReadFile:
  - Implementation: `src/kimi_cli/tools/file/read.py`
  - Description template: `src/kimi_cli/tools/file/read.md`
- WriteFile:
  - Implementation: `src/kimi_cli/tools/file/write.py`
  - Description template: `src/kimi_cli/tools/file/write.md`
- StrReplaceFile:
  - Implementation: `src/kimi_cli/tools/file/replace.py`
  - Description template: `src/kimi_cli/tools/file/replace.md`
- Glob:
  - Implementation: `src/kimi_cli/tools/file/glob.py`
  - Description template: `src/kimi_cli/tools/file/glob.md`
- Grep:
  - Implementation: `src/kimi_cli/tools/file/grep_local.py`
  - Description template: `src/kimi_cli/tools/file/grep.md`

### Shared utilities

- `ToolResultBuilder` (char-limited buffered output with truncation tracking):
  - `src/kimi_cli/tools/utils.py`
- `truncate_line` (per-line truncation with configurable marker):
  - `src/kimi_cli/tools/utils.py`
- File type detection and media sniffing:
  - `src/kimi_cli/tools/file/utils.py`
- Path validation helpers:
  - `src/kimi_cli/tools/file/utils.py`, `src/kimi_cli/utils/path.py`

## Compatibility findings

### Tool names and parameter names must be PascalCase

Kimi uses PascalCase for tool names (e.g. `ReadFile`, not `read_file`) and snake_case for parameters (e.g. `line_offset`, not `lineOffset`). This is different from all three existing vendor packages.

### ReadFile: line-numbered output

Kimi's ReadFile formats output with 6-digit right-aligned line numbers and a tab separator:

```
     1	first line
     2	second line
    42	some line
```

This is a structurally different output format from Gemini/Qwen/Grok (which return raw content). The shared `reader_engine.py` should gain a line-number formatting option.

### WriteFile: overwrite + append

Kimi's WriteFile has a `mode` parameter:
- `"overwrite"` (default) — replaces entire file content.
- `"append"` — appends content to the end of an existing file.

No other vendor package supports append mode. The shared `editor_engine.py` should add append-mode support.

### StrReplaceFile: multi-edit with struct-based edit objects

Kimi's StrReplaceFile accepts a single `Edit` or a list of `Edit` objects:

```python
class Edit(BaseModel):
    old: str = Field(description="The old string to replace. Can be multi-line.")
    new: str = Field(description="The new string to replace with. Can be multi-line.")
    replace_all: bool = Field(description="Whether to replace all occurrences.", default=False)

class Params(BaseModel):
    path: str = ...
    edit: Edit | list[Edit] = ...
```

This is structurally different from Gemini's `old_string`/`new_string`/`allow_multiple` and Qwen's `old_string`/`new_string`/`replace_all` (single edit only). The shared `editor_engine.py` should add multi-edit support.

Replacement is simple `str.replace()` — no fuzzy/multi-strategy like Gemini's exact → flexible → regex → fuzzy pipeline.

### Glob: `**` prefix blocking

Kimi's Glob actively rejects patterns starting with `**`:

```
Pattern `**/*.py` starts with '**' which is not allowed.
This would recursively search all directories and may include large
directories like `node_modules`. Use more specific patterns instead.
For your convenience, a list of all files and directories in the
top level of the working directory is provided below.
```

No other vendor does this. The shared glob helpers should support this validation as a vendor-specific option.

### Grep: three output modes with ripgrep-style flags

Kimi's Grep supports three `output_mode` values:
- `"content"` — show matching lines (supports `-B`, `-A`, `-C`, `-n`, `head_limit`).
- `"files_with_matches"` — show file paths only (supports `head_limit`).
- `"count_matches"` — show total match counts.

Additional parameters:
- `-B`, `-A`, `-C` (context lines, aliased as such in the Pydantic model).
- `-n` (show line numbers).
- `-i` (case insensitive).
- `type` (rg file type like `py`, `rust`, `js`).
- `head_limit` (limit output to first N lines).
- `multiline` (enable multiline dotall mode).

The grep backend is ripgrep only — no Python fallback. The binary is auto-downloaded from `cdn.kimi.com` if not found locally.

### Content limits and truncation

| Limit | Value |
|-------|-------|
| Max lines per read | 1000 |
| Max chars per line | 2000 |
| Max bytes per read | 100KB (100 << 10) |
| Per-line truncation marker | `"..."` |
| Glob max matches | 1000 |

Truncation message format (ReadFile):
- `"N lines read from file starting from line X."`
- Appended: `" Max 1000 lines reached."` or `" Max 102400 bytes reached."` or `" End of file reached."`
- Truncated line numbers listed: `"Lines [42, 89] were truncated."`

### Result structure

Kimi uses a different result shape from Gemini/Qwen/Grok:

```python
ToolReturnValue(
    is_error=False,
    output="...",        # main content
    message="...",       # status/explanation
    display=[...],       # optional display blocks for UI
    extras={...},        # optional metadata
)
```

The tool plugin should produce this structure from shared helpers.

## Response formatting requirement

Every tool must match Kimi CLI's LLM-visible output as closely as practical. This includes:

1. **Truncation banners** — `"N lines read from file starting from line X."` + limit/end messages. Exact wording must be verified against upstream source during implementation and captured in snapshot tests.
2. **Line numbering** — `cat -n` format with 6-digit width + tab. Verified against `read.py:98`.
3. **Per-line truncation markers** — `"..."` suffix via `truncate_line`.
4. **Content/character/byte limits** — 1000 lines, 2000 chars/line, 100KB total. Each must be enforced and reflected in truncation messages.
5. **Success/error message wording** — Exact messages from upstream (e.g. `"File successfully edited. Applied 1 edit(s) with 1 total replacement(s)."`, `"No replacements were made. The old string was not found in the file."`).
6. **Result metadata structure** — `{is_error, output, message}` at minimum, with `display` and `extras` where applicable.
7. **Glob safety messages** — `**`-prefix rejection wording including the top-level directory listing.
8. **Grep output formatting** — Different formats per `output_mode`, with `head_limit` truncation messages.

Implementation pattern: shared helpers produce vendor-neutral intermediate dicts; Kimi wrapper applies Kimi-specific formatting via `format_kimi_*_result()` functions. Formatting functions should be tested with snapshot assertions for stable strings and structural assertions for dynamic values.

## Proposed shared package extensions in `tool-compat-shared`

1. **Multi-edit support in `editor_engine.py`**:
   - Struct-based `Edit` list pattern (`old`, `new`, `replace_all`).
   - `replace_multi_edits(content, edits) -> (new_content, replacements_count)`.

2. **Append mode in `editor_engine.py`**:
   - Extend `write_text_file` or add `append_text_file` with mode parameter.

3. **Line-number formatting in `reader_engine.py`**:
   - `format_with_line_numbers(lines, start_line=1) -> str` producing `cat -n` style output.

4. **`**`-prefix validation in `search_engine.py`**:
   - `validate_glob_pattern(pattern, workspace_dir) -> ToolError | None`.
   - When blocked, include a top-level directory listing in the error output.

5. **Multi-mode grep formatting in `search_engine.py`**:
   - `format_kimi_grep_result(outcome, output_mode) -> dict`.
   - Handle `content`, `files_with_matches`, `count_matches` modes.
   - Ripgrep flag mapping helpers (`-B`/`-A`/`-C`/`-n`/`-i`/`type`/`multiline` → rg CLI args).

6. **Kimi-style truncation message builder in `reader_engine.py`**:
   - `build_kimi_truncation_message(n_lines, line_offset, max_lines, max_bytes, n_bytes, truncated_lines) -> str`.

7. **Kimi `ToolResultBuilder` pattern**:
   - Consider porting the char-limited buffered output pattern from `src/kimi_cli/tools/utils.py` as a shared helper. It tracks character count, line count, and truncation state, and is useful for any tool that produces bounded streaming output.

## Behavior requirements

### ReadFile

1. Tool name: `ReadFile`. Params: `path`, `line_offset` (1-based, default 1), `n_lines` (default 1000).
2. Relative paths resolved from working directory; absolute paths required for files outside workspace.
3. Output formatted with 6-digit right-aligned line numbers + tab separator (`cat -n` style).
4. Lines exceeding 2000 chars truncated with `"..."` suffix.
5. Max 1000 lines per read; max 100KB total output.
6. Binary and unknown file types rejected with Kimi-style error wording.
7. Image/video files rejected with referral to appropriate tools.
8. Truncation message includes line count, limit reached reason, and list of truncated line numbers.
9. Schema description loaded from Jinja2 template (`read.md`) with `${MAX_LINES}`, `${MAX_LINE_LENGTH}`, `${MAX_BYTES}` substitutions.

### WriteFile

1. Tool name: `WriteFile`. Params: `path`, `content`, `mode` (default `"overwrite"`).
2. Supports `mode: "overwrite"` (replace entire file) and `mode: "append"` (append to end).
3. Plan mode: auto-approves writes to the plan file (out of scope for plugin; document limitation).
4. Parent directory must exist.
5. Diff blocks computed for display metadata.
6. Success message: `"File successfully overwritten. Current size: N bytes."` or `"File successfully appended to. Current size: N bytes."`.

### StrReplaceFile

1. Tool name: `StrReplaceFile`. Params: `path`, `edit: Edit | list[Edit]`.
2. `Edit` struct: `{old: str, new: str, replace_all: bool = False}`.
3. Single `str.replace()` replacement (no fuzzy/multi-strategy).
4. Multi-edit: applies edits sequentially to content.
5. Zero matches: returns Kimi error `"No replacements were made. The old string was not found in the file."`.
6. Success message includes edit count and total replacement count.

### Glob

1. Tool name: `Glob`. Params: `pattern`, `directory` (optional, must be absolute), `include_dirs` (default True).
2. Patterns starting with `**` are rejected with safety error and top-level directory listing.
3. Max 1000 matches; exceeded matches truncated with message.
4. Results sorted alphabetically (not by modification time like Gemini).
5. Directory param validated to be within workspace.

### Grep

1. Tool name: `Grep`. Params: `pattern`, `path` (default `"."`), `glob`, `output_mode`, `-B`, `-A`, `-C`, `-n`, `-i`, `type`, `head_limit`, `multiline`.
2. Backend: ripgrep only (no Python fallback). Binary auto-downloaded or found from system PATH.
3. Three output modes with different result formatting.
4. `head_limit` truncation message: `"Results truncated to first N lines"`.
5. `-B`, `-A`, `-C`, `-n`, `-i` parameters use short flag aliases in Pydantic model.

## Test plan

### Schema tests

1. Assert exact PascalCase tool names: `ReadFile`, `WriteFile`, `StrReplaceFile`, `Glob`, `Grep`.
2. Assert exact parameter names and types per vendor.
3. Assert required fields and defaults.
4. Assert important description text or stable snapshots.

### ReadFile behavior tests

1. Missing file → error with Kimi wording.
2. Path is directory → error.
3. File too large (>100KB) → truncation with max-bytes message.
4. Binary file → error with Kimi wording.
5. Image/video → error with referral message.
6. Line slicing via `line_offset` + `n_lines`.
7. Line-numbered output format (6-digit width + tab).
8. Per-line truncation at 2000 chars with `"..."` marker.
9. Max 1000 lines reached → truncation message.
10. Truncated line numbers listed in message.

### WriteFile behavior tests

1. Create new file (overwrite mode).
2. Overwrite existing file.
3. Append to existing file.
4. Missing parent directory → error.
5. Invalid mode value → error.

### StrReplaceFile behavior tests

1. Single edit, one match → success.
2. Single edit, `replace_all=True` → all occurrences replaced.
3. Multiple edits list → all applied sequentially.
4. Zero matches → Kimi error message.
5. Mixed multi-edit with some matches and some misses → partial application behavior.

### Glob behavior tests

1. Simple pattern match.
2. `**` prefix → rejection with directory listing.
3. `include_dirs=False` → directories filtered out.
4. Max 1000 matches → truncation message.
5. Alphabetical sort order.
6. Directory param outside workspace → error.

### Grep behavior tests

1. `output_mode="content"` → matching lines with context.
2. `output_mode="files_with_matches"` → file paths only.
3. `output_mode="count_matches"` → match counts.
4. `head_limit` truncation.
5. `-i` flag for case insensitive.
6. `-B`/`-A`/`-C` context lines.
7. `-n` line numbers.
8. `type` file type filter.
9. `multiline` mode.

### Integration tests

1. Plugin package loads through application plugin manager.
2. Tool call produces expected final tool message content.
3. OpenRouter integration test with cheap model.

## Deliverables

1. New package: `plugins/kimi-tools/` with README, pyproject.toml, setup.py, agent_plugin.json.
2. Shared helper extensions in `plugins/tool-compat-shared/`.
3. Vendor-specific tool classes with exact Kimi schemas.
4. Tests for schema, behavior, and integration.
5. README documentation covering exposed tools, behavior notes, and compatibility scope.

## Documentation follow-up

After implementation, expand the `plugins/kimi-tools/README.md` with:

1. Purpose/scope statement.
2. Quickstart config examples.
3. Exposed-tool list with parameter descriptions.
4. Kimi-specific behavior notes (line numbers, append mode, multi-edit, `**` blocking, grep output modes).
5. Compatibility-and-limitations section (host-UX boundary, approval flows).
6. Configuration reference for content limits and workspace restrictions.
7. Development/test commands.
