#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
STATIC_SITES_DIR="$SCRIPT_DIR"
# shellcheck source=deploy/aws-static-sites/lib/staging-common.sh
source "$SCRIPT_DIR/lib/staging-common.sh"

STAGING_DIST_DIR="$REPO_ROOT/landing_page/dist/staging"

parse_staging_args "$@"
require_staging_deploy_enabled

if [ ! -d "$STAGING_DIST_DIR" ]; then
  echo "Missing staging build output: $STAGING_DIST_DIR" >&2
  echo "Run: yarn --cwd landing_page build:staging" >&2
  exit 1
fi

bucket="$(staging_stack_output StagingBucket)"
distribution="$(staging_stack_output StagingCloudFrontDistributionId)"

staging_aws s3 sync "$STAGING_DIST_DIR/" "s3://${bucket}/" --delete
staging_aws cloudfront create-invalidation \
  --distribution-id "$distribution" \
  --paths "/*" >/dev/null

print_staging_outputs