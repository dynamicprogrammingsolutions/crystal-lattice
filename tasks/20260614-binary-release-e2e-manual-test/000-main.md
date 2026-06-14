# Binary Release End-To-End Manual Test

Create and run a full manual validation plan for the Crystal Lattice CLI binary release path, including release artifacts, installer UX, fresh checkout workflows, real LLM/tool execution, plugin behavior, and a temporary custom download domain.

## Task checklist

- [ ] `tasks/20260614-binary-release-e2e-manual-test/010-define-manual-test-matrix.md`
- [ ] `tasks/20260614-binary-release-e2e-manual-test/020-prepare-manual-test-commands.md`
- [ ] `tasks/20260614-binary-release-e2e-manual-test/030-set-up-temporary-download-domain.md`
- [ ] `tasks/20260614-binary-release-e2e-manual-test/040-validate-fresh-checkout-dev-prod-installs.md`
- [ ] `tasks/20260614-binary-release-e2e-manual-test/050-test-release-artifacts-on-all-platforms.md`
- [ ] `tasks/20260614-binary-release-e2e-manual-test/060-test-real-llm-tools-and-plugins.md`
- [ ] `tasks/20260614-binary-release-e2e-manual-test/070-document-dev-ux-and-readme-improvements.md`

## Goal

Validate the binary CLI release process end to end from a maintainer and end-user perspective. The work should prove that GitHub Actions-built bundles can be downloaded, installed, configured, and used across supported platforms, and that the developer-facing workflow is pleasant enough to repeat.

## Overall Acceptance Criteria

- GitHub Actions-built binary artifacts are manually tested on:
  - Linux amd64
  - macOS amd64 / Intel
  - macOS arm64 / Apple Silicon
  - Windows amd64 archive flow
- Bash installer flow works on macOS and Linux.
- Windows archive flow works for the `.zip` asset.
- Default config installation/initialization works from the binary install.
- One real provider API key is configured.
- One real LLM request succeeds.
- At least one real tool call is observed.
- At least one custom user-side plugin, not part of bundled plugins, is installed/enabled and exercised.
- At least one bundled plugin that is not in the default config closure is installed/enabled and exercised.
- Fresh checkout dev install is tested.
- Fresh checkout prod/binary install rehearsal is tested.
- Temporary custom download domain works under `dynamicprogrammingsolutions.com`, preferably:
  - `downloads.crystallattice.dev.dynamicprogrammingsolutions.com`
- Small README/doc improvements are made where they reduce friction for the workflow being tested.

## Current Implementation Notes

The official CLI release workflow is tag-driven:

- `.github/workflows/release-crystal-lattice-cli.yml`
- It triggers for tags matching `crystal-lattice-cli-v*`.
- It validates that the tag matches `application/python/pyproject.toml` `project.version`.
- It builds bundled-Python runtime archives for:
  - `linux-amd64`
  - `darwin-amd64`
  - `darwin-arm64`
  - `windows-amd64`
- It smoke-tests each archive.
- It publishes a GitHub Release.
- It publishes public downloads to S3 after the GitHub Release succeeds.

Important references:

- Release workflow: `.github/workflows/release-crystal-lattice-cli.yml`
- Bundled-Python archive builder: `scripts/build_crystal_lattice_python_runtime_package.py`
- Installer script: `scripts/install.sh`
- S3 publisher: `scripts/publish_crystal_lattice_s3.py`
- Local archive installer: `scripts/install_crystal_lattice_archive.py`
- Runtime archive smoke test: `scripts/smoke_test_crystal_lattice_python_runtime_archive.py`
- Current release docs: `application/python/README.md`, section `Release And Distribution`

The current public install command is:

```bash
curl -fsSL https://crystal-lattice-downloads-874087778966.s3.us-east-1.amazonaws.com/crystal-lattice-cli/install.sh | bash
```

The installer uses `DEFAULT_DOWNLOAD_BASE_URL` from `scripts/install.sh`, unless overridden with:

```bash
CRYSTAL_LATTICE_DOWNLOAD_BASE_URL="https://example.com/crystal-lattice-cli"
```

The same URL base must contain:

- `install.sh`
- `latest.txt`
- release archives named like `crystal-lattice-python-runtime-v<version>-<target>.tar.gz`
- the Windows `.zip` archive

## Suggested Execution Order

1. Define the exact manual test matrix.
2. Prepare friendly command blocks and evidence templates.
3. Set up the temporary download domain.
4. Validate fresh checkout dev/prod workflows.
5. Test release artifacts on all platforms.
6. Test real LLM/tool/plugin behavior.
7. Apply docs and README improvements from the observed UX.
