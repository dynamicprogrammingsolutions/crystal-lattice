# SDK Test Guidance And Command Alignment

Audit the shared SDK and workspace-package test surfaces under `packages/`, then define the same kind of practical, layered guidance we now have for the main Python test suites: fast/default runs, integration runs, slow or expensive runs, env gates, and contributor-friendly command entrypoints. In this task, “SDK” means the shared workspace packages under `packages/`, not the Python core SDK test cleanup already handled by earlier subtasks.

## Requirements checklist

- [x] Audit the shared workspace packages under `packages/` for current test scripts, integration scripts, and missing command surfaces.
- [x] Define simple standard runs for SDK/package work, similar in spirit to the Python guidance.
- [x] Separate fast/default package tests from integration or expensive test flows.
- [x] Document env flags and external prerequisites for gated SDK integration flows.
- [x] Identify packages that currently have tests but weak or missing contributor guidance.
- [x] Identify packages that have build/runtime significance but no scripts or no test guidance yet.
- [x] Decide whether any package-local docs should be updated in this task or split into `061+` follow-ups.

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

## Execution plan

Added during task completion after user approval.

This task will be completed in staged passes so the command model is based on the actual workspace-package test surface before docs, script, or test cleanup changes are made.

### Stage 1: investigation only

Audit the workspace package test surface and classify what exists today, with extra attention on `packages/frontend-sdk`.

Scope:

- root `package.json` workspace setup
- all `packages/*/package.json` scripts
- package-local `vitest.config.ts`
- package-local README guidance
- `packages/frontend-sdk/src/integration/__tests__/README.md`
- frontend SDK test layout, especially `src/integration/__tests__`
- env gates and skip patterns in frontend SDK integration/e2e tests

Output:

- a concrete inventory of script categories:
  - fast unit/package tests
  - local backend integration
  - hosted API integration
  - bridge e2e
  - cloud orchestrator e2e
  - AWS/infrastructure-backed commands
  - maintenance/build/status/down scripts currently mixed into test scripts
- a list of confusing or risky command surfaces
- a list of likely cleanup opportunities in frontend SDK tests/scripts/docs

No implementation changes should be made in this stage beyond this approved execution plan and status/finding notes in the task file.

### Stage 2: define required updates

After Stage 1, report a proposed update set before changing docs, scripts, or tests.

The proposal may include:

- documentation-only updates
- package script renames or additions
- frontend SDK test cleanup
- splitting frontend SDK integration docs
- `061+` follow-up tasks if cleanup is bigger than this pass

Separate proposed work into:

- should do in `060`
- belongs in `090` build command guidance
- belongs in `100` root `package.json` scripts
- belongs in `110` editor tasks/run configs
- should become a `061+` follow-up

### Stage 3: implement approved `060` changes

After the update set is approved:

- update docs and/or scripts
- clean up frontend SDK test-command discoverability if needed
- update task checklist and completion notes
- run safe verification

Safe verification should include:

- `git diff --check`
- fast package tests where dependency state allows:
  - `npm --workspace @crystal-lattice/frontend-sdk test`
  - `npm --workspace @crystal-lattice/frontend-sdk-react test`
  - `npm --workspace @crystal-lattice/frontend-rn-components test`

Do not run hosted API, Docker, cloud, or AWS tests unless explicitly requested.

## Stage 1 investigation notes

Added during task completion.

### Workspace package inventory

- Root `package.json`
  - declares npm workspaces as `packages/*`
  - has no root-level scripts today
- `packages/frontend-sdk`
  - package name: `@crystal-lattice/frontend-sdk`
  - scripts: `test`, `test:watch`, and a large `integration:*` surface
  - test files found: 30
  - external integration/e2e files under `src/integration/__tests__`: 8
  - one fast reducer composition file also uses `integration` in its filename: `src/chat/__tests__/reducers.integration.test.ts`
- `packages/frontend-sdk-react`
  - package name: `@crystal-lattice/frontend-sdk-react`
  - scripts: `test`, `test:watch`
  - test files found: 3
- `packages/frontend-rn-components`
  - package name: `@crystal-lattice/frontend-rn-components`
  - scripts: `test`, `test:watch`
  - test files found: 2
- `packages/react-native-mac-text-view`
  - package name: `@crystal-lattice/react-native-mac-text-view`
  - no package scripts
  - no test files found
- `packages/tool-host-node`
  - package name: `@agent-platform/tool-host-node`
  - no package scripts
  - no test files found

### Script categories found

Fast/default package tests:

- `@crystal-lattice/frontend-sdk`: `npm --workspace @crystal-lattice/frontend-sdk test`
- `@crystal-lattice/frontend-sdk-react`: `npm --workspace @crystal-lattice/frontend-sdk-react test`
- `@crystal-lattice/frontend-rn-components`: `npm --workspace @crystal-lattice/frontend-rn-components test`

Local backend integration:

- `packages/frontend-sdk`: `integration:backend`
  - gate: `RUN_BACKEND_INTEGRATION=1`
  - starts a real local FastAPI backend with deterministic/local providers

Hosted API backend integration:

- `packages/frontend-sdk`: `integration:backend:openai`
  - gate/key: `RUN_BACKEND_OPENAI_INTEGRATION=1` and `OPENAI_API_KEY`
- `packages/frontend-sdk`: `integration:backend:openrouter`
  - gate/key: `RUN_BACKEND_OPENROUTER_INTEGRATION=1` and `OPENROUTER_API_KEY`
- `packages/frontend-sdk`: `integration:backend:openrouter-images`
  - gate/key: `RUN_BACKEND_OPENROUTER_INTEGRATION=1` and `OPENROUTER_API_KEY`
- `packages/frontend-sdk`: `integration:backend:openrouter:mcp`
  - gate/key/tooling: `RUN_BACKEND_OPENROUTER_INTEGRATION=1`, `OPENROUTER_API_KEY`, and `npx`

Bridge e2e:

- `packages/frontend-sdk`: `integration:bridge`
  - gate: `RUN_BRIDGE_E2E_INTEGRATION=1`
  - default mode: local Docker bridge
  - optional modes include external and AWS-backed bridge deployments

Cloud orchestrator e2e:

- `packages/frontend-sdk`: `integration:cloud`
  - gate: `RUN_CLOUD_ORCHESTRATOR_E2E=1`
  - default mode: local Docker cloud orchestrator
- `packages/frontend-sdk`: `integration:cloud:profiles`
  - gate: `RUN_CLOUD_ORCHESTRATOR_PROFILE_E2E=1`
  - runs the standard-profile e2e file against the local Docker harness
- `packages/frontend-sdk`: `integration:cloud:openrouter`
  - gates: `RUN_CLOUD_ORCHESTRATOR_E2E=1` and `RUN_CLOUD_ORCHESTRATOR_OPENROUTER_E2E=1`
  - provider keys are resolved by the Python backend application's normal dotenv path
- `packages/frontend-sdk`: `integration:cloud:codex`
  - gates: `RUN_CLOUD_ORCHESTRATOR_E2E=1` and `RUN_CLOUD_ORCHESTRATOR_CODEX_DEFAULT_CONFIG_E2E=1`
  - provider keys are resolved by the Python backend application's normal dotenv path

AWS/infrastructure-backed e2e:

- `packages/frontend-sdk`: `integration:bridge:aws:fargate-secure`
- `packages/frontend-sdk`: `integration:bridge:aws:fargate-public`
- `packages/frontend-sdk`: `integration:bridge:aws:ec2`
- `packages/frontend-sdk`: `integration:cloud:aws`
- `packages/frontend-sdk`: `integration:cloud:aws:codex`

AWS maintenance/build/status/down/list scripts currently under the `integration:*` namespace:

- cloud orchestrator AWS: `integration:cloud:aws:build`, `status`, `down`, `down:builder`, `list`
- bridge AWS Fargate: `integration:bridge:aws:fargate-secure:status`, `down`; `integration:bridge:aws:fargate-public:status`, `down`
- bridge AWS EC2: `integration:bridge:aws:ec2:build`, `status`, `down`, `down:builder`, `list`

### Frontend SDK cleanup findings

- `packages/frontend-sdk/vitest.config.ts` includes `src/**/*.test.ts`, so default `npm test` collects `src/integration/__tests__/*.integration.test.ts` and relies on top-level `describe.skip` gates to keep those suites from running.
- That gate-based default is mostly safe when no integration env flags are set, but it means a stale shell env flag such as `RUN_BACKEND_OPENROUTER_INTEGRATION=1` can make plain `npm test` run hosted API integration files.
- The frontend SDK integration README already documents most gates in detail, but its top command table is missing at least:
  - `integration:backend:openrouter:mcp`
  - `integration:cloud:profiles`
- Four hosted-provider backend integration files duplicate a small `loadEnvVarFromRoot` helper:
  - `backend.openai.integration.test.ts`
  - `backend.openrouter.integration.test.ts`
  - `backend.image_attachments.integration.test.ts`
  - `backend.codex_mcp.integration.test.ts`
- Package-level README files under `packages/` are sparse and do not explain fast/default versus integration or absent package-local test commands.
- Root `AGENTS.md` names the shared package area but does not yet document workspace-package test commands.

### Verification status

- No hosted API, Docker, cloud, or AWS integration commands were run during Stage 1.
- No fast package tests were run during Stage 1 because the new worktree does not currently have `node_modules`.

## Approved implementation plan

Added during task completion after user approval.

Use explicit file/config selection as the primary test-selection mechanism for workspace-package tests. Keep env vars for credentials, modes, and danger interlocks, not as the normal way to select a test category.

### In-scope changes for this pass

1. Narrow the `packages/frontend-sdk` default Vitest run so `npm test` and `npm run test:watch` do not collect `src/integration/**`.
2. Add a dedicated frontend SDK integration Vitest config for exact-file integration/e2e scripts.
3. Update frontend SDK integration scripts so exact file paths select the category where possible.
4. Keep env vars for:
   - credentials such as `OPENAI_API_KEY` and `OPENROUTER_API_KEY`
   - optional provider/mode settings such as `OPENAI_BASE_URL`, `OPENROUTER_BASE_URL`, `BRIDGE_E2E_MODE`, and `CLOUD_ORCHESTRATOR_E2E_MODE`
   - AWS danger interlocks such as `RUN_AWS_BRIDGE_TESTS=1` and `RUN_AWS_CLOUD_ORCHESTRATOR_TESTS=1`
5. Remove/reduce `RUN_*` category gates where exact-file script selection is enough.
6. Extract duplicated `loadEnvVarFromRoot` helper logic from hosted-provider frontend SDK integration tests into shared harness code.
7. Update package-local README guidance and the frontend SDK integration README so users and agents can find the right command quickly.
8. Add concise shared-package test guidance to root `AGENTS.md`.

### Possible follow-up split

The `cloud-orchestrator.e2e.integration.test.ts` file currently contains multiple materially different categories behind nested env gates. If removing those gates requires a broad file decomposition, create a `061+` follow-up rather than mixing that larger refactor into this pass.

## Completion Notes

Added during task completion.

- Updated `packages/frontend-sdk` so fast/default `npm test` no longer collects `src/integration/**`.
- Added `packages/frontend-sdk/vitest.integration.config.ts` for exact-file integration/e2e scripts.
- Updated frontend SDK integration scripts so file/config selection is the primary category selector:
  - removed `RUN_BACKEND_*`, `RUN_BRIDGE_E2E_INTEGRATION`, `RUN_CLOUD_ORCHESTRATOR_E2E`, and `RUN_CLOUD_ORCHESTRATOR_PROFILE_E2E` as category gates
  - kept credentials, mode env vars, and AWS danger interlocks
  - kept the remaining cloud subcategory env gates only because those categories still share one large cloud e2e file
- Extracted `findRepoRoot` and `loadEnvVarFromRoot` into `packages/frontend-sdk/src/integration/harness.ts` and updated hosted-provider integration files to use the shared helper.
- Updated workspace-package docs:
  - `packages/frontend-sdk/README.md`
  - `packages/frontend-sdk-react/README.md`
  - `packages/frontend-rn-components/README.md`
  - `packages/react-native-mac-text-view/README.md`
  - `packages/tool-host-node/README.md`
  - `packages/frontend-sdk/src/integration/__tests__/README.md`
  - root `AGENTS.md`
- Created follow-up `tasks/20260524-test-and-agents-cleanup/061-frontend-sdk-cloud-e2e-file-decomposition.md` for decomposing the remaining mixed cloud e2e file and removing the last category-gate env vars.
- Installed workspace npm dependencies in the new worktree with `npm ci --ignore-scripts` to run fast verification.
- Verification run:
  - `npm --workspace @crystal-lattice/frontend-sdk test` passed: 22 files, 156 tests
  - `npm --workspace @crystal-lattice/frontend-sdk-react test` passed: 3 files, 15 tests
  - `npm --workspace @crystal-lattice/frontend-rn-components test` passed: 2 files, 7 tests
  - `npm --workspace @crystal-lattice/frontend-sdk run integration:backend -- -t "__NO_SUCH_TEST__" --passWithNoTests` passed, validating the new integration config/script path without starting the backend
  - no-match hosted-provider integration script checks passed for:
    - `integration:backend:openai`
    - `integration:backend:openrouter`
    - `integration:backend:openrouter-images`
    - `integration:backend:openrouter:mcp`
  - `git diff --check` passed
- Not run:
  - hosted API integrations
  - Docker-backed bridge/cloud e2e
  - AWS-backed e2e or AWS maintenance scripts