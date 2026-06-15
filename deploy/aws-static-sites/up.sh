#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATIC_SITES_DIR="$SCRIPT_DIR"
# shellcheck source=deploy/aws-static-sites/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

parse_common_args "$@"
require_aws_deploy_enabled
find_hosted_zone_id

aws_out cloudformation validate-template --template-body "file://$TEMPLATE_FILE" >/dev/null

aws_out cloudformation deploy \
  --stack-name "$STACK_NAME" \
  --template-file "$TEMPLATE_FILE" \
  --parameter-overrides \
    HostedZoneId="$HOSTED_ZONE_ID" \
    LandingDomainName="$LANDING_DOMAIN" \
    DocsDomainName="$DOCS_DOMAIN" \
    BucketNamePrefix="$BUCKET_NAME_PREFIX" \
  --tags \
    Project=crystal-lattice \
    Component=static-sites \
    Purpose=test \
    StackName="$STACK_NAME"

print_stack_outputs