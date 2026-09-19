# Current guidance status

This page summarizes the currently adopted guidance layers. Dated evaluation
reports remain the detailed evidence.

| Layer | Current state | Delivery |
|---|---|---|
| Documentation and specification guide | Current project-independent guide under `docs/development/documentation.md` | Workspace page; may also be injected explicitly by an evaluation |
| Portable Documentation section | Current bundle at commit `2a8f477b` | Compiled into each target `AGENTS.md`; effective delivery depends on the host |
| Portable root Requirements section | Empty baseline; combined-v2 remains a candidate | Compiled repository guidance |
| Portable root Testing section | Current concise baseline | Compiled repository guidance |
| Task-file guidance | Accepted v3 in canonical `agents/TASKS-v7.md` | Task-enabled developer message |
| Crystal Lattice routing | Current target-local section | Compiled root repository guidance |
| IOCharts adoption | Current portable bundle plus IOCharts-local target; migration is not yet committed in IOCharts | IOCharts root guidance plus Crystal Lattice task-enabled developer message |

The [September 18 portable comparison](documentation-guidance/20260918-portable-root-guidance-results.md)
is preserved as historical direct-injection evidence. It is not
default-runner calibration: GLM could replace the normal Claude message, GPT
could duplicate AGENTS after normal Codex compilation, and both modes bypassed
the normal TASKS toggle. The required default-runner replacement is recorded
below.

The [corrected default-runner comparison](documentation-guidance/20260918-default-runner-results.md)
is complete. Combined-v2 wins 34 of 42 pairwise reviews and materially improves
scope restraint and testing, but complete requirements fall from 36/42 to
35/42. It remains a candidate pending a focused v3 completeness correction and
full confirmation.
