# Split frontend development documentation by concern

Reorganize mobile and analogous desktop frontend development documentation so
each maintained page has a clear subject, ambiguous “hosting” terminology is
removed, shared contracts are not duplicated, and existing published paths
remain usable during migration.

## Requirements checklist

- [x] R1. Mobile developer documentation has focused, concern-based pages for
  bridge connection integration, Session Chat composer/actions, notification
  presentation, markdown display, the Connections screen, the Home workspace,
  and session request status.
- [x] R2. The analogous desktop catch-all documentation is reorganized so
  notification/action-display behavior and Session Chat controls/actions have
  clear ownership, while request-status guidance has one primary maintained
  location.
- [x] R3. Frontend documentation titles and introductions use concrete terms
  such as integration, ownership, lifecycle, presentation, implementation, or
  screen behavior instead of unexplained “hosting”; legitimate runtime-host
  terminology remains unchanged.
- [x] R4. Each behavior has one primary maintained documentation location.
  Mobile and desktop pages retain platform-specific composition, persistence,
  layout, and verification details while linking shared SDK, React Native
  component, and cross-package specifications for portable contracts.
- [x] R5. Current package indexes, README links, and other maintained inbound
  links resolve to the new structure, and the obsolete broad pages are
  removed.
- [x] R6. The mobile and desktop development indexes provide a concise map
  that lets maintainers select the relevant concern without opening a
  catch-all page.

## Scope

In scope:

- authored developer documentation under
  `mobile/crystal-lattice-control-rn/docs/development/`;
- the analogous catch-all page and index under
  `desktop/crystal-lattice-control-desktop-rn/docs/development/`;
- package README and maintained documentation links affected by moves;
- compatibility handling for the existing public page paths;
- factual deduplication against shared frontend SDK, React Native component,
  and cross-package specification documentation.

Out of scope:

- changing product behavior or source ownership;
- rewriting focused pages whose scope is already clear, such as embedded
  Python runtime, human-time telemetry, desktop native UI testing, or
  window/popover conventions;
- changing generic uses of “host” that describe a real runtime/process
  boundary;
- editing historical completed task files merely to replace old links.

## Requirement questions

None about the required outcome. The compatibility mechanism is an
implementation decision because the documentation site currently has no
redirect plugin or redirect configuration.

## Supporting details

### Terminology finding

“Hosting” appears to have meant application-level code that owns state and
composes behavior supplied by shared SDK/component packages. That relationship
can be useful in prose when explicitly defined, but the term has drifted in
page titles to cover unrelated ownership, integration, presentation,
persistence, navigation, and screen behavior.

### Current-page audit

| Page | Finding |
|---|---|
| Mobile `frontend-hosting.md` | Mixes bridge connection lifecycle, composer/actions, notifications, and rich settings/actions |
| Mobile `markdown-display-and-connections.md` | Combines unrelated markdown rendering/preferences and Connections-screen behavior without section-level separation |
| Mobile `home-watchlist-and-status.md` | Combines local Home/Watchlist/notes ownership with cross-layer request-status reading and polling |
| Desktop `frontend-hosting.md` | Mixes notifications/action displays, request-status aggregation, and Chat settings/actions |
| Mobile embedded runtime and telemetry pages | Focused and appropriately named |
| Desktop markdown, window/popover, native testing, and telemetry pages | Focused and appropriately named |
| Desktop `home-workspace-and-tabs.md` | Broad but coherent around `DesktopRoot` workspace/shell ownership; already contains the fuller request-status account |

### Recommended destination structure

Mobile:

```text
docs/development/
├── bridge-connection-integration.md
├── session-chat-composer-and-actions.md
├── notification-presentation.md
├── markdown-display.md
├── connections-screen.md
├── home-workspace.md
├── session-request-status.md
├── human-time-telemetry.md
├── embedded-python-runtime.md
└── specifications/
```

Desktop additions:

```text
docs/development/
├── notification-presentation.md
├── session-chat-controls-and-actions.md
├── home-workspace-and-tabs.md
└── ...
```

`home-workspace-and-tabs.md` remains the primary desktop request-status page;
the duplicate summary currently in `frontend-hosting.md` should be removed
rather than copied.

### Compatibility constraint

The current MkDocs configuration has no redirect support. Existing broad page
paths are linked from package indexes, the mobile README, and historical
records. Maintained inbound links can be updated, but published paths need a
temporary compatibility mechanism that does not create a second editable copy
of moved guidance.

## Execution plan

Status: Approved

Start by making a fact-and-ownership map for each paragraph in the three broad
mobile pages and the desktop catch-all page. Assign each fact to one
destination concern, identify portable claims already maintained by the
frontend SDK, frontend React Native components, or cross-package
specifications, and mark duplicate text for replacement with a link. Do not
rewrite focused sibling pages merely for naming uniformity.

Create the focused mobile pages from moved maintained content:

- `bridge-connection-integration.md` owns mobile transport selection, saved
  record reconstruction, pairing repair, foreground recovery, and mobile
  verification, while linking the bridge transport and connection-lifecycle
  contracts.
- `session-chat-composer-and-actions.md` owns mobile composer layout, primary
  and pinned action behavior, request-action eligibility, expanded composer,
  rich settings/actions placement, persistence, and relevant tests.
- `notification-presentation.md` owns mobile surface placement, display
  owners, dismissal-cache integration, and mobile verification, while linking
  the portable notification specification and SDK implementation.
- `markdown-display.md` owns persisted display preferences, capability
  fallback, renderer/code dispatch, typography application, and markdown
  verification.
- `connections-screen.md` owns saved-card state/actions, navigation behavior,
  Global Settings presentation, responsive header/action layout, and
  Connections verification.
- `home-workspace.md` owns mobile Home/Watchlist/notes persistence,
  derivation, presentation, reordering, and local actions.
- `session-request-status.md` owns the mobile status reader, polling,
  batching, retry/staleness behavior, and cross-layer verification links.

Give every destination page a short opening scope statement naming its reader,
owned behavior, and upstream shared contracts. Use concrete titles and terms;
do not introduce a replacement umbrella term.

Apply the analogous desktop cleanup. Move notification/action-display
presentation into `notification-presentation.md`. Move rich Chat settings,
composer actions, native control adaptation, and request-action eligibility
into `session-chat-controls-and-actions.md`. Keep the detailed request-status
material in `home-workspace-and-tabs.md`, merging only unique facts from the
catch-all page and replacing duplication with links.

Update the mobile and desktop development indexes with grouped or descriptive
links. Update the mobile README and every maintained inbound link found by
repository search. Historical completed tasks may continue pointing at a
compatibility path and should not be rewritten solely for this migration.

Preserve old public paths without duplicated maintained guidance. The
recommended first implementation is a short relocation/index page at each old
path that links to the focused destinations and contains no behavioral
content. Treat real MkDocs redirects as a separate documentation-site
improvement; if redirect infrastructure is added within this task instead,
verify generated output and remove the temporary pages in the same change.

Review the resulting set for page-level cohesion, duplicated claims, undefined
terminology, and orphaned entry points. Validate maintained links from source,
prepare the generated documentation input, build the MkDocs site, and inspect
the resulting package navigation and compatibility pages.

### Implementation decisions and open questions

- Decision: retire unexplained “hosting” from frontend page titles; retain
  “host” only in prose where a concrete owner/composition boundary is defined.
- Decision: split mobile documentation by the seven concerns listed above and
  include the analogous desktop cleanup in this task.
- Decision: keep focused telemetry, embedded-runtime, native-testing,
  markdown-preference, and window/popover pages structurally unchanged unless
  a moved link or local factual correction requires an edit.
- Recommendation pending execution review: use content-free relocation pages
  at old paths because no redirect mechanism currently exists. Adding redirect
  infrastructure is broader and should remain separate unless implementation
  inspection identifies an existing supported mechanism.
- Open implementation question: whether the mobile development index is
  clearest as one annotated list or small groups such as Connectivity, Session
  Chat, Home and status, Runtime, and Telemetry. Resolve locally based on the
  final page count and avoid an index that duplicates page content.

### Documentation

This task is entirely documentation maintenance. The readers are maintainers
changing the mobile or desktop frontend. Update:

- mobile and desktop development indexes;
- the mobile README’s related-documentation links;
- all affected maintained package-documentation links;
- any shared documentation that currently treats a catch-all page as the
  primary source.

Do not edit `docs_site/prepared/` or `docs_site/dist/` directly. Do not create
duplicate current guidance in compatibility pages.

### Task checklist

- [x] Build a paragraph-level ownership map for broad mobile and desktop pages.
- [x] Create the seven focused mobile pages and move each maintained fact once.
- [x] Create focused desktop notification and Session Chat pages.
- [x] Consolidate desktop request-status guidance in its existing primary page.
- [x] Replace duplicated portable contracts with links to owning shared docs.
- [x] Replace ambiguous “hosting” titles and undefined terminology.
- [x] Add non-duplicated compatibility behavior for old public paths.
- [x] Update mobile/desktop indexes, README links, and maintained inbound links.
- [x] Check focused sibling pages for link or factual fallout without
  restructuring them unnecessarily.
- [x] Prepare and build the documentation site and inspect package navigation.

### Requirement verification

- R1: Inspect the mobile development index and each destination page to verify
  one clear concern, an explicit scope introduction, current entry points, and
  no missing content from the three source pages.
- R2: Inspect the desktop development index and destination pages; verify
  notification/action-display and Chat controls are separated and request
  status has one complete primary location.
- R3: Repository-search frontend documentation titles and introductions for
  unexplained “hosting”; inspect remaining matches to confirm they describe a
  concrete runtime or explicitly defined ownership relationship.
- R4: For bridge, actions, notifications, markdown, Home/status, and request
  cancellation, compare platform pages with their shared SDK/component/spec
  owners and verify portable contracts are linked rather than independently
  restated.
- R5: Search all maintained Markdown for old filenames, verify updated links,
  and inspect generated output for each old public path and new destination.
- R6: Review the mobile and desktop development indexes as navigation
  boundaries and confirm every focused page is reachable with a descriptive
  label and no catch-all page is presented as the primary entry point.

### Additional implementation verification

- Run `python docs_site/scripts/prepare_mkdocs_site.py`.
- Run `mkdocs build -f docs_site/mkdocs.yml`.
- Inspect build warnings for newly broken links or orphaned pages and
  distinguish pre-existing warnings.
- Run `git diff --check`.
- Review the final diff for accidental edits to generated documentation,
  historical task records, or unrelated implementation files.

## Implementation Notes

- Execution was approved on 2026-09-27.
- The existing broad mobile pages map cleanly to the seven planned concerns.
  The existing desktop workspace page already contains the authoritative
  request-status account, so no duplicate status text was moved into a new
  page.
- The documentation site has no configured redirect mechanism. The old paths
  therefore remain as content-free compatibility pages linking the new
  maintained destinations.
- Connection-lifecycle specification titles retain “host” because they name a
  concrete application ownership boundary; the ambiguous catch-all frontend
  usage was removed.

## Completion Notes

- Outcome: mobile development guidance is split into seven focused pages for
  bridge integration, Connections, Session Chat controls/actions,
  notifications, markdown display, Home, and request status. Desktop
  notification/action-display and Session Chat control guidance now have
  separate pages.
- Ownership: portable bridge, cancellation, rich action, notification,
  markdown, Home/status, and polling contracts link to their shared SDK,
  frontend SDK React, React Native component, or cross-package specification
  owners. Platform pages retain application composition, persistence, layout,
  native adaptation, and verification details.
- Compatibility: the four former catch-all paths remain as content-free
  navigation pages. The mobile README and both development indexes point to
  the focused maintained pages. Repository search found no maintained
  non-historical links still targeting the old pages.
- Terminology: ambiguous “frontend hosting” and combined “Connections
  hosting”/“request-status hosting” titles were removed. Remaining `host`
  headings belong to connection-lifecycle or embedded-runtime specifications
  that name concrete ownership/runtime boundaries.
- Verification: `python docs_site/scripts/prepare_mkdocs_site.py` and
  `mkdocs build -f docs_site/mkdocs.yml` passed. Generated output contains all
  new and compatibility pages, and prepared package indexes contain the new
  navigation. Build warnings are pre-existing unlisted pages and unrelated
  plugin links; none reference this task's pages. Focused whitespace search
  and `git diff --check` passed.
- Plan deviation: no redirect infrastructure was added. The approved
  compatibility-page approach was used because the current site has no
  configured redirect mechanism.
- Unrelated state: the pre-existing deletion of the mobile reviewer proxy
  certificate was not modified or included in this work.

## Post-completion follow-up

- The user determined that the compatibility pages no longer serve a purpose
  and explicitly requested their removal.
- Removed the former mobile `frontend-hosting.md`,
  `markdown-display-and-connections.md`, and `home-watchlist-and-status.md`
  pages and the former desktop `frontend-hosting.md` page.
- R5 was updated to reflect the approved completed state: maintained links
  resolve to focused pages and obsolete broad pages are absent. The original
  plan and immutable completion notes remain as the execution record of the
  earlier compatibility-page decision.
- Follow-up verification: documentation preparation and the MkDocs build
  passed with the same existing unrelated warnings. The cleaned generated site
  contains the focused destination pages and none of the four removed paths.
  Maintained non-historical Markdown contains no links to the removed
  filenames, and `git diff --check` passed.