# AWS Fargate External Bridge Deployment

Make it easy for a user with AWS CLI credentials to start an external Crystal Lattice bridge on AWS Fargate, obtain a bridge URL, connect the local `crystal-lattice` server and mobile app, and stop/restart/destroy the deployment predictably.

## Requirements checklist

- [x] Implement stateless signed pairing tokens as a prerequisite for clustered/resumable bridge connections.
- [x] Make `resume_session` verify the token and create a fresh ephemeral bridge session id.
- [x] Add a default secure AWS deployment profile: Fargate + ALB + CloudFront.
- [x] Add start/stop/restart/down/status scripts using AWS CLI and CloudFormation.
- [x] Ensure stopped secure deployments avoid most cost, including load balancer cost, while keeping the same public CloudFront domain when restarted.
- [x] Add optional autoscaling for the secure profile, intended first for testing.
- [x] Add a cheap single-task profile: one public Fargate task with plain HTTP/WebSocket and public IP output.
- [x] Add custom-domain support for the secure profile with automatic Route53 setup.
- [x] Document AWS prerequisites, costs, security model, connection commands, and cleanup.
- [x] Add tests or validation scripts for token behavior and generated deployment templates.

Parent Task: `tasks/20260421-distribution-release-workstreams/000-main.md`

Depends On: `tasks/20260421-distribution-release-workstreams/045-readme-quickstart-revision.md`

## Proposed solution from conversation

### Goal

The bridge should be deployable by a user who has the AWS CLI configured locally:

```bash
aws sts get-caller-identity
```

The default and simplest secure setup should produce a public WebSocket URL:

```text
wss://<cloudfront-domain>/ws/websocket
```

Users should be able to connect the local server with:

```bash
crystal-lattice \
  --server \
  --console \
  --bridge-url wss://<cloudfront-domain>/ws/websocket
```

and connect the mobile app with:

```text
Bridge Service -> wss://<cloudfront-domain>/ws/websocket
```

### Prerequisite: stateless pairing tokens

Current bridge token state is local ETS through `Bridge.PersistentPairingManager`, so a token issued by node A may not be known to node B. For a clustered/autoscaled bridge, pairing identity should be stateless and signed with a shared secret.

Token payload:

```json
{
  "v": 1,
  "typ": "bridge_pairing",
  "server_id": "server uuid",
  "client_id": "client uuid",
  "iat": 1760000000,
  "exp": 1762592000,
  "jti": "random uuid"
}
```

Shared secret/config:

```text
BRIDGE_TOKEN_SECRET
BRIDGE_TOKEN_SALT=pairing-token-v1
BRIDGE_PAIRING_TOKEN_TTL_SECONDS=2592000
```

Required behavior:

```text
pair_submit:
  validate pairing code
  issue signed pairing token
  create ephemeral session_id
  return session_id + pairing_token

resume_session:
  verify signed token
  ensure token client_id matches socket client_id
  ensure optional server_id param matches token server_id
  find current registered server_id
  create fresh ephemeral session_id
  return session_id
```

Important design decision:

```text
pairing token is durable logical pairing identity
session_id is ephemeral bridge routing state
```

This lets reconnects work across cluster nodes without DynamoDB. The tradeoff is that individual token revocation is unavailable unless a revocation store is added later; expiry and secret rotation are the first revocation mechanisms.

Likely files:

```text
bridge-elixir/lib/bridge/persistent_pairing_manager.ex
bridge-elixir/lib/bridge/app_channel.ex
bridge-elixir/test/bridge/persistent_pairing_manager_test.exs
bridge-elixir/test/bridge/websocket_test.exs
bridge-elixir/test/bridge/integration_test.exs
```

Potential implementation detail:

- Replace `PersistentPairingManager` internals with signed token issue/verify functions, or add a new `Bridge.PairingToken` module and remove persistent ETS usage.
- Use Phoenix/Plug crypto primitives or an HMAC-based implementation.
- Keep local/dev mode easy by allowing a generated dev fallback only for single-node local runs, but require explicit `BRIDGE_TOKEN_SECRET` for clustered/Fargate deployments.

### Option 1: default secure profile, Fargate + ALB + CloudFront

Default deployment profile:

```text
client
  -> wss://<cloudfront-domain>/ws/websocket
  -> CloudFront
  -> ALB
  -> ECS Fargate bridge service
```

Why this is the default:

- secure `wss://` without requiring a user-owned domain
- stable public CloudFront domain
- usable from the mobile app and local `crystal-lattice`
- compatible with later autoscaling

Deployment outputs:

```text
BridgeHttpUrl=https://xxxxx.cloudfront.net/health
BridgeWebSocketUrl=wss://xxxxx.cloudfront.net/ws/websocket
CloudFrontDomain=xxxxx.cloudfront.net
```

Proposed scripts:

```text
bridge-elixir/deploy/aws-fargate/up.sh
bridge-elixir/deploy/aws-fargate/status.sh
bridge-elixir/deploy/aws-fargate/stop.sh
bridge-elixir/deploy/aws-fargate/start.sh
bridge-elixir/deploy/aws-fargate/down.sh
```

Expected user flow:

```bash
bridge-elixir/deploy/aws-fargate/up.sh \
  --profile secure \
  --stack-name crystal-lattice-bridge \
  --region us-east-1
```

### Stop/restart cost behavior

Stopping and restarting should avoid most cost while stopped, including load balancer cost, but use the same public domain when restarted.

This means `stop` cannot merely set ECS desired count to `0`, because the ALB would still cost money.

Stable resources to keep while stopped:

```text
CloudFront distribution
shared token secret/cookie material
optional Route53 record if custom domain is enabled
configuration/state outputs
```

Resources to remove while stopped:

```text
ALB
target group/listener
ECS service
Fargate running tasks
possibly VPC resources if we choose to recreate them
```

Restart should recreate the ephemeral origin infrastructure and update the existing CloudFront distribution origin to the new ALB DNS name. That preserves:

```text
https://xxxxx.cloudfront.net
wss://xxxxx.cloudfront.net/ws/websocket
```

while avoiding ALB hourly cost during stopped periods.

Recommended implementation model:

- `crystal-lattice-bridge-edge`: CloudFront, optional Route53, persistent config/secrets.
- `crystal-lattice-bridge-origin`: VPC/ALB/ECS/Fargate origin resources.
- `stop.sh` deletes origin stack and updates edge/origin status.
- `start.sh` recreates origin stack and updates CloudFront origin.

Caveat: CloudFront creates and updates can take several minutes. While stopped, the public domain remains the same, but `/health` and WebSocket connection should return an unavailable response or fail until restarted.

### Optional autoscaling for testing

The secure profile should support optional autoscaling:

```bash
bridge-elixir/deploy/aws-fargate/up.sh \
  --profile secure \
  --autoscaling \
  --min-tasks 1 \
  --max-tasks 3
```

Initial autoscaling should be documented as testing/experimental until Fargate-compatible clustering is complete and validated.

Requirements for autoscaling:

- Fargate-compatible Elixir clustering.
- Shared `BRIDGE_TOKEN_SECRET`.
- Ephemeral session ids.
- Stateless pairing token verification across nodes.
- Security groups allowing Erlang distribution between bridge tasks.
- Service discovery/Cloud Map or DNS-based node discovery.

Bridge changes required for Fargate clustering:

```text
Use libcluster DNSPoll or ECS-compatible discovery instead of the current Gossip/multicast default.
Start nodes as bridge@<task-private-ip>.
Share COOKIE across all tasks.
Allow TCP 4369 and TCP 9100-9155 between bridge tasks.
```

Environment variables likely needed:

```text
BRIDGE_CLUSTER_STRATEGY=dns_poll
BRIDGE_CLUSTER_DNS_NAME=<cloud-map-service-name>
COOKIE=<shared erlang cookie>
NODE_NAME or RELEASE_NODE=bridge@<task-private-ip>
```

The current `docker-entrypoint.sh` uses `--sname "$NODE_NAME"`, which is Docker Compose friendly. Fargate likely needs an alternate entrypoint path that reads ECS task metadata and starts with a routable private IP node name.

Autoscaling policy options:

- CPU-based first, simplest.
- Memory-based as backup.
- Later: custom CloudWatch metric for active WebSockets/sessions.

Initial default:

```text
minTasks=1
maxTasks=3
```

Scale-to-zero should remain manual/scheduled, not automatic wake-on-WebSocket.

### Option 2: cheap single Fargate task with HTTP and public IP

Profile:

```text
Internet
  -> ws://<task-public-ip>:4000/ws/websocket
  -> single public Fargate task
```

Command:

```bash
bridge-elixir/deploy/aws-fargate/up.sh \
  --profile public-task \
  --stack-name crystal-lattice-bridge-dev \
  --region us-east-1
```

Output:

```text
BridgeHealthUrl=http://<public-ip>:4000/health
BridgeWebSocketUrl=ws://<public-ip>:4000/ws/websocket
```

Pros:

- cheapest
- no ALB
- no CloudFront
- good for temporary testing
- stopping/deleting removes almost all cost

Cons:

- not secure by default
- IP changes on restart
- no stable DNS
- not appropriate as public default

Implementation notes:

- May be easiest as an `aws ecs run-task` helper plus a minimal CloudFormation stack for VPC/cluster/roles.
- Script needs to discover task ENI public IP after task starts.
- `down.sh` or `stop.sh` stops the task.

### Option 3: custom domain with Route53

For the secure profile:

```bash
bridge-elixir/deploy/aws-fargate/up.sh \
  --profile secure \
  --domain bridge.example.com \
  --hosted-zone-id Z123456 \
  --region us-east-1
```

Expected outputs:

```text
BridgeWebSocketUrl=wss://bridge.example.com/ws/websocket
BridgeHttpUrl=https://bridge.example.com/health
```

Resources:

- ACM certificate in `us-east-1` for CloudFront
- DNS validation record in Route53
- CloudFront alternate domain name
- Route53 alias record to CloudFront

Important AWS detail:

- CloudFront requires ACM certificates in `us-east-1`, even if the Fargate service is in another region.

If the user’s region is not `us-east-1`, template/scripts should either:

- create the certificate in `us-east-1` separately, or
- document that custom-domain deployment uses `us-east-1` for edge certificate operations.

### Repository placement

Keep deployment files with the bridge:

```text
bridge-elixir/
  deploy/
    aws-fargate/
      README.md
      secure-edge.yaml
      secure-origin.yaml
      public-task.yaml
      up.sh
      start.sh
      stop.sh
      down.sh
      status.sh
      lib/
        common.sh
```

Runtime code changes remain under:

```text
bridge-elixir/lib/bridge/
bridge-elixir/config/
bridge-elixir/test/
```

### Validation plan

Token tests:

```bash
cd bridge-elixir
mix test test/bridge/persistent_pairing_manager_test.exs
mix test test/bridge/websocket_test.exs
```

Template validation:

```bash
aws cloudformation validate-template \
  --template-body file://bridge-elixir/deploy/aws-fargate/secure-edge.yaml

aws cloudformation validate-template \
  --template-body file://bridge-elixir/deploy/aws-fargate/secure-origin.yaml

aws cloudformation validate-template \
  --template-body file://bridge-elixir/deploy/aws-fargate/public-task.yaml
```

Shell validation:

```bash
shellcheck bridge-elixir/deploy/aws-fargate/*.sh
```

Optional real AWS smoke tests:

```bash
bridge-elixir/deploy/aws-fargate/up.sh --profile public-task
curl http://<ip>:4000/health
bridge-elixir/deploy/aws-fargate/down.sh --profile public-task

bridge-elixir/deploy/aws-fargate/up.sh --profile secure
curl https://<cloudfront-domain>/health
bridge-elixir/deploy/aws-fargate/down.sh --profile secure
```

### Documentation requirements

Add `bridge-elixir/deploy/aws-fargate/README.md` explaining:

- AWS CLI prerequisites
- expected permissions
- rough cost model
- secure default profile
- public-task profile
- custom domain profile
- start/stop/down semantics
- why stateless tokens are required
- autoscaling limitations and status
- how to connect local `crystal-lattice`
- how to connect mobile app
- how to clean up all AWS resources

Also update the main README’s bridge section once implemented. Until then, keep a TODO in `README.md` pointing at this task.

### Open design questions

- Should the secure profile keep VPC resources while stopped, or delete all origin resources including VPC?
- Should `stop.sh` disable the CloudFront origin or point it to a placeholder?
- Should the first autoscaling implementation use CPU/memory only, or should it add active-connection metrics?
- Should token signing use `Phoenix.Token`, `Plug.Crypto.MessageVerifier`, or explicit HMAC?
- What TTL should pairing tokens use by default: 7 days, 30 days, or configurable?
- Do we require `BRIDGE_TOKEN_SECRET` in all prod modes and only allow auto-generated local dev secrets outside prod?

### Recommended scope boundaries

In scope:

- stateless token implementation
- secure Fargate CloudFront deployment
- stop/start preserving CloudFront domain while removing ALB/Fargate cost
- public-task profile
- Route53 custom-domain profile
- optional autoscaling controls and template support
- docs and validation

Out of scope for this first task:

- fully automatic wake-from-zero on incoming WebSocket
- DynamoDB token revocation
- WAF
- multi-region bridge
- production-grade active-connection autoscaling metric unless it turns out to be simple
- mobile UI changes beyond documenting connection URLs

## Execution plan

Added during completion after user approval.

### Stage 1: stateless pairing token prerequisite

1. Add a dedicated stateless signed token implementation for bridge pairing identity.
2. Use `BRIDGE_TOKEN_SECRET`, `BRIDGE_TOKEN_SALT`, and `BRIDGE_PAIRING_TOKEN_TTL_SECONDS`.
3. Keep the current protocol response shape: `pair_submit` returns `session_id` and `pairing_token`; `resume_session` returns a fresh `session_id`.
4. Make `pairing_token` route to `server_id`; treat `session_id` as ephemeral routing state.
5. Do not enforce token `client_id` binding in this pass because the current mobile/frontend saved connection persists `pairingToken`, `serverId`, and `bridgeUrl`, but not the generated `clientId`.
6. Update token/unit tests to prove verification, tamper rejection, server mismatch, and fresh-session resume behavior.

### Stage 2: reuse existing integration and end-to-end tests

1. Reuse the existing frontend SDK bridge E2E as the primary full-stack verification:
   `packages/frontend-sdk/src/integration/__tests__/bridge.e2e.integration.test.ts`.
2. Keep the existing Docker behavior as the default E2E provider.
3. Add bridge-provider selection so the same E2E can run against Docker, an external bridge URL, or AWS-created bridge stacks.
4. Make `bridge-elixir/test_docker.py` accept `BRIDGE_URL` from the environment so the current protocol smoke test can run unchanged against Docker or AWS.
5. Extend the protocol smoke test to verify `pairing_token` is returned and `resume_session` creates a usable fresh session.

### Stage 3: AWS deployment scaffold and validation

1. Add deployment files under `bridge-elixir/deploy/aws-fargate/`.
2. Add the default secure profile using a two-stack model:
   - edge stack: CloudFront, optional custom domain/Route53, stable public domain
   - origin stack: ALB, ECS/Fargate service, task networking
3. Add the cheap `public-task` profile using a single public Fargate task and plain `ws://`.
4. Add custom-domain support for the secure profile with ACM in `us-east-1` and optional Route53 DNS setup.
5. Add scripts: `up.sh`, `start.sh`, `stop.sh`, `down.sh`, `status.sh`.
6. Add static validation commands for CloudFormation templates and shell scripts.

### Stage 4: AWS deployment tests

1. Add AWS smoke tests guarded by `RUN_AWS_BRIDGE_TESTS=1`.
2. Add `smoke_public_task.sh`:
   deploy public task, capture URL, run protocol test, clean up.
3. Add `smoke_secure.sh`:
   deploy secure profile, wait for CloudFront health, run protocol test, clean up.
4. Add `smoke_secure_restart.sh`:
   deploy secure profile, record CloudFront domain, run E2E, stop origin stack, start origin stack, verify same public domain, run resume/request E2E, clean up.
5. Add optional `smoke_custom_domain.sh` gated by hosted-zone/domain env vars.
6. Use isolated stack names, AWS tags, cleanup traps, and `--keep-on-failure`.

### Stage 5: docs and task status

1. Document local, Docker, external URL, AWS public-task, AWS secure, and custom-domain verification.
2. Replace the root README TODO with the real default command once the secure profile has a concrete script path.
3. Update this task checklist and append completion notes with what was implemented and what remains.

## Completion Notes

Added during completion.

Implemented stateless signed pairing tokens in `bridge-elixir/lib/bridge/pairing_token.ex` and rewired `Bridge.PersistentPairingManager` as a compatibility wrapper around signed-token issue/verify. `pair_submit` still returns `session_id` and `pairing_token`, while `resume_session` now verifies the signed token and creates a fresh ephemeral session id.

Added bridge tests for signed token behavior and app-channel resume behavior, and extended the Docker/Python bridge smoke test so it accepts `BRIDGE_URL`, verifies signed pairing tokens, and verifies resumed sessions are fresh. The Docker integration runner now pins `BRIDGE_URL=ws://localhost:4000/ws/websocket` so a developer shell's external `BRIDGE_URL` cannot accidentally redirect the Docker test.

Added frontend SDK E2E bridge provider selection. Docker remains the default, `BRIDGE_E2E_MODE=external` can target an arbitrary URL, and `BRIDGE_E2E_MODE=aws-public-task` / `aws-secure` can drive the AWS scripts when `RUN_AWS_BRIDGE_TESTS=1`.

Added `bridge-elixir/deploy/aws-fargate/` with CloudFormation templates and scripts:

- `public-task.yaml` plus `up/start/stop/down/status` support for a cheap public Fargate task.
- `secure-origin.yaml` for ALB + ECS/Fargate, Cloud Map service discovery, DNSPoll clustering, and optional CPU autoscaling.
- `secure-edge.yaml` for stable CloudFront, optional ACM certificate, and optional Route53 alias.
- AWS smoke scripts for public task, secure profile, secure stop/start E2E, and custom domain.
- Deployment README with setup, cost-saving stop/start behavior, custom-domain usage, and smoke-test commands.

Updated the root `README.md` bridge section with the default secure AWS command and a link to the deployment README.

Verification run:

- `mix test --exclude integration --exclude websocket` from `bridge-elixir` passed: 32 tests, 0 failures, 4 excluded. Existing warnings remain for skipped WebSocket tests referencing `Bridge.TestClient`.
- `BRIDGE_URL=ws://localhost:4000/ws/websocket python3 test_docker.py` passed.
- `./run-integration-tests.sh` passed after pinning the Docker test URL.
- `npm test -- bridgeTransport.test.ts` passed: 12 tests.
- `npm test -- src/integration/__tests__/bridge.e2e.integration.test.ts` passed in skipped mode, proving the updated file loads.
- `aws --region us-east-1 cloudformation validate-template` passed for `public-task.yaml`, `secure-origin.yaml`, and `secure-edge.yaml`.
- `shellcheck -x deploy/aws-fargate/*.sh deploy/aws-fargate/tests/*.sh` passed.
- `bash -n` passed for the deployment scripts.
- `git diff --check` passed.

Not run:

- Full package `npm exec tsc -- --noEmit` in `packages/frontend-sdk` still fails on pre-existing unrelated test/mock type errors and backend type issues outside this task.

Follow-up AWS test run:

- `RUN_AWS_BRIDGE_TESTS=1 AWS_REGION=us-east-1 ... smoke_public_task.sh` passed against a real public Fargate task.
- `RUN_AWS_BRIDGE_TESTS=1 AWS_REGION=us-east-1 ... smoke_secure.sh` passed against real Fargate + ALB + CloudFront using `wss://<cloudfront-domain>/ws/websocket`.
- Initial public-task smoke exposed an architecture mismatch on Apple Silicon. Fixed by making the helper build the native Docker platform by default and pass matching `CpuArchitecture` (`ARM64` here, `X86_64` on x86 CI) to Fargate.
- Initial secure smoke exposed an invalid CloudFront managed cache policy id. Fixed by using AWS managed `CachingDisabled` id `4135ea2d-6df8-44a3-9df3-4b5a84be39ad`.
- `smoke_secure_restart.sh` exists and drives the frontend SDK E2E through AWS secure mode, but it currently times out in Vitest during the long CloudFront/Fargate stop-start cycle. The stacks were cleaned up. This test needs follow-up instrumentation and/or a larger timeout/leaner restart strategy before it can be treated as a reliable passing AWS E2E.