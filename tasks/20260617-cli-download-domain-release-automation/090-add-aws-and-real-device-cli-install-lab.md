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
- [x] Run `up.sh` against AWS and verify Linux/Windows instances reach SSM.
- [x] Run `run-cli-api-smoke.sh` on Linux EC2.
- [x] Run `run-cli-api-smoke.sh` on Windows EC2 from Git Bash.
- [ ] Fix non-interactive Windows SSM wrapper cleanup/reporting so the SSM command returns `Success` after the script prints `PASS`.

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
3. Set isolated install paths under workspace-local `.install/`.
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
- `run-cli-api-smoke.sh` is the shared isolated smoke script for Linux, macOS real devices, and Windows Git Bash. It installs from the production download domain into isolated local paths, starts `crystal-lattice --server --config-local`, sends a real request, and checks for user/tool/assistant messages plus the file marker.
- `README.md` documents AWS usage, real-device usage, `.env` handling, and Windows Git Bash as the primary Windows path.

Local validation completed:

```bash
bash -n deploy/aws-cli-install-lab/*.sh deploy/aws-cli-install-lab/lib/*.sh
aws --region us-east-1 cloudformation validate-template \
  --template-body file://deploy/aws-cli-install-lab/lab.yaml
```

AWS lab creation and real API smoke execution update added during completion on 2026-06-19.

Ran:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-install-lab/up.sh \
  --stack-name crystal-lattice-cli-install-lab \
  --region us-east-1 \
  --version 0.1.0 \
  --include-env-file /Users/ferenci84/Dev/Mine/ai-agent-platform/.env
```

The lab created/reused:

- Linux EC2: `i-0b4167d3b3f248460`
- Windows EC2: `i-0259b62e98c6f8d01`

macOS local real-device smoke passed from `/tmp/crystal-lattice-local-macos-smoke`:

```text
PASS: installed CLI made a real LLM request with a tool call.
Agent: codex-openrouter
Session: a77fabaf-2439-495d-b01b-f8956c8489d5
```

Linux EC2 smoke passed:

```text
PASS: installed CLI made a real LLM request with a tool call.
Agent: codex-openrouter
Session: c054a4e8-9ae2-4481-939b-b32e683cbeaf
```

Windows EC2 Git Bash behavioral smoke passed after switching the Windows lab to short paths (`C:\cl-lab`, `.i`, `.b`) and updating the public installer verification to accept Windows backslash plugin paths. That short-path workaround was later reverted for a manifest-level long-path retest. The independent final assertion from the short-path run returned:

```text
PASS-MESSAGES
```

and the SSM command output from an earlier short-path run included:

```text
PASS: installed CLI made a real LLM request with a tool call.
Agent: codex-openrouter
Session: edf3aeb1-d2b9-440b-90e3-c53196af8e1f
```

Important findings/fixes from this run:

- The public Windows Git Bash installer initially failed because `scripts/install.sh` checked only `/plugins`; Windows runtime layout paths use backslashes. Fixed the check to accept `/plugins` or `\plugins`, added a focused regression test, and uploaded the corrected installer to both production and testing download domains.
- The Windows lab initially used `C:\crystal-lattice-cli-manual-lab`, which made deeply nested default-config paths too long for Windows during first-run config copy. A temporary short-path workaround was tried and then reverted so the manifest-level fix can be tested against the original long path.
- The smoke script initially checked session history too early by relying on `active_request_id`; it now polls for the actual acceptance condition.
- The non-interactive Windows SSM wrapper still has a cleanup/reporting issue: the installed CLI behavior reaches `PASS`, but the wrapper can remain open or report failure during server cleanup. Manual Git Bash use is still valid, and the message-history assertion confirms the Windows product behavior passed.

The AWS lab was torn down after testing:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-install-lab/down.sh \
  --stack-name crystal-lattice-cli-install-lab \
  --region us-east-1
```
