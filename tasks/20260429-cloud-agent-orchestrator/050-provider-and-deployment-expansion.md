# Provider And Deployment Expansion
Generalize the orchestrator and cloud-agent backend model beyond Docker, and harden deployment/auth for more realistic cloud usage.

## Requirements checklist

- [ ] Formalize orchestrator provider interfaces for runtime lifecycle, storage, archive transfer, routing/token generation, status, and logs.
- [ ] Add at least one non-local-Docker backend, such as Kubernetes or AWS Fargate.
- [ ] For Fargate, design around persistent storage such as EFS plus short-running runtimes rather than SSH.
- [ ] Keep orchestrator hosting independent from cloud-agent runtime backend.
- [ ] Add stronger auth/token lifecycle and durable orchestrator state.
- [ ] Add cleanup/TTL policies and operational logs/status endpoints.
- [ ] Add expanded deployment docs and smoke tests for the new backend/hosting option.
- [ ] Add optional custom-domain deployment polish where useful, while keeping generated secure endpoints usable for automated tests.
- [x] Mirror the EC2 Docker-host + CloudFront generated HTTPS deployment shape for the bridge while keeping the existing bridge Fargate deployment intact.
- [x] Add a frontend SDK bridge E2E mode for the bridge EC2 deployment.
- [x] Separate AWS EC2 build from deploy/test by using explicit CodeBuild/ECR image builds; AWS E2E deploys fail when the prebuilt images are missing.
- [x] Provision the AWS bridge deployment once per frontend SDK test suite instead of once per test.
- [x] Add a combined bridge + cloud orchestrator EC2 deployment that runs both services on one cheap Docker host.

Parent Task: `tasks/20260429-cloud-agent-orchestrator/000-main.md`
Depends On: `tasks/20260429-cloud-agent-orchestrator/010-remote-docker-orchestrator-mvp.md`

## Backend Direction

The orchestrator service architecture and the cloud-agent runtime architecture should be independently replaceable.

Examples:

- Orchestrator hosting:
  - remote Docker host
  - EC2 Docker host
  - Kubernetes service
  - AWS Fargate service
  - serverless/Lambda-style control plane
- Cloud-agent runtime backend:
  - local Docker
  - remote Docker
  - Kubernetes pod/PVC
  - AWS Fargate task/service with persistent storage

## High-Level Behaviors To Test Before Acceptance

- Provider interface tests cover lifecycle, routing, archive transfer, status, and failure cases.
- At least one additional backend can start a cloud runtime and serve a session through cloud transport.
- Provider-specific storage persists across stop/start when designed to do so.
- Token expiry/revocation works consistently across providers.
- Cleanup policies remove stopped/expired resources without deleting active work unexpectedly.
- Deployment smoke tests verify health and minimal cloud-agent lifecycle for the added backend.
- Custom-domain support, when added, is tested separately from the default generated-address deployment path.
- Bridge EC2 E2E verifies pairing/proxy behavior and restart/resume behavior through generated CloudFront WSS.
- AWS EC2 E2E verifies that deploy/test consume prebuilt ECR images rather than building implicitly.
- Combined bridge + orchestrator EC2 E2E verifies both generated endpoints and a minimal bridge flow plus a minimal cloud-orchestrator session flow on the shared host.