#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=deploy/aws-ec2/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

parse_common_args "$@"
require_aws_tests_enabled
assert_supported_profile
load_state
parse_common_args "$@"
ensure_secrets
ensure_artifacts_available

origin_stack="$(origin_stack_name)"
edge_stack="$(edge_stack_name)"

deploy_stack "$origin_stack" "$SCRIPT_DIR/secure-origin.yaml" \
  StackName="$STACK_NAME" \
  OrchestratorImageUri="$ORCHESTRATOR_IMAGE_URI" \
  RuntimeImageUri="$RUNTIME_IMAGE_URI" \
  InstanceType="$INSTANCE_TYPE" \
  CpuArchitecture="$CPU_ARCHITECTURE" \
  KeyName="$KEY_NAME" \
  ControlToken="$CLOUD_ORCHESTRATOR_CONTROL_TOKEN_VALUE" \
  TokenSecret="$CLOUD_ORCHESTRATOR_TOKEN_SECRET_VALUE"

CLOUD_ORCHESTRATOR_EC2_URL="$(stack_output "$origin_stack" Ec2HttpUrl)"
CLOUD_ORCHESTRATOR_INSTANCE_ID="$(stack_output "$origin_stack" InstanceId)"
origin_domain="$(stack_output "$origin_stack" Ec2PublicDnsName)"

deploy_stack "$edge_stack" "$SCRIPT_DIR/secure-edge.yaml" \
  StackName="$STACK_NAME" \
  OriginDomainName="$origin_domain"

CLOUD_ORCHESTRATOR_URL="$(stack_output "$edge_stack" CloudOrchestratorUrl)"
CLOUD_ORCHESTRATOR_CLOUDFRONT_DOMAIN="$(stack_output "$edge_stack" CloudFrontDomain)"
CLOUD_ORCHESTRATOR_DISTRIBUTION_ID="$(stack_output "$edge_stack" CloudFrontDistributionId)"
save_state

wait_http_health "${CLOUD_ORCHESTRATOR_EC2_URL%/}/health"

ssm_params="$(mktemp -t cloud-orchestrator-ssm.XXXXXX.json)"
python3 - "$ssm_params" "$CLOUD_ORCHESTRATOR_URL" "$CLOUD_ORCHESTRATOR_CONTROL_TOKEN_VALUE" "$CLOUD_ORCHESTRATOR_TOKEN_SECRET_VALUE" <<'PY'
import json
import sys

path, public_url, control_token, token_secret = sys.argv[1:5]
commands = [
    "docker rm -f cloud-orchestrator-single || true",
    (
        "docker run -d --name cloud-orchestrator-single --restart unless-stopped "
        "-p 4100:4100 "
        "-v /var/run/docker.sock:/var/run/docker.sock "
        "-v /var/lib/cloud-orchestrator:/var/lib/cloud-orchestrator "
        "--add-host host.docker.internal:host-gateway "
        "-e MIX_ENV=prod "
        "-e PORT=4100 "
        "-e SECRET_KEY_BASE=$(openssl rand -hex 64) "
        "-e CLOUD_ORCHESTRATOR_RUNNER=docker "
        f"-e CLOUD_ORCHESTRATOR_PUBLIC_URL={public_url} "
        f"-e CLOUD_ORCHESTRATOR_CONTROL_TOKEN={control_token} "
        f"-e CLOUD_ORCHESTRATOR_TOKEN_SECRET={token_secret} "
        "-e CLOUD_ORCHESTRATOR_DATA_DIR=/var/lib/cloud-orchestrator "
        "-e CLOUD_ORCHESTRATOR_HOST_DATA_DIR=/var/lib/cloud-orchestrator "
        "-e CLOUD_ORCHESTRATOR_DOCKER_PROXY_HOST=host.docker.internal "
        "-e CLOUD_ORCHESTRATOR_DOCKER_BIND_HOST=172.17.0.1 "
        "-e CLOUD_WORKSPACE_DIR=/workspace "
        "cloud-orchestrator:latest"
    ),
]
with open(path, "w", encoding="utf-8") as f:
    json.dump({"commands": commands}, f)
PY

command_id="$(aws_out ssm send-command \
  --instance-ids "$CLOUD_ORCHESTRATOR_INSTANCE_ID" \
  --document-name AWS-RunShellScript \
  --parameters "file://$ssm_params" \
  --query Command.CommandId \
  --output text)"
rm -f "$ssm_params"
wait_ssm_command "$command_id" "$CLOUD_ORCHESTRATOR_INSTANCE_ID" 900

wait_http_health "${CLOUD_ORCHESTRATOR_URL%/}/health"
print_orchestrator_output "$CLOUD_ORCHESTRATOR_URL" "$CLOUD_ORCHESTRATOR_EC2_URL" "$CLOUD_ORCHESTRATOR_CLOUDFRONT_DOMAIN" "$CLOUD_ORCHESTRATOR_DISTRIBUTION_ID" "$CLOUD_ORCHESTRATOR_INSTANCE_ID"