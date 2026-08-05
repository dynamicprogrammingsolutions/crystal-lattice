# Documentation and specification standard requirements

These requirements track the live state relative to the target specification.
The specification itself is not evidence that an output or behavior exists.

Implementation values use `Not started`, `In progress`, `Implemented`,
`Deferred`, or `Removed`.

## Meta-specification bootstrap

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| DOCMETA-001 | `maintainer/` has a clear non-public maintenance boundary and uses the simplified `maintainer/specifications/` layout. | Implemented | Human verified | Documented | `maintainer/README.md`; user approval on August 5, 2026 |
| DOCMETA-002 | One meta-specification defines both reusable standards and Crystal Lattice repository policy because they share ownership, approval, delivery, and validation. | Implemented | Human verified | Documented | `index.md`, `product-spec.md`, `technical-spec.md`; user approval on August 5, 2026 |
| DOCMETA-003 | The documentation-standard task and its subtasks link their scope to stable requirements in this file without duplicating the specification. | Implemented | Human verified | Documented | `tasks/20260728-package-local-documentation-standard/`; user approval on August 5, 2026 |

## Reusable generic standards

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| DOCGEN-001 | A package-neutral documentation standard defines profiles, artifact roles, ownership, source-of-truth, incremental adoption, and generated-output boundaries without Crystal Lattice-specific paths or package names. | Not started | Unverified | Pending | `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md` |
| DOCGEN-002 | A package-neutral specification standard defines target specifications, live requirements, work-tracked approval, current public/maintainer docs, proportional artifacts, evidence, and simple spec-first commits. | Not started | Unverified | Pending | `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md` |
| DOCGEN-003 | Generic ownership rules allow every package to define specifications for behavior it owns and define approved package-specific refinements of broader contracts. | Not started | Unverified | Pending | `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md` |
| DOCGEN-004 | Generic rules define one normative owner, controlled summaries, current-versus-target separation, complete indexes, and two-link discoverability without requiring placeholder pages. | Not started | Unverified | Pending | `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md` |
| DOCGEN-005 | Generic rules define when a substantial specification is justified and require user approval unless the active task already authorizes its creation. | Not started | Unverified | Pending | `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md` |

## Crystal Lattice repository policy

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| DOCREP-001 | Repository policy maps the generic rules to root and package paths, package profiles, shared domains, tasks, agent guidance, publication, and validation. | Not started | Unverified | Pending | `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md` |
| DOCREP-002 | Repository policy defines `plugins/docs/` as shared plugin-authoring guidance while preserving ordinary ownership and specification rules for individual plugin packages and framework contracts. | Not started | Unverified | Pending | `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md` |
| DOCREP-003 | Root `docs/` is limited to repository-wide guidance, honest cross-package contracts, and site entry points; package-visible and package-maintainer documentation is owned locally. | Not started | Unverified | Pending | `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md` |
| DOCREP-004 | Public/reusable package profiles define concise README, AGENTS, docs index, quickstart, user docs, development docs, and optional reference without forcing filler into small packages. | Not started | Unverified | Pending | `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md`, subtasks 030 and 040 |
| DOCREP-005 | Repository policy distinguishes applying the standards from maintaining them and keeps maintainer specifications and workflow-evaluation internals outside public output. | Not started | Unverified | Pending | `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md` |

## Documentation publication and continuity

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| DOCPUB-001 | An explicit repository registry defines public package documentation identity, title, source, destination, included inputs, and development-doc publication. | Not started | Unverified | Pending | `tasks/20260728-package-local-documentation-standard/020-package-docs-site-assembly.md` |
| DOCPUB-002 | Site preparation assembles registered package README/docs sources predictably, uses docs index before README, and rejects invalid sources and collisions. | Not started | Unverified | Pending | `tasks/20260728-package-local-documentation-standard/020-package-docs-site-assembly.md` |
| DOCPUB-003 | `AGENTS.md`, `maintainer/`, prepared output, and other non-public maintenance inputs are excluded from public site output by default. | Not started | Unverified | Pending | Subtasks 020 and 070 |
| DOCPUB-004 | Package documentation and registry changes trigger the documentation build workflow. | Not started | Unverified | Pending | `tasks/20260728-package-local-documentation-standard/060-navigation-compatibility-and-build-triggers.md` |
| DOCPUB-005 | MkDocs navigation and LLM documentation sections point to canonical prepared destinations while preserving plugin and built-in-plugin discoverability. | Not started | Unverified | Pending | `tasks/20260728-package-local-documentation-standard/060-navigation-compatibility-and-build-triggers.md` |
| DOCPUB-006 | Relocated public documentation URLs remain available through non-authoritative compatibility pages or redirects unless a breaking change is approved. | Not started | Unverified | Pending | `tasks/20260728-package-local-documentation-standard/060-navigation-compatibility-and-build-triggers.md` |

## Bounded documentation migration

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| DOCMIG-001 | Core Python receives required package entry points and ownership-clear event, SDK, examples, and selected type/protocol documentation is migrated with bounded verification. | Not started | Unverified | Pending | `tasks/20260728-package-local-documentation-standard/030-core-python-documentation-migration.md` |
| DOCMIG-002 | Application configuration, shared plugin overview, package entry points, and selected development guidance are migrated to approved owners with bounded verification. | Not started | Unverified | Pending | `tasks/20260728-package-local-documentation-standard/040-application-and-plugin-documentation-migration.md` |
| DOCMIG-003 | Architecture, endpoint parity, tool-host protocol, and generated-reference ownership are classified and normalized without broad reverse engineering. | Not started | Unverified | Pending | `tasks/20260728-package-local-documentation-standard/050-cross-package-and-reference-documentation-triage.md` |
| DOCMIG-004 | Every first-wave or investigated page has an outcome, verification boundary, compatibility treatment, or concise deferral with owner and future trigger. | Not started | Unverified | Pending | `tasks/20260728-package-local-documentation-standard/070-verification-and-deferred-migration-inventory.md` |

## Contributor and task-guidance workflow

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| DOCFLOW-001 | Root `CONTRIBUTING.md` presents the approved concise, risk-scaled AI-assisted workflow, human/AI responsibilities, review boundaries, and short stage-specific prompts. | Not started | Unverified | Pending | `tasks/20260728-package-local-documentation-standard/065-contributing-and-ai-assisted-development-workflow.md` |
| DOCFLOW-002 | Canonical and bundled `TASKS-v7` are mechanically synchronized and explain target specifications, live requirements, task-owned approval/execution, evidence, and current documentation without embedding the full contributor guide. | Not started | Unverified | Pending | `tasks/20260728-package-local-documentation-standard/068-task-guidance-specification-alignment.md` |
| DOCFLOW-003 | Task-guidance evaluation code, fixtures, documentation, and review tooling move from root shared-test locations into a coherent `maintainer/`-owned layout with commands and consumers updated. | Not started | Unverified | Pending | `tasks/20260728-package-local-documentation-standard/068-task-guidance-specification-alignment.md` |
| DOCFLOW-004 | Task-guidance evaluation preserves deterministic assertions, separate real-model execution/review, concise-prompt scenarios, exact guidance provenance, and human interpretation. | Not started | Unverified | Pending | Subtasks 068 and 070 |

## Verification

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| DOCVAL-001 | Focused tests cover package registry/assembly behavior, maintainer exclusion, canonical/bundled task-guidance parity, and affected relocated tooling. | Not started | Unverified | Pending | Subtasks 020, 068, and 070 |
| DOCVAL-002 | Documentation preparation and normal MkDocs build complete without unresolved warnings introduced by this work. | Not started | Unverified | Pending | `tasks/20260728-package-local-documentation-standard/070-verification-and-deferred-migration-inventory.md` |
| DOCVAL-003 | New and migrated pages have valid links, owning-index reachability, accurate touched claims, and no competing authored source of truth. | Not started | Unverified | Pending | Subtasks 060 and 070 |
| DOCVAL-004 | Parent and subtask evidence maps to these requirements, and human-review requirements remain unverified until explicitly confirmed. | Not started | Unverified | Pending | `tasks/20260728-package-local-documentation-standard/070-verification-and-deferred-migration-inventory.md` |