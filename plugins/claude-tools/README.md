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

`Bash` currently supports foreground execution, raw-success vs `Exit code N` failure formatting, the observed timeout behavior, the Claude background-run message format, and working-directory persistence between commands: each foreground command starts in the working directory where the previous foreground command ended, with the ending directory stored in the tool-result message metadata as a path relative to the configured working directory (portable across sandbox moves).
Foreground execution uses the detected native shell, including PowerShell on
Windows, while retaining exit-status and working-directory capture.

Bash working-directory configuration keys:

- `bash_cwd_persistence`: keep the working directory between Bash commands (default `true`, matching Claude Code). When `false`, every command starts in the configured working directory, no ending-directory metadata is stored, and the tool description states that the working directory does not persist and advises chaining `cd dir && cmd` in a single call.
- `bash_include_cwd_in_result`: surface the working directory in Bash tool results (default `false`). When `true`, the initial working directory appears as a `[cwd: ...]` first line, and the end working directory is noted as a last line when a command changed it and persistence is enabled.
- `bash_permissive_cd_guidance`: use permissive `cd` guidance in the Bash tool description instead of the upstream restrictive wording (default `false`). With all options at their defaults and persistence on, the tool description matches upstream Claude Code verbatim.

Working combinations (preset mixins):

The three keys must stay coherent with the system message's tool-usage section, which must state the same persistence behavior the Bash tool actually applies. The default config ships four preset mixins — pure deltas defined in its `mixins` section that set the three keys plus the matching `system_message.template` tool-usage variable:

| Preset mixin | `bash_cwd_persistence` | `bash_include_cwd_in_result` | `bash_permissive_cd_guidance` | Tool-usage variable |
|---|---|---|---|---|
| `claude_bash_upstream_parity` | `true` | `false` | `false` | `{{TOOL_USAGE}}` |
| `claude_bash_permissive` | `true` | `false` | `true` | `{{TOOL_USAGE_PERMISSIVE_CD}}` |
| `claude_bash_permissive_visible` | `true` | `true` | `true` | `{{TOOL_USAGE_PERMISSIVE_CD}}` |
| `claude_bash_permissive_no_persistence` | `false` | `false` | `true` | `{{TOOL_USAGE_PERMISSIVE_CD_NO_PERSISTENCE}}` |

Each preset carries its own per-key merge policy, so applying one needs no merge configuration on the agent — just list it right after `claude_system_message` in the agent's `mixin_refs`:

```json
"claude-anthropic": {
  "mixin_refs": [
    "claude_system_message",
    "claude_bash_permissive_visible",
    "claude_mcp_defaults",
    "claude_anthropic_model_variants"
  ]
}
```

The interpreter applies a referenced mixin's own root `$merge` to that mixin's merge action and then consumes it: the policy deep-merges only `system_message` (keeping the base mixin's variables and toggle while the preset overrides the template variable), leaves everything else shallow, and neither the root nor any nested directive persists into the agent's resolved configuration. `$merge` is parent-scoped (a mapping's `$merge` controls how its sibling keys merge), so a `$merge` nested inside the preset's `system_message` would instead govern `template` — a plain string — which is why the policy sits at the preset root naming `system_message` as a deep key. References without their own directive use the referencing node's root policy.

The shipped default config uses `claude_bash_permissive` for the Claude and Ollama-backed Claude-tools agents, and `claude_bash_permissive_visible` for the Z.ai agent so its Bash results also report the working directory. In both cases, the tool description and system message give coherent permissive `cd` guidance. Switch an agent to `claude_bash_upstream_parity` for upstream-verbatim guidance everywhere.

Agent-local keys still win over preset values, so a single tweak does not need a new mixin:

```json
"claude-anthropic": {
  "mixin_refs": ["claude_system_message", "claude_bash_permissive", "claude_mcp_defaults"],
  "bash_include_cwd_in_result": true
}
```

For custom templates, the tool-usage variants are available as `files` variables in `claude_system_message.system_message.variables`:

- `{{TOOL_USAGE}}` — the original upstream Claude Code wording with restrictive `cd` guidance.
- `{{TOOL_USAGE_PERMISSIVE_CD}}` — permissive `cd` guidance; the working directory persists between commands.
- `{{TOOL_USAGE_PERMISSIVE_CD_NO_PERSISTENCE}}` — permissive `cd` guidance; chain `cd dir && cmd` in a single Bash call.

`TaskStop` currently supports stopping running background Bash tasks by the background ID returned from `Bash`. `Read` remains the primary Claude-shaped way to inspect Bash background output via the returned output path.

`WebFetch` currently supports public HTTP(S) fetches, `http` to `https` upgrade, the observed cross-host redirect message shape, and Claude-compatible invalid-URL and timeout strings for the investigated cases.

`WebSearch` currently supports the Claude `WebSearch` schema and Claude-shaped text results while letting the app choose either `gemini_api` or `tavily` as the backend provider through config.

`ClaudeMCPTool` currently supports stdio/SSE/HTTP MCP servers through the shared `mcp-shared` runtime package. It keeps runtime lifecycle, discovery, and raw tool calls in `mcp-shared`, while this package owns the Claude-facing schema and result shape observed in `investigation/fixtures/mcp/`. Successful text MCP results are returned as Claude-style Anthropic `tool_result` blocks containing a JSON string such as `{"content":"..."}`; MCP errors are returned with `is_error: true`. Large successful MCP outputs follow Claude Code's observed `<persisted-output>` shape with a first-2KB preview and the full JSON output saved under `.crystal/mcp-tool-results/` by default; large MCP errors are truncated with a Claude-style middle marker.

Claude MCP configuration keys:

- `mcp_enabled`: global toggle for MCP-backed tools
- `mcp_reuse_runtime`: reuse live MCP runtime connections across requests
- `mcp_fail_on_startup_error`: fail preparation when an enabled MCP server cannot start
- `mcp_servers`: MCP server definitions keyed by server name

`Compact conversation` currently supports the observed Claude `/compact` behavior investigated under `investigation/fixtures/compaction/`, including the appended compaction prompt, the Claude-style numbered summary structure, transcript fallback guidance, and session-history rewrite through the core/native rebuild path so provider-native formatting remains owned by the core pipeline. The action supports full-history compaction, prefix compaction, arbitrary selected ranges, and a message-level "Compact messages up to here" UI action. When a conversation has a leading system message, that system message is preserved in the visible transcript and included in subrange compaction requests as request context.

Manual compaction runs in the background. The `claude_compaction_app` application plugin owns the user-facing session and message actions, reserves the session's application operation, and drives the synchronous `claude_compaction` feature action on a worker thread. The action returns promptly with an accepted operation envelope; progress, cancellation, and completion are delivered through session notifications with Cancel and Retry followups, mirroring the OpenAI Responses native-compaction flow. A snapshot is created before the compacted session is committed. The feature action itself remains available as a synchronous compatibility adapter.

Summary validation is structural, not exhaustive: a missing or empty `<summary>` block (or a missing assistant reply) fails the compaction, while the numbered summary sections are advisory. Models legitimately omit sections that do not apply to the conversation (for example `Errors and fixes:` when nothing failed), so missing sections are logged and recorded in the compacted message metadata instead of failing; the pre-rewrite snapshot and the notification Retry action remain the safety net for poor summaries.

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
