#!/usr/bin/env bash
set -euo pipefail

app_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repository_root="$(cd "${app_root}/../.." && pwd)"
source_icon="${repository_root}/mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN/Images.xcassets/AppIcon.appiconset/Icon-App-1024x1024@1x.png"
output_directory="${app_root}/macos/CrystalLatticeControlDesktopRN-macOS/Assets.xcassets/AppIcon.appiconset"

if [[ ! -f "${source_icon}" ]]; then
  echo "Missing approved iOS icon source: ${source_icon}" >&2
  exit 1
fi

generate_icon() {
  local pixels="$1"
  local filename="$2"
  sips --resampleHeightWidth "${pixels}" "${pixels}" \
    "${source_icon}" \
    --out "${output_directory}/${filename}" >/dev/null
}

generate_icon 16 AppIcon-16.png
generate_icon 32 AppIcon-16@2x.png
generate_icon 32 AppIcon-32.png
generate_icon 64 AppIcon-32@2x.png
generate_icon 128 AppIcon-128.png
generate_icon 256 AppIcon-128@2x.png
generate_icon 256 AppIcon-256.png
generate_icon 512 AppIcon-256@2x.png
generate_icon 512 AppIcon-512.png
generate_icon 1024 AppIcon-512@2x.png

echo "Generated macOS app icons from ${source_icon}"