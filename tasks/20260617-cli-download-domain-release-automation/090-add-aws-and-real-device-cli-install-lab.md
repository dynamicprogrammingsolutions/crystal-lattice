# Add AWS And Real-Device CLI Install Lab

Create a repeatable isolated manual testing lab for installed CLI releases. The AWS lab should cover Linux and Windows EC2 through SSM; macOS EC2 is intentionally skipped for now because EC2 Mac requires Dedicated Hosts. The same installed-CLI workflow should also be documented for real Linux, macOS, and Windows devices.

## Requirements checklist

- [x] Add `deploy/aws-cli-install-lab/` with scripts and README.
- [x] Add scripts/templates to provision Linux and Windows EC2 instances with no inbound SSH/RDP required.
- [x] Use SSM Session Manager for shell access.
- [x] Install or verify Git Bash on Windows and make Windows use the public `install.sh` path.
- [x] Copy a standard isolated test workspace and smoke script to both EC2 instances.
- [x] Support optional `.env` copying from the current checkout for real API calls.
- [x] The smoke script must install into workspace-local `.install/`, not global user paths.
- [x] The smoke script must create/use workspace-local `.crystal/` via `--config-local`.
- [x] The smoke script must start the HTTP server, send a real API request, and verify a tool call in session history.
- [x] Document equivalent real-device testing for Linux, macOS, and Windows Git Bash.
- [x] Add `up.sh`, `down.sh`, and `outputs.sh` commands similar to other `deploy/` helpers.
- [x] Add validation/testing notes and run local syntax/template checks.
- [ ] Run `up.sh` against AWS and verify Linux/Windows instances reach SSM.
- [ ] Run `run-cli-api-smoke.sh` on Linux EC2.
- [ ] Run `run-cli-api-smoke.sh` on Windows EC2 from Git Bash.

Parent Task: `tasks/20260617-cli-download-domain-release-automation/000-main.md`

Depends On:

- `tasks/20260617-cli-download-domain-release-automation/080-add-smoke-tests-and-domain-cutover-docs.md`

## Current Context

The public production download URL is:

```text
https://download.crystallattice.dev/crystal-lattice-cli
```

The shell installer now supports:

- Linux x64 via `.tar.gz`
- macOS x64/arm64 via `.tar.gz`
- Windows x64 from Git Bash/MSYS/Cygwin via `.zip`, then a Bash shim that calls `Scripts/crystal-lattice.cmd`

Therefore Windows manual testing should use Git Bash and the same installer command as Linux/macOS where possible. Direct PowerShell `.zip` extraction is only a fallback path.

## Desired AWS UX

Example:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-install-lab/up.sh \
  --stack-name crystal-lattice-cli-install-lab \
  --region us-east-1 \
  --version 0.1.0 \
  --include-env-file .env
```

Expected output should include:

```text
Linux:
  aws ssm start-session --target <linux-instance-id>
  cd /home/ssm-user/crystal-lattice-cli-manual-lab
  ./run-cli-api-smoke.sh

Windows:
  aws ssm start-session --target <windows-instance-id> --document-name AWS-StartInteractiveCommand --parameters command="powershell.exe"
  & "C:\Program Files\Git\bin\bash.exe" -l
  cd /c/crystal-lattice-cli-manual-lab
  ./run-cli-api-smoke.sh
```

Teardown:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-install-lab/down.sh \
  --stack-name crystal-lattice-cli-install-lab \
  --region us-east-1
```

## Standard Isolated Smoke Workflow

The smoke script should:

1. Load `.env` when present.
2. Install with `curl -fsSL https://download.crystallattice.dev/crystal-lattice-cli/install.sh | bash`.
3. Set `INSTALL_ROOT="$PWD/.install/opt/crystal-lattice-cli"` and `BIN_DIR="$PWD/.install/bin"`.
4. Run `crystal-lattice --help`.
5. Run `crystal-lattice --runtime-layout-json`.
6. Create `tool-target.txt`.
7. Start `crystal-lattice --server --config-local --host 127.0.0.1 --port 19000`.
8. Create a session through `POST /sessions`.
9. Send a real LLM request through `POST /sessions/{id}/send_message`.
10. Ask the model to use tools to read `./tool-target.txt`.
11. Poll `GET /sessions/{id}/messages`.
12. Assert the final history includes user, tool, and assistant messages, and the file marker appears in history.

## Documentation Requirements

Document:

- AWS prerequisites and required permissions.
- Cost note: Linux/Windows only; macOS EC2 deliberately skipped.
- SSM-only access and no inbound ports.
- How `.env` is copied and why it is opt-in.
- How to run the same test on real Linux/macOS/Windows devices.
- How to use PowerShell `.zip` install only as a Windows fallback.

## Testing Requirements

At minimum before marking complete:

```bash
bash -n deploy/aws-cli-install-lab/*.sh deploy/aws-cli-install-lab/lib/*.sh
aws --region us-east-1 cloudformation validate-template \
  --template-body file://deploy/aws-cli-install-lab/lab.yaml
```

If AWS deployment is run, also record:

- Linux instance reached SSM.
- Windows instance reached SSM.
- Git Bash was installed or already present on Windows.
- `run-cli-api-smoke.sh` passed on Linux.
- `run-cli-api-smoke.sh` passed on Windows Git Bash.

## Completion Notes

Added during completion on 2026-06-18.

Implemented `deploy/aws-cli-install-lab/`:

- `lab.yaml` creates Linux and Windows EC2 instances, an SSM instance role, and an egress-only/no-ingress security group.
- `up.sh` deploys the stack, waits for both instances to register with SSM, installs/prepares the lab workspace on both machines, installs Git for Windows when needed, and optionally copies `.env`.
- `outputs.sh` prints SSM connection commands and per-OS run instructions.
- `down.sh` deletes the stack.
- `run-cli-api-smoke.sh` is the shared isolated smoke script for Linux, macOS real devices, and Windows Git Bash. It installs from the production download domain into `.install/`, starts `crystal-lattice --server --config-local`, sends a real request, and checks for user/tool/assistant messages plus the file marker.
- `README.md` documents AWS usage, real-device usage, `.env` handling, and Windows Git Bash as the primary Windows path.

Local validation completed:

```bash
bash -n deploy/aws-cli-install-lab/*.sh deploy/aws-cli-install-lab/lib/*.sh
aws --region us-east-1 cloudformation validate-template \
  --template-body file://deploy/aws-cli-install-lab/lab.yaml
```

AWS lab creation and real API smoke execution were not run yet in this completion step.
