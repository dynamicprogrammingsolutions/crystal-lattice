# Improve Local Agent Provider Settings

Deliver the requested first round of local-agent settings improvements:
clearer names, ordered OpenAI authentication controls, independent session
authentication overrides, and separate Reviewer exposure and enablement.
The user approved execution on 2026-10-06, with Reviewer initially hidden and
disabled and a two-step setup through Global and Local provider settings.

## Requirements checklist

- [x] R1 — The built-in connection is labelled **Local agent**, the ordinary
  OpenAI profile is labelled **OpenAI**, and provider model defaults are
  labelled **Default model**. Stable connection, provider, and agent IDs
  remain compatible with saved sessions and credentials.
- [x] R2 — OpenAI settings show **Default authentication**, **API key**, and
  **ChatGPT account** in that order. API-key editing and plugin-driven
  ChatGPT login/status/cancel/logout remain available regardless of the
  selected default. Only API key and ChatGPT are offered; no Auto choice is
  introduced.
- [x] R3 — The authentication selection is explicitly described as a
  default. OpenAI sessions can override it through Session Settings without
  changing the saved default, and resetting the override restores the
  provider default. Requests use the effective authentication method.
- [x] R4 — Reviewer is initially hidden and disabled. Reviewers enable it in
  Global Settings, then enter the supplied caller API key in Local provider
  settings; no third activation step is needed. When exposed, Reviewer
  appears last in provider settings with its
  own ordinary enable switch and an editable caller API key. Deployment URL,
  model, certificate, provider protocol, and tools remain hidden and fixed by
  maintained configuration. A hidden or disabled Reviewer is unavailable for
  new agent selection.
- [x] R5 — Provider settings no longer offer **Make default** or **Default
  agent** controls. Removing them preserves stored configuration and
  explicit agent selection for new sessions without choosing a new implicit
  default.
- [x] R6 — Existing autosave, non-persisting provider Test, Keychain-backed
  keys, plugin-owned ChatGPT credentials/actions, session overrides, and
  persisted sessions remain compatible across settings reload and app
  relaunch. Editing one settings surface does not overwrite independent
  values owned by the other.

Parent Task: tasks/20260910-ios-embedded-runtime-poc/000-main.md

Depends On:
tasks/20260910-ios-embedded-runtime-poc/017-openai-responses-reviewer-and-chatgpt-settings.md
tasks/20260910-ios-embedded-runtime-poc/018-embedded-json-config-plugin-parity-and-product-review.md

The dependencies' implemented provider/authentication and Python-owned
configuration capabilities are prerequisites. The remaining broad
compatibility acceptance in `018` does not require unrelated work before this
subtask can start.

## Approved decisions

- **Layout:** one OpenAI card with an Authentication subsection, ordered
  Default authentication, API key, ChatGPT account after URL/Default model.
  Both credential paths are always available.
- **Reviewer:** fresh settings hide and disable the profile. First global
  opt-in activates it so entering its key is the final setup step; later
  hide/show preserves explicit provider enable/disable preferences.
- **Labels:** Local agent, OpenAI, Default model, Local provider settings,
  Local providers, and Show reviewer sample provider are approved.
  Other profile/agent names remain provisional.

## Scope and policy correction

The user's revised direction permits per-session API/ChatGPT overrides and
replaces `018`'s earlier global-only authentication policy. Keep that earlier
record as historical implementation; this subtask owns the new default-plus-
override behavior.

Preserve the generic provider and authentication plugin contracts. The mobile
app owns placement and presentation; existing plugins own login actions,
credential interpretation, and request authentication. The Python application
continues to own the embedded JSON topology and profile metadata.

The `jsonpath` dependency-manifest correction and release smoke are already
implemented under `018` and were published as TestFlight version `0.10.0`,
build `14`. Preserve those checks; dependency packaging is not additional
implementation scope here.

The later Home/connections redesign, shared contextual-content contract,
plugin-driven empty states, information icons, new providers, multiple
accounts, and workspace enhancements are outside this first round. This
subtask does not create their task files or finalize their designs.

## Supporting facts

- `EmbeddedRuntimeSettingsModal.tsx` currently renders Reviewer visibility
  and OpenAI authentication as separate top-level cards. The API key is
  rendered inside the OpenAI provider card and disappears in ChatGPT mode;
  ChatGPT buttons are disabled in API mode. Login details are also
  conditionally hidden by the default mode.
- `GlobalSettingsModal.tsx` currently receives only visibility and close
  props. `ConnectedRoot.tsx` owns both modal hosts, and `App.tsx` already
  receives saved embedded configuration to refresh connection metadata and
  invalidate the available-agent cache.
- Swift `normalizedProviderSettings` forces Reviewer enabled, while
  `settingsByApplying` ignores Reviewer enable updates. The Python adapter
  already checks both Reviewer visibility and profile readiness when
  supplying `EMBEDDED_REVIEWER_ENABLED`.
- Both direct OpenAI and Reviewer currently have `auth_mode_options: []` in
  the maintained embedded JSON. The generic OpenAI Responses provider
  already accepts `["api", "chatgpt"]` to expose those session choices
  without Auto.
- The source runtime test
  `test_chatgpt_saved_default_and_session_override_are_independent` proves
  core override/reset semantics with fixture credentials. It does not prove
  that the user can select the currently hidden control or complete a real
  authenticated request.
- The Sessions screen creates sessions with the explicitly selected agent.
  Existing Detox setup still presses Make default, and
  `EmbeddedProviderMatrixDiagnosticsScreen.tsx` reads `defaultAgent`; those
  consumers must be revised when the control is removed.
- Existing `embeddedChatGPTLogin.e2e.test.ts` prints the login URL/code and
  gates browser approval behind `CRYSTAL_RUN_CHATGPT_LOGIN_E2E=1`. Preserve
  that manual boundary and report an ungated full-login case as not run.

## Execution plan

Status: Approved

### Settings ownership and behavior

Keep the persisted native embedded settings as the single authority for
Reviewer exposure, provider enablement, credentials, and provider defaults.
Move the Reviewer exposure control into Global Settings and connect both
modal hosts to the same saved-configuration refresh path. Global Settings
writes only `reviewerVisible`; provider settings writes only the provider
fields it owns. Preserve serialized autosave and refresh loaded values when
reopening a surface so an older form cannot overwrite a newer global choice.

Honor Reviewer `enabled` in native normalization and updates while retaining
fixed deployment fields. Initially hide and disable Reviewer. First global
opt-in activates the profile for the two-step setup; remember that initial
activation or explicit enablement has occurred so later exposure changes do
not overwrite the user's provider preference.
Python availability remains the combination of
exposure, enablement, and existing readiness checks. Preserve the credential
and enable preference when temporarily hiding the profile. Provider Test
validates its candidate without changing either exposure or enablement.

Within the OpenAI provider card, group its default selector, API key, and
ChatGPT account controls together in the required order. Manage both
credentials independently of the default selector. Signing in, checking
status, cancelling, or signing out does not rewrite the saved default.
Render action-provided login details and follow-ups regardless of that
default. Continue using the existing ChatGPT plugin action API and shared
action displays.

Change direct OpenAI's embedded `auth_mode_options` to `["api", "chatgpt"]`.
Leave Reviewer API-only. Sessions without an override inherit the saved
provider default; an explicit session override wins, and deleting it returns
to the current default. Keep the existing effective-auth streaming
selection so ChatGPT requests stream and session API overrides use the API
path. Use session-effective auth for API-only extension availability, rather
than the globally selected mode.

Remove the default-agent controls and their form writes. Keep the legacy
persisted `defaultAgent` field for compatibility and callers that omit an
agent. Update tests to create sessions through the normal production agent
picker; diagnostics must receive the explicitly tested provider context
rather than depend on the removed UI control.

### Delivery order

1. Add focused regression coverage for the current field hiding, disabled
   ChatGPT controls, absent session selector, and forced Reviewer enablement.
2. Correct naming and remove Make default while preserving internal IDs and
   existing explicit session creation.
3. Move Reviewer exposure to Global Settings, honor the independent provider
   enable switch, and prove persisted settings across both windows.
4. Apply the approved OpenAI grouping and ordered controls, then restore
   plugin-driven session authentication override/reset.
5. Update affected production-screen Detox flows, run focused acceptance,
   and update maintained documentation with verified behavior.

### Implementation decisions and open questions

- **Approved layout:** one OpenAI provider card with an inset
  Authentication section. Base URL and Default model precede that section;
  within it the order is Default authentication, API key, ChatGPT account.
  This keeps endpoint/model/credential ownership together and gives future
  provider authentication methods a reusable grouping.
- Do not duplicate the API key field across cards.
- **Approved wording:** “Sessions use this authentication method unless
  overridden in Session Settings.” This describes provider inheritance,
  rather than implying a change affects only newly created sessions.
- Reviewer first-use activation and companion labels are approved above.
  Do not introduce a new default provider, rename
  internal IDs, or settle other provisional names.
- Reuse config-driven `auth_mode_options` and ordinary action execution
  before adding an embedded plugin variant. A new generic settings/schema
  framework is not required for this task.
- Perform verification in the iOS simulator. Full ChatGPT authorization
  remains a manually enabled test; there is no physical-device gate.

### Documentation

Update the mobile runtime guide and application-owned embedded-configuration
guide after implementation. Describe defaults versus session overrides,
always-available credential controls, approved names, and the reviewer route:
Global Settings → enable Show reviewer sample provider → Local provider
settings → enter caller key.

Update affected current review instructions and remove Make-default steps.
Preserve historical task evidence and identify the superseded global-only
auth policy through this task's links. No new specification hierarchy or
broader onboarding documentation is planned.

### Task checklist

- [x] Confirm the OpenAI layout, Reviewer initial enablement, and companion
  labels; obtain execution approval.
- [x] Add focused correction tests and update the settled names.
- [x] Remove Make-default controls and dependencies in affected test flows.
- [x] Move Reviewer exposure to Global Settings and persist independent
  provider enablement without cross-window overwrites.
- [x] Implement the approved OpenAI grouping and always-available credential
  controls through existing plugin actions.
- [x] Restore direct OpenAI's session auth selector and verify override,
  reset, effective request mode, and applicable API controls.
- [x] Rebuild the embedded archive and Release simulator app; run focused
  public-path acceptance and report manual tests accurately.
- [x] Update maintained documentation, requirement evidence, and parent
  status.

### Requirement verification

- **R1 and R5:** production settings/connection component checks plus the
  affected simulator flow prove requested labels, no Make-default control,
  and session creation with the explicit selected agent. Reopen a saved
  session to prove display renaming did not change its identity.
- **R2:** extend the existing ungated ChatGPT Detox start/cancel case to start
  login while API remains the default. Assert both credential controls,
  returned URL/code/follow-ups, and cancellation. Component checks cover the
  exact field order, API-key visibility in ChatGPT mode, and unchanged
  default after account actions.
- **R3:** add one integration check using the production
  `SessionSettingsModal`, `RestAgentBackend`, public session/config routes,
  and real provider/auth plugins together. Select an override, inspect the
  effective configuration, reset it, and confirm the native/provider default
  was not modified. Fixture credentials prove configuration routing without
  claiming hosted authentication success.
- **R3 hosted acceptance:** adapt the manually gated ChatGPT simulator case
  to complete browser login and make a real tool request after selecting the
  session override, then reset and check inheritance. Run the focused API-key
  OpenAI row as the complementary request path. Do not accept a skipped
  manual login as a pass.
- **R4:** adapt the external Reviewer Detox row to start in Global Settings,
  expose Reviewer, reopen provider settings, enter its private caller key,
  exercise enable/disable and last placement, then explicitly select the
  Reviewer agent for a real tool request. Assert the fixed fields remain
  hidden; hiding exposure removes it from new-session selection.
- **R6:** extend those focused flows with modal reopen and app relaunch.
  Assert saved keys/defaults/enablement, retained session overrides, and
  unchanged independent values when switching settings windows. Preserve the
  existing non-persisting Test and autosave component checks.

### Additional implementation verification

- Run `npm run test:ios:embedded-runtime:bundle` on the rebuilt artifact and
  the existing provider-package bundle check within its provider-only scope.
- Run affected runtime/config tests, mobile Jest, TypeScript, focused Ruff,
  documentation preparation, and `git diff --check`.
- Reuse the existing focused OpenAI, ChatGPT, and Reviewer matrix commands.
  Broaden provider testing only if changed interfaces or a failure expose a
  further concern.
- Preserve modal presentation settling and production accessibility/test
  identifiers. Keep API keys and tokens out of logs and snapshots; retain
  intentional one-time URL/code reporting in the manually gated login test.

## Implementation Notes

- 2026-10-06: Execution approved with Reviewer initially hidden/disabled.
  Implementation moved to
  `/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20261006-local-provider-settings`
  after earlier edits disappeared from the shared checkout during testing.
  Implementation and simulator verification completed on 2026-10-06.
- Source verification: 39 Python tests passed, 58 mobile suites / 303 tests
  passed, plus the new pending-edit close regression. Both real-HTTP
  authentication override/reset cases passed through the production modal
  and adapter, including auth-aware Flex/Fast visibility. TypeScript,
  Swift parsing, bundle action/provider checks, and documentation preparation
  passed.
- Native settings verification exposed Global Settings opening while the Home
  menu was still dismissing. The existing fixed delay remained unreliable
  across repeated navigation; both settings routes now open from iOS's actual
  menu `onDismiss` callback. Android retains the existing delayed handoff.
  The simulator regression passed initial hidden/disabled Reviewer, first
  global opt-in followed by key entry, auth/key persistence after relaunch,
  and preservation of an explicitly disabled profile across hide/show.
- The first hosted OpenAI matrix request completed a real tool call, then
  exposed a stale diagnostic: it still searched for the removed `directory`
  core UI element. Update the diagnostic to consume the workspace application's
  public session UI schema, persist `workspace_id`, and retain boundary and
  isolation checks. This corrects test infrastructure to the current product
  contract without restoring an obsolete setting or bypassing validation.
- Hosted simulator evidence: both the direct OpenAI and real Ireland Reviewer
  rows passed with `apply_patch`, old-local-session preservation, workspace
  selection, boundary rejection, isolation, and relaunch evidence. The
  production Reviewer path used its bundled public CA and the existing caller
  credential; no server configuration or credentials were changed.
- The ungated real ChatGPT login-start/cancel case passed while API stayed the
  default. It verified plugin-provided login URL/code and follow-up actions.
  At the unattended checkpoint, the browser-authorized request case was
  collected but not run. The later manual acceptance is recorded below.
- Maintained mobile/application documentation now describes defaults versus
  overrides and the two-step Reviewer flow. Root command
  `npm run test:ios:local-provider-settings` runs the native settings
  regression. No second-round Home/contextual-content implementation was
  started.
- Final reconciliation onto `develop` preserved unrelated changes. All 30
  session-owned files matched the verified worktree. The final develop check
  passed 54 Python tests, TypeScript, 58 mobile Jest suites / 304 tests, and
  `git diff --check`. Implementation changes remain uncommitted.

## Completion Notes

Completed on 2026-10-06.

- All six requirements are verified. The approved OpenAI layout, names,
  session authentication override/reset, two-step Reviewer setup, independent
  switches, removed Make-default controls, and persistence are implemented.
- R3's final manual Release-simulator test passed after the user approved the
  real device-code login. API remained the provider default; a ChatGPT session
  override completed an actual `apply_patch` request after app relaunch, with
  tool-result and workspace boundary/isolation assertions. The gated command
  exited successfully: 1 test passed; the separately verified ungated
  start/cancel case was intentionally skipped in this mode.
- Earlier manual attempts exposed an incorrect scroll direction toward the
  provider switch at the top of the new card. Correcting the test's direction
  preserved the production user flow. A failed continuation attempt confirmed
  that a new Detox invocation reinstalls the app and clears its login; the
  temporary resume branch was removed. Final acceptance used a fresh,
  browser-approved login without credential injection or test-only shortcuts.
- Supporting verification passed: 54 Python checks, 58 mobile suites /
  304 tests, production HTTP auth override/reset cases, TypeScript, Swift
  parsing, source/bundle checks, Release simulator settings and real OpenAI/
  Reviewer requests, and maintained documentation preparation.
- Product findings fixed in scope were the Home-menu modal handoff and
  pending provider edits on close. The matrix diagnostic now consumes the
  existing public workspace-ID contract. No physical-device gate or
  production-server modification was needed.
- Changes are uncommitted on `develop`, with verification artifacts in the
  isolated worktree. The second-round Home/contextual-content task directory
  remains Draft and was not implemented.