# Agent guidance source and compilation requirements

These requirements track the live implementation, verification,
documentation, and evaluation state relative to the target specification.

Feature prefix: `GCOMP`

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| GCOMP-001 | Maintainer-owned guidance source has documented current bundles, candidate overlays, project targets, and deterministic compiler ownership outside evaluation fixtures. | Not started | Unverified | Target documented | This specification; subtask 071 |
| GCOMP-002 | Base files use named single-occurrence slots and compilation rejects missing, duplicate, unknown, or unused mappings without supporting arbitrary template execution. | Not started | Unverified | Target documented | Technical specification |
| GCOMP-003 | Shared sections and target-local sections are distinct, so portable requirements/testing rules compile into Crystal Lattice and external-project bases without unrelated repository instructions. | Not started | Unverified | Target documented | Product and technical specifications |
| GCOMP-004 | The current source bundle compiles the maintained root `AGENTS.md` byte-identically before any approved guidance promotion, and check mode detects direct drift. | Not started | Unverified | Target documented | Subtask 071 verification plan |
| GCOMP-005 | Canonical task guidance can use the same source/compilation mechanism without weakening its existing canonical-to-bundled synchronization contract. | Not started | Unverified | Target documented | Technical specification; subtask 068 |
| GCOMP-006 | The combined-v2 candidate is an inspectable candidate directory overriding only its changed sections rather than Python string replacements or a test fixture. | Not started | Unverified | Target documented | Legacy rendered hash `cf943bb…`; subtask 071 |
| GCOMP-007 | Evaluation defaults to the current checkout/current bundle and accepts an explicit candidate directory, target directory, and optional Git reference without permanently pinning a test to a commit or candidate. | Not started | Unverified | Target documented | Technical specification |
| GCOMP-008 | Every compilation records compiler version, selected source, resolved revision and dirty state, input hashes, output hashes, and a compilation hash used by evaluation cache and dataset identity. | Not started | Unverified | Target documented | Technical specification; testing strategy |
| GCOMP-009 | Eleventy, FastAPI, and Flask/Vue evaluation scenarios compile from project-appropriate bases while sharing the selected portable sections. | Not started | Unverified | Target documented | Corrected-target plan in subtask 071 |
| GCOMP-010 | Promotion remains manual: accepted candidate sections are merged into current source, repository files are compiled explicitly, and tests never promote guidance automatically. | Not started | Unverified | Target documented | Product and technical specifications |
| GCOMP-011 | The complete September 17 old-context matrix remains frozen and explicitly labeled legacy rather than current portable-guidance evidence. | Implemented | Automated | Documented | [Legacy full matrix](../documentation-and-specification-standard/agent-behavior-verification/20260917-legacy-root-guidance-full-matrix.md); 84 producers and 84 semantic assessments |
| GCOMP-012 | The corrected current baseline and latest candidate rerun all three projects, seven model/effort profiles, and both delivery modes with effort-aware requirement/testing assessment and pairwise quality review of passing and failing outputs. | Not started | Unverified | Target documented | Testing strategy; subtask 071 |
| GCOMP-013 | Deterministic tests prove compilation, historical-ref selection, working-tree pinning, target isolation, candidate overrides, repository-output checks, and exact evaluation provenance. | Not started | Unverified | Target documented | Testing strategy |