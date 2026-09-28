# Provide Immediately Testable Local Runtime For App Review

Provide an immediately testable Crystal Lattice experience for App Review
Guideline 2.1(a), while establishing an embedded mobile runtime that ordinary
users can drive with their own provider credentials.

## Requirements checklist

- [ ] A fresh install exposes a testable path without requiring the reviewer
  to install the desktop CLI, join a private LAN, or provide reviewer-owned
  provider credentials.
- [ ] App Review may use a supplied private Crystal Lattice reviewer login
  backed by a live public OpenAI-compatible service.
- [ ] API-key or supported ChatGPT-backed authorization is the first-class
  normal-user model path; an actual on-device/platform model is a fallback.
- [ ] The review path uses a real model and the normal agent/tool loop; it does
  not expose a deterministic product or reviewer model.
- [ ] The minimal reviewed flow exercises sessions, message send/receive,
  visible tool calls/results, workspace persistence, and recovery across
  navigation or relaunch.
- [x] The completed built-in runtime includes general file reader and writer
  tools restricted to one app-owned or user-selected workspace.
- [ ] A near-term fixed tool set adds Tavily web search, an equivalent
  authenticated reviewer search proxy, and restricted Python execution that
  cannot change the application, runtime, configuration, or plugin set.
- [x] Provider credentials and bundled-agent controls flow through generic
  application configuration and complete runtime reload rather than only
  session overrides.
- [x] The built-in runtime uses a fixed, reviewed configuration and plugin/tool
  closure, with no downloaded executable or plugin code required to unlock
  reviewed behavior.
- [x] Background work is bounded by iOS execution policy, persists enough
  request/session state to recover, and communicates completion,
  interruption, or retry honestly.
- [ ] App Review notes contain the supplied credentials, exact test steps,
  expected structural results, and any device/runtime limitations.
- [x] Simulator automation covers the initial embedded-runtime path and is
  sufficient evidence for this capability before external TestFlight review.

Parent Task: tasks/20260614-ios-testflight-github-fastlane/000-main.md

Depends On:
tasks/20260614-ios-testflight-github-fastlane/050-privacy-landing-page-compliance.md

Depends On:
tasks/20260729-staged-application-config-and-full-reload.md

OVERLAP:
tasks/20260910-ios-embedded-runtime-poc/000-main.md

The linked task owns the initial embedded-runtime proof of concept and the
first two tool enhancements. This task retains the broader App Review outcome,
provider/fallback direction, reviewer instructions, privacy reconciliation,
and external TestFlight gate.

## Agreed direction

As of September 10, 2026:

- The embedded runtime is the local agent, session, tool, configuration, and
  persistence host. The primary model may remain remote.
- Normal users should first configure an API key or a supported
  ChatGPT-backed authorization path.
- App Review may receive a private caller key for a public OpenAI-compatible
  proxy backed by `gpt-5.6-luna`, restricted to that model and protected by a
  configurable persisted cost budget/cooldown.
- The on-device model is a fallback, not the first-run primary model.
- No deterministic model is part of the product or reviewer path.
- The initial capability is deliberately small and general: one fixed agent,
  a workspace-restricted `Read` tool, a workspace-restricted `Write` tool,
  visible multi-round tool use, persistence, and bounded background recovery.
- The initial example should be simple enough for a small model. It validates
  runtime integration and lifecycle rather than model intelligence.
- Tavily web search and restricted Python execution are the first likely tool
  enhancements. Broader tools such as email access remain possible extensions
  whose direction will be decided later.
- Every implementation increment should run in the real app and gain focused
  verification immediately. A long platform build followed by one final
  end-to-end test is not the intended delivery shape.

## Research findings

### Existing repository seams

- `AgentBackend` already recognizes an `inProcess` backend kind. The mobile
  app's Sessions, Messages, tool rendering, application actions, and
  notifications can therefore remain behind their current shared backend
  contract.
- The Python application owner already supports complete
  `AgentApplication` replacement while preserving the outer process and
  persisted stores. The mobile host can provide configuration from an
  app-owned overlay instead of the desktop `.env` writer.
- `FilesystemSessionStore` already writes session JSON atomically and can be
  rooted under the app sandbox.
- Existing Claude-compatible file tools provide useful schemas and formatting,
  but their desktop path and media behavior should be simplified for the
  initial iOS workspace.
- `tools/openai-proxy` already forwards OpenAI-compatible streaming and
  non-streaming requests. The proof of concept can extend it with incoming
  API-key authentication and use Ollama's OpenAI-compatible endpoint as the
  target.

### Bundling

- The completed work on
  `task/20260908-cli-distribution-test-levels` introduces an isolated,
  relocatable bundled-Python archive builder and direct boot-smoke helpers.
- The iOS application cannot consume the desktop archive launcher unchanged,
  but its selected-plugin discovery, source-shaped package staging, immutable
  bundle versus mutable-state separation, and isolated-build checks are useful
  inputs for the iOS bundle.
- iOS still needs an app-bundled CPython framework/runtime, iOS-compatible
  dependencies, a fixed plugin closure, and a native bridge. Dynamic plugin
  installation and desktop subprocess tools are not part of the embedded
  runtime.

### Authentication and review service

- The first proof of concept needs only a fixed OpenAI-compatible endpoint plus
  a basic API-key entry path. Production-grade credential provenance and
  polished settings remain separate hardening.
- The current ChatGPT device-code plugin is useful follow-up research, but its
  filesystem credential storage, `curl` subprocess fallback, polling
  lifecycle, and production authorization assumptions require iOS-specific
  work. It is not part of the initial proof of concept.
- A developer-operated reviewer proxy changes the completed privacy premise
  that no developer service receives user traffic. Before external review,
  privacy answers and the published policy must be reassessed for the actual
  reviewer-service retention and logging behavior.

### Background execution

- The current mobile host disconnects its selected transport when the app
  leaves the active state. An in-process runtime needs a distinct
  prepare/checkpoint/recover path.
- Simulator automation verifies lifecycle transitions and persisted state and
  is sufficient acceptance evidence for the initial capability.
- The proof of concept should add runtime timestamps and state diagnostics to
  the real app path, use a deliberately slow multi-round request, and test both
  completion and interruption recovery. It should not promise a fixed
  background duration.

### Restricted Python execution

- Desktop shell/Python execution based on child processes is unavailable to an
  embedded iOS runtime.
- The near-term Python tool should expose a deliberately restricted
  interpreter with a narrow syntax/module surface, bounded time/output, and no
  app/runtime/plugin/configuration mutation. It must not be presented as a
  general shell or package-install environment.
- Detailed restricted-interpreter design belongs to
  `tasks/20260910-ios-embedded-runtime-poc/030-restricted-python-executor.md`,
  after the embedded runtime and workspace tools are working.

## Initial proof-of-concept shape

The first working scenario should be intentionally simple, for example:

> Read `input.txt`, write a short transformed version to `output.txt`, read
> `output.txt` back, and tell me what changed.

This is sufficient when it results in several real provider requests, visible
`Read`/`Write` tool calls, a persisted workspace file, and a request that can
be placed in the background long enough to exercise lifecycle handling.

The initial implementation may stage behavior in this order:

1. Embedded Python starts in the foreground with no model authentication or
   tools.
2. The local runtime sends one real request through an unauthenticated
   development proxy to Ollama.
3. Background continuation/checkpoint diagnostics are added.
4. Workspace-restricted `Read` and `Write` tools are added.
5. The proxy enforces an API key and the app supplies it through a basic
   configuration path.
6. Simulator checks exercise the complete scenario.

The unauthenticated stages are temporary development checkpoints. The end of
the proof of concept requires proxy API-key enforcement.

## Improvement ideas and deferred direction

- Add Tavily search under one stable `web_search` tool contract, with a
  reviewer proxy that keeps the service credential off the device.
- Add the restricted Python executor without giving generated code access to
  the application, runtime configuration, plugin loader, or workspace.
- Adapt ChatGPT-backed authorization after its supported production contract
  and iOS credential lifecycle are confirmed.
- Add an Apple Foundation Models provider as the on-device fallback.
- Add user-selected workspace roots after the app-owned workspace is stable.
- Consider richer file operations, attachments, email, and other personal-data
  integrations only through later direction-setting work.

These ideas do not expand the initial proof-of-concept specification.

## Reviewer service follow-up

The reopened
`tasks/20260910-ios-embedded-runtime-poc/015-useful-runtime-tools-providers-and-settings.md`
owns the reviewer service implementation and deployment.

The planned App Review instructions are:

1. Open **On-device Provider Settings** from Home.
2. In **OpenAI-compatible reviewer**, enter the private caller key supplied in
   App Review notes.
3. Set the endpoint to
   `https://ireland-s1.dynamicprogrammingsolutions.com:3443/v1` and the model
   to `gpt-5.6-luna`.
4. Test and save the profile, open **On-device Python agents**, and create a
   `reviewer-claude` session.
5. Ask the agent to create a workspace file with `Write`, read it with `Read`,
   and report the result.
6. Confirm that tool calls/results are visible and the session/workspace
   survives navigation or relaunch.

The distributed app contains only the public reviewer CA certificate. The
upstream OpenAI key remains on the server, the private caller key is delivered
only through App Review notes, and reviewer-proxy request/response body logging
is disabled.

## Delivered embedded-runtime foundation

`tasks/20260910-ios-embedded-runtime-poc/010-embedded-runtime-openai-proxy-and-file-tools.md`
is complete. It delivered:

- app-bundled CPython and the fixed Crystal Lattice closure;
- a production `inProcess` backend and iOS connection/setup path;
- masked API-key owner configuration with complete application reconstruction;
- an authenticated OpenAI-compatible Ollama proxy;
- workspace-restricted text `Read` and `Write`;
- persisted sessions and workspace output across process relaunch;
- bounded native lifecycle state and delayed background continuation;
- production-screen, real-model, persistence, and background simulator tests.

The completed foundation does not deliver the public reviewer service,
ChatGPT authorization, on-device model fallback, Tavily, restricted Python,
privacy reconciliation, or external TestFlight review package.

## App Review and completion notes

Apple should receive an app-specific reviewer account or token, not shared
personal provider credentials. The reviewer service must remain reachable
during review and should use bounded credentials, rate limits, and redacted
logging.

The final review notes should assert stable structure rather than exact model
prose:

- login or API-key setup succeeds;
- a session can be created;
- several model/tool rounds occur;
- `Read` and `Write` calls are visible;
- the resulting workspace file can be read after navigation/relaunch;
- background completion or interruption is visible and recoverable.

The broader task remains incomplete until the local-model fallback,
privacy/reviewer package, and external-review evidence are delivered.
