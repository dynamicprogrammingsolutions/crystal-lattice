#!/usr/bin/env bash

set -euo pipefail

BASE_URL=""
VERSION=""

usage() {
  cat <<'USAGE'
Verify a public Crystal Lattice Desktop CDN release and its checksum.

Usage:
  deploy/aws-desktop-downloads/smoke.sh --base-url URL [--version VERSION]

Options:
  --base-url URL               Public desktop download base URL.
  --version VERSION            Version without a tag prefix; defaults to latest.txt.
  --help, -h                   Show this help.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --base-url) BASE_URL="${2%/}"; shift 2 ;;
    --version) VERSION="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

: "${BASE_URL:?--base-url is required}"
command -v curl >/dev/null || { echo "curl is required" >&2; exit 1; }
command -v shasum >/dev/null || { echo "shasum is required" >&2; exit 1; }

latest="$(curl -fsSL "$BASE_URL/latest.txt" | tr -d '[:space:]')"
case "$latest" in
  crystal-lattice-desktop-v*) latest_version="${latest#crystal-lattice-desktop-v}" ;;
  *) echo "Unexpected desktop latest marker: $latest" >&2; exit 1 ;;
esac
VERSION="${VERSION:-$latest_version}"
if [ "$latest_version" != "$VERSION" ]; then
  echo "latest.txt mismatch: expected $VERSION, got $latest_version" >&2
  exit 1
fi

dmg="Crystal-Lattice-Desktop-v${VERSION}-universal.dmg"
checksum="${dmg}.sha256"
metadata="Crystal-Lattice-Desktop-v${VERSION}-release-metadata.json"
notarization="Crystal-Lattice-Desktop-v${VERSION}-notarization.json"

scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT
for name in "$dmg" "$checksum" "$metadata" "$notarization"; do
  echo "Downloading $BASE_URL/$name"
  curl -fsSL "$BASE_URL/$name" -o "$scratch/$name"
done

(cd "$scratch" && shasum -a 256 -c "$checksum")
python3 - "$scratch/$metadata" "$scratch/$notarization" "$VERSION" "$dmg" <<'PY'
import json
import sys
from pathlib import Path

metadata = json.loads(Path(sys.argv[1]).read_text())
notarization = json.loads(Path(sys.argv[2]).read_text())
version = sys.argv[3]
dmg = sys.argv[4]
if metadata.get("product") != "Crystal Lattice Desktop":
    raise SystemExit("unexpected desktop product metadata")
if metadata.get("marketing_version") != version or metadata.get("dmg") != dmg:
    raise SystemExit("desktop release metadata does not match the requested artifact")
if metadata.get("source_tree_clean") is not True:
    raise SystemExit("published desktop metadata was not built from a clean source tree")
if metadata.get("notarization_status") != "Accepted":
    raise SystemExit("desktop release metadata is not notarized")
if notarization.get("status") != "Accepted":
    raise SystemExit("desktop notarization response is not accepted")
if notarization.get("id") != metadata.get("notarization_id"):
    raise SystemExit("desktop notarization IDs differ")
print(f"Verified public Crystal Lattice Desktop {version}")
PY