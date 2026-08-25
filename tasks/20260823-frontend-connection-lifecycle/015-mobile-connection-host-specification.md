# Mobile connection lifecycle host specification

Define the package-owned technical refinement that maps the root connection
lifecycle and mobile UX contracts to the React Native host, native
application lifecycle, persistence integration, multi-runtime behavior, and
iOS/Android verification.

## Requirements checklist

- [x] The package specification links and refines the root lifecycle, mobile
  UX, bridge, transcript, and notification contracts without copying their
  product behavior.
- [x] A technical host contract defines controller ownership, factory
  injection, wizard/repair authority, focus/navigation, multiple runtimes,
  native lifecycle, caches, drafts, and verification.
- [x] Stable `MCL-*` requirements record current partial implementation and
  package-specific evidence.
- [x] The mobile development index routes to the specification.
- [x] Documentation preparation/build and focused link/status checks pass.

Parent Task: `tasks/20260823-frontend-connection-lifecycle/000-main.md`

Depends On: `tasks/20260823-frontend-connection-lifecycle/010-connection-lifecycle-specification.md`

## Supporting details

- **Decision:** Root `FCL-*` and `mobile-ux.md` remain authoritative for
  portable/user-visible behavior.
- **Decision:** This package specification owns only mobile host/native
  refinements and uses `MCL-*` requirements.
- **Decision:** Final mobile behavior permits several open runtimes; one-runtime
  behavior is an explicitly intermediate migration policy.
- **Constraint:** Existing bridge transport routing/defaults remain under the
  bridge-connectivity specification.

## Execution plan
Status: Approved

Create a proportional package specification with index, technical contract,
and requirements. Route it from the mobile development index and link the
broader root contracts.

Bound discovery to the connection host, current caches/drafts, native
lifecycle, and directly relevant tests already inspected for the root
specification. Do not reconstruct unrelated mobile UI.

Validate authored links through documentation preparation and a normal MkDocs
build. Record completion without claiming software delivery.

### Implementation decisions and open questions

- **Decided:** Do not duplicate a package product/UX page; link the root mobile
  UX.
- **Decided:** No package decision record is needed until implementation
  selects a platform-specific alternative not already decided by the root
  specification.
- No unresolved requirement question blocks specification creation.

### Documentation

Authored package sources:

- `mobile/crystal-lattice-control-rn/docs/development/specifications/connection-lifecycle/`
- `mobile/crystal-lattice-control-rn/docs/development/index.md`

No mobile user guide changes are made because this subtask defines a target.

### Task checklist

- [x] Author package specification index and ownership boundary.
- [x] Author technical host contract.
- [x] Author `MCL-*` live requirements.
- [x] Route from the mobile development index.
- [x] Run documentation tests, preparation, and build.
- [x] Inspect links, terminology, statuses, and final diff.

### Requirement verification

- Requirements 1–2: inspect package/root links, explicit ownership, technical
  state/resource/lifecycle boundaries, and exclusions.
- Requirement 3: verify unique `MCL-*` IDs and honest current evidence.
- Requirements 4–5: inspect index reachability and run documentation
  validation.

### Additional implementation verification

- Confirm prepared package documentation contains all three pages.
- Confirm no current mobile page claims target behavior as delivered.

## Implementation Notes

- 2026-08-23: Authored the approved mobile package refinement with 14
  `MCL-*` requirements.
- 2026-08-23: Documentation preparation tests, preparation, normal MkDocs
  build, requirement-ID uniqueness, terminology, links, and prepared-package
  reachability passed.

## Completion Notes

The mobile package host specification is complete. It maps the root lifecycle
and mobile UX to controller hosting, native application lifecycle, wizard and
repair authority, persistence, complete drafts, final multi-open behavior, and
iOS/Android verification without duplicating portable product behavior.

Verification performed:

- `pytest docs_site/tests/test_prepare_mkdocs_site.py -q` — 15 passed;
- `python docs_site/scripts/prepare_mkdocs_site.py` — completed;
- `(cd docs_site && mkdocs build)` — completed with existing repository
  notices/warnings;
- focused task/specification structure, link, terminology, and ID checks —
  passed.

No mobile software behavior or current user documentation changed.