#!/usr/bin/env bash
set -euo pipefail

android_home="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/Library/Android/sdk}}"
adb_bin="$android_home/platform-tools/adb"
emulator_bin="$android_home/emulator/emulator"
avd_name="${DETOX_ANDROID_AVD:-Medium_Phone_API_36.1}"

find_matching_emulator() {
  "$adb_bin" devices |
    awk '$1 ~ /^emulator-/ && $2 == "device" { print $1 }' |
    while read -r serial; do
      running_avd="$("$adb_bin" -s "$serial" emu avd name 2>/dev/null | head -n 1 | tr -d '\r')"
      if [[ "$running_avd" == "$avd_name" ]]; then
        printf '%s\n' "$serial"
        return
      fi
    done
}

serial="$(find_matching_emulator || true)"
if [[ -z "$serial" ]]; then
  log_path="${TMPDIR:-/tmp}/clc-detox-android-emulator.log"
  nohup "$emulator_bin" \
    -avd "$avd_name" \
    -no-audio \
    -no-boot-anim \
    >"$log_path" 2>&1 &

  "$adb_bin" wait-for-device
  for _attempt in $(seq 1 180); do
    serial="$(find_matching_emulator || true)"
    if [[ -n "$serial" ]] &&
      [[ "$("$adb_bin" -s "$serial" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" == "1" ]]; then
      break
    fi
    sleep 1
  done
fi

if [[ -z "$serial" ]]; then
  echo "Unable to start Android AVD: $avd_name" >&2
  exit 1
fi

"$adb_bin" -s "$serial" shell settings put secure immersive_mode_confirmations confirmed
"$adb_bin" -s "$serial" shell input keyevent KEYCODE_HOME
"$adb_bin" -s "$serial" emu kill >/dev/null

for _attempt in $(seq 1 60); do
  if ! "$adb_bin" devices | awk '{print $1}' | grep -qx "$serial"; then
    exit 0
  fi
  sleep 1
done

echo "Android emulator did not stop after environment preparation: $serial" >&2
exit 1
