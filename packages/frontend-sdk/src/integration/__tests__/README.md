# Frontend SDK Integration Tests

This directory contains Vitest integration and e2e tests for the TypeScript
frontend SDK talking to real backend processes, bridge services, cloud
orchestrators, and selected real model providers.

Run commands below from `packages/frontend-sdk` unless noted otherwise. The
package's default `npm test` run excludes this directory; use these scripts when
you intentionally want integration or e2e coverage.

```bash
npm run integration:backend
npm run integration:session-status
npm run integration:action-display-forms
npm run integration:website-runtime-ui
npm run integration:cloud -- -t "routes two cloud sessions"
```

To run an integration file directly, use the integration Vitest config:

```bash
npm exec -- vitest run --config vitest.integration.config.ts src/integration/__tests__/<file>.ts
```

`backend.compaction-menu.integration.test.ts` checks the plugin-owned
**OpenAI compaction up to here** label, confirmation, stable IDs/parameters,
and disabled-feature eligibility through real FastAPI, `FetchTransport`, and
`RestAgentBackend`. It makes no provider requests and requires no credentials.

The package scripts select exact files. Environment variables are kept for
credentials, optional modes, and AWS danger interlocks. Provider-backed tests may
need keys in the shell or in the repository root `.env`, depending on the suite.
Cloud orchestrator e2e tests intentionally let the Python backend application
resolve provider keys through its normal dotenv path.

## NPM Commands

Prefer these package scripts for day-to-day use. Extra Vitest arguments are
forwarded after `--`.

| Category | Command | Runs / requirements |
| --- | --- | --- |
| Local backend | `npm run integration:action-display-forms` | Dummy action display embedded form flow through SDK `runApplicationAction`. |
| Local backend | `npm run integration:website-runtime-ui` | Canonical website config and promoted UI fixture through FastAPI, `FetchTransport`, and `RestAgentBackend`. |
| Local backend | `npm run integration:backend` | `backend.integration.test.ts` with deterministic local providers. |
| Local backend | `npm run integration:session-status` | Explicit-ID request status through real FastAPI, HTTP transport, and `RestAgentBackend`. |
| Hosted API | `npm run integration:backend:openai` | OpenAI Responses attachment integration; requires `OPENAI_API_KEY`. |
| Hosted API | `npm run integration:backend:openrouter` | OpenRouter chat attachment integration; requires `OPENROUTER_API_KEY`. |
| Hosted API | `npm run integration:backend:openrouter-images` | OpenRouter image-generation attachment integration; requires `OPENROUTER_API_KEY`. |
| Hosted API | `npm run integration:backend:openrouter:mcp` | Codex MCP app-action integration; requires `OPENROUTER_API_KEY` and `npx`. |
| Bridge e2e | `npm run integration:bridge` | Bridge e2e in Docker mode by default. |
| Bridge e2e / AWS | `npm run integration:bridge:aws:fargate-secure` | Bridge e2e against AWS Fargate secure deployment. |
| Bridge e2e / AWS | `npm run integration:bridge:aws:fargate-public` | Bridge e2e against AWS Fargate public-task deployment. |
| Bridge e2e / AWS | `npm run integration:bridge:aws:ec2` | Bridge e2e against AWS EC2 secure deployment. |
| Bridge CLI e2e | `npm run integration:bridge:cli` | Bridge e2e using the real CLI entrypoint (`--no-tty --enable-bridge`); requires Docker. |
| Cloud e2e | `npm run integration:cloud` | Cloud orchestrator e2e in local Docker mode by default. |
| Cloud e2e | `npm run integration:cloud:profiles` | Standard cloud profile e2e in local Docker mode. |
| Cloud e2e / hosted API | `npm run integration:cloud:openrouter` | Cloud local e2e plus real OpenRouter tool-call flow. |
| Cloud e2e / hosted API | `npm run integration:cloud:codex` | Cloud local default-config Codex OpenRouter/OpenAI flows. |
| Cloud e2e / AWS | `npm run integration:cloud:aws` | Cloud orchestrator e2e against AWS EC2 + CloudFront. |
| Cloud e2e / AWS | `npm run integration:cloud:aws:fresh` | AWS EC2 + CloudFront e2e after building fresh images from the current source bundle. |
| Cloud e2e / AWS | `npm run integration:cloud:aws:codex` | AWS EC2 + CloudFront default-config Codex OpenRouter/OpenAI flows. |
| Cloud e2e / remote Docker | `npm run integration:cloud:remote-docker` | Gated remote Docker deploy smoke, then external-mode cloud orchestrator e2e. |

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
| `CLOUD_ORCHESTRATOR_E2E_BUILD_IMAGES` | Cloud orchestrator AWS mode | Set to `1` to run `deploy/aws-ec2/build.sh` before `up.sh` and avoid validating stale images. |
| `AWS_STACK_NAME` | AWS cloud/bridge harnesses | Optional fixed stack name. Use the same value for a prior cloud-orchestrator image build and e2e deploy. |
| `AWS_REGION` | AWS cloud/bridge harnesses | AWS region. Defaults to `us-east-1`. |
| `CLOUD_ORCHESTRATOR_E2E_CONTROL_TOKEN` | Cloud orchestrator tests | Optional control token to include in generated local app cloud-agent config. AWS deploy sets this after parsing deploy output. |
| `RUN_CLOUD_ORCHESTRATOR_REMOTE_DOCKER_E2E` | Remote Docker cloud smoke | Must be `1` before the remote Docker deploy smoke runs. |
| `CLOUD_ORCHESTRATOR_REMOTE` | Remote Docker cloud smoke | SSH target passed to `deploy/remote-docker/deploy.sh`. |
| `CLOUD_ORCHESTRATOR_PUBLIC_URL` | Remote Docker cloud smoke | Public URL used by deploy and then by external-mode e2e. |
| `BRIDGE_E2E_MODE` | Bridge harness | `docker` (default), `external`, `aws-public-task`, `aws-secure`, or `aws-ec2-secure`. |
| `BRIDGE_E2E_URL` | Bridge external mode | Existing bridge URL when `BRIDGE_E2E_MODE=external`. |
| `RUN_AWS_BRIDGE_TESTS` | Bridge AWS modes | Must be `1` before the harness creates AWS bridge resources. |

## Test Files

### `backend.integration.test.ts`

Selected by `npm run integration:backend`.

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

### `sessionRequestStatus.integration.test.ts`

Selected by `npm run integration:session-status`.

Starts an isolated real FastAPI backend and verifies the explicit-ID status
projection through `FetchTransport` and `RestAgentBackend`, including idle,
missing, not-started, running, and completed behavior.

Example:

```bash
npm run integration:backend
```

### `backend.openai.integration.test.ts`

Selected by `npm run integration:backend:openai`.

Requires `OPENAI_API_KEY`.

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

Selected by `npm run integration:backend:openrouter-images`.

Requires `OPENROUTER_API_KEY`.

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

### `backend.openrouter.integration.test.ts`

Selected by `npm run integration:backend:openrouter`.

Requires `OPENROUTER_API_KEY`.

This file reads `OPENROUTER_API_KEY`, optional `OPENROUTER_BASE_URL`, and
optional `OPENROUTER_VISION_MODEL` from the shell or repository root `.env`.
It starts a real backend with the general OpenRouter chat provider and
verifies upload-backed image attachment storage plus `asset_ref` sending
through the shared frontend SDK helpers.

Default vision-capable chat model:

- `OPENROUTER_VISION_MODEL=google/gemini-2.5-flash-lite`

Test:

- `stores an attachment through the SDK action helper and sends it by asset_ref against the real API`

Example:

```bash
npm run integration:backend:openrouter
```

### `backend.codex_mcp.integration.test.ts`

Selected by `npm run integration:backend:openrouter:mcp`.

Requires `OPENROUTER_API_KEY` and `npx`.

This file starts a real backend with the OpenRouter provider, the MCP runtime
app plugin, and Codex tools. It verifies SDK-discovered UI schema and MCP app
actions through the SDK.

Default models:

- provider model: `openai/gpt-5.4-mini`
- test prompt model: `openai/gpt-5.4-nano`

Test:

- `enables MCP through SDK-discovered UI schema and exercises MCP app actions through the SDK`

Example:

```bash
npm run integration:backend:openrouter:mcp
```

### `bridge.e2e.integration.test.ts`

Selected by `npm run integration:bridge` and the AWS bridge variants.

Starts or connects to an Elixir bridge and a real Python backend, then verifies
the WebSocket-only, HTTP-only, and hybrid transports end-to-end through pairing
and proxied requests.

Modes:

- `BRIDGE_E2E_MODE=docker` by default.
- `BRIDGE_E2E_MODE=external` requires `BRIDGE_E2E_URL`.
- `BRIDGE_E2E_MODE=aws-public-task`, `aws-secure`, or `aws-ec2-secure` requires `RUN_AWS_BRIDGE_TESTS=1`.

Tests:

- `supports large request + large response bodies`
- `supports HTTP-only large JSON and raw binary request/response bodies`
- `uses HTTP for normal hybrid requests and legacy WebSocket only for events`
- `reconnects and resumes after the bridge restarts`
- `allows a fast proxied request to complete while an earlier slow request is pending`

The HTTP-only case also verifies token resume, `/events` over HTTP, and
negotiated gzip. Docker mode is required for the bridge restart case and for
the normal self-managed run. External mode can exercise the remaining cases
against a bridge started separately:

```bash
BRIDGE_E2E_MODE=external \
BRIDGE_E2E_URL=ws://127.0.0.1:4000/ws/websocket \
npm run integration:bridge
```

Example:

```bash
npm run integration:bridge
```

### `bridge.cli.e2e.integration.test.ts`

Selected by `npm run integration:bridge:cli`.

Starts an Elixir bridge via Docker, then starts the **real CLI entrypoint**
(`python -m agent_terminal_app --server --no-tty --enable-bridge`) instead of
the custom backend runner.  Verifies the full user flow: bridge registration,
server visible in registry, pairing code read from CLI stdout, proxied HTTP
request through `BridgeTransport`.

This test exercises the CLI's `--no-tty` headless console mode and the
`--enable-bridge` flag end-to-end, including profile resolution and startup
summary output.

Requires Docker for the bridge.

Tests:

- `registers with bridge and serves a proxied HTTP request via the real CLI`

Example:

```bash
npm run integration:bridge:cli
```

### `cloud-orchestrator.e2e.integration.test.ts`

Selected by `npm run integration:cloud` and related cloud scripts.

Starts or connects to a cloud orchestrator, starts local backend servers with
the cloud-agent app plugin, transfers workspaces/config assets into cloud
runtimes, and verifies connection-scoped `CloudTransport` behavior.

Modes:

- `CLOUD_ORCHESTRATOR_E2E_MODE=local` by default. Requires Docker. The
  harness builds runtime images from an extracted deploy source bundle produced
  by `create_cloud_orchestrator_source_bundle`, so missing files in the reduced
  deploy build context fail the local e2e image build.
- `CLOUD_ORCHESTRATOR_E2E_MODE=external` requires `CLOUD_ORCHESTRATOR_E2E_URL`.
- `CLOUD_ORCHESTRATOR_E2E_MODE=aws-ec2-cloudfront` requires
  `RUN_AWS_CLOUD_ORCHESTRATOR_TESTS=1`. By default it validates prebuilt images
  from the AWS deploy state. Set `CLOUD_ORCHESTRATOR_E2E_BUILD_IMAGES=1` or use
  `npm run integration:cloud:aws:fresh` to build fresh images from the current
  source bundle before `up.sh`.

Provider credentials:

- The OpenRouter and Codex suites are gated only by explicit test flags. Do not
  gate them on keys in the Node process.
- Provider keys are resolved by the Python backend application's normal dotenv
  discovery path, including the current directory and its parents.
- `CLOUD_ORCHESTRATOR_OPENROUTER_MODEL` optionally overrides the OpenRouter model
  used by the OpenRouter tool-call suite.

Base tests enabled by `npm run integration:cloud`:

- `opens a cloud session through CloudTransport and syncs workspace files back down`
- `routes two cloud sessions through one connection-scoped CloudTransport`

Additional standard-profile command:

- `npm run integration:cloud:profiles`
- Runs `cloud-orchestrator.profiles.e2e.integration.test.ts`
- Always uses the local Docker orchestrator harness
- Verifies the shipped standard cloud profiles end to end using fixture-backed
  repo overrides and hooks rather than handwritten test-only scripts

Additional OpenRouter command:

- `npm run integration:cloud:openrouter`
- Internally sets `RUN_CLOUD_ORCHESTRATOR_OPENROUTER_E2E=1` because these tests still share the base cloud e2e file.
- Test: `runs local and cloud OpenRouter tool calls with config assets and sync-back`

Additional local default-config Codex command:

- `npm run integration:cloud:codex`
- Internally sets `RUN_CLOUD_ORCHESTRATOR_CODEX_DEFAULT_CONFIG_E2E=1` because these tests still share the base cloud e2e file.
- Tests:
  - `runs local-cloud-local bash and apply_patch chain with codex-openrouter`
  - `runs local-cloud-local bash and apply_patch chain with codex-openai`

Additional AWS default-config Codex command:

- `npm run integration:cloud:aws:codex`
- Internally sets `RUN_CLOUD_ORCHESTRATOR_CODEX_DEFAULT_CONFIG_EC2_E2E=1` because these tests still share the base cloud e2e file.
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

AWS fresh-build example:

```bash
AWS_STACK_NAME=crystal-lattice-cloud-orchestrator-e2e-manual npm run integration:cloud:aws:fresh
```

Remote Docker deploy smoke:

```bash
RUN_CLOUD_ORCHESTRATOR_REMOTE_DOCKER_E2E=1 \
CLOUD_ORCHESTRATOR_REMOTE=user@example-host \
CLOUD_ORCHESTRATOR_PUBLIC_URL=https://cloud.example.com \
npm run integration:cloud:remote-docker -- -t "opens a cloud session"
```

The remote Docker smoke calls
`cloud-orchestrator/deploy/remote-docker/deploy.sh` directly, then runs this
same e2e file in external mode. It leaves the remote deployment running.

Run one long cloud test at a time while debugging:

```bash
npm run integration:cloud -- -t "opens a cloud session through CloudTransport and syncs workspace files back down"
```