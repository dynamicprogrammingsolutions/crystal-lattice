# Embedded iOS Agent Runtime Proof Of Concept

Create the first working embedded Python agent runtime in the real iOS
application, make it minimally useful with provider, tool, settings, and
session-management parity, then add the next research-oriented capabilities.

## Requirements checklist

- [x] The iOS app hosts a working embedded Python/Crystal Lattice runtime and
  exercises it through the production mobile backend and screens.
- [x] A real OpenAI-compatible model path uses an API-key-protected proxy
  backed by Ollama.
- [x] The initial runtime exposes general `Read` and `Write` tools restricted
  to one application workspace.
- [x] A simple multi-round request is verifiable in the simulator, including
  bounded background continuation or recovery. Simulator evidence is
  sufficient for this proof of concept.
- [x] Separate iOS-safe Claude-like and Codex-like plugin sets provide useful
  workspace and public-fetch tools with model-family-appropriate names,
  schemas, and result formatting.
- [x] The embedded runtime offers separate generic OpenAI-compatible,
  dedicated OpenAI Responses reviewer, direct OpenAI Responses, OpenRouter,
  and Anthropic profiles with provider-specific settings and tool families.
- [x] The local connection is preconfigured, and Home exposes a separate local
  runtime settings window for provider credentials, URLs, models, and default
  selection.
- [x] The iOS-safe application plugins from the ordinary default configuration
  expose session actions, message deletion, titles, search, metadata, status,
  pinning, archive, ordering, and attachments through the production mobile
  UI.
- [ ] Tavily web search is added as the next fixed tool, with an equivalent
  reviewer proxy path.
- [ ] A restricted Python interpreter is exposed as a later fixed tool without
  access to application/runtime mutation.
- [x] No deterministic product or reviewer model is introduced.
- [x] Provider packages intended for the embedded ZIP pass their existing unit
  and integration suites while imported from that ZIP, and the root
  `package.json` exposes the important bundle and Detox matrix commands.
- [x] Release-simulator real-API Detox covers the generic OpenAI-compatible,
  OpenAI Responses API-key, OpenAI Responses ChatGPT-action login, OpenRouter,
  Anthropic, and external reviewer paths.
- [x] An externally reachable, authenticated, model-limited, cost-limited
  GPT-5.6 Luna proxy makes the app usable by App Review without exposing the
  upstream OpenAI credential.
- [x] Sessions created with the credential-free `local` agent remain usable
  after a provider profile is enabled and the embedded application reloads.
- [x] On-device OpenAI settings use an explicit API-key or ChatGPT default,
  expose plugin-driven ChatGPT login controls, and retain independent
  per-session overrides.

Related Task:
tasks/20260614-ios-testflight-github-fastlane/085-app-review-local-runtime-and-testable-mode.md

OVERLAP:
tasks/20260614-ios-testflight-github-fastlane/085-app-review-local-runtime-and-testable-mode.md

The related task retains the broader App Review, local-model fallback,
privacy, reviewer-service, and external TestFlight outcomes. This task owns
the embedded implementation and its staged tool/provider enhancements.

## Scope boundaries

- Subtask `010` is complete.
- Subtask `015` is complete historical implementation and verification.
- Subtask `017` owns the approved reviewer Responses and ChatGPT
  settings/TLS correction and is under execution.
- Subtasks `020` and `030` record later increments but have no approved
  execution plan.
- ChatGPT authorization settings and the corrected production reviewer
  Responses path are in approved subtask `017`. Local-model fallback, email, arbitrary
  workspace roots, and polished cross-platform credential hardening remain
  outside this task.

## Subtasks

- [x] `tasks/20260910-ios-embedded-runtime-poc/010-embedded-runtime-openai-proxy-and-file-tools.md`
- [x] `tasks/20260910-ios-embedded-runtime-poc/015-useful-runtime-tools-providers-and-settings.md`
- [ ] `tasks/20260910-ios-embedded-runtime-poc/017-openai-responses-reviewer-and-chatgpt-settings.md`
- [ ] `tasks/20260910-ios-embedded-runtime-poc/020-tavily-web-search.md`
- [ ] `tasks/20260910-ios-embedded-runtime-poc/030-restricted-python-executor.md`
