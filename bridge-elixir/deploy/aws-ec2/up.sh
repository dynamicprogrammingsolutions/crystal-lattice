#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=deploy/aws-ec2/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

parse_common_args "$@"
require_aws_deploy_enabled
assert_supported_profile
load_state
parse_common_args "$@"
ensure_secrets
ensure_artifacts_available

origin_stack="$(origin_stack_name)"
edge_stack="$(edge_stack_name)"

deploy_stack "$origin_stack" "$SCRIPT_DIR/secure-origin.yaml" \
  StackName="$STACK_NAME" \
  BridgeImageUri="$BRIDGE_IMAGE_URI" \
  InstanceType="$INSTANCE_TYPE" \
  BridgeTokenSecret="$BRIDGE_TOKEN_SECRET_VALUE" \
  Cookie="$COOKIE_VALUE"

BRIDGE_EC2_URL="$(stack_output "$origin_stack" Ec2HttpUrl)"
BRIDGE_INSTANCE_ID="$(stack_output "$origin_stack" InstanceId)"
origin_domain="$(stack_output "$origin_stack" Ec2PublicDnsName)"

deploy_stack "$edge_stack" "$SCRIPT_DIR/secure-edge.yaml" \
  StackName="$STACK_NAME" \
  OriginDomainName="$origin_domain"

BRIDGE_HTTP_URL="$(stack_output "$edge_stack" BridgeHttpUrl)"
BRIDGE_WEBSOCKET_URL="$(stack_output "$edge_stack" BridgeWebSocketUrl)"
BRIDGE_CLOUDFRONT_DOMAIN="$(stack_output "$edge_stack" CloudFrontDomain)"
BRIDGE_DISTRIBUTION_ID="$(stack_output "$edge_stack" CloudFrontDistributionId)"
save_state

wait_http_health "$BRIDGE_EC2_URL"
wait_http_health "$BRIDGE_HTTP_URL"
print_bridge_output