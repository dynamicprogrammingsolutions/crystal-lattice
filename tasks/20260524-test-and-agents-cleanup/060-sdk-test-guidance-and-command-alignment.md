# SDK Test Guidance And Command Alignment

Audit the shared SDK and workspace-package test surfaces under `packages/`, then define the same kind of practical, layered guidance we now have for the main Python test suites: fast/default runs, integration runs, slow or expensive runs, env gates, and contributor-friendly command entrypoints. In this task, “SDK” means the shared workspace packages under `packages/`, not the Python core SDK test cleanup already handled by earlier subtasks.

## Requirements checklist

- [ ] Audit the shared workspace packages under `packages/` for current test scripts, integration scripts, and missing command surfaces.
- [ ] Define simple standard runs for SDK/package work, similar in spirit to the Python guidance.
- [ ] Separate fast/default package tests from integration or expensive test flows.
- [ ] Document env flags and external prerequisites for gated SDK integration flows.
- [ ] Identify packages that currently have tests but weak or missing contributor guidance.
- [ ] Identify packages that have build/runtime significance but no scripts or no test guidance yet.
- [ ] Decide whether any package-local docs should be updated in this task or split into `061+` follow-ups.

Parent Task: `tasks/20260524-test-and-agents-cleanup/000-main.md`

Depends On: `tasks/20260524-test-and-agents-cleanup/020-agents-and-testing-doc-guidance.md`

Depends On: `tasks/20260524-test-and-agents-cleanup/030-test-and-build-command-alignment.md`

## Why this task exists

The Python test guidance now has a clearer model, but the shared workspace packages under `packages/` still need the same level of clarity:

- what the default fast checks are
- which integration flows are opt-in
- which commands are expensive or environment-gated
- where contributors should start when changing a package

Without that, the monorepo still has a split command story between Python and workspace-package development.

## Repo facts already verified

### Root workspace manifest

- `package.json`
  - currently only declares the npm workspaces:
    - `packages/*`
  - contains no root-level scripts yet

### Workspace package scripts already present

- `packages/frontend-sdk/package.json`
  - `test`
  - `test:watch`
  - many explicit integration scripts:
    - backend integration
    - OpenAI / OpenRouter backend integration
    - bridge e2e integration
    - cloud orchestrator e2e integration
    - several AWS build/status/down helper commands
- `packages/frontend-sdk-react/package.json`
  - `test`
  - `test:watch`
- `packages/frontend-rn-components/package.json`
  - `test`
  - `test:watch`
- `packages/react-native-mac-text-view/package.json`
  - no scripts currently
- `packages/tool-host-node/package.json`
  - no test/build scripts currently

### Workspace package docs already verified

README files exist for:

- `packages/frontend-sdk/README.md`
- `packages/frontend-sdk-react/README.md`
- `packages/frontend-rn-components/README.md`
- `packages/react-native-mac-text-view/README.md`
- `packages/tool-host-node/README.md`

At least the first four are currently sparse and do not provide meaningful test guidance.

## Suggested scope

This task should focus first on:

1. inventory and classification of current package test/build commands
2. recommended run levels and gating model
3. contributor guidance for package work

If implementation grows large, likely follow-up splits would be:

- `061-frontend-sdk-integration-command-model.md`
- `062-package-readme-test-guidance-alignment.md`
- `063-sdk-env-gates-and-prerequisites.md`

Do not create those follow-ups unless the work genuinely branches that far.

## Suggested implementation steps

1. Audit every package under `packages/` for scripts, tests, and README guidance.
2. Classify current commands into:
   - default fast tests
   - package integration tests
   - expensive or infrastructure-backed tests
3. Decide on a standard language model for workspace packages similar to the Python test guidance:
   - fast default verification
   - integration verification
   - slow/expensive or infrastructure-backed verification
4. Capture env gates and prerequisites for scripts that use flags such as:
   - `RUN_BACKEND_INTEGRATION`
   - `RUN_BACKEND_OPENAI_INTEGRATION`
   - `RUN_BACKEND_OPENROUTER_INTEGRATION`
   - `RUN_BRIDGE_E2E_INTEGRATION`
   - `RUN_CLOUD_ORCHESTRATOR_E2E`
   - AWS-specific flags and stack-name requirements
5. Decide whether root docs, package docs, or both should carry the resulting guidance.
6. If the actual file-update surface becomes broad, split follow-up work into `061+` subtasks rather than overloading this task.

## Likely files to inspect

- `package.json`
- `packages/frontend-sdk/package.json`
- `packages/frontend-sdk-react/package.json`
- `packages/frontend-rn-components/package.json`
- `packages/react-native-mac-text-view/package.json`
- `packages/tool-host-node/package.json`
- package-local README files under `packages/`