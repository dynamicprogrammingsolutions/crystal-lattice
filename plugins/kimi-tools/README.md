# kimi-tools

Kimi CLI-compatible tool plugin bundle. Provides file tools (ReadFile, WriteFile, StrReplaceFile, Glob, Grep) with schemas, parameter names, output formatting, and behavioral semantics matching MoonshotAI's `kimi-cli`.

## Exposed Tools

### ReadFile
Read text content from a file with line-numbered output (cat -n format).

- **Parameters**: `path` (required), `line_offset` (default 1), `n_lines` (default 1000)
- **Limits**: 1000 lines, 2000 chars/line, 100KB total output
- **Output**: 6-digit right-aligned line numbers with tab separator
- **Truncation**: Per-line truncation with `"..."` marker; Kimi-style truncation messages

### Shell
Execute shell commands with clean environment support.

- **Parameters**: `command` (required), `timeout` (default 60, max 300)
- **Timeout**: In seconds; default 60s, max 300s
- **Clean environment**: Removes PyInstaller/frozen-executable variables when running as frozen
- **Output format**: Raw output + success/failure message
- **No truncation**: Full output returned

### WriteFile
Write content to a file with overwrite or append mode.

- **Parameters**: `path` (required), `content` (required), `mode` (default `"overwrite"`)
- **Modes**: `"overwrite"` replaces entire file; `"append"` adds to end

### StrReplaceFile
Replace specific strings within a file. Supports single or multiple edits per call.

- **Parameters**: `path` (required), `edit` (required — single Edit or list of Edit objects)
- **Edit struct**: `{old: str, new: str, replace_all: bool}`
- **Multi-edit**: Applies edits sequentially to file content

### Glob
Find files and directories using glob patterns.

- **Parameters**: `pattern` (required), `directory` (optional), `include_dirs` (default true)
- **Safety**: Rejects patterns starting with `**` with directory listing
- **Limits**: 1000 matches maximum; alphabetical sort order

### Grep
Search for patterns in file contents using regular expressions.

- **Parameters**: `pattern` (required), `path` (default `"."`), `glob`, `output_mode`, `-B`, `-A`, `-C`, `-n`, `-i`, `type`, `head_limit`, `multiline`
- **Output modes**: `content`, `files_with_matches`, `count_matches`
- **Backend**: ripgrep (system `rg` binary) with Python fallback

## Kimi-Specific Behavior Notes

1. **PascalCase tool names**: `ReadFile`, `WriteFile`, `StrReplaceFile`, `Glob`, `Grep`, `Shell`
2. **Line-numbered output**: ReadFile returns `cat -n` style line numbers
3. **Append mode**: WriteFile supports `mode: "append"` for appending content
4. **Multi-edit**: StrReplaceFile accepts single Edit or list of Edit structs
5. **`**`-pattern blocking**: Glob rejects patterns starting with `**`
6. **Multi-mode grep**: Three output modes with ripgrep-style flags
7. **Different content limits**: 1000 lines, 2000 chars/line, 100KB total
8. **Clean environment**: Shell removes PyInstaller variables when running as frozen

## Configuration

```json
{
  "working_directory": "/path/to/project",
  "allowed_paths": ["/path/to/project"],
  "project_temp_dir": "/path/to/project/.temp"
  "shell_timeout_seconds": 60,
  "shell_max_timeout_seconds": 300,
  "shell_clean_env": true
}
```

### Config keys:

- `working_directory`: Base for relative paths
- `allowed_paths`: Allowed directories for file access
- `project_temp_dir`: Default: `<working_directory>/.temp`
- `shell_timeout_seconds`: Default timeout for shell commands (default: 60)
- `shell_max_timeout_seconds`: Maximum allowed timeout (default: 300)
- `shell_clean_env`: Use clean environment for subprocess (default: true)

## Dependencies

- `tool-compat-shared` (shared filesystem/search helpers)
- System `rg` (ripgrep) binary recommended for Grep tool performance

## Development

```bash
pip install -e ".[dev]"
pytest tests -q
```
