#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ORCHESTRATOR_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
STATE_DIR="${CLOUD_ORCHESTRATOR_AWS_STATE_DIR:-$SCRIPT_DIR/.state}"

PROFILE="secure"
STACK_NAME="crystal-lattice-cloud-orchestrator"
REGION="${AWS_REGION:-us-east-1}"
JSON_OUTPUT=0
KEEP_ON_FAILURE=0
INSTANCE_TYPE="${CLOUD_ORCHESTRATOR_AWS_INSTANCE_TYPE:-}"
BUILDER_INSTANCE_TYPE="${CLOUD_ORCHESTRATOR_AWS_BUILDER_INSTANCE_TYPE:-t3.large}"
KEY_NAME="${CLOUD_ORCHESTRATOR_AWS_KEY_NAME:-}"
SOURCE_BUCKET="${CLOUD_ORCHESTRATOR_SOURCE_BUCKET:-}"
SOURCE_BUNDLE_KEY="${CLOUD_ORCHESTRATOR_SOURCE_BUNDLE_KEY:-}"
ORCHESTRATOR_ECR_REPOSITORY="${CLOUD_ORCHESTRATOR_ECR_REPOSITORY:-}"
RUNTIME_ECR_REPOSITORY="${CLOUD_AGENT_RUNTIME_ECR_REPOSITORY:-}"
IMAGE_TAG="${CLOUD_ORCHESTRATOR_IMAGE_TAG:-latest}"
ORCHESTRATOR_IMAGE_URI="${CLOUD_ORCHESTRATOR_IMAGE_URI:-}"
RUNTIME_IMAGE_URI="${CLOUD_AGENT_RUNTIME_IMAGE_URI:-}"
CLOUD_ORCHESTRATOR_CONTROL_TOKEN_VALUE="${CLOUD_ORCHESTRATOR_CONTROL_TOKEN:-}"
CLOUD_ORCHESTRATOR_TOKEN_SECRET_VALUE="${CLOUD_ORCHESTRATOR_TOKEN_SECRET:-}"
DOCKER_PLATFORM="${CLOUD_ORCHESTRATOR_DOCKER_PLATFORM:-linux/amd64}"
CPU_ARCHITECTURE="${CLOUD_ORCHESTRATOR_CPU_ARCHITECTURE:-X86_64}"
BUILD_METHOD="${CLOUD_ORCHESTRATOR_BUILD_METHOD:-codebuild}"

usage_common() {
  cat <<'USAGE'
Common options:
  --profile secure
  --stack-name NAME
  --region REGION
  --instance-type INSTANCE_TYPE
  --builder-instance-type INSTANCE_TYPE
  --key-name EC2_KEY_PAIR_NAME
  --source-bucket BUCKET
  --source-bundle-key KEY
  --orchestrator-ecr-repository NAME
  --runtime-ecr-repository NAME
  --image-tag TAG
  --orchestrator-image-uri URI
  --runtime-image-uri URI
  --docker-platform linux/amd64|linux/arm64
  --cpu-architecture X86_64|ARM64
  --builder codebuild
  --json
  --keep-on-failure
USAGE
}

parse_common_args() {
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --profile)
        PROFILE="$2"
        shift 2
        ;;
      --stack-name)
        STACK_NAME="$2"
        shift 2
        ;;
      --region)
        REGION="$2"
        shift 2
        ;;
      --instance-type)
        INSTANCE_TYPE="$2"
        shift 2
        ;;
      --builder-instance-type)
        BUILDER_INSTANCE_TYPE="$2"
        shift 2
        ;;
      --key-name)
        KEY_NAME="$2"
        shift 2
        ;;
      --source-bucket)
        SOURCE_BUCKET="$2"
        shift 2
        ;;
      --source-bundle-key)
        SOURCE_BUNDLE_KEY="$2"
        shift 2
        ;;
      --orchestrator-ecr-repository)
        ORCHESTRATOR_ECR_REPOSITORY="$2"
        shift 2
        ;;
      --runtime-ecr-repository)
        RUNTIME_ECR_REPOSITORY="$2"
        shift 2
        ;;
      --image-tag)
        IMAGE_TAG="$2"
        shift 2
        ;;
      --orchestrator-image-uri)
        ORCHESTRATOR_IMAGE_URI="$2"
        shift 2
        ;;
      --runtime-image-uri)
        RUNTIME_IMAGE_URI="$2"
        shift 2
        ;;
      --docker-platform)
        DOCKER_PLATFORM="$2"
        shift 2
        ;;
      --cpu-architecture)
        CPU_ARCHITECTURE="$2"
        shift 2
        ;;
      --builder)
        BUILD_METHOD="$2"
        shift 2
        ;;
      --json)
        JSON_OUTPUT=1
        shift
        ;;
      --keep-on-failure)
        KEEP_ON_FAILURE=1
        shift
        ;;
      --help|-h)
        usage_common
        exit 0
        ;;
      *)
        echo "Unknown option: $1" >&2
        usage_common >&2
        exit 2
        ;;
    esac
  done
}

require_aws_tests_enabled() {
  if [ "${ALLOW_AWS_DEPLOY:-}" != "1" ] && [ "${RUN_AWS_CLOUD_ORCHESTRATOR_TESTS:-}" != "1" ]; then
    echo "Set ALLOW_AWS_DEPLOY=1 to create AWS resources." >&2
    exit 2
  fi
}

state_file() {
  mkdir -p "$STATE_DIR"
  echo "$STATE_DIR/${STACK_NAME}.${PROFILE}.env"
}

save_state() {
  local file
  file="$(state_file)"
  cat >"$file" <<EOF_STATE
STACK_NAME='$STACK_NAME'
PROFILE='$PROFILE'
REGION='$REGION'
CLOUD_ORCHESTRATOR_URL='${CLOUD_ORCHESTRATOR_URL:-}'
CLOUD_ORCHESTRATOR_EC2_URL='${CLOUD_ORCHESTRATOR_EC2_URL:-}'
CLOUD_ORCHESTRATOR_CLOUDFRONT_DOMAIN='${CLOUD_ORCHESTRATOR_CLOUDFRONT_DOMAIN:-}'
CLOUD_ORCHESTRATOR_DISTRIBUTION_ID='${CLOUD_ORCHESTRATOR_DISTRIBUTION_ID:-}'
CLOUD_ORCHESTRATOR_INSTANCE_ID='${CLOUD_ORCHESTRATOR_INSTANCE_ID:-}'
CLOUD_ORCHESTRATOR_CONTROL_TOKEN_VALUE='${CLOUD_ORCHESTRATOR_CONTROL_TOKEN_VALUE:-}'
CLOUD_ORCHESTRATOR_TOKEN_SECRET_VALUE='${CLOUD_ORCHESTRATOR_TOKEN_SECRET_VALUE:-}'
SOURCE_BUCKET='${SOURCE_BUCKET:-}'
SOURCE_BUNDLE_KEY='${SOURCE_BUNDLE_KEY:-}'
ORCHESTRATOR_ECR_REPOSITORY='${ORCHESTRATOR_ECR_REPOSITORY:-}'
RUNTIME_ECR_REPOSITORY='${RUNTIME_ECR_REPOSITORY:-}'
IMAGE_TAG='${IMAGE_TAG:-}'
ORCHESTRATOR_IMAGE_URI='${ORCHESTRATOR_IMAGE_URI:-}'
RUNTIME_IMAGE_URI='${RUNTIME_IMAGE_URI:-}'
DOCKER_PLATFORM='${DOCKER_PLATFORM:-}'
CPU_ARCHITECTURE='${CPU_ARCHITECTURE:-}'
INSTANCE_TYPE='${INSTANCE_TYPE:-}'
BUILDER_INSTANCE_TYPE='${BUILDER_INSTANCE_TYPE:-}'
BUILD_METHOD='${BUILD_METHOD:-}'
EOF_STATE
}

load_state() {
  local file
  file="$(state_file)"
  if [ -f "$file" ]; then
    # shellcheck disable=SC1090
    source "$file"
  fi
}

aws_out() {
  aws --region "$REGION" "$@"
}

stack_exists() {
  local stack="$1"
  aws_out cloudformation describe-stacks --stack-name "$stack" >/dev/null 2>&1
}

stack_output() {
  local stack="$1"
  local key="$2"
  aws_out cloudformation describe-stacks \
    --stack-name "$stack" \
    --query "Stacks[0].Outputs[?OutputKey=='$key'].OutputValue | [0]" \
    --output text
}

deploy_stack() {
  local stack="$1"
  local template="$2"
  shift 2
  aws_out cloudformation deploy \
    --stack-name "$stack" \
    --template-file "$template" \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides "$@" \
    --tags Project=crystal-lattice Component=cloud-orchestrator Purpose="${CLOUD_ORCHESTRATOR_AWS_PURPOSE:-user}" StackName="$STACK_NAME" \
    >&2
}

assert_supported_profile() {
  case "$PROFILE" in
    secure)
      ;;
    *)
      echo "Unsupported profile: $PROFILE" >&2
      exit 2
      ;;
  esac
}

origin_stack_name() {
  echo "${STACK_NAME}-origin"
}

edge_stack_name() {
  echo "${STACK_NAME}-edge"
}

builder_stack_name() {
  echo "${STACK_NAME}-builder"
}

delete_stack_if_exists() {
  local stack="$1"
  if stack_exists "$stack"; then
    aws_out cloudformation delete-stack --stack-name "$stack"
    aws_out cloudformation wait stack-delete-complete --stack-name "$stack"
  fi
}

ensure_secrets() {
  if [ -z "${CLOUD_ORCHESTRATOR_CONTROL_TOKEN_VALUE:-}" ]; then
    CLOUD_ORCHESTRATOR_CONTROL_TOKEN_VALUE="$(openssl rand -hex 32)"
  fi
  if [ -z "${CLOUD_ORCHESTRATOR_TOKEN_SECRET_VALUE:-}" ]; then
    CLOUD_ORCHESTRATOR_TOKEN_SECRET_VALUE="$(openssl rand -hex 32)"
  fi
}

ensure_source_bucket() {
  if [ -n "$SOURCE_BUCKET" ]; then
    return
  fi
  local account
  account="$(aws sts get-caller-identity --query Account --output text)"
  SOURCE_BUCKET="crystal-lattice-cloud-orchestrator-${account}-${REGION}"
  if ! aws_out s3api head-bucket --bucket "$SOURCE_BUCKET" >/dev/null 2>&1; then
    if [ "$REGION" = "us-east-1" ]; then
      aws_out s3api create-bucket --bucket "$SOURCE_BUCKET" >/dev/null
    else
      aws_out s3api create-bucket \
        --bucket "$SOURCE_BUCKET" \
        --create-bucket-configuration "LocationConstraint=$REGION" >/dev/null
    fi
  fi
}

detect_docker_platform() {
  local arch
  arch="$(docker version --format '{{.Server.Arch}}' 2>/dev/null || uname -m)"
  case "$arch" in
    arm64|aarch64)
      echo "linux/arm64"
      ;;
    amd64|x86_64)
      echo "linux/amd64"
      ;;
    *)
      echo "linux/amd64"
      ;;
  esac
}

ensure_platform_default() {
  if [ -z "$CPU_ARCHITECTURE" ]; then
    case "$DOCKER_PLATFORM" in
      linux/arm64)
        CPU_ARCHITECTURE="ARM64"
        ;;
      *)
        CPU_ARCHITECTURE="X86_64"
        ;;
    esac
  fi

  if [ -z "$INSTANCE_TYPE" ]; then
    case "$CPU_ARCHITECTURE" in
      ARM64)
        INSTANCE_TYPE="t4g.micro"
        ;;
      *)
        INSTANCE_TYPE="t3.micro"
        ;;
    esac
  fi
}

ensure_artifact_keys() {
  SOURCE_BUNDLE_KEY="${SOURCE_BUNDLE_KEY:-${STACK_NAME}/cloud-orchestrator-source.tar.gz}"
  ORCHESTRATOR_ECR_REPOSITORY="${ORCHESTRATOR_ECR_REPOSITORY:-${STACK_NAME}/cloud-orchestrator}"
  RUNTIME_ECR_REPOSITORY="${RUNTIME_ECR_REPOSITORY:-${STACK_NAME}/cloud-agent-runtime}"
  IMAGE_TAG="${IMAGE_TAG:-latest}"
}

upload_source_bundle() {
  ensure_source_bucket
  ensure_artifact_keys
  local tmp
  tmp="$(mktemp -t cloud-orchestrator-source.XXXXXX.tar.gz)"
  tar \
    --exclude '_build' \
    --exclude 'deps' \
    --exclude '.data' \
    --exclude '.elixir_ls' \
    -czf "$tmp" \
    -C "$ORCHESTRATOR_DIR" .
  aws_out s3 cp "$tmp" "s3://${SOURCE_BUCKET}/${SOURCE_BUNDLE_KEY}" >/dev/null
  rm -f "$tmp"
}

ensure_artifacts_available() {
  ensure_source_bucket
  ensure_artifact_keys
  ensure_platform_default
  if [ -z "${ORCHESTRATOR_IMAGE_URI:-}" ] || [ -z "${RUNTIME_IMAGE_URI:-}" ]; then
    echo "Missing prebuilt cloud orchestrator image URIs. Run deploy/aws-ec2/build.sh first for stack '$STACK_NAME'." >&2
    return 1
  fi
  docker_manifest_exists "$ORCHESTRATOR_IMAGE_URI"
  docker_manifest_exists "$RUNTIME_IMAGE_URI"
}

ensure_ecr_repository() {
  local repo="$1"
  if ! aws_out ecr describe-repositories --repository-names "$repo" >/dev/null 2>&1; then
    aws_out ecr create-repository --repository-name "$repo" >/dev/null
  fi
}

ecr_uri_for() {
  local repo="$1"
  local tag="$2"
  local account
  account="$(aws sts get-caller-identity --query Account --output text)"
  echo "${account}.dkr.ecr.${REGION}.amazonaws.com/${repo}:${tag}"
}

docker_manifest_exists() {
  local image_uri="$1"
  local without_registry="${image_uri#*/}"
  local repo="${without_registry%:*}"
  local tag="${image_uri##*:}"
  aws_out ecr describe-images \
    --repository-name "$repo" \
    --image-ids "imageTag=$tag" >/dev/null
}

wait_http_health() {
  local url="$1"
  local deadline=$((SECONDS + 900))

  while [ "$SECONDS" -lt "$deadline" ]; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 10
  done

  echo "Timed out waiting for $url" >&2
  return 1
}

wait_ssm_command() {
  local command_id="$1"
  local instance_id="$2"
  local deadline=$((SECONDS + ${3:-3600}))
  local status

  while [ "$SECONDS" -lt "$deadline" ]; do
    status="$(aws_out ssm get-command-invocation \
      --command-id "$command_id" \
      --instance-id "$instance_id" \
      --query Status \
      --output text 2>/dev/null || true)"

    case "$status" in
      Success)
        return 0
        ;;
      Failed|Cancelled|TimedOut|Cancelling)
        aws_out ssm get-command-invocation \
          --command-id "$command_id" \
          --instance-id "$instance_id" \
          --query StandardErrorContent \
          --output text >&2 || true
        return 1
        ;;
    esac

    sleep 15
  done

  echo "Timed out waiting for SSM command $command_id on $instance_id" >&2
  aws_out ssm get-command-invocation \
    --command-id "$command_id" \
    --instance-id "$instance_id" \
    --query StandardOutputContent \
    --output text >&2 || true
  return 1
}

print_orchestrator_output() {
  local url="$1"
  local ec2_url="$2"
  local cloudfront_domain="$3"
  local distribution_id="$4"
  local instance_id="$5"

  if [ "$JSON_OUTPUT" -eq 1 ]; then
    printf '{"cloudOrchestratorUrl":"%s","cloudOrchestratorHealthUrl":"%s","orchestratorUrl":"%s","cloudFrontUrl":"%s","ec2HttpUrl":"%s","cloudFrontDomain":"%s","cloudFrontDistributionId":"%s","instanceId":"%s","stackName":"%s","region":"%s","controlToken":"%s"}\n' \
      "$url" "${url%/}/health" "$url" "$url" "$ec2_url" "$cloudfront_domain" "$distribution_id" "$instance_id" "$STACK_NAME" "$REGION" "$CLOUD_ORCHESTRATOR_CONTROL_TOKEN_VALUE"
  else
    echo "CloudOrchestratorUrl=$url"
    echo "CloudOrchestratorHealthUrl=${url%/}/health"
    echo "CloudOrchestratorEc2Url=$ec2_url"
    echo "CloudFrontDomain=$cloudfront_domain"
    echo "CloudFrontDistributionId=$distribution_id"
    echo "InstanceId=$instance_id"
    echo "ControlToken=$CLOUD_ORCHESTRATOR_CONTROL_TOKEN_VALUE"
  fi
}