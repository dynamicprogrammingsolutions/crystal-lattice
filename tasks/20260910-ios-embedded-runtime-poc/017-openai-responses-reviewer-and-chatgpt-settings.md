# Correct The Reviewer Responses Path And Add Built-In ChatGPT Settings

Correct the embedded reviewer path to use OpenAI Responses end to end, split
it from the generic Ollama-compatible profile, and make API-key versus
ChatGPT authentication an explicit plugin-driven choice in on-device settings.

## Requirements checklist

- [ ] A dedicated reviewer profile and agent use the bundled OpenAI Responses
  provider and send inference requests through `/v1/responses`; the reviewer
  path does not use Chat Completions.
- [ ] The reviewer profile is preconfigured with the Ireland HTTPS endpoint,
  `gpt-5.6-luna`, and the bundled reviewer CA, so App Review only needs the
  private incoming caller key.
- [ ] The reviewer agent uses the Codex-like tool package, including
  `apply_patch`, and a real Release-simulator request through Ireland visibly
  completes a tool call and survives application relaunch.
- [ ] The generic OpenAI-compatible provider remains a separate endpoint-
  neutral profile using the Claude-like tool package and remains testable
  against local Ollama.
- [ ] The OpenAI Responses requests transport supports an explicit CA bundle
  without disabling certificate verification or changing ordinary public-CA
  behavior.
- [ ] The configurable reviewer proxy can restrict its deployed inference
  protocol to Responses while preserving caller authentication, upstream-key
  replacement, model/service-tier filtering, usage-based pricing, persisted
  budget/cooldown state, and redacted request handling.
- [ ] On-device OpenAI settings expose exactly two default authentication
  choices, **API key** and **ChatGPT**; embedded settings do not expose or
  persist `auto`.
- [ ] The saved OpenAI authentication choice becomes the provider default,
  remains visible in session settings, and can be overridden per session
  without rewriting the saved default.
- [ ] On-device settings expose plugin-driven **Sign in**, **Check status**,
  **Cancel**, and **Log out** controls and render the action plugin's returned
  URL, code, Open-link, Copy-code, and follow-up actions without reimplementing
  the authorization protocol in React Native.
- [ ] Embedded Python HTTPS uses a bundled trusted CA store for ChatGPT
  device-code start, polling, token exchange, credential refresh, and related
  discovery requests; verification remains enabled and an untrusted
  certificate is still rejected.
- [ ] The manually gated simulator flow completes a real ChatGPT login, a real
  OpenAI Responses Codex-like tool request, credential reuse after relaunch,
  and reports an ungated skip as not run rather than success.
- [ ] A focused human check on a physical iOS device confirms that starting
  ChatGPT login reaches the URL/code display without
  `CERTIFICATE_VERIFY_FAILED`; broader acceptance remains simulator-based.
- [ ] Current mobile, provider, proxy, bundle, App Review, and operator
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
- [ ] Add regression coverage for current reviewer protocol/defaults and the
  current ChatGPT display/TLS gaps.
- [x] Split the generic compatible and dedicated reviewer profiles, including
  stable settings persistence/migration and agent/tool-family wiring.
- [x] Add explicit custom-CA support to the OpenAI Responses requests
  transport and preserve ordinary public-CA behavior.
- [x] Add configurable proxy endpoint allowlisting and update the Ireland
  configuration toward Responses-only inference.
- [ ] Pass a local HTTPS proxy-backed reviewer Responses tool loop through the
  production embedded backend and Release simulator.
- [ ] Add verified embedded HTTPS trust for ChatGPT login, polling, token
  exchange, refresh, and related discovery.
- [ ] Replace embedded `auto` UI/configuration with explicit API-key and
  ChatGPT defaults while retaining provider compatibility outside mobile.
- [ ] Add the plugin-driven ChatGPT settings action host and generic returned
  display/follow-up handling.
- [ ] Preserve and test per-session authentication overrides independently of
  the saved default.
- [ ] Rebuild the iOS bundle and run focused provider, proxy, mobile, bundle,
  TypeScript, documentation, and simulator verification.
- [ ] Obtain exact-command approval, update/redeploy Ireland, and pass the
  external reviewer Responses row.
- [ ] Run the manually gated real ChatGPT simulator flow through tool use and
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