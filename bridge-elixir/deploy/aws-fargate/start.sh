#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=deploy/aws-fargate/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

parse_common_args "$@"
require_aws_tests_enabled
load_state
ensure_secrets
ensure_platform_defaults
ensure_image_uri

case "$PROFILE" in
  public-task)
    args=(
      --profile public-task
      --stack-name "$STACK_NAME"
      --region "$REGION"
      --image-uri "$IMAGE_URI"
      --cpu-architecture "$CPU_ARCHITECTURE"
      --docker-platform "$DOCKER_PLATFORM"
    )
    [ "$JSON_OUTPUT" -eq 1 ] && args+=(--json)
    "$SCRIPT_DIR/up.sh" "${args[@]}"
    ;;

  secure)
    autoscaling_value="false"
    [ "$ENABLE_AUTOSCALING" -eq 1 ] && autoscaling_value="true"

    deploy_stack "${STACK_NAME}-origin" "$SCRIPT_DIR/secure-origin.yaml" \
      StackName="$STACK_NAME" \
      ImageUri="$IMAGE_URI" \
      BridgeTokenSecret="$BRIDGE_TOKEN_SECRET_VALUE" \
      Cookie="$COOKIE_VALUE" \
      CpuArchitecture="$CPU_ARCHITECTURE" \
      DesiredCount=1 \
      EnableAutoscaling="$autoscaling_value" \
      MinTasks="$MIN_TASKS" \
      MaxTasks="$MAX_TASKS"

    origin_domain="$(stack_output "${STACK_NAME}-origin" LoadBalancerDNSName)"

    deploy_stack "${STACK_NAME}-edge" "$SCRIPT_DIR/secure-edge.yaml" \
      StackName="$STACK_NAME" \
      OriginDomainName="$origin_domain" \
      DomainName="$DOMAIN_NAME" \
      HostedZoneId="$HOSTED_ZONE_ID"

    save_state

    bridge_http_url="$(stack_output "${STACK_NAME}-edge" BridgeHttpUrl)"
    bridge_websocket_url="$(stack_output "${STACK_NAME}-edge" BridgeWebSocketUrl)"
    cloudfront_domain="$(stack_output "${STACK_NAME}-edge" CloudFrontDomain)"

    wait_http_health "$bridge_http_url"
    print_bridge_output "$bridge_http_url" "$bridge_websocket_url" "$cloudfront_domain"
    ;;

  *)
    echo "Unsupported profile: $PROFILE" >&2
    exit 2
    ;;
esac