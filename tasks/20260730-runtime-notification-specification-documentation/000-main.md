# Runtime Reload, Notification, and Frontend Presentation Specifications

Create durable specifications and development documentation for application
reload, notifications, action displays, and their frontend presentation. The
documentation must separate cross-package contracts from implementation-
independent frontend behavior and from package-local implementation details.

## Requirements checklist

- [ ] Root documentation contains authoritative, cross-package specifications
  for notifications, action displays, and application runtime reload.
- [ ] Root documentation contains implementation-independent frontend
  specifications that are sufficient to implement notification presentation
  and Sessions action behavior in a new frontend language or framework.
- [ ] Cross-package specifications own public shapes, lifecycle semantics,
  plugin-facing behavior, compatibility rules, and stable requirements rather
  than assigning that authority to the current Python or TypeScript packages.
- [ ] Package-local development documentation explains how Core Python,
  Application Python, the TypeScript SDK, shared React Native components,
  mobile, and desktop conform to the root specifications without redefining
  them.
- [ ] Plugin authoring documentation and public reference pages derive from and
  link to the root contracts.
- [ ] Specifications use stable requirement identifiers and record current
  implementation, automated verification, documentation, task, and eventual
  delivery evidence.
- [ ] Material cross-package and frontend decisions are recorded at the layer
  whose consumers they constrain; language- or platform-specific choices
  remain package-local.
- [ ] Existing accurate documentation is migrated, linked, or reduced to a
  concise compatibility page without creating competing sources of truth.
- [ ] Small demonstration plugins retain the reduced README-oriented package
  profile and are not given unnecessary standalone specification trees.
- [ ] Authored sources are not placed in `docs_site/prepared/` or
  `docs_site/dist/`, and generated outputs are not treated as specification
  sources.
- [ ] Documentation-site assembly and navigation expose the resulting root and
  package-local documents without breaking intentionally retained public URLs.
- [ ] The final requirements evidence distinguishes automated verification from
  the still-required human/native desktop checkpoint.

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
| Portable notification placement, visual semantics, local dismissal, connection isolation, and reusable frontend capabilities | Root frontend notification-presentation specification |
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
- Plugin documentation provides decisions and recipes rather than another
  schema definition.
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
- Application notifications live in `AgentApplicationOwner` memory. They
  survive replacement of `AgentApplication` but not owner-process restart.
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
- The native desktop test and human desktop checkpoint remain unverified at
  this task's creation.

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

## Subtasks

- [ ] `tasks/20260730-runtime-notification-specification-documentation/010-notification-and-action-display-contracts.md`
- [ ] `tasks/20260730-runtime-notification-specification-documentation/020-portable-frontend-behavior-specifications.md`
- [ ] `tasks/20260730-runtime-notification-specification-documentation/030-application-runtime-reload-specification.md`
- [ ] `tasks/20260730-runtime-notification-specification-documentation/040-core-and-application-implementation-documentation.md`
- [ ] `tasks/20260730-runtime-notification-specification-documentation/050-frontend-sdk-and-shared-components-documentation.md`
- [ ] `tasks/20260730-runtime-notification-specification-documentation/060-mobile-and-desktop-implementation-documentation.md`
- [ ] `tasks/20260730-runtime-notification-specification-documentation/070-plugin-authoring-and-public-contract-documentation.md`
- [ ] `tasks/20260730-runtime-notification-specification-documentation/080-traceability-architecture-and-site-integration.md`

The root notification/action-display contracts and runtime-reload specification
can be developed independently. Package implementation-documentation subtasks
can also proceed in parallel after the specific root contract they reference
is stable.

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
- The current-state baseline documents frontend-local revision dismissal
  because that is the implementation being captured before the follow-up
  proposal changes the contract.

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
- [ ] Add the follow-up notification lifecycle subtask.
- [ ] Revise the baseline specs to the approved proposed lifecycle and leave
  those changes uncommitted for review.

### Requirement verification

- Root and package content is reviewed for single-source normative ownership.
- The normal MkDocs build must pass without new warnings before the
  current-state documentation baseline is committed.
- Package-local public-site assembly remains pending the separate registry
  mechanism and is not claimed complete by this baseline.

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
