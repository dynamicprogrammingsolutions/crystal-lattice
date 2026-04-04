# 013 — True `apply_patch` parity with Codex CLI

Implement real upstream Codex CLI-style `apply_patch` behavior after the core prerequisite exists, using provider-capability-based schema selection plus shell-tool interception instead of model-dependent exposure.

## Requirements checklist

- [x] Expose `apply_patch` by provider capability: freeform/custom when the active provider path supports custom tools, function fallback with `input` otherwise.
- [x] Add shell-tool interception for `apply_patch` behind config so users can disable the dedicated tool plugin and still edit via shell.
- [x] Update tests and docs to cover the final parity behavior, including real API coverage for OpenAI Responses and OpenRouter.

Parent Task: `tasks/20260225-codex-tools-parity/000-main.md`
Depends On: `tasks/20260225-codex-tools-parity/011-shell-selection-parity.md`, `tasks/20260225-codex-tools-parity/012-core-freeform-tool-prerequisite.md`

## Why this task exists

The original `010` scope was too small. Upstream Codex CLI does not primarily treat `apply_patch` as a function tool with an `input` parameter for GPT-5 models; it primarily uses a freeform/custom tool and only keeps the JSON/function form as a fallback.

So the real parity task must include:

- the freeform/custom tool path
- the JSON/function fallback shape with `input`
- a shell-interception fallback path for models using shell editing flows

## Findings to preserve

### 1) Upstream freeform is the primary GPT-5 path

Upstream factories:

- freeform/custom tool: `../codex/codex-rs/core/src/tools/handlers/apply_patch.rs:288-299`
- JSON/function fallback: `../codex/codex-rs/core/src/tools/handlers/apply_patch.rs:302-389`

The upstream comment explicitly says the JSON/function tool should only be used with `gpt-oss` models.

### 2) Upstream tool registration is model-config driven

Codex CLI registers `apply_patch` only when `config.apply_patch_tool_type` is present, and then chooses freeform vs function from that value:

- `../codex/codex-rs/core/src/tools/spec.rs:1914-1923`

Important examples from current upstream model metadata:

- `gpt-5.4` -> `apply_patch_tool_type = "freeform"` at `../codex/codex-rs/core/models.json:81-117`
- `gpt-5.2` -> `apply_patch_tool_type = "freeform"` at `../codex/codex-rs/core/models.json:359-395`
- `gpt-5.1` -> `apply_patch_tool_type = "freeform"` at `../codex/codex-rs/core/models.json:427-459`
- `gpt-5` -> `apply_patch_tool_type = null` at `../codex/codex-rs/core/models.json:555-591`

### 3) Our current implementation is still a `patch_text` function tool

Current local implementation:

- `plugins/codex-tools/src/codex_tools/apply_patch_tool.py:501-694`
- `plugins/codex-tools/tests/test_apply_patch_tool.py`

Current behavior differences:

- structured arg name is `patch_text`, not `input`
- there is no freeform/custom tool path
- the tool is not yet aligned with upstream model gating

## Desired outcome

After this task:

- provider paths that support custom tools expose a freeform/custom `apply_patch` tool here too
- OpenAI-compatible chat-completions paths use a function fallback with `input` as the sole structured field, with no alias parameters
- shell tools can optionally intercept `apply_patch` heredocs and route them to the same internal patch runtime
- execution, previews, results, docs, and integration tests all reflect the final parity behavior

## Implementation notes

This task should absorb the schema cleanup that was originally imagined for `010`.

Specifically:

- do not create a separate intermediate task just to rename `patch_text` -> `input`
- perform that rename only as part of the final parity implementation
- if both freeform and function fallback are supported, keep their descriptions aligned with upstream intent while selecting between them by provider capability

Likely implementation areas:

- `plugins/codex-tools/src/codex_tools/apply_patch_tool.py`
- `plugins/codex-tools/src/codex_tools/model_family.py`
- `plugins/codex-tools/tests/test_apply_patch_tool.py`
- `plugins/codex-tools/README.md`
- any provider/tool-interop plumbing completed in `012`

## Test expectations

- Add tests for freeform/custom `apply_patch` on provider paths that support custom tools.
- Add tests for the function fallback shape using `input` only.
- Add tests for shell interception with `disabled_plugins` plus the shell interception config enabled.
- Update docs so they describe actual parity behavior rather than the old `patch_text` schema.

## Execution plan

Added during completion planning.

### Goal

Implement true `apply_patch` behavior parity on top of the `012` interop work, but with one deliberate local policy change:

- do not gate `apply_patch` exposure by model family
- instead, expose `apply_patch` whenever the plugin is enabled and the active provider path can carry it
- add a shell-tool config flag that intercepts shell-side `apply_patch` invocations and routes them to the same internal patch implementation

This gives three supported routes:

- dedicated freeform/custom `apply_patch` tool when the provider path supports custom tools
- dedicated function fallback when the provider path only supports function tools
- shell interception fallback when configured, even if the dedicated `apply_patch` tool is disabled

### Provider-capability rules

Tool exposure should be provider-capability-dependent, not model-dependent.

Decision rule:

1. Ask the effective provider/extension path which tool schema formats it accepts.
2. If it accepts `openai.responses.custom.tool_schema`, expose the freeform/custom `apply_patch` schema.
3. Else if it accepts a function schema format, expose the function fallback with `input` as the sole field.
4. Else expose no dedicated `apply_patch` tool and rely on shell interception if configured.

Practical examples in this repo:

- `openrouter_responses` / `openai_responses` should use the freeform/custom path.
- `openrouter` on the OpenAI-compatible chat-completions path should use the function fallback path.

This is independent of shell interception. If the user disables the `apply_patch` plugin with `disabled_plugins`, neither dedicated path is exposed, but shell interception may still provide the behavior when enabled in shell config.

### Main implementation steps

#### 1) Extract shared patch application helpers

Refactor `plugins/codex-tools/src/codex_tools/apply_patch_tool.py` so the actual patch parsing, validation, sandboxing, and file application logic can be called from both:

- the dedicated `ApplyPatchTool`
- shell interception code in the shell tools

The goal is to avoid duplicating patch semantics and to keep both routes behaviorally identical.

Expected shape:

- shared helper functions or a small internal runtime module
- a thin `ApplyPatchTool` wrapper that only handles schema exposure, payload extraction, and result formatting

#### 2) Make `ApplyPatchTool` provider-aware, not model-aware

Update `ApplyPatchTool.get_tool_schemas(...)` so it no longer checks model family at all.

Instead:

- inspect the effective provider target formats via the `012` interop plumbing already injected into config/state
- emit a Responses-native custom/freeform schema when custom tools are supported
- otherwise emit the function fallback schema using `input`
- if neither schema family is supported, expose no dedicated schema

#### 3) Implement the real freeform/custom schema

Make the primary dedicated tool schema mirror upstream Codex intent:

- `type: "custom"`
- `name: "apply_patch"`
- description that explicitly says it is a freeform tool and not to wrap the patch in JSON
- `format` using grammar / lark

Prefer storing the grammar in a nearby `.lark` asset if that keeps maintenance easier; embedding it in the module is acceptable if simpler.

#### 4) Replace `patch_text` with `input`

Remove the old `patch_text` field from the structured form.

The structured fallback must use:

- one object field only: `input`
- `additionalProperties: false`

This rename must also flow through:

- preview generation
- execution payload parsing
- result metadata used for display helpers
- tests and README text

Do not keep `patch_text` as a public alias unless implementation friction forces a temporary compatibility shim.

#### 5) Make execution payload-aware

Update `ApplyPatchTool` so it accepts both:

- raw string payloads for freeform/custom calls
- object payloads with `input` for function fallback calls

Internally both should normalize to one patch-text variable before validation and application.

Apply the same logic to `format_tool_call_preview(...)`.

#### 6) Add `can_handle_tool_call(...)`

Implement tool-side routing so `ApplyPatchTool` can claim calls based on:

- `tool_name == "apply_patch"`
- compatible payload kind / payload shape

This keeps the tool aligned with the post-`012` routing model and reduces dependence on pure schema-name matching.

#### 7) Add shell interception config

Introduce a shell-tool config flag, for example `intercept_apply_patch`, used by the Codex shell tools.

Behavior:

- when `false`, shell tools behave normally
- when `true`, shell-side `apply_patch` invocations are detected and routed internally to the shared patch implementation

The exact config key may be adjusted if there is a stronger naming convention in `codex-tools`, but the behavior should remain the same.

#### 8) Define and implement shell interception parsing

Add focused logic that detects Codex-style shell invocations of `apply_patch` and extracts the patch body.

The parser only needs to support the shell forms we actually expect from the GPT-5 shell path. It does not need to become a general shell parser.

The interception code should live in a helper, not inline in both shell tool implementations.

#### 9) Route shell interception directly to shared patch helpers

The shell interception path should call the extracted internal patch helpers directly, not re-enter the public tool wrapper.

That ensures interception still works even when the `apply_patch` tool plugin is disabled.

It must use the shell tool's effective:

- working directory
- allowed-path sandbox rules
- size limits where appropriate

#### 10) Support the shell-only configuration intentionally

Target supported config pattern:

- disable `apply_patch` via `disabled_plugins`
- enable shell interception in shell config
- allow the model to edit files by issuing `apply_patch` through the shell tool

This should be documented and tested explicitly.

### Test plan

#### Tool-level tests

Update `plugins/codex-tools/tests/test_apply_patch_tool.py` to cover:

- freeform/custom schema exposure
- function fallback schema exposure with `input`
- freeform execution from raw string payload
- function fallback execution from `{"input": patch}`
- preview generation for both payload forms
- display payload still includes the original patch text for humans
- old `patch_text` usage removed from public tests

#### Shell interception tests

Add focused shell-tool tests for:

- interception disabled: normal shell behavior
- interception enabled + non-patch command: normal shell behavior
- interception enabled + `apply_patch` shell invocation: patch is applied through shared helpers
- interception still works when the dedicated `apply_patch` tool is disabled from config

#### Provider-path tests

Add coverage showing capability-based schema selection:

- Responses-capable provider path gets the custom/freeform schema
- OpenAI-compatible chat-completions provider path gets the function fallback with `input`

This may live in `codex-tools` tests or a provider-side unit test depending on the cleanest fixture setup.

#### Real application-level integration coverage for GPT-5 mini shell fallback

Add real API application-level integration tests proving that a `gpt-5-mini` agent can modify a file through the shell tool when asked to do so.

Use application-level tests so the configuration path is exercised as part of the test, including:

- the dedicated `apply_patch` tool disabled via `disabled_plugins`
- shell interception enabled in config
- the model using the shell tool to issue an `apply_patch` command
- the shell tool intercepting that call and routing it to the patch implementation
- the target file actually being modified

Do not mock the provider for this coverage.

Required provider coverage:

- one real API application-level integration test on the OpenAI Responses package/provider path
- one real API application-level integration test on the OpenRouter package/provider path

Model selection for this shell-fallback coverage:

- use only the mini variant
- use `gpt-5-mini` on the OpenAI Responses side
- use `openai/gpt-5-mini` on the OpenRouter side

#### Real-provider integration coverage for dedicated `apply_patch`

Also add real API integration coverage for the dedicated `apply_patch` tool path on newer GPT-5.x models.

Preferred model target:

- `gpt-5.4-mini`
- use `openai/gpt-5.4-mini` when testing through OpenRouter

Coverage expectations:

- include at least one real-provider integration on an OpenAI Responses path using the dedicated `apply_patch` tool
- include at least one real-provider integration on an OpenRouter provider path using the dedicated `apply_patch` tool
- ensure the newer GPT-5.1+ family is covered by integration tests, with `gpt-5.4-mini` preferred as the representative model

These tests should verify that the model can actually call the dedicated `apply_patch` tool and modify a file, not just that the schema is exposed locally.

Implementation notes for these live tests:

- gate them with the appropriate provider markers / API-key environment requirements
- keep them narrow and deterministic
- prefer direct file-edit assertions over broad conversational assertions
- keep this dedicated-tool coverage separate from the `gpt-5-mini` shell-interception coverage above

### Docs updates

Update `plugins/codex-tools/README.md` so it reflects the final behavior:

- `apply_patch` uses a freeform/custom schema when the provider path supports it
- otherwise it falls back to a structured function schema using `input`
- shell tools can optionally intercept `apply_patch` invocations via config
- users can disable the dedicated `apply_patch` tool with `disabled_plugins` and rely on shell interception instead
- remove stale references to `patch_text` and any outdated model-based `apply_patch` claims

### Likely files to change

- `plugins/codex-tools/src/codex_tools/apply_patch_tool.py`
- `plugins/codex-tools/src/codex_tools/shell_tool.py`
- `plugins/codex-tools/src/codex_tools/shell_command_tool.py`
- a new shared helper module under `plugins/codex-tools/src/codex_tools/` for interception and/or patch runtime reuse
- `plugins/codex-tools/tests/test_apply_patch_tool.py`
- shell-tool test files under `plugins/codex-tools/tests/`
- one integration test for shell interception through a GPT-5 shell path
- `plugins/codex-tools/README.md`

### Notes for implementation

- Keep shell-selection parity work separate from this task unless code sharing makes a small reuse convenient.
- Do not reintroduce model-dependent `apply_patch` gating.
- Reuse the `012` interop additions rather than adding provider-specific one-offs for custom tools.
- Make the shell interception path depend only on shell config and shared patch helpers, not on whether the `apply_patch` tool itself is enabled.

## Completion Notes

Added during implementation completion.

- Extracted the shared `apply_patch` parser/runtime/helpers into `plugins/codex-tools/src/codex_tools/apply_patch_runtime.py` and rewrote `plugins/codex-tools/src/codex_tools/apply_patch_tool.py` as a thin provider-aware wrapper.
- The dedicated tool now chooses its schema by provider capability, not model family: custom/freeform for Responses-capable paths, function fallback with `input` for chat-completions paths, and no `patch_text` alias.
- Added shell interception via `intercept_apply_patch` in the Codex shell tools so `apply_patch` can still work when the dedicated plugin is disabled with `disabled_plugins`.
- Updated core/tool init plumbing so tools receive provider schema-target hints during `init()`, and taught the OpenAI/OpenRouter chat-completions tool extensions to advertise their accepted chat-function format.
- Added unit coverage for schema selection, payload handling, shell interception, and provider-capability-driven schema exposure through `AgentCore`.
- Added real API integration coverage:
  - OpenAI Responses: `gpt-5-mini` shell interception path and `gpt-5.4-mini` dedicated `apply_patch` path.
  - OpenRouter: `openai/gpt-5-mini` shell interception path and `openai/gpt-5.4-mini` dedicated `apply_patch` path.
- Updated `plugins/codex-tools/README.md` to describe the provider-capability schema selection and the shell interception fallback.

### Validation run

- `ruff check core/python/agent_core/core.py core/python/plugins/openai_tools_extension.py core/python/tests/test_openai_tools_extension_unit.py plugins/openrouter/src/openrouter_plugins/openrouter_tools_extension.py plugins/openrouter/tests/test_openrouter_tools_extension_unit.py plugins/codex-tools/src/codex_tools/apply_patch_runtime.py plugins/codex-tools/src/codex_tools/apply_patch_tool.py plugins/codex-tools/src/codex_tools/base_shell_tool.py plugins/codex-tools/src/codex_tools/shell_command_tool.py plugins/codex-tools/src/codex_tools/shell_tool.py plugins/codex-tools/tests/test_apply_patch_tool.py plugins/codex-tools/tests/test_shell_command_tool.py plugins/codex-tools/tests/test_shell_tool.py plugins/openai_responses/tests/test_agent_application_openai_responses_apply_patch_real_api.py plugins/openrouter/tests/test_agent_application_openrouter_apply_patch_real_api.py`
- `pytest core/python/tests/test_openai_tools_extension_unit.py plugins/openrouter/tests/test_openrouter_tools_extension_unit.py plugins/codex-tools/tests/test_apply_patch_tool.py plugins/codex-tools/tests/test_shell_command_tool.py plugins/codex-tools/tests/test_shell_tool.py -q`
- `pytest core/python/tests/test_application_layer_integration.py plugins/openai_responses/tests/test_openai_responses_tools_extension_unit.py plugins/openrouter/tests/test_openrouter_provider_unit.py -q`
- `pytest plugins/openai_responses/tests/test_agent_application_openai_responses_apply_patch_real_api.py plugins/openrouter/tests/test_agent_application_openrouter_apply_patch_real_api.py -q`