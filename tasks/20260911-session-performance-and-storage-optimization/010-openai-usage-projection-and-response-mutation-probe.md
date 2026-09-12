# OpenAI usage projection, response mutation probe, and session sanitization

Replace whole-object OpenAI usage persistence with a supported root-field
projection, probe other provider-response levels through the real OpenAI
Responses provider, and sanitize affected live sessions and snapshots.

## Requirements checklist

- [x] **OURP-001** Raw OpenAI response usage remains available transiently for
  current-turn token, cost, cache, turn, auth-mode, service-tier, and reasoning
  calculations.
- [x] **OURP-002** Newly persisted OpenAI `usage` contains only explicitly
  supported root fields; arbitrary current or future usage-root keys are not
  retained in core messages, phase messages, or native `_metadata`.
- [x] **OURP-003** Provider-native `_metadata` remains the intentional channel
  for metadata that must survive native-history rebuild and be projected back
  into core message metadata.
- [x] **OURP-004** A test-only mutation proxy wraps a real OpenAI API response
  while the production OpenAI Responses provider and extension pipeline remain
  responsible for all response processing.
- [x] **OURP-005** The mutation probe recursively discovers every eligible
  object in the actual provider response, traversing every array element, and
  inserts a unique recognizable arbitrary key into every discovered object
  when the candidate count is within the configured limit.
- [x] **OURP-006** The mutation probe has an explicit fixed test-only ignore
  list for intentionally open or platform-owned data such as `_metadata` and
  approved reasoning payloads; ignored subtrees are excluded during recursive
  candidate discovery.
- [x] **OURP-007** If recursive discovery exceeds the mutation limit, a
  reproducible seed selects no more than 100 candidates from the complete
  discovered set without limiting array traversal or collapsing differently
  shaped array elements.
- [x] **OURP-008** The primary probe stringifies the complete exported session
  JSON once, searches for the exact `PROBE_CONTENT_` prefix, resolves every
  discovered suffix through the mutation manifest, and reports the
  corresponding injected response path.
- [x] **OURP-009** The marker-search helper can optionally stringify and scan
  core messages and retained native messages independently so later tests can
  distinguish core-only, native-only, and shared retention without requiring a
  recursive parsed-object search.
- [x] **OURP-010** No production filtering outside OpenAI usage is implemented
  until the initial probe results identify a concrete unwanted retention path
  and a follow-up plan for that path is reviewed.
- [x] **OURP-011** Existing canonical live sessions and snapshots are scanned
  and sanitized with the same supported usage-root projection used by new
  requests.
- [x] **OURP-012** The maintenance command supports dry run, validated
  compressed recovery backups, source-state rechecks, atomic apply, live
  sessions, snapshots, and a second idempotence scan.
- [x] **OURP-013** Snapshot selection records, conflict backups, malformed
  records, and other non-canonical JSON files are not rewritten.
- [x] **OURP-014** One focused usage unit test, one real-API mutation
  integration, the two existing sanitizer tests, and relevant existing suites
  provide the new coverage without a broad test matrix.
- [ ] **OURP-015** All affected canonical live sessions and snapshots in the
  approved session root are sanitized in a confirmed no-writer window, and a
  final dry run reports no unsupported usage-root fields.
- [ ] **OURP-016** Before/after evidence records affected records, removed
  usage-root keys by path, occurrence counts, and serialized-byte savings
  without recording message content.
- [x] **OURP-017** General large-session fixture generation and reusable
  performance benchmarking remain deferred to a later storage optimization.
- [x] **OURP-018** The mutation probe treats the complete
  `response.output[*]` subtree as intentionally retained provider-native data
  and excludes it from arbitrary-key injection.
- [x] **OURP-019** No provider output-item persistence, core conversion,
  request replay, or other non-usage production behavior changes in this
  follow-up.
- [x] **OURP-020** Persisted OpenAI usage contains an explicit allowlist of
  fields observed in current real responses plus the compatibility paths used
  by usage, pricing, cache, and reasoning logic; arbitrary future root and
  nested detail keys are not retained.
- [x] **OURP-021** After exact usage allowlisting, the real
  `gpt-5.6-luna` two-request tool-loop mutation test completes and the full
  exported-session string scan finds no non-ignored marker.
- [x] **OURP-022** The existing focused usage unit test and two sanitizer tests
  cover exact root and nested-path projection without adding provider-message
  test coverage.

## Scope

In scope:

- OpenAI Responses raw usage handoff and persisted usage projection.
- An explicit allowlist of supported OpenAI usage fields and nested paths.
- A test-only deterministic mutation engine and proxy over a real OpenAI API
  response.
- A two-request `gpt-5.6-luna` tool loop that requires a real `add` tool call,
  executes it through `MathTools`, and mutates both provider responses.
- Recursive discovery and mutation of eligible dictionaries at any depth in
  the actual response, including dictionaries nested in arrays.
- Mutation of every eligible object when there are at most 100 candidates, or
  seeded selection of at most 100 candidates after complete discovery.
- One primary full exported-session JSON marker scan, with optional separate
  core/native string scans available to future tests.
- A fixed test-only ignore list for `_metadata`, the complete
  `response.output` subtree, and any other path explicitly accepted before or
  after the initial diagnostic run.
- Reuse of the usage projection by the existing live-session and snapshot
  sanitizer.
- Safe migration and before/after evidence for the current session root.
- Exact persisted usage path projection, including nested token-detail fields.

Out of scope:

- A generic core persistence-policy engine.
- Runtime byte thresholds or bulk-data path policies.
- Generic filtering of provider-native `_metadata`.
- Any change to provider output-item persistence, core conversion, request
  replay, or wire sanitization.
- Deep filtering or rewriting of known message content, tool payload,
  reasoning, compaction, attachment, or server-tool payload values.
- Changes to providers other than OpenAI Responses.
- Storage layout, incremental message APIs, bridge compression, and locking.
- General performance fixture generation or benchmarking.

Parent Task: `tasks/20260911-session-performance-and-storage-optimization/000-main.md`

## Requirement questions and decisions

- **Decision:** `_metadata` is not an arbitrary provider leak. It is the
  framework's explicit persistence channel for reconstructing core metadata
  from native history.
- **Decision:** The whitelist discussed in this task is implemented as the
  mutation test's fixed ignore list. It identifies subtrees where arbitrary
  additional keys are intentionally not injected, not a global runtime
  whitelist.
- **Decision:** The only production behavior change planned before the probe is
  a supported root-key projection for OpenAI usage.
- **Decision:** Any non-usage production change requires actual probe evidence
  and a revised or separate follow-up plan before implementation.
- **Decision:** Every inserted key and value receives a unique random or
  sequential identifier. The earlier `123` was illustrative and is not a
  fixed marker.
- **Decision:** Recursively discover all possible dictionary placements before
  mutating the response. Do not stop traversing an array or collapse its
  elements merely because several elements appear structurally similar.
- **Decision:** Mutate every eligible object when discovery returns at most
  100 candidates. If there are more, use a reproducible seed to sample no more
  than 100 from the complete candidate set.
- **Decision:** Use recognizable marker strings instead of allocating
  genuinely large payloads. The defect under test is retention of arbitrary
  keys, not JSON throughput.
- **Decision:** The complete `response.output` subtree is intentionally
  retained provider-native data. The mutation test excludes it instead of
  treating its retained markers as defects.
- **Decision:** The follow-up contains only two changes: the test exclusion and
  exact persisted usage allowlisting. Existing provider message handling is
  left unchanged.

## Research details

### Current OpenAI response boundaries

The provider currently treats each response level differently:

1. The response root is projected explicitly. The provider reads `output`,
   `id`, `usage`, service tier, and selected reasoning values; unrelated
   response-root siblings are already discarded.
2. The complete `usage` mapping is handed to the usage extension. The
   extension reads a small known set of fields but historically persisted the
   complete mapping.
3. Provider output items are retained in native history so opaque continuation
   state can survive core conversion.
4. Message content parts are also retained in native history and normalized
   selectively when replayed to the API.
5. `_metadata` is created and owned by the platform/provider pipeline. The
   provider intentionally projects non-private `_metadata` fields into core
   message metadata during rebuild.
6. Response-segment construction can copy projected metadata into
   `phase_messages`, which explains why one unsupported usage field appeared
   in several serialized locations.

The known production fix belongs in step 2: the extension should persist the
supported usage contract rather than the complete upstream mapping.

### Exact persisted usage paths

Current OpenAI usage and pricing code consumes:

- `input_tokens`;
- `input_tokens_details.cached_tokens`;
- `input_tokens_details.cache_write_tokens`;
- `output_tokens`;
- `output_tokens_details.reasoning_tokens`;
- `completion_tokens_details.reasoning_tokens` as a compatibility fallback.

The already implemented root projection still retains complete supported
detail mappings. The remaining production change narrows those mappings while
retaining `total_tokens`, which appears in the real response and is useful for
inspection. Future persisted usage data requires an intentional code and test
update.

### Why the previous generalized plan was too early

A local probe confirmed that arbitrary data can survive at several native
levels, but it injected data without distinguishing framework-owned
`_metadata`, deliberately opaque reasoning state, and ordinary provider
response objects. Native retention alone is not proof of a bug because native
history exists specifically to preserve data that lossy core messages cannot
represent.

The correct next step is an evidence-producing mutation test with explicit
test exclusions. Only after the test shows exactly where non-excluded
provider-added root keys survive can the task decide whether a native-item or
content-part change is warranted.

### Hosted tool-loop probe findings

The completed `gpt-5.6-luna` tool-loop probe used two real API responses. The
test-only proxy removed probe keys from the outgoing second request so retained
session data could not prevent completion of the diagnostic scenario. This
transport scrub does not change production provider behavior.

In the latest completed run, the first response contained 29 eligible
dictionaries and retained three markers in the exported session:

- `$.output[0]`, type `function_call`, once;
- `$.usage.input_tokens_details`, twice;
- `$.usage.output_tokens_details`, twice.

The second response also contained 30 eligible dictionaries and retained four
markers:

- `$.output[0]`, type `message`, once;
- `$.output[0].content[0]`, type `output_text`, once;
- `$.usage.input_tokens_details`, three times;
- `$.usage.output_tokens_details`, three times.

An immediately preceding real-API run returned a separate `reasoning` output
item before the function call; its injected root marker also survived once.
The test must therefore continue discovering the actual response recursively
instead of assuming a fixed output array shape.

The final test failure lists every retained marker with its seed, exact
injection path, provider object type, and occurrence count. In the latest run,
26 injections from each response did not survive. Response-root and usage-root
probe keys were among the filtered values.

Evidence-based follow-up recommendations:

1. Keep every provider object under `response.output[*]` unchanged and make no
   provider production change. Exclude that complete subtree from mutation
   candidate discovery because its retention is intentional.
2. Extend persisted usage projection into supported detail mappings and remove
   unused roots. `input_tokens_details` retains `cached_tokens` and
   `cache_write_tokens`; `output_tokens_details` and
   `completion_tokens_details` retain `reasoning_tokens`.
3. Keep `_metadata` unchanged as the explicit internal persistence channel and
   strip it only from the provider wire request, as the provider already does.

These are recommendations, not an approved implementation plan.

### Response structure and usage paths

The provider response shape relevant to this issue is:

```text
response
├── output[]
│   ├── reasoning item
│   ├── function/custom-tool item
│   └── message item
│       └── content[]
└── usage
    ├── input_tokens
    ├── input_tokens_details
    ├── output_tokens
    └── output_tokens_details
```

`usage` is a response-root sibling of `output`; it is not part of a message
item. The provider temporarily copies raw response usage into output-item
`_metadata` so the usage extension can calculate derived values. The extension
then persists projected usage in native/core metadata, which is why one
unsupported usage field can appear in several session locations.

Objects under `response.output[*]` are the provider-native continuation
history and remain complete in storage. The mutation test therefore stops
traversal at `response.output`; it does not attempt to define or enforce an
allowlist for messages, reasoning, tool calls, content parts, or future output
item types.

Current usage and pricing code reads only:

- `input_tokens`;
- `input_tokens_details.cached_tokens`;
- `input_tokens_details.cache_write_tokens`;
- `output_tokens`;
- `output_tokens_details.reasoning_tokens`;
- `completion_tokens_details.reasoning_tokens`.

The real OpenAI response also reports `total_tokens`; it remains in the
explicit allowlist for inspectability even though current displayed totals are
derived from the input/output fields and the extension's local cumulative
metadata.

### Existing session evidence

The attribution-focused dry run scanned 626 canonical records:

- 389 live sessions;
- 237 snapshots;
- 29 affected live sessions;
- 38 affected snapshots;
- 6,310 core, 2,342 phase, and 6,310 native attribution copies;
- projected savings of 2,966,685,068 bytes.

The broader usage-root projection requires another dry run before apply
because it may find unsupported usage siblings other than `attribution`.

## Execution plan

Status: Approved

### 1. Build the test-only recursive response mutation engine

Create a small deterministic helper owned by the OpenAI Responses tests. It
accepts:

- a real response dictionary;
- an explicit fixed ignore-path list;
- a configurable maximum mutation count, initially 100;
- a reproducibility seed used only when sampling or generating identifiers;
- a marker prefix.

The helper should operate in two passes:

1. Recursively traverse the complete JSON-compatible response and collect the
   exact path of every dictionary not inside an ignored subtree.
2. After discovery is complete, mutate either every candidate or a seeded
   sample of at most 100 candidates.

Dictionary mutation means adding one new root key to that dictionary. The key
and string value must both carry a unique probe ID. Probe IDs may be sequential
within a run, such as `probe_0001`, or generated by a seeded pseudo-random
generator. They must not reuse one fixed number.

Candidate discovery rules:

- visit the response root;
- recurse through every dictionary value;
- recurse through every element of every array;
- retain exact numeric array indices in the manifest;
- do not deduplicate candidates by normalized path or object shape;
- do not impose a candidate limit during discovery;
- optionally enforce a generous recursion-depth safety limit, but report a
  fixture failure if real response data exceeds it.

If the discovered candidate count is at most 100, mutate all candidates. If it
is greater than 100, select 100 candidates with a fixed CI seed from the full
candidate list. The failure report records the seed so a local run can
reproduce the same selection.

Initial excluded paths:

- every `_metadata` subtree;
- reasoning content, summaries, signatures, and encrypted continuation data;
- test harness bookkeeping;
- any explicit opaque path already required by a documented OpenAI
  continuation contract.

The ignore list is fixed input to the test. It controls traversal: when a path
matches an ignored subtree, neither that dictionary nor descendants beneath it
become mutation candidates.

The helper returns a manifest mapping every probe ID to:

- its exact response-object path;
- the inserted key;
- the inserted marker value;
- whether it was selected after sampling;
- the seed and total discovered candidate count.

Do not use message text or provider response content as assertion identity.

### 2. Proxy a real OpenAI API response

Use the production `OpenAIResponsesProvider` request, conversion, extension,
and finalization implementation. Add only a test-owned client/response proxy:

1. The wrapped client calls the real OpenAI Responses API.
2. The proxy obtains the response dictionary immediately before the provider's
   normal `_response_to_dict` processing.
3. The mutation helper adds the deterministic keys.
4. The proxy returns the mutated response object to the unchanged provider
   pipeline.

A small provider subclass or monkeypatched client factory is acceptable when
it changes only client construction. Do not duplicate provider response
processing in the test.

Start with the non-streaming real API path. Streaming mutation requires an SSE
proxy and should be added only if the non-streaming results reveal a
streaming-specific question.

Use `gpt-5.6-luna` and expose the real `MathTools` schemas through
`OpenAIResponsesToolsExtension`. The first request must require exactly one
`add(123, 456)` call. Execute the emitted call through AgentCore, append the
tool result, and send the second request. The final assistant response must be
exactly `OPENAI_RESPONSE_MUTATION_PROBE_OK 579`. Mutate and inspect both real
API responses.

### 3. Run the diagnostic test before broadening implementation

The first targeted run is expected to fail. Export the complete returned
session to JSON and search that string for the exact `PROBE_CONTENT_` prefix.
When the prefix is found, parse the following marker suffix, such as
`0005_6e81`, and resolve it through the mutation manifest to identify the
injected key and exact original response path.

The primary probe does not recursively search the parsed session object and
does not separately inspect every projection. The exported full session
already includes both core messages and retained native history.

The reusable search helper should nevertheless accept optional scopes:

- full exported session JSON;
- core messages only;
- retained native messages only.

Each scope is implemented by serializing that complete branch and performing
the same prefix/suffix string search. Do not add a positive core/native
retention test in this task; the optional scopes are only an interface for
later tests that may require native-only, core-only, or shared preservation.

The failure output must contain:

- probe ID;
- exact original response injection path from the manifest;
- selected scan scope;
- seed and candidate counts.

Do not print real response or conversation content. Report every distinct
marker suffix found in the serialized scope.

Record the results in Implementation Notes. Then classify every retained
non-usage path as one of:

- intentional native forward compatibility;
- already excluded/allowlisted test scope;
- unnecessary but harmless retention;
- concrete unwanted retention requiring a follow-up production change.

Stop and return the plan to `Draft` before implementing any non-usage
production fix. Add the resulting code plan only after the observed path and
its continuation implications are known.

### 4. Replace attribution-specific handling with usage root projection

Change the existing usage persistence helper from “remove `attribution`” to
“retain supported usage root fields.”

Apply that one helper at the existing usage persistence/rebuild boundaries:

- public/core usage metadata;
- native `_metadata["usage"]`;
- phase-message usage reconstructed from native history;
- existing-session migration.

Do not filter unrelated `_metadata` fields or native item/part roots in this
step.

Update the focused unit test to include:

- every supported usage root field;
- `attribution`;
- at least one different arbitrary root key;
- an arbitrary nested detail key under a supported detail mapping.

The two unsupported root keys must be discarded. Supported roots and their
nested detail mappings must remain.

### 5. Turn the mutation probe into stable regression coverage

After the initial retention matrix is reviewed:

- keep the fixed test-only ignore list explicit and minimal;
- keep recursive candidate discovery independent of fixed response paths;
- assert every non-ignored injected marker has the reviewed expected retention
  outcome;
- add any intentionally retained non-usage native subtree to the test ignore
  list only with a short reviewed rationale;
- leave any disputed non-usage path as a failing/expected-failing follow-up
  until its separate plan is approved.

Do not choose a fresh unreported seed in CI. Mutate all candidates when
possible; otherwise use the fixed and reported sampling seed to avoid flaky
coverage.

### 6. Generalize the existing-session usage sanitizer

Reuse the supported usage-root projection in the existing sanitizer. A usage
object is affected when it contains at least one unsupported root key, not
only when it contains `attribution`.

Keep:

- live-session and snapshot discovery;
- dry-run default;
- optional session selection;
- structured reports without content;
- separate compressed backups for sessions and snapshots;
- source hash/state rechecks;
- temporary validation and atomic replacement;
- second-run idempotence.

Update the existing two sanitizer tests rather than adding more test cases.

### 7. Verify and migrate

Run:

1. the focused usage unit test;
2. the mutation helper/proxy integration against the real API;
3. the two sanitizer tests;
4. existing OpenAI usage, provider, native-history, reasoning, tools,
   attachments, and compaction tests;
5. the explicitly enabled ordinary real OpenAI usage test if it remains
   separate from the mutation test.

Then run a new dry scan over live sessions and snapshots, review every removed
usage root key, and apply only after the CLI and active requests are stopped.

### 8. Exclude provider output from mutation probing

Add `response.output` to the mutation helper's fixed ignored subtrees. When
candidate discovery reaches that path, it does not mutate the output array,
its item dictionaries, content parts, reasoning, tool calls, or descendants.

Keep recursive mutation for the rest of the actual response, including the
response root, `usage`, and both usage-detail mappings. The existing test-only
outgoing probe scrub can then be removed because no marker is inserted into
the provider-native continuation items sent on the second request.

Do not add native/core scoped assertions, provider item allowlists, request
projection, or output-item sanitization.

### 9. Project exact persisted usage paths

Replace the current root-only usage projection with a small constructor that
retains only:

```text
input_tokens
input_tokens_details.cached_tokens
input_tokens_details.cache_write_tokens
output_tokens
output_tokens_details.reasoning_tokens
completion_tokens_details.reasoning_tokens
total_tokens
```

Preserve supported roots even when a detail mapping is empty. Remove arbitrary
root fields and arbitrary nested detail fields. Continue calculating derived
totals, cost, and formatted metadata from transient raw usage before applying
the persisted projection.

Reuse the exact projection in native metadata, core metadata, phase messages,
native rebuild, and the existing session/snapshot sanitizer.

### 10. Verify and re-scan

After the two changes:

- the two-request `gpt-5.6-luna` tool loop completes without the test-only
  outgoing scrub;
- the full exported-session string scan finds no injected marker;
- the focused usage unit test proves only consumed usage paths remain.

Run the focused usage unit test, hosted mutation integration, two sanitizer
tests, and relevant existing usage/provider tests. No new provider-message test
is needed because provider-message behavior does not change.

Update the sanitizer report to include removed nested usage paths and the
unused `total_tokens` root. Run dry mode again against live sessions and
snapshots, verify that unrelated provider usage remains untouched, and review
the expanded OpenAI-only change set before requesting a no-writer apply window.

### Implementation decisions and open questions

- **Decision:** Keep `_metadata` as the intentional native-to-core persistence
  mechanism.
- **Decision:** The mutation allowlist is test-only.
- **Decision:** Use real OpenAI API output with a test-owned mutation proxy.
- **Decision:** Recursively discover every non-ignored dictionary before
  deciding whether sampling is required.
- **Decision:** Traverse every array element and keep each exact indexed path.
- **Decision:** Mutate all candidates up to 100 and seed-sample exactly 100
  only when the discovered set is larger.
- **Decision:** Use unique sequential or seeded marker strings instead of
  large payloads or one fixed marker number.
- **Decision:** The complete `response.output` subtree is intentionally
  retained and is excluded from the mutation probe.
- **Decision:** No provider-message, native-history, core-conversion, or
  request-replay production change is needed.
- **Decision:** Update the current sanitizer to remove all unsupported usage
  root and nested keys.
- **Decision:** Persist the explicit current-response field set, including
  `total_tokens`, plus the compatibility paths consumed by current code.
- Confirm whether the mutation integration replaces or supplements the
  existing real-API usage integration.
- Confirm the no-writer window before applying the sanitizer.

### Documentation

- Update OpenAI Responses cost/usage development documentation to list the
  exact supported persisted usage paths and state that other upstream usage
  data remains transient.
- Update the maintenance page so reports and cleanup refer to unsupported usage
  roots and nested paths rather than only attribution.
- Document the test mutation proxy only in test/contributor guidance if it
  becomes reusable; do not present it as a user feature.
- No provider-message documentation changes are required.

### Task checklist

- [x] Add recursive dictionary-candidate discovery and the explicit fixed
  ignore list.
- [x] Add unique probe-key/value generation and the mutation manifest.
- [x] Add mutate-all behavior up to 100 candidates and seeded sampling above
  100.
- [x] Add the real-response proxy around the OpenAI client.
- [x] Run the mutation probe as a two-request `gpt-5.6-luna` tool loop and
  verify the emitted `add` call and real `MathTools` result.
- [x] Run the initial expected-failing mutation probe.
- [x] Record every surviving marker and its exact original response injection
  path without provider content.
- [x] Classify retained non-usage paths: output-item and part markers persist
  in native history, and an output-item root marker is replayed on the next
  request and rejected by the real API; defer its fix to a reviewed follow-up.
- [x] Keep the approved scope boundary and make no non-usage production
  change.
- [x] Replace attribution-specific usage persistence with supported root
  projection.
- [x] Update the one focused usage unit test.
- [x] Refactor the existing sanitizer to use the usage root projection.
- [x] Update the two sanitizer tests without increasing their count.
- [x] Run focused, existing, and hosted OpenAI verification.
- [x] Run and review the new live-session and snapshot dry report.
- [x] Update OpenAI development and maintenance documentation.
- [x] Add `response.output` to the mutation probe's ignored subtrees.
- [x] Remove the now-unneeded test-only outgoing probe scrub.
- [x] Replace root-only usage projection with the explicit current-response
  and compatibility path allowlist.
- [x] Update the existing focused usage unit test for exact nested paths.
- [x] Update the existing two sanitizer tests for exact nested paths.
- [x] Run the hosted probe to a passing full-session zero-marker result.
- [x] Run relevant existing usage/provider tests.
- [x] Re-run the OpenAI-only live-session and snapshot dry scan.
- [x] Update OpenAI development and maintenance documentation for exact usage
  paths.
- [ ] Establish a no-writer window and apply sanitization.
- [ ] Validate every rewritten record and run a zero-change final scan.
- [ ] Record final counts and byte savings.
- [ ] Add completion notes and close the parent subtask.

### Requirement verification

- **OURP-001 through OURP-003:** Focused usage tests and existing
  native-history rebuild tests prove transient calculation and `_metadata`
  behavior.
- **OURP-004 through OURP-009:** The hosted mutation integration, complete
  recursive candidate inventory, sampling record, marker manifest, and
  exported-session prefix scan prove placement coverage and identify every
  retained marker. Inspect the optional core/native scan interface without
  adding a positive retention test.
- **OURP-010:** Change-set inspection before each implementation stage confirms
  no non-usage production filter was added without the required plan update.
- **OURP-011 through OURP-013:** The two sanitizer tests and command inspection
  prove generalized usage-root cleanup, safe apply behavior, and canonical
  file selection.
- **OURP-014:** Test inventory and command results show the deliberately small
  new coverage set plus relevant existing suites.
- **OURP-015 and OURP-016:** Apply reports, backup inspection, transformed-file
  validation, and the final zero-change dry run provide migration evidence.
- **OURP-017:** Change-set inspection confirms no performance fixture or
  benchmark framework was added.
- **OURP-018 and OURP-019:** Mutation-helper inspection and production
  change-set inspection prove `response.output` is excluded and no
  provider-message behavior changed.
- **OURP-020:** The focused usage unit test, installed-SDK schema inspection,
  and hosted real-response assertion prove that only the explicit observed and
  compatibility usage paths are persisted.
- **OURP-021:** The hosted mutation test completes without transport scrub and
  the full exported-session scan finds no marker.
- **OURP-022:** The focused usage unit test and two existing sanitizer tests
  provide the deliberately small regression coverage.

### Additional implementation verification

- Run Ruff, Black, and targeted Pyright over changed OpenAI plugin, script, and
  test files.
- Run `pytest plugins/openai_responses/tests -q`, recording the known unrelated
  attachment-history failures separately unless this work changes them.
- Verify one transformed large live session and one snapshot through
  `Session.from_dict`, native-integrity checking, and a fresh core rebuild.

## Implementation Notes

### 2026-09-11

- Added the initial attribution-specific runtime transformation and
  live-session/snapshot sanitizer.
- Added one focused runtime unit test, one real OpenAI API assertion, and two
  sanitizer tests.
- Focused tests and the explicitly enabled real OpenAI API usage integration
  passed.

### 2026-09-12

- Added snapshot discovery and the executable
  `plugins/openai_responses/scripts/sanitize_session_usage.py` wrapper.
- The attribution-only dry run scanned 626 canonical records, found 67
  affected records, and projected 2,966,685,068 bytes of savings.
- No live session or snapshot has been rewritten because a safe no-writer
  window has not yet been confirmed.
- Commit `138c56c0` records the attribution-specific runtime fix, sanitizer,
  executable command, tests, documentation, and the prior task-plan state.
- The earlier generalized core persistence-policy proposal was superseded.
  `_metadata` is explicitly legitimate, the whitelist belongs to the mutation
  test, and non-usage production changes now require concrete probe evidence
  plus a reviewed follow-up plan.
- Refined the mutation design to discover every eligible dictionary in the
  real response before mutation, traverse every array element, mutate all
  candidates up to 100, and seed-sample 100 only when the complete candidate
  set is larger.
- Simplified marker detection to one string search over the full exported
  session JSON. Marker suffixes map back to exact injection paths through the
  manifest. Optional core-only and native-only string scopes remain available
  for later preservation tests but are not exercised as positive tests here.
- The first hosted mutation run recursively discovered 17 response
  dictionaries and mutated all 17. Before usage-root projection, six markers
  survived: the two output-item roots, one output-text part, the usage root,
  and both nested token-detail mappings.
- After implementing supported usage-root projection, the ordinary hosted API
  usage integration passed and the mutation integration reported the expected
  diagnostic xfail with five retained markers. The usage-root marker no longer
  survives. The remaining markers are the reasoning-item root, message-item
  root, output-text part root, and one nested marker in each token-detail
  mapping.
- No production filtering was added for output items, content parts,
  `_metadata`, reasoning, or nested usage detail mappings.
- Added a supported usage-root projection for `input_tokens`,
  `input_tokens_details`, `output_tokens`, `output_tokens_details`,
  `completion_tokens_details`, and `total_tokens`. Existing-session
  sanitization reuses the same projection and reports removed root keys by
  persisted path.
- The first generalized dry scan exposed unrelated provider usage fields, so
  the sanitizer now requires OpenAI Responses ownership metadata before
  projecting ordinary `usage`. This prevented removal of OpenRouter/Ollama
  usage contracts.
- The corrected dry scan inspected 629 canonical records and found four
  affected OpenAI Responses records: one live session and three snapshots.
  They contain 17 core, 14 phase, and 17 native copies of the unsupported
  `compute_units` usage root and would save 1,702 bytes.
- The previously reported multi-gigabyte `attribution` data is absent from the
  current session root, indicating that the earlier cleanup was applied
  outside this implementation turn.
- Verification completed:
  - 37 focused usage/sanitizer tests passed;
  - one ordinary hosted OpenAI usage test passed;
  - the hosted mutation probe produced one expected xfail with exact injection
    paths for five retained markers;
  - 422 existing OpenAI Responses tests passed when the same three pre-existing
    attachment-history failures were excluded;
  - the unfiltered suite reported only those three existing failures;
  - Ruff, Black, and targeted Pyright passed;
  - a synthetic 151-candidate run selected exactly 100 reproducibly and the
    optional core/native string scopes each found all selected markers.
- Migration apply remains blocked because the CLI is still listening on port
  57889 as PID 20874. No live session or snapshot was changed by this turn.
- Follow-up verification now requires the hosted mutation probe to use
  `gpt-5.6-luna`, emit one real `add(123, 456)` tool call, execute it through
  `MathTools`, and mutate both the tool-call and final-answer responses.
- The updated `gpt-5.6-luna` hosted run successfully emitted the required
  `add(123, 456)` call and `MathTools` returned `579`. The second provider
  request failed before a final response because a probe key retained on the
  first response's native function-call item was replayed as
  `input[1].__probe_...`; the API rejected that unknown parameter with status
  400.
- This is a concrete non-usage retention and wire-replay defect. The mutation
  test is currently a genuine failure rather than an expected xfail. No
  production fix was implemented because the plan requires a reviewed
  follow-up before changing native item or request sanitization behavior.
- Added a test-only outgoing-request scrub that removes only `__probe_` keys.
  Both real requests now complete, and the test fails exclusively at the final
  exported-session marker assertion.
- The latest completed run discovered 29 first-response and 30 second-response
  dictionaries. It retained seven markers: `function_call`, `message`,
  `output_text`, and both usage-detail objects in each response. Twenty-six
  markers from each response were filtered. A preceding run additionally
  retained a `reasoning` item root, demonstrating expected real-response shape
  variation.
- The final failure reports every retained marker with exact injection path,
  provider object type, and occurrence count. The failing traceback uses a
  string-compatible redacted API-key value and was checked to contain no
  API-key-like `sk-` text.
- Repository and installed-SDK inspection confirmed the user's proposed
  boundary: known response-item root fields can be enumerated, while their
  semantic payload values should remain unchanged. Current code consumes only
  `input_tokens`, two input-detail cache counters, `output_tokens`, and the
  reasoning-token counter under output/completion details; raw
  `total_tokens` has no current consumer.
- Added an evidence-backed exact usage-path and mutation-probe follow-up as a
  Draft plan. No production implementation or commit was made.
- Revised the Draft after the user clarified that complete provider output
  items should remain untouched. Removed all proposed provider-message and
  request-replay changes. The follow-up now contains only the
  `response.output` test exclusion and exact persisted usage allowlisting.
- The user approved the two-change follow-up. The usage allowlist retains the
  five roots observed in real OpenAI Responses usage (`input_tokens`,
  `input_tokens_details`, `output_tokens`, `output_tokens_details`, and
  `total_tokens`) plus the extension's
  `completion_tokens_details.reasoning_tokens` compatibility path. Nested
  detail allowlists retain cache-read/cache-write and reasoning-token fields.
- The mutation probe now excludes the complete `response.output` subtree and
  no longer scrubs outgoing request dictionaries. Both real API requests
  complete normally.
- Verification completed:
  - 37 focused usage and sanitizer tests passed;
  - the ordinary real-API usage test passed and confirmed all five current
    usage roots, `cached_tokens`, `reasoning_tokens`, and `total_tokens`;
  - the `gpt-5.6-luna` tool-loop mutation probe passed with a real
    `add(123, 456)` call and no retained non-ignored marker;
  - 422 existing OpenAI Responses tests passed with the three previously known
    unrelated attachment-history failures excluded;
  - Ruff, Black, and diff checks passed;
  - targeted Pyright continued to report only the existing provider protocol
    signature and inference errors in the usage extension.
- The repository-local read-only dry scan inspected 630 canonical records:
  390 live sessions and 240 snapshots. Four records would change, all for
  session `ee99d1cb-be3c-4d39-882f-06c3a2afbbd1`: one live session and three
  snapshots containing 17 core, 14 phase, and 17 native copies of
  `compute_units`. No newly disallowed nested usage field was found. Projected
  savings remain 1,702 bytes. The report is
  `/tmp/ourp-openai-records-exact-paths-dry-run-20260912.json`.
- No session or snapshot was rewritten because the active CLI still prevents a
  confirmed no-writer window. No commit was created.