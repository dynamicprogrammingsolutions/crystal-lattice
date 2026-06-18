#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=deploy/aws-cli-downloads/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

REPO="dynamicprogrammingsolutions/crystal-lattice"
ROLE_STACK_NAME=""
ROLE_ARN=""
DRY_RUN=0

usage() {
  cat <<'USAGE'
Configure GitHub Actions variables/secrets for CLI release downloads.

Usage:
  deploy/aws-cli-downloads/configure-github-actions-vars.sh [common options] [options]

Options:
  --repo OWNER/REPO            GitHub repository. Default: dynamicprogrammingsolutions/crystal-lattice.
  --role-stack-name NAME       CloudFormation stack with AwsRoleToAssume output.
  --role-arn ARN               Use this role ARN instead of reading role stack output.
  --dry-run                    Print gh commands without mutating GitHub.
  --help, -h                   Show this help.
USAGE
  usage_common
}

args=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo) REPO="$2"; shift 2 ;;
    --role-stack-name) ROLE_STACK_NAME="$2"; shift 2 ;;
    --role-arn) ROLE_ARN="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --help|-h) usage; exit 0 ;;
    *) args+=("$1"); shift ;;
  esac
done

if [ "${#args[@]}" -gt 0 ]; then
  parse_common_args "${args[@]}"
else
  parse_common_args
fi
ROLE_STACK_NAME="${ROLE_STACK_NAME:-crystal-lattice-cli-downloads-github-oidc-${PROFILE}}"

read_output() {
  local key="$1"
  "$SCRIPT_DIR/outputs.sh" \
    --profile "$PROFILE" \
    --stack-name "$STACK_NAME" \
    --region "$REGION" |
    awk -F= -v key="$key" '$1 == key {print substr($0, length(key) + 2)}'
}

downloads_bucket="$(read_output DOWNLOADS_BUCKET)"
downloads_prefix="$(read_output DOWNLOADS_PREFIX)"
downloads_base_url="$(read_output DOWNLOADS_BASE_URL)"
downloads_distribution_id="$(read_output DOWNLOADS_CLOUDFRONT_DISTRIBUTION_ID)"
aws_region="$(read_output AWS_REGION)"

if [ -z "$downloads_bucket" ] || [ -z "$downloads_prefix" ] ||
  [ -z "$downloads_base_url" ] || [ -z "$downloads_distribution_id" ] ||
  [ -z "$aws_region" ]; then
  echo "Could not read required outputs from download stack: $STACK_NAME" >&2
  exit 1
fi

if [ -z "$ROLE_ARN" ]; then
  ROLE_ARN="$(
    aws --region "$REGION" cloudformation describe-stacks \
      --stack-name "$ROLE_STACK_NAME" \
      --query "Stacks[0].Outputs[?OutputKey=='AwsRoleToAssume'].OutputValue | [0]" \
      --output text
  )"
fi

if [ -z "$ROLE_ARN" ] || [ "$ROLE_ARN" = "None" ]; then
  echo "Could not determine CLI_DOWNLOADS_AWS_ROLE_TO_ASSUME. Run create-github-oidc-role.sh first or pass --role-arn." >&2
  exit 1
fi

run_gh() {
  if [ "$DRY_RUN" -eq 1 ]; then
    printf 'DRY RUN:'
    printf ' %q' gh "$@"
    printf '\n'
  else
    gh "$@"
  fi
}

set_variable() {
  local name="$1"
  local value="$2"
  run_gh variable set "$name" --repo "$REPO" --body "$value"
}

set_variable AWS_REGION "$aws_region"
set_variable CLI_DOWNLOADS_BUCKET "$downloads_bucket"
set_variable CLI_DOWNLOADS_PREFIX "$downloads_prefix"
set_variable CLI_DOWNLOADS_BASE_URL "$downloads_base_url"
set_variable CLI_DOWNLOADS_CLOUDFRONT_DISTRIBUTION_ID "$downloads_distribution_id"
run_gh secret set CLI_DOWNLOADS_AWS_ROLE_TO_ASSUME --repo "$REPO" --body "$ROLE_ARN"

echo "Configured CLI download GitHub Actions settings for $REPO ($PROFILE)."
echo "Download stack: $STACK_NAME"
echo "Role stack: $ROLE_STACK_NAME"
echo "Base URL: $downloads_base_url"