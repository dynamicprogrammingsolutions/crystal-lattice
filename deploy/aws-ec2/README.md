# AWS EC2 Combined Deployment

This deployment runs both the Crystal Lattice bridge and the cloud orchestrator on one EC2 Docker host, with generated CloudFront HTTPS/WSS endpoints for each service.

Use this when you want the cheapest single-user or testing deployment that exposes both external services.

## Prerequisites

- AWS CLI configured locally.
- Permission to create S3 objects, ECR repositories/images, CodeBuild projects, CloudFormation stacks, VPC networking, EC2 instances, IAM roles, SSM commands, and CloudFront distributions.
- `ALLOW_AWS_DEPLOY=1` for commands that create or delete AWS resources.

## Build

Build images first. The build step delegates to the bridge and cloud-orchestrator CodeBuild/ECR builders, then records all image URIs in combined deploy state.

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-ec2/build.sh \
  --profile secure \
  --stack-name crystal-lattice-combined \
  --region us-east-1
```

## Up

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-ec2/up.sh \
  --profile secure \
  --stack-name crystal-lattice-combined \
  --region us-east-1
```

The command prints:

```text
BridgeWebSocketUrl=wss://<bridge-cloudfront-domain>/ws/websocket
CloudOrchestratorUrl=https://<orchestrator-cloudfront-domain>
ControlToken=<cloud-orchestrator-control-token>
```

## Down

Delete runtime resources:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-ec2/down.sh \
  --profile secure \
  --stack-name crystal-lattice-combined \
  --region us-east-1
```

The CodeBuild projects, ECR repositories, and source bundles created by the build step are separate build artifacts and are not removed by `down.sh`.

## Tests

```bash
aws --region us-east-1 cloudformation validate-template --template-body file://deploy/aws-ec2/secure-origin.yaml
aws --region us-east-1 cloudformation validate-template --template-body file://deploy/aws-ec2/secure-edge.yaml
ALLOW_AWS_DEPLOY=1 deploy/aws-ec2/tests/smoke_secure.sh
```

Run `build.sh` first with the same stack name and region before running the smoke test.