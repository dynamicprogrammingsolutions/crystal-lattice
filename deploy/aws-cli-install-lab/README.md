# AWS CLI Install Lab

This lab creates isolated Linux and Windows EC2 instances for manual
end-to-end testing of the public Crystal Lattice CLI installer. It deliberately
skips EC2 macOS for now because EC2 Mac requires Dedicated Hosts. Use a real
macOS device with the same isolated smoke script for macOS coverage.

The lab uses:

- Amazon Linux 2023 x64
- Windows Server 2022 x64
- SSM Session Manager for access
- no inbound SSH or RDP rules
- Git Bash on Windows, so Windows uses the same `install.sh` path as Linux and
  macOS
- workspace-local `.install/`, `.crystal`, and `logs/` directories on
  Linux/macOS
- short `C:\cl-lab`, `.i/`, and `.b/` paths on Windows Git Bash to avoid
  Windows path-length issues in deeply nested bundled config files

## Prerequisites

- AWS CLI configured locally.
- Permission to create EC2 instances, security groups, IAM roles/instance
  profiles, CloudFormation stacks, and SSM commands.
- Default VPC with a public default subnet, or pass `--vpc-id` and
  `--subnet-id`.
- `ALLOW_AWS_DEPLOY=1` for commands that create or delete AWS resources.
- Optional `.env` containing `OPENROUTER_API_KEY` or `OPENAI_API_KEY`.

The `.env` copy is opt-in. When `--include-env-file` is used, the helper sends
the file content through SSM Run Command so the test scripts can make real API
calls. Treat the lab instances and SSM command history as sensitive while the
lab is running.

## Up

Create or update the lab:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-install-lab/up.sh \
  --stack-name crystal-lattice-cli-install-lab \
  --region us-east-1 \
  --version 0.1.0 \
  --include-env-file .env
```

Without `.env` copying:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-install-lab/up.sh \
  --stack-name crystal-lattice-cli-install-lab \
  --region us-east-1 \
  --version 0.1.0
```

Use explicit networking when there is no default VPC/subnet:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-install-lab/up.sh \
  --vpc-id vpc-... \
  --subnet-id subnet-...
```

## Connect And Run

Linux:

```bash
aws --region us-east-1 ssm start-session --target <linux-instance-id>
cd /home/ssm-user/crystal-lattice-cli-manual-lab
./run-cli-api-smoke.sh
```

Windows PowerShell session:

```bash
aws --region us-east-1 ssm start-session \
  --target <windows-instance-id> \
  --document-name AWS-StartInteractiveCommand \
  --parameters command="powershell.exe"
```

Then open Git Bash and run the same smoke script:

```powershell
& "C:\Program Files\Git\bin\bash.exe" -l
```

```bash
cd /c/cl-lab
./run-cli-api-smoke.sh
```

To run the Windows smoke non-interactively through SSM while preserving the Git
Bash exit code:

```bash
aws --region us-east-1 ssm send-command \
  --instance-ids <windows-instance-id> \
  --document-name AWS-RunPowerShellScript \
  --parameters commands='["& \"C:\\Program Files\\Git\\bin\\bash.exe\" -lc \"cd /c/cl-lab && ./run-cli-api-smoke.sh\"; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }"]'
```

The smoke script:

1. Loads `.env` if present.
2. Installs from `https://download.crystallattice.dev/crystal-lattice-cli/install.sh`.
3. Uses workspace-local `.install/` paths on Linux/macOS and short `.i/` plus
   `.b/` paths on Windows.
4. Starts `crystal-lattice --server --config-local`.
5. Sends a real HTTP API request.
6. Asks the model to use tools to read `./tool-target.txt`.
7. Verifies user, tool, and assistant messages plus the file marker.

Logs are written under:

```text
logs/
```

## Outputs

Print lab connection details:

```bash
deploy/aws-cli-install-lab/outputs.sh \
  --stack-name crystal-lattice-cli-install-lab \
  --region us-east-1
```

## Down

Delete the lab:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-install-lab/down.sh \
  --stack-name crystal-lattice-cli-install-lab \
  --region us-east-1
```

## Equivalent Real-Device Testing

Use the same smoke script on real Linux, macOS, and Windows devices.

Linux/macOS:

```bash
mkdir -p ~/crystal-lattice-cli-manual-lab
cp deploy/aws-cli-install-lab/run-cli-api-smoke.sh ~/crystal-lattice-cli-manual-lab/
cp .env ~/crystal-lattice-cli-manual-lab/   # optional
cd ~/crystal-lattice-cli-manual-lab
./run-cli-api-smoke.sh
```

Windows:

1. Install Git for Windows.
2. Open Git Bash.
3. Copy `run-cli-api-smoke.sh` into `C:\cl-lab`.
4. Optionally copy `.env` into the same directory.
5. Run:

```bash
cd /c/cl-lab
./run-cli-api-smoke.sh
```

PowerShell direct `.zip` extraction is only a fallback path now. The primary
Windows acceptance path is Git Bash plus the public shell installer.

## Validation

Local syntax/template checks:

```bash
bash -n deploy/aws-cli-install-lab/*.sh deploy/aws-cli-install-lab/lib/*.sh
aws --region us-east-1 cloudformation validate-template \
  --template-body file://deploy/aws-cli-install-lab/lab.yaml
```
