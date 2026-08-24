# Frontend connection lifecycle specification

Define the durable cross-package target for connection UX, asynchronous
lifecycle authority, offline workspace continuity, multiple-open readiness,
and composed-message durability without redefining existing transport
protocols.

## Requirements checklist

- [x] The specification has an explicit cross-package owner, bounded scope,
  current/target boundary, and relationships to existing bridge,
  notification, and transcript contracts.
- [x] The canonical product page captures the ideal connection, reconnection,
  repair, offline, multi-open, and draft user experience.
- [x] Portable frontend behavior and technical/persistence contracts make the
  target testable across mobile, desktop, and shared packages.
- [x] Stable requirements distinguish current partial behavior from completed
  behavior and do not use the specification itself as implementation evidence.
- [x] Every authored specification page is discoverable, internally linked,
  and passes the repository documentation preparation/build checks.

Parent Task: `tasks/20260823-frontend-connection-lifecycle/000-main.md`

## Supporting details

- **Decision:** Root cross-package ownership is required because shared SDK,
  mobile, desktop, bridge lifecycle integration, and cloud/direct adapters
  coordinate the behavior without one current package owning the whole user
  outcome.
- **Decision:** `product-spec.md` is the canonical home of the ideal UX.
  `frontend-behavior.md` translates it into portable interaction rules.
- **Decision:** A dedicated persistence page is justified because caches,
  drafts, hydration, eviction, and deletion form one substantial contract.
- **Constraint:** Bridge wire behavior and transport mode selection remain
  normative in `docs/development/specifications/bridge-connectivity/`.
- **Constraint:** Current package guides must not claim future target behavior.

## Execution plan
Status: Approved

Create the proportional specification set approved by the user:

- an index declaring ownership, scope, relationships, and current/target
  boundary;
- a product specification containing terms, principles, ideal UX, failure
  outcomes, acceptance examples, and non-goals;
- portable frontend behavior for focus, status, cancellation, navigation,
  offline surfaces, per-kind refinements, and accessibility;
- a technical specification for state ownership, adapters, operation
  authority, candidate promotion, lifecycle recovery, errors, compatibility,
  and verification;
- a persistence/offline contract for identities, hydration, freshness, draft
  durability, eviction, uncertain sends, deletion, and migration;
- stable live-state requirements and concise material decision records.

Add the specification to the root development index. Validate links through
documentation preparation and a normal MkDocs build. Inspect the resulting
diff for audience boundaries, accidental current-behavior claims, and
unrelated edits.

### Implementation decisions and open questions

- **Decided:** Use `FCL` as the stable requirement prefix.
- **Decided:** Keep one active target rather than versioning this initial
  specification.
- **Decided:** Record three material decisions separately: state separation,
  operation authority/candidate promotion, and draft durability/eviction.
- No unresolved requirement question blocks this specification.

### Documentation

Authored sources:

- `docs/development/specifications/frontend-connection-lifecycle/`
- `docs/development/index.md`

No package user or current implementation page is changed because this
subtask defines target behavior and does not deliver software behavior.

### Task checklist

- [x] Author specification index and ownership/overlap boundaries.
- [x] Author product behavior and ideal UX.
- [x] Author portable frontend behavior.
- [x] Author technical lifecycle contract.
- [x] Author persistence/offline contract.
- [x] Author stable requirements and decision records.
- [x] Link the specification from the development index.
- [x] Run documentation preparation and normal MkDocs build.
- [x] Inspect links, terminology, status honesty, and final diff.

### Requirement verification

- Requirements 1–2: inspect the index, product specification, relationships,
  and explicit exclusions.
- Requirement 3: inspect frontend, technical, and persistence acceptance
  boundaries and their verification sections.
- Requirement 4: inspect `requirements.md` status/evidence values against the
  bounded implementation discovery.
- Requirement 5: run documentation preparation/build and verify owning-index
  reachability.

### Additional implementation verification

- Search the new specification for broken relative links and prohibited
  umbrella terminology.
- Confirm no generated `docs_site/prepared/` or `docs_site/dist/` file is
  edited directly.

## Implementation Notes

- 2026-08-23: Authored the approved root cross-package specification, 21
  stable `FCL-*` requirements, three decision records, and development-index
  entry.
- 2026-08-23: Documentation preparation, its 15 focused tests, and the normal
  MkDocs build passed. Prepared-source inspection confirmed the development
  index and specification index links. Build output retained existing
  repository notices and reference warnings but reported no broken new link.

## Completion Notes

The cross-package specification is complete. The ideal UX is canonical in the
product specification; portable interaction, lifecycle architecture, and
persistence/offline behavior have separate authoritative pages. The
requirements table records current partial implementation without treating
the specification as delivery evidence.

Verification performed:

- `pytest docs_site/tests/test_prepare_mkdocs_site.py -q` — 15 passed;
- `python docs_site/scripts/prepare_mkdocs_site.py` — completed;
- `(cd docs_site && mkdocs build)` — completed with existing repository
  notices/warnings;
- `git diff --check` and focused structure/terminology inspection — passed.

No software behavior or current package-user claim was changed. Implementation
of `FCL-*` requirements remains with Draft subtasks 020–050 and requires
separate approval.

## Post-completion follow-up

### Mobile UX refinement — 2026-08-23

At the user's request, the specification gained a dedicated screen-level
mobile refinement:

- `docs/development/specifications/frontend-connection-lifecycle/mobile-ux.md`

The page translates the product and portable contracts into concrete mobile
navigation, connection-row, wizard, bridge repair, offline Sessions/Messages,
composer, destructive-action, accessibility, and acceptance-sequence
behavior. Its wireframes are explicitly illustrative while state, actions,
ownership, navigation, recovery, and accessibility remain normative.

The specification index and portable mobile section link the refinement. No
`FCL-*` target or live implementation status changed.

Follow-up verification:

- `pytest docs_site/tests/test_prepare_mkdocs_site.py -q` — 15 passed;
- `python docs_site/scripts/prepare_mkdocs_site.py` — completed;
- `(cd docs_site && mkdocs build)` — completed with existing repository
  notices/warnings;
- focused `git diff --check`, terminology scan, and prepared-source
  discoverability inspection — passed.

### Desktop UX refinement — 2026-08-23

At the user's request, the specification gained a dedicated screen-level
desktop refinement:

- `docs/development/specifications/frontend-connection-lifecycle/desktop-ux.md`

The page preserves the existing multi-open, focused Sessions, persistent-tab,
cached Chat, display-rail, and native-window/popover model while defining
authoritative cancellation, runtime convergence, follow-active-tab behavior,
candidate editing, offline composition, complete draft continuity,
destructive-action clarity, accessibility, and native acceptance behavior.

`FCL-022` was added to track the desktop-specific focused-connection and
active-tab policy. The specification index and portable desktop section link
the refinement.

Follow-up verification:

- `pytest docs_site/tests/test_prepare_mkdocs_site.py -q` — 15 passed;
- `python docs_site/scripts/prepare_mkdocs_site.py` — completed;
- `(cd docs_site && mkdocs build)` — completed with existing repository
  notices/warnings;
- focused `git diff --check`, requirement-ID uniqueness, terminology, and
  prepared-source discoverability inspection — passed.