# Session-settable shell_tool_mode settings plugin

Expose `shell_tool_mode` as a session-settable setting through a small,
opt-in feature plugin (outside `codex-tools`, not part of the default
plugin set), and drop model-based shell tool selection so the default is
`exec_command` + `write_stdin` for every model (upstream parity). Agents
that load the plugin get a `shell_tool_mode` selector in their session
settings (terminal `/set` and the mobile/desktop settings UI); setting it
per session writes a session override that swaps the shell tool surface on
the next request.

Parent Task: `tasks/20261008-codex-tool-parity-refresh/000-main.md`
Depends On: `tasks/20261008-codex-tool-parity-refresh/020-unified-exec-shell-tools.md`

## Requirements checklist

- [ ] A dedicated, opt-in feature plugin (separate plugin project, not
  referenced by the default config) exposes a `shell_tool_mode` setting
  with the documented options (`auto`, `shell`, `shell_command`,
  `exec_command`).
- [ ] The setting is visible and settable per session in the session
  settings (terminal `/set` and the settings UI the mobile/desktop apps
  render from the UI schema), and resettable back to the agent default.
- [ ] Setting it to `shell_command` for a session makes `shell_command`
  the active shell tool (unified exec off) from the next request in that
  session, without a restart — the per-session revert mechanism.
- [ ] Agents that do not load the plugin see no new setting and keep their
  configured behavior (inactive by default at the bundle level).
- [ ] Model-based shell tool selection is removed: `auto` (default) gives
  `exec_command` + `write_stdin` for every model; the `codex-variant` tag
  no longer drives shell selection (the feature keeps emitting it).
- [ ] Tests cover the UI element (schema, options, default), the session
  override flow through the real config path, the new model-agnostic
  selection matrix, and the resulting tool-set changes; documentation is
  updated.

## Supporting details

All mechanisms verified in code on 2026-10-10:

- **Session override write path:** `/set <key> <value>` →
  `TerminalApplication.update_override(key, value)`
  (`terminal_app.py:1209-1237`) → `session.metadata["overrides"][key]`,
  persisted and the session core reloaded.
- **Override read path:** `resolve_request_config(base, overrides)`
  (`core/python/agent_app/config.py:1138`) merges overrides over the agent
  config for every request; the shell tools' `is_enabled` receives this
  merged config, so an override changes the active tool set on the next
  request of an existing session.
- **UI element surfacing:** `core.get_ui_schema(config)` collects
  `get_ui_elements` from resolved plugins (`core.py:3098-3195`) using the
  effective config (`terminal_app.py:139-166`).
- **Option-type elements are supported everywhere needed:** terminal `/set`
  matches by value or label (`terminal.py:1318-1345`); the mobile
  session-settings modal renders `type: "select"` elements with `options`
  as a chip selector with per-key override reset (trash icon → back to the
  agent default)
  (`mobile/crystal-lattice-control-rn/src/components/ServerSettingsModal.tsx:141-175`);
  checkboxes render as switches.
- **Why no codex-tools changes are needed:** `shell_tool_mode` is already
  the single selection knob (`shell`/`shell_command`/`exec_command`
  explicit modes; `auto` model-tag routing). Exposing it as an override
  reuses the existing consumption point verbatim.
- **Placement:** a separate plugin project (proposed
  `plugins/shell-tool-settings`) keeps codex-tools free of UX preferences;
  not being referenced by the default config gives the "inactive by
  default" property — the setting only exists for agents whose config
  loads the plugin.

## Execution plan

Status: Approved

Approved 2026-10-10 with the user's decisions: the plugin is the simple
`shell_tool_mode` settings surface (no new gate key), and model-based
selection is dropped together with it — `auto` means unified exec for
every model.

### Design

**Part 1 — drop model-based selection (codex-tools):**

The three shell tools' `is_enabled` stop consulting the `codex-variant`
tag; the mode alone decides:

- `exec_command` + `write_stdin`: enabled iff `shell_tool_mode` is
  `"auto"`/missing/`"exec_command"` (the default surface for every
  model).
- `shell_command`: enabled iff `shell_tool_mode == "shell_command"`.
- `shell` (array): enabled iff `shell_tool_mode == "shell"`.

`CodexVariantFeature` stays registered and keeps emitting the
`codex-variant` tag (nothing else consumes it; kept for compatibility);
its docstring is updated to say the tag no longer drives shell selection.
`model_family.py` is left in place for the feature. Impact: legacy models
(`gpt-5`, `gpt-5-mini`, gemini, glm, …) under `auto` move from array
`shell` to unified exec — matching current upstream Codex, where every
model gets `exec_command`.

**Part 2 — the settings plugin:**

New plugin project `plugins/shell-tool-settings` containing one
FeaturePlugin (`shell_tool_settings`, `default_enabled: True` — activation
is controlled by loading the plugin project at all):

- `get_ui_elements`: one element, `type: "select"`, `key:
  "shell_tool_mode"`, `default: "auto"`, options
  `auto / shell / shell_command / exec_command` with short labels, plus a
  description ("Shell tool used by this agent/session; `auto`,
  `shell_command`, and `shell` select the unified exec, legacy
  string-command, and legacy array tools respectively").
- `init` no-op; no tags; no behavior — purely a settings surface. The
  codex-tools tools consume the key exactly as they do from agent config.

Data flow: session settings chips / `/set shell_tool_mode shell_command` →
`metadata["overrides"]["shell_tool_mode"]` → merged per request → tools'
`is_enabled` → `shell_command` replaces unified exec from the next request
on; deleting the override (reset) returns the session to the agent
default.

Compatibility: no persisted-data changes; `shell_tool_mode` values keep
their meanings; no behavior change for agents that do not load the plugin
(beyond the intended selection-default change in Part 1).

### Ordered steps

1. Rework the three shell tools' `is_enabled` to the mode-only matrix;
   update the `CodexVariantFeature` docstring.
2. Create the plugin project (module, `agent_plugin.json`, packaging) with
   the feature and its UI element.
3. Add tests: the new model-agnostic selection matrix (plugin unit +
   AgentCore-level, including legacy models now defaulting to unified
   exec); UI schema exposes the element with the expected options and
   default (and agents without the plugin do not get it); a session
   override on `shell_tool_mode` flips the resolved tool set through the
   real `resolve_request_config` path (shell_command on, exec off, and
   back after reset); terminal `/set` value/label handling.
4. Documentation: plugin README; codex-tools README selection section
   rewritten for the new matrix; task docs.
5. Verification runs.

### Implementation decisions and open questions

- **D1 — Model-based `auto` selection: resolved 2026-10-10 — drop it.**
  `auto` gives `exec_command` + `write_stdin` for every model (upstream
  parity); legacy models move off array `shell` under `auto`. Done
  together with the plugin so the new setting's semantics are stable at
  delivery.
- Resolved: plugin lives outside codex-tools and outside the default
  config; the setting key is `shell_tool_mode` itself (no new gate key, no
  precedence questions); element type `select` with the four documented
  options; `CodexVariantFeature` retained, tag kept for compatibility.

No open questions remain for this subtask.

### Documentation

- New `plugins/shell-tool-settings/README.md` — what the setting does, the
  per-session usage (`/set shell_tool_mode shell_command`, mobile chips,
  reset), and the mode semantics (linking to the codex-tools README).
- `plugins/codex-tools/README.md` — pointer from the selection section.

### Task checklist

- [x] Resolve D1; mark plan Approved.
- [x] Drop model-based selection in the shell tools' `is_enabled`.
- [x] Plugin project + feature + UI element.
- [x] Tests (selection matrix, UI schema, override flow, /set handling).
- [x] Documentation.
- [x] Verification runs.

## Implementation Notes

- 2026-10-10: executed as planned. The plugin is behavior-free — only the
  `select` UI element; the codex-tools `is_enabled` rework carries the
  selection semantics (`auto`/`exec_command` → unified exec for every
  model; `shell_command`/`shell` explicit-mode only; no tag consultation).
- The shell array hosted-API test (`test_shell_array_tool_with_standard_model`)
  now needs the explicit `shell_tool_mode: "shell"` (auto no longer enables
  the array tool); the legacy and shell_command API tests already carried
  explicit modes/force-enabling.
- Pyright: the new feature shows the same pre-existing
  `reportIncompatibleMethodOverride` errors as the sibling
  `codex_variant_feature.py` (4 errors, identical class) — codebase-wide
  pattern, not introduced by this change.

### Requirement verification

- Selection matrix: unit and AgentCore-level tests over mode × model
  (including legacy models like `gpt-5`/gemini now defaulting to unified
  exec under `auto`, and the tag no longer affecting any tool).
- UI element: unit test that `get_ui_schema` (with the plugin registered)
  exposes the `shell_tool_mode` select element with options and default
  `auto`, and that agents without the plugin do not get it.
- Session override flow: application-level test driving the real path —
  session with `metadata["overrides"]["shell_tool_mode"] = "shell_command"`
  resolves `shell_command` active and `exec_command`/`write_stdin` off
  (and vice versa after removing the override), through
  `resolve_request_config` + `_resolve_plugins_for_config`.
- Terminal `/set`: test that `/set shell_tool_mode shell_command` persists
  the override (value and label forms accepted).

### Additional implementation verification

- Full codex-tools suite plus this plugin's tests; key-gated selection
  suites with `OPENROUTER_API_KEY` exported.
- Manual smoke of the mobile session-settings chips against a local server
  (if a device/simulator is unavailable, verify via the schema/API layer
  and report as not run).

## Completion Notes

Completed 2026-10-10.

**Outcome:** model-based shell tool selection is removed and
`shell_tool_mode` is exposed as a per-session setting through a new opt-in
plugin.

- Selection (`codex-tools`): `auto`/missing/`exec_command` →
  `exec_command` + `write_stdin` for every model (upstream parity);
  `shell_command` and `shell` are explicit-mode only; no tool consults the
  `codex-variant` tag anymore. `CodexVariantFeature` keeps emitting the
  tag (informational); its docstring was updated.
- New plugin `plugins/shell-tool-settings`: one behavior-free
  `ShellToolSettingsFeature` contributing a `select` UI element
  (`shell_tool_mode`, default `auto`, options auto/exec_command/
  shell_command/shell with `{value, label}` shape accepted by both the
  terminal `/set` matcher and the mobile settings chips). Not referenced
  by the default config — the setting only exists for agents that load
  the plugin.
- Session revert flow verified end to end at the
  `resolve_request_config` + `_resolve_plugins_for_config` boundary:
  a session override flips the active shell tools from the next request
  on; removing it restores the agent default; agent-level setting acts as
  the default and a session override wins over it.

**Requirement evidence:** 13 tests in
`plugins/shell-tool-settings/tests/test_shell_tool_settings_feature.py`
(element shape/options/default, schema present-with/absent-without the
plugin, override flow incl. reset and agent-default precedence,
model-agnostic default for gpt-6/gpt-5/gemini); updated codex-tools
selection suites (auto-without-tag → unified exec, array tool
explicit-mode-only, matrix tests).

**Verification:** full codex-tools suite 238 passed / 40 key-gated skips
(exit 0); key-gated suites with `OPENROUTER_API_KEY`: 37 passed (one
stale assertion in `test_force_enabled_enables_legacy_tool` found and
fixed, then the file plus the hosted-API file re-run: 32 passed, including
the real-API `exec_command` round-trip on `openai/gpt-6-luna` and the
array tool with its new explicit mode); ruff clean; the new plugin shows
only the same pre-existing pyright override-pattern errors as sibling
feature plugins.

**Not run / deferred:** mobile session-settings chip smoke on a device
(schema/API layer verified instead); Windows (030).
