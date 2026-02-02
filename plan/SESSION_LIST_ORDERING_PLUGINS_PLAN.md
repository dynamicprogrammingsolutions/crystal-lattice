## Session List Ordering Plugins – Draft Plan

This plan sketches two application-level plugins that work together to
provide richer session timestamps and a specific ordering strategy on top of
the server-side `session_list_order` contract defined in
`SESSION_LIST_ORDERING_PLAN.md`.

Plugins:

1. **SessionTimeMetaAppPlugin** (name TBD; likely an evolution of
   `SessionTimestampMetaAppPlugin`):
   - Computes `session_created_at` and `session_updated_at` based on the first
     and last messages in a session.
   - Exposes explicit "Updated: ..." and "Created: ..." display fields for
     the session list.
   - Does **not** define ordering; it just provides data and display.

2. **SessionOrderingBucketsAppPlugin** (new plugin):
   - Implements a specific ordering strategy via `session_list_order`:
     1. Sessions updated in the **last 24 hours**.
     2. Among the rest, **pinned sessions** first.
     3. Within each bucket, order by **last updated time** (most recent first).

The two plugins are loosely coupled: the ordering plugin *depends on* the
presence of `session_updated_at` (or falls back to `modified`) and the pinned
flag, but it does not own how those are computed.

---

## 1. SessionTimeMetaAppPlugin – Created/Updated Timestamps + Display

### 1.1. Responsibilities

- Derive **session-level timestamps** from the message history:
  - `session_created_at`: timestamp of the first message (oldest).
  - `session_updated_at`: timestamp of the last message (newest).
- Surface explicit UI metadata in the session list:
  - `Updated: <human time>`.
  - `Created: <human time>`.
- Resist changing ordering; this plugin focuses on **data and display** only.

### 1.2. Inputs and assumptions

- Runs as an **application plugin** at the `AgentApplication` layer.
- Assumes that message-level timestamps are available via
  `message.metadata["timestamp"]` when the `TimestampExtension` feature plugin
  is enabled. If those are missing, it may:
  - Fallback to an approximate timestamp (e.g., `modified` or now), or
  - Choose to leave `session_created_at` / `session_updated_at` unset.
- Has access to:
  - `session_id` (always).
  - Optionally `session` object if requested in the action's `inputs`.

### 1.3. Plugin shape

- File: `core/python/plugins/session_time_meta_app.py` (new) **or** an
  extension of `session_timestamp_meta_app.py` if we decide to fold them
  together.
- Class: `SessionTimeMetaAppPlugin` (name TBD).

**Config schema** (under `application`):

- Initially minimal; possible future options:
  - `session_time_use_modified_when_missing` (bool, default `True`).
  - `session_time_timezone` (string, mostly for docs; actual formatting is on
     clients).

**UI elements** (`get_ui_elements`):

- Two `session_list_field` elements for display:

  ```python
  return [
      {
          "ui_type": "session_list_field",
          "id": "session_updated_at_field",
          "plugin": "session_time_meta",  # added by wrapper if omitted
          "role": "meta",
          "label": "Updated",
          "data": "session_updated_at",
          "template": "Updated: {{data}}",
          "order": 0,
          "metadata": {"format": "datetime"},
      },
      {
          "ui_type": "session_list_field",
          "id": "session_created_at_field",
          "role": "meta",
          "label": "Created",
          "data": "session_created_at",
          "template": "Created: {{data}}",
          "order": 1,
          "metadata": {"format": "datetime"},
      },
  ]
  ```

Clients (mobile) already interpret `metadata.format == "datetime"` for
numeric values and display them as localized strings.

**Actions** (`get_actions` / `execute_action`):

- Provide a single `trigger == "session_list"` action, e.g.:

  ```python
  {
      "id": "compute_session_time_meta",
      "label": "Compute session created/updated times",
      "inputs": {
          "session_id": {"type": "string", "required": True},
          "session_summary": {"required": False},
          "session": {"required": False},
      },
      "trigger": "session_list",
  }
  ```

- `execute_action` logic:

  1. Accept `session_id` and either:
     - Use `params["session"]` if it is already a `Session` instance, or
     - Call `app.load_session(session_id)` to load it.
  2. Inspect `session.messages`:
     - Determine the **first** message with a usable `metadata.timestamp` →
       `session_created_at`.
     - Determine the **last** such message → `session_updated_at`.
  3. If timestamps are missing, and config allows, fallback to
     `session_summary.get("modified")` or to the file mtime via store.
  4. Return:

     ```python
     return {
         "session_list_fields": {
             "session_created_at": created_ts,   # float seconds since epoch
             "session_updated_at": updated_ts,
         },
         # No session_list_order here; this plugin is display-only.
     }
     ```

**Notes:**

- This plugin intentionally does **not** emit `session_list_order`; it only
  ensures that `session_created_at` and `session_updated_at` exist as session
  summary fields and that the UI can render them.
- Other plugins can rely on `session_updated_at` for ordering.

---

## 2. SessionOrderingBucketsAppPlugin – 24h / Pinned / Last Updated Ordering

### 2.1. Desired ordering semantics

Overall ordering (when plugin ordering is active):

1. **Sessions updated within the last 24 hours**.
2. Then, among the rest, **pinned sessions** should come before unpinned.
3. Within each bucket, order by **last updated time** (most recent first).

This is interpreted as a multi-level sort over three dimensions:

1. `updated_24h_rank` – bucket for "updated in last 24h":
   - `0` for sessions with `session_updated_at` within the last 24 hours.
   - `1` for older sessions.
2. `pinned_rank` – bucket for pinned state:
   - `0` for pinned sessions.
   - `1` for unpinned or missing pinned state.
3. `last_updated_sort_key` – numeric key such that **smaller means more
   recent** when sorting ascending (for example, the negative of
   `session_updated_at`).

We choose a **global ascending direction** and encode recency via negative
values so that we can keep the `direction` consistent across specs.

### 2.2. Plugin shape

- File: `core/python/plugins/session_ordering_buckets_app.py` (new).
- Class: `SessionOrderingBucketsAppPlugin` (name TBD).

**Config schema** (under `application`):

Initial config can be simple and focused on tunables:

- `session_order_24h_window_seconds` (default `86400` → 24h):
  - Length of the "recently updated" window.
- `session_order_use_updated_at` (bool, default `True`):
  - If `True`, look for `session_updated_at` in the summary.
  - If `False` or missing, fallback to `modified`.

**UI elements** (`get_ui_elements`):

- None required for this plugin; it is purely behavioral/ordering. All UI
  remains in time/pinned/title plugins.

### 2.3. Action definition

**Action** (`get_actions`):

- Provide a `trigger == "session_list"` action, e.g.:

  ```python
  {
      "id": "compute_session_order_buckets",
      "label": "Compute session order buckets",
      "description": "Assign 24h and pinned ranks and ordering keys.",
      "inputs": {
          "session_id": {"type": "string", "required": True},
          "session_summary": {"required": False},
      },
      "trigger": "session_list",
  }
  ```

No `session` input is needed; all necessary data should be present in the
summary (including `pinned` and `session_updated_at`).

### 2.4. Execution logic

At execution time, for each session:

1. Determine **now** (`now_ts`) in UTC seconds.
2. Determine an "effective" last-updated timestamp for this session:
   - Preferred: `session_updated_at` from `session_summary` (if present and
     numeric).
   - Fallback: `session_summary.get("modified")` (numeric file mtime).
   - If neither is available:
     - Use a **neutral** default like `0.0`.
     - This situation should be rare if the time meta plugin is active and the
       store is healthy.
3. Compute **24h bucket**:
   - Using configured window (default 86400 seconds):
     - If `effective_updated >= now_ts - window` → `updated_24h_rank = 0`.
     - Else → `updated_24h_rank = 1`.
4. Compute **pinned bucket**:
   - Read `pinned = bool(session_summary.get("pinned"))`.
   - Set `pinned_rank = 0` for pinned sessions, `1` for others.
5. Compute **last-updated sort key** for ascending sort:
   - `last_updated_sort_key = -float(effective_updated)`.
   - More recent timestamps produce **smaller** negative values, giving a
     descending-by-time effect when sorting ascending.

6. Emit `session_list_fields`:

   ```python
   "session_list_fields": {
       "updated_24h_rank": updated_24h_rank,
       "pinned_rank": pinned_rank,
       "last_updated_sort_key": last_updated_sort_key,
   }
   ```

7. Emit `session_list_order` for all three dimensions:

   ```python
   "session_list_order": [
       {
           "key": "updated_24h_rank",
           "direction": "asc",
           "fallback": 1,
           "priority": 10,
       },
       {
           "key": "pinned_rank",
           "direction": "asc",
           "fallback": 1,
           "priority": 20,
       },
       {
           "key": "last_updated_sort_key",
           "direction": "asc",
           "fallback": 0.0,
           "priority": 30,
       },
   ]
   ```

Interpretation under the global ordering contract:

- Global `direction` is taken from the first spec: `"asc"`.
- Specs are applied in priority order:
  1. `updated_24h_rank` – sessions with `0` (last 24h) come before `1`
     (older).
  2. `pinned_rank` – pinned (`0`) come before unpinned (`1`) within each
     24h bucket.
  3. `last_updated_sort_key` – smaller values (more recent timestamps) come
     first within `(24h_rank, pinned_rank)` buckets.

Fallback behavior:

- `updated_24h_rank`: fallback `1` ensures entries missing this field are
  treated as "older".
- `pinned_rank`: fallback `1` treats missing pinned information as unpinned.
- `last_updated_sort_key`: fallback `0.0` is a neutral baseline (older than
  any negative real timestamps) and will place such sessions behind any that
  have a real `last_updated_sort_key`.

### 2.5. Interactions with other plugins

- **SessionTimeMetaAppPlugin**:
  - Provides `session_updated_at`; this ordering plugin prefers that field
    when present.
- **SessionPinnedAppPlugin**:
  - Manages pinned state in metadata and emits `pinned` flag via `/sessions`.
  - Ordering plugin only reads `session_summary["pinned"]` and does not
    change how pinned is stored.
- **Title / message-count / other meta plugins**:
  - Remain orthogonal; they can still provide additional `session_list_fields`
    and `session_list_order` specs with higher `priority` values (e.g. >30)
    if multi-level ordering needs to be extended further.

### 2.6. Fallback when ordering is misconfigured

- If, due to misconfiguration or bugs, any of the specs from this plugin
  violate the server contract (e.g. `key` missing for some sessions and no
  `fallback`), the server will drop that spec and log an error.
- If **all** specs from all plugins are dropped, the server reverts to
  legacy behavior (sort by `modified` desc and apply pinned-first grouping).

---

## 3. Summary of Plugin Roles

- **SessionTimeMetaAppPlugin**:
  - Computes and surfaces `session_created_at` and `session_updated_at`.
  - Contributes display-only `session_list_field` elements for meta lines.
  - Does not influence ordering.

- **SessionOrderingBucketsAppPlugin**:
  - Uses `session_updated_at` (or `modified`) and `pinned` to:
    - Mark sessions as updated within the last 24 hours vs older.
    - Bucket pinned vs unpinned.
    - Compute a recency-based sort key.
  - Emits `session_list_fields` and `session_list_order` specs so that the
    server can order sessions as:
    1. Last 24h updated.
    2. Then pinned vs unpinned.
    3. Then last updated time (most recent first).

The precise class names, module names, and configuration keys can be refined
when implementing, but this plan provides a concrete, testable target
behavior and clear separation of concerns between time computation and
ordering.

---

## 4. Testing Strategy (Overview)

This section captures the intended test coverage so implementation can wire
tests in the right places.

### 4.1. SessionTimeMetaAppPlugin tests (core/python/tests)

- **UI schema coverage**:
  - Config with only `SessionTimeMetaAppPlugin` as `application_plugin`.
  - `AgentApplication.get_application_ui_schema()` must include two
    `session_list_field` elements:
    - `role == "meta"`, `data == "session_updated_at"`,
      `metadata.format == "datetime"`.
    - `role == "meta"`, `data == "session_created_at"`,
      `metadata.format == "datetime"`.

- **Created/updated fields from messages**:
  - Build a `Session` with several messages whose
    `metadata.timestamp` values are known.
  - Call `execute_application_action` for the `trigger == "session_list"`
    action, passing `session` (and optionally `session_summary`).
  - Assert that:
    - `session_created_at` corresponds to the earliest message timestamp.
    - `session_updated_at` corresponds to the latest message timestamp.

- **Fallback behavior when message timestamps are missing**:
  - Scenario where no messages have `metadata.timestamp`.
  - Depending on the chosen fallback semantics:
    - If falling back to `session_summary["modified"]`, assert both
      fields equal that value.
    - If leaving fields unset, assert the plugin returns without crashing
      and does not include those keys in `session_list_fields`.

- **No ordering emitted**:
  - For any call, assert that `session_list_order` is absent or empty,
    confirming this plugin is display/data-only.

### 4.2. SessionOrderingBucketsAppPlugin tests (core/python/tests)

- **Action metadata and trigger**:
  - Minimal config with only `SessionOrderingBucketsAppPlugin` enabled.
  - `get_application_actions()` must expose an action with:
    - Expected `id`.
    - `trigger == "session_list"`.
    - `session_id` input (required) and `session_summary` (optional).

- **Bucket and sort key computation**:
  - With a fixed `now` (e.g. monkeypatch time), build several synthetic
    `session_summary` dicts:
    - Recent vs older `session_updated_at` values.
    - Pinned vs unpinned.
  - For each, call `execute_application_action` and assert:
    - `updated_24h_rank` is 0 for sessions within the window, 1 otherwise.
    - `pinned_rank` is 0 for pinned, 1 for others.
    - `last_updated_sort_key` equals `-effective_updated`.

- **Fallback to modified when session_updated_at missing**:
  - Provide summaries with only `modified` set.
  - Assert that bucket and sort key logic uses `modified` and remains
    consistent.

- **session_list_order spec correctness**:
  - Inspect one `session_list_order` result and assert:
    - Three specs present with keys `updated_24h_rank`, `pinned_rank`, and
      `last_updated_sort_key`.
    - All specs have `direction == "asc"`.
    - All specs include `fallback` and expected `priority` values.

### 4.3. End-to-end server tests (application/python/tests)

Using an `AgentApplication` wired with:

- Core echo provider.
- `SessionTimeMetaAppPlugin`.
- `SessionPinnedAppPlugin`.
- `SessionOrderingBucketsAppPlugin`.

and injecting it into `agent_terminal_app.server`, add tests that:

- **24h / pinned / recency ordering**:
  - Create multiple sessions covering combinations of:
    - Updated within 24h vs older.
    - Pinned vs unpinned.
  - Call `GET /sessions` and assert the list order matches:
    1. Recent (24h) sessions first.
    2. Within those, pinned before unpinned.
    3. Within each bucket, most recently updated first.

- **Plugin-driven pinned ordering**:
  - With all ordering plugins active, assert pinned-first behavior is
    achieved via `pinned_rank` and **no server-side pinned grouping**.
  - With ordering plugin disabled but pinned plugin enabled, assert that
    legacy pinned-first grouping still works (backward compatibility).

- **Global direction precedence**:
  - Optional: introduce a second test-only ordering plugin with conflicting
    `direction` but lower priority, and assert that the effective ordering
    follows the direction from the higher-priority specs.

These tests, combined with the unit-level plugin tests and the generic
server tests from `SESSION_LIST_ORDERING_PLAN.md`, should fully exercise the
planned behavior for timestamp display and `24h → pinned → recency`
ordering.

