#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=deploy/aws-cli-downloads/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

ROLE_TEMPLATE="$SCRIPT_DIR/github-oidc-role.yaml"
ROLE_STACK_NAME=""
ROLE_NAME=""
GITHUB_OWNER="dynamicprogrammingsolutions"
GITHUB_REPO="crystal-lattice"
GITHUB_BRANCH="main"
GITHUB_ENVIRONMENT="cli-release"

usage() {
  cat <<'USAGE'
Create or update the GitHub Actions AWS OIDC role for CLI download publishing.

Usage:
  ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/create-github-oidc-role.sh [common options] [options]

Options:
  --role-stack-name NAME       CloudFormation stack for the GitHub OIDC role.
  --role-name NAME             IAM role name to create/update.
  --github-owner OWNER         GitHub owner/org. Default: dynamicprogrammingsolutions.
  --github-repo REPO           GitHub repo name. Default: crystal-lattice.
  --github-branch BRANCH       Branch trusted for workflow testing. Release tags are always trusted.
  --github-environment NAME    Environment trusted for release publishing. Default: cli-release.
  --help, -h                   Show this help.
USAGE
  usage_common
}

args=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --role-stack-name) ROLE_STACK_NAME="$2"; shift 2 ;;
    --role-name) ROLE_NAME="$2"; shift 2 ;;
    --github-owner) GITHUB_OWNER="$2"; shift 2 ;;
    --github-repo) GITHUB_REPO="$2"; shift 2 ;;
    --github-branch) GITHUB_BRANCH="$2"; shift 2 ;;
    --github-environment) GITHUB_ENVIRONMENT="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) args+=("$1"); shift ;;
  esac
done

if [ "${#args[@]}" -gt 0 ]; then
  parse_common_args "${args[@]}"
else
  parse_common_args
fi
require_aws_deploy_enabled

ROLE_STACK_NAME="${ROLE_STACK_NAME:-crystal-lattice-cli-downloads-github-oidc-${PROFILE}}"
if [ "$PROFILE" = "prod" ]; then
  ROLE_NAME="${ROLE_NAME:-CrystalLatticeCliDownloadsGitHubDeployRoleProd}"
else
  ROLE_NAME="${ROLE_NAME:-CrystalLatticeCliDownloadsGitHubDeployRoleTest}"
fi

if ! stack_exists; then
  echo "Download stack does not exist: $STACK_NAME" >&2
  exit 1
fi

downloads_bucket="$(stack_output DownloadsBucket)"
downloads_prefix="$(stack_output DownloadsPrefix)"
downloads_distribution_id="$(stack_output DownloadsCloudFrontDistributionId)"

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
  --template-body "file://$ROLE_TEMPLATE" >/dev/null

aws --region "$REGION" cloudformation deploy \
  --stack-name "$ROLE_STACK_NAME" \
  --template-file "$ROLE_TEMPLATE" \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    GitHubOwner="$GITHUB_OWNER" \
    GitHubRepo="$GITHUB_REPO" \
    GitHubBranch="$GITHUB_BRANCH" \
    GitHubEnvironment="$GITHUB_ENVIRONMENT" \
    RoleName="$ROLE_NAME" \
    CreateOidcProvider="$create_oidc_provider" \
    ExistingOidcProviderArn="$oidc_provider_arn" \
    DownloadsBucket="$downloads_bucket" \
    DownloadsPrefix="$downloads_prefix" \
    DownloadsDistributionId="$downloads_distribution_id" \
  --tags \
    Project=crystal-lattice \
    Component=cli-downloads-github-actions \
    Profile="$PROFILE"

role_arn="$(
  aws --region "$REGION" cloudformation describe-stacks \
    --stack-name "$ROLE_STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='AwsRoleToAssume'].OutputValue | [0]" \
    --output text
)"

echo "CLI_DOWNLOADS_AWS_ROLE_TO_ASSUME=$role_arn"
echo "ROLE_STACK_NAME=$ROLE_STACK_NAME"
echo "ROLE_NAME=$ROLE_NAME"
echo "OIDC_PROVIDER_ARN=$oidc_provider_arn"
echo "GITHUB_REPOSITORY=${GITHUB_OWNER}/${GITHUB_REPO}"
echo "GITHUB_BRANCH=$GITHUB_BRANCH"
echo "GITHUB_ENVIRONMENT=$GITHUB_ENVIRONMENT"
echo "GITHUB_TAG_PATTERN=refs/tags/crystal-lattice-cli-v*"