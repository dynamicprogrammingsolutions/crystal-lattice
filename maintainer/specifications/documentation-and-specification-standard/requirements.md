# Documentation and specification standard requirements

These requirements track the live state relative to the target specification.
The specification itself is not evidence that an output or behavior exists.

Implementation values use `Not started`, `In progress`, `Implemented`,
`Deferred`, or `Removed`.

## Meta-specification bootstrap

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| DOCMETA-001 | `maintainer/` has a clear non-public maintenance boundary and uses the simplified `maintainer/specifications/` layout. | Implemented | Human verified | Documented | `maintainer/README.md`; `maintainer/documentation-standards-review-bundle.md`; user approval on August 5, 2026 |
| DOCMETA-002 | One meta-specification defines both reusable standards and Crystal Lattice repository policy because they share ownership, approval, delivery, and validation. | Implemented | Human verified | Documented | `index.md`, `product-spec.md`, `technical-spec.md`; user approval on August 5, 2026 |
| DOCMETA-003 | The documentation-standard task and its subtasks link their scope to stable requirements in this file without duplicating the specification. | Implemented | Human verified | Documented | `tasks/20260728-package-local-documentation-standard/`; user approval on August 5, 2026 |

## Reusable generic standards

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| DOCGEN-001 | A package-neutral documentation standard defines profiles, artifact roles, ownership, source-of-truth, incremental adoption, and generated-output boundaries without Crystal Lattice-specific paths or package names. | Implemented | Unverified | Documented | `docs/development/standards/documentation.md`; project-specific term scan; human review pending |
| DOCGEN-002 | A package-neutral specification standard defines target specifications, live requirements, work-tracked approval, current public/maintainer docs, proportional artifacts, evidence, and simple spec-first commits. | Implemented | Unverified | Documented | `docs/development/standards/specifications.md`; human review pending |
| DOCGEN-003 | Generic ownership rules allow every package to define specifications for behavior it owns and define approved package-specific refinements of broader contracts. | Implemented | Unverified | Documented | `docs/development/standards/specifications.md`; human review pending |
| DOCGEN-004 | Generic rules define one normative owner, controlled summaries, current-versus-target separation, complete indexes, and two-link discoverability without requiring placeholder pages. | Implemented | Unverified | Documented | `docs/development/standards/documentation.md`; link check; human review pending |
| DOCGEN-005 | Generic rules define when a substantial specification is justified and require user approval unless the active task already authorizes its creation. | Implemented | Unverified | Documented | `docs/development/standards/specifications.md`; human review pending |
| DOCGEN-006 | The package-neutral documentation standard assigns an audience and context boundary to every artifact role. An artifact depends only on information available and appropriate to that audience; cross-audience information is translated into the destination role's vocabulary without leaking internal tasks, phases, requirement IDs, evidence, approval, or maintainer context. | In progress | Unverified | Documented | Uncommitted review draft in `docs/development/standards/documentation.md`; boundary-pressure behavioral verification pending |
| DOCGEN-007 | The package-neutral documentation standard preserves scope, ownership, source-of-truth, audience, validation, and publication boundaries when the normal workflow is blocked. Agents make safe partial progress, report the blocker and remaining action, request approval before a boundary-changing workaround, and do not claim incomplete work as complete. | In progress | Unverified | Documented | Uncommitted review draft in `docs/development/standards/documentation.md`; blocked-workflow behavioral verification pending |

## Crystal Lattice repository policy

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| DOCREP-001 | Repository policy maps the generic rules to root and package paths, package profiles, shared domains, tasks, agent guidance, publication, and validation. | Implemented | Unverified | Documented | `docs/development/repository/`; root `AGENTS.md`; human review pending |
| DOCREP-002 | Repository policy defines `plugins/docs/` as shared plugin-authoring guidance while preserving ordinary ownership and specification rules for individual plugin packages and framework contracts. | Implemented | Unverified | Documented | `docs/development/repository/documentation.md`; human review pending |
| DOCREP-003 | Root `docs/` is limited to repository-wide guidance, honest cross-package contracts, and site entry points; package-visible and package-maintainer documentation is owned locally. | Implemented | Unverified | Documented | `docs/development/repository/documentation.md`; root `AGENTS.md`; human review pending |
| DOCREP-004 | Public/reusable package profiles define concise README, AGENTS, docs index, quickstart, user docs, development docs, and optional reference without forcing filler into small packages. | Implemented | Unverified | Documented | `docs/development/repository/documentation.md`; package entry-point creation remains assigned to subtasks 030/040; human review pending |
| DOCREP-005 | Repository policy distinguishes applying the standards from maintaining them and keeps maintainer specifications and workflow-evaluation internals outside public output. | Implemented | Unverified | Documented | `docs/development/repository/`; root `AGENTS.md`; `maintainer/README.md`; human review pending |
| DOCREP-006 | Repository policy maps generic audience roles to exact Crystal Lattice artifacts and defines normal, pointer-only, evidence-only, and prohibited reference directions among README and user docs, reference, development docs, specifications, requirements, AGENTS files, tasks, maintainer material, and generated output. | In progress | Unverified | Documented | Uncommitted review draft in `docs/development/repository/documentation.md` and root `AGENTS.md`; boundary-pressure behavioral verification pending |

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
| DOCVAL-005 | Programmatic behavioral tests exercise every `DOCGEN-*` and `DOCREP-*` instruction requirement through narrow guidance-neutral cached task-specific base runs and clean continuations, preserving canonical artifacts for human review. | In progress | Unverified | Documented | Fourteen executable DOCGEN consumers; sixteen-scenario review-draft matrix; DOCREP and new pressure consumers pending; subtask 015 |
| DOCVAL-006 | After representative behavioral runs, a separate calibration review proposes evidence-backed seed/test removals, replacements, or additions based on clarity value, redundancy, cost, and observed variance; the approved suite does not change without user approval. | In progress | Unverified | Documented | Representative GLM/GPT runs; uncommitted calibrated review draft; user approval pending; `AEVAL-019`; subtask 015 |
| DOCVAL-007 | Behavioral verification deliberately places agents under boundary pressure, including audience-incompatible internal context, requests naming derived output, premature current-documentation requests, and unavailable or failing compliant workflows. Tests verify that agents preserve audience, ownership, source-of-truth, scope, validation, and completion-honesty boundaries. | In progress | Unverified | Documented | `agent-behavior-verification/`; revised Tests 02, 05, 06, and 13 plus proposed Tests 15–16; executable consumers pending |
| DOCVAL-008 | New guidance-clarity scenarios run first against the exact pinned pre-change guidance using the same seed, prompt, fixture, assertions, and model profile. Candidate wording is evaluated only after representative baseline evidence exposes the targeted behavior; variants are tried shortest-first, preserve paired provenance, and do not pass by weakening the task or assertions. | In progress | Unverified | Documented | Uncommitted baseline-first workflow draft; executable guidance-source variants and paired runs pending; `AEVAL-021`; subtask 015 |