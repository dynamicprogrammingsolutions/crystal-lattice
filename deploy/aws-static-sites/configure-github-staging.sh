#!/usr/bin/env bash

set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
REPO="dynamicprogrammingsolutions/crystal-lattice"
ENVIRONMENT="staging-sites"
STATIC_STACK_NAME="crystal-lattice-static-site-staging"
ROLE_STACK_NAME="crystal-lattice-static-site-github-oidc-staging"
DRY_RUN=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --region) REGION="$2"; shift 2 ;;
    --repo) REPO="$2"; shift 2 ;;
    --environment) ENVIRONMENT="$2"; shift 2 ;;
    --static-stack-name) STATIC_STACK_NAME="$2"; shift 2 ;;
    --role-stack-name) ROLE_STACK_NAME="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --help|-h)
      echo "Configure the staging-sites GitHub environment, variables, and OIDC role secret."
      exit 0
      ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

read_output() {
  local stack="$1"
  local key="$2"
  aws --region "$REGION" cloudformation describe-stacks \
    --stack-name "$stack" \
    --query "Stacks[0].Outputs[?OutputKey=='$key'].OutputValue | [0]" \
    --output text
}

bucket="$(read_output "$STATIC_STACK_NAME" StagingBucket)"
distribution="$(read_output "$STATIC_STACK_NAME" StagingCloudFrontDistributionId)"
site_url="$(read_output "$STATIC_STACK_NAME" StagingUrl)"
role_arn="$(read_output "$ROLE_STACK_NAME" AwsRoleToAssume)"

run() {
  if [ "$DRY_RUN" -eq 1 ]; then
    printf 'DRY RUN:'
    printf ' %q' "$@"
    printf '\n'
  else
    "$@"
  fi
}

run gh api --method PUT "repos/${REPO}/environments/${ENVIRONMENT}" \
  -F "deployment_branch_policy[protected_branches]=false" \
  -F "deployment_branch_policy[custom_branch_policies]=true" >/dev/null

if [ "$DRY_RUN" -eq 0 ]; then
  policy_id="$(
    gh api "repos/${REPO}/environments/${ENVIRONMENT}/deployment-branch-policies" \
      --jq '.branch_policies[] | select(.name == "main" and .type == "branch") | .id' |
      head -n 1
  )"
  if [ -z "$policy_id" ]; then
    gh api --method POST \
      "repos/${REPO}/environments/${ENVIRONMENT}/deployment-branch-policies" \
      -f name=main \
      -f type=branch >/dev/null
  fi
else
  echo "DRY RUN: ensure ${ENVIRONMENT} permits only branch main"
fi

run gh variable set AWS_REGION --repo "$REPO" --env "$ENVIRONMENT" --body "$REGION"
run gh variable set STAGING_BUCKET --repo "$REPO" --env "$ENVIRONMENT" --body "$bucket"
run gh variable set STAGING_CLOUDFRONT_DISTRIBUTION_ID \
  --repo "$REPO" --env "$ENVIRONMENT" --body "$distribution"
run gh variable set PUBLIC_CRYSTAL_LATTICE_SITE_URL \
  --repo "$REPO" --env "$ENVIRONMENT" --body "$site_url"
run gh variable set PUBLIC_CRYSTAL_LATTICE_DOCS_URL \
  --repo "$REPO" --env "$ENVIRONMENT" --body "https://docs.crystallattice.dev"
run gh secret set AWS_ROLE_TO_ASSUME \
  --repo "$REPO" --env "$ENVIRONMENT" --body "$role_arn"

echo "Configured GitHub environment ${ENVIRONMENT} for ${REPO}."