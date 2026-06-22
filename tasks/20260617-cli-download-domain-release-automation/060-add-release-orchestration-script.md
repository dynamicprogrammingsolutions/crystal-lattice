# Add Release Orchestration Script

Add a maintainer-facing script that validates release state, creates/pushes the release tag, watches GitHub Actions, and smoke-tests the configured download endpoint after the GitHub matrix publishes artifacts.

## Requirements checklist

- [x] Add `deploy/aws-cli-downloads/release.sh`.
- [x] Validate requested version against `application/python/pyproject.toml`.
- [x] Validate release tag name `crystal-lattice-cli-v<version>`.
- [x] Check git status unless explicitly bypassed.
- [x] Optionally run local fast tests or document why skipped.
- [x] Create and push the release tag only when explicitly requested.
- [x] Watch/report the GitHub Actions release workflow run.
- [x] Report GitHub Release URL when available.
- [x] Run or print `smoke.sh` command for the configured download profile.
- [x] Document release orchestration in the README.
- [ ] Test in no-op/dry-run mode.
- [ ] Test against the testing profile before any production use.

Parent Task: `tasks/20260617-cli-download-domain-release-automation/000-main.md`

Depends On:

- `tasks/20260617-cli-download-domain-release-automation/040-add-github-oidc-role-and-vars-setup.md`
- `tasks/20260617-cli-download-domain-release-automation/050-update-release-workflow-to-use-configured-download-target.md`

## Boundary

`release.sh` orchestrates GitHub. It does not locally build all platform artifacts.

It may:

- validate the local version
- validate the tag does not already exist, unless explicitly allowed
- create and push a tag
- call `gh run list/view/watch`
- call `smoke.sh`

It must not:

- claim to produce official platform release archives locally
- bypass the GitHub matrix build
- upload partial local platform artifacts as an official release unless explicitly using `publish-assets.sh`

## Expected Commands

Dry run:

```bash
deploy/aws-cli-downloads/release.sh \
  --profile test \
  --version 0.2.0 \
  --dry-run
```

Create/push tag and watch:

```bash
deploy/aws-cli-downloads/release.sh \
  --profile test \
  --version 0.2.0 \
  --push-tag \
  --watch
```

Production later:

```bash
deploy/aws-cli-downloads/release.sh \
  --profile prod \
  --version 0.2.0 \
  --push-tag \
  --watch
```

## Documentation Requirements

README must explain:

- prerequisites
- version/tag validation
- dry-run mode
- what `--push-tag` does
- how to watch workflow logs
- how to recover if GitHub Actions fails
- how to rerun publish/promotion without rebuilding
- how test profile differs from production profile

## Testing Requirements

Run:

```bash
deploy/aws-cli-downloads/release.sh --profile test --version <current-version> --dry-run
```

Verify:

- version parsing works
- tag name is correct
- script refuses dirty worktree unless bypassed
- script prints exact `git tag`, `git push`, and `gh` commands in dry-run mode
- script uses testing profile base URL

If approved for a real test tag:

- run against the testing profile
- confirm GitHub Actions matrix starts
- confirm publish job targets the testing download bucket/domain
- confirm `smoke.sh` passes against the testing domain

## Completion Notes

Added during completion on 2026-06-18.

The release orchestration script exists and is documented. A real release/tag flow was intentionally not run after the live installer smoke found a macOS runtime portability issue.
