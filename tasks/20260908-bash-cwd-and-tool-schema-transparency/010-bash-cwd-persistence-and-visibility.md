# Bash CWD Persistence, Result Visibility, and CD Guidance Config

Parent Task: tasks/20260908-bash-cwd-and-tool-schema-transparency/000-main.md

Depends On: none (parallel with `020-tool-schema-transparency.md`).

Make the claude-tools Bash tool's working-directory behavior transparent and
configurable: cwd persistence can be toggled, the cwd can be surfaced in tool
results, the cd guidance in the tool description can be switched to a
permissive variant, and the claude system message uses an improved permissive
tool-usage section by default with the upstream original still selectable.

## Requirements checklist

- [ ] A `bash_cwd_persistence` agent-level config option (default `true`) controls whether the Bash tool resolves its working directory from the previous Bash result's stored `end_cwd`; when `false`, every foreground command starts in the configured working directory and no `bash.end_cwd` metadata is emitted.
- [ ] The Bash tool description shown to the model matches `bash_cwd_persistence`: when `false` it states the working directory does not persist between commands and advises chaining `cd dir && cmd` in a single Bash call.
- [ ] A `bash_include_cwd_in_result` agent-level config option (default `false`), when `true`, adds an initial cwd line at the beginning of Bash tool result content, and adds an end cwd line at the end only when the cwd changed during the command and cwd persistence is enabled.
- [ ] A `bash_permissive_cd_guidance` agent-level config option (default `false`), when `true`, replaces the upstream restrictive cd guidance in the Bash tool description with permissive guidance; with all options at their defaults and persistence on, the tool description is verbatim upstream.
- [ ] The default config's claude system message template (kept inlined in `config.json`) references the improved permissive-cd tool-usage variable; the original upstream tool-usage file remains available by switching the template variable, and both variables are defined in the default config.
- [ ] The improved tool-usage system message content selects its persistence sentence based on `bash_cwd_persistence` (persisting → "cd alone is sufficient"; not persisting → "chain `cd dir && cmd`").
- [ ] Tests cover: persistence on/off behavior and metadata, cwd-in-result formatting (success, failure, no-output, changed-cwd end note), tool description variants for the option combinations, system message helper variant selection, and default-config wiring (template references the improved variable; both variables defined).

## Requirement questions and decisions

Resolved with the user during planning:

1. Tool description default is upstream parity; the permissive cd guidance in
   the tool description is opt-in via a boolean.
2. Cwd-in-result format: the initial cwd appears at the beginning of the
   result; the changed end cwd is noted at the end only when it persisted.
3. When `bash_cwd_persistence` is `false`, no `bash.end_cwd` metadata is
   emitted.
4. No new mixin: the improved system message version is used directly in the
   default config via a template variable; the template stays inlined in
   `config.json` so the selection is apparent.

## Supporting details

### Root causes (facts from the session analysis)

- The Bash tool description (`BASH_DESCRIPTION`) carries the upstream
  restrictive cd guidance ("Try to maintain your current working directory
  throughout the session by using absolute paths and avoiding usage of `cd`.
  You may use `cd` if the User explicitly requests it."), which suppresses
  `cd` in emitted tool calls even when reasoning correctly identifies it.
- `bash.end_cwd` metadata lives in `_metadata`, which is internal and not sent
  to the model; the model has no way to see the current cwd or verify
  persistence.
- The persistence mechanism itself works: `end_cwd` is stored relative to the
  configured working directory and resolved on the next foreground call
  (implemented in commit 3060b462).
- The system message cd guidance lives in
  `plugins/claude-tools/system_messages/claude/tool-usage.md` ("For `Bash`,
  prefer absolute paths and avoid unnecessary `cd`.") — permissive wording but
  weaker than the tool description's restriction.

### Key files

- `plugins/claude-tools/src/claude_tools/claude_bash_tool.py`
  - `BASH_DESCRIPTION` (lines ~44–217): upstream text; persistence claim at
    line ~46, cd guidance sentence at line ~58.
  - `BASH_SCHEMA` (~219): static schema; `get_tool_schemas` returns it as-is.
  - `init` (~439): reads `working_directory`, `shell_timeout_ms`, etc. from
    the tool init config.
  - `execute_tool` (~539): resolves the workdir via
    `_last_bash_end_cwd_from_context` and emits `metadata.bash.end_cwd`.
  - `_format_success_output` / `_format_failure_output`: "(Bash completed with
    no output)" placeholder and "Exit code N" prefix.
- `plugins/claude-tools/system_messages/claude/tool-usage.md`
  - Original upstream tool-usage section; the cd line is the last bullet.
- `application/python/agent_terminal_app/default_config/config.json`
  - `claude_system_message` mixin: inlined template references
    `{{TOOL_USAGE}}`; the `TOOL_USAGE` variable is file-based.
  - The mixin is shared by the `claude`, `glm-ollama`, and `deepseek-ollama`
    agents — the template change applies to all of them.
- `application/python/agent_terminal_app/default_config/system_messages/helpers/claude_runtime.py`
  - Runtime globals (`CONFIG`, `cwd`, `shell`, `is_git_repo`) for system
    message helpers; `CONFIG` is provided by the rendering context.
- Config flow (fact): `AgentCore._build_tool_init_config`
  (`core/python/agent_core/core.py` ~4133) starts from the request config
  dict, so agent-level keys reach the tool's `init` config (the same path
  `working_directory` takes today).

## Execution plan

Status: Approved

### Approach

Three agent-level config booleans on the Bash tool plus a system message
variable switch. Defaults preserve upstream parity for the tool description
and current persistence behavior; every deviation is opt-in except the
system message, which uses the improved tool-usage section by default in the
default config (upstream original still selectable via the inlined template).

### 1. System message files and helper

Create `plugins/claude-tools/system_messages/claude/tool-usage-permissive-cd.md`
(persistence=true variant) — identical to `tool-usage.md` except the last
bullet:

> For `Bash`, prefer absolute paths. You may use `cd` when a command must run
> from a specific directory (e.g. `mkdocs build`, `npm install`,
> `cargo build`). The working directory persists between commands, so `cd`
> alone is sufficient; you don't need to chain `cd dir && cmd` for one-off
> directory changes.

Create `tool-usage-permissive-cd-no-persistence.md` — same, but the last
sentence reads:

> The working directory does not persist between commands; chain
> `cd dir && cmd` in a single Bash call when you need to run from a specific
> directory.

Create
`application/python/agent_terminal_app/default_config/system_messages/helpers/render_claude_tool_usage.py`:
reads `CONFIG.get("bash_cwd_persistence", True)`, loads the matching variant
file from `${BUILTIN_PLUGINS}/claude-tools/system_messages/claude/` (resolve
via `os.environ`, the same env the config loader uses), sets
`SYSTEM_MESSAGE_VALUE`.

### 2. Default config wiring

In `config.json`, `claude_system_message.system_message`:

- Template (stays inlined): `{{TOOL_USAGE}}` → `{{TOOL_USAGE_PERMISSIVE_CD}}`.
- Variables: keep `TOOL_USAGE` (file-based original); add
  `TOOL_USAGE_PERMISSIVE_CD` with `code` pointing at the helper and
  `runtime_code` pointing at `claude_runtime.py`.

Switching back to upstream wording is a one-token template edit
(`{{TOOL_USAGE_PERMISSIVE_CD}}` → `{{TOOL_USAGE}}`).

### 3. Bash tool config options

In `claude_bash_tool.py`, `init` reads into state:

- `"cwd_persistence": bool(config.get("bash_cwd_persistence", True))`
- `"include_cwd_in_result": bool(config.get("bash_include_cwd_in_result", False))`
- `"permissive_cd_guidance": bool(config.get("bash_permissive_cd_guidance", False))`

### 4. Bash tool behavior

`execute_tool`:

- When `cwd_persistence` is `false`: skip the
  `_last_bash_end_cwd_from_context` chain resolution, always resolve from the
  configured working directory, and do not emit `bash.end_cwd` metadata.
- When `true` (default): current behavior unchanged.

### 5. Cwd lines in tool result content

When `include_cwd_in_result` is `true`:

- First line of the result content: `[cwd: <resolved start cwd>]` — always.
- Last line: `[cwd: <end cwd>]` — only when the end cwd differs from the start
  cwd and `cwd_persistence` is `true`.
- Applies to foreground success (including the "(Bash completed with no
  output)" placeholder), failure, and background results. The existing
  "Exit code N" / placeholder formats are preserved inside the cwd lines.

Example (command changed the cwd, persistence on):

```
[cwd: /Users/me/repo]
<command output>
[cwd: /Users/me/repo/docs_site]
```

### 6. Tool description variants

`get_tool_schemas(state)` builds the description by exact-string replacement
of two segments in the base `BASH_DESCRIPTION` constant (the constant stays
untouched as the upstream reference):

| `bash_cwd_persistence` | `bash_permissive_cd_guidance` | Opening claim | cd guidance sentence |
|---|---|---|---|
| `true` (default) | `false` (default) | upstream verbatim | upstream verbatim |
| `true` | `true` | upstream verbatim | permissive: "You may use `cd` when a command must run from a specific directory. The working directory persists between commands, so `cd` alone is sufficient; you don't need to chain `cd dir && cmd` for one-off directory changes." (keep the existing git `cd`-prepend warning) |
| `false` | `false` | "The working directory does not persist between commands; each command starts in the configured working directory. Shell state does not persist either." | upstream restrictive sentence + appended note: "When you do use `cd`, chain it with the command in a single Bash call (`cd dir && cmd`) because the working directory does not persist between commands." |
| `false` | `true` | same no-persist opening | permissive with chaining: "... The working directory does not persist between commands, so chain `cd dir && cmd` in a single Bash call when you need to run from a specific directory." |

With all defaults and persistence on, the description is byte-identical to
upstream.

### Implementation decisions and open questions

User-approved decisions: upstream-parity default for the tool description;
cwd format (initial at beginning, changed end noted only when persisted); no
`end_cwd` metadata when persistence is off; improved system message default
via the inlined template variable; no mixin.

Local decisions (reversible, resolved): boolean names
`bash_cwd_persistence` / `bash_include_cwd_in_result` /
`bash_permissive_cd_guidance`; `[cwd: ...]` line syntax; the chaining note
appended to restrictive guidance when persistence is off; the helper-based
variable for the persistence-aware system message; exact-string replacement
for description variants.

Open questions: none blocking.

### Documentation

Document the three config options and the system message template-variable
switch in the claude-tools plugin user docs (check `plugins/docs/` and
plugin-local docs for the owning location).

### Task checklist

- [ ] Create `tool-usage-permissive-cd.md` and `tool-usage-permissive-cd-no-persistence.md`
- [ ] Create `render_claude_tool_usage.py` helper
- [ ] Update default config: template references the improved variable; both variables defined
- [ ] Bash tool: read the three booleans in `init`
- [ ] Bash tool: persistence-off behavior (skip chain, no metadata)
- [ ] Bash tool: cwd-in-result formatting
- [ ] Bash tool: description variants in `get_tool_schemas`
- [ ] Bash tool tests (persistence, cwd lines, description variants)
- [ ] System message helper and default-config tests
- [ ] Lint (ruff, black) and typecheck (pyright) on changed files
- [ ] Docs for the new config options

### Requirement verification

- Persistence option: unit tests in `plugins/claude-tools/tests/test_claude_bash_tool.py` — persistence off runs in the configured working directory despite prior `end_cwd` in session context and emits no metadata; persistence on keeps current chain behavior (existing tests).
- Description matches persistence: `get_tool_schemas` tests assert the opening claim and cd guidance sentences for all option combinations, including byte-identical upstream output at defaults.
- Cwd lines: result-formatting tests for success, failure, no-output, and changed-cwd end note (present only when changed and persistence on).
- Permissive guidance opt-in: covered by the description-variant tests.
- System message default + switch: config test asserting the default template references `TOOL_USAGE_PERMISSIVE_CD` and both variables are defined; helper test asserting variant selection by `bash_cwd_persistence`.
- Test suite health: `pytest plugins/claude-tools/tests -q` and the relevant application tests pass with no new failures.

### Additional implementation verification

- Confirm `CONFIG` in the system message rendering context is the agent config, so the helper reads the same `bash_cwd_persistence` value the tool receives.
- Confirm `BUILTIN_PLUGINS` is available via `os.environ` during helper execution (the config loader resolves `${env:BUILTIN_PLUGINS}` from the process environment).
- Verify the shared `claude_system_message` mixin change renders correctly for the `claude`, `glm-ollama`, and `deepseek-ollama` agents.