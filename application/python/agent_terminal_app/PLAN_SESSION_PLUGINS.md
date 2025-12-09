# Terminal session plugin toggling plan

## Goal

Allow users of the terminal client (`terminal.py`) to turn plugins on/off **per session**, with clean integration into the existing `AgentApplication`/`TerminalApplication` architecture and the JSON config.

Key requirements:

- Plugins are referred to by **plugin id** (their `name` attribute), not by Python class path.
- Use an **enabled list** (whitelist) rather than a disabled list:
  - Once an explicit enabled set is present for a session, **only** those plugins are loaded.
  - Any plugins not in the list are **not loaded** for that session.
  - Any plugin ids in the list that are unknown are ignored.
- The same enabled-list configuration is available at the **agent** level via a `"plugins"` key in the agent config. This acts as the default plugin set for new sessions of that agent.
- Once a session’s enabled plugin set is changed, that set is stored on the session and respected for its lifetime; agent defaults no longer affect that session.

---

## Plugin identity and catalog

**Plugin id**: use the plugin class `name` attribute as the id, e.g.

- `OpenRouterProvider.name` → `"openrouter"`
- `OpenRouterToolsExtension.name` → `"openrouter_tools"`
- `SystemMessageFeature.name` → `"system_message"`
- `ShellTool.name` → `"shell"`
- `DelayExtension.name` → `"delay_extension"`
- `RandomFailureExtension.name` → `"random_failure_extension"`

The existing root `"plugins"` section in config (with Python class paths) remains the source of **available** plugins:

```json
"plugins": {
  "providers": ["plugins.openrouter_provider.OpenRouterProvider"],
  "extensions": [
    "plugins.openrouter_reasoning_extension.OpenRouterReasoningExtension",
    "plugins.openrouter_tools_extension.OpenRouterToolsExtension",
    "plugins.delay_extension.DelayExtension",
    "plugins.random_failure_extension.RandomFailureExtension"
  ],
  "features": ["plugins.system_message_feature.SystemMessageFeature"],
  "tools": [
    "plugins.shell_tool.ShellTool",
    "plugins.apply_patch_tool.ApplyPatchTool"
  ]
}
```

In `AgentApplication.__init__` (`core/python/agent_app/application_future.py`):

- After `load_plugins`, build a catalog mapping kind+id to classes:

  ```python
  self._plugins_by_kind_and_id: Dict[str, Dict[str, type[Any]]]
  # kind ∈ {"providers", "features", "tools", "extensions"}
  # id is plugin_cls.name (fallback to __name__ if missing)
  ```

- Also expose a catalog for callers:

  ```python
  def list_plugins(self) -> List[Dict[str, Any]]:
      # → [{
      #   "kind": "tools",
      #   "id": "shell",
      #   "class_path": "plugins.shell_tool.ShellTool",
      #   "class_name": "ShellTool",
      # }]
  ```

Unknown ids will not appear in these maps, which makes it easy to safely ignore invalid entries in enabled lists.

---

## Agent‑level default plugin set (config `agents[agent_id].plugins`)

Extend each agent’s config (`resolved_config["agents"][agent_id]`) with an optional flat list of plugin ids:

```json
"agents": {
  "default": {
    "provider": "openrouter_tools",
    "plugins": [
      "openrouter",
      "openrouter_tools",
      "system_message",
      "shell",
      "delay_extension",
      "random_failure_extension"
    ],
    "enable_delay_extension": false,
    "delay_seconds": 10,
    "enable_random_failure": false,
    "random_failure_every": 3
  }
}
```

Rules:

- Shape: `"plugins"` is a list of **plugin ids** (strings). No per‑kind structure.
- Semantics:
  - If `agents[agent_id].plugins` is present:
    - This is the **default enabled plugin id list** for *new* sessions of that agent.
  - If omitted:
    - The default for that agent is: **all loaded plugins enabled**.

Implementation details in `AgentApplication.__init__`:

- While building `self._agent_base_configs`, also build:

  ```python
  self._agent_plugin_ids: Dict[str, Optional[List[str]]]
  ```

- For each agent id:

  ```python
  raw_plugins = agent_cfg.get("plugins")
  if isinstance(raw_plugins, list):
      self._agent_plugin_ids[agent_id] = [p for p in raw_plugins if isinstance(p, str)]
  else:
      self._agent_plugin_ids[agent_id] = None  # means "all plugins enabled"
  ```

- Add a helper:

  ```python
  def get_agent_plugins(self, agent_id: str) -> Optional[List[str]]:
      # Returns the configured plugin-id list, or None for "all".
  ```

---

## Session‑level plugin set (session.metadata["plugins"])

Sessions gain an optional **flat list** of enabled plugin ids in their metadata:

```python
session.metadata["plugins"] = [
    "openrouter",
    "openrouter_tools",
    "system_message",
    "shell",
]
```

Rules:

- If `session.metadata["plugins"]` **exists and is a list**:
  - It is the **authoritative enabled plugin list** for that session.
  - Any plugin with an id *not* in this list is not registered for that session.
  - Any ids that do not match a loaded plugin are **ignored**.
- If `session.metadata["plugins"]` is **missing or not a list**:
  - The session’s effective plugin set is derived from its agent:

    ```text
    enabled_ids = agent.plugins (if configured)
               or all available plugin ids (if not).
    ```

- **Precedence and lifecycle**:

  1. On session **creation** (`create_session`):
     - There is no `metadata["plugins"]` yet.
     - Determine enabled ids from the agent default:

       ```python
       enabled_ids = self._agent_plugin_ids.get(agent_id)  # may be None
       ```

     - Build the core with that set (details in the next section).
     - The new `Session` initially has metadata `{"agent_id": agent_id}` only
       (no explicit `"plugins"` key yet).

  2. On **load_session**:

     - Load the session and inspect metadata:

       ```python
       metadata = session.metadata or {}
       plugins_from_session = metadata.get("plugins")
       if isinstance(plugins_from_session, list):
           enabled_ids = [p for p in plugins_from_session if isinstance(p, str)]
       else:
           enabled_ids = self._agent_plugin_ids.get(agent_id)  # may be None
       ```

     - Build the core based on these enabled ids.

  3. On **first manual change** of the plugin set via the terminal (`/plugins`):

     - The terminal app writes an explicit `session.metadata["plugins"]` list.
     - From that point on, **that list** is always used when loading the session,
       regardless of any changes to the agent’s default plugin list.

---

## Core construction with an enabled plugin id list

Introduce a helper in `AgentApplication` to construct a core instance using only a specified enabled set of plugin ids:

```python
def _build_core_with_enabled_ids(
    self,
    enabled_ids: Optional[List[str]],
) -> AgentCore:
    """Construct a fresh AgentCore with only selected plugins enabled.

    - enabled_ids is a list of plugin ids (strings) or None.
    - When enabled_ids is None, all available plugins are registered.
    - Unknown plugin ids are silently ignored.
    """
```

Algorithm:

1. Create a fresh core: `core = self._core_factory()`.
2. Normalize enabled ids:

   ```python
   enabled_set: Optional[Set[str]]
   if enabled_ids is None:
       enabled_set = None  # meaning "all"
   else:
       enabled_set = {p for p in enabled_ids if isinstance(p, str)}
   ```

3. For each kind `k ∈ {"providers", "extensions", "features", "tools"}`:

   ```python
   all_for_kind = self._plugins_by_kind_and_id.get(k, {})  # id -> class
   if enabled_set is None:
       enabled_for_kind = list(all_for_kind.values())
   else:
       enabled_for_kind = [cls for pid, cls in all_for_kind.items() if pid in enabled_set]
   ```

4. Apply the existing registration pattern, but using `enabled_for_kind`:

   ```python
   provider_exts = enabled_extensions  # from above
   for provider_cls in enabled_providers:
       core.register_provider(provider_cls, extensions=provider_exts)
   for feature_cls in enabled_features:
       core.register_feature(feature_cls)
   for tool_cls in enabled_tools:
       core.register_tool(tool_cls)
   ```

5. Edge case handling:

   - If `enabled_providers` is empty, the configuration is effectively unusable
     (no provider to send requests to).
   - Option: raise a clear `RuntimeError("No provider plugins enabled")` here so it
     fails fast; this will surface via the application and make misconfigurations
     easy to debug.

Call‑site integration:

- `create_session(agent_id: str)`:

  ```python
  enabled_ids = self._agent_plugin_ids.get(agent_id)  # Optional[List[str]]
  core = self._build_core_with_enabled_ids(enabled_ids)

  base = core.create_session()
  session = Session(
      session_id=base.session_id,
      messages=list(base.messages),
      metadata={"agent_id": agent_id},  # no "plugins" yet
  )
  ```

- `load_session(session_id: str)`:

  ```python
  session = self._session_store.load(session_id)
  ...
  metadata = session.metadata or {}
  plugins_from_session = metadata.get("plugins")
  if isinstance(plugins_from_session, list):
      enabled_ids = [p for p in plugins_from_session if isinstance(p, str)]
  else:
      enabled_ids = self._agent_plugin_ids.get(agent_id)

  core = self._build_core_with_enabled_ids(enabled_ids)
  return core, base_cfg, session
  ```

The existing `send_request` API remains unchanged and simply receives a core
already configured with the correct plugin set.

---

## TerminalApplication helpers

Add helpers in `TerminalApplication` (`application/python/agent_terminal_app/terminal_app.py`) to
inspect and mutate the session’s plugin set.

### 1. Inspect current session plugins

```python
def list_plugins_for_session(self) -> List[Dict[str, Any]]:
    core, base_config, session = self.require_session()
    all_plugins = self._app.list_plugins()  # from AgentApplication
    metadata = session.metadata or {}

    plugins_from_session = metadata.get("plugins")
    if isinstance(plugins_from_session, list):
        enabled_ids = {p for p in plugins_from_session if isinstance(p, str)}
        source = "session"
    else:
        agent_id = metadata.get("agent_id") if isinstance(metadata.get("agent_id"), str) else "default"
        default_ids = self._app.get_agent_plugins(agent_id)
        if default_ids is None:
            enabled_ids = None  # treat as "all enabled"
            source = "implicit"
        else:
            enabled_ids = set(default_ids)
            source = "agent"

    result: List[Dict[str, Any]] = []
    for entry in all_plugins:
        pid = entry.get("id")
        kind = entry.get("kind")
        name = entry.get("name") or pid
        if enabled_ids is None:
            enabled = True
            src = "implicit"
        else:
            enabled = pid in enabled_ids
            src = source

        result.append(
            {
                **entry,
                "enabled": enabled,
                "source": src,
            }
        )

    return result
```

Notes:

- `source` indicates where the effective enabled state came from:
  - `"session"` → explicit `session.metadata["plugins"]` list.
  - `"agent"` → agent default `agents[agent_id].plugins`.
  - `"implicit"` → no explicit lists, everything enabled.

### 2. Update session plugin list

```python
def set_session_plugins(self, enabled_ids: List[str]) -> Session:
    session = self.session
    metadata = session.metadata or {}

    # Normalize unique list while preserving order
    seen: Dict[str, None] = {}
    normalized: List[str] = []
    for pid in enabled_ids:
        if not isinstance(pid, str):
            continue
        if pid in seen:
            continue
        seen[pid] = None
        normalized.append(pid)

    new_metadata = {**metadata, "plugins": normalized}

    new_session = Session(
        session_id=session.session_id,
        messages=list(session.messages),
        metadata=new_metadata,
    )
    self._app.save_session(new_session)

    # Reload via AgentApplication so that core/base_config reflect new plugins
    ctx = self._app.load_session(new_session.session_id)
    if ctx is not None:
        core, base_config, session_obj = ctx
        self._core = core
        self._base_config = base_config
        self._session = session_obj
        self._last_event_id = None

    return self._session
```

Optional helper to clear session‑specific plugin overrides (revert to agent default):

```python
def clear_session_plugins(self) -> Session:
    session = self.session
    metadata = session.metadata or {}
    if "plugins" not in metadata:
        return session

    new_metadata = dict(metadata)
    new_metadata.pop("plugins", None)

    new_session = Session(
        session_id=session.session_id,
        messages=list(session.messages),
        metadata=new_metadata,
    )
    self._app.save_session(new_session)

    ctx = self._app.load_session(new_session.session_id)
    if ctx is not None:
        core, base_config, session_obj = ctx
        self._core = core
        self._base_config = base_config
        self._session = session_obj
        self._last_event_id = None

    return self._session
```

---

## `/plugins` slash command in `terminal.py`

Add a new slash command to `terminal.py` that lets users inspect and modify the
session’s plugin set.

### Command behavior

- `/plugins`
  - Show all known plugins (from `list_plugins_for_session()`), including:
    - index (1‑based)
    - enabled/disabled status
    - kind (`provider`, `extension`, `feature`, `tool`)
    - id (`shell`, `system_message`, `openrouter`, ...)
  - Example output:

    ```
    [plugins] Active plugin configuration for this session:
      1. [on ] provider   openrouter
      2. [on ] extension  openrouter_tools
      3. [on ] feature    system_message
      4. [on ] tool       shell
      5. [off] extension  delay_extension
    ```

  - Store the ordered list in `ui_state["plugins_last_list"]` for later index‑based
    toggles.

- `/plugins on <id-or-index>`
  - Resolve `<id-or-index>`:
    - If it is digits only → treat as 1‑based index into `plugins_last_list`.
    - Else → match by `id` (exact); if not found, optionally match a unique plugin
      by name.
  - Determine the **current effective enabled ids**:
    - If `session.metadata["plugins"]` exists and is a list, use that list as
      the starting point.
    - Otherwise, derive from the agent default / implicit all‑enabled set.
  - Add the target plugin id into the enabled list if it’s not already present.
  - Call `app.set_session_plugins(new_enabled_ids)`.
  - Print confirmation, e.g.:

    ```
    [plugins] enabled plugin 'shell' for this session
    ```

- `/plugins off <id-or-index>`
  - Same resolution logic as `on`.
  - Determine current effective enabled ids as above.
  - Remove the target plugin id from the enabled list.
  - Call `app.set_session_plugins(new_enabled_ids)`.
  - Print confirmation, e.g.:

    ```
    [plugins] disabled plugin 'shell' for this session
    ```

  - Optionally warn the user if this leaves the session with no providers at all
    (based on `kind == "providers"`).

- `/plugins reset` (optional convenience)
  - Clear session‑specific overrides by calling `app.clear_session_plugins()`.
  - After this, the session will revert to the agent’s default plugin set
    (`agents[agent_id].plugins` or implicit all‑enabled).

### Completer

Add a simple completer function:

```python
def _plugins_completion(app: TerminalApplication, text: str) -> List[Completion]:
    # First token: subcommand
    # Second token: plugin id (complete from list_plugins_for_session)
```

Behavior:

- If no space yet:
  - Complete `on`, `off`, `reset` based on prefix.
- After the first token is `on`/`off`:
  - Complete plugin ids (`entry["id"]`) from `list_plugins_for_session()`, filtered by
    prefix.

Register in `terminal.py`:

```python
@slash_command("plugins", "List or toggle plugins for this session", completer=_plugins_completion)
async def _cmd_plugins(app, arg, write, ui_state):
    ...
```

---

## Semantics summary

- **Identity**: plugins are referred to by their `name` attribute.
- **Agent default**: `agents[agent_id].plugins` is an optional list of plugin ids
  that defines the default enabled set for new sessions of that agent; if absent,
  all loaded plugins are enabled.
- **Session override**: `session.metadata["plugins"]` is an optional list of
  plugin ids that, when present, becomes the authoritative enabled set for that
  session. Unknown ids are ignored.
- **Construction**: `AgentApplication` builds cores via
  `_build_core_with_enabled_ids(enabled_ids)` for both `create_session` and
  `load_session`.
- **Terminal UI**: `/plugins` in `terminal.py` lets users view and modify the
  session’s enabled plugin set. The first change writes `session.metadata["plugins"]`
  and reloads the core so subsequent requests respect the updated set.

This plan keeps configuration and behavior consistent while adding a clear,
minimal mechanism for per‑agent defaults and per‑session plugin toggling.