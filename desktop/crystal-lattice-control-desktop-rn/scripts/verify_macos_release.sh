#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -ne 1 ]]; then
  echo "usage: $0 /path/to/Crystal\\ Lattice\\ Desktop.app" >&2
  exit 2
fi

app_path="$1"
info_plist="${app_path}/Contents/Info.plist"

if [[ ! -d "${app_path}" || ! -f "${info_plist}" ]]; then
  echo "Missing macOS application bundle: ${app_path}" >&2
  exit 1
fi

assert_plist_value() {
  local key="$1"
  local expected="$2"
  local actual
  actual="$(/usr/libexec/PlistBuddy -c "Print :${key}" "${info_plist}")"
  if [[ "${actual}" != "${expected}" ]]; then
    echo "Unexpected ${key}: expected '${expected}', found '${actual}'" >&2
    exit 1
  fi
}

assert_plist_value CFBundleDisplayName "Crystal Lattice Desktop"
assert_plist_value CFBundleIdentifier "com.dynamicprogrammingsolutions.crystallatticecontrol.macos"
assert_plist_value CFBundleShortVersionString "${MACOS_MARKETING_VERSION:-0.9.0}"
assert_plist_value CFBundleVersion "${MACOS_BUILD_NUMBER:-1}"
assert_plist_value LSMinimumSystemVersion "14.0"
assert_plist_value NSAppTransportSecurity:NSAllowsLocalNetworking "true"

if /usr/libexec/PlistBuddy \
  -c "Print :NSAppTransportSecurity:NSAllowsArbitraryLoads" \
  "${info_plist}" >/dev/null 2>&1; then
  echo "Release app must not enable NSAllowsArbitraryLoads" >&2
  exit 1
fi

if [[ ! -f "${app_path}/Contents/Resources/main.jsbundle" ]]; then
  echo "Release app is missing Contents/Resources/main.jsbundle" >&2
  exit 1
fi

if [[ ! -f "${app_path}/Contents/Resources/PrivacyInfo.xcprivacy" ]]; then
  echo "Release app is missing PrivacyInfo.xcprivacy" >&2
  exit 1
fi

checked=0
while IFS= read -r -d '' candidate; do
  if ! file "${candidate}" | grep -q "Mach-O"; then
    continue
  fi

  architectures="$(lipo -archs "${candidate}")"
  for required_architecture in arm64 x86_64; do
    if [[ " ${architectures} " != *" ${required_architecture} "* ]]; then
      echo "Missing ${required_architecture} slice in ${candidate}: ${architectures}" >&2
      exit 1
    fi
  done
  checked=$((checked + 1))
done < <(find "${app_path}/Contents" -type f -print0)

if [[ "${checked}" -eq 0 ]]; then
  echo "No Mach-O files found in ${app_path}" >&2
  exit 1
fi

echo "Verified ${checked} universal Mach-O files in ${app_path}"