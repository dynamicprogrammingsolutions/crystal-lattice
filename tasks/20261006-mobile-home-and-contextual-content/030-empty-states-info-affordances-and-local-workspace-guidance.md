# Adopt Contextual Content in Mobile Screens and Workspace Guidance

Use the shared contract/display in real Home, Sessions, chat, and settings
surfaces so users can discover useful first actions and reopen explanations
later. Configure plugin-driven session guidance and use the embedded workspace
plugin as the first domain-specific consumer.

## Requirements checklist

- [ ] G1 — Home connection, Watchlist, and Recent sections show actionable
  explanations when appropriate and provide help access when populated,
  using the shared display. Connection setup guidance works with no backend.
- [ ] G2 — Sessions and chat display configured plugin contributions in the
  approved no-session, empty, or always-visible contexts. Their buttons use
  real available actions; no user-facing “first-user instructions” label is
  introduced.
- [ ] G3 — Plugin-declared help is reachable beside relevant production UI
  elements. It uses the shared explanation presentation, including after an
  automatic panel disappears or is dismissed.
- [ ] G4 — New local sessions receive workspace-plugin guidance explaining
  the effective selected working directory and offering access to the
  existing setting/actions. Selection changes refresh the explanation
  without copying files or changing authorization rules.
- [ ] G5 — Guidance/help/actions remain scoped to the correct connection and
  session, survive the approved presentation lifecycle, and preserve existing
  session, notification, and connection behavior.

Parent Task: tasks/20261006-mobile-home-and-contextual-content/000-main.md

Depends On:
tasks/20261006-mobile-home-and-contextual-content/010-home-connection-section-and-navigation.md
tasks/20261006-mobile-home-and-contextual-content/020-contextual-content-contract-and-shared-renderer.md
tasks/20260910-ios-embedded-runtime-poc/027-local-agent-provider-settings-usability.md

Workspace capability reference:
tasks/20260910-ios-embedded-runtime-poc/025-user-selectable-ios-workspaces.md

Use the existing workspace schema/actions. Their unfinished Files-picker and
bookmark acceptance is not completed or waived by this guidance task.
Any newly discovered workspace defect is recorded against its owning work.

## Open questions

- **Generic producer:** recommend one small application-plugin package with
  configurable introductory Sessions/chat content, registered in the
  relevant maintained default and embedded configs. The workspace plugin
  supplies its own domain content. Confirm this ownership/configuration
  rather than hardcoding session instructions in the mobile screens.
- **Copy and first actions:** review the actual explanations and button labels
  before finalizing them. Candidate Home actions are Local provider settings,
  Open connection, New connection, and New session where available. Local
  copy must explain that tools run locally while a configured provider may
  process requests remotely.
- **Workspace placement:** recommend an automatic panel for an empty new
  session and an info affordance beside Working directory afterwards. Confirm
  whether a persistent chat-header info control should also expose it.
- Detailed visibility/dismissal/help/navigation behavior comes from the
  approved `020` contract. Do not create consumer-specific semantics here.

## Supporting facts

- Current Home empty content is device-owned text with no shared help
  affordance. The Sessions screen distinguishes an empty collection from
  search/filter emptiness; retain that distinction when adding guidance.
- The no-selected-session Messages placeholder is owned by
  `ConnectedRoot.tsx`; selected-session chat is owned by
  `SessionChatScreen.tsx`. No-session contributions must load without
  creating a session.
- The embedded workspace plugin returns a `workspace` config element plus
  existing create-private/create-shared/select-external actions. Settings
  renders them through the generic plugin action and client-input path.
- The Python application owns the embedded JSON configuration, while the iOS
  preparation script bundles the selected first-party packages. A newly
  configured guidance producer must be packaged with that application.
- Current full-session schema/cache refresh is not a contextual-content
  contract. `020` establishes the actual invalidation rules used here.

## Execution plan

Status: Draft

### Production consumers and data flow

Use the exact shared normalization, selectors, presentation, help controls,
and action runner delivered by `020`. Home contributes application-owned
content for connection setup, Watchlist, and Recent sessions; its callbacks
operate the real Home connection/settings/session navigation.

Implement the approved generic guidance producer as an application plugin.
Keep configured copy and domain eligibility in the Python application/plugin
layer. Sessions consumes application-scope declarations; the no-selected-chat
host does likewise. Selected chat/settings consumes the appropriate
session-specific declarations. Mobile owns slot placement and simple
view-state facts but does not recognize particular plugin IDs to manufacture
their instructions.

Have the existing workspace plugin declare guidance/help from its effective
workspace selection and existing display labels. Its actions refer to the
existing setting and directory operations. The frontend uses the approved
navigation/action metadata to open Working directory or execute an explicit
operation, including normal confirmation/client input as applicable.

The automatic panel can disappear according to approved visibility rules
while eligible content remains accessible through help. Opening help does
not create a session, run an operation, or reset a dismissal. Successful
workspace actions refresh the schema/content of the owning session; switching
connections or sessions clears obsolete ownership.

Keep existing short states for backends without contextual contributions
according to `020`'s compatibility policy. Loading, offline state, filtered
emptiness, and a genuinely new session remain distinguishable. Any additional
fallback behavior or automatic connection/session creation requires a
decision rather than a test-only shortcut.

### Delivery steps

1. Review concrete copy/actions and producer/placement choices.
2. Adopt shared Home explanations and populated-section help affordances.
3. Configure generic Sessions/chat guidance and connect both no-session and
   selected-session hosts.
4. Add workspace guidance and help beside the production workspace setting.
5. Verify first actions and refresh/dismissal across the actual backend,
   mobile adapters, and embedded runtime; update user/plugin documentation.

### Implementation decisions and open questions

- **Accepted direction:** application-owned Home explanations,
  plugin-driven Sessions/chat content, shared display and help, and workspace
  guidance based on the real selected directory.
- **Open:** generic producer ownership/configuration, copy/action labels,
  and the optional workspace chat-header help location.
- All shared contract decisions are inherited from `020`. Do not introduce
  duplicate renderers, per-plugin frontend branches, new workspace authority,
  or model-generated instructional text.
- The generic native journey covers iOS/Android where supported. Embedded
  workspace acceptance is iOS-simulator-only and needs no hosted model
  request or physical device.

### Documentation

Update the mobile Home/usage guidance for visible first actions and help
access. Document the configured generic plugin's supported contributions and
the workspace package's session/help behavior.

Update embedded configuration/runtime guidance only for verified available
behavior. Do not imply guidance testing completes Files authorization
acceptance or add a folder browser/file-import workflow.

### Task checklist

- [ ] Confirm copy/actions, producer registration, and workspace placement.
- [ ] Adopt shared Home empty content and populated-section help.
- [ ] Configure plugin-driven Sessions/chat contributions and their hosts.
- [ ] Add plugin-declared help to production elements and workspace guidance.
- [ ] Verify real first actions, owner-scoped refresh/dismissal, and relaunch.
- [ ] Update maintained user/plugin documentation and parent evidence.

### Requirement verification

- **G1/G3 — `Mobile guidance journey`:** extend production Home/Sessions/chat
  native scenarios to show empty explanations and first-action buttons,
  populate Home with a real session, and reopen explanations via Watchlist/
  Recent help. Exercise framed/plain and dismissal choices through shared
  components. Native harness checks prove layout/interaction only.
- **G2/G3/G5 — decisive public integration:** extend the real-backend mobile
  consumer with the production screen and settings hosts, actual configured
  guidance/workspace plugins, public UI-schema/action/config routes, and
  `RestAgentBackend`. Click the offered first action, observe the real
  resulting state, then populate/change the session and reopen its declared
  help. Switch connection/session and assert content/actions never retain
  the prior owner. Do not mock the contribution or duplicate the renderer.
- Planned decisive invocation, from the mobile package:
  `npm run test:components:integration -- --runTestsByPath __integration__/MobileContextualGuidance.realBackend.integration.test.tsx`.
- **G4/G5 — decisive `Embedded workspace guidance flow`:** add a Release
  simulator scenario that opens the production Local agent connection,
  creates a session with an existing available agent, displays the real
  workspace contribution, uses its button to open Working directory, and
  creates/selects an app-owned private/shared workspace through existing
  plugin actions. Confirm refreshed help and unchanged selection after
  relaunch through the production embedded backend. No tool inference or
  real Files picker is needed to prove this guidance/action connection.
- Planned decisive invocation, from the mobile package:
  `npx detox test -c ios.sim.release e2e/embeddedWorkspaceGuidance.e2e.test.ts --cleanup`.
  Keep the scenario at the production plugin/runtime/settings boundary;
  a fixture-only native card is insufficient evidence.

### Additional implementation verification

Run affected plugin, SDK/shared-component, and mobile tests/types plus the
rebuilt embedded-application bundle smoke. Check existing notification/help
modals and Home drag behavior after shared presentation changes. Do not
rerun unrelated hosted provider suites merely to test explanatory content.