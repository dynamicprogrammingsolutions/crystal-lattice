# Warning and diagnostic de-noising

Aggregate repeated equivalent warnings and keep diagnostic output bounded without hiding distinct failures or the information needed to identify their source.

## Requirements checklist

- [ ] **LOG-001** Repeated equivalent reserved-key or lifecycle warnings are rate-limited or aggregated within a defined request/time scope.
- [ ] **LOG-002** The first occurrence retains the plugin/component, key, request/session correlation, and actionable context needed to diagnose the condition.
- [ ] **LOG-003** Aggregated output reports a bounded occurrence count or summary so repetition remains visible.
- [ ] **LOG-004** Distinct keys, responsible plugins/components, exception classes, or materially different contexts are not collapsed into one misleading warning.
- [ ] **LOG-005** Diagnostic logging does not include complete large session/message payloads, credentials, secrets, or unnecessary user content.
- [ ] **LOG-006** Quiet/provider-waiting periods do not generate warning output without a new triggering condition.
- [ ] **LOG-007** Aggregation state is bounded and does not create an unbounded in-memory key cache.
- [ ] **LOG-008** Automated tests cover first occurrence, repeated occurrence, aggregation flush/reset, distinct conditions, concurrent requests, and sensitive-data exclusion.
- [ ] **LOG-009** Shared benchmark or focused measurement demonstrates a substantial reduction from warning-storm output without losing distinct diagnostics.

## Scope

In scope:

- Repeated reserved-context-key and closely related lifecycle warnings observed during request/tool phases.
- Logger call sites, aggregation/rate-limit helper behavior, correlation fields, bounded state, and tests.
- Applicable owning development/troubleshooting documentation.

Out of scope:

- General log framework replacement.
- Suppressing distinct exceptions.
- Session persistence and bridge transport changes.

Parent Task: `tasks/20260911-session-performance-and-storage-optimization/000-main.md`

Depends On: `tasks/20260911-session-performance-and-storage-optimization/010-session-growth-and-benchmark-foundation.md`

## Supporting details

One sampled recent log window contained 1,997 repeated reserved-key warnings among 2,000 lines. A separate quiet interval showed no growth, indicating an episodic request-phase warning storm rather than an unconditional background loop.

## Execution plan

Status: Draft

Identify the exact warning producers and define an equivalence key using bounded identifiers such as component/plugin, warning type, and reserved key. Emit the first warning normally, count repeats for a request or bounded time window, and emit one summary when the scope closes or expires.

Prefer request-scoped aggregation where request context is available. Use a bounded TTL/LRU fallback only for warnings that occur outside a request lifecycle.

### Implementation decisions and open questions

- Select request-scoped versus time-window aggregation for each warning source.
- Define which fields make two warnings equivalent without including large or sensitive values.
- Decide when summaries flush on success, failure, cancellation, and process shutdown.
- Preserve existing logger interfaces unless a shared bounded aggregation helper has more than one real consumer.

### Documentation

- Update owning development/troubleshooting documentation if warning wording or aggregation behavior is user-visible during diagnostics.
- Keep implementation counters and task evidence out of public user documentation unless they become a supported diagnostic interface.

### Task checklist

- [ ] Locate and classify the repeated warning producers.
- [ ] Add regression tests reproducing a warning storm.
- [ ] Define bounded equivalence keys and sensitive-data exclusions.
- [ ] Implement request-scoped aggregation and bounded fallback where needed.
- [ ] Emit first-occurrence and summary diagnostics.
- [ ] Verify cancellation, error, and concurrent-request cleanup.
- [ ] Run focused logging and owning package test suites.
- [ ] Measure output and synchronous logging reduction with the shared fixture.
- [ ] Update applicable documentation and evidence.

### Requirement verification

- **LOG-001 through LOG-004:** Run deterministic repeated and distinct warning cases and inspect structured/captured records.
- **LOG-005:** Exercise representative sensitive/large values and verify they are absent from output.
- **LOG-006:** Observe a controlled quiet interval after the triggering request phase.
- **LOG-007:** Stress unique equivalence keys and inspect bounded state/eviction behavior.
- **LOG-008:** Run the owning automated test suite including concurrent and cancellation cases.
- **LOG-009:** Compare warning count, log bytes, and request-phase overhead before and after aggregation.

### Additional implementation verification

- Verify aggregation failures cannot interrupt the request/tool lifecycle.
- Verify summary logging does not recursively trigger the same aggregation path.