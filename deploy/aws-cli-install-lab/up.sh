#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=deploy/aws-cli-install-lab/lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

setup_linux_instance() {
  local instance_id="$1"
  local script_b64 env_b64 env_command command_file command_id
  script_b64="$(base64_file_one_line "$SCRIPT_DIR/run-cli-api-smoke.sh")"
  env_command="rm -f '$LINUX_LAB_DIR/.env'"
  if [ -n "$INCLUDE_ENV_FILE" ]; then
    env_b64="$(base64_file_one_line "$INCLUDE_ENV_FILE")"
    env_command="printf '%s' '$env_b64' | base64 -d > '$LINUX_LAB_DIR/.env'; chmod 600 '$LINUX_LAB_DIR/.env'"
  fi

  command_file="$(mktemp -t crystal-lattice-cli-lab-linux.XXXXXX.json)"
  python3 - "$command_file" "$LINUX_LAB_DIR" "$script_b64" "$env_command" "$VERSION" "$BASE_URL" <<'PY'
import json
import sys

path, lab_dir, script_b64, env_command, version, base_url = sys.argv[1:7]
commands = [
    "set -euo pipefail",
    "id ssm-user >/dev/null 2>&1 || useradd -m ssm-user",
    "if command -v dnf >/dev/null 2>&1; then dnf install -y curl tar gzip unzip python3 || true; elif command -v yum >/dev/null 2>&1; then yum install -y curl tar gzip unzip python3 || true; fi",
    f"mkdir -p '{lab_dir}'",
    f"printf '%s' '{script_b64}' | base64 -d > '{lab_dir}/run-cli-api-smoke.sh'",
    f"chmod +x '{lab_dir}/run-cli-api-smoke.sh'",
    env_command,
    f"cat > '{lab_dir}/README.txt' <<'EOF'\nCrystal Lattice CLI manual install lab.\n\nRun:\n  cd {lab_dir}\n  ./run-cli-api-smoke.sh\n\nDefault version: {version or 'latest.txt'}\nDefault base URL: {base_url}\nEOF",
    f"chown -R ssm-user:ssm-user '{lab_dir}' || true",
]
with open(path, "w", encoding="utf-8") as f:
    json.dump({"commands": commands}, f)
PY

  command_id="$(aws_out ssm send-command \
    --instance-ids "$instance_id" \
    --document-name AWS-RunShellScript \
    --parameters "file://$command_file" \
    --query Command.CommandId \
    --output text)"
  rm -f "$command_file"
  wait_ssm_command "$command_id" "$instance_id" 900
}

setup_windows_instance() {
  local instance_id="$1"
  local script_b64 env_b64 env_command command_file command_id
  script_b64="$(base64_file_one_line "$SCRIPT_DIR/run-cli-api-smoke.sh")"
  env_command="Remove-Item -LiteralPath (Join-Path \$LabDir '.env') -Force -ErrorAction SilentlyContinue"
  if [ -n "$INCLUDE_ENV_FILE" ]; then
    env_b64="$(base64_file_one_line "$INCLUDE_ENV_FILE")"
    env_command="[IO.File]::WriteAllBytes((Join-Path \$LabDir '.env'), [Convert]::FromBase64String('$env_b64'))"
  fi

  command_file="$(mktemp -t crystal-lattice-cli-lab-windows.XXXXXX.json)"
  python3 - "$command_file" "$WINDOWS_LAB_DIR" "$script_b64" "$env_command" "$VERSION" "$BASE_URL" <<'PY'
import json
import sys

path, lab_dir, script_b64, env_command, version, base_url = sys.argv[1:7]
script = rf"""
$ErrorActionPreference = 'Stop'
$LabDir = '{lab_dir}'
New-Item -ItemType Directory -Force -Path $LabDir | Out-Null

$GitBash = 'C:\Program Files\Git\bin\bash.exe'
if (-not (Test-Path $GitBash)) {{
  Write-Host 'Installing Git for Windows for Git Bash support...'
  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
  $release = Invoke-RestMethod -Uri 'https://api.github.com/repos/git-for-windows/git/releases/latest' -Headers @{{'User-Agent'='crystal-lattice-cli-install-lab'}}
  $asset = $release.assets | Where-Object {{ $_.name -match '^Git-.*-64-bit\.exe$' }} | Select-Object -First 1
  if (-not $asset) {{ throw 'Could not find Git for Windows 64-bit installer asset in latest release.' }}
  $installer = Join-Path $env:TEMP $asset.name
  Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $installer
  Start-Process -FilePath $installer -ArgumentList '/VERYSILENT','/NORESTART','/NOCANCEL' -Wait
}}

[IO.File]::WriteAllBytes((Join-Path $LabDir 'run-cli-api-smoke.sh'), [Convert]::FromBase64String('{script_b64}'))
{env_command}
Set-Content -LiteralPath (Join-Path $LabDir 'README.txt') -Value @'
Crystal Lattice CLI manual install lab.

Open Git Bash:
  & "C:\Program Files\Git\bin\bash.exe" -l

Run:
  cd /c/crystal-lattice-cli-manual-lab
  ./run-cli-api-smoke.sh

Default version: {version or 'latest.txt'}
Default base URL: {base_url}
'@
"""
with open(path, "w", encoding="utf-8") as f:
    json.dump({"commands": [script]}, f)
PY

  command_id="$(aws_out ssm send-command \
    --instance-ids "$instance_id" \
    --document-name AWS-RunPowerShellScript \
    --parameters "file://$command_file" \
    --query Command.CommandId \
    --output text)"
  rm -f "$command_file"
  wait_ssm_command "$command_id" "$instance_id" 1800
}

parse_common_args "$@"
require_aws_deploy_enabled

if [ -n "$INCLUDE_ENV_FILE" ] && [ ! -f "$INCLUDE_ENV_FILE" ]; then
  echo "Env file not found: $INCLUDE_ENV_FILE" >&2
  exit 1
fi

resolve_default_vpc_and_subnet

aws_out cloudformation validate-template --template-body "file://$TEMPLATE_FILE" >/dev/null
aws_out cloudformation deploy \
  --stack-name "$STACK_NAME" \
  --template-file "$TEMPLATE_FILE" \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    NamePrefix="$NAME_PREFIX" \
    VpcId="$VPC_ID" \
    SubnetId="$SUBNET_ID" \
    LinuxInstanceType="$LINUX_INSTANCE_TYPE" \
    WindowsInstanceType="$WINDOWS_INSTANCE_TYPE" \
  --tags \
    Project=crystal-lattice \
    Component=cli-install-lab \
    Purpose=manual-test \
    StackName="$STACK_NAME"

linux_instance="$(stack_output LinuxInstanceId)"
windows_instance="$(stack_output WindowsInstanceId)"

wait_for_ssm_instance "$linux_instance" "Linux"
wait_for_ssm_instance "$windows_instance" "Windows"

if [ "$SKIP_SETUP" -eq 0 ]; then
  setup_linux_instance "$linux_instance"
  setup_windows_instance "$windows_instance"
fi

print_lab_outputs