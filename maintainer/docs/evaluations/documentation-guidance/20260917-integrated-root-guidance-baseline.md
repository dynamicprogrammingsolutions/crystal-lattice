# Integrated root-guidance baseline

Date: September 17, 2026

This baseline records the repository after reconciling:

- `task/20260728-core-python-documentation-migration`;
- `task/20260914-guidance-follow-up-rewrites`;
- the accepted v3 documentation and task guidance on
  `task/20260728-documentation-guide-rewrite`.

The incomplete
`task/20260914-destination-vocabulary-guidance` branch is not merged.

## Integrated revisions

- Core documentation merge: `8c26812e`
- Root-guidance follow-up merge: `9c30e16c`
- Baseline branch: `task/20260728-documentation-guide-rewrite`

## Guidance provenance

| Source | Words | SHA-256 |
|---|---:|---|
| Root `AGENTS.md` | 3,080 | `a56c068e7ea8357f7ef7f045e5a36c15194dc8d271517434ef74dc2bb8b1c54f` |
| Root documentation policy section | 289 | part of the root hash above |
| `docs/development/documentation.md` | 2,074 | `0dc4d6265c13ad606d447bb9f9ee2387961dad6d4a6329d9ea8f52fa43ee0e35` |
| Canonical `agents/TASKS-v7.md` | 1,461 | `191fc888e8bc987e0a76b631ab362386157ed58e04fa4e56140767f3b2ab1d6c` |
| Bundled `TASKS_v7.md` | 1,461 | `191fc888e8bc987e0a76b631ab362386157ed58e04fa4e56140767f3b2ab1d6c` |

Test 27's injected root-guidance source hash is:

`b8b890674fb4ce964ae011615eec547383a81ddb03c95eefbb707021e7d40242`

## Structural result

The integrated root guidance has:

- one documentation policy/routing section;
- the current Core package documentation route;
- one development-documentation hub route;
- no duplicate root documentation command catalog;
- no later documentation-update policy block;
- no `unit first` testing default;
- the boundary-first testing sentence from the completed follow-up;
- unchanged v3 requirements/testing documentation and canonical task guidance;
- the long-running-work instructions from the completed follow-up.

## Verification

- Core default tests:
  `528 passed, 1 xfailed, 26 deselected`.
- Core examples:
  `5 passed, 8 deselected`.
- Two example-generator runs produced
  `6c465e63b5a6602743fc2dd2c9c38a3d4c582acd1c684073db3d0ba5497f8244`.
- Maintainer agent-evaluation tests: `89 passed`.
- Root documentation-standard deterministic tests: `31 passed`.
- Documentation assembly tests: `15 passed`.
- Canonical/bundled task-guidance parity: `2 passed`; synchronization check
  passed.
- Compiled task-guidance integration: `1 passed`.
- Documentation preparation and the normal MkDocs build passed with only
  existing repository warnings.
- Focused relative-link validation passed.

## Integrated Test 27

Run:
`20260917T062658.996289Z-27-routed-current-guidance-e2c0e3e7`

Model:
`glm-5.3-flash:cloud`

The run passed every deterministic routing assertion:

- only root `AGENTS.md` was injected;
- both current guidance pages were read completely before the first mutation;
- maintainer specifications were not read;
- all changes remained package-local and documentation-only;
- target-only replay behavior was not presented as available;
- user documentation did not link directly to internal specifications.

The generated response also noted that `publish()` did not itself call the
retry helper while retaining retry wording from the package specification.
Therefore this run is routing evidence only. It is not evidence that all
resulting user-documentation claims were independently verified.

## Next comparison

Keep this integrated documentation and task guidance fixed while evaluating:

1. a root Requirements-only candidate;
2. a root Testing-only candidate;
3. the combined root candidate.

Each candidate must be exercised both without task guidance and with canonical
`TASKS-v7` active. The committed v3 requirement/testing records remain the
documentation-plus-TASKS baseline and are not overwritten.