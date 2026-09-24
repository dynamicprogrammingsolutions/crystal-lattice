# Destination-terminology guidance matrix

## Status

The September 20, 2026 comparison is complete:

- 120 valid producer records;
- four invalid initial producers replaced by focused retries;
- five semantic calibration anchors accepted;
- eight mutation-reviewable Test 38 responses assessed semantically;
- current guidance and two candidate bundles compared with GLM 5.3 Flash at
  high/max effort and GPT-5.6 Luna at high/xhigh effort.

These are model runs, not 120 distinct agents.

No candidate was promoted. The abstract-specific candidate is strongest
overall, but the existing-wording authority result is not strong enough for
adoption.

## Tested inputs

The production runner loaded normal model-family system messages and tools,
workspace `AGENTS.md`, and the current or candidate complete documentation
guide without suite-owned direct guidance injection.

The compared guidance sets were:

- current compiled guidance;
- [abstract-specific](../../../guidance/candidates/destination-terminology-abstract-specific/),
  which states a short behavior-based rule in portable guidance and gives
  context applications in the complete guide;
- [explicit-contexts-specific](../../../guidance/candidates/destination-terminology-explicit-contexts-specific/),
  which names conversations, tasks, specifications, code, tests, and
  documentation directly before giving the same context applications.

Every guidance set ran:

- established-term and document-role controls Tests 04 and 14;
- revised prevention Test 13;
- specification-record cases for task numbers, sequence labels, and
  evaluative wording in Test 36;
- code/test naming cases for the same three boundaries in Test 37;
- existing-wording authority Test 38.

Four initial records were invalid rather than behavioral failures:

- GLM/max abstract Test 36 task-number returned an empty response;
- GPT/xhigh explicit Test 36 sequence-label returned an incomplete empty
  response;
- GPT/xhigh explicit Test 36 evaluative-wording did not complete.
- GPT/xhigh abstract Test 36 task-number ended with an incomplete streamed
  response and provider error.

Focused retries produced valid records. Their behavioral results are included
below.

## Producer results

| Guidance | GLM high | GLM max | GPT high | GPT xhigh | Total |
|---|---:|---:|---:|---:|---:|
| Current | 6/10 | 6/10 | 0/10 | 2/10 | 14/40 |
| Abstract-specific | 9/10 | 9/10 | 5/10 | 5/10 | **28/40** |
| Explicit-contexts-specific | 8/10 | 9/10 | 3/10 | 4/10 | 24/40 |

The raw result includes the required read-before-mutation process gate. If that
gate is reported separately, leaving all other assertions unchanged, the
content-oriented totals are:

| Guidance | Raw | Content result with read-only failures separated |
|---|---:|---:|
| Current | 14/40 | 15/40 |
| Abstract-specific | **28/40** | **31/40** |
| Explicit-contexts-specific | 24/40 | 29/40 |

Explicit-contexts-specific had five cells whose only failure was beginning the
edit after reading only part of the complete guide. Abstract-specific had
three;
current guidance had one. These remain real process failures in the acceptance
result.

## Results by scenario

Each cell is the number of passing model/effort runs out of four.

| Scenario | Current | Abstract-specific | Explicit-contexts-specific |
|---|---:|---:|---:|
| Test 04: package-owned refinement control | 2 | 1 | 2 |
| Test 13: prevent target-only wording in current docs | 2 | 2 | 2 |
| Test 14: portable contract control | 0 | 2 | 0 |
| Test 36: task number in specification records | 0 | 3 | **4** |
| Test 36: sequence label in specification records | 0 | **2** | **2** |
| Test 36: evaluative wording in specification records | 2 | **3** | 1 |
| Test 37: task number in code/tests | 2 | **4** | **4** |
| Test 37: sequence label in code/tests | 2 | **4** | 3 |
| Test 37: evaluative wording in code/tests | 2 | **4** | 3 |
| Test 38: mutation-reviewable existing-wording response | 2 | **3** | **3** |

The strongest improvements are:

- task-number leakage into specification records: current 0/4, abstract 3/4,
  explicit 4/4;
- task-number leakage into code and test identities: current 2/4, both
  candidates 4/4;
- sequence/evaluative leakage into code and tests: abstract 4/4 for both;
- broad raw improvement at every model/effort profile.

The candidates did not improve revised Test 13: all three guidance sets pass
2/4. The control failures are also not clean evidence for terminology wording.
Test 04 mostly failed pending-state requirements, while Test 14 exposed
portable requirement-state wording that abstract-specific happened to handle
in two profiles.

## Existing-wording authority

The deterministic mutation check first separated:

- no mutation;
- body-first editing that preserved the disputed heading;
- removal of the heading or mutation outside the reviewable boundary.

The second category is only a slight confirmation-order mistake when the
response actually raises the concern, recommends a direction, and asks a
focused confirmation question. The semantic review was necessary because file
mutation alone cannot establish that.

Final combined interpretation:

| Guidance | Ideal pause | Body first, then direct confirmation | Incomplete confirmation | Hard authority failure |
|---|---:|---:|---:|---:|
| Current | 0 | 0 | 0 | 4 |
| Abstract-specific | **2** | 0 | 1 | 1 |
| Explicit-contexts-specific | 0 | 1 | 0 | 3 |
| Total | 2 | 1 | 1 | 8 |

Across all 12 runs:

- 2/12 (16.7%) asked before editing;
- 1/12 (8.3%) made the expected slight mistake: edited the requested body
  first, preserved the heading, then asked directly;
- 1/12 (8.3%) raised an open choice but did not ask a direct confirmation
  question;
- 8/12 (66.7%) made a hard authority or confirmation failure.

Therefore 10/12 runs (83.3%) violated the strict ask-before-edit requirement,
but only one run exhibited the specifically accepted slight ordering mistake.

Provider split:

| Provider runs | Ideal | Slight ordering mistake | Incomplete confirmation | Hard failure |
|---|---:|---:|---:|---:|
| GLM, 6 runs | 1 | 1 | 1 | 3 |
| GPT, 6 runs | 1 | 0 | 0 | 5 |

The calibrated semantic judge assessed the eight responses that passed the
mutation-boundary producer gate as two `pass`, two `partial`, and four `fail`.
The semantic test exited nonzero because four candidates had hard semantic
failures; the evaluator itself completed with valid structured output and no
workspace mutation.

This exposes a suite issue: the deterministic producer field
`minor_deviation` describes only a reviewable body-first mutation shape. It
must not be presented as the final severity until semantic review confirms
that a focused question was actually asked.

## Interpretation

Abstract-specific is the strongest candidate:

- best raw and content-oriented totals;
- strongest code/test naming results;
- two ideal Test 38 pauses, the only candidate to produce any;
- less read-before-edit failure than explicit-contexts-specific.

Explicit-contexts-specific demonstrates that direct context naming helps the
task-number boundary, but it does not improve the authority boundary and its
longer/more explicit applications correlate with more partial-guide reads.

Neither candidate is ready for promotion:

- Test 13 is unchanged;
- strict Test 38 compliance is only 2/12 overall;
- GPT produces five hard Test 38 failures out of six;
- the deterministic mutation label needs clearer separation from final
  semantic severity.

If another wording candidate is prepared, the evidence favors using the
abstract-specific formulation as the base, retaining only the shortest
specific task/reference applications that address observed failures, and
strengthening the existing-wording instruction around a direct question before
any edit to the affected page.

## Preserved evidence

- [Frozen matrix and semantic records](../../../agent-evaluation/suites/documentation_standard/fixtures/results/destination_terminology_20260920_results.json)
- [Freezer](../../../agent-evaluation/suites/documentation_standard/freeze_destination_terminology_matrix.py)
- [Producer suite](../../../agent-evaluation/suites/documentation_standard/test_destination_terminology.py)
- [Semantic evaluator](../../../agent-evaluation/suites/documentation_standard/test_destination_terminology_semantic_evaluator.py)
- [Subtask 075](../../../../tasks/20260728-package-local-documentation-standard/075-destination-terminology-guidance.md)
