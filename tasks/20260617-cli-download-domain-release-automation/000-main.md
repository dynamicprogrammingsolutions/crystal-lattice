# CLI Download Domain And Release Automation

Create a reproducible AWS/GitHub deployment path for Crystal Lattice CLI downloads, including test and production download domains, GitHub Actions release publishing, domain-aware installer upload, scripted release orchestration, promotion of existing GitHub release assets, documentation, and testing.

## Task checklist

- [x] `tasks/20260617-cli-download-domain-release-automation/010-design-download-hosting-and-release-boundaries.md`
- [x] `tasks/20260617-cli-download-domain-release-automation/020-add-download-domain-infra-bootstrap.md`
- [x] `tasks/20260617-cli-download-domain-release-automation/030-add-domain-aware-installer-upload.md`
- [x] `tasks/20260617-cli-download-domain-release-automation/040-add-github-oidc-role-and-vars-setup.md`
- [ ] `tasks/20260617-cli-download-domain-release-automation/050-update-release-workflow-to-use-configured-download-target.md`
  - Workflow dispatch run `27746631545` passed; tag-triggered publish still needs validation.
- [ ] `tasks/20260617-cli-download-domain-release-automation/060-add-release-orchestration-script.md`
  - Script exists; full release orchestration still needs tag/publish validation after the workflow is green.
- [ ] `tasks/20260617-cli-download-domain-release-automation/070-add-promote-existing-github-release-script.md`
  - Script exists; existing GitHub Release assets for `0.1.0` used older names, so promotion was not used for the live test.
- [x] `tasks/20260617-cli-download-domain-release-automation/080-add-smoke-tests-and-domain-cutover-docs.md`
  - Testing-domain and production-domain public installer smoke passed; production website/docs were updated and deployed.

## Goal

Move CLI binary downloads from a hardcoded S3 URL toward a reproducible custom-domain setup. The deployment should follow the style of `deploy/aws-static-sites/`: scripts under `deploy/`, CloudFormation where appropriate, a README with ready-to-use commands, GitHub OIDC setup helpers, GitHub repository variable/secret helpers, and explicit test/prod profile guidance.

The GitHub Actions release matrix remains the source of official platform artifacts. Local scripts must not pretend to build all platform artifacts locally. Local scripts should provision download infrastructure, upload/generate the installer, configure GitHub, trigger/watch releases, publish existing artifacts, promote GitHub releases, and smoke-test the public download URL.

## Domains And Profiles

Use a configurable download domain. Both test and production download hosts should use the singular `download.` prefix.

Initial testing target:

```text
download.crystallattice.dev.dynamicprogrammingsolutions.com
```

Production target:

```text
download.crystallattice.dev
```

## Target Directory

Create:

```text
deploy/aws-cli-downloads/
```

Expected files:

```text
deploy/aws-cli-downloads/README.md
deploy/aws-cli-downloads/lib/common.sh
deploy/aws-cli-downloads/downloads.yaml
deploy/aws-cli-downloads/github-oidc-role.yaml
deploy/aws-cli-downloads/up.sh
deploy/aws-cli-downloads/down.sh
deploy/aws-cli-downloads/outputs.sh
deploy/aws-cli-downloads/upload-installer.sh
deploy/aws-cli-downloads/publish-assets.sh
deploy/aws-cli-downloads/promote-github-release.sh
deploy/aws-cli-downloads/release.sh
deploy/aws-cli-downloads/smoke.sh
deploy/aws-cli-downloads/configure-github-actions-vars.sh
deploy/aws-cli-downloads/create-github-oidc-role.sh
```

## Existing References

Use these as implementation references:

- `deploy/aws-static-sites/README.md`
- `deploy/aws-static-sites/lib/common.sh`
- `deploy/aws-static-sites/static-sites.yaml`
- `deploy/aws-static-sites/up.sh`
- `deploy/aws-static-sites/down.sh`
- `deploy/aws-static-sites/outputs.sh`
- `deploy/aws-static-sites/create-github-oidc-role.sh`
- `deploy/aws-static-sites/configure-github-actions-vars.sh`
- `.github/workflows/release-crystal-lattice-cli.yml`
- `scripts/install.sh`
- `scripts/publish_crystal_lattice_s3.py`

## Main Acceptance Criteria

- Test download infrastructure can be created via script against the testing domain/profile.
- Production download infrastructure can be created via script against the production domain/profile.
- `up.sh` provisions/updates infrastructure and bootstraps the installer; it does not build platform archives.
- `upload-installer.sh` uploads a domain-correct `install.sh`.
- GitHub OIDC role can publish only the intended download bucket/prefix and invalidate only the intended CloudFront distribution.
- GitHub repository variables/secrets can be configured via script.
- Release workflow no longer hardcodes the old S3 bucket/domain.
- Release workflow still uses the GitHub matrix to build platform artifacts.
- `release.sh` can create/push a tag, watch GitHub Actions, and smoke-test the resulting download endpoint.
- `promote-github-release.sh` can copy existing GitHub Release assets to test or prod without rebuilding.
- Testing is documented and run on the testing domain first.
- README explains how to switch from the testing domain/profile to production.
- A separate `main` git worktree exists for testing GitHub workflows from `main`.

## Worktree For Workflow Testing

The user requested a separate worktree using `main` so GitHub workflow changes can be tested from a main-branch checkout. Record the created worktree path in completion notes when the task is executed.

## Execution plan

Added during completion.

Implementation will happen in the `main` worktree at:

```text
/Users/ferenci84/Dev/Mine/ai-agent-platform-main
```

The task/status notes remain in this task directory in the original checkout.

Execution approach:

1. Build a new `deploy/aws-cli-downloads/` package mirroring `deploy/aws-static-sites/` patterns.
2. Add CloudFormation for private S3 + CloudFront OAC + ACM + Route 53 aliases for the configured download domain.
3. Add shell wrappers for `up`, `down`, `outputs`, domain-aware installer upload, asset publishing, GitHub release promotion, release orchestration, smoke testing, GitHub OIDC role creation, and GitHub variable/secret setup.
4. Update `.github/workflows/release-crystal-lattice-cli.yml` so the GitHub matrix remains the only official platform build path, while publishing uses repository variables/secrets instead of hardcoded S3 values.
5. Add `deploy/aws-cli-downloads/README.md` with test/prod profile commands, GitHub setup, release/promotion flow, smoke testing, and domain cutover guidance.
6. Run local static validation: shell syntax checks, CloudFormation template validation if AWS CLI is available/credentials permit, workflow syntax if `actionlint` is available, and script `--help` smoke checks.
7. Update checklists/completion notes with what was implemented and any testing that could not be run locally.

## Completion Notes

Added during completion.

Implemented locally in both the original checkout and the `main` worktree:

```text
/Users/ferenci84/Dev/Mine/ai-agent-platform-main
```

Added `deploy/aws-cli-downloads/` with:

- CloudFormation for private S3 + CloudFront OAC + ACM + Route 53 download hosting.
- Shared shell helpers with `test` and `prod` profile defaults.
- `up.sh`, `down.sh`, `outputs.sh`.
- `upload-installer.sh` for domain-aware installer generation/upload.
- `publish-assets.sh` for publishing already-built release archives.
- `create-github-oidc-role.sh` and `configure-github-actions-vars.sh`.
- `promote-github-release.sh`.
- `release.sh`.
- `smoke.sh`.
- `README.md` with testing domain, production domain, GitHub setup, release, promotion, smoke, teardown, and cutover guidance.

Updated `.github/workflows/release-crystal-lattice-cli.yml` so the GitHub matrix build remains unchanged, but the download publishing step now uses:

```text
vars.AWS_REGION
vars.CLI_DOWNLOADS_BUCKET
vars.CLI_DOWNLOADS_PREFIX
vars.CLI_DOWNLOADS_BASE_URL
vars.CLI_DOWNLOADS_CLOUDFRONT_DISTRIBUTION_ID
secrets.CLI_DOWNLOADS_AWS_ROLE_TO_ASSUME
```

Local verification performed in both checkouts where applicable:

```bash
for f in deploy/aws-cli-downloads/*.sh deploy/aws-cli-downloads/lib/common.sh; do bash -n "$f" || exit 1; done
for f in deploy/aws-cli-downloads/*.sh; do "$f" --help >/dev/null || exit 1; done
deploy/aws-cli-downloads/upload-installer.sh --base-url https://download.crystallattice.dev.dynamicprogrammingsolutions.com/crystal-lattice-cli --print | grep -q 'DEFAULT_DOWNLOAD_BASE_URL="https://download.crystallattice.dev.dynamicprogrammingsolutions.com/crystal-lattice-cli"'
actionlint .github/workflows/release-crystal-lattice-cli.yml
aws --region us-east-1 cloudformation validate-template --template-body file://deploy/aws-cli-downloads/downloads.yaml
aws --region us-east-1 cloudformation validate-template --template-body file://deploy/aws-cli-downloads/github-oidc-role.yaml
```

Also ran a dry-run publish using temporary fake assets to verify the upload commands generated by `publish-assets.sh`.

Confirmed the testing hosted zone exists:

```text
/hostedzone/ZEJFIL16PTJ4 dynamicprogrammingsolutions.com.
```

Status update added during completion on 2026-06-18:

Implemented and pushed the deploy/release automation to `main` from:

```text
/Users/ferenci84/Dev/Mine/ai-agent-platform-main
```

Latest pushed commit at the time of this update:

```text
ae4405fe Detect Windows venv Python in runtime smoke test
```

Live testing resources created for the testing domain:

```text
AWS profile used during setup: default
region: us-east-1
stack: crystal-lattice-cli-downloads-test
hosted zone: dynamicprogrammingsolutions.com
download domain: download.crystallattice.dev.dynamicprogrammingsolutions.com
bucket: crystal-lattice-cli-downloads-test-874087778966
prefix: crystal-lattice-cli
CloudFront distribution: E2SBEYDBKC4Y7A
base URL: https://download.crystallattice.dev.dynamicprogrammingsolutions.com/crystal-lattice-cli
```

GitHub OIDC was configured for:

```text
repo: dynamicprogrammingsolutions/crystal-lattice
role: arn:aws:iam::874087778966:role/CrystalLatticeCliDownloadsGitHubDeployRoleTest
allowed refs: refs/heads/main and refs/tags/crystal-lattice-cli-v*
```

GitHub repository variables/secrets were configured for the testing download stack:

```text
vars.AWS_REGION
vars.CLI_DOWNLOADS_BUCKET
vars.CLI_DOWNLOADS_PREFIX
vars.CLI_DOWNLOADS_BASE_URL
vars.CLI_DOWNLOADS_CLOUDFRONT_DISTRIBUTION_ID
secrets.CLI_DOWNLOADS_AWS_ROLE_TO_ASSUME
```

GitHub Actions verification:

- `release-crystal-lattice-cli.yml` workflow dispatch on `main` passed in run `27725996534`.
- The workflow test job passed.
- All matrix build jobs passed: `linux-amd64`, `darwin-amd64`, `darwin-arm64`, `windows-amd64`.
- Per-archive workflow smoke tests passed.
- Publish jobs were skipped because this was `workflow_dispatch`, not a release tag.

Published the artifacts from run `27725996534` to the testing domain with `publish-assets.sh`.
Verified:

```text
https://download.crystallattice.dev.dynamicprogrammingsolutions.com/crystal-lattice-cli/install.sh -> HTTP 200
https://download.crystallattice.dev.dynamicprogrammingsolutions.com/crystal-lattice-cli/latest.txt -> crystal-lattice-cli-v0.1.0
all four archive URLs under the same prefix -> HTTP 200
```

Release-blocking issue found during live installer smoke:

```text
deploy/aws-cli-downloads/smoke.sh \
  --base-url https://download.crystallattice.dev.dynamicprogrammingsolutions.com/crystal-lattice-cli \
  --version 0.1.0
```

The script passed URL/archive checks but failed after installing the `darwin-arm64` archive into a temp directory. The packaged Python executable aborted with:

```text
Library not loaded: /Library/Frameworks/Python.framework/Versions/3.11/Python
Referenced from: .../python/bin/python
Reason: tried: '/Library/Frameworks/Python.framework/Versions/3.11/Python' ... no such file
```

Local investigation showed the same class of issue with local pyenv builds: packaged venv Python executables can retain absolute host-library references such as:

```text
/Users/ferenci84/.pyenv/versions/3.11.12/lib/libpython3.11.dylib
/opt/homebrew/opt/gettext/lib/libintl.8.dylib
```

Remaining work:

1. Fix the Windows launcher/runtime path issue exposed by workflow run `27745015177`.
2. Re-run the GitHub workflow on `main` after the Windows fix.
3. Publish the rebuilt artifacts from a green workflow run to the `download.` testing domain.
4. Run `deploy/aws-cli-downloads/smoke.sh --base-url https://download.crystallattice.dev.dynamicprogrammingsolutions.com/crystal-lattice-cli --version 0.1.0`.
5. Run the tag-triggered publish path to verify GitHub OIDC publishing to the testing bucket/domain.
6. Only after testing-domain install smoke passes, cut over GitHub variables/secrets to production and promote/release to `download.crystallattice.dev`.

Important decisions made during implementation:

- The script defaults use `download.crystallattice.dev` as the production download domain, while the test domain is `download.crystallattice.dev.dynamicprogrammingsolutions.com`.
- `up.sh` provisions infrastructure and uploads/updates the domain-aware `install.sh`; it intentionally does not build the platform archives.
- Official platform archives remain GitHub matrix artifacts.
- Existing GitHub Release `crystal-lattice-cli-v0.1.0` was not promoted because its asset names use the older `crystal-lattice-cli-v0.1.0-*` pattern; the current installer expects `crystal-lattice-python-runtime-v0.1.0-*`.
- I pushed changes directly to `main` because the user explicitly allowed pushing `main` when needed for workflow testing.

Additional status update added during completion on 2026-06-18:

- The user clarified that both testing and production download domains should use singular `download.`.
- Updated and pushed script defaults/docs in `96820fe3 Use download subdomains for CLI downloads`.
- Updated the live testing stack, installer, and GitHub Actions variables to `https://download.crystallattice.dev.dynamicprogrammingsolutions.com/crystal-lattice-cli`.
- Pushed `22f647f9 Use managed Python runtime for CLI release archives`.
- Locally verified the macOS runtime portability fix with a uv-managed Python runtime and archive smoke test.
- Workflow dispatch run `27745015177` passed test, Linux, `darwin-amd64`, and `darwin-arm64`, but failed `windows-amd64` archive smoke. The failure was:

  ```text
  '"...\python\Scripts\python.exe"' is not recognized as an internal or external command
  ```

- Copied these task files into the `main` worktree and cleaned duplicate CLI-release changes out of the original `develop` worktree. The original worktree still has unrelated staged doc edits in `deploy/aws-static-sites/README.md` and `docs/reference/providers/openai_provider.md`, which were left untouched.

Final status update added during completion on 2026-06-18:

- Pushed `543dc933 Use actual packaged Python path in Windows runtime launcher`.
- Workflow dispatch run `27746631545` on `main` passed:
  - test job
  - `linux-amd64`
  - `darwin-amd64`
  - `darwin-arm64`
  - `windows-amd64`
- Published artifacts from run `27746631545` to the testing download domain.
- Public testing-domain smoke passed:

  ```bash
  deploy/aws-cli-downloads/smoke.sh \
    --base-url https://download.crystallattice.dev.dynamicprogrammingsolutions.com/crystal-lattice-cli \
    --version 0.1.0
  ```

Remaining work after this update:

1. Run a tag-triggered release to verify GitHub Release publication and the `publish-downloads` job through OIDC.
2. Decide whether to tag a follow-up release now that source defaults and website commands point at production.

Production cutover update added during completion on 2026-06-18:

- Created/updated production download infrastructure for `https://download.crystallattice.dev/crystal-lattice-cli`.
- Created/updated production GitHub OIDC role:

  ```text
  arn:aws:iam::874087778966:role/CrystalLatticeCliDownloadsGitHubDeployRoleProd
  ```

- Configured GitHub Actions variables/secrets for production downloads.
- Tried the documented `promote-github-release.sh --profile prod --version 0.1.0` path. It failed with:

  ```text
  no assets match the file pattern
  ```

  The existing `0.1.0` GitHub Release used older asset names, so the README was corrected to document `publish-assets.sh` for validated workflow artifacts.
- Published the already-validated artifacts from workflow run `27746631545` to production with `publish-assets.sh`.
- Ran and passed:

  ```bash
  deploy/aws-cli-downloads/smoke.sh --profile prod
  ```

- Updated and deployed the production landing website install command to:

  ```bash
  curl -fsSL https://download.crystallattice.dev/crystal-lattice-cli/install.sh | bash
  ```

Git Bash installer update added during completion on 2026-06-18:

- Extended `scripts/install.sh` so Git Bash/MSYS/Cygwin on Windows detects `windows-amd64`, downloads the `.zip` runtime archive, and writes a Bash shim that calls `Scripts/crystal-lattice.cmd`.
- Uploaded the updated generated installer to both the testing and production download domains.
- Added focused installer tests for Linux tarball installs, Windows Git Bash zip installs, and unsupported Windows architectures.
- Production endpoint smoke with `--skip-install` passed after upload.
