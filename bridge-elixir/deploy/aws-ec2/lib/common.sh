#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BRIDGE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
STATE_DIR="${BRIDGE_AWS_EC2_STATE_DIR:-$SCRIPT_DIR/.state}"

PROFILE="secure"
STACK_NAME="crystal-lattice-bridge"
REGION="${AWS_REGION:-us-east-1}"
JSON_OUTPUT=0
KEEP_ON_FAILURE=0
INSTANCE_TYPE="${BRIDGE_AWS_EC2_INSTANCE_TYPE:-t3.micro}"
BUILDER_INSTANCE_TYPE="${BRIDGE_AWS_EC2_BUILDER_INSTANCE_TYPE:-t3.large}"
SOURCE_BUCKET="${BRIDGE_SOURCE_BUCKET:-}"
SOURCE_BUNDLE_KEY="${BRIDGE_SOURCE_BUNDLE_KEY:-}"
BRIDGE_ECR_REPOSITORY="${BRIDGE_ECR_REPOSITORY:-}"
IMAGE_TAG="${BRIDGE_IMAGE_TAG:-latest}"
BRIDGE_IMAGE_URI="${BRIDGE_IMAGE_URI:-}"
BRIDGE_TOKEN_SECRET_VALUE="${BRIDGE_TOKEN_SECRET:-}"
COOKIE_VALUE="${COOKIE:-}"
DOCKER_PLATFORM="${BRIDGE_DOCKER_PLATFORM:-linux/amd64}"
CPU_ARCHITECTURE="${BRIDGE_CPU_ARCHITECTURE:-X86_64}"
BUILD_METHOD="${BRIDGE_AWS_BUILDER:-codebuild}"

usage_common() {
  cat <<'USAGE'
Common options:
  --profile secure
  --stack-name NAME
  --region REGION
  --instance-type INSTANCE_TYPE
  --builder-instance-type INSTANCE_TYPE
  --source-bucket BUCKET
  --source-bundle-key KEY
  --bridge-ecr-repository NAME
  --image-tag TAG
  --bridge-image-uri URI
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
      --profile) PROFILE="$2"; shift 2 ;;
      --stack-name) STACK_NAME="$2"; shift 2 ;;
      --region) REGION="$2"; shift 2 ;;
      --instance-type) INSTANCE_TYPE="$2"; shift 2 ;;
      --builder-instance-type) BUILDER_INSTANCE_TYPE="$2"; shift 2 ;;
      --source-bucket) SOURCE_BUCKET="$2"; shift 2 ;;
      --source-bundle-key) SOURCE_BUNDLE_KEY="$2"; shift 2 ;;
      --bridge-ecr-repository) BRIDGE_ECR_REPOSITORY="$2"; shift 2 ;;
      --image-tag) IMAGE_TAG="$2"; shift 2 ;;
      --bridge-image-uri) BRIDGE_IMAGE_URI="$2"; shift 2 ;;
      --docker-platform) DOCKER_PLATFORM="$2"; shift 2 ;;
      --cpu-architecture) CPU_ARCHITECTURE="$2"; shift 2 ;;
      --builder) BUILD_METHOD="$2"; shift 2 ;;
      --json) JSON_OUTPUT=1; shift ;;
      --keep-on-failure) KEEP_ON_FAILURE=1; shift ;;
      --help|-h) usage_common; exit 0 ;;
      *) echo "Unknown option: $1" >&2; usage_common >&2; exit 2 ;;
    esac
  done
}

require_aws_deploy_enabled() {
  if [ "${ALLOW_AWS_DEPLOY:-}" != "1" ] && [ "${RUN_AWS_BRIDGE_TESTS:-}" != "1" ]; then
    echo "Set ALLOW_AWS_DEPLOY=1 to create AWS resources." >&2
    exit 2
  fi
}

assert_supported_profile() {
  case "$PROFILE" in
    secure) ;;
    *) echo "Unsupported profile: $PROFILE" >&2; exit 2 ;;
  esac
}

state_file() {
  mkdir -p "$STATE_DIR"
  echo "$STATE_DIR/${STACK_NAME}.${PROFILE}.env"
}

load_state() {
  local file
  file="$(state_file)"
  if [ -f "$file" ]; then
    # shellcheck disable=SC1090
    source "$file"
  fi
}

save_state() {
  local file
  file="$(state_file)"
  cat >"$file" <<EOF_STATE
STACK_NAME='$STACK_NAME'
PROFILE='$PROFILE'
REGION='$REGION'
BRIDGE_HTTP_URL='${BRIDGE_HTTP_URL:-}'
BRIDGE_WEBSOCKET_URL='${BRIDGE_WEBSOCKET_URL:-}'
BRIDGE_EC2_URL='${BRIDGE_EC2_URL:-}'
BRIDGE_CLOUDFRONT_DOMAIN='${BRIDGE_CLOUDFRONT_DOMAIN:-}'
BRIDGE_DISTRIBUTION_ID='${BRIDGE_DISTRIBUTION_ID:-}'
BRIDGE_INSTANCE_ID='${BRIDGE_INSTANCE_ID:-}'
SOURCE_BUCKET='${SOURCE_BUCKET:-}'
SOURCE_BUNDLE_KEY='${SOURCE_BUNDLE_KEY:-}'
BRIDGE_ECR_REPOSITORY='${BRIDGE_ECR_REPOSITORY:-}'
IMAGE_TAG='${IMAGE_TAG:-}'
BRIDGE_IMAGE_URI='${BRIDGE_IMAGE_URI:-}'
BRIDGE_TOKEN_SECRET_VALUE='${BRIDGE_TOKEN_SECRET_VALUE:-}'
COOKIE_VALUE='${COOKIE_VALUE:-}'
DOCKER_PLATFORM='${DOCKER_PLATFORM:-}'
CPU_ARCHITECTURE='${CPU_ARCHITECTURE:-}'
INSTANCE_TYPE='${INSTANCE_TYPE:-}'
BUILDER_INSTANCE_TYPE='${BUILDER_INSTANCE_TYPE:-}'
BUILD_METHOD='${BUILD_METHOD:-}'
EOF_STATE
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
    --tags Project=crystal-lattice Component=bridge Purpose="${BRIDGE_AWS_PURPOSE:-user}" StackName="$STACK_NAME" \
    >&2
}

delete_stack_if_exists() {
  local stack="$1"
  if stack_exists "$stack"; then
    aws_out cloudformation delete-stack --stack-name "$stack"
    aws_out cloudformation wait stack-delete-complete --stack-name "$stack"
  fi
}

origin_stack_name() { echo "${STACK_NAME}-origin"; }
edge_stack_name() { echo "${STACK_NAME}-edge"; }
builder_stack_name() { echo "${STACK_NAME}-builder"; }

ensure_secrets() {
  if [ -z "${BRIDGE_TOKEN_SECRET_VALUE:-}" ]; then
    BRIDGE_TOKEN_SECRET_VALUE="${BRIDGE_TOKEN_SECRET:-$(openssl rand -hex 32)}"
  fi
  if [ -z "${COOKIE_VALUE:-}" ]; then
    COOKIE_VALUE="${COOKIE:-$(openssl rand -hex 24)}"
  fi
}

ensure_source_bucket() {
  if [ -n "$SOURCE_BUCKET" ]; then
    return
  fi
  local account
  account="$(aws sts get-caller-identity --query Account --output text)"
  SOURCE_BUCKET="crystal-lattice-bridge-ec2-${account}-${REGION}"
  if ! aws_out s3api head-bucket --bucket "$SOURCE_BUCKET" >/dev/null 2>&1; then
    if [ "$REGION" = "us-east-1" ]; then
      aws_out s3api create-bucket --bucket "$SOURCE_BUCKET" >/dev/null
    else
      aws_out s3api create-bucket --bucket "$SOURCE_BUCKET" --create-bucket-configuration "LocationConstraint=$REGION" >/dev/null
    fi
  fi
}

ensure_artifact_keys() {
  SOURCE_BUNDLE_KEY="${SOURCE_BUNDLE_KEY:-${STACK_NAME}/bridge-source.tar.gz}"
  BRIDGE_ECR_REPOSITORY="${BRIDGE_ECR_REPOSITORY:-${STACK_NAME}/bridge}"
  IMAGE_TAG="${IMAGE_TAG:-latest}"
}

upload_source_bundle() {
  ensure_source_bucket
  ensure_artifact_keys
  local tmp
  tmp="$(mktemp -t bridge-source.XXXXXX.tar.gz)"
  tar --exclude '_build' --exclude 'deps' --exclude '.elixir_ls' -czf "$tmp" -C "$BRIDGE_DIR" .
  aws_out s3 cp "$tmp" "s3://${SOURCE_BUCKET}/${SOURCE_BUNDLE_KEY}" >/dev/null
  rm -f "$tmp"
}

ensure_artifacts_available() {
  ensure_source_bucket
  ensure_artifact_keys
  if [ -z "${BRIDGE_IMAGE_URI:-}" ]; then
    echo "Missing prebuilt bridge image URI. Run deploy/aws-ec2/build.sh first for stack '$STACK_NAME'." >&2
    return 1
  fi
  docker_manifest_exists "$BRIDGE_IMAGE_URI"
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
    status="$(aws_out ssm get-command-invocation --command-id "$command_id" --instance-id "$instance_id" --query Status --output text 2>/dev/null || true)"
    case "$status" in
      Success) return 0 ;;
      Failed|Cancelled|TimedOut|Cancelling)
        aws_out ssm get-command-invocation --command-id "$command_id" --instance-id "$instance_id" --query StandardErrorContent --output text >&2 || true
        return 1
        ;;
    esac
    sleep 15
  done
  echo "Timed out waiting for SSM command $command_id on $instance_id" >&2
  return 1
}

print_bridge_output() {
  if [ "$JSON_OUTPUT" -eq 1 ]; then
    printf '{"bridgeHttpUrl":"%s","bridgeWebSocketUrl":"%s","cloudFrontDomain":"%s","cloudFrontDistributionId":"%s","ec2HttpUrl":"%s","instanceId":"%s"}\n' \
      "$BRIDGE_HTTP_URL" "$BRIDGE_WEBSOCKET_URL" "$BRIDGE_CLOUDFRONT_DOMAIN" "$BRIDGE_DISTRIBUTION_ID" "$BRIDGE_EC2_URL" "$BRIDGE_INSTANCE_ID"
  else
    echo "BridgeHttpUrl=$BRIDGE_HTTP_URL"
    echo "BridgeWebSocketUrl=$BRIDGE_WEBSOCKET_URL"
    echo "CloudFrontDomain=$BRIDGE_CLOUDFRONT_DOMAIN"
    echo "CloudFrontDistributionId=$BRIDGE_DISTRIBUTION_ID"
    echo "BridgeEc2Url=$BRIDGE_EC2_URL"
    echo "InstanceId=$BRIDGE_INSTANCE_ID"
  fi
}