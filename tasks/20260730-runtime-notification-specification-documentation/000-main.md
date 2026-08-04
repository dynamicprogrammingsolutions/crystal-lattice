# Runtime Reload, Notification, and Frontend Presentation Specifications

Create durable specifications and development documentation for application
reload, notifications, action displays, and their frontend presentation. The
documentation must separate cross-package contracts from implementation-
independent frontend behavior and from package-local implementation details.

## Requirements checklist

- [x] Root documentation contains authoritative, cross-package specifications
  for notifications, action displays, and application runtime reload.
  - Documentation: [Notifications](../../docs/development/specifications/notifications/index.md),
    [action displays](../../docs/development/specifications/action-display/index.md),
    and [application runtime reload](../../docs/development/specifications/application-runtime-reload/index.md).
- [x] Root documentation contains implementation-independent frontend
  specifications that are sufficient to implement notification presentation
  and Sessions action behavior in a new frontend language or framework.
  - Documentation: [Portable notification frontend behavior](../../docs/development/specifications/notifications/frontend-behavior.md)
    and [Sessions actions](../../docs/development/specifications/sessions-actions/index.md).
- [x] Cross-package specifications own public shapes, lifecycle semantics,
  plugin-facing behavior, compatibility rules, and stable requirements rather
  than assigning that authority to the current Python or TypeScript packages.
  - Documentation: [Notification technical contract](../../docs/development/specifications/notifications/technical-spec.md),
    [action-display technical contract](../../docs/development/specifications/action-display/technical-spec.md),
    and [runtime-reload technical contract](../../docs/development/specifications/application-runtime-reload/technical-spec.md).
- [ ] Package-local development documentation explains how Core Python,
  Application Python, the TypeScript SDK, shared React Native components,
  mobile, and desktop conform to the root specifications without redefining
  them.
  - Documentation: [Core application owner](../../core/python/docs/development/application-owner.md),
    [Core notification implementation](../../core/python/docs/development/notification-implementation.md),
    [Application runtime-owner integration](../../application/python/docs/development/runtime-owner-integration.md),
    [Frontend SDK notification implementation](../../packages/frontend-sdk/docs/development/notification-implementation.md),
    [shared notification components](../../packages/frontend-rn-components/docs/development/notification-components.md),
    [shared action-menu components](../../packages/frontend-rn-components/docs/development/actions-menu-components.md),
    [mobile frontend hosting](../../mobile/crystal-lattice-control-rn/docs/development/frontend-hosting.md),
    and [desktop frontend hosting](../../desktop/crystal-lattice-control-desktop-rn/docs/development/frontend-hosting.md).
- [ ] Plugin authoring documentation and public reference pages derive from and
  link to the root contracts.
  - Documentation: [Plugin notification/action-display guide](../../plugins/docs/notifications-and-action-displays.md),
    [plugin actions](../../plugins/docs/actions.md), and
    [application plugins](../../plugins/docs/application-plugins.md).
  - Authoritative destinations: [Notification specification](../../docs/development/specifications/notifications/index.md)
    and [action-display specification](../../docs/development/specifications/action-display/index.md).
- [ ] Specifications use stable requirement identifiers and record current
  implementation, automated verification, documentation, task, and eventual
  delivery evidence.
  - Documentation: [Notification requirements](../../docs/development/specifications/notifications/requirements.md),
    [action-display requirements](../../docs/development/specifications/action-display/requirements.md),
    [runtime-reload requirements](../../docs/development/specifications/application-runtime-reload/requirements.md),
    and [Sessions-action requirements](../../docs/development/specifications/sessions-actions/requirements.md).
- [x] Material cross-package and frontend decisions are recorded at the layer
  whose consumers they constrain; language- or platform-specific choices
  remain package-local.
  - Documentation: [Notification technical contract](../../docs/development/specifications/notifications/technical-spec.md),
    [portable frontend behavior](../../docs/development/specifications/notifications/frontend-behavior.md),
    [action-display technical contract](../../docs/development/specifications/action-display/technical-spec.md),
    and [runtime-reload technical contract](../../docs/development/specifications/application-runtime-reload/technical-spec.md).
- [ ] Existing accurate documentation is migrated, linked, or reduced to a
  concise compatibility page without creating competing sources of truth.
  - Compatibility/source pages: [Events API](../../docs/api/events.md),
    [Application README](../../application/python/README.md),
    [plugin actions](../../plugins/docs/actions.md), and
    [application plugins](../../plugins/docs/application-plugins.md).
  - Authoritative destinations: [Notification specification](../../docs/development/specifications/notifications/index.md),
    [action-display specification](../../docs/development/specifications/action-display/index.md),
    and [runtime-reload specification](../../docs/development/specifications/application-runtime-reload/index.md).
- [x] Small demonstration plugins retain the reduced README-oriented package
  profile and are not given unnecessary standalone specification trees.
  - Documentation: [Dummy application notifications](../../plugins/dummy-application-notification-app/README.md),
    [dummy session notifications](../../plugins/dummy-session-notification-app/README.md),
    and [dummy action displays](../../plugins/dummy-action-display-app/README.md).
- [x] Authored sources are not placed in `docs_site/prepared/` or
  `docs_site/dist/`, and generated outputs are not treated as specification
  sources.
- [ ] Documentation-site assembly and navigation expose the resulting root and
  package-local documents without breaking intentionally retained public URLs.
  - Root navigation: [Development documentation](../../docs/development/index.md).
  - Package entry points: [Core development docs](../../core/python/docs/development/index.md),
    [Application development docs](../../application/python/docs/development/index.md),
    [Frontend SDK development docs](../../packages/frontend-sdk/docs/development/index.md),
    [shared React Native development docs](../../packages/frontend-rn-components/docs/development/index.md),
    [mobile development docs](../../mobile/crystal-lattice-control-rn/docs/development/index.md),
    and [desktop development docs](../../desktop/crystal-lattice-control-desktop-rn/docs/development/index.md).
- [ ] The final requirements evidence distinguishes automated verification
  from native/human verification and records checkpoint completion only after
  the corresponding evidence exists.
  - Evidence pages: [Notification requirements](../../docs/development/specifications/notifications/requirements.md),
    [action-display requirements](../../docs/development/specifications/action-display/requirements.md),
    [runtime-reload requirements](../../docs/development/specifications/application-runtime-reload/requirements.md),
    and [Sessions-action requirements](../../docs/development/specifications/sessions-actions/requirements.md).

## Subtasks

- [ ] `tasks/20260730-runtime-notification-specification-documentation/010-notification-and-action-display-contracts.md`
  - Missing: determine whether the original root decision-record requirement
    needs standalone files or is satisfied by rationale in the technical specs.
  - Documentation: [Notification overview](../../docs/development/specifications/notifications/index.md),
    [product specification](../../docs/development/specifications/notifications/product-spec.md),
    [technical specification](../../docs/development/specifications/notifications/technical-spec.md),
    [requirements](../../docs/development/specifications/notifications/requirements.md),
    [action-display overview](../../docs/development/specifications/action-display/index.md),
    [action-display technical specification](../../docs/development/specifications/action-display/technical-spec.md),
    and [action-display requirements](../../docs/development/specifications/action-display/requirements.md).
- [x] `tasks/20260730-runtime-notification-specification-documentation/020-portable-frontend-behavior-specifications.md`
  - Documentation: [Portable notification frontend behavior](../../docs/development/specifications/notifications/frontend-behavior.md),
    [Sessions-action overview](../../docs/development/specifications/sessions-actions/index.md),
    [Sessions-action technical specification](../../docs/development/specifications/sessions-actions/technical-spec.md),
    and [Sessions-action requirements](../../docs/development/specifications/sessions-actions/requirements.md).
- [x] `tasks/20260730-runtime-notification-specification-documentation/030-application-runtime-reload-specification.md`
  - Documentation: [Runtime-reload overview](../../docs/development/specifications/application-runtime-reload/index.md),
    [product specification](../../docs/development/specifications/application-runtime-reload/product-spec.md),
    [technical specification](../../docs/development/specifications/application-runtime-reload/technical-spec.md),
    and [requirements](../../docs/development/specifications/application-runtime-reload/requirements.md).
- [ ] `tasks/20260730-runtime-notification-specification-documentation/040-core-and-application-implementation-documentation.md`
  - Missing: explicit package implementation mappings to the applicable
    `RLD-*`, `NTF-*`, and `DSP-*` requirements.
  - Documentation: [Core application owner](../../core/python/docs/development/application-owner.md),
    [Core notification implementation](../../core/python/docs/development/notification-implementation.md),
    [Core development index](../../core/python/docs/development/index.md),
    [Application runtime-owner integration](../../application/python/docs/development/runtime-owner-integration.md),
    and [Application development index](../../application/python/docs/development/index.md).
- [ ] `tasks/20260730-runtime-notification-specification-documentation/050-frontend-sdk-and-shared-components-documentation.md`
  - Missing: SDK/shared-component requirement mappings and substantive
    shared server-settings form/model ownership documentation.
  - Documentation: [Frontend SDK notification implementation](../../packages/frontend-sdk/docs/development/notification-implementation.md),
    [Frontend SDK development index](../../packages/frontend-sdk/docs/development/index.md),
    [shared notification components](../../packages/frontend-rn-components/docs/development/notification-components.md),
    [shared action-menu components](../../packages/frontend-rn-components/docs/development/actions-menu-components.md),
    and [shared React Native development index](../../packages/frontend-rn-components/docs/development/index.md).
- [ ] `tasks/20260730-runtime-notification-specification-documentation/060-mobile-and-desktop-implementation-documentation.md`
  - Missing: current hosting/follow-up/coordinator details, corrected mobile
    modal hosting, and `FNT-*`/`FSA-*` implementation mappings.
  - Documentation: [Mobile frontend hosting](../../mobile/crystal-lattice-control-rn/docs/development/frontend-hosting.md),
    [mobile development index](../../mobile/crystal-lattice-control-rn/docs/development/index.md),
    [desktop frontend hosting](../../desktop/crystal-lattice-control-desktop-rn/docs/development/frontend-hosting.md),
    [desktop window/popover conventions](../../desktop/crystal-lattice-control-desktop-rn/docs/development/window-and-popover-conventions.md),
    [desktop native UI testing](../../desktop/crystal-lattice-control-desktop-rn/docs/development/native-ui-testing.md),
    and [desktop development index](../../desktop/crystal-lattice-control-desktop-rn/docs/development/index.md).
- [ ] `tasks/20260730-runtime-notification-specification-documentation/070-plugin-authoring-and-public-contract-documentation.md`
  - Missing: the originally required application-config and three dummy-plugin
    README coverage; some current README statements are stale or incomplete.
  - Documentation: [Notification/action-display authoring guide](../../plugins/docs/notifications-and-action-displays.md),
    [plugin actions](../../plugins/docs/actions.md),
    [application plugins](../../plugins/docs/application-plugins.md),
    [plugin documentation index](../../plugins/docs/index.md),
    [application-config plugin](../../plugins/application-config-app/README.md),
    [dummy application notifications](../../plugins/dummy-application-notification-app/README.md),
    [dummy session notifications](../../plugins/dummy-session-notification-app/README.md),
    and [dummy action displays](../../plugins/dummy-action-display-app/README.md).
  - Authoritative destinations: [Notification specification](../../docs/development/specifications/notifications/index.md)
    and [action-display specification](../../docs/development/specifications/action-display/index.md).
- [ ] `tasks/20260730-runtime-notification-specification-documentation/080-traceability-architecture-and-site-integration.md`
  - Missing: root architecture, current evidence matrices, selected test
    traceability, compatibility-link audit, and package-local site publication
    or an approved replacement/deferment for those requirements.
  - Documentation: [Architecture](../../ARCHITECTURE.md),
    [development documentation index](../../docs/development/index.md),
    [notification requirements](../../docs/development/specifications/notifications/requirements.md),
    [action-display requirements](../../docs/development/specifications/action-display/requirements.md),
    [runtime-reload requirements](../../docs/development/specifications/application-runtime-reload/requirements.md),
    and [Sessions-action requirements](../../docs/development/specifications/sessions-actions/requirements.md).
  - Package pages to publish/link: [Core](../../core/python/docs/development/index.md),
    [Application](../../application/python/docs/development/index.md),
    [Frontend SDK](../../packages/frontend-sdk/docs/development/index.md),
    [shared React Native](../../packages/frontend-rn-components/docs/development/index.md),
    [mobile](../../mobile/crystal-lattice-control-rn/docs/development/index.md),
    and [desktop](../../desktop/crystal-lattice-control-desktop-rn/docs/development/index.md).

The root notification/action-display contracts and runtime-reload specification
can be developed independently. Package implementation-documentation subtasks
can also proceed in parallel after the specific root contract they reference
is stable.

## Scope and authority model

The documentation hierarchy is:

1. **Root cross-package specifications** define contracts that constrain
   runtimes, transports, SDKs, plugins, tools, and frontends.
2. **Root frontend specifications** define language- and framework-independent
   frontend behavior. A new frontend should be implementable from these
   documents plus the cross-package contracts.
3. **Package-local development documentation** maps the current implementation
   to those requirements and records language/platform design choices.
4. **Public references and authoring guides** present concise schemas,
   examples, and usage instructions while linking to the authoritative specs.

Normative ownership:

| Concern | Authority |
|---|---|
| Notification fields, lifecycle, persistence classes, events, and plugin/tool behavior | Root notification specification |
| Action-display shape, follow-up actions, and presentation semantics | Root action-display specification |
| Reload state machine and externally observable runtime behavior | Root runtime-reload specification |
| Portable notification placement, authoritative dismissal behavior, history/replay, connection isolation, and reusable frontend capabilities | Root notification frontend-behavior specification |
| Portable Sessions action composition and pinning behavior | Root frontend Sessions-actions specification |
| Python storage, locks, owner internals, and server wiring | Core/Application package development docs |
| TypeScript polling, controllers, selectors, and display bus | Frontend SDK package development docs |
| React Native components and platform hosts | Shared RN, mobile, and desktop development docs |
| How Python plugins use the contracts | Shared plugin authoring docs |

## Approved source structure

The first documentation baseline uses one authoritative cross-package
specification per durable contract and concise package-local implementation
maps. Package pages must not repeat lifecycle, persistence, or presentation
semantics owned by the root specifications.

```text
docs/
├── development/
│   └── specifications/
│       ├── notifications/
│       │   ├── index.md
│       │   ├── product-spec.md
│       │   ├── technical-spec.md
│       │   ├── frontend-behavior.md
│       │   └── requirements.md
│       ├── action-display/
│       │   ├── index.md
│       │   ├── technical-spec.md
│       │   └── requirements.md
│       ├── application-runtime-reload/
│       └── sessions-actions/
└── api/
    └── events.md

core/python/docs/development/
├── application-owner.md
└── notification-implementation.md

application/python/docs/development/
└── runtime-owner-integration.md

packages/frontend-sdk/docs/development/
└── notification-implementation.md

packages/frontend-rn-components/docs/development/
├── notification-components.md
└── actions-menu-components.md

mobile/crystal-lattice-control-rn/docs/development/
└── frontend-hosting.md

desktop/crystal-lattice-control-desktop-rn/docs/development/
├── frontend-hosting.md
├── window-and-popover-conventions.md
└── native-ui-testing.md

plugins/docs/
└── notifications-and-action-displays.md
```

Do not create empty directory/profile files solely to reproduce this tree.
Create package entry points only where they route readers to substantive
content. Defer hand-maintained public contract reference pages unless they can
be generated or kept to a genuinely concise field/event table.

## Anti-duplication rules

- Each normative rule has exactly one authoritative root specification page.
- Package documentation maps requirement IDs to classes, modules, tests, and
  debugging paths; it does not restate the normative rule.
- Platform documentation describes hosting and native conventions only.
- Plugin documentation must stand on its own for plugin authors. It may include
  the concise field summaries and tested examples required to use the feature,
  while leaving lifecycle rationale, requirements, and cross-package decisions
  authoritative in the root specification.
- Public references, when added, contain concise lookup tables or generated
  material rather than lifecycle rationale.
- Prefer a substantive section in an existing package page over a new
  notification-specific page with duplicated prose.

## Reference principles, not dependencies

This task does **not** depend on the unfinished package-local documentation
standard task. That task is a focused reference for terminology and intended
repository conventions:

- `tasks/20260728-package-local-documentation-standard/000-main.md`
  - read from `## Package documentation profiles` through
    `### Specification lifecycle`;
  - read `## Approved decision register`, especially `DOC-DEC-002` through
    `DOC-DEC-012`;
  - consult `## Current repository findings` and
    `## Proposed final source structure` when choosing final paths.
- `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md`
  - reference its `## Supporting details` for artifact roles and agent routing.
- `tasks/20260728-package-local-documentation-standard/020-package-docs-site-assembly.md`
  - reference landing-page precedence, generated-output boundaries, and the
    proposed explicit package registry.

If that task has not been implemented when this work starts, this task may
author the substantive source documents using the principles summarized here.
It must not duplicate or silently pre-implement the unrelated contributor
workflow, task-guidance synchronization, or broad migration inventory.

## Related feature tasks

- `tasks/20260729-staged-application-config-and-full-reload.md`
  contains the implemented reload/notification work, current evidence, deferred
  stages, and the pending native desktop checkpoint.
- `tasks/20260619-generic-session-notifications/000-main.md` and subtasks
  `010`–`040` contain the original persistent session-notification model and
  completed implementation details.
- `tasks/20260619-generic-session-notifications/045-stage-1-authoritative-dismissal-retention-history-and-interaction-readiness.md`
  contains the proposed next lifecycle, retention, history, and Stage
  2-readiness changes.
- `tasks/20260614-ios-testflight-github-fastlane/085-app-review-local-runtime-and-testable-mode.md`
  is a downstream consumer of the application-owner/restart plumbing and may
  use different credential storage and owner-process integration.

Task files are implementation-history and planning references, not
specification sources. Durable intended behavior must be normalized into the
new specifications.

## Current implementation ground truth

### Runtime reload

- `core/python/agent_app/application_owner.py` owns one replaceable
  `AgentApplication`, rejects new operations while reload is pending, waits for
  admitted operations, constructs a candidate, swaps or rolls back, and closes
  the old application.
- `core/python/agent_app/application_future.py` exposes reload and notification
  APIs but remains the replaceable application.
- `application/python/agent_terminal_app/server.py`, `terminal_app.py`, and
  `__main__.py` connect HTTP, terminal, server/console, bridge, and shutdown
  paths to the stable owner.
- Reload does not require restarting the whole CLI/server process.
- New HTTP requests receive `application_reload_pending` while admission is
  closed.
- Old runtime closure includes application plugins, runtime stores, async
  runtime resources, tools, and MCP servers before reload completion is
  reported.
- `plugins/application-config-app` contributes reload and allowlisted dotenv
  key-update actions. Credential hardening and running-request reload policy
  remain deferred stages.

### Notifications

- `core/python/agent_app/notifications.py` implements persistent session
  notifications under `Session.metadata["notifications"]["items"]`, session
  locking, event/checkpoint publication, deduplication, update/resolve, pruning,
  and the failure-contained tool `notification_sink`.
- Application notifications use a runtime-injected durable
  `ApplicationNotificationStore`. They survive replacement of
  `AgentApplication`, owner reconstruction, and server-process restart subject
  to retention.
- Application events omit `session_id`; session notification events include it.
- Stage 1 notifications are model-hidden.
- Existing public discussion is split among `docs/api/events.md`,
  `plugins/docs/actions.md`, `plugins/docs/application-plugins.md`, and
  `application/python/README.md`. None is yet a complete authoritative
  specification.

### Frontend contracts and implementation

- `packages/frontend-sdk/src/types/notifications.ts` and
  `types/applicationNotifications.ts` define current TypeScript shapes.
- `packages/frontend-sdk/src/notifications/` contains selectors, merge logic,
  application-scope polling, and action invalidation.
- `packages/frontend-sdk/src/plugins/displayPresentation.ts` defines the
  current display envelope and backend-keyed presentation subscription.
- Explicit `banner`, `inline`, and `modal` presentations are no longer
  suppressed by action source. Defaults are application notification →
  banner, session notification → inline, and direct action response → modal.
- `packages/frontend-rn-components/src/notifications/` contains shared banner,
  rail, and session-host components.
- Mobile owns lifecycle state at `ConnectedRoot`, presents application
  notifications only on Sessions, and presents session notifications only on
  the exact matching Chat.
- Desktop polls each open backend and presents connection-level notifications
  in one message/detail-area rail; the active ChatPane contributes its session
  notifications at the same visual location.
- Mobile and desktop Sessions surfaces use the reusable pinnable
  `ActionsMenuBar` for built-ins and plugin-contributed application actions.
- Desktop uses native popovers for anchored transient menus and a React window
  for Server settings. Notification and action-response modal requests use
  inline fallback in the message/detail area.

### Demonstration and verification assets

- Non-default demo packages:
  - `plugins/dummy-application-notification-app`
  - `plugins/dummy-session-notification-app`
  - `plugins/dummy-action-display-app`
- Core, application, SDK, React, mobile, desktop, public HTTP, and real-backend
  tests exist. See the related 20260729 task for current counts.
- Mobile includes a focused notification-banner Detox harness.
- Desktop extends the existing Session Filters native harness/XCUITest for the
  unified action popover, shared banner rail, and Server settings window.
- The native desktop test and human desktop checkpoint were subsequently
  completed and confirmed on August 2, 2026.

### Existing documentation structure

- A first current-state baseline now exists under root
  `docs/development/specifications/` for notifications, action displays,
  runtime reload, and Sessions actions.
- Core, Application, frontend SDK, shared React Native, mobile, and desktop
  package-local development pages now map current implementation ownership
  without redefining root contracts.
- `plugins/docs/notifications-and-action-displays.md` provides the first shared
  authoring decision guide while small demonstration plugins remain
  README-only.
- The application README still contains useful reload and endpoint text and
  remains a compatibility/entry-point page rather than the normative source.
- The existing docs-site preparation pipeline currently publishes root docs,
  shared plugin docs, and generated plugin README pages. The package registry
  proposed by the documentation-standard task does not yet exist, so
  package-local pages are authored sources but are not yet assembled into the
  public site.

## Documentation rules for this task

- Use normative language only in the root contracts and root portable frontend
  specifications.
- Package implementation docs state which root requirements they satisfy and
  may add internal constraints, but must not redefine cross-package behavior.
- Plugin guides contain examples and authoring advice, not a competing schema.
- Public reference pages are concise projections of the specifications.
- Link to code where reading the source is clearer than maintaining a duplicate
  implementation inventory.
- Do not copy execution sequences, raw test output, or task chronology into
  specifications.
- Do not mark native or human verification complete without the corresponding
  evidence.
- Do not copy a root notification lifecycle explanation into Core,
  Application, SDK, shared-component, mobile, or desktop pages. Link to its
  requirement ID and document only the package-specific implementation.

## Execution plan

Status: Approved

The user approved a two-baseline workflow on July 31, 2026:

1. Commit the completed runtime/UI implementation and its implementation task.
2. Author and commit a concise current-state specification baseline using the
   approved anti-duplication structure.
3. Record the newly discussed notification lifecycle changes in a separate
   follow-up subtask and revise the specifications in the working tree so the
   uncommitted diff represents proposed behavior not yet implemented.

### Implementation decisions and open questions

- One root notification specification owns lifecycle, storage, dismissal,
  retention, history, and portable frontend behavior.
- Package-local pages are implementation maps and may remain sections of a
  broader page when separate files would add duplicate prose.
- Hand-maintained public reference pages are deferred unless they can remain
  concise or be generated.
- Commit `f14b39bf` preserves the original frontend-local dismissal baseline.
  Later notification commits implemented and documented server-owned
  dismissal, durable application history, retention, and the completed
  Stage A–D frontend behavior. History/replay and interaction readiness remain
  proposed.

### Documentation

- Root specifications under `docs/development/specifications/`
- Package implementation maps listed in `## Approved source structure`
- Shared plugin authoring guide
- Root docs index and MkDocs navigation

### Task checklist

- [x] Normalize the proposed documentation structure to avoid duplicated
  notification explanations.
- [x] Correct obsolete mobile/desktop presentation statements.
- [x] Author the current-state root specification baseline.
- [x] Author concise package implementation maps.
- [x] Add the plugin decision guide and root navigation.
- [x] Add the follow-up notification lifecycle subtask.
- [x] Revise the baseline specs to the approved proposed lifecycle and leave
  those changes uncommitted for review.

### Requirement verification

- Root and package content is reviewed for single-source normative ownership.
- The normal MkDocs build must pass without new warnings before the
  current-state documentation baseline is committed.
- Package-local public-site assembly remains pending the separate registry
  mechanism and is not claimed complete by this baseline.

### August 3, 2026 evidence audit

The authored baseline is present, but the task is not complete.

Completed in substance:

- root notification, action-display, runtime-reload, Sessions-action, and
  portable frontend specification sets;
- root and MkDocs navigation for those specifications;
- Core, Application, SDK, shared React Native, mobile, and desktop package
  development-page structure;
- the shared notification/action-display plugin authoring guide;
- reduced README-only profiles for the demonstration plugins;
- generated-output boundaries.

Incomplete work within the approved scope:

- correct stale package documentation, including mobile native modal hosting
  and the durable application-notification authority;
- complete the application-config and demonstration plugin README content;
- add package implementation-to-requirement-ID mappings;
- complete the root architecture view;
- complete the inbound-link and compatibility audit;
- refresh requirement matrices with current native/human and delivery
  evidence;
- run final link/build verification and add immutable completion notes to the
  main task and completed subtasks.

Explicit scope or ownership decisions:

- decide whether the requirement for separate root decision records is
  satisfied by rationale in the root technical specifications or requires new
  standalone decision files;
- decide whether selected acceptance tests must contain requirement-ID
  references or whether a centralized test-evidence map replaces that
  requirement;
- decide whether this task must publish package-local development pages through
  the current documentation site or whether that requirement is split/deferred
  to the package documentation registry task;
- decide whether mobile/desktop/SDK package documentation for notification
  history and interaction hosting remains in this task until Stages E–H are
  implemented, or moves to the owning implementation stages in
  `tasks/20260619-generic-session-notifications/045-stage-1-authoritative-dismissal-retention-history-and-interaction-readiness.md`.

The scope-decision items remain unchecked until the user approves a changed
completion boundary. They are not evidence that the already-authored
current-state pages are missing.

### Additional implementation verification

- Run `git diff --check`.
- Run `mkdocs build -f docs_site/mkdocs.yml`.
- Inspect generated navigation for all root specification pages and the shared
  plugin notification guide.

## Implementation Notes

- July 31, 2026: Authored the current-state specification baseline after the
  completed notification surface-ownership implementation. The baseline
  deliberately records local revision dismissal as implemented behavior so the
  subsequent uncommitted proposal can be reviewed as a focused lifecycle diff.
- July 31, 2026: Added
  `tasks/20260619-generic-session-notifications/045-stage-1-authoritative-dismissal-retention-history-and-interaction-readiness.md`
  and revised the root notification/action-display/Sessions-action
  specifications in the working tree. No implementation code was changed.
- August 1, 2026: Expanded
  `plugins/docs/notifications-and-action-displays.md` into the self-contained,
  runtime-accurate plugin authoring guide required by `plugins/docs/AGENTS.md`.
  Reduced notification duplication in `application-plugins.md` and
  `actions.md` to concise capability summaries and links.
