# Traceability, Architecture, and Documentation-Site Integration

Integrate the completed specifications into repository architecture,
requirements evidence, navigation, and the current documentation-site
assembly without treating generated output as authored source.

## Requirements checklist

- [ ] Root architecture documentation shows the owning process, stable
  application owner, replaceable application, event store, notification
  persistence, frontend routing, and platform hosts at the correct conceptual
  level.
- [ ] Requirements matrices contain accurate implementation, automated
  verification, documentation, related-task, native/human verification, and
  delivery evidence.
- [ ] Important acceptance/contract tests reference appropriate `RLD-*`,
  `NTF-*`, `DSP-*`, `FNT-*`, or `FSA-*` identifiers without tagging ordinary
  low-level tests unnecessarily.
- [ ] Root and package documentation indexes provide a clear reading path and
  no circular or competing authority.
- [ ] Existing URLs and inbound links are updated or covered by compatibility
  pages/redirects.
- [ ] Current documentation-site preparation publishes the authored root and
  package-local sources; if the package registry is not yet available, the
  task records the bounded compatible integration used.
- [ ] Generated prepared/dist files remain untracked sources.
- [ ] Normal documentation build succeeds without new warnings caused by this
  work.
- [ ] Native desktop and human-verification fields remain incomplete until the
  related checkpoint is actually performed and confirmed.

Parent Task:
`tasks/20260730-runtime-notification-specification-documentation/000-main.md`

Depends On:

- `tasks/20260730-runtime-notification-specification-documentation/010-notification-and-action-display-contracts.md`
- `tasks/20260730-runtime-notification-specification-documentation/020-portable-frontend-behavior-specifications.md`
- `tasks/20260730-runtime-notification-specification-documentation/030-application-runtime-reload-specification.md`
- `tasks/20260730-runtime-notification-specification-documentation/040-core-and-application-implementation-documentation.md`
- `tasks/20260730-runtime-notification-specification-documentation/050-frontend-sdk-and-shared-components-documentation.md`
- `tasks/20260730-runtime-notification-specification-documentation/060-mobile-and-desktop-implementation-documentation.md`
- `tasks/20260730-runtime-notification-specification-documentation/070-plugin-authoring-and-public-contract-documentation.md`

## Architecture content

Add a compact cross-package view:

```text
Owning process
  └─ stable application owner
       ├─ shared event store / application notifications
       └─ current replaceable application
            ├─ sessions / persistent session notifications
            ├─ application plugins
            ├─ request and tool operations
            └─ MCP/runtime resources

Backend contracts and events
  → frontend controller/state
  → portable display routing
  → shared or native presentation capabilities
  → mobile/desktop platform hosts
```

Keep class-level mechanics in package docs. Root architecture should establish
ownership and data flow.

Review package pages for copied normative prose. A package page should link to
root requirement IDs and describe only its implementation mapping.

## Requirement evidence

Each root requirements page should record:

- implementation status;
- implementing files/packages;
- automated unit/contract/integration/native evidence;
- documentation status;
- related task paths;
- native/human verification status;
- completion commit or PR when delivery exists.

Current automated evidence is summarized in
`tasks/20260729-staged-application-config-and-full-reload.md`. Recheck commands
and file references when recording evidence; do not copy stale counts blindly.

Candidate tests for nearby requirement IDs/comments:

- owner admission/swap/rollback contract tests;
- session notification persistence/lifecycle tests;
- public HTTP notification integration;
- SDK routing/default tests;
- mobile and desktop real-backend notification integrations;
- focused mobile Detox and macOS XCUITest acceptance tests.

## Navigation and compatibility

Inspect and handle links to:

- `docs/api/events.md`;
- `application/python/README.md` reload/event sections;
- `plugins/docs/actions.md`;
- `plugins/docs/application-plugins.md`;
- package READMEs;
- docs-site nav and LLM/full-text entry points.

Do not remove old public paths without compatibility treatment approved by the
repository documentation standard.

## Site integration reference

Consult, but do not depend on:

- `tasks/20260728-package-local-documentation-standard/020-package-docs-site-assembly.md`
  for explicit registry, landing precedence, recursive copy, and generated
  boundaries;
- `tasks/20260728-package-local-documentation-standard/060-navigation-compatibility-and-build-triggers.md`
  for URL/navigation/CI principles;
- `tasks/20260728-package-local-documentation-standard/070-verification-and-deferred-migration-inventory.md`
  for build and deferred-inventory conventions.

If those mechanisms are still drafts, use the smallest current-pipeline change
that publishes these authored sources and record follow-up needed to adopt the
future registry. Do not make this task depend on completing unrelated broad
documentation migration.
