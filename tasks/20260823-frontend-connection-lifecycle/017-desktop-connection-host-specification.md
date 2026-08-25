# Desktop connection lifecycle host specification

Define the package-owned technical refinement that maps the root connection
lifecycle and desktop UX contracts to `DesktopRoot`, multiple runtimes,
focused Sessions, persistent tabs, native windows/popovers, complete drafts,
and macOS verification.

## Requirements checklist

- [x] The package specification links and refines the root lifecycle, desktop
  UX, transcript, and notification contracts without copying their product
  behavior.
- [x] A technical host contract defines controller/runtime mapping,
  editor-event authority, focus/tab coordination, warm-pane restoration,
  runtime convergence, drafts, and native verification.
- [x] Stable `DCL-*` requirements record current partial implementation and
  package-specific evidence.
- [x] The desktop development index routes to the specification.
- [x] Documentation preparation/build and focused link/status checks pass.

Parent Task: `tasks/20260823-frontend-connection-lifecycle/000-main.md`

Depends On: `tasks/20260823-frontend-connection-lifecycle/010-connection-lifecycle-specification.md`

## Supporting details

- **Decision:** Root `FCL-*` and `desktop-ux.md` remain authoritative for
  portable/user-visible behavior.
- **Decision:** This package specification owns only desktop host/native
  refinements and uses `DCL-*` requirements.
- **Decision:** Initial desktop connection-kind scope remains manual direct
  HTTP; other kinds require a later approved UX extension.
- **Constraint:** Existing native window/popover and transcript/notification
  contracts remain authoritative.

## Execution plan
Status: Approved

Create a proportional package specification with index, technical contract,
and requirements. Route it from the desktop development index and link the
broader root contracts.

Bound discovery to `DesktopRoot`, connection/runtime hooks, Connections and
Sessions panels, tab/Chat hosting, caches/drafts, native coordinator behavior,
and directly relevant tests already inspected for the root desktop UX.

Validate authored links through documentation preparation and a normal MkDocs
build. Record completion without claiming software delivery.

### Implementation decisions and open questions

- **Decided:** Do not duplicate a package product/UX page; link the root
  desktop UX.
- **Decided:** No package decision record is needed until implementation
  selects a desktop-specific alternative not already decided by the root
  specification.
- No unresolved requirement question blocks specification creation.

### Documentation

Authored package sources:

- `desktop/crystal-lattice-control-desktop-rn/docs/development/specifications/connection-lifecycle/`
- `desktop/crystal-lattice-control-desktop-rn/docs/development/index.md`

No desktop user guide changes are made because this subtask defines a target.

### Task checklist

- [x] Author package specification index and ownership boundary.
- [x] Author technical host contract.
- [x] Author `DCL-*` live requirements.
- [x] Route from the desktop development index.
- [x] Run documentation tests, preparation, and build.
- [x] Inspect links, terminology, statuses, and final diff.

### Requirement verification

- Requirements 1–2: inspect package/root links, explicit ownership, technical
  state/resource/native boundaries, and exclusions.
- Requirement 3: verify unique `DCL-*` IDs and honest current evidence.
- Requirements 4–5: inspect index reachability and run documentation
  validation.

### Additional implementation verification

- Confirm prepared package documentation contains all three pages.
- Confirm no current desktop page claims target behavior as delivered.

## Implementation Notes

- 2026-08-23: Authored the approved desktop package refinement with 16
  `DCL-*` requirements.
- 2026-08-23: Documentation preparation tests, preparation, normal MkDocs
  build, requirement-ID uniqueness, terminology, links, and prepared-package
  reachability passed.

## Completion Notes

The desktop package host specification is complete. It maps the root lifecycle
and desktop UX to controller hosting, several runtime mappings, focus/tab
coordination, native editor events, cached warm-pane restoration, complete
drafts, and macOS verification without duplicating portable product behavior.

Verification performed:

- `pytest docs_site/tests/test_prepare_mkdocs_site.py -q` — 15 passed;
- `python docs_site/scripts/prepare_mkdocs_site.py` — completed;
- `(cd docs_site && mkdocs build)` — completed with existing repository
  notices/warnings;
- focused task/specification structure, link, terminology, and ID checks —
  passed.

No desktop software behavior or current user documentation changed.