# Test And Build Command Alignment

Align package-level pytest marker declarations, default command behavior, and documented build/test commands so that everyday verification is safe by default and major provider-plugin surfaces are explicitly covered when needed.

## Requirements checklist

- [ ] Align pytest marker declarations across core, application, and major provider plugin packages.
- [ ] Decide whether package-level default pytest behavior should exclude integration suites in more places.
- [ ] Update documented standard commands to match the actual package behavior.
- [ ] Ensure provider plugin packages used for major-change verification are explicitly covered.
- [ ] Record any command changes that may affect existing local habits or CI workflows.

Parent Task: `tasks/20260524-test-and-agents-cleanup/000-main.md`

Depends On: `tasks/20260524-test-and-agents-cleanup/010-test-markers-env-and-standard-runs.md`

## Why this is separate from the marker/env policy subtask

Subtask 010 defines the desired semantics. This subtask is about turning those semantics into concrete command and config behavior without surprising developers or breaking existing flows accidentally.

## Current package command behavior

### Core

- `core/python/pyproject.toml:46-56`
- Already excludes `integration` by default.
- This makes `pytest core/python/tests -q` relatively safe as a fast verification command.

### Application

- `application/python/pyproject.toml:53-60`
- Declares markers but does not exclude `integration` or `docker` by default.
- Current broad command in root docs, `pytest application/python/tests -q`, can include:
  - hosted API tests
  - Ollama integration tests
  - Docker-marked tests if selected broadly enough elsewhere

### OpenRouter plugin package

- `plugins/openrouter/pyproject.toml:37-43`
- Declares only `integration` and `openrouter`
- No current declaration for `api` or `slow_integration`

### OpenAI Responses plugin package

- `plugins/openai_responses/pyproject.toml:40-46`
- Declares `integration`, `openai`, `manual_integration`
- No current `api` or `slow_integration`

### Reference OpenAI-compatible provider package

- `plugins/reference-openai-compatible-provider/pyproject.toml:40-44`
- Declares `integration`, `fireworks`, `zai`, `ollama`
- No current `api` or `slow_integration`

## Important implementation decision

The implementing agent will likely need to choose between two approaches:

### Option A: safer package defaults

Add default exclusion behavior such as `-m 'not integration'` to more packages.

Pros:

- safer default local runs
- docs and actual default behavior stay closer together

Cons:

- can change developer expectations
- may affect CI or existing package-local commands if they rely on broad defaults

### Option B: keep package defaults broad, standardize only docs/commands

Pros:

- lower behavior-change risk
- less chance of disrupting existing automation

Cons:

- easier for contributors to accidentally run slow/billable suites
- root guidance remains more dependent on remembering the right command

This choice should be recorded clearly if implementation proceeds.

## Provider packages the command story must cover

For major provider-facing or request-pipeline changes, the final command guidance should explicitly mention follow-up verification in:

- `plugins/openrouter`
- `plugins/openai_responses`
- `plugins/reference-openai-compatible-provider`

This was a direct user requirement.

## Candidate command cleanup items

- Add `api` and `slow_integration` markers to package marker declarations.
- Consider package-local fast commands in READMEs or AGENTS docs where appropriate.
- Update root `AGENTS.md` to stop recommending broad example or application test commands without caveats.
- If needed, add or update package README testing sections for:
  - `plugins/openrouter`
  - `plugins/openai_responses`
  - `plugins/reference-openai-compatible-provider`

## Build-command angle

The user asked for test/build command cleanup, but current research so far is much more test-command-heavy than build-command-heavy. The implementing agent should:

- verify whether any packaging/build commands in docs conflict with the new testing guidance
- only broaden scope into build tooling if a real inconsistency is found
- avoid inventing build cleanup work that is not justified by the current findings

## Relevant files to review during implementation

- `AGENTS.md`
- `core/python/pyproject.toml`
- `application/python/pyproject.toml`
- `plugins/openrouter/pyproject.toml`
- `plugins/openai_responses/pyproject.toml`
- `plugins/reference-openai-compatible-provider/pyproject.toml`
- package README files if command guidance is duplicated there

## Success criteria

- A contributor can tell which command to run for fast local verification versus hosted API verification without reading a large block of prose.
- Package marker declarations support the documented command matrix.
- The command story explicitly handles slow integration suites instead of burying them inside generic integration runs.