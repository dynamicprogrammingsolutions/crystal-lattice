#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_FILE="$SCRIPT_DIR/github-oidc-role.yaml"

PROFILE="test"
REGION="${AWS_REGION:-us-east-1}"
STATIC_STACK_NAME=""
ROLE_STACK_NAME=""
ROLE_NAME=""
GITHUB_OWNER="dynamicprogrammingsolutions"
GITHUB_REPO="crystal-lattice"
GITHUB_BRANCH="main"

usage() {
  cat <<'USAGE'
Create or update the GitHub Actions AWS OIDC deploy role for static sites.

This script reads static hosting stack outputs automatically. Run the static
site stack first with deploy/aws-static-sites/up.sh.

Usage:
  ALLOW_AWS_DEPLOY=1 deploy/aws-static-sites/create-github-oidc-role.sh [options]

Options:
  --profile test|prod          Defaults stack names and public profile labels.
  --static-stack-name NAME     CloudFormation stack with static hosting outputs.
  --role-stack-name NAME       CloudFormation stack for the GitHub OIDC role.
  --role-name NAME             IAM role name to create/update.
  --region REGION              AWS region. Default: us-east-1.
  --github-owner OWNER         GitHub owner/org. Default: dynamicprogrammingsolutions.
  --github-repo REPO           GitHub repo name. Default: crystal-lattice.
  --github-branch BRANCH       Trusted branch. Default: main.
  --help, -h                   Show this help.

Defaults by profile:
  test static stack:           crystal-lattice-static-sites-test
  test role stack:             crystal-lattice-static-sites-github-oidc-test
  test role name:              CrystalLatticeStaticSitesGitHubDeployRoleTest

  prod static stack:           crystal-lattice-static-sites-prod
  prod role stack:             crystal-lattice-static-sites-github-oidc-prod
  prod role name:              CrystalLatticeStaticSitesGitHubDeployRoleProd
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --profile) PROFILE="$2"; shift 2 ;;
    --static-stack-name) STATIC_STACK_NAME="$2"; shift 2 ;;
    --role-stack-name) ROLE_STACK_NAME="$2"; shift 2 ;;
    --role-name) ROLE_NAME="$2"; shift 2 ;;
    --region) REGION="$2"; shift 2 ;;
    --github-owner) GITHUB_OWNER="$2"; shift 2 ;;
    --github-repo) GITHUB_REPO="$2"; shift 2 ;;
    --github-branch) GITHUB_BRANCH="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

case "$PROFILE" in
  test|prod) ;;
  *) echo "Unsupported profile: $PROFILE" >&2; exit 2 ;;
esac

if [ "${ALLOW_AWS_DEPLOY:-}" != "1" ]; then
  echo "Set ALLOW_AWS_DEPLOY=1 to create or update AWS IAM resources." >&2
  exit 2
fi

if [ "$PROFILE" = "prod" ]; then
  STATIC_STACK_NAME="${STATIC_STACK_NAME:-crystal-lattice-static-sites-prod}"
  ROLE_STACK_NAME="${ROLE_STACK_NAME:-crystal-lattice-static-sites-github-oidc-prod}"
  ROLE_NAME="${ROLE_NAME:-CrystalLatticeStaticSitesGitHubDeployRoleProd}"
else
  STATIC_STACK_NAME="${STATIC_STACK_NAME:-crystal-lattice-static-sites-test}"
  ROLE_STACK_NAME="${ROLE_STACK_NAME:-crystal-lattice-static-sites-github-oidc-test}"
  ROLE_NAME="${ROLE_NAME:-CrystalLatticeStaticSitesGitHubDeployRoleTest}"
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

if [ -z "$landing_bucket" ] || [ -z "$docs_bucket" ] ||
  [ -z "$landing_distribution_id" ] || [ -z "$docs_distribution_id" ]; then
  echo "Could not read required outputs from static stack: $STATIC_STACK_NAME" >&2
  exit 1
fi

oidc_provider_arn="$(
  aws --region "$REGION" iam list-open-id-connect-providers \
    --query "OpenIDConnectProviderList[?contains(Arn, 'token.actions.githubusercontent.com')].Arn | [0]" \
    --output text
)"

if [ -z "$oidc_provider_arn" ] || [ "$oidc_provider_arn" = "None" ]; then
  create_oidc_provider="true"
  account_id="$(aws --region "$REGION" sts get-caller-identity --query Account --output text)"
  oidc_provider_arn="arn:aws:iam::${account_id}:oidc-provider/token.actions.githubusercontent.com"
else
  create_oidc_provider="false"
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
    GitHubBranch="$GITHUB_BRANCH" \
    RoleName="$ROLE_NAME" \
    CreateOidcProvider="$create_oidc_provider" \
    ExistingOidcProviderArn="$oidc_provider_arn" \
    LandingBucket="$landing_bucket" \
    DocsBucket="$docs_bucket" \
    LandingDistributionId="$landing_distribution_id" \
    DocsDistributionId="$docs_distribution_id" \
  --tags \
    Project=crystal-lattice \
    Component=static-sites-github-actions \
    Profile="$PROFILE"

role_arn="$(
  aws --region "$REGION" cloudformation describe-stacks \
    --stack-name "$ROLE_STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='AwsRoleToAssume'].OutputValue | [0]" \
    --output text
)"

echo "AWS_ROLE_TO_ASSUME=$role_arn"
echo "ROLE_STACK_NAME=$ROLE_STACK_NAME"
echo "ROLE_NAME=$ROLE_NAME"
echo "OIDC_PROVIDER_ARN=$oidc_provider_arn"
echo "GITHUB_REPOSITORY=${GITHUB_OWNER}/${GITHUB_REPO}"
echo "GITHUB_BRANCH=$GITHUB_BRANCH"