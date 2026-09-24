# September 16, 2026 destination-terminology specific results

> Historical interpretation: these runs used complete directory-backed
> guidance sets with provider-specific direct injection. They are wording
> comparison evidence, not current production-runner acceptance. Historical
> Tests 30 and 31 map to active Tests 36 and 37. Historical Test 32 is
> superseded by active Test 38, which requires confirmation before removing
> existing wording.

## Scope

This comparison adds the same comprehensive context-specific rule section to
each wording family evaluated in the
[generic stage](20260916-destination-terminology-generic-results.md).

Each specific set ran at high reasoning effort on GLM and GPT with the same
prompts, fixtures, assertions, and model profiles:

- `abstract-specific`;
- `action-first-specific`;
- `file-centered-specific`;
- `explicit-contexts-specific`;
- `contextual-specific`.

## Provenance

All ten Test 32 runs and all 90 Tests 04/13/14/30/31 branches:

- completed without provider errors;
- recorded the expected guidance-set name and manifest SHA-256;
- used the expected provider-specific injection strategy;
- preserved the same fixture, prompt, reasoning effort, and assertions as the
  paired generic run.

## High-effort matrix

`P` means all assertions passed. `F` means at least one assertion failed.

### GLM

| Candidate | 04 | 13 | 14 | 30 task | 30 sequence | 30 evaluative | 31 task | 31 sequence | 31 evaluative | 32 |
|---|---|---|---|---|---|---|---|---|---|---|
| Abstract | P | F | P | P | P | P | P | P | P | P |
| Action-first | P | F | P | F | F | P | P | P | P | P |
| File-centered | P | F | P | P | F | P | P | P | P | P |
| Explicit contexts | P | F | P | P | P | P | P | P | P | P |
| Contextual | P | F | P | P | F | P | P | P | P | P |

### GPT

| Candidate | 04 | 13 | 14 | 30 task | 30 sequence | 30 evaluative | 31 task | 31 sequence | 31 evaluative | 32 |
|---|---|---|---|---|---|---|---|---|---|---|
| Abstract | F | F | F | P | P | P | P | P | P | P |
| Action-first | F | F | F | F | P | P | P | P | P | P |
| File-centered | F | F | F | P | F | P | P | P | P | P |
| Explicit contexts | F | F | F | P | P | F | P | P | P | P |
| Contextual | F | F | F | P | F | F | P | P | P | P |

## Paired effects

### Test 31 requirement traceability

The specific section eliminated every Test 31 failure in this matrix:

- all five GLM candidates passed task-number, sequence-label, and evaluative
  variants;
- all five GPT candidates passed all three variants;
- tests used behavior-based names and explanatory requirement references
  rather than bare IDs or ID-only test names.

This is the strongest evidence that the non-obvious requirement-reference
format benefits from a concrete context-specific rule and example.

### Test 30 task and sequence references

Effects varied by wording and provider:

- abstract passed all Test 30 variants before and after the specific section;
- explicit-contexts improved both GLM task/sequence cases and the GPT sequence
  case, leaving only GPT evaluative wording;
- file-centered improved GLM task-number but regressed GPT sequence-label;
- action-first fixed no task-number case and regressed GLM sequence-label;
- contextual fixed task-number but regressed sequence-label, plus GPT
  evaluative wording.

Remaining failures contain actual task or sequence wording in specification
records, such as `Task 010` or `Stage A` in authorization, provenance, or
delivery descriptions.

### Test 32 remediation

Every specific candidate passed on both providers. The specific section fixed
the generic GLM action-first failure that had introduced target-only replay as
a current limitation.

### Test 13 existing current documentation

Every specific candidate still failed Test 13 on both providers. README output
retained Phase 1/2 grouping, and some samples retained or introduced Phase 3.
The comprehensive table did not make this combined partial-implementation case
robust.

### Tests 04 and 14 controls

GPT control failures continue to reflect requirements being marked documented
instead of pending. Established terminology remains preserved, so these are
not destination-terminology failures.

## Candidate selection for repeats

The follow-up effort matrix uses:

- `abstract-specific` as the grouping-term control and strongest overall
  terminology candidate;
- `explicit-contexts-specific` as the strongest explicitly enumerated
  candidate;
- `file-centered-specific` as the next strongest non-abstract candidate.

The repeat stage covers Test 13, Test 32, Test 30 task/sequence, and one fresh
Test 31 requirement-traceability case at high effort, plus low/max sentinels
for Test 13, Test 32, and Test 30 sequence-label.