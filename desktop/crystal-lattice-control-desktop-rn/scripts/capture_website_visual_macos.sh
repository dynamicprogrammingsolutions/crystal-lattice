#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
derived_data="${project_root}/build/website-visual-derived-data"
workspace="${project_root}/macos/CrystalLatticeControlDesktopRN.xcworkspace"
scheme="CrystalLatticeControlDesktopRN-macOS"
destination="platform=macOS,arch=arm64"
app="${derived_data}/Build/Products/Release/Crystal Lattice Desktop.app"
executable="${app}/Contents/MacOS/Crystal Lattice Desktop"
output_dir="${project_root}/artifacts/website-visual"

rm -rf "${output_dir}"
mkdir -p "${output_dir}"

FORCE_BUNDLING=1 xcodebuild \
  -workspace "${workspace}" \
  -scheme "${scheme}" \
  -configuration Release \
  -destination "${destination}" \
  -derivedDataPath "${derived_data}" \
  build

capture_one() {
  local kind="$1"
  local appearance="$2"
  local output="${output_dir}/${kind}-${appearance}.png"

  pkill -f "${executable}" 2>/dev/null || true
  CLC_ENABLE_WEBSITE_VISUAL_HARNESS=1 \
    CLC_WEBSITE_VISUAL_KIND="${kind}" \
    CLC_WEBSITE_VISUAL_OUTPUT_PATH="${output}" \
    "${executable}" \
    -clcWebsiteVisualTheme "${appearance}" \
    -AppleInterfaceStyle "$([ "${appearance}" = dark ] && echo Dark || echo Light)" \
    >"/tmp/crystal-lattice-${kind}-${appearance}.log" 2>&1 &
  local app_pid=$!

  for _attempt in $(seq 1 30); do
    if [[ -s "${output}" ]]; then
      break
    fi
    sleep 1
  done

  if [[ ! -s "${output}" ]]; then
    echo "Harness did not create ${output}" >&2
    tail -n 100 "/tmp/crystal-lattice-${kind}-${appearance}.log" >&2 || true
    exit 1
  fi

  kill "${app_pid}" 2>/dev/null || true
  wait "${app_pid}" 2>/dev/null || true
}

capture_one agent-codex light
capture_one agent-codex dark
capture_one agent-claude light
capture_one agent-claude dark
capture_one cross-device light
capture_one cross-device dark
capture_one workspace light
capture_one workspace dark

ls -lh "${output_dir}"/*.png