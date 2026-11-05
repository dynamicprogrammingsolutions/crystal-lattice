#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATIC_SITES_DIR="$SCRIPT_DIR"
# shellcheck source=deploy/aws-static-sites/lib/staging-common.sh
source "$SCRIPT_DIR/lib/staging-common.sh"

parse_staging_args "$@"
require_staging_deploy_enabled
find_staging_hosted_zone_id

staging_aws cloudformation validate-template \
  --template-body "file://$STAGING_TEMPLATE_FILE" >/dev/null

staging_aws cloudformation deploy \
  --stack-name "$STACK_NAME" \
  --template-file "$STAGING_TEMPLATE_FILE" \
  --parameter-overrides \
    HostedZoneId="$HOSTED_ZONE_ID" \
    DomainName="$DOMAIN_NAME" \
    BucketNamePrefix="$BUCKET_NAME_PREFIX" \
  --tags \
    Project=crystal-lattice \
    Component=staging-site \
    StackName="$STACK_NAME"

print_staging_outputs