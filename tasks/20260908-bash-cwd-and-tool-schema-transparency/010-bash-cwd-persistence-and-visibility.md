# Bash CWD Persistence, Result Visibility, and CD Guidance Config

Parent Task: tasks/20260908-bash-cwd-and-tool-schema-transparency/000-main.md

Depends On: none (parallel with `020-tool-schema-transparency.md`).

Make the claude-tools Bash tool's working-directory behavior transparent and
configurable: cwd persistence can be toggled, the cwd can be surfaced in tool
results, the cd guidance in the tool description can be switched to a
permissive variant, and the claude system message uses an improved permissive
tool-usage section by default with the upstream original still selectable.

## Requirements checklist

- [x] A `bash_cwd_persistence` agent-level config option (default `true`) controls whether the Bash tool resolves its working directory from the previous Bash result's stored `end_cwd`; when `false`, every foreground command starts in the configured working directory and no `bash.end_cwd` metadata is emitted.
- [x] The Bash tool description shown to the model matches `bash_cwd_persistence`: when `false` it states the working directory does not persist between commands and advises chaining `cd dir && cmd` in a single Bash call.
- [x] A `bash_include_cwd_in_result` agent-level config option (default `false`), when `true`, adds an initial cwd line at the beginning of Bash tool result content, and adds an end cwd line at the end only when the cwd changed during the command and cwd persistence is enabled.
- [x] A `bash_permissive_cd_guidance` agent-level config option (default `false`), when `true`, replaces the upstream restrictive cd guidance in the Bash tool description with permissive guidance; with all options at their defaults and persistence on, the tool description is verbatim upstream.
- [x] The default config's claude system message template (kept inlined in `config.json`) references the improved permissive-cd tool-usage variable; the original upstream tool-usage file remains available by switching the template variable, and both variables are defined in the default config.
- [x] The improved tool-usage system message content selects its persistence sentence based on `bash_cwd_persistence` (persisting → "cd alone is sufficient"; not persisting → "chain `cd dir && cmd`").
- [x] Tests cover: persistence on/off behavior and metadata, cwd-in-result formatting (success, failure, no-output, changed-cwd end note), tool description variants for the option combinations, system message helper variant selection, and default-config wiring (template references the improved variable; both variables defined).

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

- [x] Create `tool-usage-permissive-cd.md` and `tool-usage-permissive-cd-no-persistence.md`
- [x] Create `render_claude_tool_usage.py` helper
- [x] Update default config: template references the improved variable; both variables defined
- [x] Bash tool: read the three booleans in `init`
- [x] Bash tool: persistence-off behavior (skip chain, no metadata)
- [x] Bash tool: cwd-in-result formatting
- [x] Bash tool: description variants in `get_tool_schemas`
- [x] Bash tool tests (persistence, cwd lines, description variants)
- [x] System message helper and default-config tests
- [x] Lint (ruff, black) and typecheck (pyright) on changed files
- [x] Docs for the new config options

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
## Implementation Notes

- The description variants are built by exact-string replacement of two
  upstream segments (opening persistence claim, cd guidance sentence) in the
  base `BASH_DESCRIPTION`; `test_upstream_description_segments_present` guards
  the segment constants against upstream text drift.
- Background results include only the start `[cwd: ...]` line (the background
  command's end cwd is unknown at start time and background runs do not join
  the cwd chain).
- The failure-case test uses `sh -c "echo problem 1>&2; exit 7"` (subshell)
  because a bare `exit` inside the eval-wrapped command terminates the
  wrapping shell before the sentinel prints.
- Environment finding (pre-existing, not caused by this task): fresh plugin
  cache installs in a new worktree pull latest PyPI dependencies — mcp 2.2.0
  requires `typing_extensions.sentinel`, but the ambient pyenv
  `typing_extensions` (4.14.1) lacked it, and the plugin installer's stale
  module eviction could not swap it because `typing_extensions`' dist-info has
  no `top_level.txt`. Full-config application tests failed with
  `plugin_import_error` entries until the ambient `typing_extensions` was
  upgraded (`pip install -U typing_extensions`). The main checkout only
  worked because its warm cache still had mcp 2.0.0. This eviction gap is a
  candidate for a separate infrastructure fix.
- Running `pytest plugins/claude-tools/tests/test_claude_bash_tool.py
  application/python/tests/test_claude_system_message_helpers.py` in a single
  invocation causes a cross-suite failure (the application test's plugin
  installs mutate process sys.path/module state); the suites must be run
  separately, matching the normal per-package invocations.

## Completion Notes

- Outcome: all requirements delivered. Three agent-level config options
  (`bash_cwd_persistence` default `true`, `bash_include_cwd_in_result`
  default `false`, `bash_permissive_cd_guidance` default `false`) control the
  Bash tool's cwd chain, result cwd lines, and description cd guidance; the
  default claude system message uses the permissive-cd tool-usage variable
  (helper-selected persistence variant) with the original variable still
  selectable via the inlined template.
- Requirement evidence: 16 new tests in
  `plugins/claude-tools/tests/test_claude_bash_tool.py` (description variants
  incl. byte-identical upstream at defaults, persistence off/on, cwd lines
  for success/failure/no-output/changed-cwd, init option reading,
  `_apply_cwd_lines` unit) and 3 new tests plus extended assertions in
  `application/python/tests/test_claude_system_message_helpers.py` (helper
  variant selection, empty fallback without `BUILTIN_PLUGINS`, default-config
  wiring, full-render shows the permissive line and not the original).
- Verification performed: `pytest plugins/claude-tools/tests -q` → 139
  passed, 9 deselected; `pytest application/python/tests/test_claude_system_message_helpers.py -q`
  → 7 passed; `ruff check` and `black` clean on all changed files; `pyright`
  shows only the 3 pre-existing errors (verified identical on the clean
  state). Additional verification: `CONFIG` in the system message rendering
  context is the request config (feature `_build_base_runtime_context`);
  `BUILTIN_PLUGINS` is installed into `os.environ` by the runtime overlay
  (`agent_app/config.py` `build_runtime_overlay_env`); the shared
  `claude_system_message` mixin renders the permissive section for the
  `claude` (via the committed full-render test), `glm-ollama`, and
  `deepseek-ollama` agents (direct render check).
- Plan deviations: none.
- Unresolved/deferred: the plugin-install `typing_extensions` eviction gap
  (dist-info without `top_level.txt` prevents swapping a stale ambient
  module) is a pre-existing infrastructure issue worth a separate task.

## Post-completion follow-up

Independent review found a merge blocker: the permissive tool-usage Markdown
variants were referenced only through dynamically constructed filenames inside
the `render_claude_tool_usage.py` helper, while plugin packaging discovers
resources only from literal paths in the resolved config. Bundled binary/cloud
layouts therefore omitted both variant files and the helper silently rendered
an empty "Using your tools" section.

Correction (user-directed): drop the helper-based selection entirely. All
tool-usage variants are now plain `files` variables in the default config —
`TOOL_USAGE` (upstream), `TOOL_USAGE_PERMISSIVE_CD` (default, for
`bash_cwd_persistence: true`), and `TOOL_USAGE_PERMISSIVE_CD_NO_PERSISTENCE`
(for `bash_cwd_persistence: false`) — and the user selects the variant by
editing the inlined template variable. The README documents which variable
matches which Bash setting. Literal config paths make the files
packaging-discoverable, so no packaging-support changes were needed; the
deleted helper removes the silent-empty failure mode.

Verification: new bundled-layout regression test
`test_cloud_runtime_plugin_bundle_stages_claude_tool_usage_variants` in
`application/python/tests/test_cloud_runtime_plugin_bundle_builder.py`
asserts all three variant files are staged into the preinstalled plugin layout
and listed in the manifest `resource_paths`; confirmed it fails against the
old code-variable config and passes with the files variables.
`pytest application/python/tests/test_claude_system_message_helpers.py -q` →
5 passed; `pytest application/python/tests/test_cloud_runtime_plugin_bundle_builder.py -q`
→ 11 passed; `pytest plugins/claude-tools/tests -q` → 139 passed, 9
deselected; ruff and black clean.

Follow-up addition (user-directed): added four coherent preset mixins to the
default config's `mixins` section — `claude_bash_upstream_parity`,
`claude_bash_permissive`, `claude_bash_permissive_visible`, and
`claude_bash_permissive_no_persistence` — each chaining `claude_system_message`
via `mixin_refs` with `"$merge": "deep"` so the preset overrides the three
Bash config keys plus the `system_message.template` tool-usage variable while
the base variables survive (shallow merge would wipe them, verified). The
shipped default agents keep `claude_system_message`; presets are opt-in via an
agent's `mixin_refs`, and agent-local keys still win over preset values
(verified). README now documents the exact working combinations as a table
with concise `mixin_refs` and local-override examples. Verification: two new
tests in `application/python/tests/test_claude_system_message_helpers.py`
(preset resolution for all four presets through `resolve_config_mixins` +
`build_agent_config`, and an end-to-end `AgentApplication` render with
`claude_bash_permissive_no_persistence` applied to `glm-ollama`); suite passes
(7 tests), cloud bundle builder suite still passes (11 tests).

Follow-up refinement (user-directed): the presets are now pure delta mixins
(no internal `mixin_refs` to `claude_system_message`, no root `$merge`), and
the configured claude agents (`claude-openrouter`, `claude-anthropic`,
`glm-ollama`, `deepseek-ollama`) list `claude_system_message` followed by
`claude_bash_permissive` in `mixin_refs`, so the default combination is
coherent permissive guidance in both the Bash tool description and the system
message (supersedes the earlier upstream-parity tool-description default).
Each agent declares a per-key merge policy
`"$merge": {"default": "shallow", "deep": ["system_message"]}` instead of a
broad `"deep"`: `$merge` is parent-scoped, so the directive governing the
`system_message` collision between the base mixin and the preset must live on
the agent; an inner `$merge` inside the preset's `system_message` and a root
`$merge` on the preset were both verified to lose the base variables (the
root directive is popped at reference time). The per-key policy keeps the
provider-defaults merge in `build_agent_config` shallow for every other key.
Tests updated to the delta design (probe agent uses base + preset with the
per-key policy; real-agent assertions added); suites pass: helpers 7,
effective-configs + docs + cloud bundle builder 22, claude-tools 139.
