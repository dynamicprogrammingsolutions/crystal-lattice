#!/usr/bin/env bash

set -euo pipefail

APP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_SVG="$APP_ROOT/src/assets/icons/icon.svg"
APPICON_DIR="$APP_ROOT/ios/CrystalLatticeControlRN/Images.xcassets/AppIcon.appiconset"
TMP_DIR="${TMPDIR:-/tmp}/crystal-lattice-ios-icons"

if ! command -v rsvg-convert >/dev/null 2>&1; then
  echo "Missing rsvg-convert. Install librsvg before generating iOS app icons." >&2
  exit 2
fi

if ! command -v magick >/dev/null 2>&1; then
  echo "Missing magick. Install ImageMagick before generating iOS app icons." >&2
  exit 2
fi

mkdir -p "$TMP_DIR"

render_icon() {
  local pixels="$1"
  local name="$2"
  local inner=$((pixels * 82 / 100))
  local raw_png="$TMP_DIR/${name}.raw.png"

  if [ "$inner" -lt 1 ]; then
    inner="$pixels"
  fi

  rsvg-convert \
    --keep-aspect-ratio \
    --width "$inner" \
    --height "$inner" \
    --page-width "$inner" \
    --page-height "$inner" \
    --background-color none \
    --output "$raw_png" \
    "$SOURCE_SVG"

  magick "$raw_png" \
    -background white \
    -alpha remove \
    -alpha off \
    -gravity center \
    -extent "${pixels}x${pixels}" \
    "$APPICON_DIR/$name"
}

render_icon 40 Icon-App-20x20@2x.png
render_icon 60 Icon-App-20x20@3x.png
render_icon 58 Icon-App-29x29@2x.png
render_icon 87 Icon-App-29x29@3x.png
render_icon 80 Icon-App-40x40@2x.png
render_icon 120 Icon-App-40x40@3x.png
render_icon 120 Icon-App-60x60@2x.png
render_icon 180 Icon-App-60x60@3x.png
render_icon 1024 Icon-App-1024x1024@1x.png

magick identify -format '%f %wx%h %[channels]\n' "$APPICON_DIR"/*.png | sort