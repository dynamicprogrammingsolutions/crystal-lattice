# Agent guidance compiler requirements

These requirements define generic source, target, compilation, lock, and
promotion behavior. Section semantics and repository-specific outputs are owned
by consuming guidance specifications.

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| GCOMP-001 | Maintainer-owned guidance source has documented current bundles, candidate overlays, project targets, and deterministic compiler ownership outside evaluation fixtures. | Implemented | Automated | Documented | `maintainer/guidance/`; compiler tests; subtask 071 |
| GCOMP-002 | Base files use named single-occurrence slots and compilation rejects missing, duplicate, unknown, or unused mappings without supporting arbitrary template execution. | Implemented | Automated | Documented | `maintainer/guidance/compiler.py`; duplicate/unused-slot tests |
| GCOMP-003 | Shared bundle sections and target-local templates or sections are distinct inputs. A compiler source does not need to store another project's target, and bundle and target may be supplied through independent paths. | Implemented | Automated | Documented | Independent-path compiler and temporary external-target tests |
| GCOMP-007 | Compilation and evaluation default to the current portable bundle and accept an explicit candidate bundle plus a consuming-repository target path without permanently pinning a test to a commit or candidate. Historical versions use a checkout or worktree at that revision. | Implemented | Automated | Documented | Independent absolute-path compiler; external-target environment selection; evaluation guide |
| GCOMP-008 | Every compilation records compiler version, bundle/target paths, optional independently detected Git metadata, input hashes, output hashes, and a location-independent compilation hash used by evaluation cache and dataset identity. | Implemented | Automated | Documented | Compiler lock; cross-location hash test |
| GCOMP-009 | A consuming project can compile shared sections using its own templates and local sections without copying those project-owned inputs into the bundle repository. | Implemented | Automated | Documented | Temporary external-target compiler test and target-isolation tests |
| GCOMP-010 | Promotion remains manual: accepted candidate sections are merged into current source, repository files are compiled explicitly, and tests never promote guidance automatically. | Implemented | Automated | Documented | Separate compiler `check`/`compile`/`write` commands; candidate tests use temporary compiled content |
| GCOMP-013 | Deterministic tests prove compilation, historical-ref selection, working-tree pinning, target isolation, candidate overrides, repository-output checks, and exact evaluation provenance. | Implemented | Automated | Documented | 8 compiler tests; 105 maintainer evaluator tests; compilation checks |
