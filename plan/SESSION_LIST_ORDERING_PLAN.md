## Session List Ordering – Plugin-Driven Design Plan

This plan describes how to make session ordering fully plugin-driven, while
keeping `/sessions` and the mobile Sessions screen simple and backward
compatible.

The focus here is **ordering semantics and server wiring**; concrete plugin
implementations (timestamp, pinned, etc.) will be planned separately.

---

## 1. Goals

- Let **application plugins** determine how sessions are ordered.
- Support **multi-level ordering** (e.g. pinned first, then updated, then
  message count).
- Allow **per-session missing data** (e.g. sessions without messages) via
  explicit fallback values, not hard-coded logic.
- Move **pinned ordering** out of server-specific rules into plugin logic.
- Preserve a **sensible default** when no ordering information is provided or
  when plugin contracts are violated.

Non-goals:

- No arbitrary user-provided sort expressions or code; ordering remains
  deterministic and based on simple keys + priorities.
- No changes to the mobile API surface beyond the existing `/sessions`
  response; ordering is purely server-side.

---

## 2. Current State (Summary)

**Server** – `application/python/agent_terminal_app/server.py`

- `GET /sessions`:
  - Scans `*.json` under the sessions root.
  - Builds each entry with:
    - `session_id` – filename stem.
    - `modified` – file `stat().st_mtime` (float seconds since epoch).
    - `preview` – first `role == "user"` message content, truncated.
    - `metadata` – stored session metadata, with `native_messages` removed.
    - `pinned` – boolean from `metadata[session_pinned_metadata_key]`.
  - Runs application actions with `trigger == "session_list"` and merges
    any returned `session_list_fields` into the entry.
  - Caches entries per session root for performance.
  - Orders sessions as:
    1. Sort by `modified` (descending).
    2. Partition into `pinned` then `unpinned`, preserving per-group order.

**Application plugins** – `core/python/plugins`

- `SessionMessageCountMetaAppPlugin`:
  - Adds a `message_count` field per session via a
    `trigger == "session_list"` action that returns
    `{"session_list_fields": {"message_count": <int>}}`.
- `SessionTimestampMetaAppPlugin`:
  - Adds a `session_list_field` UI element pointing at `modified` for
    display (meta line), but does not change ordering.
- `SessionPinnedAppPlugin`:
  - Stores pinned state in session metadata using a configurable
    `session_pinned_metadata_key` under `application`.
  - Provides UI elements for toggling pinned via `/actions`.
  - **Ordering is still implemented directly in `/sessions`**, not via this
    plugin.

**Mobile app** – `mobile/crystal-lattice-control-rn`

- `apiListSessions` consumes `/sessions` and exposes `SessionSummary` with
  `session_id`, `modified`, `preview`, optional `metadata`, `pinned`, and
  any extra plugin fields.
- `ApplicationPluginsContext` loads application UI schema and actions, then
  derives:
  - `sessionListFields` (from `session_list_field` elements).
  - `sessionListPinnedToggles` (from `session_list_toggle_pinned`).
- `SessionsScreen`:
  - Renders session rows using `sessionListFields` for title/subtitle/meta.
  - Does **not** apply any extra sorting; it trusts the server order.

Conclusion: **Ordering is currently hard-coded** to `modified` + pinned-first
in `/sessions`. Application plugins can compute per-session fields but cannot
influence order.

---

## 3. Target Design – Plugin-Driven Ordering

We extend the contract for application actions with `trigger == "session_list"`
so they can **declare ordering preferences** in addition to per-session fields.

### 3.1. Extended action result shape

For `trigger == "session_list"` actions, we support:

```python
return {
    "session_list_fields": {
        # per-session fields as today
        "session_created_at": 1_704_000_000.0,   # example epoch seconds
        "session_updated_at": 1_704_100_000.0,
        "pinned_rank": 0,                        # example for pinned ordering
    },
    "session_list_order": [
        {
            "key": "pinned_rank",        # dotted path into the summary
            "direction": "asc",          # "asc" or "desc" (required)
            "fallback": 1,                # literal value when key is missing
            "priority": 0,                # optional, default 100
        },
        {
            "key": "session_updated_at",
            "direction": "desc",        # will be normalized globally
            "fallback": 0.0,
            "priority": 10,
        },
    ],
}
```

**Fields:**

- `session_list_fields` (unchanged):
  - Per-session fields to be merged into the `/sessions` entry.

- `session_list_order`: list of **order specs** (zero or more):
  - `key: str` (required)
    - Dotted path into the final session summary entry (e.g.
      `"session_updated_at"`, `"metadata.title"`, `"pinned_rank"`).
  - `direction: "asc" | "desc"` (required)
    - Per spec, but effectively **global**; the application will choose a
      single direction and ignore the rest.
  - `fallback: Any` (optional but semantically required when some sessions
    may not have the `key` field)
    - A **literal value**, not a path.
    - Used when `key` does not resolve for a given session.
    - Example: for `direction == "desc"`, a very small timestamp like `0`
      will place missing entries at the end; for `direction == "asc"`, a
      very large timestamp can be used to push them to the end.
  - `priority: int` (optional, default `100`)
    - Lower means higher precedence in the multi-level sort order.

Plugins may return **multiple** specs in `session_list_order`, and multiple
plugins may contribute specs. The server will merge and normalize these.

### 3.2. Semantics and validation

- **Global direction**:
  - The server sorts all collected specs by `(priority, plugin order,
    spec index)`.
  - The **direction** of the *first* spec in this sorted list becomes the
    global direction for the entire ordering.
  - All other specs' `direction` values are ignored (optionally logged for
    debugging when they differ).

- **Fallback requirement**:
  - For each spec, if **any** session entry cannot resolve `key` and the spec
    does **not** provide a `fallback`, that spec is considered invalid and is
    **dropped** from the ordering set.
  - The server logs an error like:
    - `Ignoring session_list_order spec from plugin 'X': key 'Y' missing for some sessions and no fallback provided.`
  - This enforces the invariant: *when a key might be missing, fallback must
    be explicitly defined by the plugin*.

- **Spec viability**:
  - If a spec's `key` never resolves for any session *and* `fallback` is not
    provided, it is dropped and logged as above.
  - If a spec's `key` never resolves but `fallback` is present, it is still
    valid: all sessions will use the same literal fallback.

- **Legacy fallback**:
  - If **no valid specs** remain after filtering (all dropped due to missing
    fallback or other issues), `/sessions` falls back to **current legacy
    behavior**:
    - Sort by `modified` descending.
    - Apply pinned-first grouping (for backward compatibility).
  - The server logs that plugin-driven ordering was ignored.

---

## 4. Server-Side Ordering Algorithm

This section describes how `GET /sessions` will use the new contract.

### 4.1. Data collection (unchanged)

For each `*.json` session file:

1. Build the base `entry` with `session_id`, `modified`, `preview`,
   `metadata`, `pinned` as today.
2. Run all `trigger == "session_list"` actions:
   - Merge any `session_list_fields` into `entry`.
   - Collect any `session_list_order` specs, tagging each with:
     - `plugin_id`.
     - `plugin_index` – index of the plugin in `application_plugins`.
     - `spec_index` – index in the plugin's `session_list_order` list.

After processing all sessions, we have:

- `items`: list of session entries.
- `order_specs_raw`: list of all candidate order specs from plugins.

### 4.2. Normalizing order specs

1. **Sort specs** by `(priority, plugin_index, spec_index)`.
2. **Pick global direction** from the first spec in this sorted list.
   - Example: if the first spec is `{"direction": "asc"}`, the global
     ordering direction is ascending.
3. **Filter invalid specs**:
   - For each spec, check all session entries:
     - If `key` cannot be resolved for at least one entry and `fallback` is
       not defined → drop spec and log an error.
     - Otherwise, keep spec.
4. If after filtering there are **no specs left**, fall back to legacy
   behavior as described above.

### 4.3. Computing per-session sort keys

Given the filtered, ordered specs `S1, S2, ..., Sn` and global direction `D`:

For each session entry `E`:

1. For each spec `Si`:
   - Attempt to resolve `Si.key` on `E` using a dotted-path helper.
   - If resolution succeeds and yields a comparable value, use it.
   - If resolution fails or yields an unusable value, use `Si.fallback`
     (known to exist by this point, due to filtering).
2. Compose a **composite key**:

   ```python
   composite_key(E) = (
       value_for_S1(E),
       value_for_S2(E),
       ...,
       value_for_Sn(E),
       E["modified"],    # final fallback
       E["session_id"],  # tiebreaker for deterministic ordering
   )
   ```

3. Sort `items` by `composite_key(E)`:
   - If `D == "asc"`, sort ascending.
   - If `D == "desc"`, sort ascending then reverse, or invert values as
     appropriate.

### 4.4. Pinned semantics

- **New behavior when plugin ordering is active**:
  - If there is at least one valid `session_list_order` spec, **do not** apply
    any special pinned grouping in `/sessions`.
  - Pinned-first behavior is entirely up to plugins, typically via a
    `pinned_rank` field and an order spec like:

    ```python
    {
        "key": "pinned_rank",   # 0 for pinned, 1 for unpinned
        "direction": "asc",
        "fallback": 1,
        "priority": 0,
    }
    ```

- **Legacy behavior when no valid specs exist**:
  - Retain current pinned-first grouping and `modified`-based ordering for
    backward compatibility.

This makes pinned ordering fully plugin-driven when plugins are configured,
while not breaking existing deployments that have no ordering plugins.

---

## 5. Example Plugin Usage

### 5.1. Timestamp-based ordering (first & last message)

A future `SessionTimeMetaAppPlugin` (or an evolution of
`SessionTimestampMetaAppPlugin`) would:

1. `get_actions`:
   - Provide a `trigger == "session_list"` action, e.g.
     `compute_session_times`.
2. `execute_action` for that action:
   - Accept `session_id` and optionally `session` from params.
   - Load the `Session` if needed.
   - Determine:
     - `session_created_at` = timestamp of the first message (or earliest
       available message timestamp).
     - `session_updated_at` = timestamp of the last message.
   - Return:

     ```python
     return {
         "session_list_fields": {
             "session_created_at": created_ts,
             "session_updated_at": updated_ts,
         },
         "session_list_order": [
             {
                 "key": "session_updated_at",
                 "direction": "desc",
                 "fallback": 0.0,
                 "priority": 10,
             },
         ],
     }
     ```

3. `get_ui_elements`:
   - Contribute `session_list_field` entries for explicit "Updated" and
     "Created" meta lines, with `metadata.format == "datetime"` so the
     mobile client formats them properly.

### 5.2. Pinned-first via plugin ordering

An updated `SessionPinnedAppPlugin` would, in its `trigger == "session_list"`
action:

1. Compute a `pinned_rank` field per session:
   - `0` for pinned sessions.
   - `1` for unpinned or missing pinned state.
2. Return an order spec:

   ```python
   {
       "session_list_fields": {
           "pinned_rank": 0 if is_pinned else 1,
       },
       "session_list_order": [
           {
               "key": "pinned_rank",
               "direction": "asc",
               "fallback": 1,
               "priority": 0,
           },
       ],
   }
   ```

This makes pinned-first behavior purely a function of plugin-configured
ordering, not server hard-coding.

---

## 6. Implementation Steps (Server Layer)

1. **Update `/sessions` implementation** in
   `application/python/agent_terminal_app/server.py`:
   - While collecting `session_list_fields`, also collect
     `session_list_order` specs with plugin metadata.
   - Implement the normalization and filtering logic described in
     Sections 3 & 4.
   - When valid specs exist, sort using composite keys and **do not** apply
     hard-coded pinned grouping.
   - When no valid specs exist, retain legacy ordering and pinned grouping.
   - Add clear log messages when:
     - Specs are dropped due to missing fallback.
     - All plugin ordering is ignored and fallback to legacy behavior occurs.

2. **Dotted-path resolution helper**:
   - Introduce a small helper to resolve dotted paths into the session summary
     dict (similar to the mobile-side `extractByPath`).
   - Use this helper for `key` lookups in order specs.

3. **Tests for server behavior**:
   - New tests in `application/python/tests` to cover end-to-end `/sessions`
     semantics with and without ordering plugins:
     - Single plugin providing a valid `session_list_order` with `key`,
       `direction`, `fallback`, and `priority`, verifying that ordering
       follows the plugin-defined field and falls back to `modified` only
       when appropriate.
     - Multiple plugins contributing specs with different priorities and
       multiple specs per plugin, verifying:
       - Priority ordering (`priority`, plugin order, spec index).
       - That the global direction comes from the highest-priority spec and
         later `direction` values are ignored.
       - Multi-level composite ordering (primary/secondary/tertiary keys).
     - Pinned-first behavior expressed purely via plugin-driven fields (e.g.
       `pinned_rank`) when at least one valid ordering spec is present, and
       confirmation that no server-side pinned grouping is applied in that
       case.
     - Legacy fallback when no valid specs exist (or no ordering plugins are
       configured): sorting by `modified` desc and applying the old
       pinned-first grouping.
     - Specs dropped when `key` is missing for some sessions and no
       `fallback` is provided, with behavior matching the legacy fallback and
       no crashes.

4. **Documentation updates**:
   - Update `APPLICATION_APP_PLUGINS_AND_ACTIONS_PLAN.md` (or a dedicated
     plugin dev doc) to describe the `session_list_order` contract for
     `trigger == "session_list"` actions.
   - Note that ordering is now plugin-driven and that pinned-first semantics
     should be expressed via ordering fields rather than assumed.

---

## 7. Next Steps (Out of Scope for This Plan)

- Design and implement specific plugins (or plugin extensions) that:
  - Compute `session_created_at` and `session_updated_at` from the first and
    last message timestamps.
  - Expose explicit "Updated: ..." and "Created: ..." meta fields in the
    session list UI schema.
  - Express pinned-first semantics via `pinned_rank` ordering.
- Consider whether any existing application configs should set defaults for
  ordering-related fields, or whether we rely purely on plugin defaults.

Those plugin-level designs will be captured in a separate plan file.
