# Add Promote Existing GitHub Release Script

Add a script that promotes already-built GitHub Release assets to the selected test or production download domain without rebuilding platform artifacts.

## Requirements checklist

- [x] Add `deploy/aws-cli-downloads/promote-github-release.sh`.
- [x] Download release assets from GitHub for a given version/tag.
- [x] Validate all four expected release archives are present.
- [x] Generate/upload a domain-correct `install.sh`.
- [x] Upload release archives to the selected bucket/prefix.
- [x] Write/upload `latest.txt`.
- [x] Invalidate CloudFront.
- [x] Reuse or call `publish-assets.sh` for local asset upload.
- [x] Document promotion flow in the README.
- [x] Test promotion against the testing domain.
- [x] Document production promotion from test-validated artifacts.

Parent Task: `tasks/20260617-cli-download-domain-release-automation/000-main.md`

Depends On:

- `tasks/20260617-cli-download-domain-release-automation/030-add-domain-aware-installer-upload.md`
- `tasks/20260617-cli-download-domain-release-automation/040-add-github-oidc-role-and-vars-setup.md`

## Purpose

This script supports switching from the testing download domain to the production download domain without asking developers to rebuild platform artifacts locally.

The source of truth is a completed GitHub Release such as:

```text
crystal-lattice-cli-v0.2.0
```

The script should fetch those release assets, validate them, upload them to the selected download stack, generate the correct installer for that domain, update `latest.txt`, and smoke-test or print the smoke command.

## Expected Commands

Promote to testing domain:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/promote-github-release.sh \
  --profile test \
  --version 0.2.0 \
  --repo dynamicprogrammingsolutions/crystal-lattice
```

Promote the same release to production:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/promote-github-release.sh \
  --profile prod \
  --version 0.2.0 \
  --repo dynamicprogrammingsolutions/crystal-lattice
```

The script should support a `--dry-run` mode that prints `gh` and `aws` commands without mutating AWS.

## Local Asset Publish Helper

If adding `publish-assets.sh`, it should accept:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/publish-assets.sh \
  --profile test \
  --assets-dir /path/to/release-assets \
  --version 0.2.0
```

This helper should validate artifact names and upload:

```text
install.sh
latest.txt
crystal-lattice-python-runtime-v<version>-linux-amd64.tar.gz
crystal-lattice-python-runtime-v<version>-darwin-amd64.tar.gz
crystal-lattice-python-runtime-v<version>-darwin-arm64.tar.gz
crystal-lattice-python-runtime-v<version>-windows-amd64.zip
```

## Documentation Requirements

README must include:

- when to use promotion instead of a new release
- how to promote a GitHub Release to the testing domain
- how to promote the same release to production
- how to inspect downloaded assets
- how to avoid accidentally changing `latest.txt`
- rollback options, such as promoting the previous version

## Testing Requirements

Against the testing domain:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/promote-github-release.sh \
  --profile test \
  --version <existing-version> \
  --dry-run
```

Then, when approved:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/promote-github-release.sh \
  --profile test \
  --version <existing-version>
```

Verify:

- all expected assets were downloaded from GitHub
- all expected assets were uploaded to the testing bucket/prefix
- `latest.txt` contains the expected tag
- generated installer points at the testing domain
- CloudFront invalidation was created
- `smoke.sh` passes on the testing domain

## Execution plan

Status: Approved

Finish and validate promotion after subtask 050 creates a new GitHub Release
with the current `crystal-lattice-python-runtime-v<version>-...` asset names.
The existing `0.1.0` release cannot satisfy this test because its assets use
the legacy naming scheme.

Correct dry-run behavior first. The current implementation prints the
`gh release download` command, leaves the assets directory empty, then invokes
`publish-assets.sh --dry-run`, which fails while validating missing files.
Change dry-run so it prints the intended GitHub download and publish commands
without requiring files that were deliberately not downloaded. Preserve full
asset validation for every real promotion.

Add focused tests for:

- dry-run exits successfully and prints the normalized tag, asset pattern,
  selected profile, stack, version, and publish command
- dry-run does not call AWS or modify `latest.txt`
- real-mode preparation rejects missing archives
- release download failure propagates
- all four current asset names are required
- `--keep-assets-dir` preserves downloaded files for inspection
- test and production profiles resolve to their respective domain/stack

After the new tag-triggered release has published to the testing domain:

1. Run a promotion dry run against testing.
2. Run a real, idempotent promotion of the same GitHub Release back to testing
   with `--keep-assets-dir`.
3. Inspect the downloaded directory and verify exactly the four expected
   runtime archives.
4. Verify testing `install.sh`, `latest.txt`, archive URLs, content types, and
   CloudFront invalidation.
5. Run `smoke.sh --profile test --version <version>`.

Then promote the exact same GitHub Release to production:

1. Confirm GitHub repository variables have been restored to production so
   future tag releases use the canonical target.
2. Run a production promotion dry run and review the bucket/domain/version.
3. Run the real production promotion with explicit version and repository.
4. Verify production `latest.txt`, installer default, all four archives, and
   CloudFront invalidation.
5. Run `smoke.sh --profile prod --version <version>`.
6. Verify the public website installer still resolves through the production
   domain.

The testing and production publishes must use byte-identical GitHub Release
assets. Record hashes from the kept asset directory and compare them with the
objects downloaded through both domains.

### Implementation decisions and open questions

- Requirement question: promotion depends on the approved new release version
  from subtask 050; recommendation remains `0.1.1`.
- Implementation decision: validate promotion with the new release rather than
  adding compatibility for the legacy `0.1.0` asset names. Legacy compatibility
  is not required to prove the current release path.
- Implementation decision: make dry-run non-mutating and successful without
  downloading assets; real mode remains responsible for complete asset
  validation.
- Implementation decision: perform an idempotent real promotion to testing
  before production so the script itself, not only `publish-assets.sh`, is
  validated against the testing domain.

### Documentation

- Correct the README's dry-run description and include the test→production
  promotion sequence.
- Document that legacy `0.1.0` cannot be promoted with the current filename
  contract.
- Record kept asset hashes, testing and production smoke results, invalidation
  evidence, and final `latest.txt` values in this task.

### Task checklist

- [x] Fix promotion dry-run so it succeeds without downloaded assets.
- [x] Add focused promotion-script tests.
- [x] Run local syntax/lint/tests.
- [x] Run successful testing-profile promotion dry run.
- [x] Run idempotent real promotion to testing and inspect kept assets.
- [x] Run testing-domain smoke verification.
- [x] Restore/confirm production GitHub repository configuration.
- [x] Run production-profile promotion dry run.
- [x] Promote the same GitHub Release to production.
- [x] Run production-domain smoke verification.
- [x] Compare GitHub/test/prod asset hashes.
- [x] Record evidence and mark this subtask complete.

### Requirement verification

- GitHub release download: kept asset directory and `gh release view` evidence.
- Four-archive validation: exact filename inventory and successful real
  promotion.
- Domain-correct installer/latest/archive upload: content inspection through
  both public domains.
- CloudFront invalidation: recorded invalidation IDs for test and production.
- Dry-run behavior: successful non-mutating focused test and command output.
- Testing-domain promotion: real promotion plus `smoke.sh --profile test`.
- Production promotion: real promotion plus `smoke.sh --profile prod`.

### Additional implementation verification

- Compare SHA-256 hashes for all four archives across the kept GitHub assets,
  testing domain, and production domain.
- Verify `latest.txt` changes only after reviewed real promotion commands.
- Verify no legacy `crystal-lattice-cli-v0.1.0-*` asset is accepted as a
  substitute for the current runtime archive contract.

## Implementation Notes

- 2026-08-23: Execution approved with release version `0.1.1`; implementation
  started after the release workflow/orchestration fixes.
- 2026-08-23: Promotion dry-run now prints the GitHub download and real publish
  commands without validating an intentionally empty asset directory.
- 2026-08-23: Focused dry-run coverage passed as part of the nine release and
  promotion script tests.
- 2026-08-23: Testing and production dry runs passed. Real promotion downloaded
  exactly four current `0.1.1` assets and published them first to testing, then
  production.
- 2026-08-23: Full installer smoke passed on both domains. Testing invalidation
  `IA4YQSLTQOKLY6EB13ZF2ZK5WV` and production invalidation
  `I8UEXRNLJ7325HCQFQOBT9241E` completed for the promotion publishes.
- 2026-08-23: SHA-256 values matched across separate GitHub Release downloads,
  testing S3 downloads, and production S3 downloads:

  ```text
  7077dd445e4ba5811f01b3a15c5faa87d8111c5a4d11bc6e9ea24f9cc7e1a682  darwin-amd64
  8c468f40e6bd3b6701d65a3da9fb9dc68176f5bdb804b61b014deb5cedbbf206  darwin-arm64
  052f0bc91763dbe0c1524dca72b3fdce39ba50f02d48788869948c5d81547f88  linux-amd64
  2b1f59d7b9eed2354e880bf48c17299885562c3a8c2cbcf6b82f0fc7a6b83c2f  windows-amd64
  ```

## Completion Notes

Added during completion on 2026-06-18.

The promotion script exists, but it was not used for the live testing-domain publish because the existing `crystal-lattice-cli-v0.1.0` GitHub Release assets use older asset names. The current installer and `publish-assets.sh` expect `crystal-lattice-python-runtime-v0.1.0-*` archive names.

Production update added during completion on 2026-06-18.

The documented production promotion command was run:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-cli-downloads/promote-github-release.sh \
  --profile prod \
  --version 0.1.0 \
  --repo dynamicprogrammingsolutions/crystal-lattice
```

It failed before mutating AWS with:

```text
no assets match the file pattern
```

The production endpoint was populated with the validated workflow-dispatch artifacts via `publish-assets.sh` instead. The README now documents this fallback for old releases whose GitHub Release asset names do not match the current runtime archive names.

Completion update added on 2026-08-23:

- `promote-github-release.sh --dry-run` now succeeds without requiring files
  that were intentionally not downloaded.
- The `0.1.1` GitHub Release was promoted idempotently to testing and then to
  production.
- `latest.txt`, domain-specific installers, all four archive URLs, CloudFront
  invalidations, and full current-platform installer smoke were verified on
  both domains.
- Production GitHub variables/secrets were restored before production
  promotion and remain the canonical configuration for future tag releases.
