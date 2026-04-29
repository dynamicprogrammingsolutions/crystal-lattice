#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BRIDGE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
STATE_DIR="${BRIDGE_AWS_STATE_DIR:-$SCRIPT_DIR/.state}"

PROFILE="secure"
STACK_NAME="crystal-lattice-bridge"
REGION="${AWS_REGION:-us-east-1}"
IMAGE_URI="${BRIDGE_IMAGE_URI:-}"
JSON_OUTPUT=0
KEEP_ON_FAILURE=0
DOMAIN_NAME="${BRIDGE_DOMAIN:-}"
HOSTED_ZONE_ID="${AWS_HOSTED_ZONE_ID:-}"
ENABLE_AUTOSCALING=0
MIN_TASKS=1
MAX_TASKS=3
CPU_ARCHITECTURE="${BRIDGE_FARGATE_CPU_ARCHITECTURE:-}"
DOCKER_PLATFORM="${BRIDGE_DOCKER_PLATFORM:-}"

usage_common() {
  cat <<'USAGE'
Common options:
  --profile secure|public-task
  --stack-name NAME
  --region REGION
  --image-uri IMAGE_URI
  --domain DOMAIN_NAME
  --hosted-zone-id HOSTED_ZONE_ID
  --autoscaling
  --min-tasks N
  --max-tasks N
  --cpu-architecture X86_64|ARM64
  --docker-platform linux/amd64|linux/arm64
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
      --image-uri)
        IMAGE_URI="$2"
        shift 2
        ;;
      --domain)
        DOMAIN_NAME="$2"
        shift 2
        ;;
      --hosted-zone-id)
        HOSTED_ZONE_ID="$2"
        shift 2
        ;;
      --autoscaling)
        ENABLE_AUTOSCALING=1
        shift
        ;;
      --min-tasks)
        MIN_TASKS="$2"
        shift 2
        ;;
      --max-tasks)
        MAX_TASKS="$2"
        shift 2
        ;;
      --cpu-architecture)
        CPU_ARCHITECTURE="$2"
        shift 2
        ;;
      --docker-platform)
        DOCKER_PLATFORM="$2"
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
  if [ "${RUN_AWS_BRIDGE_TESTS:-}" != "1" ]; then
    echo "Set RUN_AWS_BRIDGE_TESTS=1 to create AWS resources." >&2
    exit 2
  fi
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
  mkdir -p "$(dirname "$file")"
  cat >"$file" <<EOF_STATE
STACK_NAME='$STACK_NAME'
PROFILE='$PROFILE'
REGION='$REGION'
IMAGE_URI='$IMAGE_URI'
BRIDGE_TOKEN_SECRET_VALUE='${BRIDGE_TOKEN_SECRET_VALUE:-}'
COOKIE_VALUE='${COOKIE_VALUE:-}'
DOMAIN_NAME='$DOMAIN_NAME'
HOSTED_ZONE_ID='$HOSTED_ZONE_ID'
EOF_STATE
}

ensure_secrets() {
  if [ -z "${BRIDGE_TOKEN_SECRET_VALUE:-}" ]; then
    BRIDGE_TOKEN_SECRET_VALUE="${BRIDGE_TOKEN_SECRET:-$(openssl rand -hex 32)}"
  fi
  if [ -z "${COOKIE_VALUE:-}" ]; then
    COOKIE_VALUE="${COOKIE:-$(openssl rand -hex 24)}"
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

ensure_platform_defaults() {
  if [ -z "$DOCKER_PLATFORM" ]; then
    DOCKER_PLATFORM="$(detect_docker_platform)"
  fi

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

ensure_image_uri() {
  if [ -n "$IMAGE_URI" ]; then
    return
  fi

  local account repo tag repo_uri
  account="$(aws sts get-caller-identity --query Account --output text)"
  repo="crystal-lattice-bridge/${STACK_NAME}"
  tag="${BRIDGE_IMAGE_TAG:-latest}"
  repo_uri="${account}.dkr.ecr.${REGION}.amazonaws.com/${repo}"

  aws_out ecr describe-repositories --repository-names "$repo" >/dev/null 2>&1 ||
    aws_out ecr create-repository --repository-name "$repo" >/dev/null

  aws_out ecr get-login-password |
    docker login --username AWS --password-stdin "${account}.dkr.ecr.${REGION}.amazonaws.com" >/dev/null

  ensure_platform_defaults
  docker build --platform "$DOCKER_PLATFORM" -t "${repo_uri}:${tag}" "$BRIDGE_DIR" >&2
  docker push "${repo_uri}:${tag}" >/dev/null

  IMAGE_URI="${repo_uri}:${tag}"
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

print_bridge_output() {
  local http_url="$1"
  local websocket_url="$2"
  local domain="$3"

  if [ "$JSON_OUTPUT" -eq 1 ]; then
    printf '{"bridgeHttpUrl":"%s","bridgeWebSocketUrl":"%s","cloudFrontDomain":"%s"}\n' \
      "$http_url" "$websocket_url" "$domain"
  else
    echo "BridgeHttpUrl=$http_url"
    echo "BridgeWebSocketUrl=$websocket_url"
    [ -n "$domain" ] && echo "CloudFrontDomain=$domain"
  fi
}