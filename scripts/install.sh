#!/usr/bin/env bash
set -euo pipefail

PACKAGE_NAME="crystal-lattice-cli"
COMMAND_NAME="${COMMAND_NAME:-crystal-lattice}"
DEFAULT_DOWNLOAD_BASE_URL="https://crystal-lattice-downloads-874087778966.s3.us-east-1.amazonaws.com/crystal-lattice-cli"
DOWNLOAD_BASE_URL="${CRYSTAL_LATTICE_DOWNLOAD_BASE_URL:-${DOWNLOAD_BASE_URL:-$DEFAULT_DOWNLOAD_BASE_URL}}"
INSTALL_ROOT="${INSTALL_ROOT:-$HOME/.local/opt/$PACKAGE_NAME}"
BIN_DIR="${BIN_DIR:-$HOME/.local/bin}"
CRYSTAL_LATTICE_TEMP_DIR=""

log() {
  printf '%s\n' "$*"
}

fail() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

need_command() {
  command -v "$1" >/dev/null 2>&1 || fail "required command not found: $1"
}

normalize_tag() {
  case "$1" in
    crystal-lattice-cli-v*) printf '%s\n' "$1" ;;
    v*) printf 'crystal-lattice-cli-%s\n' "$1" ;;
    *) printf 'crystal-lattice-cli-v%s\n' "$1" ;;
  esac
}

detect_target() {
  local os
  local arch
  os="$(uname -s)"
  arch="$(uname -m)"

  case "$os" in
    Darwin)
      case "$arch" in
        x86_64) printf 'darwin-amd64\n' ;;
        arm64) printf 'darwin-arm64\n' ;;
        *) fail "unsupported macOS architecture: $arch" ;;
      esac
      ;;
    Linux)
      case "$arch" in
        x86_64 | amd64) printf 'linux-amd64\n' ;;
        *) fail "unsupported Linux architecture: $arch" ;;
      esac
      ;;
    *)
      fail "unsupported operating system for this shell installer: $os"
      ;;
  esac
}

fetch_latest_tag() {
  local url="$DOWNLOAD_BASE_URL/latest.txt"
  local latest
  latest="$(curl -fsSL "$url" | tr -d '[:space:]')"
  [ -n "$latest" ] || fail "latest version marker was empty: $url"
  normalize_tag "$latest"
}

extract_archive() {
  local archive="$1"
  local destination="$2"
  mkdir -p "$destination"
  tar -xzf "$archive" -C "$destination"
}

install_bundle() {
  local archive="$1"
  local archive_stem="$2"
  local temp_dir="$3"
  local extract_dir="$temp_dir/extract"
  local target_bundle="$INSTALL_ROOT/$archive_stem"
  local staging_bundle="$INSTALL_ROOT/.$archive_stem.staging"

  extract_archive "$archive" "$extract_dir"

  local extracted_bundle="$extract_dir/$archive_stem"
  [ -d "$extracted_bundle" ] || fail "archive did not contain expected directory: $archive_stem"
  [ -x "$extracted_bundle/crystal-lattice" ] || fail "archive did not contain executable crystal-lattice"

  mkdir -p "$INSTALL_ROOT"
  rm -rf "$staging_bundle"
  mv "$extracted_bundle" "$staging_bundle"
  rm -rf "$target_bundle"
  mv "$staging_bundle" "$target_bundle"

  mkdir -p "$BIN_DIR"
  ln -sfn "$target_bundle/crystal-lattice" "$BIN_DIR/$COMMAND_NAME"
  printf '%s\n' "$target_bundle"
}

verify_install() {
  local command_path="$1"
  "$command_path" --help >/dev/null
  local layout
  layout="$("$command_path" --runtime-layout-json)"
  printf '%s\n' "$layout" | grep -q '"layout": "bundled"' \
    || fail "installed command did not report bundled runtime layout"
  printf '%s\n' "$layout" | grep -q '/_internal/plugins' \
    || fail "installed command did not report bundled plugin path"
}

main() {
  need_command curl
  need_command tar
  need_command mktemp
  need_command grep

  local tag
  if [ -n "${VERSION:-}" ]; then
    tag="$(normalize_tag "$VERSION")"
  else
    tag="$(fetch_latest_tag)"
  fi

  local target
  target="$(detect_target)"

  local version="${tag#crystal-lattice-cli-v}"
  local archive_stem="$PACKAGE_NAME-v$version-$target"
  local archive_name="$archive_stem.tar.gz"
  local archive_url="$DOWNLOAD_BASE_URL/$archive_name"
  local temp_dir
  temp_dir="$(mktemp -d)"
  CRYSTAL_LATTICE_TEMP_DIR="$temp_dir"
  trap 'rm -rf "$CRYSTAL_LATTICE_TEMP_DIR"' EXIT

  log "Installing $PACKAGE_NAME $tag for $target"
  log "Downloading $archive_url"
  curl -fL "$archive_url" -o "$temp_dir/$archive_name"

  local installed_bundle
  installed_bundle="$(install_bundle "$temp_dir/$archive_name" "$archive_stem" "$temp_dir")"
  verify_install "$BIN_DIR/$COMMAND_NAME"

  log "Installed bundle: $installed_bundle"
  log "Installed command: $BIN_DIR/$COMMAND_NAME"
  case ":$PATH:" in
    *":$BIN_DIR:"*) ;;
    *) log "Add this directory to PATH if needed: $BIN_DIR" ;;
  esac
}

main "$@"