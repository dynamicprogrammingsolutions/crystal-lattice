# AWS Fargate Bridge Deployment

This directory contains AWS CLI driven deployment helpers for the Crystal Lattice bridge.

## Prerequisites

- AWS CLI configured locally.
- Docker available locally if `--image-uri` is not provided.
- Permission to create ECR repositories, CloudFormation stacks, VPC networking, ECS/Fargate resources, IAM roles, CloudWatch Logs, ALB, CloudFront, and optionally Route53/ACM.

All commands that create AWS resources require an explicit guard:

```bash
export ALLOW_AWS_DEPLOY=1
```

If `--image-uri` is omitted, the helper creates an ECR repository, builds the
bridge image locally, pushes it, and uses that image for Fargate.

By default the helper builds the native Docker platform and passes the matching
Fargate CPU architecture. On Apple Silicon this means `linux/arm64` + `ARM64`;
on x86 CI this means `linux/amd64` + `X86_64`. Override when needed:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-fargate/up.sh \
  --profile secure \
  --docker-platform linux/amd64 \
  --cpu-architecture X86_64
```

## Default Secure Setup

The default profile creates a stable CloudFront URL in front of an ALB and ECS/Fargate service:

```bash
cd bridge-elixir
ALLOW_AWS_DEPLOY=1 deploy/aws-fargate/up.sh \
  --profile secure \
  --stack-name crystal-lattice-bridge \
  --region us-east-1
```

The script prints:

```text
BridgeHttpUrl=https://<cloudfront-domain>/health
BridgeWebSocketUrl=wss://<cloudfront-domain>/ws/websocket
CloudFrontDomain=<cloudfront-domain>
```

Connect the local server:

```bash
crystal-lattice \
  --server \
  --console \
  --bridge-url wss://<cloudfront-domain>/ws/websocket
```

Connect the mobile app with the same bridge URL.

## Stop, Start, And Down

For the secure profile, `stop.sh` removes the origin stack, including ALB and Fargate service resources, while keeping the CloudFront edge stack:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-fargate/stop.sh \
  --profile secure \
  --stack-name crystal-lattice-bridge \
  --region us-east-1
```

Restart with the same CloudFront domain:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-fargate/start.sh \
  --profile secure \
  --stack-name crystal-lattice-bridge \
  --region us-east-1
```

Delete everything:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-fargate/down.sh \
  --profile secure \
  --stack-name crystal-lattice-bridge \
  --region us-east-1
```

## Cheap Public Task

The `public-task` profile runs one public Fargate task and prints a plain WebSocket URL:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-fargate/up.sh \
  --profile public-task \
  --stack-name crystal-lattice-bridge-dev \
  --region us-east-1
```

Output:

```text
BridgeWebSocketUrl=ws://<public-ip>:4000/ws/websocket
```

This profile is cheaper and useful for temporary testing, but it is not secure and the IP changes when restarted.

## Custom Domain

For Route53-managed domains:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-fargate/up.sh \
  --profile secure \
  --stack-name crystal-lattice-bridge \
  --region us-east-1 \
  --domain bridge.example.com \
  --hosted-zone-id Z123456
```

CloudFront certificates must be in `us-east-1`; this template creates the ACM certificate in the region where the edge stack is deployed.

## Tests

Static validation:

```bash
aws cloudformation validate-template --template-body file://deploy/aws-fargate/public-task.yaml
aws cloudformation validate-template --template-body file://deploy/aws-fargate/secure-origin.yaml
aws cloudformation validate-template --template-body file://deploy/aws-fargate/secure-edge.yaml
```

Protocol smoke tests:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-fargate/tests/smoke_public_task.sh
ALLOW_AWS_DEPLOY=1 deploy/aws-fargate/tests/smoke_secure.sh
```

Secure stop/start E2E:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-fargate/tests/smoke_secure_restart.sh
```

Custom domain smoke test:

```bash
ALLOW_AWS_DEPLOY=1 \
BRIDGE_DOMAIN=bridge.example.com \
AWS_HOSTED_ZONE_ID=Z123456 \
deploy/aws-fargate/tests/smoke_custom_domain.sh
```

Use `KEEP_ON_FAILURE=1` to leave resources behind for debugging.