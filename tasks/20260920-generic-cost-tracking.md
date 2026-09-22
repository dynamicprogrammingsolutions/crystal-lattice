# Generic cost tracking and usage data directory

Separate detailed cost tracking from the ChatGPT integration into a generic,
provider-agnostic cost tracking plugin, give user-owned usage data a stable
home-directory default via a new config placeholder variable, and rework the
chat footer session total to aggregate from that store by workspace and
session id.

Delivery is checkpointed: the first version is the minimal working slice
(SQLite store, footer total, report total, per-bucket reset); deeper reporting
and the ChatGPT simplification follow in later checkpoints.

## Requirements checklist — first version (checkpoint 1)

- [ ] A derived config placeholder variable `CRYSTAL_DATA_DIR` defaults to the
  user-level Crystal directory (`$HOME/.crystal`), is available to
  `${env:...}` config placeholders and the runtime environment, and is
  distinct in purpose from `CONFIG_DIR` (user data vs active config location).
- [ ] The ChatGPT rate-limits file, usage journal, and summary CSV default to
  the new data directory rather than `CONFIG_DIR`.
- [ ] Any provider that emits the `cost_tracking` capability tag also provides
  a bucket. The bucket base can be altered by config, but the final bucket is
  defined by the provider that emits the capability tag: `openai_responses`
  appends `-chatgpt` or `-api` depending on the active endpoint (e.g. config
  `openai` → `openai-chatgpt` / `openai-api`; default base `openai-responses`),
  and `reference-openai-compatible-provider` derives the bucket from its
  endpoint URL.
- [ ] Cost records include both actual cost (when the provider supplies one)
  and estimated cost.
- [ ] A generic cost tracking plugin records per-request records (time,
  bucket, session id, workspace, token counts, estimated cost, actual cost)
  for every provider emitting the capability tag, in a SQLite store that
  supports efficient filtering and aggregation by workspace + session id,
  bucket, and time.
- [ ] The chat footer session total is served by the cost tracking store,
  aggregated by workspace (current working directory) + session id, replacing
  the stateless per-message cumulative aggregation.
- [ ] A session action report shows cost totals (per bucket and overall).
- [ ] An action resets tracking for a specific bucket.
- [ ] A manual checkpoint is defined for the first version (user verification
  with the real login before later checkpoints start).

## Later checkpoints (planned, not approved for execution)

Each checkpoint gets its own detailed plan and explicit approval before
execution.

- **Checkpoint 2 — footer breakdown.** The footer additionally shows
  per-request averages for cost items (input / cached / cache write / output /
  reasoning) plus the total request count — or, selectable in config, the
  totals only along with the request count.
- **Checkpoint 3 — ChatGPT account status simplification.** ChatGPT keeps a
  simple report: manual reset time, usage percentage at that time, and total
  cost consumed since. The detailed report moves to the cost tracking plugin,
  and the ChatGPT usage reset offers resetting cost tracking as a follow-up
  action. The ChatGPT journal stays intact until this checkpoint.
- **Checkpoint 4 — report depth.** The detailed report includes the top 10
  sessions by cost (showing project and session ids) and the top 5 projects
  (workspaces resolved to project names via `~/.crystal/projects.json`).
- **Possible follow-up — pricing config.** Per-bucket pricing configuration
  for providers that cannot compute cost themselves.

## Decisions (approved)

- Env var name: `CRYSTAL_DATA_DIR`.
- Store backend: SQLite.
- Buckets are part of the first version; the footer token-breakdown display is
  not.
- Bucket rule: config alters the base, the capability-emitting provider defines
  the final bucket.
- ChatGPT integration stays intact in the first version.

## Supporting details

- Derived config env defaults are built in
  `core/python/agent_app/config.py:43-72` (`build_config_resolution_env`:
  `CONFIG_DIR`, `WORKING_DIR`, `BUILTIN_PLUGINS`) and installed into the
  process environment by `build_runtime_overlay_env`
  (`core/python/agent_app/config.py:75-94`). Process env overlays derived
  values, so the new variable is namespaced (`CRYSTAL_DATA_DIR`) to avoid
  collisions.
- **No specification exists for config env variables.**
  `maintainer/specifications/` contains only `agent-evaluation-framework` and
  `documentation-and-specification-standard`. The behavior is documented in
  `application/python/README.md` (~line 350: "`CONFIG_DIR` always resolves to
  the directory of the active config file") and `docs/reference/default-config.md`.
- Journal path chain today:
  `plugins/openai_responses/src/openai_responses_plugins/chatgpt_usage_journal.py:51-57`
  (journal derives from the rate-limits path; summary CSV derives from the
  journal) and `chatgpt_rate_limits.py:16-29` (config override → credentials
  sibling → `CONFIG_DIR` env → cwd). Under the cloud runtime `CONFIG_DIR`
  points at a copied asset tree (`application/python/README.md:742-743`), so
  user-owned usage data following `CONFIG_DIR` is wrong there — this is the
  "different purpose" the new variable addresses.
- Capability tag mechanism: providers emit tags via
  `get_tags(config, models)` (`plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:381-395`);
  extensions gate activation via `required_tags()` / `forbidden_tags()` /
  `is_enabled(config, tags, models, context)`
  (`core/python/agent_core/plugin/extension.py:53-77`); the core resolves
  enabled plugins from tags in `get_ui_schema` and request resolution
  (`core/python/agent_core/core.py:3018-3054`, tags documented at 3023-3024).
- Current chat footer total:
  `plugins/openai_responses/src/openai_responses_plugins/openai_responses_usage_extension.py:455-465`
  contributes `ui_type: "status_bar"` with
  `data: "metadata.usage_total_cost_cumulative_formatted"`, gated by
  `show_usage_status_total` (default on). The cumulative total is recomputed
  statelessly per message from prior message metadata (~lines 1108-1172).
  Per-message `message_footer` elements (turn cost, token cumulatives) are
  separate and stay stateless.
- The reference provider knows its endpoint: `base_url` with a `scope_key`
  precedent at
  `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/provider.py:151-153`,
  and ships its own `usage_extension.py`.
- Session id comes from provider state `_request_context`
  (`chatgpt_usage_journal.py:77-90`); workspace from `resolve_working_directory`
  (absolute, `chatgpt_usage_journal.py:93+`). Both already recorded in journal
  records (commit `d2eb3711`).
- The openai_responses usage extension stamps usage metadata per response
  (`usage_total_cost`, token counts, `usage_effective_auth_mode`) — the cost
  tracking extension consumes the provider-stamped usage/cost metadata plus
  the provider-defined bucket.
- `~/.crystal/projects.json` is the user-level project registry keyed by
  absolute project path (`application/python/agent_terminal_app/project_profile.py`;
  `ProjectProfile`: name, port, bridge_server_id) — needed only at checkpoint 4.
- SQLite store precedent: `core/python/agent_app/application_notifications.py`;
  config example `${env:CONFIG_DIR}/application-notifications.sqlite3`
  (`application/python/README.md:816`).
- `status_bar` UI elements are rendered by mobile `SessionChatScreen.tsx` and
  desktop `ChatPane.tsx` from UI schema (`filterFooterElements`); documented in
  `plugins/docs/ui-elements.md` — no frontend changes needed.
- Session actions and application actions with form inputs are the existing
  pattern for report/reset actions (`plugins/docs/application-plugins.md`,
  `plugins/docs/actions.md`).
- Eval-runner (Crystal Lattice) runs are tracked automatically via the
  production request path; they will also be captured by the cost store once
  the capability tag is emitted (no runner changes).

## Execution plan

Status: Approved

Scope: checkpoint 1 only. Later checkpoints are listed above and are not
authorized by this plan.

### Approach

**1. Data directory variable (core config).**
Add `CRYSTAL_DATA_DIR` to the derived defaults in `build_config_resolution_env`
and `build_runtime_overlay_env` (`core/python/agent_app/config.py`), defaulting
to `str(Path.home() / ".crystal")`. It resolves like any `${env:...}`
placeholder and can be overridden by process env or `env_overrides` like the
other derived keys. Because the default equals the usual `CONFIG_DIR`
location, configs referencing both point at the same directory on a normal
machine, but the purposes stay separable (data follows the user, config
follows the active config file — e.g. cloud runtime asset copies).

**2. Usage file defaults.**
`resolve_rate_limits_path` (`chatgpt_rate_limits.py:16-29`) replaces its
`CONFIG_DIR` fallback with the new data dir (keeping config/credentials-path
overrides ahead of it); the journal and summary CSV inherit through the
existing chain. Existing installs already keep these files under
`~/.crystal/auth/`, so with the default value nothing moves on disk. If
`CONFIG_DIR` was customized to a non-`~/.crystal` location, new records land
under the data dir while the old file stays in place (append-only contract;
no migration).

**3. Buckets and capability tags (providers).**
- `openai_responses` provider: `get_tags` emits `cost_tracking`; config key
  `cost_bucket` (default `openai-responses`) sets the base, and the provider
  defines the final bucket per request — `openai-responses-chatgpt` when the
  effective auth mode is `chatgpt`, `openai-responses-api` otherwise — stamped
  into request metadata (e.g. `metadata.usage_bucket`).
- `reference-openai-compatible-provider`: config key `cost_bucket` (default
  `openai-compatible`) sets the base; the provider appends a slug of the
  `base_url` host (e.g. `https://api.fireworks.ai/v1` →
  `openai-compatible-api-fireworks-ai`), stamps it into request metadata, and
  emits `cost_tracking` when usage data is available.
- Bucket naming per provider is documented in each plugin's development docs.

**4. Cost tracking plugin (`plugins/cost-tracking`).**
New first-party plugin project (Python package name following
`plugins/AGENTS.md` conventions) registering:
- A provider extension gated on `required_tags: ["cost_tracking"]`:
  - Records one row per request into a SQLite store (default
    `${CRYSTAL_DATA_DIR}/cost-tracking/cost-tracking.sqlite3`, config
    `cost_tracking_db_path`): time, bucket, session id, workspace, model,
    input/cached/cache-write/output/reasoning tokens, estimated cost, actual
    cost, response id (dedupe key). Best-effort like the ChatGPT journal —
    failures never break the request pipeline.
  - Stamps footer metadata computed from the store filtered by
    (working_directory, session_id): session total and request count.
  - Contributes a `status_bar` UI element showing the session total.
- An application plugin exposing:
  - A session action report showing cost totals per bucket and overall.
  - A reset action that resets tracking for a specific bucket (reset marker
    in the store; subsequent report totals for that bucket start there).
- Totals prefer actual cost and fall back to estimated cost when the provider
  supplies no actual cost.

**5. Footer rework.**
The openai_responses `show_usage_status_total` status-bar element (stateless
cumulative) is retired in favor of the cost-tracking status bar; per-message
footers are unchanged. When cost tracking is disabled the session total
disappears (cost tracking is enabled by default whenever a capability-emitting
provider is configured). The retired config key is documented.

**6. ChatGPT integration untouched.**
The ChatGPT journal, summary CSV, and account-status app keep working exactly
as today in this checkpoint (checkpoint 3 revisits them).

**7. Documentation.**
- New plugin docs under `plugins/cost-tracking/docs/` (+ entry in
  `plugins/docs/index.md`).
- `plugins/openai_responses/docs/development/usage-journal.md`: bucket,
  capability tag, retired stateless total, data-dir default.
- `application/python/README.md` (placeholder/env docs, ~line 350 area) and
  `docs/reference/default-config.md`: the new variable.
- No env-var specification exists today; if the documentation-standard
  guidance calls for one at `application/python/docs/development/`, create a
  small page per `docs/development/documentation.md` guidance during execution.

### Implementation decisions and open questions

- Totals prefer actual cost and fall back to estimated cost
  (`COALESCE(actual, estimated)`); both columns are always recorded.
- Footer session totals are not reset-filtered (a session's total is factual
  history); report totals are reset-aware per bucket.
- The store dedupes by response id so re-finalize/rebuild paths cannot
  duplicate rows (mirrors the ChatGPT journal dedupe).
- The openai_responses stateless status-bar element and its
  `show_usage_status_total` config key are retired (documented as a config
  change); the cost-tracking status bar has its own config gate.
- Store schema, bucket slug rule for the reference provider, and the plugin
  package/module naming follow existing conventions and are finalized during
  execution.

### Documentation

Covered in approach step 7: owning-package docs for each change
(`plugins/cost-tracking/docs/`, `plugins/openai_responses/docs/development/usage-journal.md`,
`application/python/README.md`, `docs/reference/default-config.md`,
`plugins/docs/index.md`), following `docs/development/documentation.md` and
`docs/development/crystal-lattice-documentation.md` before any new doc
structure.

### Task checklist

- [x] Add the derived `CRYSTAL_DATA_DIR` env default to
  `build_config_resolution_env` / `build_runtime_overlay_env` + unit tests
  (`core/python/tests/test_application_layer_config.py`)
- [x] Point rate-limits / journal / summary CSV defaults at the data dir +
  tests (`chatgpt_rate_limits.py`, journal unit tests)
- [x] `openai_responses`: `cost_bucket` config, final-bucket metadata
  (`usage_bucket` stamped by the usage extension via the new
  `cost_bucket.py` helper), `cost_tracking` capability tag + tests
- [x] `reference-openai-compatible-provider`: endpoint-URL bucket
  (`cost_bucket.py` host slug) + capability tag + tests
- [x] Cost tracking plugin project: SQLite store module (schema, dedupe,
  aggregation by workspace+session and bucket, per-bucket reset markers) +
  tests (`plugins/cost-tracking`, package `cost_tracking_plugins`)
- [x] Cost tracking extension: record on request, stamp footer metadata,
  contribute the status-bar element + tests
- [x] Cost tracking application plugin: session action report (totals per
  bucket and overall) + per-bucket reset action + tests
- [x] Retire the stateless status-bar total in `openai_responses` + tests
  (the reference provider's stateless status-bar total was retired too)
- [x] Docs per the Documentation section (new plugin docs + README,
  `plugins/docs/index.md` entry, usage-journal.md, configuration-placeholders.md,
  application README; `docs/reference/default-config.md` needed no change —
  the default config references no data paths)
- [x] `ruff` / `black` / `pyright` on changed files; run
  `pytest plugins/openai_responses/tests -q` (478 passed),
  `pytest plugins/reference-openai-compatible-provider/tests -q` (109 passed),
  `pytest plugins/chatgpt-auth-app/tests -q -k 'not manual'` (14 passed), and
  the new plugin suite (43 passed)

### Requirement verification

- Data-dir variable: unit tests asserting `build_config_resolution_env` /
  `build_runtime_overlay_env` produce the default and honor overrides, plus a
  config-resolution test loading a config using
  `${env:CRYSTAL_DATA_DIR}` through the public `load_resolved_config` path.
- Usage file defaults: unit tests on `resolve_rate_limits_path` /
  `resolve_usage_journal_path` / `resolve_summary_csv_path` fallback order.
- Buckets + capability tag: extension/provider unit tests asserting the
  stamped metadata and emitted tags for both auth modes and a reference
  provider `base_url`, including the config-altered base.
- Cost store: unit tests covering record/dedupe, filtered aggregation by
  (workspace, session) and bucket, per-bucket reset marker semantics, and
  actual-vs-estimated cost columns.
- Footer: unit tests on the contributed `status_bar` element and stamped
  metadata; one integration test through the public request path asserting the
  store-backed total arrives in message metadata (production extension, no
  test-only bypass).
- Report/reset: application-plugin action tests asserting the report totals
  (per bucket and overall) and the per-bucket reset.
- Real-login confirmation: existing manual suites
  (`plugins/openai_responses/tests/test_openai_responses_chatgpt_usage_manual_integration.py`,
  `plugins/chatgpt-auth-app/tests/test_chatgpt_auth_account_status_manual_integration.py`)
  with `CHATGPT_TEST_STATE_DIR="$HOME/.crystal"`, extended to assert cost-store
  records carry the bucket.

### Additional implementation verification

- **Manual checkpoint (end of checkpoint 1).** After automated verification,
  the user runs their app with the real `~/.crystal` login and confirms:
  the chat footer shows the session total from the store, the session action
  report shows totals (per bucket and overall), resetting a specific bucket
  works, and the ChatGPT journal/summary CSV behave as before. Later
  checkpoints start only after this checkpoint passes.
## Implementation Notes

- **Metadata promotion mechanics (discovered during execution).** Extension
  `from_native_messages` hooks receive the native list aligned with full
  history, so promotion must index by the message's `native_indices` (the
  usage extension's approach) rather than zipping lists. In the non-stream
  finalize path the usage extension mutates native items in place
  (`item.clear(); item.update(...)`) so history entries and the provider's
  finals — which can be the same objects — both pick up stamps; the cost
  extension mirrors this. The extension finalize chain also runs twice on
  the non-stream path (inside `call_api` for provider finals, then inside
  `provider.finalize`), so recording is guarded by a
  `cost_session_total` presence check plus the response-id unique index.
- **Store path config.** The extension reads `cost_tracking_db_path` from
  the agent config (it is an extension config key); the application plugin
  additionally accepts `application.cost_tracking.db_path`. The integration
  test initially wrote to the default store because the override was placed
  under `application.*` only; two stray rows written to the real
  `~/.crystal` store during that run were deleted.
- **Environment fix.** The environment's `agent-core` editable install
  pointed at a stale worktree (`20260910-duration-session-total`), which made
  core config tests fail when run after plugin tests in one process.
  Reinstalled with `python -m pip install -e "core/python[dev]"` from this
  checkout; combined runs pass.
- **Signature conformance.** The new extension/application plugin use the
  protocol base hook shapes (`get_ui_elements(config, context)`,
  `finalize(..., *, context=None)`,
  `from_native_messages(..., state=None, *, context=None)`) so pyright
  override checks pass; the adapters dispatch by signature at runtime.

### Real-login verification status (checkpoint 1)

Both manual suites were extended to assert cost-store records carry the
provider-defined bucket (`openai-responses-chatgpt`) and that the store-backed
session total reaches the assistant message metadata. They were initially
blocked by the ChatGPT account's usage limit (`429 usage_limit_reached`);
after the user reset usage both suites **pass against the real login**:

- `test_openai_responses_chatgpt_saved_login_usage_multi_turn_tool_loop`
  (openai_responses): journal/CSV behavior unchanged, cost store rows for the
  session's own response ids under `openai-responses-chatgpt`,
  `session_totals` by workspace+session, and final assistant metadata carries
  `cost_session_total_formatted` / `cost_session_requests`.
- `test_chatgpt_account_status_after_real_request` (chatgpt-auth-app): cost
  store rows for the session with the ChatGPT bucket and absolute workspace,
  plus the store-backed total in the final assistant metadata.

Two test-side fixes were needed (no product changes): the auth-app test
defaulted to the retired `gpt-5` model (now `gpt-5.6-luna`, matching the
sibling usage test, still overridable via `OPENAI_RESPONSES_CHATGPT_MODEL`),
and it read `event["session"]` from the application event stream's `final`
event, which actually carries serialized `messages` (plain dicts) plus
`start_index` — the test now reads the assistant message from
`final_messages`. Test-created single-turn sessions written into the real
`~/.crystal/sessions` directory during these runs were removed afterwards.

The user's app-level manual checkpoint (footer/report/reset in their running
app) remains the final confirmation.
- **Test journal isolation.** Several ChatGPT-mode tests in
  `test_openai_responses_usage_extension_unit.py` configure no credentials
  path, so best-effort journal writes fell back to the process working
  directory and polluted the repo root with an `auth/` directory. An autouse
  fixture now sets `CRYSTAL_DATA_DIR` to a tmp directory for that file; the
  stray directory was removed.

### Ollama (reference provider) cost tracking fix

The user reported that streamed ollama requests via the reference provider
recorded nothing (no bucket in the report, no footer total) while ChatGPT
worked. Root cause: `OpenAICompatibleUsageExtension` had no `priority`, so the
wrapper default (100) ran it **after** the cost tracking extension (70). Cost
tracking saw finals with `usage` but no `usage_bucket` (stamped by the usage
extension's finalize) and silently skipped. Fix: `priority: int = 60` on the
usage extension (matching the openai_responses usage extension, which is why
ChatGPT worked).

Verified with an isolated minimal repro against the real local ollama
(`glm-5.2:cloud`), both `stream=True` and `stream=False`: cost rows recorded
under `openai-compatible-localhost`, and the final event message **and** the
persisted session's assistant message carry `cost_session_total_formatted` /
`cost_session_requests`. Reference provider suite (109) and cost-tracking
suite (43) pass; the 23 pyright override errors in the reference provider are
pre-existing (identical count with changes stashed).

Mechanics confirmed while diagnosing (correcting an earlier wrong hypothesis):
the usage **extension** extracts usage, not the provider — its `process_chunk`
stamps the chunk's `usage` into the shared `state["accumulator"]`'s
`_metadata`, and the provider mixin's `finalize` builds the final from that
accumulator. `stream_options.include_usage` reaches the payload via the
`feature-request-options` feature plugin (the provider itself does not forward
`request_options`), so ollama only reports usage when that plugin and the
agent-level `request_options.stream_options.include_usage` are configured.
An experimental provider-side usage capture was reverted; the priority fix
alone is the fix. Repro rows never touched the real store (isolated
`cost_tracking_db_path` + `CRYSTAL_DATA_DIR`); two earlier stray rows in the
real store were deleted. The user's running app instances must be restarted to
pick up the fix; past ollama requests are not backfilled.

### Follow-up: growing summary CSV (completed)

A growing `cost-tracking-summary.csv` is appended beside the SQLite store:
one row per freshly recorded request with `time, bucket, working_directory,
session_id, model, cost, session_total_cost, bucket_total_cost`, plus one
marker row per reset (request columns empty, `bucket_total_cost` 0.0).
Session totals are factual history (footer semantics); bucket totals are
reset-aware (report semantics). Rows append only for freshly inserted store
rows (response-id dedupe applies). Config: `track_cost_tracking_summary_csv`
(default true) and `cost_tracking_summary_csv_path` override; the app
plugin's reset action merges plugin + session config for path resolution.
All CSV writes are best-effort.

Evidence: store unit tests (rolling totals, reset-awareness, marker row,
missing session fields, disable flag, path override, unwritable-path
best-effort), extension unit tests (row appended on record, dedupe, gates),
app-plugin reset test (marker row), integration test through the public
request path (both stream modes) asserting CSV rows beside the temp store,
and a real-ollama streaming run producing the expected row. Suite:
53 passed; ruff/black/pyright clean. Docs updated in
`plugins/cost-tracking/docs/development/overview.md`.

### Follow-up requested separately (tracked in its own task)

Per-model token rates for the reference provider, an ollama pricing sync
script, and `$include` config merging are tracked in
`tasks/20260920-per-model-rates-config-include.md` (assigned to another
agent).

## Checkpoint 2 execution plan — footer cost breakdown + report depth

Status: Approved

### Outcome

1. **Footer cost breakdown, two UI-configurable modes.** The chat footer
   shows, for the current session, the cost total and request count plus a
   per-item cost breakdown. Two modes, selectable in the UI; both modes
   include ALL applicable items (input, cached input, cache write, output —
   the earlier examples were illustrative, not exhaustive):
   - **Totals mode:** `total: $150 · input: $10 · cached input: $77 ·
     cache write: $5 · output: $63 · requests: 330` — per-item cost
     totals, each a separate metadata field.
   - **Averages mode:** `total: $150 · requests: 330 · average: $0.454 ·
     input: $0.303 · cached input: $0.2333 · cache write: $0.015 ·
     output: $0.19` — per-request average cost per item.
   Items without data are skipped (e.g. a provider that reports only a
   total cost shows only total + requests). Works at least for
   openai_responses (ChatGPT + API) and the reference provider (ollama).
   ChatGPT per-item costs ARE available: the estimate is computed from
   usage and estimated cached tokens via the manual ChatGPT pricing table,
   so ChatGPT gets input/cached/output items (cache write when reported).
2. **Report depth.** The "Show cost report" action additionally lists the
   top 10 sessions by cost (project + session id + total) and the top 5
   projects by cost (working directories resolved to project names via
   `~/.crystal/projects.json`, falling back to the raw path), over the
   reset-aware window.

### Approach

1. **Per-item cost computation (provider usage extensions).** Both usage
   extensions already split tokens into billable categories and apply a
   price table; expose the per-item components:
   - `openai_responses`: `estimate_usage_cost` already computes ordinary
     input / cached read / cache write / output components from the
     pricing snapshot. Add a breakdown-returning variant (keep the
     existing single-figure API intact) and stamp it into the internal
     usage metadata (e.g. `_metadata.usage_cost_breakdown` with
     `input` / `cached` / `cache_write` / `output` cost values, omitting
     items without data).
   - `reference-openai-compatible-provider`: `_usage_cost` computes from
     `token_rates` (input / cached / completion). Produce the same
     breakdown shape; cache-write cost is omitted while no cache-write
     rate exists (skip-if-unavailable rule). Per-model rates from
     `tasks/20260920-per-model-rates-config-include.md` plug in here when
     they land — complementary, not blocking.
2. **Store schema.** Record the per-item cost breakdown per request.
   Add dedicated cost columns (`input_cost`, `cached_cost`,
   `cache_write_cost`, `output_cost`) next to `estimated_cost` /
   `actual_cost`, with an `ALTER TABLE`-based migration for existing
   databases (check `PRAGMA table_info`, add missing columns). Extend
   `record_request_usage` and `session_totals` (per-item session sums).
3. **Cost tracking extension.** Record the breakdown; stamp
   session-scoped per-item totals (totals mode) or per-item averages
   (averages mode = session item sum / request count) as separate metadata
   fields plus a preformatted footer string. Mode comes from the
   `cost_status_breakdown` config key (`"totals"` default / `"averages"`),
   declared in `get_config_schema` so it is selectable through the existing
   plugin-config override UI and persisted in agent config. Items with no
   recorded data are omitted from both metadata and the formatted string.
4. **Status bar element.** Render the formatted breakdown via the existing
   single data-path + template mechanism; `show_cost_status_total` keeps
   gating the footer as a whole.
5. **Report depth.** Store queries for top 10 sessions (group by
   working_directory + session_id) and top 10 projects (group by
   working_directory), rendered as tables in the report action; project
   display names resolved via `~/.crystal/projects.json`.
6. **Tests + docs.** Unit tests at each layer (pricing breakdown variants,
   store migration + aggregations, extension stamps/mode switch/gates,
   report rendering), extend the public-path integration test (both stream
   modes), and update the plugin overview docs.

### Implementation decisions and open questions

- **Reasoning (resolved):** not reported as a cost line; only output is
  shown (reasoning tokens are billed within the output rate).
- **Top-lists window (resolved):** reset-aware, covering the same request
  set as the report's overall total (each bucket's requests since its last
  reset).
- **Default mode (resolved):** `"totals"`.
- **Report depth (resolved):** top 10 sessions and top 5 projects.
- **Breakdown storage (decision, reversible).** Dedicated columns (not a
  JSON blob) so per-item aggregation stays plain SQL; migration must be
  best-effort and idempotent for existing user databases.
- **ChatGPT backend.** When ChatGPT reports no per-item prices for the
  active model, only total + requests render — per the
  skip-if-unavailable rule; no synthetic per-item split.
- Session-scoped footer (existing scope); report-level depth stays in the
  report action.

### Documentation

- `plugins/cost-tracking/docs/development/overview.md`: footer breakdown
  modes, new config key and metadata fields, store schema, report depth.
- `plugins/openai_responses` and reference provider docs: the stamped
  `usage_cost_breakdown` metadata contract.
- Status bar element contract unchanged (single data path + template).

### Task checklist

- [x] Confirm open questions (reasoning line, top-lists window, default
      mode).
- [x] openai_responses: breakdown variant of cost estimation + stamps.
- [x] Reference provider: breakdown from token_rates + stamps.
- [x] Store: per-item columns + migration + aggregation queries + tests.
- [x] Extension: record breakdown, stamp totals/averages by mode, config
      key + schema, formatted footer string + tests.
- [x] Report action: top 10 sessions + top 5 projects + tests.
- [x] Extend integration test (both stream modes); run openai_responses
      and reference provider suites.
- [x] Lint (ruff/black), pyright, full cost-tracking suite.
- [x] Update docs; record completion notes.

### Requirement verification

- Per-item costs: provider-level unit tests asserting the breakdown for a
  seeded usage payload (both providers), at the metadata boundary the cost
  extension consumes.
- Store: unit tests for migration on a pre-existing schema, per-item
  session sums, and top-list queries.
- Footer: extension unit tests asserting the per-item metadata fields and
  formatted string in both modes, the skip-if-unavailable rule, and the
  gates; the public-path integration test (both stream modes) asserts the
  breakdown reaches the final assistant message through the real pipeline.
- Report: app-plugin unit tests asserting the top-10 tables and project
  name resolution; one integration-level check through the action surface.
- Manual confirmation in the user's running app for both providers
  remains the final checkpoint sign-off.

### Additional implementation verification

- The openai_responses ChatGPT manual suites assert footer metadata;
  re-run them after the stamp changes.
- The ollama (reference provider) path is covered by the same extension;
  verify via the reference provider suite plus one real-ollama run.
- Existing user databases: verify the migration on a copy of a real store
  before shipping.


## Checkpoint 2 implementation notes

- **Per-item cost source.** Both providers stamp `usage_cost_breakdown`
  (`{input, cached, cache_write, output}`, zero/absent items omitted) into
  internal `_metadata` next to `usage_bucket`. openai_responses:
  `estimate_usage_cost_breakdown` shares `_usage_cost_components` with
  `estimate_usage_cost` (which now sums the breakdown-equivalent single
  expression, preserving its exact historical float math — summing the
  per-item values instead produced last-ulp drift that broke formatted-cost
  assertions). ChatGPT mode gets items from usage + estimated cached tokens
  via the manual pricing table, so ChatGPT per-item costs ARE available
  (correction to an earlier note). Reference provider: `_rate_token_split`
  splits prompt tokens into ordinary/cached/cache-write (cache-write carved
  out only when a `cache_write` rate is configured — otherwise historical
  behavior where cache-write tokens stay ordinary input) and resolves
  effective rates; `_usage_cost` and `_cost_breakdown_from_rates` share it,
  so items always sum to the total.
- **Store.** New REAL columns `input_cost`/`cached_cost`/`cache_write_cost`/
  `output_cost`; `_ensure_schema` migrates pre-existing databases via
  `PRAGMA table_info` + `ALTER TABLE`. `session_totals` returns per-item
  session sums. `top_sessions`/`top_projects` aggregate over the
  reset-aware window (each bucket's requests since its last reset — the
  same set as the report's overall total), skipping rows without
  working_directory/session_id.
- **Footer.** `cost_status_breakdown` config key (`totals` default /
  `averages`) declared in the schema (UI-selectable). Stamps:
  `cost_session_<item>_cost` (+ `_avg` in averages mode),
  `cost_session_average_cost`, and `cost_session_breakdown_formatted`; the
  status-bar element now renders the breakdown string (template
  `{{data}}`). Promotion is prefix-based (`cost_*`) so new keys flow
  automatically. Skip-if-unavailable: items with no recorded data are
  omitted from both fields and the string.
- **Report.** Top 10 sessions (project + session id) and top 5 projects;
  project names resolved from `projects.json` under `CRYSTAL_DATA_DIR`
  (default `~/.crystal`), falling back to raw paths.
- **Pyright.** The refactor fixed two pre-existing `Optional[float]`
  multiplication errors in `estimate_usage_cost`; changed-file error count
  is now below the pre-change baseline (12 vs 14). Remaining errors are
  pre-existing override-conformance issues.
- **Verification note.** Running `pytest plugins/cost-tracking/tests
  plugins/reference-openai-compatible-provider/tests` as ONE command is not
  a valid path: pytest then uses a single config and loses the reference
  package's `not integration` default filter, executing real-ollama
  integration tests (looks like a hang; it is real API traffic). Per-package
  runs remain the verification form.

## Checkpoint 2 completion notes

Outcome: delivered and verified. The footer shows the session cost total,
request count, and per-item cost breakdown in two UI-selectable modes
(totals/averages, `cost_status_breakdown`), with all applicable items and
skip-if-unavailable semantics; the report lists the top 10 sessions and
top 5 projects over the reset-aware window with project names resolved.

Requirement evidence:

- openai_responses per-item costs: pricing unit tests (items, zero-omission,
  None vs empty-mapping semantics, sum == total) and usage-extension tests
  in both API and ChatGPT modes (ChatGPT items from usage + estimated
  cached tokens).
- Reference provider per-item costs: `_cost_breakdown_from_rates` unit tests
  (items, cache-write carve-out and skip, sum == total) and finalize stamp
  tests (breakdown stamped from token_rates; none for provider-reported
  cost).
- Store: migration test against a pre-item-columns schema, per-item session
  sums, reset-aware `top_sessions`/`top_projects` with cross-bucket union,
  limits.
- Footer: extension unit tests for both modes, all-item inclusion,
  skip-if-unavailable, request-count division, gates, element shape, config
  schema; public-path integration test (both stream modes) asserts the
  breakdown metadata and store item columns.
- Report: app-plugin tests for the top tables and project-name resolution
  (with fallbacks).
- Suites: cost-tracking 63 passed; reference provider 113 passed (61
  deselected); openai_responses 481 passed (93 deselected); manual ChatGPT
  suite 10 passed against the real login; ruff/black clean on changed
  files; pyright on changed files below the pre-change baseline.
- Real-endpoint check: real ollama (`glm-5.2:cloud`, official rates)
  streaming request produced `Total: $0.000355 · input: $0.000014 · cached
  input: $0.000003 · output: $0.000339 · requests: 1` in totals mode and
  the averages-mode equivalent.

Deviations: report depth is top 10 sessions + top 5 projects (user
correction of the earlier top-10-projects draft). Reasoning tokens are not
a cost line (billed within output). No unresolved scope remains for this
checkpoint; the user's in-app confirmation is the final sign-off.
## Checkpoint 2 correction plan — separate breakdown fields

Status: Approved

Tracking note: the checkpoint 2 implementation as originally built (combined
`cost_session_breakdown_formatted` footer string, mode-dependent stamping)
is committed first as its own commit; this correction is implemented
afterwards and committed separately, so both versions are tracked in git
history.

### Outcome

Corrects the footer breakdown to the intended design: the existing total
footer stays unchanged, and the breakdown items are separate fields with
separate UI elements; the platform renders and orders them.

1. **Total footer unchanged.** The original `status_bar` element stays
   exactly as before: `data: metadata.cost_session_total_formatted`,
   `template: "Total: {{data}}"`, with its exists condition.
2. **Separate fields, raw and formatted.** Every breakdown item is stamped
   as its own metadata field pair, always (both totals and averages are
   stored regardless of config; the config only controls display):
   - Totals: `cost_session_input_cost` + `cost_session_input_cost_formatted`
     (same for `cached`, `cache_write`, `output`).
   - Averages: `cost_session_input_cost_avg` + `_formatted` (same for the
     other items), plus `cost_session_average_cost` + `_formatted`.
   - `cost_session_requests_formatted` (raw `cost_session_requests` exists).
   - The combined `cost_session_breakdown_formatted` string is removed
     (it was the misunderstanding; unreleased, created this session).
3. **UI config "Total usage breakdown"** — key `total_usage_breakdown`
   (replacing `cost_status_breakdown`), choices `none` / `totals` /
   `averages`:
   - `none`: only the unchanged total element.
   - `totals`: total, then `input: {{data}}`, `cached input: {{data}}`,
     `cache write: {{data}}`, `output: {{data}}`, `requests: {{data}}` —
     one element per field, each with an exists condition on its formatted
     path so unavailable items do not render.
   - `averages`: total, then `requests:`, `average:`, then the per-item
     average elements in the same item order.
   - Element order follows the list order returned by `get_ui_elements`
     (verified: the core appends elements in order and the terminal renders
     status-bar elements in that order).
4. **Stamping is mode-independent.** `_breakdown_metadata` no longer takes
   a mode; it always stamps the complete field set when item data exists.
   Only `get_ui_elements` reads the config.

### Approach

1. Extension: simplify `_breakdown_metadata` to always stamp totals +
   averages + formatted variants; delete the combined-string builder.
2. Extension: restore the original total element as the first element;
   append the breakdown elements per the config choice with fixed labels
   and exists conditions.
3. Config schema: replace `cost_status_breakdown` with
   `total_usage_breakdown` (select with `none`/`totals`/`averages`,
   label "Total usage breakdown").
4. Tests: rewrite the breakdown stamp tests (always-stamped field pairs),
   the element tests (element set + order per choice), the schema test, and
   update the integration test to assert the separate fields.
5. Docs: rewrite the footer section of the plugin overview.

### Implementation decisions and open questions

- **Default choice (resolved).** `none` — the footer stays unchanged
  until the user enables the breakdown in the UI.
- **Config key (resolved).** `total_usage_breakdown`, label
  "Total usage breakdown"; the previous `cost_status_breakdown` key is
  unreleased and gets renamed.
- **Combined string removal (resolved).** Remove
  `cost_session_breakdown_formatted` entirely.
- **Element labels (resolved).** `input:`, `cached input:`, `cache write:`,
  `output:`, `requests:`, `average:` — matching the user's example
  wording; formatting stays `$%.6f`.
- Requests element appears only when a breakdown mode is enabled (the
  unchanged default footer shows just the total).

### Documentation

- `plugins/cost-tracking/docs/development/overview.md`: footer section
  rewritten for the separate fields, the new config key and choices, and
  the element ordering contract.

### Task checklist

- [x] Confirm the open questions.
- [x] Rework `_breakdown_metadata` (always-stamped raw+formatted pairs).
- [x] Rework `get_ui_elements` (unchanged total first; per-choice elements).
- [x] Replace the config schema key.
- [x] Update unit, element, schema, and integration tests.
- [x] Lint (ruff/black), pyright, cost-tracking suite; re-run the
      openai_responses and reference provider suites.
- [x] Update docs; record completion notes.

### Requirement verification

- Stamp boundary: extension unit tests asserting the full field set
  (totals + averages, raw + formatted) is stamped whenever item data
  exists, independent of the config choice.
- Element boundary: extension unit tests asserting the exact element list
  and order for `none`, `totals`, and `averages`, with exists conditions.
- Public path: the integration test (both stream modes) asserts the
  separate formatted fields on the final assistant message.
- Real-endpoint spot check (ollama) after implementation.

### Additional implementation verification

- The manual ChatGPT suites assert footer metadata; re-run if the stamp
  changes affect them (additive renames only expected).


## Checkpoint 2 correction completion notes

Outcome: delivered and verified. The total footer is unchanged; breakdown
items are separate raw+formatted metadata fields (totals and averages both
always stamped); the `total_usage_breakdown` UI config ("Total usage
breakdown", choices none/totals/averages, default none) selects which
status-bar elements are contributed, in fixed list order that the platform
renders.

Requirement evidence:

- Stamp boundary: `test_breakdown_stamps_totals_and_averages_fields`
  asserts the complete raw+formatted field set is stamped even with the
  config at `none`; `test_breakdown_skips_unavailable_items` asserts item
  fields are absent without breakdown data while session-level fields
  remain; `test_breakdown_averages_divide_by_request_count` covers
  multi-request sums and averages.
- Element boundary: `test_status_bar_element_and_gate` (default/none keeps
  only the unchanged total element; gate returns []),
  `test_status_bar_elements_totals_choice` (6 elements in order),
  `test_status_bar_elements_averages_choice` (7 elements in order).
- Config schema: `test_config_schema_defaults` asserts the key, label,
  default `none`, and options.
- Public path: integration test (both stream modes) asserts the separate
  formatted fields on the final assistant message and the absence of the
  removed combined string.
- Suites: cost-tracking 64 passed; openai_responses 481 passed; reference
  provider 113 passed; ruff/black clean; pyright clean on the plugin.
- Real-endpoint check (ollama, `glm-5.2:cloud`): `none` renders only
  `Total: $0.000289`; `totals` renders `Total: … input: … cached input: …
  output: … requests: 1` (6 elements, cache write skipped — no data);
  `averages` renders `Total: … requests: 1 average: … input: … cached
  input: … output: …` (7 elements).

Tracking: the original combined-string implementation is commit
`75bd9ed8` ("Add cost breakdown footer and report depth"); this correction
is the follow-up commit on top of it.

The manual ChatGPT suites were not re-run for the correction: the stamp
changes are additive renames of cost-tracking metadata those suites do not
assert, and the ChatGPT breakdown path itself is unchanged (covered by
the openai_responses unit tests).