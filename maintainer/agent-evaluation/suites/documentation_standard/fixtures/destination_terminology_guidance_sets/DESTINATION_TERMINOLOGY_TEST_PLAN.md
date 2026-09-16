# Destination-terminology guidance-set test plan

Status: Draft for compiled-set review

## Outcome

Compare whether explicit context names or a defined `context` term are more
effective than the grouping terms `input material`, `destination`, and
`artifact`, while keeping separate evidence for:

- preventing terminology from entering a new file or record;
- removing inappropriate terminology already present in edited content;
- preserving exact requested and established terms;
- reducing remaining variation through comprehensive context-specific rules.

The repository's current guidance remains unchanged during comparison.

## Candidate matrix

The committed fixture provides one checkpoint and ten candidate sets:

| Wording | Generic only | Comprehensive rules |
|---|---|---|
| Abstract grouping-term control | `abstract-generic` | `abstract-specific` |
| Explicit action-first | `action-first-generic` | `action-first-specific` |
| File- and reader-centered | `file-centered-generic` | `file-centered-specific` |
| Explicit maintained contexts | `explicit-contexts-generic` | `explicit-contexts-specific` |
| Defined `context` and `audience` | `contextual-generic` | `contextual-specific` |

All wording families use the same examples. All specific sets use the same
comprehensive rule section.

No specific-set run begins until all generic-set runs are complete, inspected,
and recorded.

## Compiled-set verification

Before real-model execution:

1. Run `compile.py --check`.
2. Validate every manifest through `GuidanceSource`.
3. Confirm that only `AGENTS.md` and
   `docs/development/documentation.md` differ from `option-a-checkpoint`.
4. Confirm that each generic/specific pair has the same root guidance and
   differs only by the comprehensive guide section.
5. Confirm that all examples are identical across wording families and remain
   separate from scenario vocabulary.
6. Review the complete generated root and guide for every set.
7. Review pairwise diffs against the checkpoint and between each
   generic/specific pair.

The first real-model branch for each set is an empirical loading check:

- recorded guidance name and hash match `guidance-set.json`;
- the workspace contains the compiled files;
- the injection record contains the expected paths and strategy;
- the output is inspected before the rest of that set's matrix starts.

## Behavioral split

### Prevention

Test 30 remains the primary new-record prevention scenario. Its specification,
requirements, decisions, and developer index are created during the run.

Test 31 remains prevention coverage for newly added source and test
identifiers, comments, requirement traces, evidence, and developer
documentation.

### Remediation

Add a focused scenario whose existing user page contains an internal progress
label before the run while the new prompt and active task do not repeat it.

The scenario verifies that the agent:

- edits the affected page within authorized scope;
- removes the inherited label;
- preserves supported behavior;
- preserves established public terminology;
- introduces no replacement planning or tracking terminology.

Test 13 remains broader integration coverage. It is not the focused evidence
for either prevention or remediation because it combines inherited wording,
new phase wording, current behavior, and future-target boundaries.

### Preservation controls

Tests 04 and 14 verify that established contract terminology remains intact.
Legacy documentation-state assertions are reported separately from terminology
behavior.

## Execution order

### 1. Preparation

1. Complete compiled-set review.
2. Add the focused remediation fixture, contract, and consumer.
3. Confirm prevention destinations do not contain their held-out terms
   initially.
4. Confirm remediation content contains its held-out term initially while its
   prompt does not.
5. Record fixture hashes and sizes.

### 2. Generic comparison

Run all five generic sets at high effort on both providers:

- Test 13;
- all three Test 30 variants;
- all three Test 31 variants;
- the focused remediation scenario;
- Tests 04 and 14.

Inspect complete files, diffs, responses, tool use, and provenance. Freeze the
generic result matrix before continuing.

Evidence that a wording improves on `abstract-generic` requires:

- at least one prevention improvement;
- at least one remediation improvement;
- no semantic regression in exact or established terms;
- confirmation in a fresh repeat or another model or effort.

### 3. Specific comparison

Run the same high-effort matrix for all five specific sets. Compare every
specific set directly with its generic counterpart.

The comprehensive rules are useful when they improve model or effort
combinations that did not respond to generic wording, especially:

- task and sequence references in Test 30;
- requirement traceability in Test 31;
- inherited current-page terminology in the remediation scenario and
  Test 13.

### 4. Repeats and effort sentinels

For `abstract`, the strongest explicitly enumerated candidate, and the
strongest concise candidate:

1. Repeat high-effort Test 13, remediation, and the task-number and
   sequence-label Test 30 variants.
2. Run low and max effort for Test 13, remediation, and Test 30
   sequence-label.
3. Run one fresh Test 31 requirement-traceability sample on both providers.

Invalid provider, transport, or incomplete-tool-budget runs are excluded and
rerun. Recoverable tool errors remain in evidence.

## Temporary parallel execution

Task-local orchestration may run at most:

- five GLM/Ollama-profile processes;
- five GPT/OpenAI-profile processes;
- ten total processes.

The five wording families fit in one batch per provider. Generic and specific
batches do not overlap.

The temporary launcher sets:

- guidance set name and directory;
- model profile and reasoning effort;
- unique branch cache label and sample number;
- separate log path.

It records PIDs and exit status and stops its children if interrupted. It is
not committed unless the work reveals a reusable, non-trivial capability.

## Selection and publication

Selection considers prevention and remediation separately, both providers,
effort variance, established-term preservation, full artifact quality,
readability, portability, and final consolidated size.

After human selection:

1. Consolidate overlapping public-guide prose.
2. Apply the selected portable-guide and root wording.
3. Recheck current-guide size limits.
4. Rerun decisive cases against the actual repository guidance.
5. Update specifications, requirements, task evidence, and dated results.

Task-file guidance remains a later comparison owned through
`tasks/20260728-package-local-documentation-standard/068-task-guidance-specification-alignment.md`.
