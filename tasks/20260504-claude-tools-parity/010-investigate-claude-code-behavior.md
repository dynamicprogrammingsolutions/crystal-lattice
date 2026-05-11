# Investigate Claude Code Behavior

Build and run deterministic Claude Code proxy investigations for all standard tools and the system message so implementation can be based on observed behavior rather than guesses.

## Requirements checklist

- [x] Create a repeatable harness that launches `../openai-proxy`, runs Claude Code through Ollama's Anthropic-compatible API, captures stdout/stderr/debug/proxy logs, and normalizes volatile fields.
- [ ] Capture schemas for `Read`, `Write`, `Edit`, `Bash`, `Glob`, `Grep`, `WebFetch`, and `WebSearch`.
- [ ] Capture result formatting for success and important error/truncation cases for each standard tool.
- [x] Capture Claude Code system-message request bodies with no tools and with relevant tool subsets enabled.
- [x] Store normalized fixtures or investigation artifacts in a repo location suitable for tests or future reference.

Parent Task: tasks/20260504-claude-tools-parity/000-main.md

## Existing Research

Claude Code is installed at `/Users/ferenci84/.local/bin/claude` and was updated to `2.1.126`.

Known working proxy setup:

```bash
cd ../openai-proxy
node proxy.js http://localhost:11434/v1 9018
```

Known working Claude invocation shape:

```bash
cd /Users/ferenci84/Dev/Mine/ai-agent-platform

ANTHROPIC_BASE_URL=http://localhost:9018/api \
ANTHROPIC_API_KEY=ollama \
ANTHROPIC_AUTH_TOKEN=ollama \
ANTHROPIC_SMALL_FAST_MODEL=qwen3-coder-next:cloud \
ANTHROPIC_DEFAULT_HAIKU_MODEL=qwen3-coder-next:cloud \
claude -p \
  --verbose \
  --setting-sources project \
  --settings '{"env":{"ANTHROPIC_BASE_URL":"http://localhost:9018/api","ANTHROPIC_API_KEY":"ollama","ANTHROPIC_AUTH_TOKEN":"ollama","ANTHROPIC_SMALL_FAST_MODEL":"qwen3-coder-next:cloud","ANTHROPIC_DEFAULT_HAIKU_MODEL":"qwen3-coder-next:cloud"}}' \
  --no-session-persistence \
  --model qwen3-coder-next:cloud \
  --tools Read \
  --permission-mode bypassPermissions \
  --output-format stream-json \
  'Use the Read tool to read README.md. Then answer with exactly the first Markdown heading from that file and nothing else.'
```

This command produced an actual `Read` tool call and final answer. The proxy captured:

```text
GET  /api/v1/models?limit=1000
POST /api/v1/messages?beta=true
POST /api/v1/messages?beta=true
POST /api/v1/messages?beta=true
```

Key lessons:

- `--tools Read` restricts schemas sent to the model.
- `--allowedTools Read` does not restrict schemas; it only affects permissioning.
- `--setting-sources project` plus explicit `--settings` is necessary because user-level `~/.claude/settings.json` can override shell env.
- `--output-format stream-json` requires `--verbose` in Claude Code `2.1.126`.
- Pin `ANTHROPIC_SMALL_FAST_MODEL` and `ANTHROPIC_DEFAULT_HAIKU_MODEL`.

Confirmed `Read` schema and result formatting are recorded in the parent task.

## Investigation Matrix

For each tool, capture:

- Schema: name, description, full `input_schema`.
- Tool call shape emitted by the model.
- Successful result payload sent back to the model.
- Error payload for validation/path/file failures.
- Truncation/large-output behavior where applicable.

Tools:

- `Read`
- `Write`
- `Edit`
- `Bash`
- `Glob`
- `Grep`
- `WebFetch`
- `WebSearch`

Suggested focused prompts:

- `Read`: read a small text file, missing file, offset/limit range, large file.
- `Write`: create a small file in a temp workspace, overwrite behavior if allowed.
- `Edit`: exact one-match replacement, no-match replacement, multiple-match replacement.
- `Bash`: `printf`, nonzero exit, stderr, timeout/long-running command.
- `Glob`: match known files, no matches, directory/path variant.
- `Grep`: match known text, no matches, glob filters, output limits.
- `WebFetch`: local test HTTP server if possible for deterministic content.
- `WebSearch`: determine whether deterministic local testing is possible; otherwise capture schema and disabled/provider-error behavior.

Normalize:

- request ids
- session ids
- device ids
- timestamps
- absolute temp directories
- model-specific generated ids such as `call_*`

## Execution plan

Added during completion after user approval.

Start the investigation inside the future `claude-tools` plugin package rather than as generic repo scripts. The investigation artifacts are provenance for the package and should live with it.

Create the initial package/investigation layout:

```text
plugins/claude-tools/
  README.md
  pyproject.toml
  agent_plugin.json
  src/claude_tools/
    __init__.py
  investigation/
    README.md
    scripts/
      investigate_read_tool.py
      normalize_proxy_log.py
    fixtures/
      read/
    notes/
      read-tool.md
    raw/
      .gitkeep
  tests/
```

Raw logs are not committed:

```gitignore
/plugins/claude-tools/investigation/raw/*
!/plugins/claude-tools/investigation/raw/.gitkeep
```

Parsed/normalized findings are committed under `plugins/claude-tools/investigation/fixtures/read/`. Human-readable implementation guidance is committed under `plugins/claude-tools/investigation/notes/read-tool.md`.

First implementation checkpoint: `Read` only.

- [x] Create the `plugins/claude-tools` investigation skeleton.
- [x] Add a package-local raw artifact gitignore.
- [x] Implement `investigation/scripts/investigate_read_tool.py`.
- [x] Implement or embed proxy-log normalization sufficient to extract `Read` schema, assistant `tool_use`, model-facing `tool_result`, and final assistant message.
- [x] Run at least the small-file `Read` case end to end.
- [x] Save normalized parsed results under `investigation/fixtures/read/`.
- [x] Write `investigation/notes/read-tool.md` from parsed results with implementation directions.

## Progress Notes

Added during completion.

Created the initial `plugins/claude-tools` package skeleton and package-local investigation layout. Added scripts:

- `plugins/claude-tools/investigation/scripts/investigate_read_tool.py`
- `plugins/claude-tools/investigation/scripts/normalize_proxy_log.py`

Ran these `Read` cases successfully through Claude Code, Ollama, and `../openai-proxy`:

- `success-small-file`
- `success-offset-limit`
- `missing-file-error`
- `large-file-truncation`
- `empty-file`
- `directory-path-error`
- `small-image`
- `small-pdf`
- `large-pdf-requires-pages`
- `pdf-pages-range`
- `notebook-simple`

Committed normalized fixtures:

- `plugins/claude-tools/investigation/fixtures/read/success-small-file.json`
- `plugins/claude-tools/investigation/fixtures/read/success-offset-limit.json`
- `plugins/claude-tools/investigation/fixtures/read/missing-file-error.json`
- `plugins/claude-tools/investigation/fixtures/read/large-file-truncation.json`
- `plugins/claude-tools/investigation/fixtures/read/empty-file.json`
- `plugins/claude-tools/investigation/fixtures/read/directory-path-error.json`
- `plugins/claude-tools/investigation/fixtures/read/small-image.json`
- `plugins/claude-tools/investigation/fixtures/read/small-pdf.json`
- `plugins/claude-tools/investigation/fixtures/read/large-pdf-requires-pages.json`
- `plugins/claude-tools/investigation/fixtures/read/pdf-pages-range.json`
- `plugins/claude-tools/investigation/fixtures/read/notebook-simple.json`

Updated implementation directions:

- `plugins/claude-tools/investigation/notes/read-tool.md`

Verified script syntax with:

```bash
python -m py_compile plugins/claude-tools/investigation/scripts/investigate_read_tool.py plugins/claude-tools/investigation/scripts/normalize_proxy_log.py
```

Installed Poppler via Homebrew and reran PDF cases. `pdftoppm` is now available at `/opt/homebrew/bin/pdftoppm` (`pdftoppm version 26.04.0`). Homebrew reported a persistent `fontconfig` postinstall warning, but Poppler is installed and usable.

After installing Poppler:

- `pdf-pages-range` now captures a text status block plus two native JPEG image blocks. The Ollama investigation model rejects the follow-up request because it does not support image input, but the tool-result payload is captured.
- `large-pdf-requires-pages` now captures the expected "too many pages" error with `is_error: true`.
- `small-pdf` remains a status-string result.

Remaining `Read` follow-ups before implementation:

- Additional image media types if broad image parity is required.

System-message investigation added during completion:

- Added `plugins/claude-tools/investigation/scripts/investigate_system_message.py`.
- Fixed `plugins/claude-tools/investigation/scripts/normalize_proxy_log.py` long-text parsing so system prompts containing markdown `---` fences are restored correctly.
- Ran these cases successfully through Claude Code, Ollama, and `../openai-proxy`:
  - `no-tools`
  - `read-tool`
  - `read-relative-path`
  - `standard-tools`
- Committed normalized fixtures:
  - `plugins/claude-tools/investigation/fixtures/system-message/no-tools.json`
  - `plugins/claude-tools/investigation/fixtures/system-message/read-tool.json`
  - `plugins/claude-tools/investigation/fixtures/system-message/read-relative-path.json`
  - `plugins/claude-tools/investigation/fixtures/system-message/standard-tools.json`
- Updated implementation directions:
  - `plugins/claude-tools/investigation/notes/system-message.md`

Key finding: Claude Code includes `Primary working directory: <WORKSPACE>` in the main system prompt's `# Environment` section. Tool schemas such as `Read`, `Write`, and `Edit` require absolute file paths. In the `read-relative-path` case, the user asked for `README.md`, and Claude called `Read` with `<WORKSPACE>/README.md`.
