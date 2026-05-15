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
    deploy_stack "${STACK_NAME}-public-task" "$SCRIPT_DIR/public-task.yaml" \
      StackName="$STACK_NAME" \
      ImageUri="$IMAGE_URI" \
      BridgeTokenSecret="$BRIDGE_TOKEN_SECRET_VALUE" \
      Cookie="$COOKIE_VALUE" \
      CpuArchitecture="$CPU_ARCHITECTURE"

    cluster="$(stack_output "${STACK_NAME}-public-task" ClusterName)"
    task_definition="$(stack_output "${STACK_NAME}-public-task" TaskDefinitionArn)"
    subnets="$(stack_output "${STACK_NAME}-public-task" PublicSubnetIds)"
    security_group="$(stack_output "${STACK_NAME}-public-task" SecurityGroupId)"

    task_arn="$(aws_out ecs run-task \
      --cluster "$cluster" \
      --launch-type FARGATE \
      --started-by "$STACK_NAME" \
      --task-definition "$task_definition" \
      --network-configuration "awsvpcConfiguration={subnets=[$subnets],securityGroups=[$security_group],assignPublicIp=ENABLED}" \
      --query 'tasks[0].taskArn' \
      --output text)"

    aws_out ecs wait tasks-running --cluster "$cluster" --tasks "$task_arn"

    eni_id="$(aws_out ecs describe-tasks \
      --cluster "$cluster" \
      --tasks "$task_arn" \
      --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value | [0]" \
      --output text)"
    public_ip="$(aws_out ec2 describe-network-interfaces \
      --network-interface-ids "$eni_id" \
      --query 'NetworkInterfaces[0].Association.PublicIp' \
      --output text)"

    save_state
    wait_http_health "http://${public_ip}:4000/health"
    print_bridge_output "http://${public_ip}:4000/health" "ws://${public_ip}:4000/ws/websocket" ""
    ;;

  secure)
    args=(
      --profile secure
      --stack-name "$STACK_NAME"
      --region "$REGION"
      --image-uri "$IMAGE_URI"
      --cpu-architecture "$CPU_ARCHITECTURE"
      --docker-platform "$DOCKER_PLATFORM"
      --min-tasks "$MIN_TASKS"
      --max-tasks "$MAX_TASKS"
    )
    [ -n "$DOMAIN_NAME" ] && args+=(--domain "$DOMAIN_NAME")
    [ -n "$HOSTED_ZONE_ID" ] && args+=(--hosted-zone-id "$HOSTED_ZONE_ID")
    [ "$ENABLE_AUTOSCALING" -eq 1 ] && args+=(--autoscaling)
    [ "$JSON_OUTPUT" -eq 1 ] && args+=(--json)
    "$SCRIPT_DIR/start.sh" "${args[@]}"
    ;;

  *)
    echo "Unsupported profile: $PROFILE" >&2
    exit 2
    ;;
esac