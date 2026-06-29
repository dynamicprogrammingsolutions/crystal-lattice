# Add Smoke Tests And Domain Cutover Docs

Add a smoke-test script and final documentation that explains test-domain validation, production cutover, installer default updates, README updates, and rollback.

## Requirements checklist

- [x] Add `deploy/aws-cli-downloads/smoke.sh`.
- [x] Smoke-test `install.sh`, `latest.txt`, expected archive URLs, and content types.
- [x] On macOS/Linux, optionally run the current-platform installer into isolated paths.
- [x] Verify installed command reports `python-runtime` when an installer run is possible.
- [x] Document full test-domain validation.
- [x] Document production cutover from testing domain to production domain.
- [x] Document how and when to update `scripts/install.sh` default URL.
- [x] Update root/application README install commands if production domain becomes canonical.
- [x] Document rollback/promotion of previous release.
- [x] Run smoke tests against the testing domain.
- [x] Run final docs checks.

Parent Task: `tasks/20260617-cli-download-domain-release-automation/000-main.md`

Depends On:

- `tasks/20260617-cli-download-domain-release-automation/020-add-download-domain-infra-bootstrap.md`
- `tasks/20260617-cli-download-domain-release-automation/030-add-domain-aware-installer-upload.md`
- `tasks/20260617-cli-download-domain-release-automation/050-update-release-workflow-to-use-configured-download-target.md`
- `tasks/20260617-cli-download-domain-release-automation/070-add-promote-existing-github-release-script.md`

## Smoke Script

Expected usage:

```bash
deploy/aws-cli-downloads/smoke.sh --profile test
```

or:

```bash
deploy/aws-cli-downloads/smoke.sh \
  --base-url https://download.crystallattice.dev.dynamicprogrammingsolutions.com/crystal-lattice-cli \
  --version 0.2.0
```

The script should verify:

- `install.sh` returns HTTP 200
- `latest.txt` returns `crystal-lattice-cli-v<version>`
- all expected archives return HTTP 200
- content types are reasonable
- generated installer contains the selected base URL
- on supported current platform, installer can install to temp `INSTALL_ROOT` and `BIN_DIR`
- installed command runs:

  ```bash
  crystal-lattice --help
  crystal-lattice --runtime-layout-json
  ```

For unsupported current platforms, URL/content checks are enough.

## Cutover Documentation

README must include a step-by-step cutover:

1. Deploy/update testing download stack.
2. Configure GitHub variables/secrets for testing.
3. Run/promote release to testing.
4. Run `smoke.sh --profile test`.
5. Deploy/update production download stack.
6. Configure GitHub variables/secrets for production.
7. Promote same GitHub Release to production, or publish validated workflow artifacts if the existing GitHub Release asset names do not match the current archive names.
8. Run `smoke.sh --profile prod`.
9. Update `scripts/install.sh` default base URL if production is now canonical.
10. Update README install commands.
11. Use a follow-up release so the published installer default is canonical.

## Documentation Requirements

Update:

- `deploy/aws-cli-downloads/README.md`
- `README.md` if the public install command changes
- `application/python/README.md` if release/install docs change

Include:

- testing domain examples
- production domain examples
- pinned install example
- custom base URL override example
- rollback/promote previous version example
- warning that local scripts do not build all matrix artifacts

## Testing Requirements

Run against testing domain:

```bash
deploy/aws-cli-downloads/smoke.sh --profile test
```

Also run:

```bash
rg -n "crystal-lattice-downloads|install.sh|CRYSTAL_LATTICE_DOWNLOAD_BASE_URL|downloads\\.crystallattice|crystallattice\\.dev" \
  README.md application/python/README.md deploy/aws-cli-downloads
```

Verify docs do not still instruct users to use the old S3 URL once production cutover is complete. During testing, docs may mention the old URL only as legacy/background.

## Completion Notes

Added during completion on 2026-06-18.

The testing domain served `install.sh`, `latest.txt`, and all four expected archive URLs. The current-platform install portion of `smoke.sh` originally failed on macOS after install because the packaged Python runtime was linked to a host Python framework path. A local uv-managed runtime archive smoke now passes for macOS, but do not mark this smoke task complete until rebuilt artifacts from a green GitHub workflow pass:

```bash
deploy/aws-cli-downloads/smoke.sh \
  --base-url https://download.crystallattice.dev.dynamicprogrammingsolutions.com/crystal-lattice-cli \
  --version 0.1.0
```

Final update added during completion on 2026-06-18:

After workflow run `27746631545` passed and its artifacts were published to the testing domain, the public smoke command above passed. It verified `install.sh`, `latest.txt`, all expected archive URLs, a temp-path install on macOS arm64, `--help`, and `--runtime-layout-json`.

Production cutover update added during completion on 2026-06-18:

- Updated `README.md`, `application/python/README.md`, `scripts/install.sh`, and `landing_page/src/content/pages/home.yaml` to use `https://download.crystallattice.dev/crystal-lattice-cli`.
- Updated `deploy/aws-cli-downloads/README.md` because `promote-github-release.sh` cannot promote the old `0.1.0` GitHub Release assets; use `publish-assets.sh` for validated workflow-dispatch artifacts in that case.
- Built and synced the production landing/docs static site.
- Verified the live website contains:

  ```bash
  curl -fsSL https://download.crystallattice.dev/crystal-lattice-cli/install.sh | bash
  ```

- Production `smoke.sh --profile prod` passed.

Git Bash installer update added during completion on 2026-06-18:

- The shell installer now supports Git Bash/MSYS/Cygwin on Windows by downloading `crystal-lattice-python-runtime-v<version>-windows-amd64.zip`.
- The installer writes the normal `$BIN_DIR/crystal-lattice` shim, which invokes the bundled `Scripts/crystal-lattice.cmd` launcher.
- `deploy/aws-cli-downloads/smoke.sh` now runs the installer path on Git Bash/MSYS/Cygwin instead of skipping Windows.
- The updated installer was uploaded to both public download domains and verified on production with:

  ```bash
  deploy/aws-cli-downloads/smoke.sh --profile prod --skip-install
  ```

If README command examples are executable in the current environment, run the testing-domain variants with temp install paths.
