# 050 - Vendor-Friendly System Message Extraction

Short description: Investigate the default system messages used by Gemini CLI, Qwen Code, and Grok CLI, then extract the information, prompt structure, and template skeletons needed so a later agent can manually reconstruct equivalent system messages in this platform. This task is about research, extraction, and documentation, not about implementing new feature behavior.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On: None

## Goal

Produce a handoff-quality extraction package for Gemini-like, Qwen-like, and Grok-like system messages.

The purpose of this task is to gather enough information that a later agent can:

1. manually assemble equivalent system messages in this platform
2. create sample prompt templates with placeholders for dynamic sections
3. write richer user-facing documentation describing how those dynamic sections should be computed
4. identify future feature/plugin work that would be needed for higher-fidelity parity

Important scope boundary:

1. This task is not about extending the current `feature-system-message` plugin.
2. This task is not about implementing new runtime prompt-generation features.
3. This task is not about wiring new system-message behavior into the application.

Instead, it should extract and document the source material thoroughly enough that later implementation work becomes straightforward.

## Key source references

### Gemini CLI

- Prompt entrypoint:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/core/prompts.ts:21`
- Prompt builder:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/prompts/promptProvider.ts:36`
- Modern prompt composition:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/prompts/snippets.ts:95`
- Core preamble and mandates:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/prompts/snippets.ts:140`
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/prompts/snippets.ts:147`
- Workflow, operational, sandbox, git, memory sections:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/prompts/snippets.ts:287`
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/prompts/snippets.ts:314`
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/prompts/snippets.ts:351`
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/prompts/snippets.ts:386`
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/prompts/snippets.ts:408`
- Representative rendered modern prompt snapshot:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/core/__snapshots__/prompts.test.ts.snap:3374`

### Qwen Code

- Main system prompt implementation:
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/core/prompts.ts:102`
- Base prompt body:
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/core/prompts.ts:138`
- Dynamic sandbox/git/tool-call-example appendices:
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/core/prompts.ts:269`
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/core/prompts.ts:292`
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/core/prompts.ts:314`
- Tool-call example variants:
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/core/prompts.ts:439`
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/core/prompts.ts:515`
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/core/prompts.ts:672`
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/core/prompts.ts:771`
- Prompt tests showing model-specific tool-call examples:
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/core/prompts.test.ts:280`
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/core/prompts.test.ts:300`
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/core/prompts.test.ts:322`

### Grok CLI

- Main system message construction:
  - `/Users/ferenci84/Dev/Mine/grok-cli/src/agent/grok-agent.ts:81`
- Base system message content:
  - `/Users/ferenci84/Dev/Mine/grok-cli/src/agent/grok-agent.ts:87`
- Custom instructions injection:
  - `/Users/ferenci84/Dev/Mine/grok-cli/src/agent/grok-agent.ts:82`

### Current platform system-message support and limits

- Existing feature plugin:
  - `plugins/feature-system-message/src/feature_system_message/system_message_feature.py:1`
- Current behavior and limits:
  - `plugins/feature-system-message/src/feature_system_message/system_message_feature.py:9`
  - `plugins/feature-system-message/src/feature_system_message/system_message_feature.py:22`
  - `plugins/feature-system-message/src/feature_system_message/system_message_feature.py:285`
- Current default config usage:
  - `application/python/agent_terminal_app/default_config.json:15`
- Current application-config docs:
  - `docs/plugins/application-config.md:1`

## Findings to preserve

### Gemini CLI prompt structure is highly compositional and runtime-aware

Gemini does not use one static prompt blob. It composes a prompt from many sections:

1. preamble
2. core mandates
3. sub-agent list
4. skills section
5. hook-context section
6. primary workflow or planning workflow depending on approval mode
7. operational guidelines
8. autonomous/YOLO mode section
9. sandbox section
10. git repository section
11. contextual memory / GEMINI.md content

Important Gemini traits worth preserving in an adapted form:

1. strong emphasis on context efficiency and minimizing unnecessary turns
2. clear distinction between inquiries and directives
3. strong testing and validation expectations
4. explicit instruction precedence for local context files
5. brief, high-signal CLI tone
6. runtime-dependent sections for plan mode, sandbox mode, git, skills, and subagents

Important Gemini traits that cannot be copied literally without adaptation:

1. `GEMINI.md` file naming and hierarchical memory semantics
2. Gemini-specific approval modes and `enter_plan_mode` / `exit_plan_mode`
3. hook-context and skill activation semantics as defined in Gemini CLI
4. assumptions about Gemini's own sub-agent registry and tool list rendering

### Qwen Code prompt is a single large base prompt with several important dynamic appendices

Qwen keeps most of the prompt as one large string and then appends:

1. sandbox instructions
2. git-repo instructions
3. model-specific textual tool-call examples
4. user memory suffix

Important Qwen traits worth preserving in an adapted form:

1. very explicit todo-driven task management expectations
2. concise CLI response style
3. strong path/absolute-path emphasis
4. strong instructions about explaining destructive shell commands before running them
5. strong expectations around build/lint/typecheck verification
6. practical workflow examples for implementation tasks

Important Qwen traits that should likely be adapted or omitted:

1. model-specific textual tool-call syntax examples for `qwen-coder`, `qwen-vl`, and generic models
2. examples that assume Qwen's exact tool names or parameter names when those differ from the configured plugin set
3. references to Qwen-specific memory file layout and interaction details that do not exist here

Note for implementation:

This platform already supports native tool calling. The Qwen textual tool-call examples may be unnecessary or actively confusing for providers that already receive tool schemas natively. Any attempt to preserve them should be conditional and deliberate.

### Grok CLI prompt is simpler and more directly tool-oriented

Grok's default system message is compact compared with Gemini and Qwen.

Important Grok traits worth preserving in an adapted form:

1. direct tool-oriented instructions
2. simple edit/read/create workflow guidance
3. concise, efficient response style
4. explicit emphasis on using the todo list for complex work
5. visible current working directory

Important Grok traits that must be conditional or adapted:

1. claims about automatic real-time web/X access
2. confirmation UX wording that assumes Grok's own confirmation UI
3. exact tool inventory, especially `search` and optional `edit_file`

### The current platform already has a system-message feature, but this task should treat it only as context, not as the implementation target

The existing `feature-system-message` plugin can:

1. inject a configured default system message
2. use a string template
3. interpolate variables from inline text, files, or Python code

But in its current form it does not cleanly model large runtime-aware prompt builders such as:

1. available tool list derived from the actual loaded plugin set
2. git-repository detection
3. sandbox-mode detection with different wording
4. provider/model-sensitive prompt branches
5. vendor-specific prompt sections that should appear only when certain tools are enabled

That means this task should not be framed as "just write three static prompt strings in JSON config".

It also means this task should document where the current platform falls short so a future agent can decide whether to:

1. keep the reconstructed prompts manual and static
2. add placeholders computed externally
3. build new feature support later

## Required output shape for this task

The completing agent should deliver extracted material, not code-driven behavior.

At minimum the handoff should contain:

1. a Gemini template skeleton
2. a Qwen template skeleton
3. a Grok template skeleton
4. a per-vendor inventory of dynamic sections and how they are computed upstream
5. explicit notes about which upstream sections can be copied nearly verbatim, which need placeholders, and which should be omitted or rewritten in this platform
6. pointers to the exact upstream source files and functions that define each section
7. follow-up notes describing which future plugin or feature work would improve parity

### Preferred extraction format

The extracted material should preferably be organized as:

1. a human-readable research/task document in this task file or linked companion docs
2. one or more sample template files with placeholders such as:
   - `{{AVAILABLE_TOOLS}}`
   - `{{SANDBOX_SECTION}}`
   - `{{GIT_SECTION}}`
   - `{{WORKING_DIRECTORY}}`
   - `{{CONTEXT_FILES_SECTION}}`
   - `{{MODEL_TOOL_CALL_EXAMPLES}}`
3. a short "dynamic elements guide" that explains how each placeholder should be calculated

The goal is for a later agent to be able to take those templates and either:

1. render them manually for a concrete agent setup, or
2. implement a proper system-message feature later with minimal rediscovery.

## Recommended extraction direction

### What to extract directly

Extract the stable, reusable sections of the upstream prompts in near-template form.

Examples:

1. Gemini core mandates wording
2. Gemini workflow section structure
3. Qwen core prompt body and workflow examples
4. Grok tool-usage rules and concise behavioral guidance

### What to convert into placeholders

Convert runtime-dependent sections into explicit placeholders with calculation notes.

Examples:

1. available tools or tool names
2. subagent and skill listings
3. sandbox mode sections
4. git repository sections
5. working-directory insertion
6. memory/context-file sections
7. model-dependent Qwen tool-call examples

### What to mark as future-feature candidates

For sections that cannot be reconstructed cleanly with static templates alone, the task should document them as future-feature candidates rather than trying to solve them now.

Examples:

1. Gemini plan-mode-specific sections
2. Gemini hook-context and activated-skill sections
3. Qwen model-sensitive tool-call-example switching
4. Grok capability-conditional claims such as real-time web/X access
5. any section that depends on exact runtime tool inventory or platform capabilities

## Reconstruction guidance to include

For each vendor, the extracted output should answer these questions:

1. What is the high-level structure of the system message?
2. Which sections are static enough to copy?
3. Which sections need placeholders?
4. What inputs are required to fill those placeholders?
5. Which sections should be dropped in this platform because they would be misleading?
6. Which sections point to future plugin or feature work if we want closer parity?

### Suggested per-vendor reconstruction notes

#### Gemini

The extraction should preserve:

1. section order
2. tone and framing
3. inquiry-vs-directive language
4. context-efficiency emphasis
5. testing/validation expectations

The extraction should mark these as placeholders or future work:

1. available subagents
2. available skills
3. hook-context support
4. plan-mode sections
5. contextual instruction file naming and hierarchy

#### Qwen

The extraction should preserve:

1. main base prompt body
2. todo-heavy workflow expectations
3. concise CLI style
4. verification and shell-safety guidance

The extraction should mark these as placeholders or future work:

1. sandbox section
2. git section
3. tool-call examples by model family
4. memory suffix

Special note to preserve:

Qwen's textual tool-call examples may not belong in the final reconstructed prompt for all providers here. The extraction should still document them carefully and explain when they might be useful versus when they should be omitted.

#### Grok

The extraction should preserve:

1. compact base instruction style
2. direct tool-usage rules
3. edit/read/create workflow guidance
4. todo-list guidance
5. concise response guidance

The extraction should mark these as placeholders or future work:

1. custom instructions insertion
2. actual tool inventory
3. capability-conditional claims about search/web access
4. current working directory insertion
5. confirmation-flow wording if it differs from our platform's actual UX

## Deliverables

1. A written breakdown of Gemini, Qwen, and Grok default system-message structure.
2. A reusable template skeleton for each vendor with explicit placeholders for dynamic content.
3. A mapping from each placeholder to the upstream source code or prompt section that defines it.
4. A short guide explaining how each dynamic element should be calculated.
5. Notes about which sections can be used directly, which should be adapted, and which should be omitted.
6. A future-work list for plugin/feature capabilities that would improve parity, without implementing them.
7. If helpful, standalone sample template files or markdown snippets that a later agent can use immediately.

## Not in scope

1. Extending `feature-system-message`.
2. Adding new system-message runtime features.
3. Wiring new prompt presets into config or application logic.
4. Implementing placeholder resolution beyond documenting how it should work.
5. Building the future parity features themselves.

## Recommended execution direction for the completing agent

1. Read the upstream prompt-builder files and prompt snapshots.
2. Split each vendor prompt into sections.
3. Classify each section as:
   - static reusable text
   - placeholder-backed text
   - future-feature-dependent text
   - omit/rewrite for this platform
4. Produce vendor template skeletons using placeholders.
5. Document each placeholder with enough detail that another agent can compute it later.
6. Optionally create companion sample docs or template files if that makes the handoff clearer.

## Useful companion outputs to consider

The completing agent may decide to create additional non-code artifacts such as:

1. `docs/prompt-extraction/gemini-system-message-template.md`
2. `docs/prompt-extraction/qwen-system-message-template.md`
3. `docs/prompt-extraction/grok-system-message-template.md`
4. `docs/prompt-extraction/dynamic-elements-guide.md`

These are optional, but they would likely make later implementation easier.
## Recommended parity target

Aim for "adapted parity" rather than literal parity.

That means:

1. preserve the vendor's tone, priorities, and major workflow guidance
2. preserve vendor-specific sections when they map naturally to this platform
3. adapt tool references to the actually configured plugin/tool surface
4. omit or rewrite prompt sections that would be false or misleading in this platform

Examples:

1. Gemini-style context-efficiency and inquiry-vs-directive language should be preserved.
2. Qwen-style todo discipline and verification guidance should be preserved.
3. Grok-style direct tool workflow guidance should be preserved.
4. Qwen textual tool-call examples should likely be omitted unless a provider-specific mode really needs them.
5. Grok's "real-time web search and X data" claim should only appear if the configured tools really provide that capability.

## Documentation expectations

This task should produce documentation-quality extraction notes, not user-facing runtime configuration docs.

Useful documentation outputs include:

1. vendor template skeletons
2. dynamic-elements guide
3. section-by-section parity notes
4. future-feature candidates for higher fidelity

If the completing agent adds companion docs, they should be framed as reconstruction references rather than end-user setup instructions.

## Execution Plan Added During Completion

Added on 2026-03-16 after user approval.

1. Reorganize the existing Codex instruction archive from `docs/codex-default-instructions/` into the shared vendor layout under `docs/default-system-instructions/codex/`, preserving the extracted model files while making the top-level structure vendor-oriented.
2. Read the upstream Gemini, Qwen, and Grok prompt-builder sources and split each vendor's system prompt into named sections with exact upstream source references.
3. Create dedicated vendor directories under `docs/default-system-instructions/`:
- `docs/default-system-instructions/gemini/`
- `docs/default-system-instructions/qwen/`
- `docs/default-system-instructions/grok/`
4. For each vendor directory, add multiple smaller artifacts for readability:
- one template skeleton file
- separate files for static sections that can be reused nearly verbatim
- one vendor-specific dynamic-elements guide
- one vendor-specific reconstruction/parity notes file tying placeholders back to upstream logic
5. Keep this subtask documentation-only: do not change runtime system-message behavior or extend `feature-system-message`.
6. Add lightweight regression tests that verify the new documentation structure exists and that each vendor directory contains the expected template and dynamic-guide artifacts.
7. Run the relevant test slice, then append completion notes to this task file summarizing files touched, test results, and any remaining parity caveats.

## Completion Notes Added During Completion

Added on 2026-03-16 after implementation and verification.

### What changed

1. Created a new shared documentation root at `docs/default-system-instructions/` and moved the existing Codex instruction archive into `docs/default-system-instructions/codex/`.
2. Added a Gemini extraction set under `docs/default-system-instructions/gemini/` with:
- `template.md`
- `static-preamble.md`
- `static-core-mandates.md`
- `static-operational-guidelines.md`
- `dynamic-elements.md`
- `reconstruction-notes.md`
3. Added a Qwen extraction set under `docs/default-system-instructions/qwen/` with:
- `template.md`
- `static-introduction-and-core-mandates.md`
- `static-task-management.md`
- `static-primary-workflows.md`
- `static-operational-guidelines.md`
- `dynamic-elements.md`
- `reconstruction-notes.md`
4. Added a Grok extraction set under `docs/default-system-instructions/grok/` with:
- `template.md`
- `static-introduction.md`
- `static-tool-usage-rules.md`
- `static-workflow-and-response-guidance.md`
- `dynamic-elements.md`
- `reconstruction-notes.md`
5. Added a top-level `docs/default-system-instructions/README.md` describing the vendor-oriented layout and intent.
6. Added a focused docs regression test in `core/python/tests/test_default_system_instructions_docs.py` to verify the new directory layout, required artifacts, and the Codex archive move.

### Files touched

1. New documentation root:
- `docs/default-system-instructions/README.md`

2. Codex archive move and small README update:
- `docs/default-system-instructions/codex/README.md`
- all previously existing Codex extracted model files now live under `docs/default-system-instructions/codex/`

3. Gemini extraction docs:
- `docs/default-system-instructions/gemini/README.md`
- `docs/default-system-instructions/gemini/template.md`
- `docs/default-system-instructions/gemini/static-preamble.md`
- `docs/default-system-instructions/gemini/static-core-mandates.md`
- `docs/default-system-instructions/gemini/static-operational-guidelines.md`
- `docs/default-system-instructions/gemini/dynamic-elements.md`
- `docs/default-system-instructions/gemini/reconstruction-notes.md`

4. Qwen extraction docs:
- `docs/default-system-instructions/qwen/README.md`
- `docs/default-system-instructions/qwen/template.md`
- `docs/default-system-instructions/qwen/static-introduction-and-core-mandates.md`
- `docs/default-system-instructions/qwen/static-task-management.md`
- `docs/default-system-instructions/qwen/static-primary-workflows.md`
- `docs/default-system-instructions/qwen/static-operational-guidelines.md`
- `docs/default-system-instructions/qwen/dynamic-elements.md`
- `docs/default-system-instructions/qwen/reconstruction-notes.md`

5. Grok extraction docs:
- `docs/default-system-instructions/grok/README.md`
- `docs/default-system-instructions/grok/template.md`
- `docs/default-system-instructions/grok/static-introduction.md`
- `docs/default-system-instructions/grok/static-tool-usage-rules.md`
- `docs/default-system-instructions/grok/static-workflow-and-response-guidance.md`
- `docs/default-system-instructions/grok/dynamic-elements.md`
- `docs/default-system-instructions/grok/reconstruction-notes.md`

6. Tests:
- `core/python/tests/test_default_system_instructions_docs.py`

7. Task tracking:
- `tasks/20260315-gemini-qwen-grok-tool-packages/050-vendor-friendly-system-messages.md`

### Tests run

1. `pytest core/python/tests/test_default_system_instructions_docs.py -q`

### Outcomes

1. The focused docs regression test passed.
2. The new extraction layout now matches the requested vendor directory structure.
3. Codex has been moved into the same vendor-oriented documentation tree.

### Remaining parity caveats

1. The Gemini, Qwen, and Grok files intentionally target adapted parity rather than literal runtime parity.
2. High-fidelity runtime behaviors such as Gemini plan mode, Qwen model-sensitive example switching, and Grok capability-conditional claims still require future rendering logic if they are to be automated.
3. The new test validates document presence and key placeholders, not the semantic completeness of the extracted text.

## Addendum Added During Completion

Added on 2026-03-16 after follow-up user direction about human usability.

The vendor directories were then reshaped further for copy-paste-first human use:

1. `template.md` files are now raw top-level prompt text with section placeholders only, without explanatory wrappers.
2. Section files now favor raw prompt text that can be pasted directly into a compiled instruction.
3. Each vendor now includes `compiled.md` as a worked example with placeholders already substituted.
4. Each vendor now includes `agent-notes.md` for deeper research and future automation guidance.
5. `dynamic-elements.md` files were rewritten to explain each placeholder by example rather than only by source mapping.
6. Relative source references are now concentrated in `agent-notes.md` instead of using absolute filesystem paths in the vendor research notes.