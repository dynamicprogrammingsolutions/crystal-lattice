#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
STATE_DIR="${CRYSTAL_LATTICE_AWS_EC2_STATE_DIR:-$SCRIPT_DIR/.state}"

PROFILE="secure"
STACK_NAME="crystal-lattice-combined"
REGION="${AWS_REGION:-us-east-1}"
JSON_OUTPUT=0
INSTANCE_TYPE="${CRYSTAL_LATTICE_AWS_EC2_INSTANCE_TYPE:-t3.micro}"
KEY_NAME="${CRYSTAL_LATTICE_AWS_EC2_KEY_NAME:-}"
IMAGE_TAG="${CRYSTAL_LATTICE_IMAGE_TAG:-latest}"
DOCKER_PLATFORM="${CRYSTAL_LATTICE_DOCKER_PLATFORM:-linux/amd64}"
CPU_ARCHITECTURE="${CRYSTAL_LATTICE_CPU_ARCHITECTURE:-X86_64}"
BUILD_METHOD="${CRYSTAL_LATTICE_AWS_BUILDER:-codebuild}"

BRIDGE_IMAGE_URI="${BRIDGE_IMAGE_URI:-}"
ORCHESTRATOR_IMAGE_URI="${CLOUD_ORCHESTRATOR_IMAGE_URI:-}"
RUNTIME_IMAGE_URI="${CLOUD_AGENT_RUNTIME_IMAGE_URI:-}"
BRIDGE_TOKEN_SECRET_VALUE="${BRIDGE_TOKEN_SECRET:-}"
COOKIE_VALUE="${COOKIE:-}"
CLOUD_ORCHESTRATOR_CONTROL_TOKEN_VALUE="${CLOUD_ORCHESTRATOR_CONTROL_TOKEN:-}"
CLOUD_ORCHESTRATOR_TOKEN_SECRET_VALUE="${CLOUD_ORCHESTRATOR_TOKEN_SECRET:-}"

usage_common() {
  cat <<'USAGE'
Common options:
  --profile secure
  --stack-name NAME
  --region REGION
  --instance-type INSTANCE_TYPE
  --key-name EC2_KEY_PAIR_NAME
  --image-tag TAG
  --docker-platform linux/amd64|linux/arm64
  --cpu-architecture X86_64|ARM64
  --builder codebuild
  --bridge-image-uri URI
  --orchestrator-image-uri URI
  --runtime-image-uri URI
  --json
USAGE
}

parse_common_args() {
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --profile) PROFILE="$2"; shift 2 ;;
      --stack-name) STACK_NAME="$2"; shift 2 ;;
      --region) REGION="$2"; shift 2 ;;
      --instance-type) INSTANCE_TYPE="$2"; shift 2 ;;
      --key-name) KEY_NAME="$2"; shift 2 ;;
      --image-tag) IMAGE_TAG="$2"; shift 2 ;;
      --docker-platform) DOCKER_PLATFORM="$2"; shift 2 ;;
      --cpu-architecture) CPU_ARCHITECTURE="$2"; shift 2 ;;
      --builder) BUILD_METHOD="$2"; shift 2 ;;
      --bridge-image-uri) BRIDGE_IMAGE_URI="$2"; shift 2 ;;
      --orchestrator-image-uri) ORCHESTRATOR_IMAGE_URI="$2"; shift 2 ;;
      --runtime-image-uri) RUNTIME_IMAGE_URI="$2"; shift 2 ;;
      --json) JSON_OUTPUT=1; shift ;;
      --help|-h) usage_common; exit 0 ;;
      *) echo "Unknown option: $1" >&2; usage_common >&2; exit 2 ;;
    esac
  done
}

require_aws_deploy_enabled() {
  if [ "${ALLOW_AWS_DEPLOY:-}" != "1" ]; then
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
INSTANCE_TYPE='$INSTANCE_TYPE'
KEY_NAME='$KEY_NAME'
IMAGE_TAG='$IMAGE_TAG'
DOCKER_PLATFORM='$DOCKER_PLATFORM'
CPU_ARCHITECTURE='$CPU_ARCHITECTURE'
BUILD_METHOD='$BUILD_METHOD'
BRIDGE_IMAGE_URI='${BRIDGE_IMAGE_URI:-}'
ORCHESTRATOR_IMAGE_URI='${ORCHESTRATOR_IMAGE_URI:-}'
RUNTIME_IMAGE_URI='${RUNTIME_IMAGE_URI:-}'
BRIDGE_TOKEN_SECRET_VALUE='${BRIDGE_TOKEN_SECRET_VALUE:-}'
COOKIE_VALUE='${COOKIE_VALUE:-}'
CLOUD_ORCHESTRATOR_CONTROL_TOKEN_VALUE='${CLOUD_ORCHESTRATOR_CONTROL_TOKEN_VALUE:-}'
CLOUD_ORCHESTRATOR_TOKEN_SECRET_VALUE='${CLOUD_ORCHESTRATOR_TOKEN_SECRET_VALUE:-}'
COMBINED_BRIDGE_HTTP_URL='${COMBINED_BRIDGE_HTTP_URL:-}'
COMBINED_BRIDGE_WEBSOCKET_URL='${COMBINED_BRIDGE_WEBSOCKET_URL:-}'
COMBINED_ORCHESTRATOR_URL='${COMBINED_ORCHESTRATOR_URL:-}'
COMBINED_INSTANCE_ID='${COMBINED_INSTANCE_ID:-}'
COMBINED_BRIDGE_DISTRIBUTION_ID='${COMBINED_BRIDGE_DISTRIBUTION_ID:-}'
COMBINED_ORCHESTRATOR_DISTRIBUTION_ID='${COMBINED_ORCHESTRATOR_DISTRIBUTION_ID:-}'
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
    --tags Project=crystal-lattice Component=combined Purpose="${CRYSTAL_LATTICE_AWS_PURPOSE:-user}" StackName="$STACK_NAME" \
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

ensure_secrets() {
  if [ -z "${BRIDGE_TOKEN_SECRET_VALUE:-}" ]; then
    BRIDGE_TOKEN_SECRET_VALUE="${BRIDGE_TOKEN_SECRET:-$(openssl rand -hex 32)}"
  fi
  if [ -z "${COOKIE_VALUE:-}" ]; then
    COOKIE_VALUE="${COOKIE:-$(openssl rand -hex 24)}"
  fi
  if [ -z "${CLOUD_ORCHESTRATOR_CONTROL_TOKEN_VALUE:-}" ]; then
    CLOUD_ORCHESTRATOR_CONTROL_TOKEN_VALUE="${CLOUD_ORCHESTRATOR_CONTROL_TOKEN:-$(openssl rand -hex 32)}"
  fi
  if [ -z "${CLOUD_ORCHESTRATOR_TOKEN_SECRET_VALUE:-}" ]; then
    CLOUD_ORCHESTRATOR_TOKEN_SECRET_VALUE="${CLOUD_ORCHESTRATOR_TOKEN_SECRET:-$(openssl rand -hex 32)}"
  fi
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

ensure_artifacts_available() {
  if [ -z "${BRIDGE_IMAGE_URI:-}" ] || [ -z "${ORCHESTRATOR_IMAGE_URI:-}" ] || [ -z "${RUNTIME_IMAGE_URI:-}" ]; then
    echo "Missing prebuilt image URIs. Run deploy/aws-ec2/build.sh first for stack '$STACK_NAME'." >&2
    return 1
  fi
  docker_manifest_exists "$BRIDGE_IMAGE_URI"
  docker_manifest_exists "$ORCHESTRATOR_IMAGE_URI"
  docker_manifest_exists "$RUNTIME_IMAGE_URI"
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
  local deadline=$((SECONDS + ${3:-900}))
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
    sleep 10
  done
  echo "Timed out waiting for SSM command $command_id on $instance_id" >&2
  return 1
}

print_combined_output() {
  if [ "$JSON_OUTPUT" -eq 1 ]; then
    printf '{"bridgeHttpUrl":"%s","bridgeWebSocketUrl":"%s","cloudOrchestratorUrl":"%s","cloudOrchestratorHealthUrl":"%s","instanceId":"%s","bridgeDistributionId":"%s","cloudOrchestratorDistributionId":"%s","controlToken":"%s","stackName":"%s","region":"%s"}\n' \
      "$COMBINED_BRIDGE_HTTP_URL" "$COMBINED_BRIDGE_WEBSOCKET_URL" "$COMBINED_ORCHESTRATOR_URL" "${COMBINED_ORCHESTRATOR_URL%/}/health" "$COMBINED_INSTANCE_ID" "$COMBINED_BRIDGE_DISTRIBUTION_ID" "$COMBINED_ORCHESTRATOR_DISTRIBUTION_ID" "$CLOUD_ORCHESTRATOR_CONTROL_TOKEN_VALUE" "$STACK_NAME" "$REGION"
  else
    echo "BridgeHttpUrl=$COMBINED_BRIDGE_HTTP_URL"
    echo "BridgeWebSocketUrl=$COMBINED_BRIDGE_WEBSOCKET_URL"
    echo "CloudOrchestratorUrl=$COMBINED_ORCHESTRATOR_URL"
    echo "CloudOrchestratorHealthUrl=${COMBINED_ORCHESTRATOR_URL%/}/health"
    echo "InstanceId=$COMBINED_INSTANCE_ID"
    echo "BridgeDistributionId=$COMBINED_BRIDGE_DISTRIBUTION_ID"
    echo "CloudOrchestratorDistributionId=$COMBINED_ORCHESTRATOR_DISTRIBUTION_ID"
    echo "ControlToken=$CLOUD_ORCHESTRATOR_CONTROL_TOKEN_VALUE"
  fi
}