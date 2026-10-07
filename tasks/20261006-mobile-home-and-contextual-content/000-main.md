# Improve Mobile Home and Contextual Guidance

Plan the second round of mobile usability improvements: move connections onto
Home, introduce reusable contextual content, and use it for actionable empty
states, persistent help access, and plugin-driven workspace guidance.
The user reviewed and accepted this overall shape. Execution of `010` was
approved and completed on 2026-10-07; `020`, `030`, and this overall plan remain
Draft.

## Requirements checklist

- [x] M1 — Connection management appears at the top of Home and the separate
  Connections bottom tab is removed. Existing connection creation, saved
  connection management, switching, disconnect, settings, and session
  navigation remain accessible. Preserve the cards and behavior, initially
  show up to three with a footer expand/collapse button, and present setup in
  a modal while retaining the current connection until replacement succeeds.
- [ ] M2 — Home, Sessions, and chat can use a shared contextual-content
  presentation with explanatory text and action/link buttons. The generic
  plugin/frontend contract supports empty/no-session and always-visible
  content, dismissible or non-dismissible content, and framed or unframed
  presentation. User-facing UI does not label it “first-user instructions.”
- [ ] M3 — Sessions and chat guidance is plugin-driven. Plugins own content
  and complex eligibility rules; the frontend owns presentation and simple
  view-state decisions. Application-owned connection and Home explanations
  work before a backend is connected.
- [ ] M4 — Information/question affordances beside non-obvious application
  elements, including Watchlist and Recent sessions, and beside
  plugin-declared UI elements let users access explanations when the section
  is populated or its initial panel is no longer visible. Plugin help is
  declared through UI metadata and uses the shared display.
- [ ] M5 — The embedded server contributes contextual guidance for new local
  sessions explaining their current working directory and providing a path
  to the existing workspace setting/actions. The feature remains useful for
  general agent work rather than one task type.
- [ ] M6 — Existing connection/session identity, persistence, notification
  behavior, plugin actions, and filesystem authorization remain compatible.
  Introducing guidance does not create a second credential, connection, or
  workspace authority.

## Scope and ownership

This is the second round after the first-round settings task:
`tasks/20260910-ios-embedded-runtime-poc/027-local-agent-provider-settings-usability.md`.
That task still owns OpenAI authentication layout, provider naming,
Reviewer switches, and removal of Make default. This directory does not
reopen those choices.

Use exactly three independently reviewable deliveries:

1. `010`: the production Home connection section and navigation.
2. `020`: the reusable plugin contract, SDK interpretation, display/help
   components, and their public-backend integration evidence.
3. `030`: production empty states and help consumers, generic session
   guidance, embedded workspace contributions, and their complete user flow.

The framework feature is called contextual content. A producer plugin may
provide introductory guidance, help, or other contextual information without
changing that contract. Notifications continue to represent operational
state with their existing publication, dismissal, and resolution lifecycle.

No new providers, authentication flows, directory-selection capabilities,
file browsing, notification lifecycle redesign, or desktop navigation changes
are required. Shared interfaces must remain compatible with desktop and
older backends, but desktop adoption of the new presentation is later work.
Physical-device testing is not an acceptance gate.

## Open questions

- **Visibility semantics:** distinguish no selected session, an empty new
  session, and an empty filtered list. Recommendation: expose explicit
  frontend states; do not infer new-user state from a filtered list or a
  partial transcript. The final field/value shape belongs to `020`.
- **Dismissal and help identity:** the accepted direction is device-local
  presentation dismissal, separate from server notification state. Scope,
  revision changes, and reference-versus-inline help metadata remain to be
  confirmed in `020`.
- **Actions and app navigation:** plugin actions and links can reuse existing
  contracts. Opening a frontend view or a particular setting needs a small
  explicit contract; its supported targets and ownership remain open in
  `020`.
- **Guidance producer/configuration:** confirm the recommended small generic
  application plugin for configurable Sessions/chat guidance, with
  working-directory content owned by the existing embedded workspace plugin.
  Exact copy and initial action labels are reviewed in `030`.

These questions refine the accepted shape. They are not additional approved
requirements, and no unresolved behavior should be implemented by assumption.

## Supporting facts

- `ConnectedRoot.tsx` currently starts on Home but renders separate Home,
  Connections, Sessions, and Messages tabs. New connection actions switch to
  the Connections tab, and the no-backend Sessions placeholder directs users
  there.
- `ConnectionsScreen.tsx` already exposes saved connection cards and their
  open/disconnect/delete/health/settings actions. `App.tsx` owns connection
  records and transport/backend creation.
- Home currently shows Watchlist and Recent Sessions with short static empty
  labels. Both sections are device-owned and can be present without a live
  backend.
- Application UI schema is available without a session; session application
  UI schema receives effective configuration and the full persisted session.
  Those existing surfaces can deliver plugin contributions for both contexts.
- Existing action displays provide safe text/Markdown bodies and follow-up
  actions. Application notifications reject inline presentation, and all
  notifications carry lifecycle state; neither should become a store for
  static introductory content.
- The embedded workspace application plugin already owns the workspace
  setting and private/shared/Files actions. Files bookmark acceptance remains
  unfinished in
  `tasks/20260910-ios-embedded-runtime-poc/025-user-selectable-ios-workspaces.md`;
  this task explains existing behavior and does not claim to complete that
  native-permission boundary.

## Subtasks

- [x] `tasks/20261006-mobile-home-and-contextual-content/010-home-connection-section-and-navigation.md`
- [ ] `tasks/20261006-mobile-home-and-contextual-content/020-contextual-content-contract-and-shared-renderer.md`
- [ ] `tasks/20261006-mobile-home-and-contextual-content/030-empty-states-info-affordances-and-local-workspace-guidance.md`

## Requirement ownership

| Requirement | Owning delivery | Decisive check |
| --- | --- | --- |
| M1 | `010` | `Home connection public flow`: production App opens a real HTTP connection from Home and creates/reopens a session through its production adapter. |
| M2 | `020` for contract/display; `030` for Home/Sessions/chat adoption | `Contextual content public integration`, then `Mobile guidance journey` through production screen hosts. |
| M3 | `020` for publication/eligibility; `030` for production producers | `Contextual content public integration` changes real session/config state and observes plugin output in the shared host. |
| M4 | `020` for help metadata/display; `030` for application/plugin element affordances | `Mobile guidance journey` reopens the same explanation from a populated section and a production plugin setting. |
| M5 | `030` | `Embedded workspace guidance flow`: real embedded application publishes content, existing workspace action changes selection, and the chat/settings hosts refresh the explanation. |
| M6 | Explicit combination of all three children | `010` preserves connection persistence; `020` keeps notification/action contracts separate; `030` verifies connection/session isolation and existing workspace authorization through the above paths. |

Dependencies are declared in each child. The numbering suggests delivery
order; `010` and `020` can run independently after first-round settings work,
and `030` requires both. No separate implementation/testing/documentation
children are created.

## Execution plan

Status: Draft

Keep connection lifecycle and navigation in the mobile application.
`010` extracts the existing connection controls into the first Home section
and updates the wizard host without requiring backend-delivered guidance.
It supplies a useful and testable navigation change on its own.

`020` establishes contextual content as declarative UI metadata and implements
its SDK and presentation boundary with a neutral producer. Application
content comes from the application UI schema; selected-session content comes
from the appropriate session schema. Producers decide backend eligibility
in Python. Hosts supply a small explicit view context, execute existing
actions, and own presentation/dismissal. Complex rule code does not move to
the frontend.

`030` uses those actual shared helpers in Home, Sessions, chat, and plugin
settings. Application-owned explanations handle the pre-connection state;
configured plugins provide Sessions/chat content once a runtime is available.
Workspace instructions and operations come from the workspace plugin.

Each child owns its focused tests and maintained documentation. The checks
named above must traverse the real components together; mocked per-side tests
or native fixture layouts alone are not substitutes. Use a local test server
and neutral plugins for the generic connection/contract checks. Embedded
workspace acceptance uses the real iOS runtime and existing actions without
requiring a paid model request.

### Implementation decisions and open questions

- **Accepted direction:** the three-delivery split, Home-first connections,
  generic contextual content, plugin-owned session guidance, shared help
  display, and workspace guidance as an initial consumer.
- **Accepted boundary:** application-owned pre-connection guidance;
  plugin-owned domain content/eligibility; frontend-owned layout and simple
  view-state decisions.
- **Approved for `010`:** existing cards and ordering, three-card collapse
  with footer toggle, preserved card/Open behavior, modal setup, and keeping
  the active connection until a replacement succeeds. Focused connection UI
  extraction is included.
- **Open:** exact visibility, dismissal/help identity, navigation-action
  metadata, producer configuration, and final copy, as
  recorded near the top and in the owning children.
- Review schema and product choices before implementation. Execution approval
  of `010` is approved; the other children still require plan approval.
- Preserve existing test frameworks. Use the iOS simulator for native
  acceptance and the Android emulator for shared mobile scenarios where
  supported; do not add a physical-device gate.

### Documentation

Keep navigation and user guidance in mobile-owned documentation. Document the
supported plugin metadata in `plugins/docs/ui-elements.md` and
`plugins/docs/actions.md`, with SDK/shared-component behavior in their owning
package documentation. The workspace package explains its own contribution.

Update only verified current behavior during execution. Do not create
placeholder documentation or a separate specification hierarchy during this
planning handoff.

### Task checklist

- [ ] Resolve the material questions and approve the relevant execution plans.
- [x] Complete `010` and its public connection-flow verification.
- [ ] Complete `020` and its real-backend contract/display verification.
- [ ] Complete `030`, including the shared help consumers and embedded
  workspace guidance flow.
- [ ] Confirm all parent requirements through their owning evidence and
  complete current user/developer documentation.

### Requirement verification

Use the ownership table and each child's detailed verification plan.
Requirement completion requires its complete approved conditions, not merely
the existence of the new UI element or component. Record native UI evidence
as native UI coverage and real HTTP/embedded runtime evidence at the boundary
actually crossed.

### Additional implementation verification

Run the affected package tests, TypeScript checks, embedded bundle smoke,
documentation preparation, and `git diff --check` in the owning changes.
Re-run existing Home/connection and notification consumers when shared
helpers or navigation change. Do not expand into a provider/API matrix
unless a change or failure exposes a relevant provider risk.

## Implementation Notes

- `010` completed on 2026-10-07. M1 is supported by the real HTTP simulator
  connection/session journey and native Home, connection-settings, and bridge
  mode consumers. Existing cards, ordering, actions, pinning, and persistence
  remain; setup uses the approved modal and retained-connection handoff.
- The connection/navigation portion of M6 is verified by `010`; M6 remains
  incomplete until the other owning children supply their evidence.
- The contextual-content contract and adoption in `020`/`030` remain Draft.