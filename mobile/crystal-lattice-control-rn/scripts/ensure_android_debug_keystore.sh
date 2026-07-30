#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
keystore_path="$project_dir/android/app/debug.keystore"

if [[ -f "$keystore_path" ]]; then
  exit 0
fi

keytool \
  -genkeypair \
  -storetype JKS \
  -keystore "$keystore_path" \
  -storepass android \
  -alias androiddebugkey \
  -keypass android \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000 \
  -dname "CN=Android Debug,O=Android,C=US"
