# AWS EC2 Docker-Host Deployment

This directory contains AWS CLI driven deployment helpers for the Crystal Lattice cloud orchestrator. The MVP Docker runner needs a normal Docker host so it can start cloud runtime containers.

## Prerequisites

- AWS CLI configured locally.
- Permission to create S3 buckets/objects, CloudFormation stacks, VPC networking, EC2 instances, IAM roles, SSM commands, and CloudFront distributions.
- `ALLOW_AWS_DEPLOY=1` for commands that create or delete AWS resources.

The scripts are guarded:

```bash
export ALLOW_AWS_DEPLOY=1
```

## Default Secure Setup

```bash
cd cloud-orchestrator
ALLOW_AWS_DEPLOY=1 deploy/aws-ec2/build.sh \
  --profile secure \
  --stack-name crystal-lattice-cloud-orchestrator \
  --region us-east-1

ALLOW_AWS_DEPLOY=1 deploy/aws-ec2/up.sh \
  --profile secure \
  --stack-name crystal-lattice-cloud-orchestrator \
  --region us-east-1
```

The default secure profile creates:

- one EC2 Docker host
- one CloudFront distribution with a generated `https://*.cloudfront.net` URL
- no load balancer
- a generated control-plane bearer token
- a generated runtime token-signing secret
- prebuilt Docker images pushed to ECR before EC2 provisioning

The script prints:

```text
CloudOrchestratorUrl=https://<cloudfront-domain>
CloudOrchestratorEc2Url=http://<ec2-public-dns>:4100
CloudFrontDomain=<cloudfront-domain>
ControlToken=<token>
```

The EC2 origin currently exposes port `4100` publicly as the CloudFront origin. The orchestrator still requires the control token for mutating operations, and clients should use the generated CloudFront HTTPS URL. A later hardening pass can restrict origin access to CloudFront origin-facing ranges.

## Build Artifacts

The runtime EC2 host does not build the application images. `build.sh` uploads a source bundle to S3, uses CodeBuild to build the Docker images, pushes them to ECR, and records the image URIs in local deploy state. `up.sh` only deploys prebuilt images and fails if the build step has not run for the stack.

Build explicitly before running deploys or AWS E2E tests:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-ec2/build.sh \
  --profile secure \
  --stack-name crystal-lattice-cloud-orchestrator \
  --region us-east-1 \
  --builder codebuild
```

## Down

Delete runtime resources:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-ec2/down.sh --profile secure --stack-name crystal-lattice-cloud-orchestrator --region us-east-1
```

The CodeBuild project, ECR repositories, and source bundle are build artifacts and are not removed by `down.sh`.

## Tests

```bash
aws --region us-east-1 cloudformation validate-template --template-body file://deploy/aws-ec2/builder.yaml
aws --region us-east-1 cloudformation validate-template --template-body file://deploy/aws-ec2/secure-origin.yaml
aws --region us-east-1 cloudformation validate-template --template-body file://deploy/aws-ec2/secure-edge.yaml
ALLOW_AWS_DEPLOY=1 deploy/aws-ec2/tests/smoke_secure.sh
```

Frontend SDK AWS E2E:

```bash
RUN_CLOUD_ORCHESTRATOR_E2E=1 \
RUN_AWS_CLOUD_ORCHESTRATOR_TESTS=1 \
CLOUD_ORCHESTRATOR_E2E_MODE=aws-ec2-cloudfront \
npm test --prefix ../packages/frontend-sdk -- cloud-orchestrator.e2e
```

Run `build.sh` first with the same `--stack-name` and `--region`; the E2E harness intentionally fails when prebuilt images are missing.

The E2E deploys, tests through CloudFront HTTPS, and destroys the stack in cleanup.