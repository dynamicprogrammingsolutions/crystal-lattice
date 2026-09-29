# Correct The Reviewer Responses Path And Add Built-In ChatGPT Settings

Correct the embedded reviewer path to use OpenAI Responses end to end, split
it from the generic Ollama-compatible profile, and make API-key versus
ChatGPT authentication an explicit plugin-driven choice in on-device settings.

## Requirements checklist

- [x] A dedicated reviewer profile and agent use the bundled OpenAI Responses
  provider and send inference requests through `/v1/responses`; the reviewer
  path does not use Chat Completions.
- [x] The reviewer profile is preconfigured with the Ireland HTTPS endpoint,
  `gpt-5.6-luna`, and the bundled reviewer CA, so App Review only needs the
  private incoming caller key.
- [x] The reviewer agent uses the Codex-like tool package, including
  `apply_patch`, and a real Release-simulator request through Ireland visibly
  completes a tool call and survives application relaunch.
- [x] The generic OpenAI-compatible provider remains a separate endpoint-
  neutral profile using the Claude-like tool package and remains testable
  against local Ollama.
- [x] The OpenAI Responses requests transport supports an explicit CA bundle
  without disabling certificate verification or changing ordinary public-CA
  behavior.
- [x] The configurable reviewer proxy can restrict its deployed inference
  protocol to Responses while preserving caller authentication, upstream-key
  replacement, model/service-tier filtering, usage-based pricing, persisted
  budget/cooldown state, and redacted request handling.
- [x] On-device OpenAI settings expose exactly two default authentication
  choices, **API key** and **ChatGPT**; embedded settings do not expose or
  persist `auto`.
- [x] The saved OpenAI authentication choice becomes the provider default,
  remains visible in session settings, and can be overridden per session
  without rewriting the saved default.
- [x] On-device settings expose plugin-driven **Sign in**, **Check status**,
  **Cancel**, and **Log out** controls and render the action plugin's returned
  URL, code, Open-link, Copy-code, and follow-up actions without reimplementing
  the authorization protocol in React Native.
- [x] Embedded Python HTTPS uses a bundled trusted CA store for ChatGPT
  device-code start, polling, token exchange, credential refresh, and related
  discovery requests; verification remains enabled and an untrusted
  certificate is still rejected.
- [x] The manually gated simulator flow completes a real ChatGPT login, a real
  OpenAI Responses Codex-like tool request, credential reuse after relaunch,
  and reports an ungated skip as not run rather than success.
- [ ] A focused human check on a physical iOS device confirms that starting
  ChatGPT login reaches the URL/code display without
  `CERTIFICATE_VERIFY_FAILED`; broader acceptance remains simulator-based.
- [x] Current mobile, provider, proxy, bundle, App Review, and operator
  documentation describes the corrected protocol and authentication flow.

Parent Task: tasks/20260910-ios-embedded-runtime-poc/000-main.md

Depends On:
tasks/20260910-ios-embedded-runtime-poc/015-useful-runtime-tools-providers-and-settings.md

Related Task:
tasks/20260614-ios-testflight-github-fastlane/085-app-review-local-runtime-and-testable-mode.md

## Scope and supporting facts

- The historical external reviewer test was real, but its path was
  `reviewer-claude` → `reference_openai_compatible` →
  `/v1/chat/completions` → Ireland → OpenAI Chat Completions. Its proxy, TLS,
  authentication, rate-limit, tool-loop, and persistence evidence remains
  useful but does not prove the newly required Responses path.
- `tools/openai-proxy` already forwards both `/responses` and
  `/chat/completions` without translating between them. The deployment needs
  a configurable endpoint allowlist so the reviewer service cannot silently
  regress to Chat Completions.
- The current reviewer profile combines local Ollama defaults with the
  Ireland reviewer CA. The correction creates a dedicated reviewer profile
  and leaves a separate generic OpenAI-compatible profile for Ollama and
  future compatible endpoints.
- OpenAI Responses and the reviewer both use Codex-like tools. They remain
  separate profiles because the reviewer has a fixed deployment URL, custom
  CA, caller key, and App Review lifecycle, while ordinary OpenAI supports
  direct API-key or ChatGPT account authorization.
- The ChatGPT application plugin already owns device-code acquisition,
  polling, saved credentials, status, cancellation, logout, and generic action
  displays. Settings should invoke those actions through the ordinary
  application action API.
- The current plugin returns a pending login display with an URL, code,
  `open_url`, `copy_text`, and `run_action` follow-up. The current manual Detox
  test incorrectly waits for a modal even though that display requests inline
  presentation.
- The physical-device error is consistent with embedded
  `urllib.request.urlopen` using no explicit CA context while the iOS runtime
  has no configured OpenSSL default trust path. Certifi is already bundled and
  used by the embedded fetch engine.
- The OpenAI provider may retain `auto` for non-mobile compatibility. Existing
  embedded `auto` settings will migrate to explicit `api`; selecting ChatGPT
  remains an intentional user action.
- The upstream OpenAI key exposed by an earlier failed-test traceback must be
  rotated and the Ireland `.env` updated before external acceptance if that
  operational correction has not already occurred.
- This task does not add Tavily, restricted Python, email, arbitrary
  workspaces, new providers, or a general credential-management redesign.

## Execution plan

Status: Approved

First establish failing boundary tests for the current Chat Completions
reviewer wiring, stale ChatGPT display assertion, and absent embedded HTTPS
trust. Then deliver the reviewer Responses path as the first complete vertical
slice: a dedicated preconfigured profile, custom-CA-capable Responses
transport, Codex-like tools, configurable proxy endpoint restriction, and a
local proxy-backed simulator test. This checkpoint must work before the
settings-authentication redesign proceeds.

Next configure a trusted CA store for embedded Python HTTP clients and cover
all ChatGPT lifecycle calls rather than fixing only device-code start. Reuse a
small shared helper where package ownership permits; do not disable
verification or special-case iOS behavior in general source installations.

Then extend On-device Provider Settings with an explicit API-key/ChatGPT
choice and a small action host. The settings UI calls the existing
`chatgpt_auth` application actions and renders their returned generic display
and follow-ups with shared mobile components. No hidden session or parallel
React Native authorization implementation is introduced. Provider session
configuration continues to expose the effective choice, with only API and
ChatGPT offered by the embedded runtime.

Finally rebuild the immutable iOS ZIP and Release simulator application, run
focused source and bundle verification, run the reviewer row against the
deployed endpoint after separately approved deployment, and run the manually
gated ChatGPT login through a real `apply_patch` request and relaunch. The
physical-device check is limited to proving that login start reaches the
URL/code display without a certificate failure.

### Implementation decisions and open questions

- **Approved:** create a fifth provider profile for the dedicated reviewer
  rather than overloading either the generic compatible or ordinary OpenAI
  profile.
- **Approved:** use agent id `reviewer-codex`; preserve or migrate any existing
  `reviewer-claude` sessions/configuration sufficiently for development data
  to remain inspectable.
- **Approved:** the generic OpenAI-compatible profile keeps Claude-like tools;
  reviewer and ordinary OpenAI Responses profiles use Codex-like tools.
- **Approved:** embedded settings expose only `api` and `chatgpt`; existing
  embedded `auto` values normalize to `api`. The provider package may retain
  `auto` for other consumers.
- **Approved:** settings invoke application-level `chatgpt_auth` actions
  directly. Session action declarations remain available for session menus
  when ChatGPT mode applies.
- **Approved:** use bundled Certifi roots or an equivalent explicit verified
  context; never set `verify=False` or globally trust the reviewer self-signed
  certificate for unrelated hosts.
- **Operational gate:** changing the Ireland deployment or AWS state requires
  a new exact-command confirmation. Local assets and tests proceed before that
  confirmation.
- **Human gate:** the real-device URL/code check remains incomplete until the
  user confirms it on a physical device.

### Documentation

- Update the embedded runtime development guide with the five profiles,
  Responses reviewer protocol, preconfigured reviewer fields, API/ChatGPT
  settings flow, CA ownership, simulator gate, and focused device check.
- Correct the App Review task's target instructions and make clear which
  instructions are not implemented until this task completes.
- Update the OpenAI Responses documentation for explicit custom-CA support in
  the requests transport and clarify that the auth feature supplies ChatGPT
  credentials to that transport in the embedded runtime.
- Update the proxy README and Ireland runbook with configurable endpoint
  restriction and Responses-specific verification.
- Keep the historical Chat Completions reviewer evidence in subtask `015`,
  clearly labeled as superseded acceptance rather than rewritten.

### Task checklist

- [x] Create the approved subtask, correction handoff, parent links, and
  updated dependency boundaries.
- [x] Add regression coverage for current reviewer protocol/defaults and the
  current ChatGPT display/TLS gaps.
- [x] Split the generic compatible and dedicated reviewer profiles, including
  stable settings persistence/migration and agent/tool-family wiring.
- [x] Add explicit custom-CA support to the OpenAI Responses requests
  transport and preserve ordinary public-CA behavior.
- [x] Add configurable proxy endpoint allowlisting and update the Ireland
  configuration toward Responses-only inference.
- [x] Pass a local HTTPS proxy-backed reviewer Responses tool loop through the
  production embedded backend and Release simulator.
- [x] Add verified embedded HTTPS trust for ChatGPT login, polling, token
  exchange, refresh, and related discovery.
- [x] Replace embedded `auto` UI/configuration with explicit API-key and
  ChatGPT defaults while retaining provider compatibility outside mobile.
- [x] Add the plugin-driven ChatGPT settings action host and generic returned
  display/follow-up handling.
- [x] Preserve and test per-session authentication overrides independently of
  the saved default.
- [x] Rebuild the iOS bundle and run focused provider, proxy, mobile, bundle,
  TypeScript, documentation, and simulator verification.
- [x] Obtain exact-command approval, update/redeploy Ireland, and pass the
  external reviewer Responses row.
- [x] Run the manually gated real ChatGPT simulator flow through tool use and
  relaunch.
- [ ] Obtain human confirmation of the focused physical-device login-start
  check.
- [ ] Complete requirement evidence, documentation, and immutable completion
  notes.

### Requirement verification

- Inspect the generated runtime configuration and capture a local proxy
  request to prove the reviewer provider is `openai_responses`, the agent is
  `reviewer-codex`, the tool is `apply_patch`, and the request path is
  `/responses`.
- Exercise the generic compatible profile against Ollama through its existing
  public app/backend path and prove it still uses Claude-like tools.
- Run transport tests with a trusted custom CA, ordinary Certifi roots, and an
  untrusted certificate to prove explicit verification behavior.
- Run proxy tests proving a Responses-only deployment accepts `/responses`
  and rejects `/chat/completions` before upstream forwarding while all
  authentication, model, usage, budget, and persistence tests remain green.
- Run production-screen settings tests proving reviewer preconfiguration,
  API/ChatGPT-only choices, Keychain ownership, saved default, and independent
  session override.
- Run an action integration through the embedded backend proving settings
  receives and renders the plugin's real URL/code display and executes its
  Open-link, Copy-code, and Check-status follow-ups.
- Run the gated simulator login with real human authorization, assert
  authenticated status, complete a real `apply_patch` request, and verify
  credential/session reuse after relaunch.
- Run the deployed reviewer Release-simulator row with the private caller key;
  assert real tool output, final marker, and persisted-session relaunch.
- Record human confirmation that a physical device reaches the URL/code
  display without `CERTIFICATE_VERIFY_FAILED`.

### Additional implementation verification

- Assert the immutable iOS ZIP contains the selected providers, ChatGPT
  application plugin, Certifi CA data, reviewer public CA, and no dev/test
  dependencies.
- Re-run selected OpenAI Responses provider integration tests from the
  prebuilt ZIP after transport changes.
- Verify no API key, ChatGPT token, authorization code, or login URL query
  secret appears in committed files, logs, snapshots, or test failure output.
- Verify old `reviewer-claude` development state cannot silently select the
  generic Ollama profile as the new reviewer default.
- Run `git diff --check`, focused Ruff/TypeScript checks, and documentation
  preparation before each implementation checkpoint.

## Implementation Notes

- 2026-09-28: The user approved immediate creation and execution after
  confirming that the reviewer must use OpenAI Responses and that the
  previously proposed ChatGPT TLS/settings corrections belong in the same
  follow-up. Local implementation is authorized. Ireland/AWS mutation remains
  separately confirmation-gated.
- 2026-09-28: Added settings schema version 3 with separate
  `compatible-claude` and `reviewer-codex` profiles. The reviewer is
  preconfigured for Ireland/Luna, uses the OpenAI Responses requests transport
  with explicit CA verification, and receives Codex-like tools. Legacy V2
  settings migrate local reviewer values and Keychain credentials to the
  compatible profile while preserving known Ireland reviewer values.
- 2026-09-28: Added configurable proxy endpoint allowlisting and changed the
  checked-in Ireland configuration to permit only `/models` and `/responses`.
  Thirteen proxy tests, 12 embedded runtime tests, three focused Responses
  transport tests, 273 mobile tests, TypeScript compilation, Ruff, and the
  Release simulator build pass. Runtime preparation was corrected to preserve
  the tracked public reviewer CA across generated-resource replacement.
- 2026-09-28: Isolated the apparent API/ChatGPT selector failure against
  existing modal Detox coverage. With Detox synchronization disabled, iOS
  drops touches during modal presentation; the existing production-modal
  pattern waits 600 ms after visibility. Applying the same boundary made the
  selector pass without a test-only UI path.
- 2026-09-28: The first real device-code request then exposed the desktop
  `curl` fallback as incompatible with iOS. OpenAI returned HTTP 530
  `cf_route_error` to `urllib` while the bundled in-process `requests`
  transport returned HTTP 200 for the same request. The plugin now retries
  that specific response with verified Certifi-backed `requests`, declares it
  as a runtime dependency, and no longer requires process spawning.
- 2026-09-28: The ungated Release-simulator ChatGPT flow now selects ChatGPT,
  starts a real OpenAI device-code attempt, renders the plugin-provided
  Open-link and Copy-code actions, and cancels successfully. The action row
  wraps on compact screens. The human authorization/tool-request portion
  remains collected and skipped unless its explicit gate is enabled.
- 2026-09-28: A local HTTP loopback authenticated, Luna-only, Responses-only
  reviewer proxy completed the Release-simulator reviewer matrix through
  `reviewer-codex`. The run preserved a credential-free local session,
  invoked `apply_patch`, produced `MATRIX_REVIEWER`, and recovered the same
  provider session after relaunch. Proxy evidence contained only `/v1/models`
  and `/v1/responses`; two Responses calls completed with HTTP 200, and the
  configured budget ledger recorded `$0.0004818`. This proves the
  provider/tool/relaunch slice but does not complete the checklist's HTTPS
  boundary; that still requires a simulator-trusted local test certificate or
  the separately gated Ireland deployment. A repeat run passed with an
  explicit `embedded-provider-matrix-tools == apply_patch` assertion.
- 2026-09-28: Completed the local HTTPS boundary with a temporary self-signed
  certificate whose public PEM was copied into the simulator app data
  container and entered through the production reviewer CA setting. The
  private key remained host-only. The Release simulator again passed
  `reviewer-codex` plus `apply_patch`, persisted-session relaunch, five
  `/v1/models` responses, and two `/v1/responses` calls; all proxy responses
  were HTTP 200 and the cost ledger recorded `$0.000486`.
- 2026-09-28: Added stable session-setting auth-choice identifiers and
  selected accessibility state. Runtime coverage proves a saved ChatGPT
  default remains unchanged while one session overrides it to API using its
  available API key, then returns to the saved ChatGPT default using stored
  credentials.
- 2026-09-28: The immutable ZIP real-API boundary passed six selected OpenAI
  Responses tests and nine selected OpenRouter tests with provider,
  `agent_core`, and `requests` imports forced from the archive; its SHA-256
  remained unchanged. The rebuilt Release simulator then passed the generic
  Ollama, direct OpenAI Responses, OpenRouter, and Anthropic rows, each
  preserving the preconfiguration local session and recovering its provider
  session after relaunch.
- 2026-09-28: The provider matrix now polls validation text directly while
  Detox synchronization is disabled. The older Ollama diagnostic accepts
  `multi-provider` when another provider credential persists in iOS Keychain
  across app-data deletion; its stronger `Read`/`Write`, workspace-output,
  application-route, and relaunch assertions still prove that the
  `compatible-claude` path ran.
- 2026-09-29: After exact-command confirmation, updated the live Ireland
  deployment at `/home/irelandsrv/reviewer-openai-proxy`. The host uses a
  flattened Compose layout, so the first mirrored-layout staging attempt
  stopped before container recreation; the corrected deployment preserved
  the existing caller key, TLS certificate/private key, and budget ledger,
  while replacing the upstream key with the current root `.env` key.
- 2026-09-29: Live health reports bearer authentication, only
  `gpt-5.6-luna`, only `/models` and `/responses`, a `$1` budget, no cooldown,
  and `$0.000797` spent. Chat Completions returns `404`, unauthenticated model
  access returns `401`, request headers remain hidden, bodies remain
  unlogged, and the on-disk ledger remains readable by the non-root proxy
  container.
- 2026-09-29: The external Release-simulator reviewer row passed in 139
  seconds. It configured the prefilled Ireland profile with the preserved
  caller key, retained a credential-free local session, invoked
  `apply_patch`, produced `MATRIX_REVIEWER`, and recovered the same provider
  session after relaunch. Proxy logs show five successful `/v1/models` calls
  and two successful `/v1/responses` calls.
- 2026-09-29: The failed mirrored-layout staging left an unused
  `/home/irelandsrv/reviewer-openai-proxy/deploy/ireland/` directory with
  mode-restricted staged files. With separate user approval, removed that
  unused directory and verified that both running containers still mount
  only the flattened deployment paths.
- 2026-09-29: Gated ChatGPT simulator attempts received real device login
  URL/code actions but never reached a terminal authenticated state within
  the 15-minute human authorization window. The first attempts also exposed
  two settings-host defects: polling read a Markdown scroll wrapper instead
  of the plugin's structured `auth_status`, and follow-up polling replaced
  the login card despite its `preserve_display` flag. Settings now displays
  the structured auth state and retains the code/link during status checks;
  the gated test skips the preliminary start/cancel scenario. The next
  attempt's Detox trace and failure screenshot showed `pending` throughout
  with Open-link and Copy-code still visible. No human browser approval was
  observed, so the real authenticated tool request and relaunch requirement
  remains incomplete. The ungated start/cancel case remains passing.
- 2026-09-29: The gated test now prints the plugin-returned login URL and
  one-time code so a person can authorize in a computer browser. The same
  values remain selectable in the on-device settings card. The ungated
  start/cancel test verifies that they are present without printing a code.
  Three settings component tests, TypeScript, the Release simulator build,
  and the real ungated device-code start/cancel simulator test passed. Manual
  approval and the authenticated tool/relaunch flow remain unverified.
- 2026-09-29: The user completed the ChatGPT browser authorization during
  the gated simulator run. After Save, the provider request failed with
  `chatgpt auth_mode requires streaming requests`: both embedded `/send` and
  `/send_message` had forced non-streaming requests. The test had terminated
  the app while the settings modal was still open; Save itself had succeeded.
- 2026-09-29: Embedded requests now stream when their effective provider is
  OpenAI Responses with ChatGPT auth, including session and request overrides.
  API-key and local smoke requests retain their existing mode; streaming
  all embedded requests had exposed a local smoke-provider regression. The
  fresh-login Detox flow now confirms Save, closes the settings modal, then
  relaunches. A proposed cross-run credential-reuse test was removed after
  Detox cleanup/reinstall removed the saved simulator credentials.
- 2026-09-29: Twenty-seven mobile Python runtime tests, changed-file Ruff,
  TypeScript, docs preparation, a Release simulator build, the ungated
  device-code start/cancel Detox test, and the real API-key OpenAI Responses
  `apply_patch`/relaunch Detox row passed. The full ChatGPT-authenticated
  tool/relaunch run still requires a fresh human authorization and remains
  incomplete.
- 2026-09-29: The user ran the manually gated Release-simulator Detox flow
  with fresh browser approval and reported a passing suite (one test passed,
  one start/cancel test intentionally skipped). After login and Save, the
  test closed settings, relaunched without deleting app data, and verified
  `openai-codex`, the real `apply_patch` tool result, and `MATRIX_OPENAI`.
  This completes the ChatGPT simulator requirement; the separate
  physical-device TLS check still needs human confirmation.