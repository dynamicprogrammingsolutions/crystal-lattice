#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=deploy/aws-cli-downloads/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

BASE_URL=""
VERSION=""
SKIP_INSTALL=0

usage() {
  cat <<'USAGE'
Smoke-test a CLI download endpoint.

Usage:
  deploy/aws-cli-downloads/smoke.sh [common options] [options]

Options:
  --base-url URL               Override stack output DownloadsBaseUrl.
  --version VERSION            Version without tag prefix. Defaults to latest.txt.
  --skip-install               Do not run the current-platform installer check.
  --help, -h                   Show this help.
USAGE
  usage_common
}

args=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --base-url) BASE_URL="$2"; shift 2 ;;
    --version) VERSION="$2"; shift 2 ;;
    --skip-install) SKIP_INSTALL=1; shift ;;
    --help|-h) usage; exit 0 ;;
    *) args+=("$1"); shift ;;
  esac
done

if [ "${#args[@]}" -gt 0 ]; then
  parse_common_args "${args[@]}"
else
  parse_common_args
fi

if [ -z "$BASE_URL" ]; then
  if ! stack_exists; then
    echo "CloudFormation stack does not exist and --base-url was not provided: $STACK_NAME" >&2
    exit 1
  fi
  BASE_URL="$(downloads_base_url)"
fi

need_command() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "required command not found: $1" >&2
    exit 1
  }
}

need_command curl
need_command grep

curl -fsSI "$BASE_URL/install.sh" >/dev/null
installer="$(curl -fsSL "$BASE_URL/install.sh")"
printf '%s\n' "$installer" | grep -q "DEFAULT_DOWNLOAD_BASE_URL=\"$BASE_URL\"" || {
  echo "install.sh does not default to $BASE_URL" >&2
  exit 1
}

latest="$(curl -fsSL "$BASE_URL/latest.txt" | tr -d '[:space:]')"
[ -n "$latest" ] || {
  echo "latest.txt was empty" >&2
  exit 1
}

if [ -z "$VERSION" ]; then
  case "$latest" in
    crystal-lattice-cli-v*) VERSION="${latest#crystal-lattice-cli-v}" ;;
    v*) VERSION="${latest#v}" ;;
    *) VERSION="$latest" ;;
  esac
fi

expected_tag="$(normalize_version_tag "$VERSION")"
if [ "$latest" != "$expected_tag" ]; then
  echo "latest.txt mismatch: expected $expected_tag, got $latest" >&2
  exit 1
fi

while IFS= read -r name; do
  echo "Checking $BASE_URL/$name"
  curl -fsSI "$BASE_URL/$name" >/dev/null
done < <(archive_names_for_version "$VERSION")

if [ "$SKIP_INSTALL" -eq 1 ]; then
  echo "Download endpoint smoke test passed: $BASE_URL"
  exit 0
fi

os="$(uname -s 2>/dev/null || true)"
arch="$(uname -m 2>/dev/null || true)"
case "$os:$arch" in
  Darwin:x86_64|Darwin:arm64|Linux:x86_64|Linux:amd64)
    need_command bash
    test_root="$(mktemp -d)"
    trap 'rm -rf "$test_root"' EXIT
    printf '%s\n' "$installer" | \
      VERSION="$VERSION" \
      INSTALL_ROOT="$test_root/opt/crystal-lattice-cli" \
      BIN_DIR="$test_root/bin" \
      bash
    "$test_root/bin/crystal-lattice" --help >/dev/null
    "$test_root/bin/crystal-lattice" --runtime-layout-json | grep -q '"layout": "python-runtime"'
    ;;
  *)
    echo "Skipping installer execution on unsupported local platform: $os $arch"
    ;;
esac

echo "Download endpoint smoke test passed: $BASE_URL"