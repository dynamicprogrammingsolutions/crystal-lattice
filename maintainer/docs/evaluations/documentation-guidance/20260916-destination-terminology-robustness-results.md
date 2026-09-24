# September 16, 2026 destination-terminology robustness results

> Historical interpretation: these runs used complete directory-backed
> guidance sets with provider-specific direct injection. They are wording
> comparison evidence, not current production-runner acceptance. Historical
> Tests 30 and 31 map to active Tests 36 and 37. Historical Test 32 is
> superseded by active Test 38, which requires confirmation before removing
> existing wording.

## Scope

This follow-up tests the three specific-rule candidates selected after the
[paired generic/specific comparison](20260916-destination-terminology-specific-results.md):

- `abstract-specific`;
- `explicit-contexts-specific`;
- `file-centered-specific`.

The matrix contains:

- a fresh high-effort repeat of Test 13, Test 30 task/sequence, Test 31
  task-number, and Test 32;
- low- and max-effort sentinels for Test 13, Test 30 sequence-label, and
  Test 32;
- both GLM and GPT profiles.

## Provenance and invalid runs

All valid branches recorded the expected candidate name, manifest SHA-256,
reasoning effort, injection strategy, and provider profile.

Two GPT `abstract-specific` max-effort Test 30 sequence runs reached the
default 30-tool-call stop condition without a final assistant response. They
are excluded as incomplete. The same unchanged branch completed and passed
with `AGENT_EVAL_MAX_TOOL_CALLS=50`.

No valid branch reported a provider error.

## Fresh high-effort repeat

| Profile | Candidate | 13 | 30 task | 30 sequence | 31 task | 32 |
|---|---|---|---|---|---|---|
| GLM | Abstract | F | P | F | P | P |
| GLM | Explicit contexts | F | F | P | P | P |
| GLM | File-centered | F | P | P | P | P |
| GPT | Abstract | F | F | F | P | P |
| GPT | Explicit contexts | F | F | F | P | P |
| GPT | File-centered | F | P | P | P | P |

The repeat confirms stochastic Test 30 behavior. File-centered passed both
task and sequence variants on both providers, while abstract and
explicit-contexts regressed from their first high-effort samples.

Test 31 task-number and Test 32 passed all six repeats.

## Low-effort sentinels

| Profile | Candidate | 13 | 30 sequence | 32 |
|---|---|---|---|---|
| GLM | Abstract | F | P | P |
| GLM | Explicit contexts | F | P | F |
| GLM | File-centered | F | P | P |
| GPT | Abstract | F | P | P |
| GPT | Explicit contexts | F | P | P |
| GPT | File-centered | F | F | P |

The GLM explicit-contexts Test 32 failure removed the inherited heading but
added that failed events cannot currently be replayed, contrary to the prompt's
replay exclusion.

## Max-effort sentinels

| Profile | Candidate | 13 | 30 sequence | 32 |
|---|---|---|---|---|
| GLM | Abstract | F | P | P |
| GLM | Explicit contexts | F | P | P |
| GLM | File-centered | F | P | P |
| GPT | Abstract | F | P | P |
| GPT | Explicit contexts | F | P | P |
| GPT | File-centered | F | F | P |

The GPT abstract Test 30 result is the completed higher-budget rerun.

## Cross-stage robustness

### Existing current documentation

Test 13 failed in all 24 selected candidate/provider samples across the first
high run, fresh high repeat, low effort, and max effort.

The recurring output either retained Phase 1/2 grouping or introduced the
future Phase 3 boundary. Neither the generic examples nor the comprehensive
context table made this combined partial-implementation case robust.

### Requirement traceability

The comprehensive specific section has strong evidence:

- all 30 Test 31 variants in the full specific matrix passed;
- all six fresh Test 31 task-number repeats passed.

The requirement-reference rule and explanatory comment example should remain
substantively unchanged.

### Focused remediation

Across the full specific smoke, fresh high repeat, low effort, and max effort,
Test 32 passed 27 of 28 runs.

The one failure did not retain the inherited heading; it introduced excluded
target behavior as a current limitation. The removal rule is strong, while
the user-documentation future-work boundary still benefits from a focused
application example.

### Task and sequence references

Test 30 remains the main stochastic boundary:

- explicit-contexts passed sequence-label in seven of eight selected
  provider/effort samples;
- abstract passed six of eight;
- file-centered passed four of eight, despite passing both providers in the
  fresh high repeat;
- task-number passed nine of twelve first-high/fresh-high selected samples.

Remaining outputs append task-local wording to otherwise descriptive links or
provenance, such as `(Stage A)`, `Stage A authorization`, or `Task 010 also
authorizes`.

## Conclusion

The comprehensive specific rules are justified, especially for requirement
traceability and focused remediation. They do not make one generic wording
family uniformly superior.

- Abstract remains the strongest control and is competitive across boundaries.
- Explicit-contexts is the strongest non-abstract candidate for sequence-label
  robustness.
- File-centered performs well in the fresh high repeat but is less stable
  across effort levels.
- Action-first should not be selected from this evidence.
- Test 13 requires a focused current-user-documentation application example or
  stronger specific instruction before another behavioral comparison.
- The task-reference rule should explicitly say that a descriptive task link
  is not followed by a local stage, number, or nickname.

No further guidance rewrite is applied in this result stage.