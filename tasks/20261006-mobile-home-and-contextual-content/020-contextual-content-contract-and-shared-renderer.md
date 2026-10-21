# Add a Generic Contextual-Content Contract and Shared Display

Let plugins contribute contextual information and help through declarative
metadata. Shared frontend code owns presentation, simple view-state
visibility, actions, and local dismissal. Deliver a working shared host and
one real-backend consumer before the production guidance adoption in `030`.

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

`027` and the independently deliverable Home/navigation task `010` are complete.
This task can proceed once its public contract and execution plan are approved.
Production Home/Sessions/chat copy, the generic guidance producer, workspace
content, and broad help adoption remain owned by
`tasks/20261006-mobile-home-and-contextual-content/030-empty-states-info-affordances-and-local-workspace-guidance.md`.

## Decisions requested before execution

These are recommendations for review, not approved implementation decisions.

1. **Visibility and backend rules:** use `always`, `no_session`, and `empty`
   as the small frontend vocabulary. An optional producer-computed boolean
   gates automatic presentation separately from whether help content is
   available. The default automatic gate is enabled. Python decides complex
   rules from its real context; no expressions or executable rule code cross
   the wire. Loading, errors, filtered lists, and partial message ranges do
   not establish emptiness.
2. **Dismissal:** keep it on this device, scoped to the owning context:
   application declarations per connection, session declarations per session,
   and application-owned Home content per device. Allow an explicit
   connection-wide scope for a session declaration when a producer wants one
   dismissal across that connection's sessions. A producer-controlled revision
   resurfaces changed content; ordinary body/value changes do not implicitly
   erase dismissal.
3. **Help metadata:** support a small inline display or a reference to a
   contextual-content ID in the same plugin/context. Existing `description`
   text remains short inline help. Opening help ignores automatic-panel
   visibility and dismissal, but still requires currently available content.
4. **Actions and navigation:** reuse existing link/plugin-action metadata and
   execution. Add a contextual-only frontend navigation action for
   `session_settings` or `server_settings`, optionally focused on a setting
   key. Keep the general action-result union unchanged. App-owned Home
   guidance uses injected application callbacks for its existing connection
   and local-provider navigation.
5. **Source and refresh:** use the authoritative schema for the current
   context instead of merging cached application and session declarations.
   Reuse existing reload/invalidation boundaries. Recommend showing automatic
   cached content only after a successful refresh of that context; loading
   or refresh failure should not establish current eligibility. This is a
   proposed presentation policy, not a change to existing registry consumers.

The proposed field names and combinations are recorded below for a concrete
review. Approval should settle these five choices and the Draft plan together.
No additional guidance copy or production producer is chosen here.

## Research and feasibility

Facts verified in the current checkout:

- `AgentApplication.get_application_ui_schema()` passes an application
  context, server settings, config, tags, and models to application plugins
  and preserves opaque element data. `get_session_application_ui_schema_for_session()`
  additionally supplies the complete persisted session, its ID, effective
  overrides, and base config. Complex session eligibility needs no synthetic
  session or new backend query endpoint.
- `RestAgentBackend.listApplicationUiSchema()` uses
  `/application/ui-schema`; `getSessionApplicationUiSchema()` uses
  `/sessions/{id}/application/ui-schema`. Both already return opaque
  dictionaries. The new family needs SDK interpretation, not another
  transport protocol.
- `PluginsRegistry` retains only selected element families in its public
  result today. Its raw cache can carry contextual declarations, but the
  registry and React context must expose their normalized form.
- Application registry refresh already follows server-settings and
  application-action invalidation. Session schema controllers have
  connection/session cache keys and explicit invalidation. Existing action
  responses can invalidate session schemas. Their caches are not themselves
  a complete contextual refresh policy.
- `ActionDisplayPayload` already has text/Markdown, title, body, ordinary
  follow-up actions, optional forms, and presentation. `ActionDisplayCard`
  is mobile-owned, always frames the body, and supplies an `Action Result`
  title when none is provided. Its body/actions can be extracted for reuse;
  contextual content should not inherit that result-specific title.
- `ActionUiElement` includes `dialog`, `fixed_params`, `param_map`, owner,
  and `client_input`. `runApplicationAction()` accepts acquired client
  values. The current `ActionDisplayRunActionAction` type does not carry
  `client_input`; merely reusing that type would not preserve directory
  acquisition. The contextual adapter must preserve the existing UI-action
  metadata and invoke the existing acquisition/dialog path.
- Current message/query DTOs inspected for this work do not supply a
  guaranteed full-history count. The mobile chat normally loads a range.
  Do not infer an empty session from an empty displayed range or load the
  entire transcript solely to show guidance. A session producer can compute
  its automatic gate from the full session already in its schema context.
- `NotificationDismissalCache` is tied to notification revisions and
  server lifecycle acknowledgement. Its storage patterns are useful, but
  contextual dismissal needs its own records and no notification mutation.
- The existing mobile component integration harness starts a real public
  backend and constructs `RestAgentBackend`. Its action-display integration
  consumer already exercises real follow-up dialogs and returned displays.

Feasibility conclusion: the existing schema, action, and rendering boundaries
support this delivery. The work is concentrated in SDK selectors/state,
shared presentation, and mobile adapters. It requires no model request,
production server access, new native module, dependency installation during
planning, or production default-config change.

Primary continuation references:

- `core/python/agent_app/application_future.py` — application/session schema
  context and aggregation.
- `packages/frontend-sdk/src/plugins/pluginsRegistry.ts`,
  `types/plugins.ts`, `types/uiSchema.ts`, and `plugins/actionRunner.ts`.
- `packages/frontend-sdk/src/uiSchema/sessionApplicationUiSchemaController.ts`
  and existing schema/settings invalidation helpers.
- `packages/frontend-sdk-react/src/applicationPlugins.tsx`.
- `mobile/crystal-lattice-control-rn/src/components/ActionDisplayCard.tsx`,
  `GlobalDisplayLayer.tsx`, and `SessionSettingsModal.tsx`.
- `mobile/crystal-lattice-control-rn/__integration__/support/mobileComponentBackend.ts`
  and `ActionDisplayForm.realBackend.integration.test.tsx`.

## Execution plan

Status: Draft

### Proposed declaration

Keep the family generic: `ui_type: "contextual_content"`. This example is a
proposed schema for review, not a current supported declaration:

```json
{
  "ui_type": "contextual_content",
  "id": "workspace-guidance",
  "placement": "session_chat",
  "visibility": {
    "when": "always",
    "enabled": true
  },
  "appearance": "card",
  "dismissal": {
    "scope": "session",
    "revision": 1
  },
  "display": {
    "format": "markdown",
    "title": "Working directory",
    "body": "Files are read and written in this session's selected workspace.",
    "actions": [
      {
        "kind": "navigate",
        "id": "open-workspace-setting",
        "label": "Working directory",
        "target": "session_settings",
        "setting_key": "workspace"
      }
    ]
  }
}
```

Use `session_list` and `session_chat` as the initial plugin placement targets.
The host chooses the physical location within those screens; metadata does
not name React components, native views, selectors, or arbitrary routes.
Application-owned Home content passes the same normalized presentation shape
to its own host.

`appearance` is `card` or `plain`. Omitting `dismissal` makes the automatic
panel non-dismissible. The proposed scope vocabulary is `connection` or
`session` for plugin declarations; the host supplies context identity rather
than trusting a descriptor to select another connection/session.
Application-owned content can use its own device context without exposing a
new remote device-scope operation.

Visibility applies to automatic placement. `no_session` uses selection state.
`empty` is supplied as a known/unknown host fact and is true only after an
authoritative empty collection is established. Successful unfiltered,
unlimited list reads can establish list emptiness; a filter or partial range
cannot. Session producers can instead use `when: "always"` with a Python-
computed `enabled` flag based on full history. This lets them keep a help
descriptor available after its automatic panel should disappear.

For help, propose either:

```json
{"help": {"content_id": "workspace-guidance"}}
```

or:

```json
{"help": {"display": {"format": "text", "body": "Explanation of this setting."}}}
```

Resolve references in the declaring plugin's owning schema context.
Application-owned help passes a resolved descriptor directly. Keep existing
short descriptions; adding richer help does not move every description into
a dialog or make it disappear.

### Ownership and sources

The backend owns content, domain rules, and publication. The SDK owns
normalization, source identity, simple selection, and dismissal records. The
React package binds those states to hosts. Shared RN components own body,
frame/plain presentation, buttons, and info affordances. Mobile supplies
Markdown/theme adapters, actual action execution, storage, and bounded
navigation callbacks.

Use the application schema for a no-session context and the selected session
application schema for a selected session context. That session endpoint
already reevaluates application plugins with the session context; do not
overlay a stale application-registry copy of the same declaration. Core
session config/schema remains available for help attached to its own elements.
Preserve backend ordering and scope content identity by plugin and stable ID.
Server settings uses its own schema context for declared help; it does not
need an automatic content placement inside settings for this first delivery.

App-owned Home content is independent from backend publication and remains
usable before a connection exists. Publishing, selecting, dismissing, or
reading content never executes a plugin action or model request.

### Rendering and action flow

Extract reusable display body/actions from `ActionDisplayCard` into the
shared package with injected Markdown and action callbacks. Preserve the
existing action-result wrapper, its forms, bounds, titles, and follow-up
behavior through at least one existing consumer.

Compose a contextual host and help control from that shared presentation.
The automatic host uses the selector and local dismissal state. Help opens
the currently available explanation even when its automatic panel is hidden
or dismissed. Inside a settings modal, help must use that modal's existing
overlay surface rather than presenting a competing native modal.

Normalize contextual plugin operations with the existing `ActionUiElement`
fields, preserving any declared dialog and client-input acquisition.
Execute through `runApplicationAction()` and the production mobile adapter,
bound to the source connection/session. Returned displays and effects go
through the existing display/dialog pipeline.

The contextual navigation variant dispatches only the approved host
callbacks. It does not alter the shared `ActionDisplayFollowupAction` union
or add a general navigation interpreter. The focused-setting path opens
existing settings and reveals the declared field through the production
settings host.

### Refresh and local state

Load declarations on entry to their owning view/context and reuse existing
schema invalidation after settings, actions, and session changes. Ensure
session-history changes refresh any schema-derived automatic gate. Preserve
connection/session identity during asynchronous loads; an old response cannot
populate another selected context.

For contextual presentation, loading or a failed refresh is not authoritative
eligibility. Retain data only within its owning cache context and do not
automatically present cached guidance until that context has been refreshed
successfully. Existing registry behavior for other element families stays
unchanged. Add no separate polling service or server content store.

Store dismissal in a separate device-local key-value record keyed by
application/connection context, plugin or app producer, content ID, applicable
session ID, and revision. A changed producer revision shows a new automatic
panel. Viewing help does not clear dismissal or change a notification record.
Use the existing storage-adapter pattern, with mobile supplying AsyncStorage.

### Incremental delivery and affected boundaries

1. Implement normalized declarations, source selection, and a basic text/
   Markdown panel through the existing public schemas. Demonstrate it with a
   neutral plugin and the production adapter before adding the complete
   help/dismissal behavior.
2. Extract shared body/actions and adapt the existing action display.
   Add framed/plain contextual presentation and the bounded navigation/action
   adapter; retain the established dialog and client-input flow.
3. Add scoped local dismissal and inline/reference help. Exercise a real
   setting label/control through its production renderer, not a fixture-only
   imitation of settings.
4. Complete dynamic backend eligibility, refresh/isolation checks, and
   author/package documentation. Leave product guidance/configuration to `030`.

Required changes are limited to:

- SDK UI types/normalizers, application-registry exposure, context selection,
  existing schema refresh integration, and local dismissal state.
- React bindings for the new normalized state where existing hooks do not
  suffice.
- Shared display/help components and focused extraction from the existing
  mobile display wrapper.
- Mobile presentation/action/navigation adapters and one production settings
  help entry point.
- A neutral test plugin/consumer and its public-boundary checks.

Keep neutral fixtures in their owning test package using supported plugin
loading. Do not add a production guidance package or runtime dependency to
make the test fixture discoverable.

### Implementation decisions and open questions

- The five contract/lifecycle recommendations near the top remain unapproved.
  The JSON examples make them reviewable, not implemented or finalized.
- Source selection is proposed as authoritative per context, with no app/
  session duplicate merging or cross-plugin reference lookup.
- The initial navigation targets are session/server settings plus an
  optional setting key. Login, connection switching, folder browsing,
  purchase flows, and arbitrary app targets are outside this delivery.
- Config `description` remains current short help. The common helper must
  allow `030` to adopt help beside other plugin/app elements without copying
  rendering or defining another metadata family.
- No new total-history endpoint is planned. Producers compute full-session
  rules in Python; unknown frontend emptiness suppresses automatic empty
  content.
- Preserve existing treatment of unknown UI families and established
  nonfatal schema diagnostics. Detailed validation follows the approved
  field contract; do not invent unrelated fallback/error workflows.
- Main risks are stale context, help inside an existing native modal,
  preserving client-input/dialog behavior, and accidental action-display or
  notification lifecycle coupling. Verify those actual boundaries.

### Documentation

Keep the new schema visibly unimplemented in this Draft task. During approved
execution, document supported producer fields, Python predicates, help,
revision/dismissal, and contextual actions in `plugins/docs/ui-elements.md`
and `plugins/docs/actions.md`; explain the distinction from notifications in
the existing notification/action-display guide.

Document SDK source/refresh/local-state behavior in its existing development
documentation and shared presentation/adapter responsibilities in the RN
package. Use the React README for any new hook contract rather than creating
placeholder documentation directories. Product onboarding copy belongs to
`030`, not these framework docs.

### Task checklist

- [ ] Confirm the five material recommendations and execution plan.
- [ ] Add SDK declarations, context-specific exposure/selection, and a basic
  real-backend text/Markdown consumer.
- [ ] Extract shared presentation and preserve a production action-result
  consumer.
- [ ] Add contextual actions/settings navigation and preserve dialog/client
  input handling.
- [ ] Add scoped dismissal and inline/reference help through a real settings
  renderer.
- [ ] Verify backend predicate changes, refresh/revision, and context isolation.
- [ ] Pass focused existing action/notification consumers and package checks.
- [ ] Publish supported author/package documentation and requirement evidence
  for `030`.

### Requirement verification

- **C1/C3:** selector/component checks exercise the approved simple states,
  producer gate, framed/plain presentation, text/Markdown/actions, local
  dismissal, and inline/reference help. Unknown/loading/filtered/partial-range
  state must not be asserted to mean empty.
- **C2/C4/C5 — decisive `Contextual content public integration`:** add
  `mobile/crystal-lattice-control-rn/__integration__/ContextualContent.realBackend.integration.test.tsx`.
  Use `startMobileComponentBackend`, public UI-schema/action/settings routes,
  `RestAgentBackend`, a real neutral application plugin, and the production
  shared host/adapter. Read no-session content without creating a session,
  create/select a real session, change plugin-owned eligibility through a
  public action/setting, refresh, and observe the new content/gate. Execute a
  declared plugin operation and display its real result through the existing
  runner. Compare model messages and notification records before/after
  presentation and dismissal; they remain unchanged.
- **C3/C4:** include a real production setting element with declared help.
  Its info control opens the shared display inside the actual settings host.
  A contextual navigation button opens/focuses that field through the
  production adapter. Verify a real action dialog and the existing client-
  input callback boundary without replacing action dispatch with a mock.
- **C5:** through the same public consumer, check dismissal after remount,
  reopening help, revision resurface, server/session isolation, and a late
  schema response after context selection changes.
- Decisive HTTP/component invocation from the mobile package:
  `npm run test:components:integration -- --runTestsByPath __integration__/ContextualContent.realBackend.integration.test.tsx`.
- **Native modal boundary:** add a focused simulator case using the
  production settings/help host and stable entity selectors. Prove that
  help opens and closes inside settings, links/actions remain usable, and
  returning leaves the setting interactive. Invocation:
  `npx detox test -c ios.sim.release e2e/contextualContent.e2e.test.ts --cleanup`.
  A native fixture can supply deterministic declarations, but cannot replace
  the production modal or renderer. Report native UI evidence separately
  from the real HTTP integration evidence.

### Additional implementation verification

Run affected SDK, React-binding, shared-component, and mobile tests/types.
Verify the existing `ActionDisplayForm.realBackend.integration.test.tsx`
consumer after presentation/action extraction, plus an existing notification
consumer to ensure its dismiss/resolve lifecycle remains independent.

Add the decisive HTTP and simulator commands to root `package.json` during
execution. No hosted API/provider matrix, manual ChatGPT login, production
server access, new native module, or physical-device acceptance is required.