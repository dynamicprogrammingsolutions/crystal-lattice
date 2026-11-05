#!/usr/bin/env bash

set -euo pipefail

STATIC_SITES_DIR="${STATIC_SITES_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
STAGING_TEMPLATE_FILE="$STATIC_SITES_DIR/staging-site.yaml"

STACK_NAME="${CRYSTAL_LATTICE_STAGING_STACK_NAME:-crystal-lattice-static-site-staging}"
REGION="${AWS_REGION:-us-east-1}"
HOSTED_ZONE_NAME="${CRYSTAL_LATTICE_STAGING_HOSTED_ZONE_NAME:-crystallattice.dev}"
HOSTED_ZONE_ID="${CRYSTAL_LATTICE_STAGING_HOSTED_ZONE_ID:-}"
DOMAIN_NAME="${CRYSTAL_LATTICE_STAGING_DOMAIN:-staging.crystallattice.dev}"
BUCKET_NAME_PREFIX="${CRYSTAL_LATTICE_STAGING_BUCKET_PREFIX:-crystal-lattice-staging}"
JSON_OUTPUT=0

usage_staging_common() {
  cat <<'USAGE'
Common staging options:
  --stack-name NAME
  --region REGION
  --hosted-zone-name NAME
  --hosted-zone-id ID
  --domain DOMAIN
  --bucket-name-prefix PREFIX
  --json

Defaults:
  stack name:         crystal-lattice-static-site-staging
  region:             us-east-1
  hosted zone name:   crystallattice.dev
  domain:             staging.crystallattice.dev
  bucket prefix:      crystal-lattice-staging
USAGE
}

parse_staging_args() {
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --stack-name) STACK_NAME="$2"; shift 2 ;;
      --region) REGION="$2"; shift 2 ;;
      --hosted-zone-name) HOSTED_ZONE_NAME="$2"; shift 2 ;;
      --hosted-zone-id) HOSTED_ZONE_ID="$2"; shift 2 ;;
      --domain) DOMAIN_NAME="$2"; shift 2 ;;
      --bucket-name-prefix) BUCKET_NAME_PREFIX="$2"; shift 2 ;;
      --json) JSON_OUTPUT=1; shift ;;
      --help|-h) usage_staging_common; exit 0 ;;
      *) echo "Unknown option: $1" >&2; usage_staging_common >&2; exit 2 ;;
    esac
  done
}

require_staging_deploy_enabled() {
  if [ "${ALLOW_AWS_DEPLOY:-}" != "1" ]; then
    echo "Set ALLOW_AWS_DEPLOY=1 to create, update, or sync staging resources." >&2
    exit 2
  fi
}

staging_aws() {
  aws --region "$REGION" "$@"
}

find_staging_hosted_zone_id() {
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
    staging_aws route53 list-hosted-zones-by-name \
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

staging_stack_output() {
  local key="$1"
  staging_aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='$key'].OutputValue | [0]" \
    --output text
}

print_staging_outputs() {
  local bucket distribution url cloudfront certificate headers hosted_zone
  bucket="$(staging_stack_output StagingBucket)"
  distribution="$(staging_stack_output StagingCloudFrontDistributionId)"
  url="$(staging_stack_output StagingUrl)"
  cloudfront="$(staging_stack_output StagingCloudFrontDomainName)"
  certificate="$(staging_stack_output CertificateArn)"
  headers="$(staging_stack_output ResponseHeadersPolicyId)"
  hosted_zone="$(staging_stack_output HostedZoneId)"

  if [ "$JSON_OUTPUT" -eq 1 ]; then
    printf '{"AWS_REGION":"%s","HOSTED_ZONE_ID":"%s","STAGING_BUCKET":"%s","STAGING_CLOUDFRONT_DISTRIBUTION_ID":"%s","STAGING_URL":"%s","STAGING_CLOUDFRONT_DOMAIN":"%s","CERTIFICATE_ARN":"%s","RESPONSE_HEADERS_POLICY_ID":"%s"}\n' \
      "$REGION" "$hosted_zone" "$bucket" "$distribution" "$url" \
      "$cloudfront" "$certificate" "$headers"
  else
    echo "AWS_REGION=$REGION"
    echo "HOSTED_ZONE_ID=$hosted_zone"
    echo "STAGING_BUCKET=$bucket"
    echo "STAGING_CLOUDFRONT_DISTRIBUTION_ID=$distribution"
    echo "STAGING_URL=$url"
    echo "STAGING_CLOUDFRONT_DOMAIN=$cloudfront"
    echo "CERTIFICATE_ARN=$certificate"
    echo "RESPONSE_HEADERS_POLICY_ID=$headers"
  fi
}