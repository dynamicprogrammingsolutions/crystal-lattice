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
- [ ] Separate iOS-safe Claude-like and Codex-like plugin sets provide useful
  workspace and public-fetch tools with model-family-appropriate names,
  schemas, and result formatting.
- [ ] The embedded runtime offers fixed OpenAI-compatible, OpenAI Responses,
  OpenRouter, and Anthropic agents with provider-specific settings.
- [ ] The local connection is preconfigured, and Home exposes a separate local
  runtime settings window for provider credentials, URLs, models, and default
  selection.
- [ ] The iOS-safe application plugins from the ordinary default configuration
  expose session actions, message deletion, titles, search, metadata, status,
  pinning, archive, ordering, and attachments through the production mobile
  UI.
- [ ] Tavily web search is added as the next fixed tool, with an equivalent
  reviewer proxy path.
- [ ] A restricted Python interpreter is exposed as a later fixed tool without
  access to application/runtime mutation.
- [x] No deterministic product or reviewer model is introduced.

Related Task:
tasks/20260614-ios-testflight-github-fastlane/085-app-review-local-runtime-and-testable-mode.md

OVERLAP:
tasks/20260614-ios-testflight-github-fastlane/085-app-review-local-runtime-and-testable-mode.md

The related task retains the broader App Review, local-model fallback,
privacy, reviewer-service, and external TestFlight outcomes. This task owns
the embedded implementation and its staged tool/provider enhancements.

## Scope boundaries

- Subtask `010` is complete.
- Subtask `015` contains a Draft execution plan awaiting approval.
- Subtasks `020` and `030` record later increments but have no approved
  execution plan.
- ChatGPT authorization, local-model fallback, email, arbitrary workspace
  roots, production reviewer deployment, and polished cross-platform
  credential hardening are outside this task's current execution scope.

## Subtasks

- [x] `tasks/20260910-ios-embedded-runtime-poc/010-embedded-runtime-openai-proxy-and-file-tools.md`
- [ ] `tasks/20260910-ios-embedded-runtime-poc/015-useful-runtime-tools-providers-and-settings.md`
- [ ] `tasks/20260910-ios-embedded-runtime-poc/020-tavily-web-search.md`
- [ ] `tasks/20260910-ios-embedded-runtime-poc/030-restricted-python-executor.md`
