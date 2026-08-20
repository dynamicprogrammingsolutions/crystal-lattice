# Specialized Task Agents And Real-Model Validation

Specialized task agents are default-config agents designed to complete a narrow
project task reliably. They combine a concise developer/system message, a
task-specific guide in bundled docs, focused tool access, and a real-model test
that proves the agent can complete the task in a realistic fixture.

This pattern is useful when a product feature depends on model behavior, not
only deterministic code. The goal is not to freeze exact model output. The goal
is to verify that the shipped default config gives a capable model enough
context, tools, and documentation to complete the intended workflow.

## Recommended Shape

Add the specialized agent to the default config, not only to a test-local
config. Installed-bundle tests should exercise the same shipped defaults users
receive.

Keep the developer/system message short. It should say what the agent is for,
state important constraints, and point to a bundled guide by absolute path. Put
step-by-step instructions, examples, schemas, and troubleshooting details in the
guide, not in the developer message.

Use config variable substitution for doc paths. For docs shipped in plugins,
prefer paths under `${env:BUILTIN_PLUGINS}` so both source checkouts and
installed bundles can resolve them.

Example structure:

```json
{
  "mixins": {
    "example_task_message": {
      "system_message_enabled": true,
      "system_message": {
        "template": "Read the task guide at `{{TASK_GUIDE_PATH}}` before changing files. Follow the guide workflow, use project docs to infer project-specific details, run cheap checks before final validation, and do not print secrets.",
        "variables": {
          "TASK_GUIDE_PATH": {
            "text": "${env:BUILTIN_PLUGINS}/example-plugin/docs/task-guide.md"
          }
        }
      }
    }
  },
  "agents": {
    "example-task-author": {
      "mixin_refs": ["codex_developer_message", "codex_mcp_defaults", "example_task_message"],
      "provider": "openai",
      "model": "gpt-5.4-mini",
      "allowed_paths": [".", "..", "${env:BUILTIN_PLUGINS}/example-plugin"],
      "plugins": ["path:${env:BUILTIN_PLUGINS}/codex-tools"],
      "shell_tool_mode": "auto"
    }
  }
}
```

For harder fixtures, use a stronger model only in the specific test scenario.
Keep the cheaper model as the shipped default when it is good enough for normal
use.

## Authoring Guide

The guide should include:

- the task goal and expected output files
- the minimum schemas or file formats the agent must generate
- the intended workflow
- fast checks the agent should run before final validation
- examples or references to existing standard implementations
- constraints around secrets, idempotence, generated files, and project-specific
  guidance
- when plugin source may be read as a fallback

For project-specific tasks, tell the agent to read normal project guidance such
as `AGENTS.md`, README files, package manifests, and tests. Do not require the
project guidance to be task-specific; it should remain the ordinary project
setup and testing documentation.

## Installed-Bundle Real-Model Tests

Real-model tests for specialized agents should use the installed bundle when the
feature must work for installed users. The test should:

- extract the bundle archive
- start the bundled CLI/server with the default config
- create a realistic fixture project
- send a generic user request to the specialized agent
- allow only the fixture paths and any bundled docs/source paths the agent may
  need
- override auth/model only through normal config overrides
- assert final outputs and run independent validation after the model stops

The user prompt should stay generic. Project details should live in the fixture
project docs and files. Task mechanics should live in the bundled guide.

When ChatGPT login auth is supported in a test, make it explicit. For example,
use an env var such as `CHATGPT_CREDENTIALS` and set `auth_mode: "chatgpt"` plus
the credentials path in the request overrides. Do not silently fall back from a
requested credential mode to API-key mode.

## Process Telemetry

Capture process-quality signals separately from final pass/fail:

- total tool calls and tool calls by name
- whether the agent read the guide
- whether it read plugin source
- whether it read example tests
- generated files
- syntax checks or cheap local tests attempted
- final validation attempted
- command failures observed

Use both soft and hard budgets:

- soft tool-call limit: warn or report diagnostics, but allow a valid solution
- hard tool-call limit: stop or fail the request
- soft timeout: warn and continue so downstream validation can still be observed
- hard timeout: fail and terminate the run

Soft-budget failures are instruction-tuning signals. Hard-budget failures are
test failures.

## Fixture Design

Fixtures should be small but realistic. Prefer real files, package manifests,
git repositories, and tests over mocked internals. For multi-repository or
multi-service workflows, initialize fixture repositories during test setup and
clean them up through the test temp directory.

The assertion should check behavior, not exact text. Good assertions include:

- required files exist and are executable
- generated JSON matches expected shape
- generated scripts pass shell syntax checks
- a local no-Docker harness passes when custom transfer/setup behavior is
  generated
- the final public validation command passes

Avoid test-only product shortcuts. If the realistic test exposes a product
defect, keep the test realistic and fix the product code or document a follow-up
task.

## Documentation And Completion Notes

When the test exposes model confusion, update the guide first. Keep the
developer message concise and generic. Record observed model behavior in task
completion notes, including tool counts, timeouts, source reads, and remaining
product issues.

If a passing test still exceeds a soft budget, treat it as functionally passing
but performance-suspect. Do not hide product startup or dependency problems by
only raising hard timeouts.