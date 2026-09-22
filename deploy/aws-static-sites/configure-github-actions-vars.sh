#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PROFILE="test"
REGION="${AWS_REGION:-us-east-1}"
REPO="dynamicprogrammingsolutions/crystal-lattice"
STATIC_STACK_NAME=""
ROLE_STACK_NAME=""
ROLE_ARN=""
SITE_URL=""
DOCS_URL=""
UMAMI_SCRIPT_URL=""
UMAMI_LANDING_ID=""
UMAMI_DOCS_ID=""
DRY_RUN=0

usage() {
  cat <<'USAGE'
Configure GitHub Actions variables/secrets for static site deployment.

This script reads AWS stack outputs automatically, then uses gh to set GitHub
repository variables and the AWS_ROLE_TO_ASSUME secret.

Usage:
  deploy/aws-static-sites/configure-github-actions-vars.sh [options]

Options:
  --profile test|prod          Defaults stack names and public URLs.
  --repo OWNER/REPO            GitHub repository. Default: dynamicprogrammingsolutions/crystal-lattice.
  --static-stack-name NAME     CloudFormation stack with static hosting outputs.
  --role-stack-name NAME       CloudFormation stack with AwsRoleToAssume output.
  --role-arn ARN               Use this role ARN instead of reading role stack output.
  --region REGION              AWS region. Default: us-east-1.
  --site-url URL               PUBLIC_CRYSTAL_LATTICE_SITE_URL value.
  --docs-url URL               PUBLIC_CRYSTAL_LATTICE_DOCS_URL value.
  --umami-script-url URL       Public self-hosted Umami tracker URL.
  --umami-landing-id UUID      Umami website ID for crystallattice.dev.
  --umami-docs-id UUID         Umami website ID for docs.crystallattice.dev.
  --dry-run                    Print gh commands without mutating GitHub.
  --help, -h                   Show this help.

Defaults by profile:
  test static stack:           crystal-lattice-static-sites-test
  test role stack:             crystal-lattice-static-sites-github-oidc-test
  test site URL:               https://crystallattice.dev.dynamicprogrammingsolutions.com
  test docs URL:               https://docs.crystallattice.dev.dynamicprogrammingsolutions.com

  prod static stack:           crystal-lattice-static-sites-prod
  prod role stack:             crystal-lattice-static-sites-github-oidc-prod
  prod site URL:               https://crystallattice.dev
  prod docs URL:               https://docs.crystallattice.dev
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --profile) PROFILE="$2"; shift 2 ;;
    --repo) REPO="$2"; shift 2 ;;
    --static-stack-name) STATIC_STACK_NAME="$2"; shift 2 ;;
    --role-stack-name) ROLE_STACK_NAME="$2"; shift 2 ;;
    --role-arn) ROLE_ARN="$2"; shift 2 ;;
    --region) REGION="$2"; shift 2 ;;
    --site-url) SITE_URL="$2"; shift 2 ;;
    --docs-url) DOCS_URL="$2"; shift 2 ;;
    --umami-script-url) UMAMI_SCRIPT_URL="$2"; shift 2 ;;
    --umami-landing-id) UMAMI_LANDING_ID="$2"; shift 2 ;;
    --umami-docs-id) UMAMI_DOCS_ID="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

case "$PROFILE" in
  test|prod) ;;
  *) echo "Unsupported profile: $PROFILE" >&2; exit 2 ;;
esac

UUID_PATTERN='^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$'
if [ -n "$UMAMI_SCRIPT_URL" ] || [ -n "$UMAMI_LANDING_ID" ] || [ -n "$UMAMI_DOCS_ID" ]; then
  if [ "$UMAMI_SCRIPT_URL" != "https://stats.dynamicprogrammingsolutions.com/insight.js" ]; then
    echo "The Umami script URL must use the approved self-hosted tracker." >&2
    exit 2
  fi
  if ! [[ "$UMAMI_LANDING_ID" =~ $UUID_PATTERN ]] || ! [[ "$UMAMI_DOCS_ID" =~ $UUID_PATTERN ]]; then
    echo "Both Umami website IDs must be valid UUIDs." >&2
    exit 2
  fi
  if [ "$UMAMI_LANDING_ID" = "$UMAMI_DOCS_ID" ]; then
    echo "Landing and docs must use distinct Umami website IDs." >&2
    exit 2
  fi
fi

if [ "$PROFILE" = "prod" ]; then
  STATIC_STACK_NAME="${STATIC_STACK_NAME:-crystal-lattice-static-sites-prod}"
  ROLE_STACK_NAME="${ROLE_STACK_NAME:-crystal-lattice-static-sites-github-oidc-prod}"
  SITE_URL="${SITE_URL:-https://crystallattice.dev}"
  DOCS_URL="${DOCS_URL:-https://docs.crystallattice.dev}"
else
  STATIC_STACK_NAME="${STATIC_STACK_NAME:-crystal-lattice-static-sites-test}"
  ROLE_STACK_NAME="${ROLE_STACK_NAME:-crystal-lattice-static-sites-github-oidc-test}"
  SITE_URL="${SITE_URL:-https://crystallattice.dev.dynamicprogrammingsolutions.com}"
  DOCS_URL="${DOCS_URL:-https://docs.crystallattice.dev.dynamicprogrammingsolutions.com}"
fi

read_static_output() {
  local key="$1"
  "$SCRIPT_DIR/outputs.sh" \
    --stack-name "$STATIC_STACK_NAME" \
    --region "$REGION" |
    awk -F= -v key="$key" '$1 == key {print substr($0, length(key) + 2)}'
}

landing_bucket="$(read_static_output LANDING_BUCKET)"
docs_bucket="$(read_static_output DOCS_BUCKET)"
landing_distribution_id="$(read_static_output LANDING_CLOUDFRONT_DISTRIBUTION_ID)"
docs_distribution_id="$(read_static_output DOCS_CLOUDFRONT_DISTRIBUTION_ID)"
aws_region="$(read_static_output AWS_REGION)"

if [ -z "$landing_bucket" ] || [ -z "$docs_bucket" ] ||
  [ -z "$landing_distribution_id" ] || [ -z "$docs_distribution_id" ] ||
  [ -z "$aws_region" ]; then
  echo "Could not read required outputs from static stack: $STATIC_STACK_NAME" >&2
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
  echo "Could not determine AWS_ROLE_TO_ASSUME. Run create-github-oidc-role.sh first or pass --role-arn." >&2
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
set_variable LANDING_BUCKET "$landing_bucket"
set_variable DOCS_BUCKET "$docs_bucket"
set_variable LANDING_CLOUDFRONT_DISTRIBUTION_ID "$landing_distribution_id"
set_variable DOCS_CLOUDFRONT_DISTRIBUTION_ID "$docs_distribution_id"
set_variable PUBLIC_CRYSTAL_LATTICE_SITE_URL "$SITE_URL"
set_variable PUBLIC_CRYSTAL_LATTICE_DOCS_URL "$DOCS_URL"
if [ -n "$UMAMI_SCRIPT_URL" ] || [ -n "$UMAMI_LANDING_ID" ] || [ -n "$UMAMI_DOCS_ID" ]; then
  if [ -z "$UMAMI_SCRIPT_URL" ] || [ -z "$UMAMI_LANDING_ID" ] || [ -z "$UMAMI_DOCS_ID" ]; then
    echo "All three Umami options must be provided together." >&2
    exit 2
  fi
  set_variable PUBLIC_CRYSTAL_LATTICE_UMAMI_SCRIPT_URL "$UMAMI_SCRIPT_URL"
  set_variable PUBLIC_CRYSTAL_LATTICE_UMAMI_LANDING_ID "$UMAMI_LANDING_ID"
  set_variable PUBLIC_CRYSTAL_LATTICE_UMAMI_DOCS_ID "$UMAMI_DOCS_ID"
fi
run_gh secret set AWS_ROLE_TO_ASSUME --repo "$REPO" --body "$ROLE_ARN"

echo "Configured GitHub Actions deployment settings for $REPO ($PROFILE)."
echo "Static stack: $STATIC_STACK_NAME"
echo "Role stack: $ROLE_STACK_NAME"
echo "Site URL: $SITE_URL"
echo "Docs URL: $DOCS_URL"