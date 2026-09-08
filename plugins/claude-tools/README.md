# claude-tools

Claude Code-compatible tool plugin bundle for Crystal Lattice.

This package is built from AI-assisted, behavior-driven investigations of
Claude Code's publicly visible interfaces. Raw logs live under
`investigation/raw/` and are ignored; generated normalized fixtures and
implementation notes live under `investigation/fixtures/` and
`investigation/notes/`.

Claude Tools is an independent compatibility implementation. It is not
affiliated with, sponsored by, or endorsed by Anthropic.

## Implemented Tools

- `Read`: Claude Code-compatible file reader with Anthropic-native schemas and tool-result payloads.
- `Write`: Claude Code-compatible file writer with Anthropic-native schemas, parent-directory creation, and the observed read-before-write guard for existing files.
- `Edit`: Claude Code-compatible exact string editor with Anthropic-native schemas, read-before-edit guard behavior, and replace-all support.
- `Glob`: Claude Code-compatible file matcher with Anthropic-native schemas, relative-vs-absolute output parity, and truncation handling.
- `Grep`: Claude Code-compatible regex search tool with Anthropic-native schemas and mode-specific result formatting.
- `Bash`: Claude Code-compatible shell execution tool with Anthropic-native schemas, timeout handling, and background command support.
- `TaskStop`: Claude Code-compatible background-task stop tool for terminating running Bash tasks by task ID.
- `WebFetch`: Claude Code-compatible URL fetch tool with Anthropic-native schemas, prompt-based page analysis, redirect handling, and timeout behavior.
- `WebSearch`: Claude Code-compatible web search tool with Anthropic-native schemas and Claude-shaped result formatting backed by Gemini or Tavily providers.
- `ClaudeMCPTool`: Claude Code-compatible MCP tool wrapper that exposes discovered MCP server tools with Claude's `mcp__server__tool` naming and Anthropic-native result formatting.

`WebSearch` contributes an ordinary session checkbox and a compact composer
toggle. The toggle remains visible but muted/disabled when neither Gemini nor
Tavily credentials are configured.

## Implemented Session Actions

- `Compact conversation`: Claude Code-compatible compaction session action that captures the observed Claude `/compact` prompt contract, validates the Claude-style numbered summary output, and rewrites session history into the investigated compact-summary shape.

`Read` currently supports text files, images, PDF status/page rendering through Poppler, simple Jupyter notebooks, and observed Claude Code error formatting. OpenAI Chat Completions-compatible providers consume the Anthropic-native result through a narrow temporary bridge until first-class tool-result interop lands.

`Write` currently supports new-file creation, full overwrites after a prior `Read`, and the observed Claude error payload when attempting to overwrite an unread existing file.

`Edit` currently supports exact single replacements, `replace_all`, and the observed Claude error payloads for missing prior reads, missing match strings, and ambiguous multiple matches.

`Glob` currently supports default-directory relative results, scoped absolute-path results, the observed no-match string, and the Claude truncation suffix for large result sets.

`Grep` currently supports default `files_with_matches`, `content`, and `count` output modes, along with the observed no-match string and missing-path error wrapper.

`Bash` currently supports foreground execution, raw-success vs `Exit code N` failure formatting, the observed timeout behavior, and the Claude background-run message format.

`TaskStop` currently supports stopping running background Bash tasks by the background ID returned from `Bash`. `Read` remains the primary Claude-shaped way to inspect Bash background output via the returned output path.

`WebFetch` currently supports public HTTP(S) fetches, `http` to `https` upgrade, the observed cross-host redirect message shape, and Claude-compatible invalid-URL and timeout strings for the investigated cases.

`WebSearch` currently supports the Claude `WebSearch` schema and Claude-shaped text results while letting the app choose either `gemini_api` or `tavily` as the backend provider through config.

`ClaudeMCPTool` currently supports stdio/SSE/HTTP MCP servers through the shared `mcp-shared` runtime package. It keeps runtime lifecycle, discovery, and raw tool calls in `mcp-shared`, while this package owns the Claude-facing schema and result shape observed in `investigation/fixtures/mcp/`. Successful text MCP results are returned as Claude-style Anthropic `tool_result` blocks containing a JSON string such as `{"content":"..."}`; MCP errors are returned with `is_error: true`. Large successful MCP outputs follow Claude Code's observed `<persisted-output>` shape with a first-2KB preview and the full JSON output saved under `.crystal/mcp-tool-results/` by default; large MCP errors are truncated with a Claude-style middle marker.

Claude MCP configuration keys:

- `mcp_enabled`: global toggle for MCP-backed tools
- `mcp_reuse_runtime`: reuse live MCP runtime connections across requests
- `mcp_fail_on_startup_error`: fail preparation when an enabled MCP server cannot start
- `mcp_servers`: MCP server definitions keyed by server name

`Compact conversation` currently supports the observed Claude `/compact` behavior investigated under `investigation/fixtures/compaction/`, including the appended compaction prompt, Claude-style numbered summary validation, transcript fallback guidance, and session-history rewrite through the core/native rebuild path so provider-native formatting remains owned by the core pipeline. The action now supports full-history compaction, prefix compaction, arbitrary selected ranges, and a message-level "Compact messages up to here" UI action. When a conversation has a leading system message, that system message is preserved in the visible transcript and included in subrange compaction requests as request context.

Claude compaction configuration keys:

- `compaction_model`: optional model id dedicated to compaction; leave empty to use the normal `model`
- `claude_compaction_prompt`: optional full prompt override for the captured Claude-style compaction prompt
- `claude_compaction_settings_overrides`: optional advanced request overrides applied only to the internal compaction request

## License

Claude Tools, including its independently authored implementation and its
AI-generated normalized compatibility fixtures, is licensed under the Apache
License, Version 2.0. See [LICENSE](LICENSE).

See [PROVENANCE.md](PROVENANCE.md) for how the compatibility assets were
produced and for the non-affiliation and trademark notice.
