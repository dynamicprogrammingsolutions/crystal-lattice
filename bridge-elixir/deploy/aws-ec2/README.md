# AWS EC2 Bridge Deployment

This directory contains AWS CLI driven deployment helpers for the Crystal Lattice bridge using one EC2 Docker host and a generated CloudFront HTTPS/WSS URL.

The existing Fargate helpers under `deploy/aws-fargate/` remain supported. This EC2 path is the default low-cost single-user/testing path.

## Prerequisites

- AWS CLI configured locally.
- Permission to create S3 buckets/objects, CloudFormation stacks, VPC networking, EC2 instances, IAM roles, SSM commands, and CloudFront distributions.
- `ALLOW_AWS_DEPLOY=1` for commands that create or delete AWS resources.

## Default Secure Setup

```bash
cd bridge-elixir
ALLOW_AWS_DEPLOY=1 deploy/aws-ec2/build.sh \
  --profile secure \
  --stack-name crystal-lattice-bridge \
  --region us-east-1

ALLOW_AWS_DEPLOY=1 deploy/aws-ec2/up.sh \
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

`build.sh` uploads a source bundle to S3, uses CodeBuild to build the Docker image, pushes it to ECR, and records the image URI in local deploy state. `up.sh` only deploys prebuilt images and fails when the build step has not run for the stack.

## Down

Delete runtime resources:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-ec2/down.sh --profile secure --stack-name crystal-lattice-bridge --region us-east-1
```

The CodeBuild project, ECR repository, and source bundle are build artifacts and are not removed by `down.sh`.

## Tests

```bash
aws --region us-east-1 cloudformation validate-template --template-body file://deploy/aws-ec2/builder.yaml
aws --region us-east-1 cloudformation validate-template --template-body file://deploy/aws-ec2/secure-origin.yaml
aws --region us-east-1 cloudformation validate-template --template-body file://deploy/aws-ec2/secure-edge.yaml
ALLOW_AWS_DEPLOY=1 deploy/aws-ec2/tests/smoke_secure.sh
```