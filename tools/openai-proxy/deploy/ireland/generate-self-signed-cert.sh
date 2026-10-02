#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
output_dir="${REVIEWER_PROXY_CERT_DIR:-${script_dir}/certs}"
server_name="${REVIEWER_PROXY_SERVER_NAME:-ireland-s1.dynamicprogrammingsolutions.com}"
subject_alt_names="${REVIEWER_PROXY_CERT_SAN:-DNS:${server_name}}"
valid_days="${REVIEWER_PROXY_CERT_VALID_DAYS:-365}"
key_bits="${REVIEWER_PROXY_CERT_KEY_BITS:-3072}"

mkdir -p "$output_dir"
umask 077
openssl req \
  -x509 \
  -newkey "rsa:${key_bits}" \
  -nodes \
  -keyout "$output_dir/server.key" \
  -out "$output_dir/server.crt" \
  -days "$valid_days" \
  -subj "/CN=${server_name}" \
  -addext "subjectAltName=${subject_alt_names}" \
  -addext "basicConstraints=critical,CA:TRUE" \
  -addext "keyUsage=critical,digitalSignature,keyEncipherment,keyCertSign" \
  -addext "extendedKeyUsage=serverAuth"

chmod 600 "$output_dir/server.key"
chmod 644 "$output_dir/server.crt"
printf '%s\n' "$output_dir/server.crt"