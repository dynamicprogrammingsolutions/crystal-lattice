#!/usr/bin/env bash
set -euo pipefail
umask 077

app_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repository_root="$(cd "${app_root}/../.." && pwd)"
source_cer="${1:-/Users/ferenci84/Downloads/developerID_application.cer}"
source_p12="${2:-/Users/ferenci84/Downloads/Certificates.p12}"
mobile_env="${repository_root}/mobile/crystal-lattice-control-rn/fastlane/.env"
expected_fingerprint="556CA737C19DFF54C2CA9A3D9E198EC17463FDE2DF02BC247AA911C8F229ACFC"

for input in "${source_cer}" "${source_p12}" "${mobile_env}"; do
  if [[ ! -f "${input}" ]]; then
    echo "Missing required local file: ${input}" >&2
    exit 1
  fi
done

if [[ "$(stat -f '%Su' "${source_p12}")" != "$(id -un)" ]]; then
  echo "The exported .p12 must be owned by the current user." >&2
  exit 1
fi
chmod 600 "${source_p12}"

export PATH="/opt/homebrew/opt/ruby@3.4/bin:/opt/homebrew/lib/ruby/gems/3.4.0/bin:${PATH}"

# The existing, untracked mobile .env contains the approved encrypted
# signing-repository settings and the App Store Connect team API key path.
set -a
# shellcheck disable=SC1090
source "${mobile_env}"
set +a

: "${MATCH_GIT_URL:?Missing MATCH_GIT_URL in mobile fastlane/.env}"
: "${MATCH_PASSWORD:?Missing MATCH_PASSWORD in mobile fastlane/.env}"
: "${APP_STORE_CONNECT_KEY_ID:?Missing APP_STORE_CONNECT_KEY_ID in mobile fastlane/.env}"
: "${APP_STORE_CONNECT_ISSUER_ID:?Missing APP_STORE_CONNECT_ISSUER_ID in mobile fastlane/.env}"
: "${APP_STORE_CONNECT_KEY_PATH:?Missing APP_STORE_CONNECT_KEY_PATH in mobile fastlane/.env}"
if [[ ! -f "${APP_STORE_CONNECT_KEY_PATH}" ]]; then
  echo "The configured App Store Connect key file does not exist." >&2
  exit 1
fi

export DESKTOP_MATCH_GIT_URL="${MATCH_GIT_URL}"
export DESKTOP_MATCH_GIT_BRANCH="${MATCH_GIT_BRANCH:-main}"
export DESKTOP_MATCH_READONLY=false

certificate_fingerprint() {
  openssl x509 -inform DER -in "$1" -outform DER |
    shasum -a 256 | awk '{ print toupper($1) }'
}

if [[ "$(certificate_fingerprint "${source_cer}")" != "${expected_fingerprint}" ]]; then
  echo "The .cer is not the verified G2 Developer ID Application certificate." >&2
  exit 1
fi

staging_dir="$(mktemp -d "${TMPDIR:-/tmp}/crystal-lattice-match-import.XXXXXXXX")"
cleanup() {
  if [[ -n "${temporary_keychain:-}" ]]; then
    security delete-keychain "${temporary_keychain}" >/dev/null 2>&1 || true
  fi
  if [[ -n "${staging_dir:-}" && -d "${staging_dir}" ]]; then
    rm -rf -- "${staging_dir}"
  fi
}
trap cleanup EXIT

staged_cer="${staging_dir}/developer_id_application.cer"
staged_p12="${staging_dir}/developer_id_application.p12"
api_key_json="${staging_dir}/app-store-connect-key.json"
cp "${source_cer}" "${staged_cer}"

echo "Enter the Keychain-exported .p12 password at the local OpenSSL prompt."
# Fastlane's read-only sync imports .p12 files with an empty certificate
# password. macOS security import rejects empty-password PKCS#12 files
# written by OpenSSL, even though OpenSSL can read them. Use a one-identity
# temporary keychain to export a blank-password .p12 in Apple's format.
# All intermediate material stays in a mode-0700 temporary directory.
decoded_pem="${staging_dir}/decoded.pem"
# Keychain Access can export certificate bags with RC2-40-CBC. OpenSSL 3
# requires its legacy provider to *read* such files; keep the new .p12
# export on the modern default algorithm.
pkcs12_read_options=()
if [[ "$(openssl version)" == OpenSSL\ 3.* ]]; then
  pkcs12_read_options=(-legacy)
fi
openssl pkcs12 "${pkcs12_read_options[@]}" -in "${source_p12}" -nodes -out "${decoded_pem}"
chmod 600 "${decoded_pem}"
temporary_password="$(openssl rand -hex 32)"
transfer_p12="${staging_dir}/transfer.p12"
pkcs12_write_options=()
if [[ "$(openssl version)" == OpenSSL\ 3.* ]]; then
  pkcs12_write_options=(-legacy)
fi
openssl pkcs12 -export "${pkcs12_write_options[@]}" \
  -certpbe PBE-SHA1-3DES -keypbe PBE-SHA1-3DES -macalg sha1 \
  -in "${decoded_pem}" -out "${transfer_p12}" -passout fd:3 \
  3<<<"${temporary_password}"
rm -f -- "${decoded_pem}"
temporary_keychain="${staging_dir}/developer-id-transfer.keychain"
security create-keychain -p '' "${temporary_keychain}"
security unlock-keychain -p '' "${temporary_keychain}"
security import "${transfer_p12}" -k "${temporary_keychain}" \
  -P "${temporary_password}" -T /usr/bin/security
unset temporary_password
rm -f -- "${transfer_p12}"
security export -k "${temporary_keychain}" -t identities -f pkcs12 \
  -P '' -o "${staged_p12}"
security delete-keychain "${temporary_keychain}"
temporary_keychain=
chmod 600 "${staged_p12}"

staged_fingerprint="$(
  openssl pkcs12 "${pkcs12_read_options[@]}" -in "${staged_p12}" -passin pass: -clcerts -nokeys |
    openssl x509 -outform DER |
    shasum -a 256 | awk '{ print toupper($1) }'
)"
if [[ "${staged_fingerprint}" != "${expected_fingerprint}" ]]; then
  echo "The .p12 certificate does not match the verified .cer." >&2
  exit 1
fi

certificate_public_key="$(
  openssl x509 -inform DER -in "${staged_cer}" -pubkey -noout |
    openssl pkey -pubin -outform DER |
    shasum -a 256 | awk '{ print $1 }'
)"
private_public_key="$(
  openssl pkcs12 "${pkcs12_read_options[@]}" -in "${staged_p12}" -passin pass: -nocerts -nodes |
    openssl pkey -pubout -outform DER |
    shasum -a 256 | awk '{ print $1 }'
)"
if [[ "${certificate_public_key}" != "${private_public_key}" ]]; then
  echo "The .p12 private key does not match the verified certificate." >&2
  exit 1
fi

ruby -rjson -e '
  File.write(
    ARGV.fetch(0),
    JSON.generate(
      key_id: ENV.fetch("APP_STORE_CONNECT_KEY_ID"),
      issuer_id: ENV.fetch("APP_STORE_CONNECT_ISSUER_ID"),
      key: File.read(ENV.fetch("APP_STORE_CONNECT_KEY_PATH")),
    ),
  )
' "${api_key_json}"
chmod 600 "${api_key_json}"

echo "Verified G2 Developer ID Application certificate and paired private key."
echo "Importing into the approved encrypted signing repository on branch ${DESKTOP_MATCH_GIT_BRANCH}."
echo "At the certificate prompt, enter: ${staged_cer}"
echo "At the private key prompt, enter: ${staged_p12}"
echo "At the optional provisioning profile prompt, press Return without a path."

cd "${app_root}"
bundle exec fastlane match import \
  --type developer_id \
  --storage_mode git \
  --git_url "${DESKTOP_MATCH_GIT_URL}" \
  --git_branch "${DESKTOP_MATCH_GIT_BRANCH}" \
  --team_id "${APPLE_TEAM_ID:-73Q43R2PD4}" \
  --app_identifier com.dynamicprogrammingsolutions.crystallatticecontrol.macos \
  --api_key_path "${api_key_json}" \
  --readonly false

echo "Import completed. Temporary API-key and empty-password .p12 files will be removed on exit."