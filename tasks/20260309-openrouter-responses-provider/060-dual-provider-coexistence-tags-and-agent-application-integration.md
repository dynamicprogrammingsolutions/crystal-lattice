# Ensure OpenRouter `/chat` + `/responses` Plugins Coexist (Tags + Dual-Agent Integration)

Short description: Ensure the two OpenRouter provider/plugin sets (chat-completions provider vs `/responses` provider) can be loaded together in a single AgentApplication config without cross-activating the wrong extensions. Add a dual-agent integration test with a config that registers both plugin sets and defines two agents selecting the two providers, then validates reasoning + tool calling + multi-turn persistence + delete/slice behavior for both.

Parent Task: `tasks/20260309-openrouter-responses-provider/000-main.md`

## Motivation

We want users to be able to install/configure both OpenRouter plugin sets simultaneously, and select between them per-agent.

This requires:
- Provider tags (`get_tags`) and extension `required_tags()` to isolate which extensions activate under which provider.
- An end-to-end integration test proving that:
  - both plugin sets resolve in one config
  - each agent uses the intended provider and extensions
  - tool calling + reasoning works in both
  - history editing (delete/slice) works and does not break the next request

## Scope

- Validate tag isolation in practice, not only via unit tests.
- Add a new AgentApplication integration test that loads a config with both plugin sets listed under `plugins`.

## Implementation notes

### 1) Tag isolation

Verify and, if needed, correct:
- `OpenRouterResponsesProvider.get_tags()` returns `openrouter_responses` (and *not* `openrouter`).
- `/responses` extensions have `required_tags()` that include `openrouter_responses`.
- The chat-completions OpenRouter provider and its extensions use `openrouter` (and *not* `openrouter_responses`).

The goal is that when an agent selects provider A, only extensions that require provider A’s tag activate.

### 2) Dual-agent AgentApplication integration test

Add a new integration test (under `plugins/openrouter_responses/tests/` or `application/python/tests/`) that:

- Writes a temp config JSON with:
  - `plugins`: includes both plugin sets (chat OpenRouter provider + extensions + tools, and `/responses` provider + extensions + tools)
  - `providers`: two provider blocks (one for each provider)
  - `agents`: two agents selecting the different providers

- Runs the same tool-loop scenario for both agents using the existing `plugins/openrouter_responses/tests/reasoning_test/` fixture:
  - Use two models: `openai/gpt-5-mini` and `anthropic/claude-haiku-4.5`.
  - Ensure tool calls happen (file read) and that the loop finishes with a final assistant answer.
  - Validate “reasoning preserved between requests” using the existing reasoning_test expectations (do not recompute after tool results).

- Performs the same delete + slice operations described in `tasks/20260309-openrouter-responses-provider/050-fix-native-indices-and-slicing-integration.md` for both agents/sessions:
  - Delete first turn after two turns
  - Slice/fork first turn
  - After each operation, send a follow-up user message and assert the provider does not error.

## Test commands

- `pytest <new_test_file> -q -m openrouter`

## Acceptance criteria

- A single AgentApplication config can load both OpenRouter provider plugin sets (chat + responses) with no config errors.
- Running the reasoning+tools loop for each agent uses the correct provider/extension set (no cross-activation).
- For both agents, delete and slice operations maintain native/core integrity and a follow-up request succeeds.
