#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATIC_SITES_DIR="$SCRIPT_DIR"
# shellcheck source=deploy/aws-static-sites/lib/staging-common.sh
source "$SCRIPT_DIR/lib/staging-common.sh"

parse_staging_args "$@"
print_staging_outputs