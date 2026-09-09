# Embedded iOS Agent Runtime Proof Of Concept

Create the first working embedded Python agent runtime in the real iOS
application, then add only the two nearest tool capabilities needed to extend
it.

## Requirements checklist

- [ ] The iOS app hosts a working embedded Python/Crystal Lattice runtime and
  exercises it through the production mobile backend and screens.
- [ ] A real OpenAI-compatible model path uses an API-key-protected proxy
  backed by Ollama.
- [ ] The initial runtime exposes general `Read` and `Write` tools restricted
  to one application workspace.
- [ ] A simple multi-round request is verifiable in the simulator and on a
  physical device, including bounded background continuation or recovery.
- [ ] Tavily web search is added as the next fixed tool, with an equivalent
  reviewer proxy path.
- [ ] A restricted Python interpreter is exposed as a later fixed tool without
  access to application/runtime mutation.
- [ ] No deterministic product or reviewer model is introduced.

Related Task:
tasks/20260614-ios-testflight-github-fastlane/085-app-review-local-runtime-and-testable-mode.md

OVERLAP:
tasks/20260614-ios-testflight-github-fastlane/085-app-review-local-runtime-and-testable-mode.md

The related task retains the broader App Review, local-model fallback,
privacy, reviewer-service, and external TestFlight outcomes. This task owns
the initial implementation and only the first two tool enhancements.

## Scope boundaries

- Subtask `010` is approved for immediate execution.
- Subtasks `020` and `030` record likely next increments but have no approved
  execution plan.
- ChatGPT authorization, local-model fallback, email, broad file operations,
  production reviewer deployment, and polished production credential
  hardening are outside this task's current execution scope.

## Subtasks

- [ ] `tasks/20260910-ios-embedded-runtime-poc/010-embedded-runtime-openai-proxy-and-file-tools.md`
- [ ] `tasks/20260910-ios-embedded-runtime-poc/020-tavily-web-search.md`
- [ ] `tasks/20260910-ios-embedded-runtime-poc/030-restricted-python-executor.md`