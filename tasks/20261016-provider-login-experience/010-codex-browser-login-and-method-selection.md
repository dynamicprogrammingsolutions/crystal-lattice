# Codex Browser Login And Method Selection

Add a production-ready Codex browser OAuth path alongside the existing
device-code flow, using one complete contributed terminal login operation and
the existing provider action/credential architecture.

## Requirements checklist

- [ ] Existing Codex device-code login remains supported and selectable.
- [ ] Codex browser OAuth performs PKCE authorization, callback validation,
  token exchange, refresh-compatible persistence, and account metadata
  extraction without changing the credential format consumed by OpenAI
  Responses.
- [ ] A top-level contributed command can start one complete Codex login flow,
  present or open the authorization URL, report progress, wait for callback,
  and finish with a terminal result.
- [ ] The interactive terminal can invoke the same complete flow through a
  contributed slash command.
- [ ] When provider policy permits, terminal browser login uses a temporary
  loopback callback server owned by the auth plugin and closes it after
  success, failure, cancellation, or expiry.
- [ ] Mobile and desktop start and complete browser login through plugin
  actions and generic deep-link routing rather than running an OAuth server or
  exchanging tokens in frontend code.
- [ ] Users can select among the supported Codex login methods through
  standard action dialog controls or command arguments.
- [ ] Callback state, PKCE verifier, authorization code, access token, refresh
  token, and account identifiers remain out of ordinary displays and logs.
- [ ] Stale, duplicate, expired, cancelled, and superseded callbacks cannot
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
2. Treat only redirects demonstrated by the approved capability probe as
   supported. Prefer direct loopback for terminals and a direct
   custom/universal app redirect only if the provider accepts it.
3. Do not add an HTTPS callback relay in this task. If app redirects are
   rejected, retain device code for unsupported remote frontend/backend
   arrangements and return for a product decision.
4. Omit manual browser callback/code entry. Device code is the remote/headless
   fallback, preserving the approved bounded foreground command contract.
5. Use public method values `browser` and `device-code`, default user-facing
   command/dialog flows to browser, and preserve device code for an omitted
   raw-action method during the compatibility window.
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
- Codex currently requests additional connector scopes. pi does not. Neither
  local source checkout proves which scopes and redirect variants the live
  provider currently accepts for Crystal Lattice.
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

Implement browser OAuth as another method of the existing ChatGPT auth action
and foreground contract after recording the approved capability probe.
Keep protocol work, attempts, callback validation, token exchange, credential
persistence, and listener cleanup in `chatgpt-auth-app`; keep the command and
frontend layers provider-neutral. Real hosted sign-in/model acceptance remains
separately gated even though this execution plan is approved.

### Proposed architecture

Use one action family:

- `login_start(method, callback context...)` starts either device code or
  browser OAuth and returns the existing safe `auth_status` envelope.
- `check_status(login_id)` and `cancel_login(login_id)` remain the only
  foreground continuation actions.
- `complete_browser_login(redirect_url)` remains an ordinary callable
  procedure in `get_actions`; it gains external callback exposure only through
  an applicable `session_action_callback` UI element. That UI element and the
  loopback listener reach the same private attempt finalizer.
- `logout` remains independent.

The public CLI and slash command remain one complete foreground operation.
Method selection is command/action input, not another command route and not a
sequence of status commands. The existing generic foreground controller
starts once, renders the initial result, optionally opens the URL under the
approved browser policy, polls status, maps interruption to attempt-scoped
cancellation, and exits only on a terminal state.

For terminal browser login, the plugin generates state and PKCE, binds the
accepted loopback listener before exposing the authorization URL, and records
the exact redirect URI used for exchange. The listener accepts only the
callback path and expected method/host/port, validates provider error or
constant-time state match, consumes one authorization code, exchanges it, and
closes on success, failure, cancellation, expiry, plugin close, or start
failure. It must not send a cancellation request to an unknown process
occupying a preferred port. If no provider-accepted port is available, the
attempt fails safely and recommends device code.

For app browser login, the session action supplies generic connection and
session context. If and only if the provider accepts a custom/universal
redirect, the plugin constructs an explicit
`chatgpt_auth.chatgpt_browser_oauth_callback` callback-element link. The OS
returns that link to the frontend; a generic router resolves the named
connection and session and asks the backend to invoke that applicable callback
element. The frontend never sees the verifier, exchanges a token, or persists
credentials. If an HTTPS relay is required, stop and create an approved
security/deployment design before implementing it.

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
the PKCE verifier, expected OAuth state, exact redirect URI, and listener
handle. Device-only private fields remain the current device auth id/code and
polling interval.

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
logs, diagnostics, notifications, or frontend pending metadata. The
authorization URL exception remains subject to approval because it necessarily
embeds state.

### Method selection and browser presentation

Subject to approval, expose:

```text
crystal-lattice auth login codex [--method browser|device-code] [--no-open]
/login codex [method=browser|device-code] [--no-open]
```

Use the same select input in the standard session action dialog. The proposed
user-facing default is browser, matching pi/Codex, while an omitted `method` on
the raw action retains device code for compatibility with existing action
callers. Device code remains selectable everywhere it is currently supported.

Always render a copyable browser authorization URL. Adopt the dependency's
approved best-effort auto-open behavior only for a local interactive browser
method and preserve `--no-open`; device-code URLs never auto-open. Because
browser metadata is currently static, implement and document the smallest
approved generic conditional extension. Browser-open failure remains
non-terminal because the printed URL is authoritative.

### Frontend routing

Keep parsing and execution generic. Move or generalize the mobile-local action
link handler into the frontend SDK so mobile and desktop share callback-element
parsing, target routing, and response handling. The frontend must invoke the
callback-element endpoint/request shape rather than
`executeSessionAction(actionId)`. Register the existing custom scheme in
desktop native configuration and bridge cold-start and live URL events into
the production root.

Route against the named connection and session, never the currently focused
connection by substitution. Execute immediately when that named backend is
open. Under the proposed policy, retain a bounded, memory-only pending callback
for a known but closed connection, prompt the user to open it, expire it with
the provider attempt, and never navigate or focus automatically. Unknown
connections fail without dispatch. Do not write callback URLs or codes to
saved connection state, debug timelines, analytics, crash breadcrumbs, or
ordinary alerts.

Present the safe callback action result through each frontend's existing
action-display machinery. Refresh affected action/auth state without embedding
Codex-specific logic in React Native. Add stable test identifiers only to
production controls used by native verification.

### Ordered implementation

1. After receiving capability-probe approval, issue only the reviewed
   pre-sign-in authorize requests needed to observe redirect/scope validation.
   Record accepted/rejected loopback hosts/ports, custom app URI, and universal
   link behavior, plus anything the provider does not reveal before sign-in.
   Do not authenticate, receive a callback code, exchange tokens, write
   credentials, test refresh, or make a model request under this approval.
2. Resolve all redirect, default-method, manual fallback, browser condition,
   pending callback, and security questions. If cross-device app redirect is
   impossible without a relay, return for the approved product decision
   instead of implementing a relay or weakening the frontend requirement.
3. Add and validate the provider-neutral `session_action_callback` element,
   callback context mappings, authoritative applicable-element resolution, and
   generic frontend/backend invocation path. Migrate the generic callback and
   MCP consumers; prove bare action ids are no longer deep-link callable and
   that the new type stays out of ordinary menus and `/action`.
4. Refactor `chatgpt-auth-app` attempt handling just enough to share lifecycle,
   active-attempt guards, cleanup, normalization, persistence, and safe status
   rendering across device and browser methods. Preserve current device
   endpoint and polling behavior.
5. Add PKCE generation, authorization URL construction, strict callback
   parsing, form-encoded token exchange, account metadata extraction, and
   attempt-scoped loopback handling. Add `close(state)` cleanup.
6. Bind the browser completion procedure to the applicable callback UI element,
   add method input, and update the existing CLI, slash, and visible
   session-action elements. Extend generic browser metadata only for the
   approved method-conditional opening behavior.
7. Implement the approved generic mobile/desktop routing and pending behavior,
   including desktop native URL delivery, without frontend token logic or
   implicit navigation.
8. Add deterministic protocol, lifecycle, command, HTTP/backend, frontend,
   native routing, credential-consumer, refresh, and redaction evidence.
9. Update maintained user/developer documentation only for behavior that is
   implemented and verified.
10. Only after separate real-acceptance approval, run browser and device-code
    sign-ins, exercise live token/refresh behavior, and make one OpenAI
    Responses request. Remove isolated credentials and record non-secret
    evidence. Capability-probe approval does not authorize this step.

### Human-assisted hosted-acceptance checkpoints

These checkpoints define later acceptance behavior and do not authorize it in
the capability-probe turn.

- Terminal loopback acceptance must run where the browser is on the same host
  as the plugin-owned loopback listener. A human completes provider sign-in,
  consent, and MFA when requested. The provider returns automatically to the
  loopback callback, and the command completes without any pasted redirect URL
  or authorization code.
- Mobile hosted browser acceptance is conditional on the provider accepting a
  Crystal Lattice custom or universal redirect. A human starts browser login
  from the production session action and completes provider sign-in, consent,
  and MFA. The OS reopens the app; generic routing selects the named
  connection, session, and `session_action_callback` element; the backend owns
  callback validation, token exchange, and credential storage.
- If the provider rejects the app redirect, do not claim mobile browser
  acceptance and do not add a callback relay. Keep device code available,
  record the unsupported browser arrangement, and return for a product
  decision.

### Implementation decisions and open questions

- Approved: browser and device code are methods of one provider auth
  plugin, use one complete action-backed foreground operation, and produce the
  existing OpenAI Responses credential format.
- Approved: protocol logic, callback listeners, PKCE, state, token
  exchange, refresh-compatible persistence, cancellation, and cleanup remain
  provider-plugin responsibilities. Terminal and frontend adapters execute
  actions and render results only.
- Approved: actions remain callable procedures; external callback
  invocation is authorized only by a currently applicable action-backed UI
  element and uses the existing action execution boundary.
- Approved: terminal interruption requests attempt-scoped
  cancellation with bounded cleanup; standalone exits 130 and interactive
  terminal restores the prompt. Ordinary prompt entry is unavailable while
  the foreground slash command is active.
- Approved: use minimal pi-compatible browser scopes/flags initially and
  finalize redirect support from the bounded capability evidence. Connector
  scopes require evidence that they are necessary.
- Approved: no callback relay or manual pasted callback. Device code remains
  the unsupported-remote/headless fallback, and rejected app redirects return
  for a product decision.
- Approved: public method names/defaults, raw-action compatibility behavior,
  and the provider-neutral method condition for browser opening described
  above.
- Approved: the `session_action_callback` contract, element-id route
  semantics, explicit callback mappings, and removal of raw action-id
  deep-link invocation.
- Approved: one-shot callback claiming and the proposed
  no-auto-supersede behavior: a repeated start returns the current pending
  attempt, while cancel-then-start makes the prior callback stale.
- Approved: generic frontend target/pending semantics, including
  memory-only bounded retention, no implicit connection opening, and no focus
  or navigation changes.
- Approved: authorization URL as the sole state-bearing display
  exception and omission of account id/email from ordinary results.
- Approved for this turn: the limited pre-sign-in capability probe using the
  three reviewed redirect candidates and no credentials.
- Still separately gated: human-assisted browser/device sign-ins,
  token/refresh verification, credential writes, and the subsequent model
  request.

### Documentation

- Update `plugins/chatgpt-auth-app/README.md` with supported methods, exact
  command/action syntax, defaults, loopback/app redirect limitations,
  cancellation, expiry, port conflicts, browser-open behavior, and any approved
  manual fallback.
- Update the terminal guide for method arguments, `--no-open`, foreground
  waiting, Ctrl-C, and safe failure behavior. Update command/UI-element docs
  only if the generic browser metadata contract changes.
- Update UI-element, action, HTTP, and frontend SDK deep-link documentation
  with `session_action_callback`, element-id routing, callback mappings,
  applicability/disabled checks, explicit menu and `/action` exclusion,
  target validation, pending lifetime, no-navigation behavior, and sensitive
  callback handling.
- Update mobile and desktop user/development docs for supported incoming-link
  behavior and platform registration. Do not describe a relay or redirect mode
  that was not provider-verified and delivered.
- Preserve the OpenAI Responses credential/refresh documentation unless a
  factual clarification is needed; browser login must not create a second
  credential format.

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
- [ ] Add the approved applicable callback UI contract and migrate existing
  generic callback consumers without a raw-action fallback.
- [ ] Define the unified private attempt model and safe public status shape.
- [ ] Add browser PKCE, authorization, callback validation, token exchange,
  credential normalization, and lifecycle cleanup.
- [ ] Preserve and regression-test the existing device-code flow.
- [ ] Add approved method selection and method-conditional browser
  presentation to the existing complete command/action flow.
- [ ] Bind browser completion through the applicable callback UI element and
  add approved generic mobile/desktop routing.
- [ ] Add decisive protocol, command, frontend, lifecycle, security,
  credential-consumer, and refresh evidence.
- [ ] Update maintained documentation.
- [ ] Obtain separate real-acceptance approval and only then run hosted sign-in,
  token/refresh, and model-request acceptance.
- [ ] Record requirement evidence before marking any requirement complete.

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
- Frontend action routing: one mobile and one desktop real-backend integration
  must start from the production session action, open the returned URL,
  deliver an OS-style callback to the production generic router, cross
  `RestAgentBackend` and the public HTTP callback-element invocation path,
  re-resolve the applicable `session_action_callback`, and finish in
  `chatgpt_auth`. Native iOS/Android and macOS focused tests must prove cold and
  live URL delivery where those platforms claim support; mocked per-side tests
  alone are not decisive.
- Callback exposure boundary: generic callback and MCP production-path tests
  prove callback links target UI element ids, only declared callback mappings
  become action inputs, conditions/disabled state are authoritative at
  invocation, omitted-plugin ambiguity is rejected, and bare or inapplicable
  action ids cannot execute. Inventory tests prove callback elements are
  absent from session menus, command catalogs, and `/action`.
- Method controls: production component tests for mobile and desktop and
  terminal parser tests prove both choices, labels, defaults, cancellation
  before start, CLI `--method`, slash `method=`, and `--no-open`.
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
- No HTTPS universal-link candidate was authorized or probed, so universal-link
  behavior remains unverified. Mobile hosted browser acceptance therefore
  remains conditional on a separately demonstrated provider-accepted app
  redirect. Do not add a relay; retain device code and return for a product
  decision if no acceptable app redirect is available.
- The probe did not open a browser, authenticate, request consent or MFA,
  receive an authorization code, contact the token endpoint, write or read
  credentials, test refresh, or make a model request. Only the redacted
  classifications, HTTP status classes, and redacted response location/error
  categories above were retained.
