# Add a Generic Contextual-Content Contract and Shared Display

Let plugins contribute contextual information and help through simple
declarative metadata, while shared frontend code owns display, simple
view-state visibility, actions, and presentation dismissal. Establish the
contract with a neutral real-backend consumer before product adoption.

## Requirements checklist

- [ ] C1 — A generic plugin/frontend UI contract expresses text/Markdown
  contextual content and action/link buttons, applicable to empty/no-session
  or always-visible contexts, with framed/plain and dismissible/
  non-dismissible presentation.
- [ ] C2 — Plugins can use arbitrary Python eligibility logic based on their
  available application/session context. A session is not required for
  application-level contributions. The frontend handles a small explicit
  set of view-state conditions without evaluating a new general rule
  language.
- [ ] C3 — One shared SDK interpretation and display/help component family
  serves application-owned and plugin-owned content. Plugin UI elements can
  declare explanations that those components present via an info affordance.
- [ ] C4 — Links and plugin operations use the existing action execution,
  dialog, client-input, and result-display behavior. App-view navigation uses
  an explicit bounded frontend contract, and actions target the owning
  connection/session.
- [ ] C5 — Content refresh and presentation dismissal remain isolated by
  their owning context and do not mutate model history or notification
  lifecycle records. Existing UI schema/action/notification consumers remain
  compatible.

Parent Task: tasks/20261006-mobile-home-and-contextual-content/000-main.md

Depends On:
tasks/20260910-ios-embedded-runtime-poc/027-local-agent-provider-settings-usability.md

This is the agreed second-round sequence, not a dependency on the OpenAI
layout implementation. `010` can run independently. Production screen and
workspace content adoption is owned by `030`.

## Open questions

- **Visibility:** recommend distinguishing `no_session` from `empty` and
  `always`, with documented host meanings. Sessions emptiness should use the
  authoritative collection rather than a filtered visible list; transcript
  emptiness should not be inferred from a partial loaded range. Confirm the
  wire values and how the host obtains sufficient facts.
- **Dismissal:** recommend a device-local identity combining connection,
  plugin/content ID, context scope, optional session ID, and producer
  revision. Confirm whether a changed revision resurfaces automatically and
  whether dismissal is session-local or connection-wide for each declaration.
- **Help metadata:** should an element contain an inline `help` display,
  reference a contextual-content ID, or support both? Recommendation:
  references for reused content plus a small inline form for one-field help;
  retain existing `description` as ordinary short help. Confirm the schema
  before implementing it.
- **Navigation actions:** recommend a contextual-action wrapper referencing
  existing plugin actions and a finite set of app targets, initially
  session settings and an optional setting key. Confirm whether this belongs
  to contextual metadata or extends the shared action-display union.
- **Sources and refresh:** confirm application versus session declaration
  precedence and when content is refreshed. Recommendation: use authoritative
  context-specific schemas and existing reload/invalidation boundaries;
  no separate polling service or new persisted server content store.

## Supporting facts

- Core UI declarations are opaque and application UI schema adds plugin IDs
  and ordering. The existing public application and session UI-schema
  endpoints can carry an additional declarative element without replacing
  current schemas.
- Session application UI receives effective config and the persisted session.
  Application UI receives an application context and server settings but no
  selected session. Complex domain rules can therefore stay in the producer.
- `PluginsRegistry` retains selected UI element families and will need to
  expose normalized contextual elements. Session schema controllers already
  have load/invalidation boundaries.
- `ActionDisplayPayload` supports body, format, optional title/variant, and
  link/copy/run-action follow-ups. The existing action runner understands
  dialogs and parameter maps. Session directory acquisition already uses
  `client_input` and returns an opaque grant to plugin actions.
- `ActionDisplayCard` is currently mobile-owned and assumes a framed result
  surface. Reuse its content/actions through composition or extraction;
  do not fork its renderer into a second implementation.
- Notification dismissal caches synchronize lifecycle mutations with the
  server. Contextual dismissal can reuse key-value-store patterns, but does
  not require those notification mutations or retry semantics.

## Execution plan

Status: Draft

### Proposed declaration and boundaries

Use `ui_type: "contextual_content"` as the proposed family. The following
example records the reviewed shape; it is not a finalized public schema:

```json
{
  "ui_type": "contextual_content",
  "id": "workspace-guidance",
  "placement": "session_chat",
  "visibility": "empty",
  "appearance": "card",
  "dismissal": {"mode": "local", "revision": 1},
  "show_info": true,
  "display": {
    "format": "markdown",
    "title": "Working directory",
    "body": "Files are read and written in this session's selected workspace.",
    "actions": []
  }
}
```

Application schemas supply no-session content; session schemas supply content
for a selected session. Specify source precedence and identity in the approved
contract before adding merging behavior. Expose the available backend facts
through existing plugin context rather than installing a frontend condition
interpreter or manufacturing a hidden session.

Add a normalized SDK type/selector and controller integration, keeping
presentation metadata separate from eligibility logic. A host supplies
explicit collection/selection/message state; its selector applies only the
approved simple states. Do not treat loading or failure as proven emptiness.

Put host-neutral React bindings in `frontend-sdk-react` where needed, and
reusable presentation/help controls in `frontend-rn-components` with injected
theme/Markdown/action renderers. Mobile provides those adapters and app-view
navigation. Application-owned Home explanations pass the same normalized
content shape, using application-owned action callbacks.

Use existing plugin/action routes for operations and returned displays.
Frontend navigation is a separate recognized action unless an approved
extension to the shared action union is chosen. Publishing or viewing content
does not execute an operation or model request. Preserve directory
client-input handling when a contributed action requires it.

Store only local dismissal identities under the approved scope. An info sheet
can reopen eligible content independently of whether its automatic panel was
dismissed. Backend-ineligible content follows the approved source/refresh
policy rather than remaining visible from an unrelated cached context.

### Delivery steps

1. Resolve and document the minimal wire fields, source/visibility semantics,
   dismissal identity, help metadata, and navigation action.
2. Implement SDK interpretation, scoped refresh/dismissal, and shared
   presentation/help components.
3. Connect a neutral application-plugin fixture through the real public
   backend and production adapter to the shared host.
4. Exercise a plugin rule change, action result, and help/dismissal behavior
   in that consumer; publish supported author/SDK guidance.

### Implementation decisions and open questions

- **Accepted direction:** declarative contextual content, Python-owned
  complex eligibility, shared presentation, explicit simple frontend states,
  and local presentation dismissal separate from notifications.
- **Open:** the exact public fields and lifecycle semantics listed near the
  top. Recommendations are not implementation decisions until confirmed.
- Add no arbitrary component names, executable frontend rules, raw screen
  selectors, or notification status fields to the descriptor.
- Keep neutral fixtures in the owning test package or shared `test/` support;
  they are not production guidance plugins. Use a real consumer of the shared
  helper in verification.

### Documentation

Document the supported declaration/help/action fields and a small Python
producer example in `plugins/docs/ui-elements.md` and
`plugins/docs/actions.md`. Explain the distinction from notifications in the
existing notification/action-display guide.

Document shared SDK source/refresh/dismissal behavior and component adapter
responsibilities in the owning package documentation. No separate
specification hierarchy is required for this handoff.

### Task checklist

- [ ] Confirm the public contract/lifecycle questions and execution plan.
- [ ] Add normalized SDK declarations and context-specific schema exposure.
- [ ] Implement shared presentation, actions, help, and scoped dismissal.
- [ ] Integrate a neutral real-backend consumer and prove dynamic eligibility.
- [ ] Verify existing action/notification consumers and update author/package
  documentation.
- [ ] Record requirement evidence for the downstream production adoption.

### Requirement verification

- **C1/C3:** focused selector/component checks cover the approved visibility,
  framed/plain, dismissal, text/Markdown/action, and help combinations.
- **C2/C4/C5 — decisive `Contextual content public integration`:** add
  `__integration__/ContextualContent.realBackend.integration.test.tsx` in
  mobile using `startMobileComponentBackend`, public UI-schema/action/config
  routes, `RestAgentBackend`, real neutral plugins, and the production shared
  host/runner. Fetch no-session content, select a real session, change a
  plugin-owned state through a public action or setting, refresh, and assert
  changed eligibility/content and correctly scoped action execution.
  Assert the same operation does not create notification records or model
  messages. Separate mocked route/display tests do not satisfy this check.
- Planned decisive invocation, from the mobile package:
  `npm run test:components:integration -- --runTestsByPath __integration__/ContextualContent.realBackend.integration.test.tsx`.
- Verify local dismissal and connection/session identity through that
  consumer using the approved revision rules. Use at least one real setting
  element with declared help rather than a fixture-only help-button copy.

### Additional implementation verification

Run affected SDK, React-binding, shared-component, and mobile tests/types.
Verify an existing action display and notification consumer after any shared
renderer/runner change. Unknown/unsupported schema handling follows the
approved compatibility contract; do not invent a new fallback during
implementation merely to satisfy a test.