#!/usr/bin/env bash

set -euo pipefail

STATIC_SITES_DIR="${STATIC_SITES_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
TEMPLATE_FILE="$STATIC_SITES_DIR/static-sites.yaml"

STACK_NAME="${CRYSTAL_LATTICE_STATIC_STACK_NAME:-crystal-lattice-static-sites-test}"
REGION="${AWS_REGION:-us-east-1}"
HOSTED_ZONE_NAME="${CRYSTAL_LATTICE_STATIC_HOSTED_ZONE_NAME:-dynamicprogrammingsolutions.com}"
HOSTED_ZONE_ID="${CRYSTAL_LATTICE_STATIC_HOSTED_ZONE_ID:-}"
LANDING_DOMAIN="${CRYSTAL_LATTICE_STATIC_LANDING_DOMAIN:-crystallattice.dev.dynamicprogrammingsolutions.com}"
DOCS_DOMAIN="${CRYSTAL_LATTICE_STATIC_DOCS_DOMAIN:-docs.crystallattice.dev.dynamicprogrammingsolutions.com}"
BUCKET_NAME_PREFIX="${CRYSTAL_LATTICE_STATIC_BUCKET_PREFIX:-crystal-lattice-static-test}"
JSON_OUTPUT=0

usage_common() {
  cat <<'USAGE'
Common options:
  --stack-name NAME
  --region REGION
  --hosted-zone-name NAME
  --hosted-zone-id ID
  --landing-domain DOMAIN
  --docs-domain DOMAIN
  --bucket-name-prefix PREFIX
  --json

Defaults:
  stack name:         crystal-lattice-static-sites-test
  region:             us-east-1
  hosted zone name:   dynamicprogrammingsolutions.com
  landing domain:     crystallattice.dev.dynamicprogrammingsolutions.com
  docs domain:        docs.crystallattice.dev.dynamicprogrammingsolutions.com
  bucket prefix:      crystal-lattice-static-test
USAGE
}

parse_common_args() {
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --stack-name) STACK_NAME="$2"; shift 2 ;;
      --region) REGION="$2"; shift 2 ;;
      --hosted-zone-name) HOSTED_ZONE_NAME="$2"; shift 2 ;;
      --hosted-zone-id) HOSTED_ZONE_ID="$2"; shift 2 ;;
      --landing-domain) LANDING_DOMAIN="$2"; shift 2 ;;
      --docs-domain) DOCS_DOMAIN="$2"; shift 2 ;;
      --bucket-name-prefix) BUCKET_NAME_PREFIX="$2"; shift 2 ;;
      --json) JSON_OUTPUT=1; shift ;;
      --help|-h) usage_common; exit 0 ;;
      *) echo "Unknown option: $1" >&2; usage_common >&2; exit 2 ;;
    esac
  done
}

require_aws_deploy_enabled() {
  if [ "${ALLOW_AWS_DEPLOY:-}" != "1" ]; then
    echo "Set ALLOW_AWS_DEPLOY=1 to create, update, sync, or delete AWS resources." >&2
    exit 2
  fi
}

aws_out() {
  aws --region "$REGION" "$@"
}

find_hosted_zone_id() {
  if [ -n "$HOSTED_ZONE_ID" ]; then
    HOSTED_ZONE_ID="${HOSTED_ZONE_ID#/hostedzone/}"
    return
  fi

  local zone_name="$HOSTED_ZONE_NAME"
  case "$zone_name" in
    *.) ;;
    *) zone_name="${zone_name}." ;;
  esac

  HOSTED_ZONE_ID="$(
    aws_out route53 list-hosted-zones-by-name \
      --dns-name "$zone_name" \
      --query "HostedZones[?Name=='${zone_name}' && Config.PrivateZone==\`false\`].Id | [0]" \
      --output text
  )"
  HOSTED_ZONE_ID="${HOSTED_ZONE_ID#/hostedzone/}"

  if [ -z "$HOSTED_ZONE_ID" ] || [ "$HOSTED_ZONE_ID" = "None" ]; then
    echo "Could not find public Route 53 hosted zone for $HOSTED_ZONE_NAME" >&2
    exit 1
  fi
}

stack_exists() {
  aws_out cloudformation describe-stacks --stack-name "$STACK_NAME" >/dev/null 2>&1
}

stack_output() {
  local key="$1"
  aws_out cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='$key'].OutputValue | [0]" \
    --output text
}

print_stack_outputs() {
  local landing_bucket docs_bucket landing_distribution docs_distribution hosted_zone_id
  local landing_url docs_url landing_cloudfront docs_cloudfront certificate_arn

  landing_bucket="$(stack_output LandingBucket)"
  docs_bucket="$(stack_output DocsBucket)"
  landing_distribution="$(stack_output LandingCloudFrontDistributionId)"
  docs_distribution="$(stack_output DocsCloudFrontDistributionId)"
  hosted_zone_id="$(stack_output HostedZoneId)"
  landing_url="$(stack_output LandingUrl)"
  docs_url="$(stack_output DocsUrl)"
  landing_cloudfront="$(stack_output LandingCloudFrontDomainName)"
  docs_cloudfront="$(stack_output DocsCloudFrontDomainName)"
  certificate_arn="$(stack_output CertificateArn)"

  if [ "$JSON_OUTPUT" -eq 1 ]; then
    printf '{"AWS_REGION":"%s","HOSTED_ZONE_ID":"%s","LANDING_BUCKET":"%s","DOCS_BUCKET":"%s","LANDING_CLOUDFRONT_DISTRIBUTION_ID":"%s","DOCS_CLOUDFRONT_DISTRIBUTION_ID":"%s","LANDING_URL":"%s","DOCS_URL":"%s","LANDING_CLOUDFRONT_DOMAIN":"%s","DOCS_CLOUDFRONT_DOMAIN":"%s","CERTIFICATE_ARN":"%s"}\n' \
      "$REGION" "$hosted_zone_id" "$landing_bucket" "$docs_bucket" \
      "$landing_distribution" "$docs_distribution" "$landing_url" "$docs_url" \
      "$landing_cloudfront" "$docs_cloudfront" "$certificate_arn"
  else
    echo "AWS_REGION=$REGION"
    echo "HOSTED_ZONE_ID=$hosted_zone_id"
    echo "LANDING_BUCKET=$landing_bucket"
    echo "DOCS_BUCKET=$docs_bucket"
    echo "LANDING_CLOUDFRONT_DISTRIBUTION_ID=$landing_distribution"
    echo "DOCS_CLOUDFRONT_DISTRIBUTION_ID=$docs_distribution"
    echo "LANDING_URL=$landing_url"
    echo "DOCS_URL=$docs_url"
    echo "LANDING_CLOUDFRONT_DOMAIN=$landing_cloudfront"
    echo "DOCS_CLOUDFRONT_DOMAIN=$docs_cloudfront"
    echo "CERTIFICATE_ARN=$certificate_arn"
  fi
}