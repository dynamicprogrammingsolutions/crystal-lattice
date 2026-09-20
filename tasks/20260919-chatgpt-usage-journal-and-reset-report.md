# ChatGPT usage journal, history, and reset-aware usage report

Add persistent, append-only tracking of ChatGPT plan usage on top of the
existing `openai_responses` rate-limit capture and usage/cost estimation, and
expose it in the UI via the `chatgpt-auth-app` application plugin: estimated
usage contributing to the ChatGPT plan, a history of usage percentages, a
manual-reset marker with post-reset totals, date-based inspection of the
journal, and per-request records pairing actual usage with the plan-limit
state observed on the same response.

## Requirements checklist

- [ ] ChatGPT-backed requests append a per-request journal record containing
      the request's actual usage (token counters), its estimated cost, and the
      rate-limit snapshot observed on that same response (used/remaining
      percentage and next reset time per window), so usage contributors,
      usage changes, and reset-time changes can be inspected and reconstructed.
- [ ] Every captured ChatGPT rate-limit snapshot is appended to the journal
      (history of usage percentages), including snapshots from requests that
      do not produce a usage record.
- [ ] The journal is append-only NDJSON; records are never rewritten or
      truncated by the platform.
- [ ] Estimated usage that contributes to ChatGPT plan usage is accumulated
      across requests and sessions (journal-derived totals), not only per
      session.
- [ ] A UI action resets usage tracking by appending a manual reset marker to
      the journal.
- [ ] A UI action shows a usage report with totals accumulated since the last
      reset marker (request count, token totals, estimated cost) plus current
      left percentage and next reset time per window.
- [ ] The usage report supports narrowing by a date range: `from`/`to` are
      simple text inputs accepting a date and optionally a time, interpreted
      in the server's own timezone; the narrowed report runs as a follow-up
      action from the report display.
- [ ] The journal can be inspected by date (records, totals, and the left
      percentage / next reset time at a specific point in time) via the
      NDJSON file and a CSV export path.
- [ ] Journaling is ChatGPT auth mode only; API-key requests keep the existing
      per-session usage/cost behavior unchanged.
- [ ] Journaling failures never break the request pipeline.
- [ ] New behavior is covered by unit tests, and the existing manual
      integration tests are updated to verify real end-to-end journal growth.

## Scope and decisions (user-confirmed)

- **Manual reset** means a user-initiated reset of the *tracking totals*: a
  marker appended to the journal. The journal itself is never truncated, so
  pre-reset history remains inspectable. ChatGPT plan windows themselves are
  not resettable by the platform.
- **Scope**: ChatGPT auth mode only for now. Other providers may be added
  later; keep the design extensible but do not generalize in this task.
- **Retention**: append-only, no automatic rotation. Date-based filtering and
  CSV export are the inspection path.

## Supporting details (verified facts)

- Rate-limit capture: `plugins/openai_responses/src/openai_responses_plugins/chatgpt_rate_limits.py`
  parses `x-codex-*` headers (`parse_all_rate_limit_headers`) and
  `persist_rate_limit_snapshots` writes only the **latest merged snapshot** to
  `auth/chatgpt-rate-limits.json`. No history is kept today.
- The provider captures headers at stream start:
  `openai_responses_provider.py:599-628` (`_capture_chatgpt_rate_limits`,
  `_capture_chatgpt_rate_limits_from_stream`), invoked at lines 2842/2848 of
  `stream_api`.
- Per-request usage and estimated cost are computed in
  `plugins/openai_responses/src/openai_responses_plugins/openai_responses_usage_extension.py`
  (`_build_usage_metadata`, lines 937-1171), including the ChatGPT
  turn-aware cached-token estimate and API-equivalent cost. Both the
  streaming (`process_chunk`) and non-streaming (`finalize`) paths converge
  on `_build_usage_metadata`, so it is the single point where a response's
  usage is finalized.
- UI today: `plugins/chatgpt-auth-app/src/chatgpt_auth_app/__init__.py`
  (`ChatGPTAuthAppPlugin`) renders "Show ChatGPT account status"
  (`show_account_status`, lines 1098-1160) from the latest rate-limits JSON
  ("`98% left` (resets ...)").
- The provider's `stream_api` and the extension's `process_chunk` share the
  **same state dict instance** (`core/python/agent_core/plugin/provider.py:665-673`),
  so the provider can hand the exact per-response rate-limit snapshot to the
  usage extension through shared state (no file races).
- Cost-estimation caveats for ChatGPT mode are documented in
  `plugins/openai_responses/docs/development/cost-estimation.md`; the dollar
  value is an API-equivalent estimate, not an invoice amount.
- Plugin registration: `plugins/openai_responses/agent_plugin.json` (provider,
  features, extensions) and `plugins/chatgpt-auth-app/agent_plugin.json`
  (application plugin). No new plugin projects are needed.
- Journal path resolution should mirror `resolve_rate_limits_path`
  (`chatgpt_rate_limits.py:16-29`): explicit config key, then credentials-path
  sibling, then `CONFIG_DIR`, then cwd.

## Execution plan

Status: Approved

### 1. New journal module (features: percent history, date inspection, request records)

Create `plugins/openai_responses/src/openai_responses_plugins/chatgpt_usage_journal.py`:

- `resolve_usage_journal_path(config)` → `auth/chatgpt-usage-journal.ndjson`
  (sibling of `chatgpt-rate-limits.json`; override key
  `chatgpt_usage_journal_path`; same resolution chain as rate limits).
- Append-only NDJSON, one JSON object per line, three record types:
  - `rate_limit_snapshot` — timestamp, plan_type, full parsed snapshots
    (per limit_id: primary/secondary `used_percent`, `window_minutes`,
    `resets_at`, credits).
  - `request_usage` — timestamp, response_id, model, service_tier, token
    counters (input, estimated-cached, cache_write, output, reasoning),
    estimated cost, and the rate-limit snapshot observed on the same response
    (with derived remaining percent and reset times).
  - `usage_reset` — manual reset marker.
- Reader helpers: `iter_records(path, from_dt=None, to_dt=None)`,
  `totals_since_last_reset(path)`, `latest_snapshot_at(path, dt)`
  (left percentage / next reset at a point in time), `export_csv(...)`.
- All writes go through a module-level lock and are best-effort: failures are
  logged and swallowed.

### 2. Provider change (small)

In `_capture_chatgpt_rate_limits`: after persisting the latest snapshot as
today, also

- stash the parsed snapshots + capture time into shared state in place
  (`state["_openai_responses_chatgpt_rate_limit_snapshots"]`), and
- append the `rate_limit_snapshot` journal record.

### 3. Usage extension change (estimated plan usage accumulation)

In the ChatGPT branch of `_build_usage_metadata` (single convergence point;
exactly one record per response): append a `request_usage` journal record using
the already-computed effective usage (including the estimated cached tokens)
and estimated cost, plus the snapshot from shared state (fallback: read the
latest rate-limits JSON). Gated by a new config key `track_chatgpt_usage_journal`
(default on). Wrapped in try/except so journaling can never break a request.

### 4. UI in `chatgpt-auth-app`

- New action `show_usage_report` ("Show ChatGPT usage report", session action):
  - Default report (no params): totals since the last reset marker (request
    count, token totals, estimated cost), current left percentage and next
    reset time per window, and a percent-history summary (first/last/min/max
    per window since the reset).
  - The report display includes a **follow-up action** to narrow by date
    range: `from`/`to` presented as simple text inputs accepting a date and
    optionally a time (e.g. `2026-09-19` or `2026-09-19 14:30`), interpreted
    in the **server's own timezone**. Running the follow-up action re-renders
    the report narrowed to `[from, to]`.
  - Invalid date text produces a friendly error display, not an exception.
- New action `reset_usage_tracking` ("Reset ChatGPT usage tracking") with a
  confirm dialog: appends the `usage_reset` marker. After a manual reset, the
  report shows totals accumulated since the marker.
- Extend `show_account_status` with an "Estimated usage since reset" section.
- Journal path resolution reuses the same config plumbing as the rate-limits
  path (`rate_limits_path` sibling).

### 5. Date-based inspection (file path)

- The NDJSON journal is the source of truth; no second derived-state file.
- New CLI script `plugins/openai_responses/scripts/inspect_chatgpt_usage_journal.py`:
  `--from`/`--to` filtering, point-in-time percent lookup, optional CSV export.

### 6. Tests

- New unit tests `plugins/openai_responses/tests/test_openai_responses_chatgpt_usage_journal_unit.py`:
  record append/read, reset-marker semantics, totals since reset, date
  filtering, percent-at-point, CSV export.
- Extend `test_openai_responses_chatgpt_rate_limit_capture_unit.py`: provider
  appends snapshot records and stashes them into state.
- Usage extension unit test: `request_usage` record appended with snapshot
  pairing (state-provided snapshot preferred over file).
- `chatgpt-auth-app` unit tests: report rendering, reset marker, date-range
  narrowing incl. date+time parsing in server timezone and invalid-input
  handling.
- Update manual integration tests
  (`test_openai_responses_chatgpt_usage_manual_integration.py`,
  `test_chatgpt_auth_account_status_manual_integration.py`) to verify real
  end-to-end journal growth.

### 7. Documentation

- New `plugins/openai_responses/docs/development/usage-journal.md` + index
  entry; cross-reference in `cost-estimation.md`.
- `chatgpt-auth-app` README: document the new actions and the journal file.
- Config schema additions for `chatgpt_usage_journal_path` and
  `track_chatgpt_usage_journal`.

### Implementation decisions and open questions

Decisions (resolved):

- Journal is ChatGPT-only; keep record schema provider-agnostic enough to
  extend later, but do not generalize now.
- Append-only, no rotation; inspection script provides filtering.
- Manual reset = journal marker; totals are derived from the journal, so they
  survive restarts and span sessions.
- Per-response snapshot pairing via shared provider state (verified same dict
  instance), with the rate-limits file as fallback.
- `from`/`to` are simple text inputs parsed in the server's timezone; the
  narrowed report is a follow-up action from the report display.

Open questions: none blocking. Local, reversible choices (exact record field
names, report line wording) are left to implementation.

### Documentation

- Audience: plugin users and maintainers of `openai_responses` and
  `chatgpt-auth-app`.
- Development docs under `plugins/openai_responses/docs/development/` (new
  usage-journal page); user-facing action documentation in the
  `chatgpt-auth-app` README.

### Task checklist

- [x] Journal module with append/read/reset/date-filter/percent-at-point/CSV helpers
- [x] Provider: stash snapshots in state + append `rate_limit_snapshot` records
- [x] Usage extension: append `request_usage` records (ChatGPT mode, config-gated, failure-safe)
- [x] `chatgpt-auth-app`: `show_usage_report` action with follow-up date-range narrowing
- [x] `chatgpt-auth-app`: `reset_usage_tracking` action with confirm dialog
- [x] `chatgpt-auth-app`: extend `show_account_status` with since-reset usage
- [x] CLI inspection script with CSV export
- [x] Unit tests (journal, provider capture, usage extension, auth-app actions)
- [x] Manual integration test updates
- [x] Documentation updates

### Requirement verification

- Per-request records with plan state (req 1): unit test asserting a
  `request_usage` record contains usage, estimated cost, and the same
  response's snapshot; manual integration test shows real records.
- Percent history (req 2): unit test asserting consecutive snapshots append
  as separate records, including a request that fails before usage.
- Append-only (req 3): unit test asserting repeated writes only add lines and
  no API rewrites or truncates records.
- Cross-session accumulation (req 4): unit test deriving totals across
  multiple appended records independent of any session.
- Manual reset via UI (req 5): auth-app unit test invoking the action and
  asserting a marker record.
- Post-reset totals in UI (req 6): auth-app unit test asserting the report
  shows only post-marker records.
- Date-range narrowing via follow-up action (req 7): auth-app unit test with
  date and date+time inputs in server timezone, plus invalid-input handling.
- Date-based file inspection (req 8): unit test of reader helpers and CSV
  export; script smoke run.
- ChatGPT-only scope (req 9): unit test asserting no journal records for
  API-key-mode requests.
- Failure safety (req 10): unit test simulating an unwritable journal path
  asserting requests still succeed.
- Test coverage (req 11): default package-local pytest runs for
  `plugins/openai_responses` and `plugins/chatgpt-auth-app` pass.

### Additional implementation verification

- `pytest plugins/openai_responses/tests -q` and
  `pytest plugins/chatgpt-auth-app/tests -q` (default, non-integration).
- `ruff check` and `black` on changed Python files; `pyright` where practical.
- Manual integration suites updated but run only when ChatGPT credentials are
  available (report as "not run" otherwise).

## Implementation Notes

- The default attachment upload mode rebinds the provider `state` dict inside
  `stream_api` before the streaming worker starts, so the rate-limit snapshot
  stash targets the caller-owned dict captured at function entry
  (`capture_state`), not the rebound copy.
- The provider's own `process_chunk` copies state per chunk; copies made after
  the stream-creation stash inherit the snapshot, so the usage extension sees
  it on the normal ChatGPT streaming path. The rate-limits JSON remains the
  fallback (e.g. attachment-upload rebinding edge cases).
- The `chatgpt-auth-app` journal reader is intentionally self-contained
  (`chatgpt_auth_app/usage_journal.py`) because the plugin has no runtime
  dependency on `openai_responses`; the NDJSON record format is the shared
  contract.
- Report percent history is scoped to the report window (since reset, or the
  requested date range), consistent with the totals scope.
- The CLI script's "latest usage limits" is bounded by `--to` when no `--at`
  is given so narrowed runs reflect the end of the range.
- Removed a pre-existing unused `time` import in `chatgpt_auth_app/__init__.py`
  surfaced by ruff.
- The default field renderers in
  `packages/frontend-rn-components/src/ApplicationActionDialog.tsx` had no
  stable test identifiers, so plugin-declared embedded-form fields could not
  be targeted by testID in native UI tests. Added
  `action-form-input-<field_name>` to both default text-input renderers
  (shared-package tests pass) and documented the convention in
  `plugins/docs/actions.md`.
- One-off Detox verification was attempted on the iOS simulator against the
  embedded Python runtime (regenerated `crystal_lattice_app.zip` with the new
  plugin code, rebuilt the Release app). The run reached session creation but
  the `openai-codex` agent did not appear (profile configuration step did not
  take effect in the harness flow); the user chose to skip the verification
  and the one-off test file was removed. Failure screenshots remain under
  `mobile/crystal-lattice-control-rn/artifacts/detox/`.
- Side finding: `mobile/crystal-lattice-control-rn/scripts/prepare_ios_python_runtime.py`
  deletes the tracked `ios/CrystalLatticePythonRuntime/Resources/reviewer-proxy-ca.pem`
  when it regenerates `Resources/` (only `crystal_lattice_app.zip` is restored),
  which breaks the next Xcode build. The file was restored from git; the
  script fix is offered as follow-up.

## Completion Notes

Outcome: implemented and verified in full at the plugin/backend level; the
one-off mobile Detox verification requested during execution was attempted,
then skipped by user decision.

Requirement evidence:

- Per-request records pairing usage, estimated cost, and the same response's
  rate-limit snapshot: `test_openai_responses_usage_journal_extension_unit.py`
  (state-stash pairing, file fallback, finalize path, response_id).
- Percent history including non-usage requests:
  `test_openai_responses_chatgpt_rate_limit_capture_unit.py`
  (snapshot journaling at stream creation) plus journal percent-history tests.
- Append-only semantics: journal unit tests assert repeated appends only add
  lines; no rewrite/truncate API exists.
- Cross-session accumulation: `totals_since_last_reset` derives totals from
  the journal independent of any session (unit-tested).
- Manual reset via UI: auth-app test invokes `reset_usage_tracking` and
  asserts the marker record; post-reset report shows only post-marker usage.
- Post-reset totals in UI: `show_usage_report` test asserts totals, current
  left percentage, and percent-history lines scoped since the reset.
- Date-range narrowing as a follow-up action with simple text inputs in the
  server timezone: auth-app tests cover date-only, date+time, range
  prefill/defaults, and friendly invalid-input error display; the report
  embeds the `from`/`to` form and the `Apply date range` `run_action` with
  `$form.*` param mapping.
- NDJSON/CSV date-based inspection: journal unit tests cover inclusive
  filtering, point-in-time snapshot lookup, and CSV export; the CLI script
  was smoke-run (default, narrowed, `--at`, `--csv`).
- ChatGPT-only scope: provider and extension tests assert no capture/journal
  in API mode; auth-app gating test asserts warning displays for
  non-ChatGPT sessions.
- Failure safety: extension test with an unwritable journal path still
  attaches usage metadata; journal append failures are swallowed (unit
  tested).
- Account status now includes "Estimated usage since reset" (auth-app test).

Verification performed:

- `pytest plugins/openai_responses/tests -q`: 451 passed (default markers).
- `pytest plugins/chatgpt-auth-app/tests -q -m "not manual_integration"`:
  13 passed.
- `npm --workspace @crystal-lattice/frontend-rn-components test`: 73 passed
  (after the testID addition).
- `ruff check` and `black` on all changed Python files: clean.
- CLI inspection script smoke run with a synthetic journal.

Verification not run (reported, not skipped silently):

- Manual integration suites
  (`test_openai_responses_chatgpt_usage_manual_integration.py`,
  `test_chatgpt_auth_account_status_manual_integration.py`) were extended with
  journal assertions but require saved ChatGPT credentials; not run in this
  session.
- The one-off Detox UI verification was attempted (see Implementation Notes)
  and then skipped by user decision; no permanent test was added.

Deviations/findings:

- Provider snapshot stash targets the caller-owned state dict captured at
  `stream_api` entry (attachment-upload mode rebinds `state`); documented in
  Implementation Notes.
- The `chatgpt-auth-app` journal reader is self-contained; the NDJSON record
  format is the cross-package contract.
- Report percent history is scoped to the report window (since reset or the
  requested range), matching the totals scope.
- Removed a pre-existing unused `time` import in `chatgpt_auth_app/__init__.py`.
- Documentation assessment requested during execution: the plugin-driven UI
  docs (`plugins/docs/actions.md` embedded display forms, `$form.*` mapping,
  follow-up action kinds) match the mobile implementation; the gap was in code
  (missing stable field testIDs), fixed and documented as noted above.

Unresolved/deferred:

- Mobile Detox verification of the report/follow-up interaction (see
  Post-completion follow-up).
- `prepare_ios_python_runtime.py` deleting the tracked
  `reviewer-proxy-ca.pem` resource (bug; fix offered).

## Post-completion follow-up

- Re-run the one-off Detox verification when convenient: rebuild the embedded
  runtime app, configure the openai profile (chatgpt mode) via the embedded
  settings UI, then exercise `chatgpt_auth_show_usage_report` -> form ->
  `Apply date range` follow-up and the reset confirm dialog. The prior
  attempt stalled at the profile-configuration step; the failure screenshots
  are under `mobile/crystal-lattice-control-rn/artifacts/detox/`.
- Fix `prepare_ios_python_runtime.py` to preserve/copy
  `reviewer-proxy-ca.pem` when regenerating `Resources/` so the next
  `detox build` does not fail on the missing resource.

### Follow-up verification (same task, later session)

- Ran both manual integration suites with the real login via
  `CHATGPT_TEST_STATE_DIR="$HOME/.crystal"`
  (`OPENAI_RESPONSES_CHATGPT_MODEL=gpt-5.6-luna` for the account-status test):
  - `test_openai_responses_chatgpt_saved_login_usage_multi_turn_tool_loop`:
    passed (18s) — journal grew with one `request_usage` record per assistant
    response, each paired with its rate-limit snapshot.
  - `test_chatgpt_account_status_after_real_request`: passed (32s) — journal
    created, account status shows "Estimated usage since reset", usage report
    renders totals/percent history with the wired date-range follow-up form.
- The real journal (`~/.crystal/auth/chatgpt-usage-journal.ndjson`) also
  captured the user's own interactive `codex-openai` usage automatically
  (records with model `gpt-5.6-sol` interleaved with the test runs), and the
  CLI inspection script renders correct totals/limits/history from it.

### Evaluation-runner tracking assessment

The maintainer agent-evaluation framework's Crystal Lattice runner
(`maintainer/agent-evaluation/suites/documentation_standard/support.py`)
drives the production `AgentApplication.send_request` path with the projected
real config (`~/.crystal/config.json`), `BUILTIN_PLUGINS` pointing at the repo
checkout, and `CONFIG_DIR` set to `~/.crystal`. The `gpt` profile forces
`auth_mode: chatgpt` on the `codex-openai` agent and keeps the
`openai_responses` plugin (whose `agent_plugin.json` registers
`OpenAIResponsesUsageExtension`). Therefore evaluation runs are tracked
automatically in the same journal: rate-limit snapshots from the provider,
request usage from the extension, resolved to
`~/.crystal/auth/chatgpt-usage-journal.ndjson`. No eval-specific wiring is
needed. Records currently carry `model`/`response_id` but no run-source
label, so eval and interactive usage are merged; an optional
`chatgpt_usage_journal_source`-style label config was offered to the user if
distinguishing them becomes necessary.

### Follow-up addition: session/workspace tracking and summary CSV

Committed baseline first (`d9048808 Add ChatGPT usage journal and report`),
then added (user request):

- `session_id` and `working_directory` (resolved to an absolute path;
  relative values resolved against the server process cwd) on
  `rate_limit_snapshot` and `request_usage` records. The session id comes
  from the request context the core injects into provider state
  (`_request_context`); no core changes were needed. Fields are omitted
  when unavailable (older records stay valid; readers use `.get()`).
- Simplified append-only summary CSV written at the same time as each
  journal record: `time, working_directory, session_id, estimated_cost,
  total_cost, used_percent`. `total_cost` is the estimated cost since the
  most recent reset marker (computed from the journal after the record is
  appended, so it includes the current record; reset rows write 0).
  `used_percent` is the primary-window value carried by the record's
  rate-limit snapshot. Default path `auth/chatgpt-usage-summary.csv` next to
  the journal; gated by `track_chatgpt_usage_summary_csv` (default enabled)
  with `chatgpt_usage_summary_csv_path` override. The auth-app reset action
  appends a zeroed-total reset row through its self-contained writer.
- The full CSV export (`export_journal_csv`) gained `session_id` and
  `working_directory` columns.

Bugs found and fixed during real-login verification:

- The chatgpt-auth-app test configs registered only the provider entry, so
  the usage extension was never loaded in those test apps and their own
  requests were not journaled (earlier manual-test passes were satisfied by
  the shared real journal). Test configs now register
  `OpenAIResponsesUsageExtension` and set `working_directory`.
- Re-finalize/rebuild paths re-journaled old responses: the user's running
  app appended duplicate `request_usage` records for the same response id
  roughly every 30 seconds (visible in the real journal). The extension now
  skips journaling when the response id is already present in the journal,
  so rebuilds cannot duplicate records. The already-running app keeps
  duplicating until restarted with the new code.

Verification: openai_responses suite 466 passed; chatgpt-auth-app unit
suite 14 passed; both manual integration suites re-run with the real
`~/.crystal` login and pass on their own journaled records (session id and
absolute working directory confirmed in both the journal and the summary
CSV); ruff/black clean on changed files. Note: the real journal currently
contains duplicate records written by the pre-dedupe running app; they
inflate since-reset totals until cleaned or superseded by a reset marker.
