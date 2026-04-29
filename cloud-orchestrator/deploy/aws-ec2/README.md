# AWS EC2 Docker-Host Deployment

This deployment path is intentionally different from the bridge Fargate path. The MVP Docker runner needs a normal Docker host so it can start cloud runtime containers.

The scripts are guarded:

```bash
export RUN_AWS_CLOUD_ORCHESTRATOR_TESTS=1
```

Default secure generated-HTTPS flow:

```bash
RUN_AWS_CLOUD_ORCHESTRATOR_TESTS=1 deploy/aws-ec2/build.sh \
  --stack-name crystal-lattice-cloud-orchestrator-test \
  --region us-east-1 \
  --builder ec2

RUN_AWS_CLOUD_ORCHESTRATOR_TESTS=1 deploy/aws-ec2/up.sh \
  --stack-name crystal-lattice-cloud-orchestrator-test \
  --region us-east-1
RUN_AWS_CLOUD_ORCHESTRATOR_TESTS=1 deploy/aws-ec2/tests/smoke_secure.sh
RUN_AWS_CLOUD_ORCHESTRATOR_TESTS=1 deploy/aws-ec2/down.sh --stack-name crystal-lattice-cloud-orchestrator-test --region us-east-1
```

The default secure profile creates:

- one EC2 Docker host
- one CloudFront distribution with a generated `https://*.cloudfront.net` URL
- no load balancer
- a generated control-plane bearer token
- a generated runtime token-signing secret
- prebuilt Docker image artifacts uploaded to S3 before EC2 provisioning

The script prints:

```text
CloudOrchestratorUrl=https://<cloudfront-domain>
CloudOrchestratorEc2Url=http://<ec2-public-dns>:4100
CloudFrontDomain=<cloudfront-domain>
ControlToken=<token>
```

The EC2 origin currently exposes port `4100` publicly as the CloudFront origin. The orchestrator still requires the control token for mutating operations, and clients should use the generated CloudFront HTTPS URL. A later hardening pass can restrict origin access to CloudFront origin-facing ranges.

The runtime EC2 host does not build the application images. `build.sh` builds architecture-specific image tarballs and uploads them to S3; `up.sh` provisions EC2, loads those images, and starts containers. Use `--builder ec2` when local Docker cannot build the target architecture. The runtime defaults remain cheap and x86_64 (`linux/amd64` on `t3.micro`); the temporary EC2 builder defaults to `t3.large` and is destroyed after artifacts are uploaded.

Frontend SDK AWS E2E:

```bash
RUN_CLOUD_ORCHESTRATOR_E2E=1 \
RUN_AWS_CLOUD_ORCHESTRATOR_TESTS=1 \
CLOUD_ORCHESTRATOR_E2E_MODE=aws-ec2-cloudfront \
npm test --prefix ../packages/frontend-sdk -- cloud-orchestrator.e2e
```

The E2E deploys, tests through CloudFront HTTPS, and destroys the stack in cleanup.