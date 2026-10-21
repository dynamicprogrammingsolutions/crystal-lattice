# Codex Browser Login And Method Selection

Add a production-ready Codex browser OAuth path alongside the existing
device-code flow, using one complete contributed terminal login operation and
the existing provider action/credential architecture.

## Requirements checklist

- [x] Existing Codex device-code login remains supported and selectable.
- [x] Codex browser OAuth performs PKCE authorization, callback validation,
  token exchange, refresh-compatible persistence, and account metadata
  extraction without changing the credential format consumed by OpenAI
  Responses.
- [x] A top-level contributed command can start one complete Codex login flow,
  present or open the authorization URL, report progress, wait for callback,
  and finish with a terminal result.
- [x] The interactive terminal can invoke the same complete flow through a
  contributed slash command.
- [x] When provider policy permits, terminal browser login uses a temporary
  loopback callback server owned by the auth plugin and closes it after
  success, failure, cancellation, or expiry.
- [x] Terminal and same-host desktop/backend arrangements can complete browser
  login through the plugin-owned loopback listener on provider-accepted port
  `1455` or `1457`; the browser must run on the listener host.
- [x] Device code remains a production Codex login path for mobile, remote,
  and headless arrangements. No raw embedded WebView or public bridge callback
  relay is introduced.
- [x] A provider-neutral `session_action_callback` UI element is the only
  action-deep-link exposure boundary, and generic/MCP callback consumers no
  longer invoke bare action ids.
- [ ] Mobile browser login uses a UI-owned one-shot localhost receiver and a
  system authentication/browser surface, without making the embedded Python
  runtime own the listener, requesting background execution initially, or
  adding an Android service.
- [ ] iOS first attempts `ASWebAuthenticationSession`; Android first attempts
  Chrome Custom Tabs. Alternatives are gated on recorded failure evidence from
  the corresponding primary surface.
- [ ] Browser and device-code login are exposed as separate applicable UI
  elements: browser uses the provider-neutral `session_browser_auth`
  orchestration element bound to start/status/cancel and the existing
  `session_action_callback`; device code remains an ordinary action-backed
  `session_action` with fixed `method=device-code` and existing
  display/notification/action behavior.
- [ ] Mobile browser login binds `127.0.0.1` before start, advertises
  `http://localhost:<1455|1457>/auth/callback`, forwards the callback URL
  opaquely through named callback-element routing, returns to the app without
  putting code/state/token data in an app link, persists/logs no callback
  secrets, and closes cleanly.
- [x] Callback state, PKCE verifier, authorization code, access token, refresh
  token, and account identifiers remain out of ordinary displays and logs.
- [x] Stale, duplicate, expired, cancelled, and superseded callbacks cannot
  replace current credentials.

Parent Task:
`tasks/20261016-provider-login-experience/000-main.md`

Depends On:

- `tasks/20260824-plugin-driven-cli-and-interactive-terminal-commands.md`

## Resolved requirement decisions

The user approved the plan recommendations and the separately bounded
capability probe on 2026-10-19.

1. Begin with the minimal pi-compatible scopes needed by the existing OpenAI
   Responses credential consumer. Add connector scopes only if provider
   behavior proves they are required.
2. Treat localhost ports `1455` and `1457` and the provider-owned
   `https://auth.openai.com/deviceauth/callback` as accepted through the
   pre-sign-in boundary. The provider rejected both
   `crystal-lattice://oauth/callback` and
   `https://crystal-bridge.dynamicprogrammingsolutions.com/oauth/callback`
   with `invalid_authorize_request`.
3. Deliver browser OAuth for terminal and same-host desktop/backend
   arrangements. Retain device code as the production mobile, remote, and
   headless fallback. Do not add a raw embedded WebView or an HTTPS/public
   bridge callback relay.
4. Omit manual browser callback/code entry. Device code is the remote/headless
   fallback, preserving the approved bounded foreground command contract.
5. The completed terminal implementation introduced public method values
   `browser` and `device-code`, browser defaults, and raw-action compatibility.
   The mobile planning decisions below supersede nested method selection for UI
   exposure and require separate browser/device elements.
6. Add one provider-neutral condition over mapped command input/result state
   so only browser OAuth may auto-open. Preserve the inherited always-print,
   local-interactive best-effort opening, and `--no-open` policy.
7. Add `session_action_callback` as the applicable UI element authorizing
   generic callback invocation. Route by callback element id, require
   provider-generated links to include the plugin id, retain omitted-plugin
   routing only for one uniquely applicable callback element, map only
   declared `$callback.*` values, and remove raw action-id deep-link invocation
   with no compatibility bypass.
8. Use a bounded memory-only callback queue, dispatch immediately to any open
   named connection, require explicit opening of a known closed connection,
   and never change focus or navigation automatically.
9. Allow the complete authorization URL as the sole user-visible
   state-bearing exception. Never render state separately, and omit account id
   and email from ordinary status while retaining them only in backend
   credential storage.
10. The approved capability probe is limited to reviewed unauthenticated
    production authorize requests with fresh state/PKCE and candidate redirect
    URIs. It stops before sign-in, callback code issuance, token exchange,
    credential writes, refresh, or model requests.
11. Real browser/device sign-in, token/refresh acceptance, credential writes,
    and a model request remain a later human-assisted acceptance checkpoint
    requiring separate explicit approval. Capability-probe approval does not
    authorize them.
12. Inspect mobile source/native APIs and use safe deterministic harnesses to
    assess a mobile-owned localhost listener plus external/system browser
    handoff. Do not productize it or choose a material native lifecycle design
    unless evidence is decisive; otherwise record the unresolved decision and
    keep production mobile on device code.

## Approved mobile planning decisions

The user materially reopened mobile browser login for planning after the
initial feasibility result. These decisions supersede the prior conclusion
that mobile browser login should remain indefinitely unproductized and the
prior nested method-selection UI direction:

1. The embedded Python runtime must not own the mobile loopback listener unless
   a later failed native investigation proves it uniquely necessary.
2. The first and primary browser surfaces are iOS
   `ASWebAuthenticationSession` and Android Chrome Custom Tabs. Investigate an
   alternative only after its platform's primary path fails with recorded
   evidence.
3. Do not initially request iOS background execution time or add an Android
   foreground/background service. The initial premise is that the system
   authentication/browser session keeps the flow viable; lifecycle evidence
   must verify or falsify that premise.
4. Browser and device-code login are separate UI elements. Browser requires
   one new provider-neutral orchestration type; device code stays on the
   existing ordinary action-backed session UI contract. Neither is a method
   selector nested inside the other.
5. `openAuth`-style custom/HTTPS callback handling does not solve this flow:
   the Codex public client rejected both investigated app/public redirects.
   The system browser surface must use the provider-accepted localhost
   redirect and a UI-owned localhost receiver.
6. A raw embedded WebView and a public callback relay remain excluded.
7. Device code remains the safe production fallback throughout investigation
   and after any rejected browser attempt.
8. Fallback investigation is ordered: iOS may investigate
   `SFSafariViewController` only after decisive
   `ASWebAuthenticationSession` failure; Android may investigate service or
   background mechanisms only after decisive Custom Tabs lifecycle failure.
   Embedded-Python listener ownership requires still-later evidence that native
   ownership cannot satisfy the contract and that the runtime is uniquely
   necessary.

## Repository reassessment

- Workspace verification on 2026-10-19:
  - `pwd`:
    `/Users/ferenci84/Dev/Mine/ai-agent-platform-provider-login-orchestration`
  - `git rev-parse --show-toplevel`:
    `/Users/ferenci84/Dev/Mine/ai-agent-platform-provider-login-orchestration`
  - The worktree was clean and detached at
    `3cb26fc70f9e2e2f3381a101868826247860163d`
    (`Add plugin-driven login flows`). There were no later or uncommitted
    changes to reconcile.
- Commit `3cb26fc7` completed the declared dependency. It added validated
  action-backed CLI/slash command elements, one shared result renderer,
  foreground start/status/cancel orchestration, `--no-open`, local-interactive
  best-effort browser opening, attempt-scoped interruption, and the first
  complete ChatGPT device-code consumer.
- The dependency is complete and approved. This subtask must extend that
  architecture; it must not add a provider-specific terminal execution path,
  a second command API, or a user-coordinated start/status/cancel sequence.
- The later approved capability probe is recorded in Implementation Notes. No
  browser launch, sign-in, callback code, token exchange, credential write,
  refresh, or hosted model request was performed.
- Read-only AWS inspection found the live bridge host on the Ireland EC2
  server, verified `/health` returns 200, and observed the current
  `/oauth/callback` route returns 404. No DNS, AWS, server, deployment, or
  infrastructure state was changed.

## Supporting details

### Current Crystal Lattice behavior

- `plugins/chatgpt-auth-app` has one application-global active attempt. Its
  `login_start`, `check_status`, and `cancel_login` actions drive a device-code
  worker and atomically persist `auth/chatgpt-auth.json`. Attempt identity and
  cancellation already prevent a stale device worker from committing after a
  newer active attempt.
- The current command bindings are exactly
  `crystal-lattice auth login codex` and `/login codex`. They have no method
  input, no browser metadata, and bind the same `login_start` action and
  foreground status/cancel contract.
- The generic command layer can already expose form inputs as top-level
  `--name` options and slash `name=value` inputs. It supports select/dropdown
  choices, prompts omitted slash inputs, prints `open_url` actions, recognizes
  `--no-open`, auto-opens only when command browser metadata permits it, and
  keeps the command active until a declared terminal state.
- Application plugins are instantiated once per `AgentApplication`; their
  explicit state can own an attempt-scoped listener. The wrapper calls an
  optional plugin `close(state)` hook, providing a lifecycle point for worker
  and callback-listener cleanup.
- `plugins/openai_responses` consumes `access_token`, `refresh_token`,
  `id_token`, `token_type`, `expires_at`, and account metadata from the same
  saved file. It refreshes through `https://auth.openai.com/oauth/token`,
  preserves a rotated or omitted refresh token correctly, and sends
  `ChatGPT-Account-Id` when present. Browser login must keep this format and
  refresh behavior unchanged.
- The current ChatGPT status display exposes account id, and sometimes email.
  That conflicts with this task's explicit ordinary-display restriction and
  must be corrected as part of the browser work without removing the metadata
  from backend credential storage.

### Provider and reference evidence

- Local `pi` at `e44d75c20a` implements Codex browser OAuth with:
  - `https://auth.openai.com/oauth/authorize` and `/oauth/token`;
  - public client id `app_EMoamEEZ73f0CkXaXp7hrann`;
  - redirect `http://localhost:1455/auth/callback`;
  - PKCE S256, random state, `openid profile email offline_access`,
    `id_token_add_organizations=true`,
    `codex_cli_simplified_flow=true`, and an originator;
  - a plugin-owned loopback listener plus a pasted redirect/code race;
  - browser as the first/default method and device code as the headless method.
- Local Codex at `0650d6d1ca` uses the same authorize/token client and callback
  path. Its current server binds `127.0.0.1`, advertises
  `http://localhost:<port>/auth/callback`, prefers port `1455`, and falls back
  to registered port `1457`. The source explicitly says those ports must stay
  synchronized with the OAuth redirect allow-list. It validates state before
  exchanging the code, bounds browser login, returns a small browser response,
  and keeps device auth as the remote/headless path.
- Codex currently requests additional connector scopes. pi does not. The
  approved probe established only the pre-sign-in redirect boundary; it did
  not authorize or prove hosted sign-in, callback completion, token exchange,
  refresh, or provider requests.
- Local OpenCode at `1c7c03332e` reinforces the foreground interaction model:
  return URL/instructions, gather automatic or code input, report progress, and
  await one terminal result. It does not justify moving provider protocol into
  a frontend.

### Frontend routing evidence

- `packages/frontend-sdk` parses generic
  `crystal-lattice://action/<connection>/<session>/<plugin>/<action>` links and
  passes query inputs plus the original `redirect_url` to a session action.
- Mobile registers the `crystal-lattice` scheme on iOS and Android and routes
  incoming links to a named connection/session. At this revision it can execute
  only against the selected backend, retains only one pending callback in
  React state, and loses that callback on process restart.
- Desktop has multiple open backends but no `parseActionDeepLink` consumer, no
  incoming-Linking subscription, and no macOS custom-URL registration in this
  revision.
- Existing MCP integration tests prove that a plugin can create an
  action-targeted redirect URI and that the mobile router can send its callback
  to a real backend action. They do not prove Codex redirect acceptance,
  desktop OS routing, multi-connection routing, stale callback rejection, or a
  real OAuth exchange.
- The current deep-link contract resolves the last path segment as an action
  id and calls the session action endpoint directly. That bypasses the approved
  rule that callable actions gain external exposure only through applicable UI
  elements. The corrected plan replaces that behavior with an applicable
  callback UI element; it does not preserve raw-action deep-link invocation.

## Separate generic follow-up: headless action discovery and execution

After the generic action-command dependency and this worktree are merged,
create a separate application-owned task for model agents and non-interactive
automation. This is not a Codex browser-login requirement, does not block this
task, and must not add provider-specific auth behavior to the generic command
layer.

The follow-up should reuse the applicable-action discovery, context
construction, validation, execution, result rendering, disabled-state, and
reference behavior already implemented for interactive `/action` rather than
building a second interpretation of UI elements.

Target surfaces:

```text
crystal-lattice actions [context selectors] --format text|json
crystal-lattice action run --plugin PLUGIN --id ELEMENT_ID \
  [context selectors] [structured inputs] --format text|json
```

and equivalent `LocalAgentRuntime` methods for listing applicable
action-oriented UI elements and executing one selected element.

The task should cover:

- application, session, session-list, and message contexts supported by the
  interactive action surface;
- qualified plugin/element identity and unqualified selection only when
  unique;
- action label, description, scope, form/dialog schema, defaults, fixed
  parameters, disabled state, and disabled reason;
- config- and condition-aware applicability from the active runtime rather
  than a static plugin inventory;
- non-interactive structured input with the same coercion and validation as
  the interactive terminal;
- bounded structured results and follow-up references;
- explicit handling for confirmation, secret, and password fields without
  accepting sensitive values in ordinary command arguments, echoes, logs, or
  diagnostics;
- corresponding plugin and effective UI-schema discovery so an agent checks
  active config/schema/actions before consulting plugin README/docs or source;
- package-user documentation that points unresolved behavior to the
  runtime-provided built-in plugin documentation/source root.

Verification must compare headless and interactive discovery for the same
contexts, execute representative application/session/message actions through
the production application boundary, prove disabled and ambiguous actions
cannot run, and assert that sensitive inputs and unrestricted action payloads
do not enter command output.

## Execution plan

Status: Approved

Preserve the completed terminal and same-host desktop/backend browser OAuth,
device-code flow, provider-owned PKCE/state/exchange/persistence, and generic
`session_action_callback` implementation and evidence. Reopen only the mobile
browser-login product surface and the UI-element split required by the new
decisions. No mobile implementation begins until the contract and remaining
native lifecycle decisions below are approved.

### Preserved completed baseline

- Terminal browser OAuth and same-host desktop/backend use the existing
  plugin-owned loopback listener and one complete foreground operation.
- Device code remains complete and independently usable.
- `chatgpt-auth-app` owns PKCE, OAuth state, attempt identity, token exchange,
  credential normalization/persistence, stale-write prevention, and
  start/status/cancel procedures.
- The applicable `session_action_callback` contract remains the sole generic
  external callback exposure boundary. Generic and MCP consumers remain
  element-addressed rather than bare-action-addressed.
- The Codex public client evidence remains unchanged: localhost ports `1455`
  and `1457` reached the pre-sign-in boundary; custom-scheme and investigated
  public HTTPS redirects were rejected.
- Raw embedded WebViews, public callback relays, pasted browser callbacks, and
  frontend token exchange remain excluded.

### Provider-neutral authentication UI contract

Introduce only one new provider-neutral UI element type, working name
`session_browser_auth`. Existing UI contracts are sufficient for device code;
do not introduce `session_device_code_auth` unless later implementation
evidence proves that an ordinary action-backed session element cannot satisfy
the requirements.

`session_browser_auth` is a dedicated browser workflow declaration. It binds:

- a start action and its static parameters/mappings;
- a status action, attempt-id mapping, pending/success/failure/cancelled/expired
  states, and bounded polling;
- an attempt-scoped cancel action;
- one existing applicable `session_action_callback` element;
- one UI-owned loopback receiver declaration;
- one platform system-authentication/browser presentation.

The receiver declaration is provider-neutral and includes:

```python
{
    "owner": "ui",
    "bind_host": "127.0.0.1",
    "advertised_host": "localhost",
    "ports": [1455, 1457],
    "path": "/auth/callback",
    "bind_before_start": True,
    "redirect_uri_param": "redirect_uri",
    "one_shot": True,
}
```

The UI must bind one accepted port before calling the start action, construct
the exact `http://localhost:<bound-port>/auth/callback` URI, and map that URI
into `login_start`. Start creates the plugin-owned PKCE/state attempt and
returns the authorization URL. The UI presents the URL through
`ASWebAuthenticationSession` on iOS or Chrome Custom Tabs on Android. The
one-shot receiver captures the complete callback URL as an opaque string and
forwards it to the declared callback element for the named connection and
session. The backend callback action validates state/attempt/expiry and owns
exchange and persistence.

UI cancellation invokes the attempt-scoped cancel action once and then closes
the browser surface and receiver. Start failure, browser presentation failure,
successful forwarding, backend failure, expiry, app teardown, and port setup
failure all close the receiver. A callback accepted after closure cannot
recreate or complete the attempt.

Device code remains a separate ordinary `session_action` bound to
`login_start` with `fixed_params: {"method": "device-code"}`. It uses existing
action result displays, notifications, follow-ups, status checks, and
cancellation actions. It has no loopback receiver or browser callback binding.
Frontends render the ordinary device-code action separately from the browser
orchestration element; neither presents a nested method selector.

The completed public terminal grammar is preserved exactly:

```text
crystal-lattice auth login codex --method browser|device-code
/login codex method=browser|device-code
```

This mobile UI split leaves the completed command grammar unchanged.

### Provider-neutral callback UI contract

Add `ui_type: "session_action_callback"` as the sole UI-schema declaration
that authorizes an external action deep link for a session. It is action-backed
and carries the established `plugin`, `id`, `action_id`, optional
`action_owner`, `fixed_params`, `param_map`, `condition`, `disabled`, and
`disabled_reason` fields. It is not a bare action definition and has no
implicit action-id exposure.

The deep-link route shape remains provider-neutral:

```text
crystal-lattice://action/<connection-id>/<session-id>/<callback-element-id>?...
crystal-lattice://action/<connection-id>/<session-id>/<plugin-id>/<callback-element-id>?...
```

The final segment is redefined as a callback UI element id. Plugin omission may
continue only when exactly one applicable `session_action_callback` with that
id exists; provider-generated OAuth links should include the plugin id. The
SDK parser should expose `callbackElementId`, not imply that the route names a
procedure.

The frontend routes the original URL and target identity through the generic
session callback invocation contract. The backend then:

1. Loads the authoritative target session and current effective UI schema.
2. Selects only `session_action_callback` elements matching the element id and
   optional plugin, evaluates `condition`, and rejects missing, ambiguous, or
   disabled elements before action execution.
3. Builds a callback context containing the full `redirect_url`, decoded query
   mapping, and route identity without automatically forwarding arbitrary
   query keys as action parameters.
4. Applies only the element's declared `fixed_params` and provider-neutral
   mappings such as `$callback.redirect_url` or `$callback.query.state`.
5. Validates the bound action and final inputs, then executes through the
   existing `execute_action_with_metadata(...)` boundary.

For Codex, the declaration is conceptually:

```python
{
    "ui_type": "session_action_callback",
    "id": "chatgpt_browser_oauth_callback",
    "label": "Complete ChatGPT browser login",
    "action_id": "complete_browser_login",
    "param_map": {"redirect_url": "$callback.redirect_url"},
    "condition": {...current OpenAI Responses/ChatGPT applicability...},
}
```

The browser-auth element references this callback element by plugin and
element id. The receiver and system browser never call
`complete_browser_login` as a bare procedure.

`session_action_callback` is excluded from session menus, toolbars, command
catalogs, and `/action` because those consumers enumerate their own explicit UI
types and do not include this type. Do not add `hidden`, `discoverable: false`,
or any other flag that turns a menu action into an implicit callback. The
generic callback plugin and MCP callback consumer must migrate to this
declaration so compatibility tests prove there is no raw-action fallback.

### Attempt and credential model

Represent both methods with one attempt record containing a generated
`login_id`, method, state, start/expiry times, cancellation signal, terminal
outcome, and method-owned cleanup handles. Browser-only private fields include
the PKCE verifier, expected OAuth state, and exact redirect URI. Terminal and
same-host flows may retain the existing plugin-owned listener handle. Mobile
instead keeps the receiver handle and opaque UI flow id in UI/native memory;
the embedded Python runtime does not own them. Device-only private fields
remain the current device auth id/code and polling interval.

Only the active pending attempt may exchange or commit. Cancellation marks the
attempt terminal before stopping workers/listeners. A callback must match the
active browser attempt, exact state, redirect mode, and expiry; the finalizer
atomically claims it before exchange so duplicate callbacks cannot race. A
cancelled, expired, replaced, already-consumed, wrong-method, wrong-target, or
wrong-state callback returns a safe error and cannot touch credentials.

Normalize a successful browser token response into the existing credential
keys and path. Extract account id/email/plan from reviewed token claims for
backend use, preserve refresh compatibility, and atomically replace the file
only after all validation succeeds. Do not place state, verifier, code, tokens,
or account identifiers in action status, browser response, errors, events,
logs, diagnostics, notifications, or frontend pending metadata. The complete
authorization URL remains the approved sole state-bearing display exception.

### Separate login elements and browser presentation

Remove method selection from visible action dialogs. Browser and device code
have separate labels, applicability, disabled reasons, commands, accessibility
identifiers, progress, cancellation, and acceptance evidence. Browser uses
`session_browser_auth`; device code uses an ordinary `session_action` with
fixed `method=device-code`. They may bind the same provider procedures, but
one UI element never asks the user to choose the other method.

The completed terminal command and slash grammar remains unchanged. Browser
commands continue to print a copyable URL and may best-effort open it with
`--no-open` support. Device-code commands never auto-open. Mobile browser
presentation is native and platform-specific:

- iOS: `ASWebAuthenticationSession` is the first attempted surface.
- Android: Chrome Custom Tabs is the first attempted surface.

These are system authentication/browser surfaces, not raw embedded WebViews.
An `openAuth` helper that waits for a custom scheme or public HTTPS callback
does not solve this provider constraint because those redirects were rejected.
The primary surfaces are used with the accepted localhost redirect and the
UI-owned receiver.

### Frontend routing

Keep callback forwarding provider-neutral and opaque. The UI flow record,
stored only in bounded memory, contains an opaque flow id, named connection,
session, callback plugin/element, bound listener address, expiry, and
cancellation handle. It never stores parsed code/state/token values.

After the local receiver accepts one request:

1. Stop accepting additional callbacks and preserve the complete URL only in
   the live forwarding operation.
2. Invoke the applicable callback element against the named backend/session;
   never substitute the focused connection.
3. If a bridge disconnects, retain the opaque callback only in bounded memory
   until reconnect or expiry. Process death loses it and the flow fails safely;
   no callback secret is persisted for recovery.
4. Render only the backend's safe terminal result and retire the flow.
5. Close the receiver and browser session on every terminal outcome.

For Android, the local completion response should return from the Custom Tab
to Crystal Lattice using an app deep link containing only the opaque flow id,
for example `crystal-lattice://auth-return/<flow-id>`. Code, state, callback
URL, access token, and refresh token never enter that app link. The flow id
resolves only an in-memory record and is useless after completion/expiry.

For iOS, investigate whether `ASWebAuthenticationSession` can finish from the
localhost response directly or requires the same secret-free flow-id return.
Do not assume either behavior; record simulator and physical-device evidence.

### Mobile system-browser and listener investigation

Build the first deterministic native harness around a UI/native-owned one-shot
receiver, not embedded Python:

1. Bind `127.0.0.1:1455`; fall back to `:1457`; fail visibly if both are busy.
2. Advertise `localhost` and `/auth/callback` exactly.
3. Start a local deterministic OAuth fixture that can emulate normal,
   delayed-MFA, denial, malformed, duplicate, and late callbacks.
4. Bind before invoking the plugin start action and assert the chosen redirect
   URI is mapped into `login_start`.
5. Present through `ASWebAuthenticationSession` or Custom Tabs.
6. Capture and forward the callback URL opaquely to the applicable backend
   callback element.
7. Return to the app, display only safe status, and release all native/JS
   resources.

The initial implementation plan must not call iOS
`beginBackgroundTask`, declare a new iOS background mode, or add an Android
service. Tests first verify the premise that the system auth/browser session
and UI/native listener remain viable. A failure caused by suspension,
termination, or browser-surface behavior is decisive only when reproduced on a
physical device with timestamps and lifecycle evidence.

### Ordered implementation

1. Approve the exact `session_browser_auth` schema, nested receiver contract,
   native receiver API, and process-death semantics. The existing CLI/slash
   grammar is fixed and is not an approval question.
2. Add generic validation and discovery only for
   `session_browser_auth`. Validate every start/status/cancel/callback binding
   before start and prove it is excluded from `/action` by explicit UI-type
   semantics.
3. Update `chatgpt-auth-app` UI declarations to contribute one browser
   orchestration element and one separate ordinary device-code
   `session_action` with fixed `method=device-code`. Preserve completed
   procedures, credentials, terminal grammar/behavior, and
   `session_action_callback`.
4. Add an iOS test-native one-shot receiver and
   `ASWebAuthenticationSession` harness. Do not use embedded Python or request
   background time.
5. Run iOS simulator evidence, then physical-device evidence for the complete
   scenario matrix. If the primary path fails, classify the cause before
   changing architecture.
6. Only after recorded `ASWebAuthenticationSession` failure attributable to
   the browser surface, investigate `SFSafariViewController`. If failure is
   listener suspension/lifecycle instead, stop for a lifecycle decision rather
   than switching browser surfaces.
7. Add an Android test-native one-shot receiver, Chrome Custom Tabs harness,
   and secret-free opaque-flow-id completion response. Do not add a service.
8. Run Android emulator evidence, then physical-device evidence for the
   complete scenario matrix. If Custom Tabs cannot preserve the listener,
   record that failure and stop before considering a service/background
   mechanism.
9. Verify callback forwarding through direct and bridge-backed named
   connections using the production callback-element adapter, with disconnect,
   reconnect, expiry, and process-death behavior.
10. If either platform's native listener remains inconclusive or fails, retain
    device code and request approval for the next ordered fallback. Investigate
    embedded-Python ownership only after native approaches fail and evidence
    shows it is uniquely necessary.
11. Update maintained docs and requirement evidence only for behavior that was
    implemented and physically verified. Keep target-only browser claims
    marked not implemented until then.
12. Real OpenAI acceptance remains separately gated; deterministic fixtures
    precede any request for hosted sign-in approval.

### Human-assisted hosted-acceptance checkpoints

These checkpoints define later acceptance behavior and do not authorize it in
the capability-probe turn.

- Terminal loopback acceptance must run where the browser is on the same host
  as the plugin-owned loopback listener. A human completes provider sign-in,
  consent, and MFA when requested. The provider returns automatically to the
  loopback callback, and the command completes without any pasted redirect URL
  or authorization code.
- Mobile hosted browser acceptance remains incomplete. It requires the
  physically verified UI-owned localhost flow described above, human
  sign-in/consent/MFA in the primary system browser surface, automatic
  localhost callback, opaque callback-element forwarding, safe app return, and
  backend-owned exchange/storage. A custom/HTTPS redirect or `openAuth`
  callback is not an acceptance substitute.

### Implementation decisions and open questions

- Fixed: terminal/same-host browser OAuth, device code, provider-owned
  PKCE/state/exchange/persistence, and the applicable
  `session_action_callback` remain completed.
- Fixed: the mobile listener is UI/native-owned. Embedded Python is excluded
  unless later native failure evidence proves it uniquely necessary.
- Fixed: the primary surfaces are `ASWebAuthenticationSession` and Chrome
  Custom Tabs. A raw embedded WebView and public relay remain out of scope.
- Fixed: no iOS background task or Android service is added initially.
- Fixed: browser and device code are separate UI elements. Only browser gets a
  new orchestration type; device code remains an ordinary action-backed
  `session_action` with fixed `method=device-code`.
- Fixed: preserve the public terminal grammar exactly as
  `crystal-lattice auth login codex --method browser|device-code` and
  `/login codex method=browser|device-code`.
- Fixed: mobile browser uses localhost `1455`/`1457` and `/auth/callback`;
  rejected custom/HTTPS redirect handling is not retried under another helper.
- Fixed: Android app return carries only an opaque flow id. No OAuth callback
  secret enters an app deep link.
- Fixed: device code remains available before, during, and after browser
  investigation.
- Open: should the receiver contract live directly on
  `session_browser_auth` or in a reusable nested capability object?
  - Recommendation: keep one `session_browser_auth` type with a nested
    `loopback_receiver` object. Do not add a second auth orchestration type
    unless ordinary device-code action evidence later proves insufficient.
- Open: should iOS set `prefersEphemeralWebBrowserSession`?
  - Recommendation: default to the ordinary shared authentication session so
    account/MFA behavior matches user expectations; test ephemeral mode only
    if provider/session behavior requires it.
- Open: which native listener primitive should own the one-shot HTTP receiver?
  - Recommendation: choose the smallest maintained platform-native primitive
    that can bind loopback, reject non-loopback traffic, enforce one request,
    and expose explicit close/cancel; do not introduce a general embedded web
    server.
- Open: how should process death be presented when callback secrets cannot be
  persisted?
  - Recommendation: fail the browser attempt safely, retire the opaque flow
    id, and offer restart plus device code. Do not persist callback URLs.
- Open: how long may an opaque callback remain in memory while a bridge
  reconnects?
  - Recommendation: never beyond the provider attempt expiry, with one bounded
    item per flow and explicit cancellation on connection removal.
- Open: can `ASWebAuthenticationSession` close directly after the localhost
  response, or must the response issue a secret-free flow-id app return?
  - Recommendation: test direct completion first; use the same opaque flow-id
    return pattern as Android only if physical-device evidence requires it.
- Open: what failure threshold unlocks a fallback?
  - Recommendation: require reproducible physical-device failure with native
    timestamps, lifecycle state, listener state, and a passing deterministic
    control before opening the next fallback gate.
- Remaining hosted acceptance work: verify reload and refresh from the
  isolated browser credential and make the approved minimal model request.
  Human browser sign-in and the existing device-code flow have been confirmed.

### Documentation

- Preserve maintained terminal, same-host desktop, callback-element,
  credential, and device-code documentation.
- Update plugin-author UI docs with the single new
  `session_browser_auth` schema, bind-before-start receiver contract,
  callback-element reference, opaque forwarding, fallback gates, and the
  separate ordinary device-code `session_action` pattern.
- Document mobile browser login as target-only until physical-device evidence
  passes. Clearly distinguish `ASWebAuthenticationSession` and Custom Tabs
  from raw WebViews.
- Document that `openAuth`-style custom/HTTPS callbacks remain unsuitable for
  this provider and that localhost is the actual OAuth redirect.
- Document the Android secret-free opaque-flow-id app return and the
  no-persistence/process-death behavior.
- Document platform evidence and any opened fallback gate alongside the code
  that makes it true; do not publish aspirational browser support as current.

### Task checklist

- [x] Verify the required workspace and Git root.
- [x] Reassess the clean repository at `3cb26fc7`, the completed dependency,
  current ChatGPT/OpenAI Responses contracts, reference implementations, and
  mobile/desktop routing state.
- [x] Obtain approval for every material decision and requirement conflict
  listed above.
- [x] Obtain the distinct limited capability-probe approval.
- [x] Perform only the reviewed pre-sign-in capability requests and record
  redacted classifications.
- [x] Add the approved applicable callback UI contract and migrate existing
  generic callback consumers without a raw-action fallback.
- [x] Complete and record the bounded mobile-local loopback feasibility
  checkpoint without productizing an inconclusive native lifecycle design.
- [x] Define the unified private attempt model and safe public status shape.
- [x] Add browser PKCE, authorization, callback validation, token exchange,
  credential normalization, and lifecycle cleanup.
- [x] Preserve and regression-test the existing device-code flow.
- [x] Add approved method selection and method-conditional browser
  presentation to the existing complete command/action flow.
- [x] Bind browser completion through the applicable callback UI element and
  add approved generic callback routing while keeping production mobile on
  device code.
- [x] Add decisive protocol, command, frontend, lifecycle, security,
  credential-consumer, and refresh evidence.
- [x] Update maintained documentation.
- [ ] Approve the materially amended `session_browser_auth` receiver contract,
  listener primitive criteria, process-death semantics, and failure thresholds.
- [ ] Split mobile presentation into one browser orchestration element and one
  ordinary device-code `session_action` with fixed `method=device-code`,
  without changing completed CLI/slash grammar or behavior.
- [ ] Build and verify the iOS `ASWebAuthenticationSession` plus UI-owned
  one-shot localhost harness without background execution time.
- [ ] Run the full iOS simulator and physical-device lifecycle/security matrix;
  open the `SFSafariViewController` gate only after qualifying primary failure.
- [ ] Build and verify the Android Custom Tabs plus UI-owned one-shot localhost
  harness with secret-free opaque-flow-id app return and no service.
- [ ] Run the full Android emulator and physical-device lifecycle/security
  matrix; open the service/background gate only after qualifying primary
  failure.
- [ ] Verify direct and bridge callback forwarding, disconnect/reconnect,
  process-death failure, secret non-persistence, and app return on production
  adapters.
- [ ] Update maintained mobile/plugin UI documentation only for physically
  verified current behavior.
- [x] Obtain separate real-acceptance approval and complete the human browser
  sign-in; retain the user's confirmation that the existing device-code flow
  still works.
- [ ] Complete isolated credential reload, refresh, and model-request
  acceptance.
- [x] Record deterministic requirement evidence before marking non-hosted
  requirements complete.

### Requirement verification

- Device-code preservation and selection: run the existing deterministic
  device-code package tests plus public CLI subprocess and interactive PTY
  flows selecting `device-code`; assert the same endpoints, polling,
  credential keys, cancellation, and final status.
- Browser protocol and credential compatibility: use a real local HTTP OAuth
  fixture through the public `crystal-lattice auth login codex` process,
  deliver the callback over the actual loopback socket, inspect the saved
  credential contract, force a refresh through the OpenAI Responses refresh
  helper, and execute a provider request through the production
  ChatGPT-authenticated adapter. The hosted equivalent remains manual,
  separately approved evidence.
- Complete command architecture: a CLI subprocess and production interactive
  slash dispatcher each select browser login, expose the URL, stay active
  through callback, and return one terminal result without user-issued status
  commands. PTY interruption must cancel exactly that attempt and restore the
  interactive prompt.
- Loopback ownership: parameterized tests cover success, provider denial,
  malformed callback, wrong state/path/method/host, timeout, cancellation,
  token-exchange failure, port conflict, plugin close, and start failure. Each
  case proves the listener is closed and a later attempt can bind and finish.
- Frontend callback routing: generic/MCP mobile and desktop real-backend
  integrations must deliver an OS-style callback to the production generic
  router, cross `RestAgentBackend` and the public HTTP callback-element
  invocation path, and re-resolve the applicable
  `session_action_callback`. Codex browser acceptance is not inferred from
  those tests; same-host desktop Codex uses the plugin loopback listener and
  production mobile uses device code.
- Callback exposure boundary: generic callback and MCP production-path tests
  prove callback links target UI element ids, only declared callback mappings
  become action inputs, conditions/disabled state are authoritative at
  invocation, omitted-plugin ambiguity is rejected, and bare or inapplicable
  action ids cannot execute. Inventory tests prove callback elements are
  absent from session menus, command catalogs, and `/action`.
- Separate auth elements: schema, inventory, component, and native UI tests
  prove browser orchestration and the ordinary device-code action are
  independent applicable elements with separate labels, accessibility ids,
  bindings, disabled states, cancellation, and no nested method selector.
  Inventory tests prove only browser introduces a new UI type and device code
  remains `session_action` with fixed `method=device-code`.
- Terminal compatibility: public subprocess and interactive tests preserve
  exactly `crystal-lattice auth login codex --method browser|device-code` and
  `/login codex method=browser|device-code`; the mobile split adds no alternate
  command grammar.
- iOS primary path: simulator and physical-device tests use the production
  `ASWebAuthenticationSession` adapter and UI-owned receiver. Evidence covers
  normal completion, provider denial, MFA delays long enough to exercise
  backgrounding, user cancellation, Home/background/foreground transitions,
  screen lock/unlock, interruption by another auth session, app process
  termination/relaunch, port `1455` conflict with `1457` fallback, both ports
  unavailable, duplicate/late callbacks, and return to the app.
- Android primary path: emulator and physical-device tests use production
  Custom Tabs and the UI-owned receiver. Run the same lifecycle matrix plus
  back-button/tab dismissal, activity recreation, task switching, and the
  local completion response that deep-links back with only an opaque flow id.
- Callback forwarding: direct and real bridge-backed tests route the opaque
  callback URL to the named connection/session/callback element. Cover bridge
  disconnect before callback, callback while disconnected, reconnect before
  expiry, expiry before reconnect, connection removal, duplicate delivery, and
  wrong-connection rejection.
- Secret non-persistence: canary code/state/token/callback values are absent
  from app deep links, intents, universal-link state, AsyncStorage, UserDefaults,
  Android preferences/saved state, logs, diagnostics, analytics, crash
  breadcrumbs, notifications, screenshots/accessibility labels, and persisted
  pending-flow records. Native memory is released on every terminal outcome.
- Lifecycle premise: tests explicitly report whether the listener remained
  reachable without iOS background time or an Android service. Simulator or
  emulator success alone is insufficient. A physical-device failure with a
  passing foreground control and native timestamps is required to falsify the
  premise and unlock a fallback gate.
- Sensitive-data boundary: seeded canaries for state, verifier, code, access
  token, refresh token, account id, and account email must be absent from
  captured terminal output other than the approved complete authorization-URL
  exception, action displays after callback, browser response bodies, events,
  notifications, frontend pending state diagnostics, server/plugin logs, and
  raised errors.
- Stale-write protection: concurrency tests deliver duplicate callbacks,
  callback-after-cancel, callback-after-expiry, device callback against browser
  attempt, browser callback against device attempt, and old callback after a
  cancel/new start. Assert that only the active one-shot attempt writes the
  credential file and that an existing valid credential remains intact after
  every rejected callback.

### Additional implementation verification

- Run `pytest plugins/chatgpt-auth-app/tests -q` with manual tests explicitly
  deselected, focused OpenAI Responses credential/refresh/provider tests, the
  core command/action tests, and the application terminal/HTTP tests.
- Run frontend SDK, shared React/component, mobile, and desktop tests whenever
  their contracts change. Run the existing real-backend deep-link suites and
  the new Codex-specific production-path integrations; do not count a skipped
  gated test as success.
- Run focused native URL-routing verification on every platform documented as
  supported. Record unsupported platforms explicitly instead of inferring
  support from JavaScript tests.
- Run Ruff and Black checks for changed Python files, relevant TypeScript
  typechecks/lint, `pyright` for touched public Python contracts, and
  `git diff --check`. Distinguish any pre-existing baseline failure from new
  diagnostics.
- Inspect attempt state and shutdown paths for retained listener/thread
  references, plaintext callback persistence, unbounded pending queues,
  duplicate credential writers, and browser-opening branches outside the
  generic terminal/frontend presentation layers.
- Inspect native dependency and binary configuration to prove the first
  implementation adds neither an iOS background mode/background-task request
  nor an Android service/foreground-service permission.
- Prove the primary adapters use `ASWebAuthenticationSession` and Custom Tabs,
  not a raw embedded WebView. Treat an `openAuth` helper as acceptable only if
  it is a thin adapter over the required system surface and still uses the
  localhost receiver rather than a rejected custom/HTTPS OAuth redirect.
- Keep a fallback decision record per platform containing the failing
  production scenario, physical device/OS, timestamps, listener/browser/app
  lifecycle state, deterministic control result, and why the next fallback
  addresses that exact failure. No evidence record means no fallback work.

## Implementation Notes

- 2026-10-19: Completed only the approved limited pre-sign-in capability
  probe. Each candidate used fresh in-memory OAuth state and PKCE
  verifier/challenge values, an independently constructed HTTP client with no
  cookie jar, credentials, or ambient proxy, and the minimal pi-compatible
  authorize parameters. Redirect following was disabled. The local
  `/Users/ferenci84/Dev/Mine/pi` checkout remained a read-only reference.
- `http://localhost:1455/auth/callback` — apparent pre-sign-in acceptance. The
  authorize request returned HTTP 302 to the redacted
  `https://auth.openai.com/log-in` path. This shows that the candidate reached
  the sign-in boundary without an explicit redirect rejection; it does not
  prove human sign-in, callback delivery, code exchange, or credential use.
- `http://localhost:1457/auth/callback` — apparent pre-sign-in acceptance. The
  authorize request returned HTTP 302 to the same redacted OpenAI `/log-in`
  path, with the same limitations as port `1455`.
- `crystal-lattice://oauth/callback` — explicit pre-sign-in rejection. Repeated
  fresh isolated requests returned HTTP 400 JSON with non-secret classification
  `invalid_request_error` / `invalid_authorize_request` and no redirect. No
  custom-scheme browser acceptance may be claimed from this candidate.
- Follow-up pre-sign-in evidence recorded after the HTTPS/AWS investigation:
  the provider-owned
  `https://auth.openai.com/deviceauth/callback` reached the accepted
  pre-sign-in boundary, while
  `https://crystal-bridge.dynamicprogrammingsolutions.com/oauth/callback`
  returned `invalid_authorize_request`. This rejects the investigated public
  bridge callback candidate and does not authorize a relay.
- Read-only AWS inspection found the live bridge host on the Ireland EC2
  server. Its `/health` route returned HTTP 200 and its current
  `/oauth/callback` route returned HTTP 404. No DNS, AWS, EC2, bridge service,
  deployment, server, or other infrastructure state was changed.
- The approved product scope is therefore loopback browser OAuth for terminal
  and same-host desktop/backend arrangements, with device code retained for
  production mobile, remote, and headless use. Do not claim mobile browser
  acceptance, add a raw embedded WebView, or add a public callback relay.
- The probe did not open a browser, authenticate, request consent or MFA,
  receive an authorization code, contact the token endpoint, write or read
  credentials, test refresh, or make a model request. Only the redacted
  classifications, HTTP status classes, and redacted response location/error
  categories above were retained.
- 2026-10-19: Implemented the approved non-hosted product scope. The ChatGPT
  auth plugin now shares one attempt lifecycle across browser and device-code
  methods, generates PKCE/state, binds strict loopback callbacks on `1455`
  then `1457`, validates host/path/state and one-shot ownership, performs
  form-encoded exchange, normalizes the existing refresh-compatible credential
  file, and closes workers/listeners on success, failure, cancellation,
  expiry, and application close. No hosted OpenAI flow had been executed at
  the time of this implementation checkpoint.
- Command and action adoption now provides `browser` / `device-code`
  selection, browser-only conditional opening, `--no-open`, complete
  CLI/slash foreground waiting, and a device-code default on visible session
  actions. The embedded iOS runtime sets `browser_login_enabled: false`, so
  production mobile exposes device code only.
- Added the provider-neutral `session_action_callback` boundary. Deep links
  target applicable callback element ids; the backend reloads authoritative
  session UI, enforces condition/disabled state, maps only declared
  `$callback.*` fields, and executes through the existing action boundary.
  Frontends route the original callback as an opaque URL. Generic callback and
  MCP consumers were migrated with no bare action-id fallback.
- Mobile-local loopback feasibility remains inconclusive and was not
  productized. Foreground-only deterministic harnesses proved that both
  `127.0.0.1:1455` and `:1457` can bind, capture one opaque callback in memory,
  and clean up. Existing production routing proves callback-element forwarding
  over generic HTTP paths, including bridge transports. However, iOS provides
  only the existing finite background task tied to an active embedded request,
  has no durable OAuth-listener background mode, and explicitly does not
  guarantee background duration. Android has no embedded listener/service
  counterpart. Existing native tests prove only a short bounded background
  tool request, not external-browser sign-in/MFA survival or a secret-free
  automatic return. A production mobile listener therefore requires a later
  material lifecycle decision; device code remains the supported mobile path.
- Maintained docs now distinguish same-host browser login from production
  mobile/remote/headless device code, document callback-element authorization
  and opaque frontend routing, and explicitly exclude a raw WebView and public
  callback relay.
- Deterministic verification passed:
  - ChatGPT auth package excluding manual integration: 23 passed, 2 deselected.
  - Combined core application-plugin plus application callback/terminal slice:
    59 passed.
  - OpenAI Responses ChatGPT auth and refresh recovery: 16 passed.
  - Generic callback and MCP runtime plugin packages: 24 passed.
  - Embedded mobile runtime/configuration slice: 16 passed, 9 deselected.
  - Frontend SDK parser/router/backend units: 15 passed.
  - Frontend SDK generic callback real-backend integration: 1 passed across
    the public HTTP callback-element route.
  - Ruff, targeted Black checks for plugin/test/server files, Python
    compilation, JSON parsing, and `git diff --check` passed. The large
    pre-existing core/terminal modules retain their existing formatting to
    avoid unrelated churn.
- Supplementary MCP real-backend verification reached backend startup after
  increasing its dynamic-install budget, completed one token exchange in each
  test, and then failed the unchanged downstream reconnect assertion because
  no MCP Authorization header was observed. The callback-element and existing
  manual-form paths failed identically after the hermetic environment resolved
  the latest unpinned MCP dependency, while the owning 20-test MCP Python suite
  passed. This is recorded as incomplete environment/dependency evidence, not
  weakened into a passing test.
- Mobile Jest and TypeScript commands could not run because this worktree has
  no local `jest` or `tsc` executable. Frontend SDK Vitest was run using the
  sibling dependency tree only as a module resolver; no dependencies or
  lockfiles were installed or changed in this worktree.
- Targeted Pyright still reports the repository's established strict-typing
  and duplicate-route baseline across the large application modules. The new
  callback endpoint's redirect input was narrowed explicitly; Ruff and runtime
  tests are green.
- 2026-10-19: The separately approved human-assisted browser flow completed
  successfully against OpenAI in an isolated local config. The resulting
  credential file was present with owner-only permissions and the expected
  credential-field contract; no secret values were printed or recorded. The
  user also confirmed the existing device-code flow still works as before.
  Credential reload, refresh, and the minimal model request remain incomplete.
- 2026-10-19: Mobile browser login was reopened for planning. The prior
  foreground-only listener result remains valid evidence but no longer closes
  the requirement. The next investigation uses a UI/native-owned one-shot
  listener with `ASWebAuthenticationSession` and Chrome Custom Tabs as the
  mandatory primary surfaces.
- The revised plan deliberately requests no initial iOS background execution
  and adds no Android service. Physical lifecycle tests must verify or falsify
  the premise that the system auth/browser surface keeps the flow viable.
- Browser and device-code presentation must be split into separate applicable
  UI elements. The existing callback-element, provider-owned OAuth protocol,
  completed terminal/same-host behavior, and device-code evidence remain
  preserved.
- The split is intentionally minimal: add only `session_browser_auth`; keep
  device code as an ordinary action-backed `session_action` with fixed
  `method=device-code`. Preserve the implemented CLI/slash `--method` /
  `method=` grammar exactly.
- Android completion may return to Crystal Lattice only with an opaque,
  in-memory flow id. No callback URL, code, state, or token may appear in that
  app deep link.
- No product code, test, maintained documentation, native configuration, or
  runtime state was changed as part of this planning revision.
