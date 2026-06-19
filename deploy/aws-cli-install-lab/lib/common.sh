#!/usr/bin/env bash

set -euo pipefail

CLI_INSTALL_LAB_DIR="${CLI_INSTALL_LAB_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
REPO_ROOT="${REPO_ROOT:-$(cd "$CLI_INSTALL_LAB_DIR/../.." && pwd)}"
TEMPLATE_FILE="$CLI_INSTALL_LAB_DIR/lab.yaml"

DEFAULT_STACK_NAME="crystal-lattice-cli-install-lab"
STACK_NAME="$DEFAULT_STACK_NAME"
REGION="${AWS_REGION:-us-east-1}"
VPC_ID=""
SUBNET_ID=""
LINUX_INSTANCE_TYPE="t3.small"
WINDOWS_INSTANCE_TYPE="t3.large"
NAME_PREFIX="$DEFAULT_STACK_NAME"
VERSION="0.1.0"
BASE_URL="https://download.crystallattice.dev/crystal-lattice-cli"
INCLUDE_ENV_FILE=""
LINUX_LAB_DIR="/home/ssm-user/crystal-lattice-cli-manual-lab"
WINDOWS_LAB_DIR='C:\cl-lab'
JSON_OUTPUT=0
SKIP_SETUP=0

usage_common() {
  cat <<'USAGE'
Common options:
  --stack-name NAME
  --region REGION
  --vpc-id VPC_ID
  --subnet-id SUBNET_ID
  --linux-instance-type TYPE
  --windows-instance-type TYPE
  --name-prefix NAME
  --version VERSION
  --base-url URL
  --include-env-file PATH
  --linux-lab-dir PATH
  --windows-lab-dir PATH
  --skip-setup
  --json

Defaults:
  stack name:             crystal-lattice-cli-install-lab
  region:                 us-east-1
  Linux instance type:    t3.small
  Windows instance type:  t3.large
  download base URL:      https://download.crystallattice.dev/crystal-lattice-cli
  Linux lab dir:          /home/ssm-user/crystal-lattice-cli-manual-lab
  Windows lab dir:        C:\cl-lab

If --vpc-id/--subnet-id are omitted, up.sh uses the default VPC and one default
public subnet in the selected region.
USAGE
}

parse_common_args() {
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --stack-name) STACK_NAME="$2"; shift 2 ;;
      --region) REGION="$2"; shift 2 ;;
      --vpc-id) VPC_ID="$2"; shift 2 ;;
      --subnet-id) SUBNET_ID="$2"; shift 2 ;;
      --linux-instance-type) LINUX_INSTANCE_TYPE="$2"; shift 2 ;;
      --windows-instance-type) WINDOWS_INSTANCE_TYPE="$2"; shift 2 ;;
      --name-prefix) NAME_PREFIX="$2"; shift 2 ;;
      --version) VERSION="$2"; shift 2 ;;
      --base-url) BASE_URL="$2"; shift 2 ;;
      --include-env-file) INCLUDE_ENV_FILE="$2"; shift 2 ;;
      --linux-lab-dir) LINUX_LAB_DIR="$2"; shift 2 ;;
      --windows-lab-dir) WINDOWS_LAB_DIR="$2"; shift 2 ;;
      --skip-setup) SKIP_SETUP=1; shift ;;
      --json) JSON_OUTPUT=1; shift ;;
      --help|-h) usage_common; exit 0 ;;
      *) echo "Unknown option: $1" >&2; usage_common >&2; exit 2 ;;
    esac
  done
  if [ "$NAME_PREFIX" = "$DEFAULT_STACK_NAME" ]; then
    NAME_PREFIX="$STACK_NAME"
  fi
}

require_aws_deploy_enabled() {
  if [ "${ALLOW_AWS_DEPLOY:-}" != "1" ]; then
    echo "Set ALLOW_AWS_DEPLOY=1 to create, update, or delete AWS resources." >&2
    exit 2
  fi
}

aws_out() {
  aws --region "$REGION" "$@"
}

stack_exists() {
  aws_out cloudformation describe-stacks --stack-name "$STACK_NAME" >/dev/null 2>&1
}

stack_output() {
  local key="$1"
  aws_out cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='$key'].OutputValue | [0]" \
    --output text
}

resolve_default_vpc_and_subnet() {
  if [ -z "$VPC_ID" ]; then
    VPC_ID="$(
      aws_out ec2 describe-vpcs \
        --filters Name=is-default,Values=true \
        --query 'Vpcs[0].VpcId' \
        --output text
    )"
    if [ -z "$VPC_ID" ] || [ "$VPC_ID" = "None" ]; then
      echo "Could not find default VPC. Pass --vpc-id and --subnet-id." >&2
      exit 1
    fi
  fi

  if [ -z "$SUBNET_ID" ]; then
    SUBNET_ID="$(
      aws_out ec2 describe-subnets \
        --filters "Name=vpc-id,Values=$VPC_ID" Name=default-for-az,Values=true \
        --query 'Subnets[0].SubnetId' \
        --output text
    )"
    if [ -z "$SUBNET_ID" ] || [ "$SUBNET_ID" = "None" ]; then
      echo "Could not find default subnet in $VPC_ID. Pass --subnet-id." >&2
      exit 1
    fi
  fi
}

wait_for_ssm_instance() {
  local instance_id="$1"
  local label="$2"
  local deadline=$((SECONDS + 1200))
  local status
  echo "Waiting for $label instance to register with SSM: $instance_id" >&2
  while [ "$SECONDS" -lt "$deadline" ]; do
    status="$(
      aws_out ssm describe-instance-information \
        --filters "Key=InstanceIds,Values=$instance_id" \
        --query 'InstanceInformationList[0].PingStatus' \
        --output text 2>/dev/null || true
    )"
    if [ "$status" = "Online" ]; then
      return 0
    fi
    sleep 10
  done
  echo "Timed out waiting for $label instance to become SSM Online: $instance_id" >&2
  return 1
}

wait_ssm_command() {
  local command_id="$1"
  local instance_id="$2"
  local timeout="${3:-900}"
  local deadline=$((SECONDS + timeout))
  local status
  while [ "$SECONDS" -lt "$deadline" ]; do
    status="$(
      aws_out ssm get-command-invocation \
        --command-id "$command_id" \
        --instance-id "$instance_id" \
        --query Status \
        --output text 2>/dev/null || true
    )"
    case "$status" in
      Success) return 0 ;;
      Failed|Cancelled|TimedOut|Cancelling)
        aws_out ssm get-command-invocation \
          --command-id "$command_id" \
          --instance-id "$instance_id" \
          --query '{Status:Status,Stdout:StandardOutputContent,Stderr:StandardErrorContent}' \
          --output json >&2 || true
        return 1
        ;;
    esac
    sleep 5
  done
  echo "Timed out waiting for SSM command $command_id on $instance_id" >&2
  return 1
}

base64_file_one_line() {
  if base64 --help 2>&1 | grep -q -- '-w'; then
    base64 -w 0 "$1"
  else
    base64 < "$1" | tr -d '\n'
  fi
}

windows_lab_dir_git_bash_path() {
  case "$WINDOWS_LAB_DIR" in
    [A-Za-z]:\\*)
      local drive rest
      drive="$(printf '%s' "${WINDOWS_LAB_DIR%%:*}" | tr '[:upper:]' '[:lower:]')"
      rest="${WINDOWS_LAB_DIR#?:}"
      rest="${rest//\\//}"
      printf '/%s%s\n' "$drive" "$rest"
      ;;
    *)
      printf '%s\n' "$WINDOWS_LAB_DIR"
      ;;
  esac
}

print_lab_outputs() {
  local linux_instance windows_instance linux_private windows_private windows_bash_dir
  linux_instance="$(stack_output LinuxInstanceId)"
  windows_instance="$(stack_output WindowsInstanceId)"
  linux_private="$(stack_output LinuxPrivateIp)"
  windows_private="$(stack_output WindowsPrivateIp)"
  windows_bash_dir="$(windows_lab_dir_git_bash_path)"

  if [ "$JSON_OUTPUT" -eq 1 ]; then
    printf '{"AWS_REGION":"%s","STACK_NAME":"%s","LINUX_INSTANCE_ID":"%s","WINDOWS_INSTANCE_ID":"%s","LINUX_PRIVATE_IP":"%s","WINDOWS_PRIVATE_IP":"%s","LINUX_LAB_DIR":"%s","WINDOWS_LAB_DIR":"%s","BASE_URL":"%s","VERSION":"%s"}\n' \
      "$REGION" "$STACK_NAME" "$linux_instance" "$windows_instance" "$linux_private" "$windows_private" "$LINUX_LAB_DIR" "$WINDOWS_LAB_DIR" "$BASE_URL" "$VERSION"
    return
  fi

  cat <<EOF
CLI install lab is ready.

Linux:
  instance: $linux_instance
  private IP: $linux_private
  connect:
    aws --region $REGION ssm start-session --target $linux_instance
  run:
    cd $LINUX_LAB_DIR
    ./run-cli-api-smoke.sh

Windows:
  instance: $windows_instance
  private IP: $windows_private
  connect PowerShell:
    aws --region $REGION ssm start-session --target $windows_instance --document-name AWS-StartInteractiveCommand --parameters command="powershell.exe"
  open Git Bash:
    & "C:\\Program Files\\Git\\bin\\bash.exe" -l
  run from Git Bash:
    cd $windows_bash_dir
    ./run-cli-api-smoke.sh

Download base URL:
  $BASE_URL

Version:
  $VERSION
EOF
}