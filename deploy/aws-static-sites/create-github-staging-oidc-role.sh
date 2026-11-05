#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_FILE="$SCRIPT_DIR/staging-github-oidc-role.yaml"
REGION="${AWS_REGION:-us-east-1}"
STATIC_STACK_NAME="crystal-lattice-static-site-staging"
ROLE_STACK_NAME="crystal-lattice-static-site-github-oidc-staging"
ROLE_NAME="CrystalLatticeStagingSiteGitHubDeployRole"
GITHUB_OWNER="dynamicprogrammingsolutions"
GITHUB_REPO="crystal-lattice"
GITHUB_ENVIRONMENT="staging-sites"

if [ "${ALLOW_AWS_DEPLOY:-}" != "1" ]; then
  echo "Set ALLOW_AWS_DEPLOY=1 to create or update the staging IAM role." >&2
  exit 2
fi

while [ "$#" -gt 0 ]; do
  case "$1" in
    --region) REGION="$2"; shift 2 ;;
    --static-stack-name) STATIC_STACK_NAME="$2"; shift 2 ;;
    --role-stack-name) ROLE_STACK_NAME="$2"; shift 2 ;;
    --role-name) ROLE_NAME="$2"; shift 2 ;;
    --github-owner) GITHUB_OWNER="$2"; shift 2 ;;
    --github-repo) GITHUB_REPO="$2"; shift 2 ;;
    --github-environment) GITHUB_ENVIRONMENT="$2"; shift 2 ;;
    --help|-h)
      echo "Create the staging-only GitHub OIDC deployment role."
      exit 0
      ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

read_output() {
  local key="$1"
  aws --region "$REGION" cloudformation describe-stacks \
    --stack-name "$STATIC_STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='$key'].OutputValue | [0]" \
    --output text
}

bucket="$(read_output StagingBucket)"
distribution="$(read_output StagingCloudFrontDistributionId)"
oidc_provider_arn="$(
  aws --region "$REGION" iam list-open-id-connect-providers \
    --query "OpenIDConnectProviderList[?contains(Arn, 'token.actions.githubusercontent.com')].Arn | [0]" \
    --output text
)"

if [ -z "$oidc_provider_arn" ] || [ "$oidc_provider_arn" = "None" ]; then
  echo "The shared GitHub Actions OIDC provider does not exist." >&2
  exit 1
fi

aws --region "$REGION" cloudformation validate-template \
  --template-body "file://$TEMPLATE_FILE" >/dev/null

aws --region "$REGION" cloudformation deploy \
  --stack-name "$ROLE_STACK_NAME" \
  --template-file "$TEMPLATE_FILE" \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    GitHubOwner="$GITHUB_OWNER" \
    GitHubRepo="$GITHUB_REPO" \
    GitHubEnvironment="$GITHUB_ENVIRONMENT" \
    RoleName="$ROLE_NAME" \
    ExistingOidcProviderArn="$oidc_provider_arn" \
    StagingBucket="$bucket" \
    StagingDistributionId="$distribution" \
  --tags \
    Project=crystal-lattice \
    Component=staging-site-github-actions

role_arn="$(
  aws --region "$REGION" cloudformation describe-stacks \
    --stack-name "$ROLE_STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='AwsRoleToAssume'].OutputValue | [0]" \
    --output text
)"

echo "AWS_ROLE_TO_ASSUME=$role_arn"
echo "ROLE_STACK_NAME=$ROLE_STACK_NAME"
echo "GITHUB_ENVIRONMENT=$GITHUB_ENVIRONMENT"