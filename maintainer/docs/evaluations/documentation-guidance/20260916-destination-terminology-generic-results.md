# September 16, 2026 destination-terminology generic results

> Historical interpretation: these runs used complete directory-backed
> guidance sets with provider-specific direct injection. They are wording
> comparison evidence, not current production-runner acceptance. Historical
> Tests 30 and 31 map to active Tests 36 and 37. Historical Test 32 is
> superseded by active Test 38, which requires confirmation before removing
> existing wording.

## Scope

This comparison evaluates the five generic-only guidance sets committed in
`ef936892`:

- `abstract-generic`;
- `action-first-generic`;
- `file-centered-generic`;
- `explicit-contexts-generic`;
- `contextual-generic`.

Each set ran at high reasoning effort on GLM and GPT with unchanged prompts,
fixtures, assertions, and provider profiles.

The main matrix contains Tests 04, 13, 14, all three Test 30 variants, and all
three Test 31 variants. Test 32 ran first as the separate remediation and
guidance-loading check.

## Provenance

All ten generic Test 32 runs recorded:

- the expected guidance-set name and manifest SHA-256;
- candidate guidance copied into the isolated workspace;
- guidance injection enabled;
- GLM's leading-system-message strategy or GPT's late endpoint-instruction
  strategy as appropriate;
- exactly one changed current user page.

All 90 high-effort matrix branches completed with matching guidance hashes and
no provider errors.

One original GLM `file-centered-generic` process stopped producing evidence
after seven branches and remained in one request for approximately 18 minutes.
It was excluded as incomplete. Fresh focused runs completed the two missing
Test 31 variants: sequence-label failed and evaluative wording passed.

## Test 32 remediation reference

The `option-a-checkpoint` set passed Test 32 on both providers.

All generic candidates passed on both providers except
`action-first-generic` on GLM. That run removed the inherited
`Milestone Cedar` heading but added target-only replay as a current
“Limitation,” contrary to the prompt's explicit replay exclusion.

The result demonstrates model and wording variation but not a general
remediation improvement over the checkpoint.

## High-effort matrix

`P` means all assertions passed. `F` means at least one assertion failed.

### GLM

| Candidate | 04 | 13 | 14 | 30 task | 30 sequence | 30 evaluative | 31 task | 31 sequence | 31 evaluative | 32 |
|---|---|---|---|---|---|---|---|---|---|---|
| Abstract | P | F | P | P | P | P | P | F | P | P |
| Action-first | P | F | P | F | P | P | F | P | P | F |
| File-centered | P | F | P | F | F | P | P | F | P | P |
| Explicit contexts | P | F | P | F | F | P | P | P | P | P |
| Contextual | P | F | P | F | P | P | P | P | P | P |

### GPT

| Candidate | 04 | 13 | 14 | 30 task | 30 sequence | 30 evaluative | 31 task | 31 sequence | 31 evaluative | 32 |
|---|---|---|---|---|---|---|---|---|---|---|
| Abstract | F | F | P | P | P | P | F | F | P | P |
| Action-first | F | F | F | F | P | P | F | F | F | P |
| File-centered | P | F | F | P | P | P | F | P | F | P |
| Explicit contexts | P | F | F | P | F | F | F | P | P | P |
| Contextual | P | F | F | P | F | P | P | P | F | P |

## Failure interpretation

### Test 13

Every generic candidate failed Test 13 on both providers. Outputs retained
Phase 1/2 grouping, added the future Phase 3 boundary, or both. Generic
prevention/remediation language alone did not reliably clean an existing
current user page in this combined partial-implementation workflow.

### Test 30

Failures were genuine maintained-record leaks:

- task-number wording appeared in specification or decision prose;
- `Stage A` appeared in specification records;
- evaluative wording influenced formal record descriptions in one
  explicit-context GPT sample.

GLM abstract passed all three Test 30 cases. GPT abstract and file-centered
also passed all three. Other candidates varied by source-term class.

### Test 31

Most failures used `STATUS-002` without explaining the assertion:

- a bare comment before or beside assertions;
- a requirement ID used as part of a test function name;
- an ID-only comment attached to a test rather than behavior.

One GLM abstract sequence-label run also retained source wording in maintained
implementation text.

GLM contextual and explicit-contexts passed all three Test 31 variants. No GPT
candidate passed all three; contextual passed task and sequence, while
file-centered and explicit-contexts each passed only one or two variants.

### Tests 04 and 14

The Test 04/14 failures were the known live-state expectation difference:
requirements were marked documented rather than remaining pending. Established
contract terminology was preserved. These failures are reported separately
from destination-terminology behavior.

## Generic-stage conclusion

No generic wording is uniformly strongest across both providers.

- Abstract is strongest for Test 30 prevention, especially on GLM.
- Contextual and explicit-contexts are strongest for GLM Test 31.
- File-centered is strong for GPT Test 30.
- Action-first is weakest overall in this sample and is the only generic
  candidate to fail the focused GLM remediation case.
- Test 13 remains unresolved by every generic candidate.

The generic variants nevertheless produce different behavior in several model
and boundary combinations. The next paired comparison should add the same
comprehensive context-specific rule section to every wording family and
measure whether it closes the remaining task-reference, requirement-reference,
and inherited-user-documentation variation.