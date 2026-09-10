#!/usr/bin/env bash
set -euo pipefail

PACKAGE_NAME="crystal-lattice-cli"
ARCHIVE_PACKAGE_NAME="crystal-lattice-python-runtime"
COMMAND_NAME="${COMMAND_NAME:-crystal-lattice}"
DEFAULT_DOWNLOAD_BASE_URL="https://download.crystallattice.dev/crystal-lattice-cli"
DOWNLOAD_BASE_URL="${CRYSTAL_LATTICE_DOWNLOAD_BASE_URL:-${DOWNLOAD_BASE_URL:-$DEFAULT_DOWNLOAD_BASE_URL}}"
INSTALL_ROOT="${INSTALL_ROOT:-$HOME/.local/opt/$PACKAGE_NAME}"
BIN_DIR="${BIN_DIR:-}"
LOCAL_ARCHIVE="${CRYSTAL_LATTICE_PYTHON_RUNTIME_ARCHIVE:-}"
CRYSTAL_LATTICE_TEMP_DIR=""
INCOMPATIBLE_COMMAND_DIR=""
LOG_STEP_TOTAL=5
LOG_STEP_INDEX=0

log_step() {
  LOG_STEP_INDEX=$((LOG_STEP_INDEX + 1))
  printf '[%d/%d] %s\n' "$LOG_STEP_INDEX" "$LOG_STEP_TOTAL" "$1"
}

log_detail() {
  printf '      %s\n' "$1"
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
    MINGW* | MSYS* | CYGWIN*)
      case "$arch" in
        x86_64 | amd64) printf 'windows-amd64\n' ;;
        *) fail "unsupported Windows architecture for Git Bash installer: $arch" ;;
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

windows_native_path() {
  if command -v cygpath >/dev/null 2>&1; then
    cygpath -w "$1"
  else
    printf '%s\n' "$1"
  fi
}

canonical_dir() {
  (CDPATH= cd -- "$1" 2>/dev/null && pwd -P)
}

path_contains_dir() {
  local requested
  requested="$(canonical_dir "$1")" || return 1
  local entry
  local resolved
  local entries=()
  IFS=':' read -r -a entries <<< "${PATH:-}"
  for entry in "${entries[@]}"; do
    [ -n "$entry" ] || continue
    resolved="$(canonical_dir "$entry")" || continue
    [ "$resolved" = "$requested" ] && return 0
  done
  return 1
}

is_world_writable_dir() {
  local permissions
  permissions="$(LC_ALL=C ls -ld "$1" 2>/dev/null)" || return 1
  permissions="${permissions%% *}"
  [ "${permissions:8:1}" = "w" ]
}

is_suitable_path_dir() {
  local directory="$1"
  case "$directory" in
    /*) ;;
    *) return 1 ;;
  esac
  [ -d "$directory" ] || return 1
  [ -w "$directory" ] || return 1

  local resolved
  resolved="$(canonical_dir "$directory")" || return 1
  if [ -n "$INCOMPATIBLE_COMMAND_DIR" ] \
    && [ "$resolved" = "$INCOMPATIBLE_COMMAND_DIR" ]; then
    return 1
  fi
  local working
  working="$(canonical_dir "$PWD")" || return 1
  [ "$resolved" != "$working" ] || return 1

  local temp_candidate
  for temp_candidate in "${TMPDIR:-}" "${TEMP:-}" "${TMP:-}" "/tmp"; do
    [ -n "$temp_candidate" ] || continue
    temp_candidate="$(canonical_dir "$temp_candidate")" || continue
    [ "$resolved" != "$temp_candidate" ] || return 1
  done

  if [ -n "${VIRTUAL_ENV:-}" ]; then
    local virtual_env
    if virtual_env="$(canonical_dir "$VIRTUAL_ENV")"; then
      case "$resolved" in
        "$virtual_env" | "$virtual_env"/*) return 1 ;;
      esac
    fi
  fi

  is_world_writable_dir "$resolved" && return 1
  return 0
}

select_default_bin_dir() {
  local existing
  existing="$(command -v "$COMMAND_NAME" 2>/dev/null || true)"
  case "$existing" in
    /*)
      local existing_dir
      existing_dir="${existing%/*}"
      local existing_layout
      existing_layout="$("$existing" --runtime-layout-json 2>/dev/null || true)"
      if printf '%s\n' "$existing_layout" \
        | grep -q '"layout"[[:space:]]*:[[:space:]]*"python-runtime"' \
        && path_contains_dir "$existing_dir" \
        && is_suitable_path_dir "$existing_dir"; then
        canonical_dir "$existing_dir"
        return
      fi
      INCOMPATIBLE_COMMAND_DIR="$(canonical_dir "$existing_dir" || true)"
      ;;
  esac

  local candidate
  for candidate in "$HOME/.local/bin" "$HOME/bin"; do
    if path_contains_dir "$candidate" && is_suitable_path_dir "$candidate"; then
      canonical_dir "$candidate"
      return
    fi
  done

  local entries=()
  IFS=':' read -r -a entries <<< "${PATH:-}"
  for candidate in "${entries[@]}"; do
    [ -n "$candidate" ] || continue
    if is_suitable_path_dir "$candidate"; then
      canonical_dir "$candidate"
      return
    fi
  done
  return 1
}

extract_archive() {
  local archive="$1"
  local destination="$2"
  local target="$3"
  mkdir -p "$destination"
  case "$target" in
    windows-*)
      if command -v unzip >/dev/null 2>&1; then
        unzip -q "$archive" -d "$destination"
      elif command -v powershell.exe >/dev/null 2>&1; then
        archive="$(windows_native_path "$archive")"
        destination="$(windows_native_path "$destination")"
        powershell.exe -NoProfile -Command \
          "Expand-Archive -LiteralPath '$archive' -DestinationPath '$destination' -Force"
      elif command -v pwsh.exe >/dev/null 2>&1; then
        archive="$(windows_native_path "$archive")"
        destination="$(windows_native_path "$destination")"
        pwsh.exe -NoProfile -Command \
          "Expand-Archive -LiteralPath '$archive' -DestinationPath '$destination' -Force"
      else
        fail "required command not found: unzip or powershell.exe"
      fi
      ;;
    *)
      tar -xzf "$archive" -C "$destination"
      ;;
  esac
}

archive_name_for() {
  local archive_stem="$1"
  local target="$2"
  case "$target" in
    windows-*) printf '%s.zip\n' "$archive_stem" ;;
    *) printf '%s.tar.gz\n' "$archive_stem" ;;
  esac
}

write_command_shim() {
  local target="$1"
  local target_bundle="$2"

  mkdir -p "$BIN_DIR"
  case "$target" in
    windows-*)
      cat > "$BIN_DIR/$COMMAND_NAME" <<EOF
#!/usr/bin/env sh
exec "$target_bundle/Scripts/crystal-lattice.cmd" "\$@"
EOF
      local native_launcher
      native_launcher="$(windows_native_path "$target_bundle/Scripts/crystal-lattice.cmd")"
      printf '@echo off\r\ncall "%s" %%*\r\n' "$native_launcher" \
        > "$BIN_DIR/$COMMAND_NAME.cmd"
      ;;
    *)
      cat > "$BIN_DIR/$COMMAND_NAME" <<EOF
#!/usr/bin/env sh
exec "$target_bundle/bin/crystal-lattice" "\$@"
EOF
      ;;
  esac
  chmod +x "$BIN_DIR/$COMMAND_NAME"
}

install_bundle() {
  local archive="$1"
  local archive_stem="$2"
  local target="$3"
  local temp_dir="$4"
  local extract_dir="$temp_dir/extract"
  local target_bundle="$INSTALL_ROOT/$archive_stem"
  local staging_bundle="$INSTALL_ROOT/.$archive_stem.staging"

  extract_archive "$archive" "$extract_dir" "$target"

  local extracted_bundle="$extract_dir/$archive_stem"
  [ -d "$extracted_bundle" ] || fail "archive did not contain expected directory: $archive_stem"
  case "$target" in
    windows-*)
      [ -f "$extracted_bundle/Scripts/crystal-lattice.cmd" ] \
        || fail "archive did not contain launcher Scripts/crystal-lattice.cmd"
      chmod +x "$extracted_bundle/Scripts/crystal-lattice.cmd" 2>/dev/null || true
      ;;
    *)
      [ -x "$extracted_bundle/bin/crystal-lattice" ] \
        || fail "archive did not contain launcher bin/crystal-lattice"
      ;;
  esac

  mkdir -p "$INSTALL_ROOT"
  rm -rf "$staging_bundle"
  mv "$extracted_bundle" "$staging_bundle"
  rm -rf "$target_bundle"
  mv "$staging_bundle" "$target_bundle"

  write_command_shim "$target" "$target_bundle"
  printf '%s\n' "$target_bundle"
}

verify_install() {
  local command_path="$1"
  "$command_path" --help >/dev/null
  local layout
  layout="$("$command_path" --runtime-layout-json)"
  printf '%s\n' "$layout" | grep -q '"layout": "python-runtime"' \
    || fail "installed command did not report python-runtime layout"
  printf '%s\n' "$layout" | grep -Eq '[/\\]plugins' \
    || fail "installed command did not report bundled plugin source path"
}

main() {
  log_step "Checking installer prerequisites and command location"
  need_command curl
  need_command mktemp
  need_command grep

  if [ -z "$BIN_DIR" ]; then
    BIN_DIR="$(select_default_bin_dir)" || fail \
      "could not find an existing writable command directory on PATH; set BIN_DIR to an explicit directory"
  fi
  log_detail "command directory: $BIN_DIR"

  log_step "Resolving the target platform and release"
  local target
  target="$(detect_target)"
  log_detail "target: $target"

  local temp_dir
  temp_dir="$(mktemp -d)"
  CRYSTAL_LATTICE_TEMP_DIR="$temp_dir"
  trap 'rm -rf "$CRYSTAL_LATTICE_TEMP_DIR"' EXIT

  local tag
  local archive_stem
  local archive_path
  if [ -n "$LOCAL_ARCHIVE" ]; then
    [ -f "$LOCAL_ARCHIVE" ] || fail "local archive does not exist: $LOCAL_ARCHIVE"
    local archive_dir
    local archive_name
    local archive_parent="${LOCAL_ARCHIVE%/*}"
    [ "$archive_parent" != "$LOCAL_ARCHIVE" ] || archive_parent="."
    archive_dir="$(canonical_dir "$archive_parent")" \
      || fail "could not resolve local archive directory: $LOCAL_ARCHIVE"
    archive_name="${LOCAL_ARCHIVE##*/}"
    archive_path="$archive_dir/$archive_name"
    case "$target:$archive_name" in
      windows-*:"$ARCHIVE_PACKAGE_NAME"-v*-"$target".zip)
        archive_stem="${archive_name%.zip}"
        ;;
      *:"$ARCHIVE_PACKAGE_NAME"-v*-"$target".tar.gz)
        archive_stem="${archive_name%.tar.gz}"
        ;;
      *)
        fail "local archive does not match current target $target: $archive_name"
        ;;
    esac
    local version="${archive_stem#"$ARCHIVE_PACKAGE_NAME-v"}"
    version="${version%-$target}"
    tag="crystal-lattice-cli-v$version"
    log_detail "release: $tag"
  else
    if [ -n "${VERSION:-}" ]; then
      tag="$(normalize_tag "$VERSION")"
    else
      tag="$(fetch_latest_tag)"
    fi
    local version="${tag#crystal-lattice-cli-v}"
    archive_stem="$ARCHIVE_PACKAGE_NAME-v$version-$target"
    local archive_name
    archive_name="$(archive_name_for "$archive_stem" "$target")"
    local archive_url="$DOWNLOAD_BASE_URL/$archive_name"
    archive_path="$temp_dir/$archive_name"
    log_detail "release: $tag"
  fi

  log_step "Acquiring the bundled-Python archive"
  if [ -n "$LOCAL_ARCHIVE" ]; then
    log_detail "Installing $PACKAGE_NAME $tag for $target from $archive_path"
  else
    log_detail "Downloading $archive_url"
    curl -fL "$archive_url" -o "$archive_path"
  fi

  log_step "Installing the runtime and command"
  local installed_bundle
  installed_bundle="$(install_bundle "$archive_path" "$archive_stem" "$target" "$temp_dir")"

  log_step "Verifying the installed command"
  verify_install "$BIN_DIR/$COMMAND_NAME"

  log_detail "Installed bundle: $installed_bundle"
  log_detail "Installed command: $BIN_DIR/$COMMAND_NAME"
  case "$target" in
    windows-*) log_detail "Installed Windows command: $BIN_DIR/$COMMAND_NAME.cmd" ;;
  esac
  case ":$PATH:" in
    *":$BIN_DIR:"*) ;;
    *) log_detail "Add this directory to PATH if needed: $BIN_DIR" ;;
  esac
}

main "$@"