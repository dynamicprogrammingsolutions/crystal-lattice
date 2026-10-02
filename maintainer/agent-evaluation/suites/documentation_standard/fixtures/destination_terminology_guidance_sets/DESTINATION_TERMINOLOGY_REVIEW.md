# Compiled guidance-set review

Reviewed: September 16, 2026

Reviewer: implementation agent. Independent human review remains pending.

## Scope

The review covered all eleven committed-form sets:

- `option-a-checkpoint`;
- five generic wording candidates;
- five matching comprehensive-specific candidates.

For every candidate, the review inspected:

- the complete compiled root documentation policy in `AGENTS.md`;
- the complete compiled `Write pages readers can use` section in the portable
  guide and its surrounding transition;
- the pairwise diff against `option-a-checkpoint`;
- the pairwise generic/specific diff;
- manifest identity, hashes, and word counts.

Mechanical checks separately proved that the other four guidance files remain
byte-identical to the checkpoint.

## Inventory

| Set | Portable guide words | Root policy words | Combined SHA-256 prefix |
|---|---:|---:|---|
| `option-a-checkpoint` | 2,200 | 294 | `3a4c51039aa4` |
| `abstract-generic` | 2,178 | 294 | `45af4ab7a49c` |
| `abstract-specific` | 2,464 | 294 | `1ea52c931c07` |
| `action-first-generic` | 2,179 | 300 | `27df7d844055` |
| `action-first-specific` | 2,465 | 300 | `887eb4667e43` |
| `file-centered-generic` | 2,170 | 295 | `0ca9f838fc2b` |
| `file-centered-specific` | 2,456 | 295 | `d8883eee997c` |
| `explicit-contexts-generic` | 2,178 | 300 | `421fed7aca9a` |
| `explicit-contexts-specific` | 2,464 | 300 | `a574976813a4` |
| `contextual-generic` | 2,176 | 299 | `8f6606435f62` |
| `contextual-specific` | 2,462 | 299 | `2fadaa4d961e` |

## Observations

- `abstract` consistently uses `input material`, `destination`, and
  `artifact`, providing the intended grouping-term control.
- `action-first` gives direct actions after naming likely preceding records.
- `file-centered` consistently frames choices around a file's purpose,
  readers, and interfaces.
- `explicit-contexts` names maintained record types where the other families
  use a grouping term.
- `contextual` defines context as where wording comes from, where it is used,
  and its audience. It then distinguishes source context from the context of
  the current file or record.
- All five families use the same five portable-guide examples and the same
  root examples.
- Boundary-analysis labels do not appear in the compiled public wording.
- Generic and specific pairs have identical root guidance and identical
  general rules.
- Every specific guide adds the same table and reference examples at the same
  boundary between general terminology guidance and existing verified-example
  guidance.
- The table reads coherently after each wording family and does not require the
  reader to reinterpret the preceding examples.

## Corrections made during review

1. Generic compilation initially left excessive blank space where the
   specific-rule marker was removed. The compiler now replaces the complete
   marker block and preserves one normal section boundary.
2. The first contextual definition described context as a role. It now states
   directly that context covers where wording comes from, where it is used,
   and its audience.
3. A wrapped sentence in the explicit-contexts source was reformatted for
   readability without changing its wording.
4. The contextual deterministic test was changed from requiring one exact
   phrase to verifying the semantic relation between terminology and the
   defined context.

## Empirical loading result

The first real-model branch for every generic and specific set confirmed:

- the recorded guidance name and combined hash match `guidance-set.json`;
- the isolated workspace contains the expected compiled files;
- the guidance-injection record contains the expected paths and strategy;
- the branch uses GLM's leading-system-message strategy or GPT's late endpoint
  instructions as appropriate.

The complete behavioral comparison is recorded in the September 16 generic,
specific, and robustness result pages. Behavioral success varies by candidate;
this section confirms fixture consistency and delivery rather than guidance
quality.
