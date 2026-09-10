# Tool Schema Transparency Plugin

Parent Task: tasks/20260908-bash-cwd-and-tool-schema-transparency/000-main.md

Depends On: none (parallel with `010-bash-cwd-persistence-and-visibility.md`).

Let users see and adjust the tool schemas the model receives — tool names,
tool descriptions, parameters, and parameter descriptions — and disable
specific tools, through a rich UI element around the composer. This subtask
captures requirements and facts only: the implementation approach and exact
UX will be planned in a separate brainstorming session.

## Requirements checklist

Functional:

- [ ] Users can view, for the tools available to the current agent/session: tool names, tool descriptions, tool parameters, and parameter descriptions.
- [ ] Users can disable specific tools.
- [ ] Users can change tool descriptions.
- [ ] Users can change parameter descriptions.
- [ ] The capability appears as a rich UI element around the composer in frontends.

Non-functional:

- [ ] The mechanism uses the same plugin pattern as the existing "disable all tools" option (a feature plugin exposing a config schema, UI elements, and request-time tool-list transformation).
- [ ] A single plugin provides the mechanism, tool gating, and tool schema transformation.
- [ ] Frontends implement a generic rich UI with supporting capabilities: multiple levels (to structure controls), read-only and changeable settings, and similar setting types as ordinary settings.

Optional extra (separate scope decision, not part of the requirements above):

- [ ] Using the same frontend feature, the system message plugin exposes a way to inspect the system message template and the variable contents, with the option to change them for the session.

## Constraint

The way this is implemented and the exact UX will be planned in a separate
brainstorming session. Draft the execution plan there before implementing this
subtask; do not implement from this file alone.

## Requirement questions

- Plugin placement: repo-root `plugins/` (first-party convention) or
  core-packaged next to `ToolGatingFeature`? (Repository policy: no new
  core-packaged plugins without explicit user consent.)
- Override scope: per-request (matching `disable_all_tools`) or per-session
  persistence of overrides?
- Do description and parameter-description changes apply only to the
  model-visible schema, or also to UI display?

## Supporting details

### Existing "disable all tools" mechanism (fact)

- `core/python/plugins/tool_gating_feature.py` — `ToolGatingFeature`
  (FeaturePlugin, name `tool_gating_feature`):
  - `get_config_schema()` → `{"disable_all_tools": {type: boolean, default: False}}`.
  - `get_ui_elements(config, context)` → a checkbox UI element; the context
    already carries `available_tools` (a `ToolDescriptor` list), and the
    feature lists tool names in its description.
  - `prepare_tools(config, tools, context)` → returns `[]` when
    `disable_all_tools` is set, else the tool list.
- Registered in the default config plugin list as
  `plugins.tool_gating_feature.ToolGatingFeature`.
- `ToolDescriptor` (`core/python/agent_core/types.py:40`): frozen dataclass
  with `plugin_name`, `tool_name`, `schema`, `metadata`. The `schema` dict is
  what reaches the model, so description and parameter-description overrides
  are transformations of `schema` applied in `prepare_tools`.
- UI elements are collected by `AgentCore`
  (`core/python/agent_core/core.py` ~3118–3126) from providers, features, and
  tools via `get_ui_elements(config, ui_context)` and rendered by frontends
  (terminal app: `terminal.py` / `terminal_app.py`).
- The tool list pipeline applies feature `prepare_tools` in
  `AgentCore._prepare_tools_for_request`
  (`core/python/agent_core/core.py` ~3985–4053) before the outbound request.

### Frontend setting types (fact)

Ordinary settings UI already supports typed controls (checkboxes, selects,
text inputs — see `get_ui_elements` consumers in the terminal app and the
`request_options_ui` structures in the default config). The generic rich UI
for this feature should reuse those setting types rather than inventing new
ones.