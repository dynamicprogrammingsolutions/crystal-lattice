# Persisted session data policy and existing-session sanitization

Introduce a generalized provider-data persistence policy, adopt it for OpenAI
Responses, and sanitize existing live sessions and snapshots so an arbitrary
upstream field cannot create unbounded duplicated session metadata.

## Requirements checklist

- [ ] **PSDP-001** Raw provider responses and provider usage remain available
  transiently for current-turn parsing, usage normalization, cost calculation,
  reasoning, tool, attachment, and continuation processing.
- [ ] **PSDP-002** A reusable persistence-policy engine distinguishes
  structured mappings with explicit retained fields from paths that are
  intentionally allowed to contain large payloads.
- [ ] **PSDP-003** Unknown small provider fields remain compatible by default,
  while oversized values outside declared bulk-data paths cannot enter
  persisted core messages, retained native history, snapshots, backups, or
  final session responses.
- [ ] **PSDP-004** Providers, provider extensions, and features can contribute
  persistence rules through one composable contract rather than adding
  sanitizers at individual streaming, non-streaming, phase, rebuild, and
  checkpoint paths.
- [ ] **PSDP-005** OpenAI Responses persists only supported usage fields and
  derived usage/cost metadata; the rule does not depend on recognizing the
  name `attribution`.
- [ ] **PSDP-006** OpenAI Responses retains legitimate large assistant content,
  tool inputs/results, reasoning and compaction state, attachment references,
  and other explicitly declared continuation data in both core and native
  history.
- [ ] **PSDP-007** Persistence projection is idempotent and emits only bounded,
  content-free diagnostics identifying an omitted path and its serialized
  size.
- [ ] **PSDP-008** A deterministic application-level integration test injects
  large sentinel data into usage, native-item, internal-metadata, content-part,
  and core-metadata locations, then verifies final events, the JSON file, and a
  fresh reload contain only policy-approved data.
- [ ] **PSDP-009** The deterministic integration preserves equally large data
  at approved content/tool-result paths and preserves small opaque continuation
  fields outside those paths.
- [ ] **PSDP-010** One explicitly enabled real OpenAI API integration verifies
  that supported usage presentation and ordinary native continuation still
  work after projection.
- [ ] **PSDP-011** The existing-session maintenance command reuses the same
  persistence-policy engine to inspect and sanitize canonical live sessions
  and snapshots.
- [ ] **PSDP-012** Dry-run and apply modes report policy violations, occurrence
  counts, original/projected bytes, and savings without logging message
  content; apply uses validated compressed recovery backups and atomic
  replacement.
- [ ] **PSDP-013** Snapshot selection records, conflict backups, malformed
  records, and other non-canonical JSON files are not rewritten.
- [ ] **PSDP-014** All affected canonical live sessions and snapshots in the
  approved session root are sanitized during a confirmed no-writer window, and
  a second dry run reports no remaining policy violations.
- [ ] **PSDP-015** The change is covered by one focused policy unit test, one
  deterministic application integration test, the existing OpenAI real-API
  assertion, the two small sanitizer tests, and relevant existing suites.
- [x] **PSDP-016** General large-session fixture generation and the reusable
  performance benchmark remain deferred to the first later optimization that
  needs them.

## Scope

In scope:

- A generic persisted-session projection and size-policy model in the core SDK.
- Policy contributions from the active provider, provider extensions, and
  features.
- Central policy application before final core/native session publication and
  at the application save boundary as an idempotent backstop.
- OpenAI Responses policy rules for usage, native output items, internal
  metadata, reasoning, tools, attachments, and compaction data.
- Removal of the provisional attribution-name-specific runtime sanitizer once
  the policy covers that behavior.
- A higher-level deterministic application integration covering emitted,
  persisted, and freshly reloaded core/native data.
- Reuse of the policy engine by the existing live-session and snapshot
  maintenance command.
- Safe migration and before/after evidence for the current session root.
- Provider-contract, conformance-test, and OpenAI package development
  documentation.

Out of scope:

- Immediate policy adoption by every first-party provider bundle. Providers
  without an explicit native-history policy remain in audit/pass-through mode
  for provider-native branches; the portable core-message policy still
  applies.
- A global strict key allowlist for all provider-native protocols.
- Removing legitimate opaque continuation data merely because the core does
  not understand it.
- General large-session generation or cross-task performance benchmarking.
- JSON/JSONL storage redesign, incremental message APIs, bridge compression,
  or locking changes.

Parent Task: `tasks/20260911-session-performance-and-storage-optimization/000-main.md`

## Requirement questions and material decisions

- **Recommendation:** Project disallowed persisted fields out and emit a
  bounded warning rather than fail the complete assistant response. A
  test/audit helper should return every violation so tests can fail without
  making production persistence all-or-nothing.
- **Recommendation:** Preserve unknown fields below the ordinary-field byte
  budget. A strict global known-key schema conflicts with the native-history
  requirement to preserve opaque provider continuation state.
- **Recommendation:** Enforce native-history rules initially for OpenAI
  Responses and deterministic policy fixtures. Other providers should receive
  audit results until their owning package declares bulk-data paths.
- **Proposed initial limits:** 64 KiB for one undeclared value and 256 KiB of
  undeclared aggregate data within one structured container. These limits may
  be lowered or raised during implementation only when the deterministic
  policy test and sanitized real-session scan show a concrete false positive
  or missed pathological case.
- **Question:** Should policy diagnostics be warnings only, or should the
  persisted session also contain one bounded notification that data was
  omitted? The recommendation is warning only for this task so diagnostics do
  not add more session growth.

## Research details

### Current data flow

For OpenAI Responses, the SDK response is converted to a dictionary. The
provider already selects only a few response-level fields:

- `output` becomes provider-native history;
- `id`, `usage`, `service_tier`, and selected reasoning values become private
  `_metadata`;
- arbitrary response-root siblings are not retained.

The remaining boundaries are open:

1. Output items are retained as complete provider-native dictionaries.
2. Response usage is attached privately to each output item for extension
   processing.
3. The usage extension computes derived fields, then historically copied the
   complete upstream usage mapping into public/native `usage`.
4. The provider projects nearly every non-private native `_metadata` field into
   core message metadata.
5. Response-segment construction can duplicate that metadata into
   `phase_messages`.
6. AgentCore stores the complete native history under
   `session.metadata.native_messages`, while the application serializes the
   complete session without a persistence projection.

This explains why one upstream field was multiplied across core, native, and
phase representations.

### Deterministic probe

An in-memory scripted OpenAI response containing 200 KB sentinels showed:

- an arbitrary response-root field was not retained;
- arbitrary direct and nested usage fields were retained in native history;
- the same usage fields were surfaced into core message metadata;
- an arbitrary native-item field was retained;
- an arbitrary content-part sibling was retained;
- ordinary assistant text was retained as expected.

The failure therefore exists outside `usage.attribution` and is reproducible
without a hosted request.

### Real-session evidence

Before sanitization, the combined dry run found:

- 389 live sessions and 237 snapshots;
- 29 affected live sessions and 38 affected snapshots;
- 6,310 core, 2,342 phase, and 6,310 native attribution copies;
- projected savings of 2,966,685,068 bytes.

After excluding usage attribution in memory, sampled large sessions showed
legitimate payload-bearing paths such as:

- core message content and structured tool results;
- native tool output and tool input;
- reasoning and compaction encrypted content;
- compiled system content and bounded display projections.

The largest sampled non-attribution message subtree was about 134 KB, while
the important large leaves were concentrated at identifiable semantic paths.
This supports a policy that allows bulk data at explicit paths instead of
allowing arbitrary large metadata.

### Why a global key allowlist is unsafe

Native history is the continuation source when core/native conversion is
lossy. Existing contracts intentionally preserve opaque provider fields such
as reasoning signatures, encrypted state, compaction data, tool identifiers,
and attachment references. Deleting every unknown key would make provider
upgrades and compatible endpoints brittle.

The recommended model has two complementary rule types:

1. **Structured projection rules** for externally owned mappings with a stable
   local contract, such as persisted usage. Only explicitly supported
   descendants survive.
2. **Bulk-data path rules** for open-ended histories. Unknown small fields
   survive, but a field may exceed the ordinary byte budget only when an
   active plugin declares that exact path as intentional bulk data.

This catches arbitrary oversized additions without treating all provider
extensions as invalid.

## Execution plan

Status: Draft

### 1. Establish the failing generalized acceptance test

Add one dedicated deterministic provider fixture used through
`AgentApplication`, its real filesystem session store, and the normal request
checkpoint path.

The provider should emit one unique large sentinel in each of these locations:

- usage as a direct unknown child;
- usage as a nested unknown object;
- a provider-native item sibling;
- a provider-native content-part sibling;
- provider-native `_metadata`;
- projected core message metadata.

It should also emit equally large but legitimate assistant content and
structured tool-result/continuation data at declared bulk paths, plus one
small unknown opaque continuation field.

The test should first describe the current failing behavior, then accept only
the completed contract:

- final emitted core messages contain no disallowed sentinel;
- returned session native history contains no disallowed sentinel;
- the checkpoint JSON contains no disallowed sentinel;
- a new application/core instance reloads the same projected state;
- approved large payloads and the small opaque field remain;
- projection is idempotent.

Use compact repeated sentinel data so the test is deterministic and fast. Do
not generate a general benchmark fixture in this task.

### 2. Add a reusable persistence-policy model

Introduce a small immutable policy representation and pure projector in the
core SDK. Use normalized tuple paths internally and a documented dotted/wildcard
form at plugin boundaries.

The policy should support:

- retained-child rules for structured mappings such as usage;
- exact or wildcard bulk-data paths allowed to exceed ordinary limits;
- ordinary per-value and per-container byte budgets;
- content-free violation records containing path, reason, and byte counts;
- audit and project modes;
- idempotent projection.

Compute encoded sizes in one post-order traversal rather than repeatedly
serializing every ancestor. The policy work must not introduce another
superlinear operation into large-session handling.

Core-owned rules should cover portable visible content, multipart content, and
structured tool-result payloads. Plugin rules extend those defaults for native
history and plugin-owned metadata.

### 3. Add one composable plugin contribution contract

Add an optional policy-contribution hook to provider, provider-extension, and
feature protocols plus their default adapters and wrappers.

AgentCore should resolve and compose contributions from only the plugins active
for the effective request/session configuration. Conflicting rules should use
a deterministic, documented precedence:

1. core structural rules;
2. provider rules;
3. active provider-extension rules;
4. active feature rules.

Rules may grant a narrower structured child set or add an explicit bulk path;
they must not disable the global ordinary-data budget.

Providers without an explicit native policy should initially be audited but
not have native continuation fields removed. This keeps the first rollout
compatible while making missing provider adoption visible.

### 4. Apply the policy at publication and persistence boundaries

Use the same pure projector at two central boundaries:

1. AgentCore response publication, after provider/extensions/features and
   response lifecycle actions have completed but before final messages and the
   final session are emitted.
2. `AgentApplication._prepare_session_for_save`, after save-prepare lifecycle
   actions, as an idempotent backstop for direct saves, checkpoints, snapshots,
   and conflict recovery paths.

Do not add separate streaming, non-streaming, phase-message, native-rebuild,
snapshot, and backup sanitizers. Those paths should converge on the same
projection helper.

Projection removes mapping fields, not complete message/native items, so
message ordering and native indices remain stable. Recompute or verify native
integrity after projection.

### 5. Adopt the generalized policy in OpenAI Responses

Declare OpenAI bulk paths for the payloads that must remain large, including:

- message/content payloads;
- tool call input/arguments and tool result output;
- reasoning and compaction encrypted state;
- supported attachment source/reference data;
- explicitly retained provider continuation fields.

Declare structured retained fields for OpenAI usage, including the currently
consumed input/output/total token values and supported detail counters. Keep
derived cost, cache, turn, auth-mode, service-tier, reasoning, duration, and TPS
metadata under their existing local keys.

Raw upstream usage remains transient until those values are calculated. Then
remove the provisional `attribution`-name-specific runtime transformation and
let the structured usage rule discard any undeclared current or future field.

Add a scripted OpenAI-shaped assertion containing concrete `attribution` plus a
different arbitrary usage key so the task proves the fix is schema-based, not
key-name-based.

### 6. Reuse the policy for existing-session migration

Refactor the existing sanitizer transformation to invoke the same OpenAI/core
policy over imported session payloads. Keep the executable command, live and
snapshot discovery, report format, backup layout, source-state checks,
validation, and atomic replacement.

The migration report should group removals by policy path/reason rather than
hard-coding core/native/phase attribution counters. Preserve aggregate
original/projected bytes and savings.

Run a new combined dry run because the projected set may include additional
oversized, undeclared OpenAI fields beyond attribution. Review every path class
before apply. Apply only after the running CLI and active requests are stopped.

### 7. Verification sequence

Run:

1. the focused policy unit test;
2. the deterministic application/filesystem integration;
3. the scripted OpenAI-shaped assertion;
4. the two sanitizer tests;
5. the explicitly enabled real OpenAI API usage integration;
6. existing core/application persistence, native-history, and OpenAI Responses
   suites;
7. selective first-party provider suites in audit mode to identify undeclared
   legitimate native bulk paths without changing their persisted behavior.

The full OpenAI suite's three pre-existing attachment-history failures remain
outside scope unless the generalized policy changes their result.

### Implementation decisions and open questions

- **Decision:** Replace the narrow runtime attribution filter with a
  generalized persistence-policy engine.
- **Decision:** Keep raw provider responses and raw usage transient; persist a
  local projected contract.
- **Decision:** Combine strict structured projection with declared bulk-data
  paths. A size budget alone would still retain small arbitrary usage fields,
  while a global key allowlist would break opaque continuation compatibility.
- **Decision:** Preserve unknown small fields outside strict structured
  mappings.
- **Decision:** Enforce OpenAI native-history policy in this task; audit other
  providers until their packages declare native bulk paths.
- **Decision:** Use one deterministic application/filesystem integration as
  the main generalized acceptance test.
- **Decision:** Reuse the same projector for current-session migration.
- Resolve the warning-versus-session-notification question before execution.
- Confirm the proposed byte limits after running the policy in audit mode over
  sanitized representative sessions.
- Confirm the no-writer window before applying changes to current files.

### Documentation

- Update the core/provider protocol documentation with the persistence-policy
  contribution contract and precedence.
- Update provider implementation and conformance standards to distinguish
  transient raw provider data from persisted projected data.
- Update the provider template with a minimal policy declaration example.
- Update OpenAI Responses development documentation with its supported usage
  contract, bulk native paths, diagnostics, and migration command.
- Do not expose task IDs or migration phase language in package-user
  documentation.

### Task checklist

- [ ] Add the failing deterministic application/filesystem integration.
- [ ] Add one focused policy projector unit test.
- [ ] Implement the immutable policy model, path matcher, byte accounting, and
  audit/project modes.
- [ ] Add optional provider, extension, and feature policy contributions.
- [ ] Compose active-plugin policies deterministically.
- [ ] Apply projection before final response/session publication.
- [ ] Apply projection at application save preparation.
- [ ] Add OpenAI Responses structured usage and bulk-path rules.
- [ ] Replace the attribution-specific runtime filter.
- [ ] Add the scripted OpenAI attribution-plus-arbitrary-key assertion.
- [ ] Refactor the session/snapshot sanitizer to reuse the policy projector.
- [ ] Update the two sanitizer tests without expanding their count.
- [ ] Run the focused, existing, hosted, and audit verification sequence.
- [ ] Run a combined live-session and snapshot dry run and review every removed
  path class.
- [ ] Establish a no-writer window and apply sanitization.
- [ ] Validate rewritten records and rerun dry mode for zero violations.
- [ ] Record before/after counts and bytes without committing session content.
- [ ] Update provider/core/OpenAI development documentation.
- [ ] Add completion evidence and close the parent subtask.

### Requirement verification

- **PSDP-001:** Scripted and real-provider tests prove calculations and
  supported continuation behavior still use transient raw response data.
- **PSDP-002 through PSDP-004:** Focused policy unit coverage and protocol
  inspection prove structured, bulk-path, budget, composition, and idempotence
  behavior.
- **PSDP-005 and PSDP-006:** Scripted OpenAI and existing reasoning, tool,
  attachment, compaction, usage, duration, and native-history suites prove the
  OpenAI policy boundary.
- **PSDP-007:** Unit/integration diagnostics assertions contain only paths,
  reasons, and byte counts and a second projection reports no changes.
- **PSDP-008 and PSDP-009:** The deterministic application integration checks
  emitted core messages, returned native history, disk JSON, and fresh reload.
- **PSDP-010:** The explicitly enabled real OpenAI API usage test runs and
  passes without a skip.
- **PSDP-011 through PSDP-014:** Sanitizer tests, apply report, filesystem
  inspection, backup validation, and the final zero-change dry run provide
  evidence.
- **PSDP-015:** Test inventory and command results show the deliberately small
  new coverage set plus existing regression suites.
- **PSDP-016:** Change-set inspection confirms no benchmark or general large
  fixture was added.

### Additional implementation verification

- Run Ruff, Black, and targeted Pyright over changed core, application, plugin,
  script, and test files.
- Run `pytest core/python/tests -q` and
  `pytest plugins/openai_responses/tests -q`, recording unrelated existing
  failures separately.
- Run selective OpenRouter, OpenAI-compatible reference, and Anthropic
  provider persistence tests in audit mode because their usage/native
  extensions exercise similar open dictionaries.
- Inspect one sanitized large live session and one snapshot through
  `Session.from_dict`, native-integrity verification, and a fresh application
  reload.

## Implementation Notes

### 2026-09-11

- Added a provisional targeted runtime transformation that removes only
  `usage.attribution` after current-response calculations.
- Added a separate live-session/snapshot sanitizer with dry-run and apply
  modes, reports, compressed backups, source-content rechecks, validation, and
  atomic replacement.
- Added one focused runtime unit test, one real OpenAI API integration
  assertion, one pure sanitizer test, and one sanitizer command test.
- Focused local verification passed, and the explicitly enabled OpenAI API
  usage integration passed.
- The complete OpenAI package suite passed 422 tests when three unrelated
  attachment-history failures were excluded.

### 2026-09-12

- Extended migration discovery to canonical snapshots and added the executable
  `plugins/openai_responses/scripts/sanitize_session_usage.py` wrapper.
- The combined attribution-only dry run scanned 626 canonical records, found
  67 affected records, and projected 2,966,685,068 bytes of savings.
- No live session or snapshot has yet been rewritten because the running CLI
  still owns the session root and one affected session had an active request.
- A new deterministic in-memory probe showed arbitrary 200 KB fields outside
  attribution also survive in usage, native items, content parts, native
  `_metadata`, and projected core metadata.
- The user broadened the required solution from an attribution-specific
  bugfix to a generalized persisted-session data policy. The execution plan
  returned to `Draft`; the current narrow runtime sanitizer is provisional and
  migration apply remains paused pending approval of the revised plan.