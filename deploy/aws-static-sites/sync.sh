#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
STATIC_SITES_DIR="$SCRIPT_DIR"
# shellcheck source=deploy/aws-static-sites/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

LANDING_DIST_DIR="$REPO_ROOT/landing_page/dist/production"
DOCS_SITE_DIR="$REPO_ROOT/docs_site/dist"

usage() {
  cat <<'USAGE'
Sync built static site artifacts to the AWS static hosting buckets.

Usage:
  ALLOW_AWS_DEPLOY=1 deploy/aws-static-sites/sync.sh [common options]

Build outputs must already exist:
  landing_page/dist/production
  docs_site/dist
USAGE
  usage_common
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --help|-h) usage; exit 0 ;;
    *) break ;;
  esac
done

parse_common_args "$@"
require_aws_deploy_enabled

if ! stack_exists; then
  echo "CloudFormation stack does not exist: $STACK_NAME" >&2
  exit 1
fi
if [ ! -d "$LANDING_DIST_DIR" ]; then
  echo "Missing landing build output: $LANDING_DIST_DIR" >&2
  echo "Run: cd landing_page && yarn build" >&2
  exit 1
fi
if [ ! -d "$DOCS_SITE_DIR" ]; then
  echo "Missing docs build output: $DOCS_SITE_DIR" >&2
  echo "Run: python docs_site/scripts/build_mkdocs_site.py" >&2
  exit 1
fi

landing_bucket="$(stack_output LandingBucket)"
docs_bucket="$(stack_output DocsBucket)"
landing_distribution="$(stack_output LandingCloudFrontDistributionId)"
docs_distribution="$(stack_output DocsCloudFrontDistributionId)"

aws_out s3 sync "$LANDING_DIST_DIR/" "s3://${landing_bucket}/" --delete
aws_out s3 sync "$DOCS_SITE_DIR/" "s3://${docs_bucket}/" --delete

find "$DOCS_SITE_DIR" -name '*.md' -print0 | while IFS= read -r -d '' file; do
  key="${file#"$DOCS_SITE_DIR"/}"
  aws_out s3 cp "$file" "s3://${docs_bucket}/${key}" \
    --content-type "text/plain; charset=utf-8" \
    --metadata-directive REPLACE >/dev/null
done

for file in "$DOCS_SITE_DIR/llms.txt" "$DOCS_SITE_DIR/llms-full.txt"; do
  [ -f "$file" ] || continue
  key="${file#"$DOCS_SITE_DIR"/}"
  aws_out s3 cp "$file" "s3://${docs_bucket}/${key}" \
    --content-type "text/plain; charset=utf-8" \
    --metadata-directive REPLACE >/dev/null
done

aws_out cloudfront create-invalidation \
  --distribution-id "$landing_distribution" \
  --paths "/*" >/dev/null
aws_out cloudfront create-invalidation \
  --distribution-id "$docs_distribution" \
  --paths "/*" >/dev/null

print_stack_outputs