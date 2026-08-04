# Gemini-Compatible Persistent Subagent Tools

Implement the inspected Gemini CLI specialist-as-tool behavior on top of the shared persistent subagent runtime, extending shared functionality only where the Gemini implementation proves it reusable.

## Requirements checklist

- [ ] Capture the inspected Gemini specialist tool schemas, descriptions, argument behavior, outputs, and errors in contract fixtures or equivalent tests.
- [ ] Generate one model-facing tool per configured specialist as required by the upstream behavior.
- [ ] Run each invocation in a persisted child application session configured with the selected agent.
- [ ] Preserve blocking invocation behavior and configured execution limits.
- [ ] Preserve the expected completion contract and final consolidated result.
- [ ] Keep child tools/configuration isolated according to the configured child agent.
- [ ] Stream child thought/tool activity through the tool invocation where supported and expected.
- [ ] Reuse shared persistence, request exclusivity, idempotency, blocking-run, and restart behavior.
- [ ] Keep Gemini-specific dynamic naming, schemas, prompts, completion rules, formatting, and errors in `gemini-tools`.
- [ ] Add shared limit/completion abstractions only if they are vendor-neutral and already needed by more than one adapter or clearly belong to execution mechanics.
- [ ] Add deterministic unit, application integration, and restart tests.

Parent Task: `tasks/20260715-persistent-plugin-subagents/000-main.md`

Depends On: `tasks/20260715-persistent-plugin-subagents/040-kimi-compatible-subagent-tools.md`

## Upstream references

- `../gemini-cli/packages/core/src/agents/subagent-tool.ts`
- `../gemini-cli/packages/core/src/agents/local-invocation.ts`
- `../gemini-cli/packages/core/src/agents/local-executor.ts`
- `../gemini-cli/packages/core/src/services/chatRecordingService.ts`

Gemini exposes configured specialists as separate tool names. The shared runtime must not contain those generated schemas or specialist selection descriptions.

## Scope constraints

- Do not replace Gemini's named specialist tools with a generic Codex-style target parameter.
- Do not make child-agent recursion available unless it is explicitly part of the selected supported upstream behavior and approved configuration.
- Do not add new session-list filtering; child sessions remain visible.
- No new UI is required.

## Verification

- Dynamic schema generation for multiple configured specialists.
- Correct dispatch to each configured child agent.
- Child tool isolation and execution limits.
- Persistent visible child session after completion.
- Restart of an interrupted blocking invocation without duplicate child creation.
- Contract-compatible final tool result.