# Frontend SDK Integration Tests

This directory contains Vitest integration and e2e tests for the TypeScript
frontend SDK talking to real backend processes, bridge services, cloud
orchestrators, and selected real model providers.

Run commands below from `packages/frontend-sdk` unless noted otherwise.

```bash
npm test -- src/integration/__tests__/<file>.ts
```

Most suites are skipped unless an explicit gate environment variable is set.
Provider-backed tests may also need keys in the shell or in the repository root
`.env`, depending on the suite. Cloud orchestrator e2e tests intentionally let
the Python backend application resolve provider keys through its normal dotenv
path.

## NPM Commands

Prefer these package scripts for day-to-day use. They set the right gate
variables and call the test file directly; extra Vitest arguments are forwarded
after `--`.

| Command | Runs |
| --- | --- |
| `npm run integration:backend` | `backend.integration.test.ts` with local deterministic providers. |
| `npm run integration:backend:openai` | OpenAI Responses attachment integration. |
| `npm run integration:backend:openrouter-images` | OpenRouter image-generation attachment integration. |
| `npm run integration:backend:openrouter:interceptor` | OpenRouter real-provider tool interception flow via SDK prompt APIs. |
| `npm run integration:bridge` | Bridge e2e in Docker mode by default. |
| `npm run integration:bridge:aws:fargate-secure` | Bridge e2e against AWS Fargate secure deployment. |
| `npm run integration:bridge:aws:fargate-public` | Bridge e2e against AWS Fargate public-task deployment. |
| `npm run integration:bridge:aws:ec2` | Bridge e2e against AWS EC2 secure deployment. |
| `npm run integration:cloud` | Cloud orchestrator e2e in local Docker mode by default. |
| `npm run integration:cloud:openrouter` | Cloud orchestrator local e2e plus real OpenRouter tool-call flow. |
| `npm run integration:cloud:codex` | Cloud orchestrator local default-config Codex OpenRouter/OpenAI flows. |
| `npm run integration:cloud:aws` | Cloud orchestrator e2e against AWS EC2 + CloudFront. |
| `npm run integration:cloud:aws:codex` | AWS EC2 + CloudFront default-config Codex OpenRouter/OpenAI flows. |

Examples:

```bash
npm run integration:backend
npm run integration:cloud -- -t "routes two cloud sessions"
npm run integration:cloud:openrouter -- -t "runs local and cloud OpenRouter tool calls"
AWS_STACK_NAME=e2e-manual npm run integration:cloud:aws -- -t "opens a cloud session"
```

AWS build/status/cleanup scripts:

| Command | Purpose |
| --- | --- |
| `AWS_STACK_NAME=name npm run integration:cloud:aws:build` | Build cloud orchestrator AWS images for a stack. |
| `AWS_STACK_NAME=name npm run integration:cloud:aws:status` | Show cloud orchestrator origin/edge/builder stack status. |
| `AWS_STACK_NAME=name npm run integration:cloud:aws:down` | Delete cloud orchestrator origin/edge stacks. |
| `AWS_STACK_NAME=name npm run integration:cloud:aws:down:builder` | Delete cloud orchestrator builder stack. |
| `npm run integration:cloud:aws:list` | List cloud orchestrator CloudFormation stacks with the standard prefix. |
| `AWS_STACK_NAME=name npm run integration:bridge:aws:ec2:build` | Build bridge EC2 AWS image for a stack. |
| `AWS_STACK_NAME=name npm run integration:bridge:aws:ec2:status` | Show bridge EC2 origin/edge/builder stack status. |
| `AWS_STACK_NAME=name npm run integration:bridge:aws:ec2:down` | Delete bridge EC2 origin/edge stacks. |
| `AWS_STACK_NAME=name npm run integration:bridge:aws:ec2:down:builder` | Delete bridge EC2 builder stack. |
| `AWS_STACK_NAME=name npm run integration:bridge:aws:fargate-secure:status` | Show bridge Fargate secure stack status. |
| `AWS_STACK_NAME=name npm run integration:bridge:aws:fargate-secure:down` | Delete bridge Fargate secure stacks. |
| `AWS_STACK_NAME=name npm run integration:bridge:aws:fargate-public:status` | Show bridge Fargate public-task stack status. |
| `AWS_STACK_NAME=name npm run integration:bridge:aws:fargate-public:down` | Delete bridge Fargate public-task stack. |
| `npm run integration:bridge:aws:list` | List bridge CloudFormation stacks with the standard prefix. |

Set `AWS_REGION` to override the default `us-east-1`.

## Shared Harness Environment

These variables are consumed by `src/integration/harness.ts`.

| Variable | Used By | Meaning |
| --- | --- | --- |
| `PYTHON` | Backend harness | Python executable used to start the FastAPI backend. Defaults to `python`. |
| `CLOUD_ORCHESTRATOR_E2E_MODE` | Cloud orchestrator harness | `local` (default), `external`, or `aws-ec2-cloudfront`. |
| `CLOUD_ORCHESTRATOR_E2E_URL` | Cloud orchestrator external mode | Existing orchestrator URL when `CLOUD_ORCHESTRATOR_E2E_MODE=external`. |
| `RUN_AWS_CLOUD_ORCHESTRATOR_TESTS` | Cloud orchestrator AWS mode | Must be `1` before the harness creates AWS resources. |
| `AWS_STACK_NAME` | AWS cloud/bridge harnesses | Optional fixed stack name. Use the same value for a prior cloud-orchestrator image build and e2e deploy. |
| `AWS_REGION` | AWS cloud/bridge harnesses | AWS region. Defaults to `us-east-1`. |
| `CLOUD_ORCHESTRATOR_E2E_CONTROL_TOKEN` | Cloud orchestrator tests | Optional control token to include in generated local app cloud-agent config. AWS deploy sets this after parsing deploy output. |
| `BRIDGE_E2E_MODE` | Bridge harness | `docker` (default), `external`, `aws-public-task`, `aws-secure`, or `aws-ec2-secure`. |
| `BRIDGE_E2E_URL` | Bridge external mode | Existing bridge URL when `BRIDGE_E2E_MODE=external`. |
| `RUN_AWS_BRIDGE_TESTS` | Bridge AWS modes | Must be `1` before the harness creates AWS bridge resources. |

## Test Files

### `backend.integration.test.ts`

Gate: `RUN_BACKEND_INTEGRATION=1`

Starts a real FastAPI backend with deterministic local providers and exercises
SDK/controller behavior without real model providers.

Tests:

- `A: system_message_feature first append triggers one auto reload and recovers`
- `B: manual reload during an in-flight request does not leave the session dirty`
- `C1: server-side pause of /events keeps a poll in flight; reload stays consistent`
- `C2: client-side delayed /events response keeps a poll in flight; reload stays consistent`
- `D: session plugins list/set/clear roundtrip`
- `E: disabling system_message removes the synthetic system message from stored history`
- `F: append message with multipartContent roundtrips`
- `F2: uploaded attachment previews are present in frontend-visible user messages`
- `G: FetchTransport times out cleanly against a delayed backend response`
- `H: recoverAfterResume reloads the active window and reconciles a stale request id`
- `I: reopened persisted sessions after backend restart keep the next user send visible before assistant final`
- `J: polling continues across backend restart while the same controller remains open`
- `K1: rehydrated cached session without restart can send and stream immediately`
- `K2: rehydrated cached session after backend restart can send and stream immediately`
- `K3: empty cached session without restart still reloads and can send immediately`
- `K4: empty cached session after backend restart still reloads and can send immediately`
- `L: expired event cursors trigger automatic controller reload recovery`
- `M: expired snapshot cursor does not trigger a /messages reload loop`
- `N: reload and polling timing matrix stays clean during delayed persistence`
- `O: tool-loop reopen matrix stays aligned across delayed checkpoint publication`

Example:

```bash
npm run integration:backend
```

### `backend.openai.integration.test.ts`

Gate: `RUN_BACKEND_OPENAI_INTEGRATION=1` and `OPENAI_API_KEY`

This file reads `OPENAI_API_KEY` and optional `OPENAI_BASE_URL` from the shell
or repository root `.env`. It starts a real backend with the OpenAI Responses
plugin and verifies attachment upload/send behavior against the real API.

Optional model override:

- `OPENAI_RESPONSES_VISION_MODEL`, default `gpt-5-mini`

Test:

- `stores an attachment through the SDK action helper and sends it by asset_ref against the real API`

Example:

```bash
npm run integration:backend:openai
```

### `backend.image_attachments.integration.test.ts`

Gate: `RUN_BACKEND_OPENROUTER_INTEGRATION=1` and `OPENROUTER_API_KEY`

This file reads `OPENROUTER_API_KEY`, optional `OPENROUTER_BASE_URL`, and
optional `OPENROUTER_IMAGE_GENERATION_E2E_MODEL` from the shell or repository
root `.env`. It starts a real backend with the OpenRouter image-generation
plugin and verifies generated images, source-image generation, and attachment
download behavior.

Default image model:

- `OPENROUTER_IMAGE_GENERATION_E2E_MODEL=google/gemini-2.5-flash-image`

Test:

- `covers simple generation, source-image generation, and result download against the real provider`

Example:

```bash
npm run integration:backend:openrouter-images
```

### `backend.tool_interceptor.integration.test.ts`

Gate: `RUN_BACKEND_OPENROUTER_INTERCEPTOR_INTEGRATION=1` and at least one of:

- `OPENROUTER_API_KEY`
- `OPENAI_API_KEY`

This file loads the shared fixture config at
`src/integration/fixtures/interceptor-provider-matrix.config.json`, a
simplified version of the local Crystal config shape, and runs the real
tool-interception happy path against whichever provider credentials are
available:

- `intercept-openrouter` using `openrouter`
- `intercept-openai` using `openai_responses`

For each available provider, it:

- sends a real user prompt through the SDK
- observes a pending interception prompt through SDK prompt APIs
- answers the prompt through the SDK
- verifies that the resumed request reaches a stable completed state
- reloads the session through both the same controller and a fresh controller

Default fixture models:

- OpenRouter: `openai/gpt-5.4-nano`
- OpenAI Responses: `gpt-5-mini`

Example:

```bash
npm run integration:backend:openrouter:interceptor
```

### `bridge.e2e.integration.test.ts`

Gate: `RUN_BRIDGE_E2E_INTEGRATION=1`

Starts or connects to an Elixir bridge and a real Python backend, then verifies
`BridgeTransport` end-to-end through pairing and proxied HTTP requests.

Modes:

- `BRIDGE_E2E_MODE=docker` by default.
- `BRIDGE_E2E_MODE=external` requires `BRIDGE_E2E_URL`.
- `BRIDGE_E2E_MODE=aws-public-task`, `aws-secure`, or `aws-ec2-secure` requires `RUN_AWS_BRIDGE_TESTS=1`.

Tests:

- `supports large request + large response bodies`
- `reconnects and resumes after the bridge restarts`

Example:

```bash
npm run integration:bridge
```

### `cloud-orchestrator.e2e.integration.test.ts`

Base gate: `RUN_CLOUD_ORCHESTRATOR_E2E=1`

Starts or connects to a cloud orchestrator, starts local backend servers with
the cloud-agent app plugin, transfers workspaces/config assets into cloud
runtimes, and verifies connection-scoped `CloudTransport` behavior.

Modes:

- `CLOUD_ORCHESTRATOR_E2E_MODE=local` by default. Requires Docker.
- `CLOUD_ORCHESTRATOR_E2E_MODE=external` requires `CLOUD_ORCHESTRATOR_E2E_URL`.
- `CLOUD_ORCHESTRATOR_E2E_MODE=aws-ec2-cloudfront` requires `RUN_AWS_CLOUD_ORCHESTRATOR_TESTS=1`. Build images first from `cloud-orchestrator` with a fixed `AWS_STACK_NAME`, then run the e2e with the same `AWS_STACK_NAME`.

Provider credentials:

- The OpenRouter and Codex suites are gated only by explicit test flags. Do not
  gate them on keys in the Node process.
- Provider keys are resolved by the Python backend application's normal dotenv
  discovery path, including the current directory and its parents.
- `CLOUD_ORCHESTRATOR_OPENROUTER_MODEL` optionally overrides the OpenRouter model
  used by the OpenRouter tool-call suite.

Base tests enabled by `RUN_CLOUD_ORCHESTRATOR_E2E=1`:

- `opens a cloud session through CloudTransport and syncs workspace files back down`
- `routes two cloud sessions through one connection-scoped CloudTransport`

Additional OpenRouter gate:

- `RUN_CLOUD_ORCHESTRATOR_OPENROUTER_E2E=1`
- Test: `runs local and cloud OpenRouter tool calls with config assets and sync-back`

Additional local default-config Codex gate:

- `RUN_CLOUD_ORCHESTRATOR_CODEX_DEFAULT_CONFIG_E2E=1`
- Tests:
  - `runs local-cloud-local bash and apply_patch chain with codex-openrouter`
  - `runs local-cloud-local bash and apply_patch chain with codex-openai`

Additional AWS default-config Codex gate:

- `RUN_CLOUD_ORCHESTRATOR_CODEX_DEFAULT_CONFIG_EC2_E2E=1`
- Requires `CLOUD_ORCHESTRATOR_E2E_MODE=aws-ec2-cloudfront`
- Tests:
  - `runs EC2 local-cloud-local bash and apply_patch chain with codex-openrouter`
  - `runs EC2 local-cloud-local bash and apply_patch chain with codex-openai`

Local example:

```bash
npm run integration:cloud
```

AWS example:

```bash
AWS_STACK_NAME=crystal-lattice-cloud-orchestrator-e2e-manual npm run integration:cloud:aws:build
AWS_STACK_NAME=crystal-lattice-cloud-orchestrator-e2e-manual npm run integration:cloud:aws
```

Run one long cloud test at a time while debugging:

```bash
npm run integration:cloud -- -t "opens a cloud session through CloudTransport and syncs workspace files back down"
```