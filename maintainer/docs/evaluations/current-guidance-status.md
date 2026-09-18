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
has valid root-only producer, semantic, and complete pairwise evidence. All
task-mode agents created task files, but the recorder initially missed their
retained content and the suite delivered root and task guidance through one
instruction layer. Task-mode semantic and pairwise conclusions therefore
remain unavailable until delivery is corrected and rerun.
